import ast
import pprint
import sys

import rdflib
from configparser import ConfigParser


def literal_to_tuple(literal):
    return literal.value, literal.language


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
    config = ConfigParser()
    config.read('generate_xsd_elements.ini')

    # RDF files
    filename_owl = ast.literal_eval(config.get('Input', 'filename_owl'))
    format_owl = ast.literal_eval(config.get('Input', 'filename_owl_format'))
    try:
        domains = ast.literal_eval(config.get('Input', 'domains'))
    except:
        domains = None

    related_properties = ast.literal_eval(config.get('Input', 'related_properties'))
    generate_attributes_properties = ast.literal_eval(config.get('Input', 'generate_attributes_properties'))

    log_file = config.get('Output', 'log_file')
    sys.stdout = open(log_file, 'w')

    # Read OWL ontology file
    rdfGraph = rdflib.Graph()
    for id_x, file in enumerate(filename_owl):
        rdfGraph.parse(file, format=format_owl[id_x])
        print("graph has %s statements." % len(rdfGraph))

    pp = pprint.PrettyPrinter(indent=4)
    dict_for_xml = []
    xml_entities = set()

    # For DataProperties
    if domains:
        query = str('''
            SELECT DISTINCT ?p
            WHERE {{ 
             ?p a owl:DatatypeProperty 
             FILTER({0})
            }}
            ORDER BY ASC(?p)
            ''')
        # Keep properties from given domains
        filter_str = ''
        for id_d, d in enumerate(domains):
            filter_str += "regex(str(?p), \"{0}\")".format(d)
            if id_d + 1 < len(domains):
                filter_str += ' || '
        query = query.format(filter_str)
    else:
        query = '''
            SELECT DISTINCT ?p
            WHERE {{ 
             ?p a owl:DatatypeProperty 
            }}
            ORDER BY ASC(?p)
            '''

    data_properties_results = rdfGraph.query(query)

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
    if domains:
        query = str('''
         SELECT DISTINCT ?p
         WHERE {{
         ?p a owl:ObjectProperty
         FILTER({0})
         }}
         ORDER BY ASC(?p)
         ''')

        # Keep properties from given domains
        filter_str = ''
        for id_d, d in enumerate(domains):
            filter_str += "regex(str(?p), \"{0}\")".format(d)
        if id_d + 1 < len(domains):
            filter_str += ' || '
        query = query.format(filter_str)
    else:
        query = '''
         SELECT DISTINCT ?p
         WHERE {{
         ?p a owl:ObjectProperty         
         }}
         ORDER BY ASC(?p)
         '''

    obj_properties_results = rdfGraph.query(query)

    for res in obj_properties_results:
        resource = rdfGraph.resource(res['p'])
        print('Working on r:', resource)
        range = resource.value(rdflib.namespace.RDFS.range)
        if range is not None:
            query_class_instances = "SELECT DISTINCT ?i WHERE { ?i a <" + range.identifier + ">} ORDER BY ASC(?i)"
            ci_res = rdfGraph.query(query_class_instances)
            # Case 2: CV the instances of the class range
            if len(ci_res) > 0:
                dict_r = resource_common_elements_to_dict(resource)
                if str(resource.identifier) in generate_attributes_properties:
                    print('Case 7.2', resource)
                    dict_r['property'] = 'attrProp'
                else:
                    print('Case 2', resource)
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
                query_subclasses = "SELECT DISTINCT ?sc WHERE { ?sc rdfs:subClassOf* <" + range.identifier + ">} ORDER BY ASC(?sc)"
                sc_res = rdfGraph.query(query_subclasses)

                if len(sc_res) > 1 and str(resource.identifier) not in related_properties:
                    print("Subclasses ", len(sc_res))
                    for sc in sc_res:
                        subclass = rdfGraph.resource(sc['sc'])
                        query_class_instances = "SELECT DISTINCT ?i WHERE { ?i a <" + subclass.identifier + ">} ORDER BY ASC(?i)"
                        ci_res = rdfGraph.query(query_class_instances)
                        dict_r = resource_common_elements_to_dict(subclass)

                        dict_r['type'] = subclass.qname()
                        dict_r['controlled_vocabulary'] = []
                        # Case 3: CV the instances of the classes, where classes are subclasses of class range
                        if len(ci_res) > 0:
                            if str(resource.identifier) in generate_attributes_properties:
                                print('Case 7.3', subclass)
                                dict_r['property'] = 'attrProp'
                            else:
                                print('Case 3', subclass, len(ci_res))
                                dict_r['property'] = 'objProp'
                            dict_r['controlled_vocabulary'] = []
                            for ci in ci_res:
                                instance = rdfGraph.resource(ci['i'])
                                dict_r['controlled_vocabulary'].append(resource_common_elements_to_dict(instance))
                        # Case 4:  Object properties with range with subclasses without instances
                        else:
                            if str(resource.identifier) in generate_attributes_properties:
                                print('Case 7.4', subclass)
                                dict_r['property'] = 'attrProp'
                            else:
                                print('Case 4', subclass)
                                dict_r['property'] = 'objProp'
                            dict_r['controlled_vocabulary'] = []
                        if dict_r['identifier'] not in xml_entities:
                            dict_for_xml.append(dict_r)
                            xml_entities.add(dict_r['identifier'])
                # Case 5: for Object properties with range class without subclasses and without individuals
                else:
                    dict_r = resource_common_elements_to_dict(resource)
                    if str(resource.identifier) in generate_attributes_properties:
                        print('Case 7.5', resource)
                        dict_r['property'] = 'attrProp'
                    else:
                        print('Case 5', resource)
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
