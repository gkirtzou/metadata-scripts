import ConfigParser
import rdflib
import jsonpickle


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


def createFlareObj(workingClassURI, rdfGraph):
    print 'Working with class:', workingClassURI
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

    # print len(qres)
    for row in qres:
        # Get subclass URI
        workingSubClassURI = row['c']
        # print 'Working subclass', workingSubClassURI
        # Create subclass flare object
        flare_obj_child = createFlareObj(workingSubClassURI, rdfGraph)
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

    flare_root = Flare('OWL-Thing', '', '')
    # For each OWL Thing subclass, ie workingClass
    for workingClassURI in ontology_classes:
        print workingClassURI.encode('utf-8')
        flare_obj = createFlareObj(workingClassURI, rdfGraph)
        flare_root.add_child(flare_obj)

    # print(flare_root)
    # print(jsonpickle.encode(flare_root))
    # Export to json
    print('Exporting to file:', filename_json)
    json_data = jsonpickle.encode(flare_root)
    output = open(filename_json, 'w')
    output.write(json_data)
    output.close()
