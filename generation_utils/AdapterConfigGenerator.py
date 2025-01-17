from pathlib import Path
from generation_utils.Logger import Logger
from lxml import etree
import json

class AdapterConfigGenerator:
    def __init__(self, adapter_config_path: Path, precice_config_path: Path, target_participant: str) -> None:
        """
        Initializes the AdapterConfigGenerator with paths to the adapter config and precice config.

        Args:
            adapter_config_path (Path): Path to the output adapter-config.json file.
            precice_config_path (Path): Path to the input precice-config.xml file.
        """
        self.adapter_config_path = adapter_config_path
        self.adapter_config_schema_path = Path(__file__).parent.parent / "templates" / "adapter-config-template.json"
        self.logger = Logger()
        self.precice_config_path = precice_config_path
        self.target_participant = target_participant

        # Load the JSON template into a dictionary during initialization
        self.adapter_config_schema = self._load_adapter_schema()

    def _load_adapter_schema(self) -> dict:
        """
        Loads the adapter-config JSON template from the templates directory.

        Returns:
            dict: The adapter configuration schema as a dictionary.
        """
        try:
            with open(self.adapter_config_schema_path, 'r', encoding='utf-8') as adapter_config_template_file:
                adapter_config_schema = json.load(adapter_config_template_file)
            self.logger.info("Retrieved adapter-config template successfully.")
            return adapter_config_schema
        
        except FileNotFoundError:
            self.logger.error(f"Adapter-Config-Schema file doesn't exist at {self.adapter_config_schema_path}")

        except json.JSONDecodeError as jsonDecodeError:
            self.logger.error(f"Error decoding JSON from the adapter-config template: {jsonDecodeError}")
            raise

    def _get_generated_precice_config(self):
        """
        Parses the precice-config.xml file, removes namespaces, and stores the root element.
        """
        try:
            with open(self.precice_config_path, 'r', encoding='utf-8') as precice_config_file:
                precice_config = precice_config_file.read()
        except FileNotFoundError:
            self.logger.error(f"PreCICE config file not found at {self.precice_config_path}")
            raise

        # Parse with lxml and clean namespaces
        parser = etree.XMLParser(ns_clean=True, recover=True)
        try:
            doc = etree.fromstring(precice_config.encode('utf-8'), parser=parser)
        except etree.XMLSyntaxError as e:
            self.logger.error(f"Error parsing XML: {e}")
            raise

        # Strip namespace prefixes from tags
        for elem in doc.iter():
            if isinstance(elem.tag, str) and '}' in elem.tag:
                elem.tag = elem.tag.split('}', 1)[1]

        self.root = doc
        self.logger.info("Parsed precice-config.xml successfully.")

    def _fill_out_adapter_schema(self):
        """
        Fills out the adapter configuration schema based on the precice-config.xml data.
        """
        self._get_generated_precice_config()

        participant_elem = None
        for participant in self.root.findall(".//participant"):
            if participant.get("name") == self.target_participant:
                participant_elem = participant
                break

        if participant_elem is None:
            self.logger.error(f"Participant '{self.target_participant}' not found in precice-config.xml.")
            return

        # Attempt to find read-data and write-data elements
        read_data_elem = participant_elem.find("read-data")
        write_data_elem = participant_elem.find("write-data")

        # Log warnings if certain elements are missing
        if read_data_elem is None:
            self.logger.warning(f"Participant '{self.target_participant}' is missing a 'read-data' element.")
        if write_data_elem is None:
            self.logger.warning(f"Participant '{self.target_participant}' is missing a 'write-data' element.")

        # Update the adapter_config_schema dictionary according to the new template
        self.adapter_config_schema["participant_name"] = self.target_participant

        # Access the first interface in the interfaces list
        interface_dict = self.adapter_config_schema["interfaces"][0]

        # Initialize write_data_names and read_data_names lists
        interface_dict["write_data_names"] = []
        interface_dict["read_data_names"] = []

        # If read_data_elem exists, set mesh_name and read_data_names
        if read_data_elem is not None:
            interface_dict["mesh_name"] = read_data_elem.get("mesh_name")
            read_data_name = read_data_elem.get("name")
            if read_data_name:
                interface_dict["read_data_names"].append(read_data_name)

        # If write_data_elem exists, set write_data_names
        if write_data_elem is not None:
            write_data_name = write_data_elem.get("name")
            if write_data_name:
                interface_dict["write_data_names"].append(write_data_name)

        # Remove keys if their lists are empty
        if not interface_dict["write_data_names"]:
            interface_dict.pop("write_data_names")
        if not interface_dict["read_data_names"]:
            interface_dict.pop("read_data_names")

        self.logger.info("Adapter configuration schema filled out successfully.")


        
    def write_to_file(self) -> None:
        """
        Writes the filled adapter configuration schema to the specified JSON file.
        """
        self._fill_out_adapter_schema()

        try:
            with open(self.adapter_config_path, 'w', encoding='utf-8') as adapter_config_file:
                json.dump(self.adapter_config_schema, adapter_config_file, indent=4)
            self.logger.success(f"Adapter configuration written to {self.adapter_config_path}")
        except IOError as e:
            self.logger.error(f"Failed to write adapter configuration to file: {e}")
            raise
