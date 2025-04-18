from pathlib import Path
from generation_utils.StructureHandler import StructureHandler
from generation_utils.Logger import Logger
from controller_utils.ui_struct.UI_UserInput import UI_UserInput
from controller_utils.myutils.UT_PCErrorLogging import UT_PCErrorLogging
from controller_utils.precice_struct import PS_PreCICEConfig
from generation_utils.AdapterConfigGenerator import AdapterConfigGenerator
from generation_utils.format_precice_config import PrettyPrinter
import yaml
import argparse
import jsonschema, json

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

    def _generate_precice_config(self) -> None:
        """Generates the precice-config.xml file based on the topology.yaml file."""

        def is_utf8_encoded(file_path):
            try:
                with open(file_path, 'rb') as f:
                    # Read the first few bytes to check for BOM
                    bom = f.read(3)
                    if bom == b'\xef\xbb\xbf':
                        return False  # File has a BOM, so it's not considered pure UTF-8

                    # Try to decode the rest of the file
                    f.seek(0)  # Go back to the start of the file
                    f.read().decode('utf-8')
                return True
            except UnicodeDecodeError:
                return False

        # Check if the topology YAML file is UTF-8 encoded
        topology_file_path = self.input_file  # Assuming this is the path to your YAML file
        if not is_utf8_encoded(topology_file_path):
            self.logger.error(f"Input YAML file {topology_file_path} is not UTF-8 encoded.")
            return

        # Try to open the yaml file and get the configuration
        try:
            with open(self.input_file, "r") as config_file:
                config = yaml.load(config_file.read(), Loader=yaml.SafeLoader)
                self.logger.info(f"Input YAML file: {self.input_file}")
        except FileNotFoundError:
            self.logger.error(f"Input YAML file {self.input_file} not found.")
            return
        except Exception as e:
            self.logger.error(f"Error reading input YAML file: {str(e)}")
            return

        # Build the ui
        self.logger.info("Building the user input info...")
        self.user_ui.init_from_yaml(config, self.mylog)

        # Generate the precice-config.xml file
        self.logger.info("Generating preCICE config...")
        self.precice_config.create_config(self.user_ui)

        # Set the target of the file and write out to it
        # Warning: self.structure.precice_config is of type Path, so it needs to be converted to str
        target = str(self.structure.precice_config)
        try:
            self.logger.info(f"Writing preCICE config to {target}...")
            self.precice_config.write_precice_xml_config(
            target, self.mylog, sync_mode=self.user_ui.sim_info.sync_mode, mode=self.user_ui.sim_info.mode
        )

        except Exception as e:
            self.logger.error(f"Failed to write preCICE XML config: {str(e)}")
            return

        self.logger.success(f"XML generation completed successfully: {target}")
    
    def _generate_static_files(self, target: Path, name: str) -> None:
        """Generate static files from templates
            :param target: target file path
            :param name: name of the function"""
        try:
            tempalte = Path(__file__).parent / "templates" / f"template_{name}"
            self.logger.info(f"Reading in the template file for {name}")

            # Check if the template file exists
            if not tempalte.exists():
                raise FileNotFoundError(f"Template file not found: {tempalte}")

            # Read the template content
            template_content = tempalte.read_text(encoding="utf-8")

            self.logger.info(f"Writing the template to the target: {str(target)}")

            # Write content to the target file
            with open(target, 'w', encoding="utf-8") as template:
                template.write(template_content)

            self.logger.success(f"Successfully written {name} content to: {str(target)}")

        except FileNotFoundError as fileNotFoundException:
            self.logger.error(f"File not found: {fileNotFoundException}")
        except PermissionError as premissionErrorException:
            self.logger.error(f"Permission error: {premissionErrorException}")
        except Exception as generalExcpetion:
            self.logger.error(f"An unexpected error occurred: {generalExcpetion}")
        pass
    
    def _generate_README(self) -> None:
        """Generates the README.md file with dynamic content based on simulation configuration"""
        # Comprehensive solver documentation links
        SOLVER_DOCS = {
            # CFD Solvers
            'openfoam': 'https://www.openfoam.com/documentation',
            'su2': 'https://su2code.github.io/docs/home/',
            'foam-extend': 'https://sourceforge.net/p/foam-extend/',
            
            # Structural Solvers
            'calculix': 'https://www.calculix.de/',
            'elmer': 'https://www.elmersolver.com/documentation/',
            'code_aster': 'https://www.code-aster.org/V2/doc/default/en/index.php',
            
            # Other Solvers
            'fenics': 'https://fenicsproject.org/docs/',
            'dealii': 'https://dealii.org/current/doxygen/deal.II/index.html',
            
            # Fallback
            'default': 'https://precice.org/adapter-list.html'
        }

        # Read the template README with explicit UTF-8 encoding
        with open(Path(__file__).parent / "templates" / "template_README.md", 'r', encoding='utf-8') as template_file:
            readme_content = template_file.read()

        # Extract participants and their solvers
        participants_list = []
        solvers_list = []
        solver_links = {}
        original_solver_names = {}

        # Ensure participants exist before processing
        if not hasattr(self.user_ui, 'participants') or not self.user_ui.participants:
            self.logger.warning("No participants found. Using default placeholders.")
            participants_list = ["DefaultParticipant"]
            solvers_list = ["DefaultSolver"]
            original_solver_names = {"defaultparticipant": "DefaultSolver"}
        else:
            for participant_name, participant_info in self.user_ui.participants.items():
                # Preserve original solver name
                original_solver_name = getattr(participant_info, 'solverName', 'UnknownSolver')
                solver_name = original_solver_name.lower()
                
                participants_list.append(participant_name)
                solvers_list.append(original_solver_name)
                original_solver_names[participant_name.lower()] = original_solver_name
                
                # Get solver documentation link, use default if not found
                solver_links[solver_name] = SOLVER_DOCS.get(solver_name, SOLVER_DOCS['default'])

        # Determine coupling strategy (you might want to extract this from topology.yaml)
        coupling_strategy = "Partitioned" if len(participants_list) > 1 else "Single Solver"

        # Replace placeholders
        readme_content = readme_content.replace("{PARTICIPANTS_LIST}", "\n  ".join(f"- {p}" for p in participants_list))
        readme_content = readme_content.replace("{SOLVERS_LIST}", "\n  ".join(f"- {s}" for s in solvers_list))
        readme_content = readme_content.replace("{COUPLING_STRATEGY}", coupling_strategy)
        
        # Explicitly replace solver-specific placeholders
        readme_content = readme_content.replace("{SOLVER1_NAME}", solvers_list[0] if solvers_list else "Solver1")
        readme_content = readme_content.replace("{SOLVER2_NAME}", solvers_list[1] if len(solvers_list) > 1 else "Solver2")
        
        # Generate adapter configuration paths for all participants
        adapter_config_paths = []
        
        for participant in participants_list:
            # Find the corresponding solver name for this participant
            solver_name = original_solver_names.get(participant.lower(), 'solver')
            adapter_config_paths.append(f"- **{participant}**: `{participant}-{solver_name}/adapter-config.json`")
        
        # Replace adapter configuration section
        readme_content = readme_content.replace(
            "- **Adapter Configuration**: `{PARTICIPANT_NAME}/adapter-config.json`", 
            "**Adapter Configurations**:\n" + "\n".join(adapter_config_paths)
        )
        
        # Explicitly replace solver links
        readme_content = readme_content.replace(
            "[Link1]", 
            f"[{solvers_list[0] if solvers_list else 'Solver1'}]({solver_links.get(solvers_list[0].lower(), '#') if solvers_list else '#'})"
        )
        readme_content = readme_content.replace(
            "[Link2]", 
            f"[{solvers_list[1] if len(solvers_list) > 1 else 'Solver2'}]({solver_links.get(solvers_list[1].lower(), '#') if len(solvers_list) > 1 else '#'})"
        )

        # Generate comprehensive solver links
        solver_links_section = "**Solvers Links and Names**:\n"
        for solver_name, solver_link in solver_links.items():
            solver_links_section += f"- {original_solver_names.get(solver_name, solver_name.capitalize())}: [{solver_name.upper()}]({solver_link})\n"
        
        # Replace the placeholder with the generated solver links
        readme_content = readme_content.replace("[Solvers Links and Names]", solver_links_section)

        # Write the updated README with UTF-8 encoding
        with open(self.structure.README, 'w', encoding='utf-8') as readme_file:
            readme_file.write(readme_content)

        self.logger.success(f"Generated README at {self.structure.README}")
    
    def _generate_run(self, run_sh: Path) -> None:
        """Generates the run.sh file
            :param run_sh: Path to the run.sh file"""
        self._generate_static_files(target=run_sh,
                                    name="run.sh")

    def _generate_clean(self) -> None:
        """Generates the clean.sh file."""
        self._generate_static_files(target=self.structure.clean,
                                    name="clean.sh")

    def _generate_adapter_config(self, target_participant: str, adapter_config: Path) -> None:
        """Generates the adapter-config.json file."""
        adapter_config_generator = AdapterConfigGenerator(adapter_config_path=adapter_config,
                                                            precice_config_path=self.structure.precice_config, 
                                                            topology_path=self.input_file,  
                                                            target_participant=target_participant)
        adapter_config_generator.write_to_file()
    
    def generate_level_0(self) -> None:
        """Fills out the files of level 0 (everything in the root folder)."""
        self._generate_clean()
        self._generate_precice_config()
        self._generate_README()
    
    def _extract_participants(self) -> list[str]:
        """Extracts the participants from the topology.yaml file."""
        try:
            with open(self.input_file, "r") as config_file:
                config = yaml.load(config_file.read(), Loader=yaml.SafeLoader)
                self.logger.info(f"Input YAML file: {self.input_file}")
        except FileNotFoundError:
            self.logger.error(f"Input YAML file {self.input_file} not found.")
            return
        except Exception as e:
            self.logger.error(f"Error reading input YAML file: {str(e)}")
            return
        
        # Extract participant names from the new list format
        return [participant['name'] for participant in config.get('participants', [])]
    
    def generate_level_1(self) -> None:
        """Generates the files of level 1 (everything in the generated sub-folders)."""

        participants = self._extract_participants()
        for participant in participants:
            target_participant = self.structure.create_level_1_structure(participant, self.user_ui)
            adapter_config = target_participant[1]
            run_sh = target_participant[2]
            self._generate_adapter_config(target_participant=participant, adapter_config=adapter_config)
            self._generate_run(run_sh)

    def format_precice_config(self) -> None:
        """Formats the generated preCICE configuration file."""
        
        precice_config_path = self.structure.precice_config
        # Create an instance of PrettyPrinter.
        printer = PrettyPrinter(indent='    ', maxwidth=120)
        # Specify the path to the XML file you want to prettify.
        try:
            printer.prettify_file(precice_config_path)
            self.logger.success(f"Successfully prettified preCICE configuration XML")
        except Exception as prettifyException:
            self.logger.error("An error occurred during XML prettification: ", prettifyException)
            
        
