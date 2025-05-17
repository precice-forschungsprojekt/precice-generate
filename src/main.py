from precice_config import PreciceConfig
from topology_input import TopologyInput
from participant import Participant
from mesh import Mesh
from controller_utils.myutils.UT_PCErrorLogging import UT_PCErrorLogging
import yaml
from pathlib import Path


def generate_precice_config(topology_file: str, output_file: str):
    """
    Main function to generate preCICE configuration from topology file.
    
    Args:
        topology_file: Path to the topology YAML file
        output_file: Path where the preCICE XML configuration will be saved
    """
    # Initialize error logging
    log = UT_PCErrorLogging()
    
    try:
        # Create topology input handler
        topology = TopologyInput()
        
        # Read and process topology file
        with open(topology_file, 'r') as f:
            topology_yaml = yaml.safe_load(f)
            topology.create_etree(topology_yaml, log)
        
        # Create preCICE configuration
        config = PreciceConfig()
        config.topology = topology
        
        # Initialize participants
        config.init_participants()
        
        # Write preCICE XML configuration
        config.write_precice_xml_config(output_file, log)
        
        if log.has_errors():
            print("\nErrors occurred during configuration generation:")
            for error in log.get_errors():
                print(f"- {error}")
            return False
            
        print(f"Successfully generated preCICE configuration at: {output_file}")
        return True
        
    except Exception as e:
        # log.rep_error(f"Error during configuration generation: {str(e)}")
        print(f"Error during configuration generation: {str(e)}")
        return False


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate preCICE configuration from topology YAML")
    parser.add_argument("-i", "--input", required=False, help="Path to topology YAML file", default=Path("examples/5/topology.yaml"))
    parser.add_argument("-o", "--output", required=False, help="Path to output XML configuration file", default=Path(__file__).parent)
    
    args = parser.parse_args()
    
    success = generate_precice_config(args.input, args.output)
    exit(0 if success else 1)