from pathlib import Path
from generation_utils.logger import Logger
from generation_utils.adapter_config_generator import AdapterConfigGenerator

class OtherFilesGenerator:
    def __init__(self, logger: Logger = None):
        """
        Initialize OtherFilesGenerator with optional logger.
        
        :param logger: Optional Logger instance. If not provided, a new Logger will be created.
        """
        self.logger = logger or Logger()

    def _generate_static_files(self, target: Path, name: str) -> None:
        """Generate static files from templates
            :param target: target file path
            :param name: name of the function"""
        try:
            template = Path(__file__).parent.parent / "templates" / f"template_{name}"
            self.logger.info(f"Reading in the template file for {name}")

            # Check if the template file exists
            if not template.exists():
                raise FileNotFoundError(f"Template file not found: {template}")

            # Read the template content
            template_content = template.read_text(encoding="utf-8")

            self.logger.info(f"Writing the template to the target: {str(target)}")

            # Write content to the target file
            with open(target, 'w', encoding="utf-8") as template:
                template.write(template_content)

            self.logger.success(f"Successfully written {name} content to: {str(target)}")

        except FileNotFoundError as fileNotFoundException:
            self.logger.error(f"File not found: {fileNotFoundException}")
        except PermissionError as permissionErrorException:
            self.logger.error(f"Permission error: {permissionErrorException}")
        except Exception as generalException:
            self.logger.error(f"An unexpected error occurred: {generalException}")

    def generate_run(self, run_sh: Path) -> None:
        """Generates the run.sh file
            :param run_sh: Path to the run.sh file"""
        self._generate_static_files(target=run_sh, name="run.sh")

    def generate_clean(self, clean_sh: Path) -> None:
        """Generates the clean.sh file.
            :param clean_sh: Path to the clean.sh file"""
        self._generate_static_files(target=clean_sh, name="clean.sh")

    def generate_adapter_config(self, adapter_config: Path, precice_config: Path, topology_path: Path, target_participant: str) -> None:
        """Generates the adapter-config.json file.
        
        :param adapter_config: Path to the output adapter-config.json file
        :param precice_config: Path to the precice-config.xml file
        :param topology_path: Path to the topology YAML file
        :param target_participant: Name of the target participant
        """
        adapter_config_generator = AdapterConfigGenerator(
            adapter_config_path=adapter_config,
            precice_config_path=precice_config, 
            topology_path=topology_path,  
            target_participant=target_participant
        )
        adapter_config_generator.write_to_file()