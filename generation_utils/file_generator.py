from pathlib import Path

import json
import jsonschema
import yaml

from controller_utils.myutils.UT_PCErrorLogging import UT_PCErrorLogging
from controller_utils.precice_struct import PS_PreCICEConfig
from controller_utils.ui_struct.UI_UserInput import UI_UserInput
from .config_generator import ConfigGenerator
from .format_precice_config import PrettyPrinter
from .logger import Logger
from .other_files_generator import OtherFilesGenerator
from .readme_generator import ReadmeGenerator
from .structure_handler import StructureHandler


class FileGenerator:
    def __init__(self, input_file: Path, output_path: Path) -> None:
        """ Class which takes care of generating the content of the necessary files
            :param input_file: Input yaml file that is needed for generation of the precice-config.xml file
            :param output_path: Path to the folder where the _generated/ folder will be placed"""
        self.input_file = input_file
        self.precice_config = PS_PreCICEConfig()
        self.mylog = UT_PCErrorLogging()
        self.user_ui = UI_UserInput()
        self.logger = Logger()
        self.structure = StructureHandler(output_path)
        self.config_generator = ConfigGenerator()
        self.readme_generator = ReadmeGenerator()
        self.other_files_generator = OtherFilesGenerator()
    
    
    def generate_level_0(self) -> None:
        """Fills out the files of level 0 (everything in the root folder)."""
        self.other_files_generator.generate_clean(clean_sh=self.structure.clean)
        self.config_generator.generate_precice_config(self)
        self.readme_generator.generate_readme(self)
    
    def _extract_participants(self) -> list[str] | None:
        """Extracts the participants from the topology.yaml file."""
        try:
            with open(self.input_file, "r") as config_file:
                config = yaml.load(config_file.read(), Loader=yaml.SafeLoader)
                self.logger.info(f"Input YAML file: {self.input_file}")
        except FileNotFoundError:
            self.logger.error(f"Input YAML file {self.input_file} not found.")
            return None
        except Exception as e:
            self.logger.error(f"Error reading input YAML file: {str(e)}")
            return None
        
        # Extract participant names from the new list format
        return [participant['name'] for participant in config.get('participants', [])]
    
    def generate_level_1(self) -> None:
        """Generates the files of level 1 (everything in the generated sub-folders)."""

        participants = self._extract_participants()
        for participant in participants:
            target_participant = self.structure.create_level_1_structure(participant, self.user_ui)
            adapter_config = target_participant[1]
            run_sh = target_participant[2]
            self.other_files_generator.generate_adapter_config(target_participant=participant, adapter_config=adapter_config,
                                                                precice_config=self.structure.precice_config, topology_path=self.input_file)
            self.other_files_generator.generate_run(run_sh)

    def format_precice_config(self) -> None:
        """Formats the generated preCICE configuration file."""
        
        precice_config_path = self.structure.precice_config
        # Create an instance of PrettyPrinter.
        printer = PrettyPrinter(indent='    ', max_width=120)
        # Specify the path to the XML file you want to prettify.
        try:
            printer.prettify_file(precice_config_path)
            self.logger.success(f"Successfully prettified preCICE configuration XML")
        except Exception as prettify_exception:
            self.logger.error("An error occurred during XML prettification: " + str(prettify_exception))
            
    def handle_output(self, args):
        """
        Handle output based on verbose mode and log state
        """
        if not args.verbose:
            if not self.logger.has_errors():
                self.logger.clear_messages()
                # No errors, show success message
                self.logger.success("Everything worked. You can find the generated files at: " + str(self.structure.generated_root))
                # Always show warnings if any exist
                if self.logger.has_warnings():
                    for warning in self.logger.get_warnings():
                        self.logger.warning(warning)
        self.logger.print_all()

    @staticmethod
    def validate_topology(args):
        """Validate the topology.yaml file against the JSON schema."""
        if args.validate_topology:
            with open(Path(__file__).parent.parent / "schemas" / "topology-schema.json") as schema_file:
                schema = json.load(schema_file)
            with open(args.input_file) as input_file:
                data = yaml.load(input_file, Loader=yaml.SafeLoader)
            try:
                jsonschema.validate(instance=data, schema=schema)
            except jsonschema.exceptions.ValidationError as e:
                print(f"Validation of {args.input_file} failed: {e}")
