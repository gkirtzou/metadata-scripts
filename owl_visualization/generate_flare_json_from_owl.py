import ConfigParser
import rdflib
import jsonpickle
import sys
sys.setrecursionlimit(100000)


class Flare:

    def __init__(self, label, URI, definition):
        self.name = label
        self.URI = URI
        self.definition = definition
        self.children = []

    def __str__(self):
        str_representation = "name=%s URI=%s definition=%s children=[" % (
            self.name, self.URI, self.definition)
        for child in self.children:
            str_representation = str_representation + str(child) + ', '
        str_representation = str_representation + ']'
        return str_representation

    def add_child(self, child):
        self.children.append(child)


def createFlareObj(workingClassURI, rdfGraph, deprecated_classes):
    workingClass = rdfGraph.resource(workingClassURI)
    # Create flare object for the working OWL class
    wcName = workingClass.label().encode('utf-8')
    wcURI = workingClassURI.encode('utf-8')
    wcDefinition = workingClass.comment().encode('utf-8')
    # print wcDefinition
    flare_obj = Flare(wcName, wcURI, wcDefinition)
    # print(flare_obj)

    # Get working OWL class subclasses
    query = "SELECT DISTINCT ?c  WHERE { ?c a owl:Class. ?c rdfs:subClassOf <%s>}" % workingClassURI
    qres = rdfGraph.query(query)

    print 'Working with class:', workingClassURI,  'which has ', len(qres), ' children'
    for row in qres:
        # Get subclass URI
        workingSubClassURI = row['c'].encode('utf-8')
        if workingSubClassURI in deprecated_classes:
            print workingClassURI, ' is deprecated. Ignore'
        else:
            # Create subclass flare object
            flare_obj_child = createFlareObj(
                workingSubClassURI, rdfGraph, deprecated_classes)
            # Add subclass flare object to working class flare object
            flare_obj.add_child(flare_obj_child)

    return flare_obj


if __name__ == '__main__':
    Config = ConfigParser.ConfigParser()
    Config.read('generate_flare_json_from_owl.ini')

    filename_owl = Config.get('Input', 'filename_owl')
    filename_owl_format = Config.get('Input', 'filename_owl_format')
    filename_json = Config.get('Output', 'filename_json')

    # Read OWL ontology file
    rdfGraph = rdflib.Graph()
    rdfGraph.parse(filename_owl, format=filename_owl_format)

    # Get top level OWL classes defined in ontology
    qres = rdfGraph.query(
        """ SELECT DISTINCT ?c
        WHERE {
        ?c a owl:Class.
        ?c rdfs:subClassOf owl:Thing
        }""")
    ontology_classes = [
        x['c'] for x in qres if 'http://w3id.org/meta-share/omtd-share/' in x['c']]

    # Get deprecated classes
    qres = rdfGraph.query(
        """ SELECT ?deprecatedClass
            WHERE  {
            ?deprecatedClass a owl:Class.
            ?deprecatedClass owl:deprecated "true"^^<http://www.w3.org/2001/XMLSchema#boolean>
        } """)
    deprecated_classes = [
        x['deprecatedClass'].encode('utf-8') for x in qres if 'http://w3id.org/meta-share/omtd-share/' in x['deprecatedClass']]
    print('Deprecated classes', deprecated_classes)

    flare_root = Flare('OWL-Thing', '', '')
    # For each OWL Thing subclass, ie workingClass
    for workingClassURI in ontology_classes:
        if workingClassURI not in deprecated_classes:
            print 'Working on ', workingClassURI.encode('utf-8'), ' branch'
            flare_obj = createFlareObj(
                workingClassURI, rdfGraph, deprecated_classes)
            flare_root.add_child(flare_obj)
        else:
            print workingClassURI, ' is deprecated. Ignore'

    # print(flare_root)
    # print(jsonpickle.encode(flare_root))
    # Export to json
    print('Exporting to file:', filename_json)
    json_data = jsonpickle.encode(flare_root)
    output = open(filename_json, 'w')
    output.write(json_data)
    output.close()
