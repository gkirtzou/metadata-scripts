import lxml.etree as etree
# from lxml.etree import Element, SubElement, QName, tostring
import rdflib

# Declaring namespace
xs = 'http://www.w3.org/2001/XMLSchema'
xml = 'xml'

# Declaring target namespace info
target_ns = 'http://www.meta-share.org/OMTD-SHARE_XMLSchema'
target_version = '3.0.1'


# Create xsd root element
root = etree.Element(etree.QName(xs, 'schema'),
                     nsmap={'ms': target_ns, 'xs': xs})
root.attrib[etree.QName('targerNamespace')] = target_ns
root.attrib[etree.QName('elementFormDefault')] = 'qualified'
root.attrib[etree.QName('attributeFormDefault')] = 'unqualified'
root.attrib[etree.QName('version')] = target_version
root.attrib[etree.QName(xml, 'lang')] = 'en'


# Read OWL ontology file
graph = rdflib.Graph()
result = graph.parse("omtd-share-tdm-ontology.rdf",
                     format="application/rdf+xml")
print('graph has %s statements.' % len(graph))

# Create xsd controlledVocabulary element
# Get RDF Class
uriControlledVocabulary = 'http://w3id.org/meta-share/omtd-share/AnnotationType'
resourceControlledVocabulary = graph.resource(uriControlledVocabulary)
print('ControlledVocabulary :: ' + str(resourceControlledVocabulary))
print resourceControlledVocabulary.identifier

controlledVocabulary = etree.SubElement(root, etree.QName(xs, 'simpleType'))
controlledVocabulary.attrib[etree.QName(
    'name')] = resourceControlledVocabulary.identifier
cvAnnotation = etree.SubElement(
    controlledVocabulary, etree.QName(xs, 'annotation'))
cvDocumentation = etree.SubElement(
    cvAnnotation, etree.QName(xs, 'documentation'))
cvDocumentation.text = resourceControlledVocabulary.comment()
cvAppInfo = etree.SubElement(
    cvAnnotation, etree.QName(xs, 'appinfo'))
cvLabel = etree.SubElement(cvAppInfo, etree.QName('label'))
cvLabel.text = resourceControlledVocabulary.label()
cvRestriction = etree.SubElement(
    controlledVocabulary, etree.QName(xs, 'restriction'))
cvRestriction.attrib[etree.QName('base')] = 'xs:URI'

parent = resourceControlledVocabulary
subclasses = list(
    parent.subjects(rdflib.RDFS.subClassOf))
# subclasses = list(graph.subjects(
#    rdflib.RDF.type, uriControlledVocabulary))
print 'Subclasses size is ' + str(subclasses.__len__())
for c in subclasses:
    print c

c = subclasses[1]
# rdf URI to enumeration value
enumerationCV = etree.SubElement(cvRestriction, etree.QName(xs, 'enumeration'))
enumerationCV.attrib[etree.QName('value')] = c.identifier
# xs:annotation
enumerationCVAnnotation = etree.SubElement(
    enumerationCV, etree.QName(xs, 'annotation'))
# rdfs:comment to xs:documentation
enumerationCVDocumentation = etree.SubElement(
    enumerationCVAnnotation, etree.QName(xs, 'documentation'))
enumerationCVDocumentation.text = c.comment()
# xs:appinfo
enumerationCVAppInfo = etree.SubElement(
    enumerationCVAnnotation, etree.QName(xs, 'appinfo'))
# rdfs:label to label
enumerationCVLabel = etree.SubElement(
    enumerationCVAppInfo, etree.QName('label'))
enumerationCVLabel.text = c.label()
# rdfs:subclassOf to subclassOf
enumerationCVSubclassOf = etree.SubElement(
    enumerationCVAppInfo, etree.QName('subclassOf'))
enumerationCVSubclassOf.text = parent.identifier

enumerationCValtLabels = list(c.objects(rdflib.namespace.SKOS.altLabel))
for altlabel in enumerationCValtLabels:
    # skos:altLabel to altLabel
    enumerationCValtLabel = etree.SubElement(
        enumerationCVAppInfo, etree.QName('altLabel'))
    enumerationCVAltLabel.text = altlabel


print etree.tostring(root, pretty_print=True)
