import sys
from pathlib import Path
import pytest
import yaml
import json
import jsonschema
import os


def _get_examples():
    """Get the list of examples as ints in the examples directory"""
    root = Path(__file__).parent.parent.parent
    examples_dir = root / "controller_utils" / "examples"
    return sorted([example.name for example in examples_dir.iterdir() if example.is_dir()])


def _normalize_xml_line(line):
    """
    Normalize an XML line by removing extra whitespaces while preserving structure.
    
    Args:
        line (str): Input XML line
    
    Returns:
        str: Normalized XML line
    """
    # Remove trailing whitespaces from the content
    stripped_line = line.rstrip()
    
    # Normalize self-closing tags
    stripped_line = stripped_line.replace(' />', '/>')
    
    return stripped_line


def _sort_xml_elements(file_path):
    """
    Sort XML elements with the same name by their first common attribute value alphabetically.
    
    Args:
        file_path (Path): Path to the XML file to be sorted
    
    Returns:
        str: Sorted and prettified XML content
    """
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Split the content into lines and normalize
    lines = [_normalize_xml_line(line) for line in content.split('\n')]
    
    # Separate XML declaration, comments, and root element
    xml_declaration = [line for line in lines if line.strip().startswith('<?xml')]
    comments = [line for line in lines if line.strip().startswith('<!--')]
    
    # Remove XML declaration, comments, and empty lines
    content_lines = [line for line in lines if line.strip() 
                     and not line.strip().startswith('<?xml') 
                     and not line.strip().startswith('<!--')]
    
    # Group elements by their tag and depth
    element_groups = {}
    
    for line in content_lines:
        # Calculate depth based on parent tag's depth
        stripped = line.strip()
        is_opening = stripped.startswith('<') and not stripped.startswith('</')
        is_closing = stripped.startswith('</')
        is_self_closing = stripped.endswith('/>')
        
        if is_opening or is_self_closing:
            # Extract tag name and attributes
            tag_end = stripped.find(' ') if ' ' in stripped else stripped.find('>')
            tag = stripped[1:tag_end]
            
            # Extract first attribute if exists
            first_attr_value = ''
            if ' ' in stripped:
                attrs = stripped[stripped.find(' ')+1:stripped.find('>')].split()
                if attrs:
                    first_attr = attrs[0]
                    if '=' in first_attr:
                        first_attr_value = first_attr.split('=')[1].strip('"\'')
            
            # Group elements
            if tag not in element_groups:
                element_groups[tag] = []
            
            element_groups[tag].append({
                'full_line': line,
                'first_attr_value': first_attr_value
            })
    
    # Sort elements within each group
    sorted_content = []
    for tag, elements in element_groups.items():
        # Sort elements by their first attribute value
        sorted_elements = sorted(elements, key=lambda x: x['first_attr_value'])
        
        # Replace original group with sorted group
        sorted_content.extend([elem['full_line'] for elem in sorted_elements])
    
    # Reconstruct the XML with sorted elements
    final_content = '\n'.join(xml_declaration + comments + sorted_content)
    
    return final_content


def _compare_formatted_files(original_file, generated_file):
    """
    Compare two files line by line, removing empty lines and sorting XML elements.
    
    Args:
        original_file (Path): Path to the original file
        generated_file (Path): Path to the generated file
    
    Raises:
        AssertionError: If files do not match line by line
    """
    # Sort XML elements for both files
    sorted_original = _sort_xml_elements(original_file)
    sorted_generated = _sort_xml_elements(generated_file)
    
    # Read sorted content and normalize lines
    original_lines = [_normalize_xml_line(line) for line in sorted_original.split('\n') if line.strip()]
    generated_lines = [_normalize_xml_line(line) for line in sorted_generated.split('\n') if line.strip()]
    
    # Compare line by line, ignoring whitespace
    for orig_line, gen_line in zip(original_lines, generated_lines):
        # Remove all whitespace for comparison
        orig_line_stripped = ''.join(orig_line.split())
        gen_line_stripped = ''.join(gen_line.split())

        print(orig_line_stripped)
        print(gen_line_stripped)
        print()
        
        assert orig_line_stripped == gen_line_stripped, \
            f"Mismatch:\nOriginal: {orig_line}\nGenerated: {gen_line}"
    
    # Ensure same number of lines
    assert len(original_lines) == len(generated_lines), \
        f"Different number of lines. Original: {len(original_lines)}, Generated: {len(generated_lines)}"


@pytest.mark.parametrize("example_nr", _get_examples())
def test_generate(capsys, example_nr):
    root = Path(__file__).parent.parent.parent
    sys.path.append(str(root))
    from FileGenerator import FileGenerator

    # Load JSON schema
    schema_path = root / "schemas" / "topology-schema.json"
    with open(schema_path, 'r') as schema_file:
        topology_schema = json.load(schema_file)

    # Use example_nr for 8 examples
    topology_file = root / "controller_utils" / "examples" / f"{example_nr}" / "topology.yaml"
    output_path = root
    
    # Validate topology file against JSON schema
    with open(topology_file, 'r') as file:
        topology_data = yaml.safe_load(file)
    
    try:
        # Validate against JSON schema
        jsonschema.validate(instance=topology_data, schema=topology_schema)
    except jsonschema.ValidationError as validation_error:
        pytest.fail(f"Topology file {topology_file} failed schema validation: {validation_error}")

    fileGenerator = FileGenerator(topology_file, output_path)

    # Capture and test output of generate_level_0
    fileGenerator.generate_level_0()
    captured = capsys.readouterr()
    assert "error" not in captured.out.lower() and "error" not in captured.err.lower(), \
        f"Error in {str(topology_file)}"

    # Capture and test output of generate_level_1
    fileGenerator.generate_level_1()
    captured = capsys.readouterr()
    assert "error" not in captured.out.lower() and "error" not in captured.err.lower(), \
        f"Error in {str(topology_file)}"

    # Capture and test output of format_precice_config
    fileGenerator.format_precice_config()
    captured = capsys.readouterr()
    assert "error" not in captured.out.lower() and "error" not in captured.err.lower(), \
        f"Error in {str(topology_file)}"

    # New: Compare generated files
    generated_precice_config = root / "_generated" / "precice-config.xml"
    original_precice_config = root / "controller_utils" / "examples" / f"{example_nr}" / "precice-config.xml"
    
    if original_precice_config.exists():
        _compare_formatted_files(original_precice_config, generated_precice_config)
