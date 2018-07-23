import rdflib
import ConfigParser

def generate_dictionary(choices, uriResource, rdfGraph):
    resource = rdfGraph.resource(uriResource)
    parentResources = resource.objects(rdflib.RDFS.subClassOf)

    print "Working resource is " + resource.identifier
    #for parent in parentResources:
    #    print "and has parent " + parent.identifier

    pair = (resource.identifier.__str__(), resource.label().__str__())
    choices.append(pair)


    subclasses = resource.subjects(rdflib.RDFS.subClassOf)

    for c in subclasses:
        # Ignore myself resource
        if c.identifier == resource.identifier:
            continue
        generate_dictionary(choices, c.identifier, rdfGraph)
    return



if __name__ == '__main__':
    Config = ConfigParser.ConfigParser()
    Config.read('generate_dictionary.ini')

    filename_owl = Config.get('Input', 'filename_owl')
    filename_output = Config.get('Output', 'filename_output')

    # Read OWL ontology file
    rdfGraph = rdflib.Graph()
    result = rdfGraph.parse(filename_owl,
                            format="application/rdf+xml")

    fileOuput = open(filename_output, 'w')

    mapping = Config.items('Mapping')
    for m in mapping:
        root_url = Config.get('Mapping', m[0])

        print root_url
        choices = []
        generate_dictionary(choices, root_url, rdfGraph)

        fileOuput.write(m[0] + ' = (\n')
        # Print Result
        for c in choices:
            fileOuput.write(c.__str__() + ",\n")
        fileOuput.write(')\n\n')
    fileOuput.close()
