#! /usr/bin/env python3

from lxml import etree
import itertools
import argparse
import sys
import io
import shutil

CONVERGENCE_MEASURE_TAGS = ['relative-convergence-measure', 'absolute-convergence-measure', 'absolute-or-relative-convergence-measure']

TOP_LEVEL_ORDER = {
    'data:': 1,
    'mesh': 2,
    'participant': 3,
    'm2n:': 4,
    'coupling-scheme:': 5
}

PARTICIPANT_ORDER = {
    'provide-mesh': 1,
    'receive-mesh': 2,
    'write-data': 3,
    'read-data': 4,
    'mapping:': 5
}

def custom_sort_key(elem, order):
    """
    Custom sorting key for XML elements like top-level-order.
    
    Args:
        elem (etree._Element): XML element to sort
        order (dict): Dictionary mapping prefix to rank
    
    Returns:
        int: Sorting rank for the element
    """
    tag = str(elem.tag)
    # Find the first matching key
    for prefix, rank in order.items():
        if tag.startswith(prefix):
            return rank
    # Dynamically assign the next number for unknown elements
    if not hasattr(custom_sort_key, 'unknown_counter'):
        custom_sort_key.unknown_counter = len(order) + 1
    
    #Add this? Each time an unknown element is encountered, the counter is incremented, giving each unique unknown element a distinct sorting rank.
    # custom_sort_key.unknown_counter += 1

    return custom_sort_key.unknown_counter


def isEmptyTag(element):
    return not element.getchildren()


def isComment(element):
    return isinstance(element, etree._Comment)


def attribLength(element):
    total = 0
    for k, v in element.items():
        # KEY="VALUE"
        total += len(k) + 2 + len(v) + 1
    # spaces in between
    total += len(element.attrib) - 1
    return total


def elementLen(element):
    total = 2  # Open close
    total += len(element.tag)
    if element.attrib:
        total += 1 + attribLength(element)
    if isEmptyTag(element):
        total += 2  # space and slash
    return total


