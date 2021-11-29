from lxml import etree

from owl2xml.xsd.namespaces import xs


class XSDBlock:
    namespace = xs

    @staticmethod
    def prefix(block_type):
        return '{' + xs + '}' + block_type


class AppInfo(XSDBlock):
    def __init__(self, **children):
        for c in children.values():
            print(c)
            assert isinstance(c, list)
        print(children)


class Documentation(XSDBlock):
    pass


class Annotation(XSDBlock):
    app_info = None
    documentation = None

    def __init__(self, app_info: AppInfo = None, documentation: Documentation = None):
        self.app_info = app_info
        self.documentation = documentation

    def to_xsd(self, raw=False):
        element = etree.Element(self.prefix('annotation'))
        if self.documentation:
            etree.SubElement(element, self.prefix('documentation'))
        if not raw:
            return element
        return etree.tostring(element, pretty_print=True, encoding='unicode')


class Enumeration(XSDBlock):
    name = None
    annotation = None
    value = None

    def __init__(self, value, annotation: Annotation = None):
        self.value = value
        self.annotation = annotation

    def to_xsd(self, raw=False):
        element = etree.Element(self.prefix('enumeration'), attrib={'value': self.value})
        if self.annotation:
            etree.SubElement(element, self.prefix('annotation'))
        if not raw:
            return element
        return etree.tostring(element, pretty_print=True, encoding='unicode')
