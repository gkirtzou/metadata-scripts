import ConfigParser
import rdflib

if __name__ == '__main__':
    Config = ConfigParser.ConfigParser()
    Config.read('generate_flare_json_from_owl.ini')

    filename_owl = Config.get('Input', 'filename_owl')
    filename_owl_format = Config.get('Input', 'filename_owl_format')
    filename_json = Config.get('Output', 'filename_json')

    # Read OWL ontology file
    rdfGraph = rdflib.Graph()
    rdfGraph.parse(filename_owl, format=filename_owl_format)

    # Get all OWL classes defined in ontology
    qres = rdfGraph.query(
        """ SELECT DISTINCT ?c
        WHERE {
        ?c a owl:Class.
        ?c rdfs:subClassOf owl:Thing
        }""")
    ontology_classes_tmp = list(qres)
    ontology_classes = [
        x for x in ontology_classes_tmp if 'http://w3id.org/meta-share/omtd-share/' in str(x)]

    for uri in ontology_classes:
        print "All classes:",  uri

    workingResourceURI = ontology_classes.pop()
    workingResource = rdfGraph.resource(workingResourceURI)
    print 'Working resource ', workingResource
#    subclassesOfWorkingResource = rdfGraph.subjects(predicate=rdflib.RDFS.subClassOf,
 #                                                   object=workingResource.identifier)
    query = "SELECT DISTINCT ?c  WHERE { ?c a owl:Class. ?c rdfs:subClassOf <%s>}" % workingResourceURI
    print query
    qres = rdfGraph.query(query)

    for s in qres:
        print 'subclasses', s
