import lxml.etree as etree
import rdflib


def recursiveFunction(element, uriResource, rdfGraph):
    resource = rdfGraph.resource(uriResource)
    parentResources = resource.objects(rdflib.RDFS.subClassOf)

    print "Working resource is " + resource.identifier
    # for parent in parentResources:
    #    print "and has parent " + parent.identifier

    # Create xsd enumeration element
    # rdf URI to enumeration value
    enumeration = etree.SubElement(
        element, etree.QName(xs, 'enumeration'))
    enumeration.attrib[etree.QName('value')] = resource.identifier
    # xs:annotation
    enumerationAnnotation = etree.SubElement(
        enumeration, etree.QName(xs, 'annotation'))
    # rdfs:comment to xs:documentation
    enumerationDocumentation = etree.SubElement(
        enumerationAnnotation, etree.QName(xs, 'documentation'))
    enumerationDocumentation.text = resource.comment()
    # xs:appinfo
    enumerationAppInfo = etree.SubElement(
        enumerationAnnotation, etree.QName(xs, 'appinfo'))
    # rdfs:label to label
    enumerationLabel = etree.SubElement(
        enumerationAppInfo, etree.QName('label'))
    enumerationLabel.text = resource.label()

    # rdfs:subclassOf to subclassOf
    for parent in parentResources:
        print "and has parent " + parent.identifier
        if parent.identifier.startswith('http'):
            enumerationSubclassOf = etree.SubElement(
                enumerationAppInfo, etree.QName('subclassOf'))
            enumerationSubclassOf.text = parent.identifier

    enumerationAltLabels = resource.objects(rdflib.namespace.SKOS.altLabel)
    for altlabel in enumerationAltLabels:
        # skos:altLabel to altLabel
        enumerationAltLabel = etree.SubElement(
            enumerationAppInfo, etree.QName('altLabel'))
        enumerationAltLabel.text = altlabel

    subclasses = resource.subjects(rdflib.RDFS.subClassOf)

    for c in subclasses:
        # Ignore myself resource
        if c.identifier == resource.identifier:
            continue
        recursiveFunction(element, c.identifier, rdfGraph)
    return

# Read xsd file
tree = etree.parse('OMTD-SHARE-ControlledVocabs.xsd')
root = tree.getroot()
# print etree.tostring(root, pretty_print=True)

# Declaring namespace
xs = 'http://www.w3.org/2001/XMLSchema'
xml = 'xml'

# Declaring target namespace info
target_ns = 'http://www.meta-share.org/OMTD-SHARE_XMLSchema'
target_version = '3.0.1'


# Create xsd root element
# root = etree.Element(etree.QName(xs, 'schema'),
#                     nsmap={'ms': target_ns, 'xs': xs})
# root.attrib[etree.QName('targerNamespace')] = target_ns
# root.attrib[etree.QName('elementFormDefault')] = 'qualified'
# root.attrib[etree.QName('attributeFormDefault')] = 'unqualified'
# root.attrib[etree.QName('version')] = target_version
# root.attrib[etree.QName(xml, 'lang')] = 'en'


# Read OWL ontology file
rdfGraph = rdflib.Graph()
result = rdfGraph.parse("omtd-share-tdm-ontology.rdf",
                        format="application/rdf+xml")
print('graph has %s statements.' % len(rdfGraph))

for element in root.iter(etree.QName(xs, 'simpleType').text):
    print("%s - %s" % (element.tag, element.attrib['name']))
    subelement = list(element.iter(etree.QName(xs, 'restriction').text))
    assert len(subelement) == 1
    subelement = subelement[0]
    uriResources = []
    # Get RDF Class
    if element.attrib['name'] == 'dataFormatType':
        uriResources.append('http://w3id.org/meta-share/omtd-share/DataFormat')
    elif element.attrib['name'] == 'annotationTypeType':
        uriResources.append(
            'http://w3id.org/meta-share/omtd-share/AnnotationType')
    elif element.attrib['name'] == 'TDMMethodType':
        uriResources.append('http://w3id.org/meta-share/omtd-share/TdmMethod')
    elif element.attrib['name'] == 'operationType':
        uriResources.append(
            'http://w3id.org/meta-share/omtd-share/ComponentType')
        uriResources.append('http://w3id.org/meta-share/omtd-share/Annotation')
        uriResources.append(
            'http://w3id.org/meta-share/omtd-share/TextAndDataMining')
    else:
        continue
    for uriResource in uriResources:
        recursiveFunction(subelement, uriResource, rdfGraph)


# print etree.tostring(root, pretty_print=True)

# Print xml
fileXML = open("foo.xsd", 'w')
fileXML.write(etree.tostring(root, pretty_print=True))
fileXML.close()
