import ConfigParser

import rdflib
from rdflib import Literal


def literals_to_list(literals):
    return [(l.value, l.language) for l in literals]

def resources_to_list(resources):
    return [r for r in resources]

if __name__ == '__main__':
    Config = ConfigParser.ConfigParser()
    Config.read('generate_xsd_elements.ini')


    filename_owl = Config.get('Input', 'filename_owl')
    filename_xsd = Config.get('Output', 'filename_xsd')

    # Read OWL ontology file
    rdfGraph = rdflib.Graph()
    rdfGraph.parse(filename_owl)

    dict_for_xml = []
    # For DatatypeProperties
    data_properties_results = rdfGraph.query(
        """
        SELECT ?p
	    WHERE { ?p a owl:DatatypeProperty }
	    ORDER BY ASC(?p)
	    LIMIT 10
        """)

    for res in data_properties_results:
        resource = rdfGraph.resource(res['p'])

        data_property = dict()
        data_property['property'] = 'dataProp'
        # More thought when range is or combination
        range = resource.value(rdflib.namespace.RDFS.range)
        if range != None:
            data_property['type'] = range.qname()
        else:
            data_property['type'] = None
        data_property['name'] = resource.qname()
        data_property['def'] = literals_to_list(resource.objects(rdflib.namespace.RDFS.comment))
        data_property['label'] = literals_to_list(resource.objects(rdflib.namespace.RDFS.label))
        data_property['label_plural'] = []
        data_property['alt_labels'] = literals_to_list(resource.objects(rdflib.namespace.SKOS.altLabel))
        data_property['example'] = literals_to_list(resource.objects(rdflib.namespace.SKOS.example))
        data_property['close_match'] = resources_to_list(resource.objects(rdflib.namespace.SKOS.closeMatch))
        data_property['exact_match'] = resources_to_list(resource.objects(rdflib.namespace.SKOS.exactMatch))
        data_property['broad_match'] = resources_to_list(resource.objects(rdflib.namespace.SKOS.broadMatch))
        data_property['narrow_match'] = resources_to_list(resource.objects(rdflib.namespace.SKOS.narrowMatch))

        dict_for_xml.append(data_property)

    for d in dict_for_xml:
         print(d)

    r = rdfGraph.resource('http://purl.org/net/def/metashare#contactPoint').value(rdflib.namespace.RDFS.range)

    print(r)

    # For ObjectProperties
    # qres = rdfGraph.query(
    #    """
    #    SELECT ?p
    #    WHERE { ?p a owl:ObjectProperty }
    #    ORDER BY ASC(?p)
    #    """)
    #
    # for row in qres:
    #     resource = rdfGraph.resource(row['p'])
    #
    #     print(resource)
    #     range = resource.value(rdflib.namespace.RDFS.range)
    #     if range != None:
    #         rr = rdfGraph.resource(range)
    #         print('range resource', rr.label())
    #
    #     # print(resource.qname())
    #     # print('Label', resource.label())
    #     # print('Def', resource.comment())
    #     #
    #     # print('AltLabels', [(altL.value, altL.language) for altL in resource.objects(rdflib.namespace.SKOS.altLabel)])
    #     # print('Example', [ex for ex in resource.objects(rdflib.namespace.SKOS.example)])
    #     # print('CloseMatch', [ex for ex in resource.objects(rdflib.namespace.SKOS.closeMatch)])
    #     # print('ExactMatch', [ex for ex in resource.objects(rdflib.namespace.SKOS.exactMatch)])
    #     # print('BroadMatch', [ex for ex in resource.objects(rdflib.namespace.SKOS.broadMatch)])
    #     # print('NarrowMatch', [ex for ex in resource.objects(rdflib.namespace.SKOS.narrowMatch)])



    # print etree.tostring(root, pretty_print=True)

    # Print xml
    #tree = etree.parse(filename_xsd)
    #fileXML = open(filename_xsd, 'w')
    #ileXML.write(etree.tostring(root, pretty_print=True))
    #fileXML.close()


