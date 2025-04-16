import yaml
from pathlib import Path

class ConfigGenerator:
    @staticmethod
    def is_utf8_encoded(file_path):
        """Check if a file is UTF-8 encoded without BOM"""
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

    def generate_precice_config(self, file_generator):
        """Generates the precice-config.xml file based on the topology.yaml file."""
        # Check if the topology YAML file is UTF-8 encoded
        topology_file_path = file_generator.input_file
        logger = file_generator.get_logger()
        
        if not self.is_utf8_encoded(topology_file_path):
            logger.error(f"Input YAML file {topology_file_path} is not UTF-8 encoded.")
            return None

        # Try to open the yaml file and get the configuration
        try:
            with open(topology_file_path, "r") as config_file:
                config = yaml.load(config_file.read(), Loader=yaml.SafeLoader)
                logger.info(f"Input YAML file: {topology_file_path}")
        except FileNotFoundError:
            logger.error(f"Input YAML file {topology_file_path} not found.")
            return None
        except Exception as e:
            logger.error(f"Error reading input YAML file: {str(e)}")
            return None

        # Build the ui
        logger.info("Building the user input info...")
        user_ui = file_generator.get_user_ui()
        user_ui.init_from_yaml(config, file_generator.mylog)

        # Generate the precice-config.xml file
        logger.info("Generating preCICE config...")
        precice_config = file_generator.precice_config
        precice_config.create_config(user_ui)

        # Set the target of the file and write out to it
        structure = file_generator.get_structure()
        target = str(structure.precice_config)
        
        try:
            logger.info(f"Writing preCICE config to {target}...")
            precice_config.write_precice_xml_config(
                target, 
                file_generator.mylog, 
                sync_mode=user_ui.sim_info.sync_mode, 
                mode=user_ui.sim_info.mode
            )
        except Exception as e:
            logger.error(f"Failed to write preCICE XML config: {str(e)}")
            return None

        logger.success(f"XML generation completed successfully: {target}")
        return target