from controller_utils.ui_struct.UI_SimulationInfo import UI_SimulationInfo
from controller_utils.ui_struct.UI_Participant import UI_Participant
from controller_utils.ui_struct.UI_Coupling import UI_Coupling
from controller_utils.myutils.UT_PCErrorLogging import UT_PCErrorLogging
from controller_utils.ui_struct.UI_Coupling import UI_CouplingType


class UI_UserInput(object):
    """
    This class represents the main object that contains either one YAML file
    or a user input through a GUI

    The main components are:
     - the list of participants
     - general simulation informations
    """
    def __init__(self):
        """The constructor, dummy initialization of the fields"""
        self.participants = {} # empty participants stored as a dictionary
        self.couplings = []    # empty coupling list
        self.coupling_type = None
        self.acceleration = None
        self.exchanges = []
        self.data_from_exchanges = []
        pass

    def init_from_yaml(self, etree, mylog: UT_PCErrorLogging):
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
        self.coupling = coupling_scheme.get("coupling", "parallel") #independent of standard value
        #standard value handling
        if coupling_scheme.get('display_standard_values', 'false'):
            self.max_time = coupling_scheme.get("max-time", str(1e-3))
            self.time_window_size = coupling_scheme.get("time-window-size", str(1e-3))
            self.max_iterations = coupling_scheme.get("max-iterations", 50)
        else:          
            self.max_time = coupling_scheme.get("max-time")
            self.time_window_size = coupling_scheme.get("time-window-size")
            self.max_iterations = coupling_scheme.get("max-iterations")

        ##Participants
        for participant in participants:
            if isinstance(participant, dict):                
                if participant.get("name") is None:
                    mylog.rep_error(f"Participant missing 'name' key: {participant}")
                    break
                new_participant = UI_Participant()
                new_participant.name = participant.get("name")
                new_participant.solverName = participant.get("solver")
                new_participant.dimensionality = participant.get("dimensionality", 3)
            else:
                # Unsupported format
                mylog.rep_error(f"Unsupported participant configuration: {participant}")
                break

            new_participant.list_of_couplings = []
            self.participants[new_participant.name] = new_participant

        ##Exchanges
        self.exchanges = exchanges
        for exchange in self.exchanges:
            data_key = exchange.get("data")
            data_type = exchange.get("data-type")
            self.data_from_exchanges.append((data_key, data_type))

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
            if acceleration.get("display_standard_values").lower() not in ['true', 'false']:
                mylog.rep_error("Invalid display_standard_values value: " + acceleration.get("display_standard_values").lower() + ". Must be 'true' or 'false'.")
                # print("Invalid display_standard_values value: " + acceleration.get("display_standard_values").lower() + ". Must be 'true' or 'false'.")

            if acceleration.get("display_standard_values", "false"):

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

        # Group exchanges by unique participant pairs
        groups = {}
        for exchange in exchanges:
            exchanges = exchange.get("data-type").lower() if  exchange.get("data-type") is not None else "scalar"
            pair = tuple(sorted([exchange["from"], exchange["to"]]))
            groups.setdefault(pair, []).append(exchange)

        self.couplings = []
        for pair, ex_list in groups.items():
            coupling = UI_Coupling()
            p1_name, p2_name = pair
            coupling.partitcipant1 = self.participants[p1_name]
            coupling.partitcipant2 = self.participants[p2_name]

            # Determine coupling type based on exchanged data
            data_names = {ex["data"] for ex in ex_list}
            if any("force" in name.lower() for name in data_names) and any("displacement" in name.lower() for name in data_names):
                coupling.coupling_type = UI_CouplingType.fsi
            elif any("force" in name.lower() for name in data_names):
                coupling.coupling_type = UI_CouplingType.f2s
            # elif any("temperature" in name.lower() or "heat" in name.lower() for name in data_names):
            elif any("temperature" in name.lower() for name in data_names):
                coupling.coupling_type = UI_CouplingType.cht
            else:
                coupling.coupling_type = UI_CouplingType.error_coupling

            # Use the first exchange's patches as boundary interfaces (simple heuristic)
            first_ex = ex_list[0]
            coupling.boundaryC1 = first_ex.get("from-patch", "")
            coupling.boundaryC2 = first_ex.get("to-patch", "")

            self.couplings.append(coupling)
            coupling.partitcipant1.list_of_couplings.append(coupling)
            coupling.partitcipant2.list_of_couplings.append(coupling)
