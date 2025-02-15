import sys
from pathlib import Path
import pytest
import yaml
import json
import jsonschema
import os
import io
from lxml import etree
from generation_utils.format_precice_config import PrettyPrinter


def _get_examples():
    """Get the list of examples as ints in the examples directory"""
    root = Path(__file__).parent.parent.parent
    examples_dir = root / "controller_utils" / "examples"
    return sorted([example.name for example in examples_dir.iterdir() if example.is_dir()])


def _compare_formatted_files(original_file, generated_file):
    """
    Compare two files after formatting, removing empty lines.
    
    Args:
        original_file (Path): Path to the original file
        generated_file (Path): Path to the generated file
    
    Raises:
        AssertionError: If files do not match line by line after formatting
    """
    # Create a PrettyPrinter with a StringIO stream for capturing output
    pretty_printer = PrettyPrinter(stream=io.StringIO(), indent='  ', maxwidth=100)
    
    # Parse and format original file
    original_tree = etree.parse(str(original_file))
    pretty_printer.stream.seek(0)
    pretty_printer.stream.truncate()
    pretty_printer.printRoot(original_tree)
    formatted_original = pretty_printer.stream.getvalue()
    
    # Parse and format generated file
    generated_tree = etree.parse(str(generated_file))
    pretty_printer.stream.seek(0)
    pretty_printer.stream.truncate()
    pretty_printer.printRoot(generated_tree)
    formatted_generated = pretty_printer.stream.getvalue()
    
    # Remove empty lines from both
    original_lines = [line.strip() for line in formatted_original.split('\n') if line.strip()]
    generated_lines = [line.strip() for line in formatted_generated.split('\n') if line.strip()]
    
    # Compare line by line
    for orig_line, gen_line in zip(original_lines, generated_lines):
        assert orig_line == gen_line, f"Mismatch:\nOriginal: {orig_line}\nGenerated: {gen_line}"
    
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
