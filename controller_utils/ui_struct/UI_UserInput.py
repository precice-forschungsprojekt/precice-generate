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
        self.sim_info = UI_SimulationInfo()
        self.participants = {} # empty participants stored as a dictionary
        self.couplings = []    # empty coupling list
        self.exchanges = []    # empty exchanges list
        pass

    def init_from_yaml(self, etree, mylog: UT_PCErrorLogging):
        # Check if using new topology structure
        if "coupling-scheme" in etree and "participants" in etree and "exchanges" in etree:
            # --- Parse simulation info from 'coupling-scheme' ---
            simulation_info = etree["coupling-scheme"]
            self.sim_info.sync_mode = simulation_info.get("sync-mode", "on")
            self.sim_info.mode = simulation_info.get("mode", "fundamental")
            self.sim_info.steady = False
            self.sim_info.NrTimeStep = simulation_info.get("max-time", 1e-3)
            self.sim_info.Dt = simulation_info.get("time-window-size", 1e-3)
            self.sim_info.max_iterations = simulation_info.get("max-iterations", 50)
            self.sim_info.accuracy = "medium"

            # Initialize coupling type+ acceleration to None
            self.coupling_type = None
            self.acceleration = None
            
            # Extract coupling type from exchanges
            if 'exchanges' in etree:
                exchanges = etree['exchanges']
                exchange_types = [exchange.get('type') for exchange in exchanges if 'type' in exchange]
                
                # Validate exchange types
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
            
            # --- Parse Acceleration ---
            if 'acceleration' in etree:
                acceleration = etree['acceleration']
                self.acceleration = {
                    'name': acceleration.get('name', 'IQN-ILS'),
                    'initial-relaxation': acceleration.get('initial-relaxation', None),
                    'preconditioner': {
                        'freeze-after': acceleration.get('preconditioner', {}).get('freeze-after', -1),
                        'type': acceleration.get('preconditioner', {}).get('type', None)
                    },
                    'filter': {
                        'limit': acceleration.get('filter', {}).get('limit', 1e-16),
                        'type': acceleration.get('filter', {}).get('type', None)
                    },
                    'max-used-iterations': acceleration.get('max-used-iterations', None),
                    'time-windows-reused': acceleration.get('time-windows-reused', None),
                    'imvj-restart-mode': {
                        'truncation-threshold': acceleration.get('imvj-restart-mode', {}).get('truncation-threshold', None),
                        'chunk-size': acceleration.get('imvj-restart-mode', {}).get('chunk-size', None),
                        'reused-time-windows-at-restart': acceleration.get('imvj-restart-mode', {}).get('reused-time-windows-at-restart', None),
                        'type': acceleration.get('imvj-restart-mode', {}).get('type', None)
                    },
                    'display_standard_values': acceleration.get('display_standard_values', 'false')
                }
            else:
                self.acceleration = {'display_standard_values': 'false'}
            
            # --- Parse participants ---
            self.participants = {}
            participants_data = etree["participants"]
            for participant_name, solver_info in participants_data.items():
                new_participant = UI_Participant()
                
                # Handle different input formats
                if isinstance(solver_info, str):
                    # Simple solver name format
                    new_participant.name = participant_name
                    new_participant.solverName = solver_info
                    new_participant.solverType = ""
                    new_participant.dimensionality = 3  # Default to 3D
                
                elif isinstance(solver_info, dict):
                    # New dictionary format
                    if ":" in participant_name:
                        name, solver_name = participant_name.split(":", 1)
                        name = name.strip()
                        solver_name = solver_name.strip()
                    else:
                        name = participant_name
                        solver_name = solver_info.get("solver", participant_name)
                    
                    new_participant.name = name
                    new_participant.solverName = solver_name
                    new_participant.solverType = solver_info.get("solver-type", "")  # Use solver as solverType
                    new_participant.dimensionality = solver_info.get("dimensionality", 3)
                
                else:
                    # Unsupported format
                    mylog.rep_error(f"Unsupported participant configuration for {participant_name}")
                    continue
                
                new_participant.list_of_couplings = []
                self.participants[new_participant.name] = new_participant

            # --- Parse couplings from exchanges ---
            exchanges_list = etree["exchanges"]
            # Save full exchange details
            self.exchanges = exchanges_list.copy()

            # Group exchanges by unique participant pairs
            groups = {}
            for exchange in exchanges_list:
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

        else:
            # --- Fallback to original parsing logic for old YAML structures ---
            try:
                simulation_info = etree["simulation"]
                sync_mode = simulation_info.get("sync-mode", "on")
                mode = simulation_info.get("mode", "fundamental")
                self.sim_info.sync_mode = sync_mode
                self.sim_info.mode = mode
                self.sim_info.init_from_yaml(simulation_info, mylog)

                # Parse participants from the old structure
                participants_list = etree["participants"]
                for participant_name in participants_list:
                    participant_data = participants_list[participant_name]
                    new_participant = UI_Participant()
                    new_participant.init_from_yaml(participant_data, participant_name, mylog)
                    self.participants[participant_name] = new_participant

                # Parse couplings from the old structure
                couplings_list = etree["couplings"]
                self.couplings = []
                for couplings in couplings_list:
                    for coupling_name in couplings:
                        coupling_data = couplings[coupling_name]
                        new_coupling = UI_Coupling()
                        new_coupling.init_from_yaml(coupling_name, coupling_data, self.participants, mylog)
                        self.couplings.append(new_coupling)
            except Exception as e:
                mylog.rep_error("Error during YAML initialization: " + str(e))