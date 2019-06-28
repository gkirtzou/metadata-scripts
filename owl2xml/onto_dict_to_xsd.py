import datetime

from lxml import etree

# dataProp example
from owl2xml.dummy_data import data
from owl2xml.generate_xsd_elements import get_rdf_dict
from xsd.namespaces import ms, xs, xml
from xsd.xsd import Enumeration

NSMAP = {
    'ms': ms,
    'xs': xs,
}

# Create ROOT element "schema"
schema = etree.Element('{' + xs + '}schema', nsmap=NSMAP, attrib={
    'targetNamespace': 'http://w3id.org/meta-share/ms_onto/',
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

    _list_to_child_element_multi(appinfo, data_dict['close_match'], 'closeMatch')
    _list_to_child_element_multi(appinfo, data_dict['exact_match'], 'exactMatch')
    _list_to_child_element_multi(appinfo, data_dict['narrow_match'], 'narrowMatch')
    _list_to_child_element_multi(appinfo, data_dict['broad_match'], 'broadMatch')

    return annotation


def create_data_prop(data, el_type=None):
    if el_type:
        if el_type == 'rdf:langString':
            element_type = 'xs:string'
        else:
            element_type = el_type.replace('xsd', 'xs')
    else:
        element_type = 'xs:string'
    if el_type == 'rdf:langString':
        element = etree.Element('{' + xs + '}element', attrib={'name': data['name'].split(':')[1]
                                                                       +f"_{data['name'].split(':')[0]}"})
    else:
        element = etree.Element('{' + xs + '}element', attrib={'name': data['name'].split(':')[1]
                                                                       +f"_{data['name'].split(':')[0]}",
                                                               'type': element_type})

    _create_annotation(element, data)

    # check if type is rdf:langString and create an extension
    if el_type == 'rdf:langString':
        complex_type = etree.SubElement(element, '{' + xs + '}complexType')
        simple_content = etree.SubElement(complex_type, '{' + xs + '}simpleContent')
        extension = etree.SubElement(simple_content, '{' + xs + '}extension', attrib={'base': 'xs:string'})
        etree.SubElement(extension, '{' + xs + '}attribute',
                         attrib={'ref': 'xml:lang'})
    return element


def create_object_prop(data, el_type=None):
    if data['controlled_vocabulary']:
        element = etree.Element('{' + xs + '}element', attrib={'name': data['name'].split(':')[1]
                                                                       +f"_{data['name'].split(':')[0]}"})
    else:
        element = etree.Element('{' + xs + '}element', attrib={'name': data['name'].split(':')[1]
                                                                       +f"_{data['name'].split(':')[0]}",
                                                               'type': el_type})
    _create_annotation(element, data)

    if data['controlled_vocabulary']:
        # build enumeration block
        simpe_type = etree.SubElement(element, '{' + xs + '}simpleType')
        restriction = etree.SubElement(simpe_type, '{' + xs + '}restriction', attrib={'base': 'xs:string'})
        for cv in data['controlled_vocabulary']:
            enum = Enumeration(cv['identifier']).to_xsd()
            _create_annotation(enum, cv)
            restriction.append(enum)

    return element


for d in get_rdf_dict():
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
            el = create_object_prop(d, el_type=d['type'].split(':')[1])
            schema.append(el)
        except KeyError:
            pass

with open('onto_xsd_output.xsd', 'wb') as f:
    f.write(etree.tostring(schema, pretty_print=True, xml_declaration=True, encoding='UTF-8'))

# print(etree.tostring(schema, pretty_print=True, encoding='unicode'))