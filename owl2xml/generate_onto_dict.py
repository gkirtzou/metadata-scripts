import pprint
from configparser import ConfigParser
import rdflib
import sys


def literal_to_tuple(literal):
    return (literal.value, literal.language)


def literals_to_list(literals):
    return [literal_to_tuple(l) for l in literals]


def resources_to_list(resources):
    return [str(r.identifier) for r in resources]


def resource_common_elements_to_dict(resource):
    dict_r = dict()
    dict_r['identifier'] = str(resource.identifier)
    try:
        dict_r['name'] = resource.qname()
    except:
        pass
    dict_r['def'] = literals_to_list(resource.objects(rdflib.namespace.RDFS.comment))
    dict_r['label'] = literals_to_list(resource.objects(rdflib.namespace.RDFS.label))
    dict_r['label_plural'] = []
    dict_r['alt_label'] = literals_to_list(resource.objects(rdflib.namespace.SKOS.altLabel))
    dict_r['example'] = literals_to_list(resource.objects(rdflib.namespace.SKOS.example))
    dict_r['close_match'] = resources_to_list(resource.objects(rdflib.namespace.SKOS.closeMatch))
    dict_r['exact_match'] = resources_to_list(resource.objects(rdflib.namespace.SKOS.exactMatch))
    dict_r['broad_match'] = resources_to_list(resource.objects(rdflib.namespace.SKOS.broadMatch))
    dict_r['narrow_match'] = resources_to_list(resource.objects(rdflib.namespace.SKOS.narrowMatch))
    return dict_r


def get_rdf_dict():

    Config = ConfigParser()
    Config.read('generate_xsd_elements.ini')

    filename_owl = Config.get('Input', 'filename_owl')
    format_owl = Config.get('Input', 'filename_owl_format')
    related_properties = Config.get('Input', 'related_properties')

    log_file = Config.get('Output', 'log_file')
    sys.stdout = open(log_file, 'w')

    # Read OWL ontology file
    rdfGraph = rdflib.Graph()
    rdfGraph.parse(filename_owl, format=format_owl)


    pp = pprint.PrettyPrinter(indent=4)
    dict_for_xml = []
    xml_entities = set()
    data_properties_results = rdfGraph.query(
        """
        SELECT DISTINCT ?p
	    WHERE { ?p a owl:DatatypeProperty }
	    ORDER BY ASC(?p)
        """)

    for res in data_properties_results:
        resource = rdfGraph.resource(res['p'])
        print('Case 1', resource)
        data_property = resource_common_elements_to_dict(resource)
        data_property['property'] = 'dataProp'
        range = resource.value(rdflib.namespace.RDFS.range)
        if range:
            try:
                data_property['type'] = range.qname()
            except:
                data_property['type'] = None
        else:
            data_property['type'] = None

        dict_for_xml.append(data_property)

    # For ObjectProperties
    obj_properties_results = rdfGraph.query(
        """
        SELECT DISTINCT ?p
        WHERE { ?p a owl:ObjectProperty }
        ORDER BY ASC(?p)
        """)

    for res in obj_properties_results:
        resource = rdfGraph.resource(res['p'])
        print('Working on r:', resource)
        range = resource.value(rdflib.namespace.RDFS.range)
        if range != None:
            query_class_instances = "SELECT DISTINCT ?i WHERE { ?i a <" + range.identifier + ">} ORDER BY ASC(?i)"
            ci_res = rdfGraph.query(query_class_instances)
            # Case 2: CV the instances of the class range
            if len(ci_res) > 0:
                print('Case 2', resource)
                dict_r = resource_common_elements_to_dict(resource)
                dict_r['property'] = 'objProp'
                dict_r['type'] = range.qname()
                dict_r['controlled_vocabulary'] = []
                for ci in ci_res:
                    instance = rdfGraph.resource(ci['i'])
                    dict_r['controlled_vocabulary'].append(resource_common_elements_to_dict(instance))
                if dict_r['identifier'] not in xml_entities:
                    dict_for_xml.append(dict_r)
                    xml_entities.add(dict_r['identifier'])
            else:
                # Subclass condition
                query_subclasses = "SELECT DISTINCT ?sc WHERE { ?sc rdfs:subClassOf <" + range.identifier + ">} ORDER BY ASC(?sb)"
                sc_res = rdfGraph.query(query_subclasses)

                if len(sc_res) > 0 and resource.identifier not in related_properties:
                    for sc in sc_res:
                        subclass = rdfGraph.resource(sc['sc'])
                        query_class_instances = "SELECT DISTINCT ?i WHERE { ?i a <" + subclass.identifier + ">} ORDER BY ASC(?i)"
                        ci_res = rdfGraph.query(query_class_instances)
                        dict_r = resource_common_elements_to_dict(subclass)

                        dict_r['property'] = 'objProp'
                        dict_r['type'] = subclass.qname()
                        dict_r['controlled_vocabulary'] = []
                        # Case 3: CV the instances of the classes, where classes are subclasses of class range
                        if len(ci_res) > 0:
                            print('Case 3', subclass, len(ci_res))
                            dict_r['controlled_vocabulary'] = []
                            for ci in ci_res:
                                instance = rdfGraph.resource(ci['i'])
                                dict_r['controlled_vocabulary'].append(resource_common_elements_to_dict(instance))
                        else:
                            print('Case 5', subclass)
                            dict_r['controlled_vocabulary'] = []
                        if dict_r['identifier'] not in xml_entities:
                            dict_for_xml.append(dict_r)
                            xml_entities.add(dict_r['identifier'])
                else:
                    print('Case 4', resource)
                    dict_r = resource_common_elements_to_dict(resource)
                    dict_r['property'] = 'objProp'
                    try:
                        dict_r['type'] = range.qname()
                    except:
                        dict_r['type'] = None
                    dict_r['controlled_vocabulary'] = []
                    if dict_r['identifier'] not in xml_entities:
                        dict_for_xml.append(dict_r)
                        xml_entities.add(dict_r['identifier'])

    sys.stdout.close()
    return dict_for_xml

