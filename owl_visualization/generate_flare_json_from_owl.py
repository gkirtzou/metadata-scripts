import ConfigParser
import rdflib
import jsonpickle


class Flare:

    def __init__(self, label, URI):
        self.name = label
        self.URI = URI
        self.children = []

    def __str__(self):
        str_representation = "name=%s URI=%s children=[" % (
            self.name, self.URI)
        for child in self.children:
            str_representation = str_representation + str(child) + ', '
        str_representation = str_representation + ']'
        return str_representation

    def add_child(self, child):
        self.children.append(child)


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

    for uri in ontology_classes:
        print "Top classes:",  uri

    workingClassURI = ontology_classes.pop()
    workingClass = rdfGraph.resource(workingClassURI)

    # Get working class subclasses
    query = "SELECT DISTINCT ?c  WHERE { ?c a owl:Class. ?c rdfs:subClassOf <%s>}" % workingClassURI
    print query
    qres = rdfGraph.query(query)
    flare_obj = Flare(str(workingClass.label()), str(workingClassURI))
    print(flare_obj)

    for s in qres:
        workingSubClassURI = s['c']
        print 'subclass', workingSubClassURI
        workingSubClass = rdfGraph.resource(workingSubClassURI)
        flare_obj_child = Flare(
            str(workingSubClass.label()), str(workingSubClassURI))
        print('Str print:', str(flare_obj_child))
        print('Json print:', jsonpickle.encode(flare_obj_child))
        flare_obj.add_child(flare_obj_child)

    print(flare_obj)
    print(jsonpickle.encode(flare_obj))
    # # Export to json
    # f1 = Flare('label1', 'URI1')
    # f11 = Flare('label11', 'URI11')
    # f12 = Flare('label12', 'URI12')
    # f1.add_child(f11)
    # f1.add_child(f12)

    # print(jsonpickle.encode(f1, make_refs=False))
    json_data = jsonpickle.encode(flare_obj)
    output = open('data.txt', 'w')
    output.write(json_data)
    output.close()
