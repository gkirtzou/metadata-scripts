import pprint
from configparser import ConfigParser
import rdflib
import sys



# import owlrl
# from owlrl import OWLRL_Semantics


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
    sys.stdout = open("test.txt", "w")
    Config = ConfigParser()
    Config.read('generate_xsd_elements.ini')

    filename_owl = Config.get('Input', 'filename_owl')

    # Read OWL ontology file
    rdfGraph = rdflib.Graph()
    rdfGraph.parse(filename_owl)
    # owlrl.DeductiveClosure(OWLRL_Semantics).expand(rdfGraph)

    pp = pprint.PrettyPrinter(indent=4)
    dict_for_xml = []
    # For DatatypeProperties
    # data_properties_results = rdfGraph.query(
    #     " SELECT ?p WHERE { ?p a owl:DatatypeProperty  FILTER regex(str(?p), \" "
    #     + domain +
    #     "\")} ORDER BY ASC(?p) ")
    data_properties_results = rdfGraph.query(
        """
        SELECT DISTINCT ?p
	    WHERE { ?p a owl:DatatypeProperty }
	    ORDER BY ASC(?p)
        """)

    for res in data_properties_results:
        resource = rdfGraph.resource(res['p'])

        data_property = resource_common_elements_to_dict(resource)
        data_property['property'] = 'dataProp'
        # More thought when range is or combination
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
            # Case 1: CV the instances of the class range
            if len(ci_res) > 0:
                print('Case 1', resource)
                dict_r = resource_common_elements_to_dict(resource)
                dict_r['property'] = 'objProp'
                dict_r['type'] = range.qname()
                dict_r['controlled_vocabulary'] = []
                for ci in ci_res:
                    instance = rdfGraph.resource(ci['i'])
                    dict_r['controlled_vocabulary'].append(resource_common_elements_to_dict(instance))
                dict_for_xml.append(dict_r)
            else:
                query_subclasses = "SELECT DISTINCT ?sc WHERE { ?sc rdfs:subClassOf <" + range.identifier + ">} ORDER BY ASC(?sb)"
                sc_res = rdfGraph.query(query_subclasses)

                if len(sc_res) > 0:
                    is_cv_case = False
                    for sc in sc_res:
                        subclass = rdfGraph.resource(sc['sc'])
                        query_class_instances = "SELECT DISTINCT ?i WHERE { ?i a <" + subclass.identifier + ">} ORDER BY ASC(?i)"
                        ci_res = rdfGraph.query(query_class_instances)
                        # Case 2: CV the instances of the classes, where classes are subclasses of class range
                        if len(ci_res) > 0:
                            is_cv_case = True
                            dict_r = resource_common_elements_to_dict(subclass)
                            print('Case 2', subclass, len(ci_res))
                            dict_r['property'] = 'objProp'
                            dict_r['type'] = subclass.qname()
                            dict_r['controlled_vocabulary'] = []
                            for ci in ci_res:
                                instance = rdfGraph.resource(ci['i'])
                                dict_r['controlled_vocabulary'].append(resource_common_elements_to_dict(instance))
                            dict_for_xml.append(dict_r)
                    # Case 3: no CV
                    if not is_cv_case:
                        print('Case 3.1', resource)
                        dict_r = resource_common_elements_to_dict(resource)
                        dict_r['property'] = 'objProp'
                        try:
                            dict_r['type'] = range.qname()
                        except:
                            dict_r['type'] = None
                            dict_r['controlled_vocabulary'] = []
                            dict_for_xml.append(dict_r)
                # Case 3: no CV
                else:
                    print('Case 3.2', resource)
                    dict_r = resource_common_elements_to_dict(resource)
                    dict_r['property'] = 'objProp'
                    try:
                        dict_r['type'] = range.qname()
                    except:
                        dict_r['type'] = None
                    dict_r['controlled_vocabulary'] = []
                    dict_for_xml.append(dict_r)
        #else:
        #    print(resource)
    sys.stdout.close()
    return dict_for_xml

