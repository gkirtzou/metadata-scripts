import datetime
import sys

from configparser import ConfigParser
from lxml import etree

from owl2xml.generate_onto_dict import get_rdf_dict
from xsd.namespaces import ms, xs, xml, omtd
from xsd.xsd import Enumeration


def _tuple_list_to_child_element_multi(parent, item, name, prefix=None):
    ns = ''
    if prefix:
        ns = '{' + prefix + '}'

    for x in item:
        if x[1]:
            lang = x[1]
        else:
            lang = 'en'
        etree.SubElement(parent, ns + name, attrib={
            '{' + xml + '}lang': lang
        }).text = x[0]


def _list_to_child_element_multi(parent, item, name, prefix=None):
    ns = ''
    if prefix:
        ns = '{' + prefix + '}'

    for x in item:
        etree.SubElement(parent, ns + name).text = x


def _create_annotation(parent, data_dict):
    annotation = etree.SubElement(parent, '{' + xs + '}annotation')

    # create definitions
    _tuple_list_to_child_element_multi(annotation, data_dict['def'], 'documentation', prefix=xs)

    # create appinfo
    appinfo = etree.SubElement(annotation, '{' + xs + '}appinfo')

    etree.SubElement(appinfo, 'identifier').text = data_dict['identifier']

    # appinfo children
    _tuple_list_to_child_element_multi(appinfo, data_dict['label'], 'label')
    _tuple_list_to_child_element_multi(appinfo, data_dict['label_plural'], 'label_plural')
    _tuple_list_to_child_element_multi(appinfo, data_dict['alt_label'], 'alt_label')
    _tuple_list_to_child_element_multi(appinfo, data_dict['example'], 'example')
    _tuple_list_to_child_element_multi(appinfo, data_dict['note'], 'note')

    _list_to_child_element_multi(appinfo, data_dict['close_match'], 'closeMatch')
    _list_to_child_element_multi(appinfo, data_dict['exact_match'], 'exactMatch')
    _list_to_child_element_multi(appinfo, data_dict['narrow_match'], 'narrowMatch')
    _list_to_child_element_multi(appinfo, data_dict['broad_match'], 'broadMatch')
    _list_to_child_element_multi(appinfo, data_dict['subclass_of'], 'subclassOf')

    return annotation


def get_name(name):
    # attrib={'name': data['name'].split(':')[1]+f"_{data['name'].split(':')[0]}"}
    try:
        new_name = name.split(':')[1]
    except IndexError:
        return name
    return new_name
    # name.replace(':', '_')


def create_data_prop(data, el_type=None):
    if el_type:
        if el_type == 'rdf:langString':
            element_type = 'xs:string'
        else:
            element_type = el_type.replace('xsd', 'xs')
    else:
        element_type = 'xs:string'
    #if el_type == 'rdf:langString':
    #    element = etree.Element('{' + xs + '}element', attrib={'name': get_name(data['name'])})
    if element_type == 'xs:string':
        element = etree.Element('{' + xs + '}element', attrib={'name': get_name(data['name'])})
    else:
        element = etree.Element('{' + xs + '}element', attrib={'name': get_name(data['name']),
                                                               'type': element_type})

    _create_annotation(element, data)

    # check if type is rdf:langString and create an restriction of ms:langString with maxlength
    if el_type == 'rdf:langString':
        complex_type = etree.SubElement(element, '{' + xs + '}complexType')
        simple_content = etree.SubElement(complex_type, '{' + xs + '}simpleContent')
       # extension = etree.SubElement(simple_content, '{' + xs + '}extension', attrib={'base': 'xs:string'})
       # etree.SubElement(extension, '{' + xs + '}attribute',
       #                  attrib={'ref': 'xml:lang'})
        restriction = etree.SubElement(simple_content, '{' + xs + '}restriction', attrib={'base': 'ms:langString'})
        etree.SubElement(restriction, '{' + xs + '}maxLength',
                       attrib={'value': '300'})
    elif element_type == 'xs:string':
        simple_content = etree.SubElement(element,
                                          '{' + xs + '}simpleType')
        restriction = etree.SubElement(simple_content,
                                       '{' + xs + '}restriction',
                                       attrib={'base': 'xs:string'})
        etree.SubElement(restriction, '{' + xs + '}maxLength',
                         attrib={'value': '300'})
    return element