def main():
    parser = argparse.ArgumentParser(description="Takes topology.yaml files as input and writes out needed files to start the precice.")
    parser.add_argument(
        "-f", "--input-file", 
        type=Path, 
        required=False, 
        help="Input topology.yaml file",
        default=Path("examples/1/topology.yaml")
    )
    parser.add_argument(
        "-o", "--output-path",
        type=Path,
        required=False,
        help="Output path for the generated folder.",
        default=Path(__file__).parent
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        required=False,
        help="Enable verbose logging output.",
    )
    parser.add_argument(
        "--validate-topology",
        action="store_true",
        required=False,
        default=True,
        help="Whether to validate the input topology.yaml file against the preCICE topology schema.",
    )

    args = parser.parse_args()

    fileGenerator = FileGenerator(args.input_file, args.output_path)

    # Clear any previous log state
    fileGenerator.logger.clear_log_state()

    fileGenerator.generate_level_0()
    fileGenerator.generate_level_1()

    # Format the generated preCICE configuration
    fileGenerator.format_precice_config()
    
    fileGenerator.logger.warning("aaa")
    # Handle output based on verbose mode and log state
    if not args.verbose:
        if not fileGenerator.logger.has_errors():
            fileGenerator.logger.clear_messages()
            # No errors, show success message
            fileGenerator.logger.success("Everything worked. You can find the generated files at: " + str(fileGenerator.structure.generated_root))
            # Always show warnings if any exist
            if fileGenerator.logger.has_warnings():
                print("aaaaaaaaaaaaaaaa")
                for warning in fileGenerator.logger.get_warnings():
                    fileGenerator.logger.warning(warning)
            fileGenerator.logger.print_all()
        else:
            fileGenerator.logger.print_all()
    if args.validate_topology:
        with open(Path(__file__).parent / "schemas" / "topology-schema.json") as schema_file:
            schema = json.load(schema_file)
        with open(args.input_file) as input_file:
            data = yaml.load(input_file, Loader=yaml.SafeLoader)
        try:
            jsonschema.validate(instance=data, schema=schema)
        except jsonschema.exceptions.ValidationError as e:
            print(f"Validation of {args.input_file} failed: {e}")
    


if __name__ == "__main__":
    main()
