#OMTD ontology
import datetime

import lxml.etree as etree
import rdflib
from configparser import ConfigParser

from owl2xml.parse_rdf_to_dict import resource_common_elements_to_dict, create_dict_for_object_prop
from owl2xml.generate_xsd_elements import _create_annotation, get_name, create_object_prop
from xsd.namespaces import ms, omtd, xs, xml


def recursiveFunction(element, uriResource, rdfGraph, alreadySeen):
    if uriResource in alreadySeen:
        print('Already seen ' + uriResource)
        return

    alreadySeen.append(uriResource)
    resource = rdfGraph.resource(uriResource)
    parentResources = resource.objects(rdflib.RDFS.subClassOf)

    print("Working resource is " + uriResource)
    resource_dict = resource_common_elements_to_dict(resource)
    # for parent in parentResources:
    #    print "and has parent " + parent.identifier

    # Create xsd enumeration element
    # rdf URI to enumeration value

    enumeration = etree.SubElement(
        element, etree.QName(xs, 'enumeration'))

    enumeration.attrib[etree.QName('value')] = resource_dict['identifier']
    _create_annotation(enumeration, resource_dict)

    subclasses = resource.subjects(rdflib.RDFS.subClassOf)
    subclasses_list = sorted(c.identifier for c in subclasses)
    for c in subclasses_list:
        # Ignore myself resource
        if c == resource.identifier:
            continue
        recursiveFunction(element, c, rdfGraph, alreadySeen)
    return


if __name__ == '__main__':
    config = ConfigParser()
    config.read('generate_controlled_vocabularies.ini')

    filename_owl = config.get('Input', 'filename_owl')

    target_namespace = config.get('Input', 'target_namespace')
    NSMAP = {
        'ms': ms,
        'xs': xs,
        'omtd': omtd,
    }

    # Create ROOT element "schema"
    schema = etree.Element('{' + xs + '}schema', nsmap=NSMAP, attrib={
        'targetNamespace': target_namespace,
        'elementFormDefault': 'qualified',
        'attributeFormDefault': 'unqualified',
        'version': '0.01',
        '{' + xml + '}lang': 'en'
    })

    schema.append(etree.Comment(f'Last Updated: {datetime.datetime.today().strftime("%B %d, %Y")}'))

    # import xml namespace
    etree.SubElement(schema, '{' + xs + '}import', attrib={
        'namespace': xml,
        'schemaLocation': 'http://www.w3.org/2001/xml.xsd'
    })

    # Read xsd file
    #   root = etree.getroot()
    # print etree.tostring(root, pretty_print=True)

    # Declaring namespace
    xs = 'http://www.w3.org/2001/XMLSchema'
    xml = 'xml'

    # Read OWL ontology file
    rdfGraph = rdflib.Graph()
    result = rdfGraph.parse(filename_owl,
                            format="application/rdf+xml")

    subclass_map = config.items('Subclassing')
    for (k, v) in subclass_map:
        print('{} is mapped to resources {}'.format(k, v))
        resource = rdfGraph.resource(v)
        # Create xml annotation
        resource_dict = resource_common_elements_to_dict(resource)
        schema.append(etree.Comment(f'Definition for {v}'))
        element = etree.Element('{' + xs + '}simpleType', attrib={'name': get_name(resource_dict['name'])})
        _create_annotation(element, resource_dict)
        # Create xml restriction
        restriction = etree.SubElement(
            element, etree.QName(xs, 'restriction')
        )
        restriction.attrib[etree.QName('base')] = etree.QName(xs, 'anyURI')
        subclasses = resource.subjects(rdflib.RDFS.subClassOf)
        subclasses_list = sorted(c.identifier for c in subclasses)
        alreadySeen = []
        for subcl in subclasses_list:
            recursiveFunction(restriction, subcl, rdfGraph, alreadySeen)
        schema.append(element)

    instance_map = config.items('Instances')
    for (k, v) in instance_map:
        print('{} is mapped to resources {}'.format(k, v))
        resource = rdfGraph.resource(v)
        dict_resource = create_dict_for_object_prop(resource, rdfGraph)
        for d in dict_resource:
            schema.append(etree.Comment(f'Definition for {d["name"]}'))
            if d['type']:
                el = create_object_prop(d, el_type=d['type'])
            else:
                el = create_object_prop(d)
            schema.append(el)

    # print(str(etree.tostring(schema, pretty_print=True, xml_declaration=True, encoding='UTF-8')))

    filename_xsd = config.get('Output', 'filename_xsd')
    with open(filename_xsd, 'wb') as f:
        f.write(etree.tostring(schema, pretty_print=True, xml_declaration=True, encoding='UTF-8'))
