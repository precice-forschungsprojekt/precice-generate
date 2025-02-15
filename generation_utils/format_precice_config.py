#!/usr/bin/env python3
from lxml import etree
import itertools
import sys
import io
import shutil

# Global list of valid convergence measure tags
CONVERGENCE_MEASURE_TAGS = [
    'relative-convergence-measure', 
    'absolute-convergence-measure', 
    'absolute-or-relative-convergence-measure'
]

# Global constant for element sorting order
ELEMENT_ORDER = {
    'data:vector': 1,
    'mesh': 2,
    'participant': 3,
    'm2n:sockets': 4,
    'coupling-scheme:': 5
}

def custom_sort_key(elem):
    """
    Custom sorting key for top-level XML elements.
    
    Args:
        elem (etree._Element): XML element to sort
    
    Returns:
        int: Sorting rank for the element
    """
    tag = str(elem.tag)
    # Find the first matching key
    for prefix, rank in ELEMENT_ORDER.items():
        if tag == prefix:
            return rank
    
    # Dynamically assign the next number for unknown elements
    if not hasattr(custom_sort_key, 'unknown_counter'):
        custom_sort_key.unknown_counter = len(ELEMENT_ORDER) + 1
    
    #Add this? Each time an unknown element is encountered, the counter is incremented, giving each unique unknown element a distinct sorting rank.
    # custom_sort_key.unknown_counter += 1

    return custom_sort_key.unknown_counter

def isEmptyTag(element):
    """
    Check if an XML element is empty (has no children).
    """
    return not element.getchildren()

def isComment(element):
    """
    Check if the given element is an XML comment.
    """
    return isinstance(element, etree._Comment)

def attribLength(element):
    """
    Calculate the total length of the attributes in an element.
    For each attribute, count the key, quotes, equals sign, and value.
    """
    total = 0
    for k, v in element.items():
        # Format: key="value"
        total += len(k) + 2 + len(v) + 1
    # Add spaces between attributes (if more than one attribute exists)
    total += len(element.attrib) - 1
    return total

def elementLen(element):
    """
    Estimate the length of an element's start tag (including its attributes).
    This is used to decide whether to print attributes inline or vertically.
    """
    total = 2  # For the angle brackets "<" and ">"
    total += len(element.tag)
    if element.attrib:
        total += 1 + attribLength(element)
    if isEmptyTag(element):
        total += 2  # For the space and slash in an empty tag "<tag />"
    return total