def create_object_prop(data, el_type=None):
    if data['controlled_vocabulary']:
        element = etree.Element('{' + xs + '}element', attrib={'name': get_name(data['name'])})
    else:
        if el_type:
            element = etree.Element('{' + xs + '}element', attrib={'name': get_name(data['name']),
                                                                   'type': el_type})
        else:
            element = etree.Element('{' + xs + '}element', attrib={'name': get_name(data['name'])})
    _create_annotation(element, data)

    if data['controlled_vocabulary']:
        # build enumeration block
        simpe_type = etree.SubElement(element, '{' + xs + '}simpleType')
        restriction = etree.SubElement(simpe_type, '{' + xs + '}restriction', attrib={'base': 'xs:anyURI'})
        for cv in data['controlled_vocabulary']:
            enum = Enumeration(cv['identifier']).to_xsd()
            _create_annotation(enum, cv)
            restriction.append(enum)

    return element


def create_attribute(data):
    element = etree.Element('{' + xs + '}attribute', attrib={'name': get_name(data['name'])})
    _create_annotation(element, data)

    if data['controlled_vocabulary']:
        # build enumeration block
        simpe_type = etree.SubElement(element, '{' + xs + '}simpleType')
        restriction = etree.SubElement(simpe_type, '{' + xs + '}restriction', attrib={'base': 'xs:anyURI'})
        for cv in data['controlled_vocabulary']:
            enum = Enumeration(cv['identifier']).to_xsd()
            _create_annotation(enum, cv)
            restriction.append(enum)

    return element


if __name__ == '__main__':
    config = ConfigParser()
    config.read('generate_xsd_elements.ini')
    target_namespace = config.get('Input', 'target_namespace')
    NSMAP = {
        'ms': ms,
        'xs': xs,
        'omtd': omtd,
    }

    # Create ROOT element "schema"
    schema = etree.Element('{' + xs + '}schema', nsmap=NSMAP, attrib={
        'targetNamespace': target_namespace,
        'elementFormDefault': 'qualified',
        'attributeFormDefault': 'unqualified',
        'version': '0.01',
        '{' + xml + '}lang': 'en'
    })

    schema.append(etree.Comment(f'Last Updated: {datetime.datetime.today().strftime("%B %d, %Y")}'))

    # import xml namespace
    etree.SubElement(schema, '{' + xs + '}import', attrib={
        'namespace': xml,
        'schemaLocation': 'http://www.w3.org/2001/xml.xsd'
    })

    for d in get_rdf_dict():
        print(d['name'])
        if d['property'] == 'dataProp':
            try:
                schema.append(etree.Comment(f'Definition for {d["name"]}'))
                el = create_data_prop(d, el_type=d['type'])
                schema.append(el)
            except KeyError:
                pass

        elif d['property'] == 'objProp':
            try:

                schema.append(etree.Comment(f'Definition for {d["name"]}'))
                if d['type']:
                    el = create_object_prop(d, el_type=d['type'])
                else:
                    el = create_object_prop(d)
                schema.append(el)
            except KeyError:
                pass
        elif d['property'] == 'attrProp':
            try:
                schema.append(etree.Comment(f'Definition for {d["name"]}'))
                el = create_attribute(d)
                schema.append(el)
            except KeyError:
                pass

    filename_xsd = config.get('Output', 'filename_xsd')
    with open(filename_xsd, 'wb') as f:
        f.write(etree.tostring(schema, pretty_print=True, xml_declaration=True, encoding='UTF-8'))

    sys.stdout.close()
