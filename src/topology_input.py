from pathlib import Path
import yaml
from controller_utils.myutils.UT_PCErrorLogging import UT_PCErrorLogging
from participant import Participant

class TopologyInput:
    """Class to read a topology YAML file and extract the necessary information."""

    def __init__(self):
        self.participants = {}
        self.coupling_type = None

    def create_etree(self, etree, mylog: UT_PCErrorLogging) -> dict:
        """Create a etreeuration dictionary from the topology YAML file."""
        #errors if not found
        if not "coupling-scheme" in etree:
            mylog.rep_error("No coupling-scheme found in the topology YAML file.")
        if not "participants" in etree:
            mylog.rep_error("No participants found in the topology YAML file.")
        if not "exchanges" in etree:
            mylog.rep_error("No exchanges found in the topology YAML file.")

        coupling_scheme = etree["coupling-scheme"]
        participants = etree["participants"]
        exchanges = etree["exchanges"]

        if "acceleration" in etree:
            acceleration = etree["acceleration"]


        ##Coupling scheme
        self.sim_info.coupling = coupling_scheme.get("coupling", "parallel") #independent of standard value
        #standard value handling
        if coupling_scheme.get('display_standard_values', 'false').lower() == 'true':
            # mylog.rep_info("Display standard values is enabled.")            
            self.max_time = coupling_scheme.get("max-time")
            self.time_window_size = coupling_scheme.get("time-window-size")
            self.max_iterations = coupling_scheme.get("max-iterations")
        else:
            self.max_time = coupling_scheme.get("max-time", str(1e-3))
            self.time_window_size = coupling_scheme.get("time-window-size", str(1e-3))
            self.max_iterations = coupling_scheme.get("max-iterations", 50)

        ##Participants
        for participant in participants:
            new_participant = Participant()
    
            if isinstance(participant, dict):                
                if name is None:
                    mylog.rep_error(f"Participant missing 'name' key: {participant}")
                    break
                
                new_participant.name = participant.get("name")
                new_participant.solver = participant.get("solver")
                new_participant.dimensionality = participant.get("dimensionality", 3)
            
            else:
                # Unsupported format
                mylog.rep_error(f"Unsupported participant configuration: {participant}")
                break

            # self.participants[new_participant.name] = new_participant

        ##Exchanges
        exchange_types = [exchange.get('type') for exchange in exchanges if 'type' in exchange]
        if exchange_types:
            # If all types are the same, set that as the coupling type
            if len(set(exchange_types)) == 1:
                if exchange_types[0] == 'strong' or exchange_types[0] == 'weak':
                    self.coupling_type = exchange_types[0]
                else:
                    mylog.rep_error(f"Invalid exchange type: {exchange_types[0]}. Must be 'strong' or 'weak'.")
                    self.coupling_type = None
            else:
                # Mixed types, default to weak
                #mylog.rep_error("Mixed exchange types detected. Defaulting to 'weak'.")
                self.coupling_type = 'weak'
        #Convert to implicit or explicit
        if self.coupling_type == 'strong':
            self.coupling_type = 'implicit'
        elif self.coupling_type == 'weak':
            self.coupling_type = 'explicit'