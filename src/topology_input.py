from pathlib import Path
import yaml
from controller_utils.myutils.UT_PCErrorLogging import UT_PCErrorLogging
from participant import Participant

class TopologyInput:
    """Class to read a topology YAML file and extract the necessary information."""

    def __init__(self):
        self.participants = {}
        self.coupling_type = None
        self.acceleration = None
        self.exchanges = []

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
        self.exchanges = exchanges
        #implicit explicit handling
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
        
        ##Acceleration
        if "acceleration" in etree:
            acceleration = etree["acceleration"]
            if acceleration.get("display_standard_values", "false").lower() not in ['true', 'false']:
                mylog.rep_error(f"Invalid display_standard_values value: {acceleration.get("display_standard_values").lower()}. Must be 'true' or 'false'.")

            if acceleration.get("display_standard_values", "false").lower() == "true":
                self.acceleration = {key: value for key, value in {
                    'name': acceleration.get('name', 'IQN-ILS'),
                    'initial-relaxation': (
                        {'value': acceleration.get('initial-relaxation', {}).get('value', 0.1),
                        'enforce': acceleration.get('initial-relaxation', {}).get('enforce', 'false')}
                        if 'initial-relaxation' in acceleration else None
                    ),
                    'preconditioner': (
                        {'freeze-after': acceleration.get('preconditioner', {}).get('freeze-after', -1),
                        'type': acceleration.get('preconditioner', {}).get('type', None)}
                        if 'preconditioner' in acceleration else None
                    ),
                    'filter': (
                        {'limit': acceleration.get('filter', {}).get('limit', 1e-16),
                        'type': acceleration.get('filter', {}).get('type', None)}
                        if 'filter' in acceleration else None
                    ),
                    'max-used-iterations': acceleration.get('max-used-iterations', None) if 'max-used-iterations' in acceleration else None,
                    'time-windows-reused': acceleration.get('time-windows-reused', None) if 'time-windows-reused' in acceleration else None,
                    'imvj-restart-mode': (
                        {'truncation-threshold': acceleration.get('imvj-restart-mode', {}).get('truncation-threshold', None),
                        'chunk-size': acceleration.get('imvj-restart-mode', {}).get('chunk-size', None),
                        'reused-time-windows-at-restart': acceleration.get('imvj-restart-mode', {}).get('reused-time-windows-at-restart', None),
                        'type': acceleration.get('imvj-restart-mode', {}).get('type', None)}
                        if any(acceleration.get('imvj-restart-mode', {}).values()) else None
                    ),
                    'display_standard_values': acceleration.get('display_standard_values', 'false')
                }.items() if value is not None}

            else:
                self.acceleration = {
                    'name': acceleration.get('name', 'IQN-ILS'),
                    'initial-relaxation': acceleration.get('initial-relaxation', None),
                    'preconditioner': {
                        'freeze-after': acceleration.get('preconditioner', {}).get('freeze-after', None),
                        'type': acceleration.get('preconditioner', {}).get('type', None)
                    } if any(acceleration.get('preconditioner', {}).values()) else None,
                    'initial-relaxation': {
                        'value': acceleration.get('initial-relaxation', {}).get('value', None),
                        'enforce': acceleration.get('initial-relaxation', {}).get('enforce', None)
                    } if any(acceleration.get('initial-relaxation', {}).values()) else None,
                    'filter': {
                        'limit': acceleration.get('filter', {}).get('limit', None),
                        'type': acceleration.get('filter', {}).get('type', None)
                    } if any(acceleration.get('filter', {}).values()) else None,
                    'max-used-iterations': acceleration.get('max-used-iterations', None),
                    'time-windows-reused': acceleration.get('time-windows-reused', None),
                    'imvj-restart-mode': {
                        'truncation-threshold': acceleration.get('imvj-restart-mode', {}).get('truncation-threshold', None),
                        'chunk-size': acceleration.get('imvj-restart-mode', {}).get('chunk-size', None),
                        'reused-time-windows-at-restart': acceleration.get('imvj-restart-mode', {}).get('reused-time-windows-at-restart', None),
                        'type': acceleration.get('imvj-restart-mode', {}).get('type', None)
                    } if any(acceleration.get('imvj-restart-mode', {}).values()) else None,
                    'display_standard_values': acceleration.get('display_standard_values', 'false')
                }



    # def create_coupling_scheme(self, mylog: UT_PCErrorLogging):
    #     """Create a coupling scheme based on the coupling type."""
    #     if self.coupling_type == 'implicit':
    #         self.coupling_scheme = CouplingSchemeImplicit()
    #     elif self.coupling_type == 'explicit':
    #         self.coupling_scheme = CouplingSchemeExplicit()
    #     else:
    #         mylog.rep_error(f"Invalid coupling type: {self.coupling_type}. Must be 'implicit' or 'explicit'.")
    #         self.coupling_scheme = None