class PrettyPrinter():
    def __init__(self,
                 stream=sys.stdout,
                 indent='  ',
                 maxwidth=100,
                 maxgrouplevel=1):
        self.stream = stream
        self.indent = indent
        self.maxwidth = maxwidth
        self.maxgrouplevel = maxgrouplevel

    def print(self, text=''):
        self.stream.write(text + '\n')

    def sort_attributes(self, element):
        """
        Sort attributes with 'name' always first, then alphabetically.
        
        Args:
            element (etree._Element): XML element whose attributes to sort
        
        Returns:
            list of tuples: Sorted list of (key, value) attribute pairs
        """
        # Get all attributes as a list of tuples
        all_attrs = list(element.items())
        
        # Separate 'name' attribute if it exists
        name_attrs = [attr for attr in all_attrs if attr[0] == 'name']
        other_attrs = sorted([attr for attr in all_attrs if attr[0] != 'name'], key=lambda x: x[0])
        
        # Combine name attributes (if any) with sorted other attributes
        return name_attrs + other_attrs

    def fmtAttrH(self, element):
        """
        Format attributes horizontally with sorted order.
        
        Args:
            element (etree._Element): XML element to format
        
        Returns:
            str: Formatted attribute string
        """
        return " ".join(['{}="{}"'.format(k, v) for k, v in self.sort_attributes(element)])

    def fmtAttrV(self, element, level):
        """
        Format attributes vertically with sorted order.
        
        Args:
            element (etree._Element): XML element to format
            level (int): Indentation level
        
        Returns:
            str: Formatted attribute string
        """
        prefix = self.indent * (level + 1)
        return "\n".join(
            ['{}{}="{}"'.format(prefix, k, v) for k, v in self.sort_attributes(element)]
        )

    def printXMLDeclaration(self, root):
        self.print('<?xml version="{}" encoding="{}" ?>'.format(
            root.docinfo.xml_version, root.docinfo.encoding))

    def printRoot(self, root):
        self.printXMLDeclaration(root)
        self.printElement(root.getroot(), level=0)

    def printTagStart(self, element, level):
        assert (isinstance(element, etree._Element))
        if element.attrib:
            if elementLen(element) + len(self.indent) * level <= self.maxwidth:
                self.print("{}<{} {}>".format(self.indent * level, element.tag,
                                              self.fmtAttrH(element)))
            else:
                self.print("{}<{}".format(self.indent * level, element.tag))
                self.print("{}>".format(self.fmtAttrV(element, level)))
        else:
            self.print("{}<{}>".format(self.indent * level, element.tag))

    def printTagEnd(self, element, level):
        assert (isinstance(element, etree._Element))
        self.print("{}</{}>".format(self.indent * level, element.tag))

    def printTagEmpty(self, element, level):
        assert (isinstance(element, etree._Element))
        if element.attrib:
            if elementLen(element) + len(self.indent) * level <= self.maxwidth:
                self.print("{}<{} {} />".format(self.indent * level,
                                                element.tag,
                                                self.fmtAttrH(element)))
            else:
                self.print("{}<{}".format(self.indent * level, element.tag))
                self.print("{} />".format(self.fmtAttrV(element, level)))
        else:
            self.print("{}<{} />".format(self.indent * level, element.tag))

    def printComment(self, element, level):
        assert (isinstance(element, etree._Comment))
        self.print(self.indent * level + str(element))

    def printElement(self, element, level):
        if isinstance(element, etree._Comment):
            self.printComment(element, level=level)
            return

        if isEmptyTag(element):
            self.printTagEmpty(element, level=level)
        else:
            self.printTagStart(element, level=level)
            self.printChildren(element, level=level + 1)
            self.printTagEnd(element, level=level)

    def printChildren(self, element, level):
        if level > self.maxgrouplevel:
            for child in element.getchildren():
                self.printElement(child, level=level)
            return

        # Sort children based on the predefined order
        sorted_children = sorted(element.getchildren(), key=lambda elem: custom_sort_key(elem, TOP_LEVEL_ORDER))

        last = len(sorted_children)
        for i, group in enumerate(sorted_children, start=1):
            # Special handling for participants to reorder child elements
            if 'participant' in str(group.tag):
                
                # Sort participant's children based on the defined order
                sorted_participant_children = sorted(
                    group.getchildren(), 
                    key=lambda child: custom_sort_key(child, PARTICIPANT_ORDER)
                )
                
                # Separate different types of elements
                mesh_elements = []
                data_elements = []
                mapping_elements = []
                
                for child in sorted_participant_children:
                    if str(child.tag) in ['provide-mesh', 'receive-mesh']:
                        mesh_elements.append(child)
                    elif str(child.tag) in ['write-data', 'read-data']:
                        data_elements.append(child)
                    elif str(child.tag).startswith('mapping:'):
                        mapping_elements.append(child)
                
                # Construct participant tag with attributes
                participant_tag = "<{}".format(group.tag)
                for attr, value in group.items():
                    participant_tag += ' {}="{}"'.format(attr, value)
                participant_tag += ">"
                
                # Print participant opening tag
                self.print(self.indent * level + participant_tag)
                
                # Print mesh elements
                for child in mesh_elements:
                    self.printElement(child, level + 1)
                
                # Add newline between mesh and data
                if mesh_elements and data_elements:
                    self.print()
                
                # Print data elements
                for child in data_elements:
                    self.printElement(child, level + 1)
                
                # Add newline before mapping
                if data_elements and mapping_elements:
                    self.print()
                
                # Print mapping elements with multi-line formatting
                for mapping_elem in mapping_elements:
                    # Check if the mapping element has a basis-function child
                    has_basis_function = any('basis-function:' in str(child.tag) for child in mapping_elem.getchildren())
                    
                    # Print the mapping element
                    if len(mapping_elem.items()) > 2:
                        self.print("{}<{}".format(self.indent * (level + 1), mapping_elem.tag))
                        for k, v in self.sort_attributes(mapping_elem):
                            self.print("{}{}=\"{}\"".format(self.indent * (level + 2), k, v))
                        
                        # Add basis-function child if it exists in the original
                        if has_basis_function:
                            self.print("{}>".format(self.indent * (level + 1)))
                            for child in mapping_elem.getchildren():
                                if 'basis-function:' in str(child.tag):
                                    self.printElement(child, level + 2)
                            self.print("{}</{}>"
                                       .format(self.indent * (level + 1), mapping_elem.tag))
                        else:
                            self.print("{} />".format(self.indent * (level + 1)))
                    else:
                        # Single-line formatting for simple mappings
                        self.printElement(mapping_elem, level + 1)
                
                # Close participant tag
                self.print("{}</participant>".format(self.indent * level))
                
                # Add newline after participant if not the last element
                if i < last:
                    self.print()
                
                continue
            
            # Special handling for coupling-scheme elements
            elif 'coupling-scheme' in str(group.tag):
                # Sort children of coupling-scheme
                sorted_scheme_children = sorted(
                    group.getchildren(),
                    key=lambda child: 0 if str(child.tag) in CONVERGENCE_MEASURE_TAGS else 
                                      1 if str(child.tag) == 'exchange' else 2
                )
                
                # Separate different types of elements
                other_elements = []
                exchange_elements = []
                convergence_elements = []
                acceleration_elements = []
                
                for child in sorted_scheme_children:
                    tag = str(child.tag)
                    if tag == 'exchange':
                        exchange_elements.append(child)
                    elif tag in CONVERGENCE_MEASURE_TAGS:
                        convergence_elements.append(child)
                    elif tag.startswith('acceleration:'):
                        acceleration_elements.append(child)
                    else:
                        other_elements.append(child)
                
                # Print coupling-scheme opening tag
                self.print(self.indent * level + "<{}>".format(group.tag))
                
                # Print initial elements
                initial_elements = [
                    elem for elem in other_elements 
                    if str(elem.tag) in ['participants', 'max-time', 'time-window-size']
                ]
                # Print initial elements first
                for child in initial_elements:
                    self.printElement(child, level + 1)
                    # Remove the printed elements from the list
                    other_elements.remove(child)
                
                if other_elements:
                    if initial_elements:
                        self.print()
                    # Print all other elements
                    for child in other_elements:
                        self.printElement(child, level + 1)
                
                # Print convergence measures
                if convergence_elements:
                    # Add newline before convergence measures if there are initial elements
                    if initial_elements or other_elements:
                        self.print()
                    for conv in convergence_elements:
                        self.printElement(conv, level + 1)
                
                # Print exchanges
                if exchange_elements:
                    if initial_elements or convergence_elements or other_elements:
                        self.print()
                    for exchange in exchange_elements:
                        self.printElement(exchange, level + 1)
                
                # Print acceleration elements
                if acceleration_elements:
                    if exchange_elements or convergence_elements or initial_elements or other_elements:
                        self.print()
                    for child in acceleration_elements:
                        self.printElement(child, level + 1)
                
                # Close coupling-scheme tag
                self.print("{}</{}>"
                    .format(self.indent * level, group.tag))
                
                # Add newline after coupling-scheme if not the last element
                if i < last:
                    self.print()
                
                continue
            
            # Print the element normally
            self.printElement(group, level=level)
            
            # Add an extra newline between top-level groups
            if i < last:
                self.print()


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        'files',
        nargs='+',
        type=str,
        help="The XML configuration files."
    )
    return parser.parse_args()


def parseXML(content):
    p = etree.XMLParser(recover=True,
                        remove_comments=False,
                        remove_blank_text=True)
    return etree.fromstring(content, p).getroottree()


def example():
    return parseXML(open('./BB-sockets-explicit-twoway.xml', 'r').read())


def main():
    args = parse_args()

    modified = False
    failed = False
    for filename in args.files:
        content = None
        try:
            with open(filename, 'rb') as xml_file:
                content = xml_file.read()
        except Exception as e:
            print(f"Unable to open file: \"{filename}\"")
            print(e)
            failed = True
            continue

        xml = None
        try:
            xml = parseXML(content)
        except Exception as e:
            print(f"Error occured while parsing file: \"{filename}\"")
            print(e)
            failed = True
            continue

        buffer = io.StringIO()
        printer = PrettyPrinter(stream=buffer)
        printer.printRoot(xml)

        if buffer.getvalue() != content.decode("utf-8"):
            print(f"Reformatting file: \"{filename}\"")
            modified = True
            with open(filename, "w") as xml_file:
                buffer.seek(0)
                shutil.copyfileobj(buffer, xml_file)

    if failed: return 1

    if modified: return 2

    return 0

if __name__ == '__main__':
    sys.exit(main())