class PrettyPrinter():
    """
    Class to handle the prettification of XML content.
    This class not only provides methods for printing XML elements
    in a prettified format, but also methods to parse and reformat
    an XML file directly.
    """
    def __init__(self, stream=sys.stdout, indent='  ', maxwidth=100, maxgrouplevel=1):
        self.stream = stream      # Output stream (can be a file, StringIO, etc.)
        self.indent = indent      # String used for indentation (2 spaces)
        self.maxwidth = maxwidth  # Maximum width for a single line
        self.maxgrouplevel = maxgrouplevel  # Maximum depth to group elements on one line
        self.global_newline_between_groups = True  # Add newline between top-level groups
        
        # Specific ordering for top-level elements
        self.top_level_order = [
            'data:vector',
            'mesh',
            'participant',
            'm2n:sockets',
            'coupling-scheme:'
        ]

    def print(self, text='', end='\n'):
        """
        Write text to the output stream with optional end character.
        """
        self.stream.write(text + end)

    def fmtAttrH(self, element):
        """
        Format element attributes for inline (horizontal) display.
        """
        return " ".join(['{}="{}"'.format(k, v) for k, v in element.items()])

    def fmtAttrV(self, element, level):
        """
        Format element attributes for vertical display, with indentation.
        """
        prefix = self.indent * (level + 1)
        return "\n".join(['{}{}="{}"'.format(prefix, k, v) for k, v in element.items()])

    def printXMLDeclaration(self, root):
        """
        Print the XML declaration at the beginning of the file.
        """
        self.print('<?xml version="{}" encoding="{}"?>'.format(
            root.docinfo.xml_version, root.docinfo.encoding))

    def printRoot(self, root):
        """
        Print the entire XML document starting from the root element.
        """
        self.printXMLDeclaration(root)
        self.print()  # Add an extra newline after XML declaration
        self.printElement(root.getroot(), level=0)

    def printTagStart(self, element, level):
        """
        Print the start tag of an element with precise formatting.
        """
        assert isinstance(element, etree._Element)
        # Always use self-closing tags for empty elements
        if not element.getchildren() and element.attrib:
            self.print("{}<{} {}/>".format(self.indent * level, element.tag, self.fmtAttrH(element)))
        elif not element.getchildren():
            self.print("{}<{} />".format(self.indent * level, element.tag))
        else:
            # For non-empty elements, use traditional open/close tags
            if element.attrib:
                self.print("{}<{} {}>".format(self.indent * level, element.tag, self.fmtAttrH(element)))
            else:
                self.print("{}<{}>".format(self.indent * level, element.tag))

    def printTagEnd(self, element, level):
        """
        Print the end tag of an element.
        """
        assert isinstance(element, etree._Element)
        # Only print end tag for non-empty elements
        if element.getchildren():
            self.print("{}</{}>".format(self.indent * level, element.tag))

    def printTagEmpty(self, element, level):
        """
        Print an empty element with precise self-closing tag formatting.
        """
        assert isinstance(element, etree._Element)
        if element.attrib:
            self.print("{}<{} {}/>".format(self.indent * level, element.tag, self.fmtAttrH(element)))
        else:
            self.print("{}<{} />".format(self.indent * level, element.tag))

    def printComment(self, element, level):
        """
        Print an XML comment.
        """
        assert isinstance(element, etree._Comment)
        self.print(self.indent * level + str(element))

    def printElement(self, element, level):
        """
        Recursively print an XML element and its children in prettified format.
        """
        # If the element is a comment, print it and return.
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
        sorted_children = sorted(element.getchildren(), key=custom_sort_key)

        last = len(sorted_children)
        for i, group in enumerate(sorted_children, start=1):
            # Special handling for participants to reorder child elements
            if 'participant' in str(group.tag):
                # Define order for participant child elements with more generalized matching
                participant_order = {
                    'provide-mesh': 1,
                    'receive-mesh': 2,
                    'write-data': 3,
                    'read-data': 4,
                    'mapping:': 5  # Matches mapping:nearest-neighbor, mapping:rbf, etc.
                }
                
                # Sort participant's children based on the defined order
                sorted_participant_children = sorted(
                    group.getchildren(), 
                    key=lambda child: next(
                        (rank for prefix, rank in participant_order.items() 
                         if str(child.tag).startswith(prefix)), 
                        6  # Unknown elements appear last
                    )
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
                    # Check if the mapping element has multiple attributes
                    if len(mapping_elem.items()) > 2:
                        self.print("{}<{}".format(self.indent * (level + 1), mapping_elem.tag))
                        for k, v in mapping_elem.items():
                            self.print("{}{}=\"{}\"".format(self.indent * (level + 2), k, v))
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
                    elif tag.startswith('acceleration'):
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
                for child in initial_elements:
                    self.printElement(child, level + 1)
                    other_elements.remove(child)

                if initial_elements:
                    self.print()
                    # Print all other elements
                    for child in other_elements:
                        self.printElement(child, level + 1)
                
                # Print convergence measures
                if convergence_elements:
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
                    if exchange_elements or convergence_elements or other_elements or initial_elements:
                        self.print()
                    for child in acceleration_elements:
                        self.printElement(child, level + 1)
                
                # Close coupling-scheme tag
                self.print("{}</{}>".format(self.indent * level, group.tag))
                
                # Add newline after coupling-scheme if not the last element
                if i < last:
                    self.print()
                
                continue
            
            # Print the element normally
            self.printElement(group, level=level)
            
            # Add an extra newline between top-level groups
            if i < last:
                self.print()

    @staticmethod
    def parse_xml(content):
        """
        Parse XML content into an lxml ElementTree, with recovery and whitespace cleanup.
        
        Parameters:
          content (bytes): The XML content in bytes.
        
        Returns:
          An lxml ElementTree object.
        """
        parser = etree.XMLParser(recover=True, remove_comments=False, remove_blank_text=True)
        return etree.fromstring(content, parser).getroottree()

    def prettify_file(self, file_path):
        """
        Prettify the XML file at the given path and overwrite the file with the prettified content.

        Parameters:
          file_path (str): Path to the XML file.
        
        Returns:
          bool: True if the file was processed (even if no changes were made), False if an error occurred.
        """
        try:
            # Open and read the file as bytes.
            with open(file_path, 'rb') as xml_file:
                content = xml_file.read()
        except Exception as e:
            print(f"Unable to open file: \"{file_path}\"")
            print(e)
            return False

        try:
            # Parse the XML content using the static method.
            xml_tree = PrettyPrinter.parse_xml(content)
        except Exception as e:
            print(f"Error occurred while parsing file: \"{file_path}\"")
            print(e)
            return False

        # Create an in-memory text stream to hold the prettified XML.
        buffer = io.StringIO()
        # Use a temporary PrettyPrinter instance with the buffer as output.
        temp_printer = PrettyPrinter(stream=buffer, indent=self.indent,
                                     maxwidth=self.maxwidth, maxgrouplevel=self.maxgrouplevel)
        temp_printer.printRoot(xml_tree)

        # Get the prettified content from the buffer.
        new_content = buffer.getvalue()
        # Compare with the original content (decoded from bytes).
        if new_content != content.decode("utf-8"):
            try:
                # Overwrite the original file with the prettified content.
                with open(file_path, "w") as xml_file:
                    buffer.seek(0)
                    shutil.copyfileobj(buffer, xml_file)
            except Exception as e:
                print(f"Failed to write prettified content to file: \"{file_path}\"")
                print(e)
                return False
        else:
            print(f"No changes required for file: \"{file_path}\"")
        return True
