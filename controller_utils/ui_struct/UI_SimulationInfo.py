from controller_utils.myutils.UT_PCErrorLogging import UT_PCErrorLogging

class UI_SimulationInfo(object):
    """
    This class contains information on the user input level regarding the
    general simulation informations
    """
    def __init__(self):
        """The constructor."""
        self.steady = False
        self.NrTimeStep = -1
        self.Dt = 1E-3
        self.max_iterations = 50
        self.accuracy = "medium"
        self.mode = "on"
        self.sync_mode = "fundamental"
        # Acceleration parameters
        self.acceleration = {
            'name': 'IQN-ILS',
            'initial-relaxation': 0.5,
            'preconditioner': 'residual-sum',
            'filter': 'QR1',
            'max-used-iterations': 50,
            'time-windows-reused': 10
        }
        pass

    def init_from_yaml(self, etree, mylog: UT_PCErrorLogging):
        """ Method to initialize fields from a parsed YAML file node """
        # catch exceptions if these items are not in the list
        try:
            self.steady = etree["steady-state"]
            self.NrTimeStep = etree["timesteps"]
            self.Dt = etree["time-window-size"]
            self.max_iterations = etree.get("max-iterations", 50)
            self.accuracy = etree["accuracy"]
            self.sync_mode = etree.get("synchronize", "on")
            self.mode = etree.get("mode", "fundamental")
            
            # Initialize acceleration parameters if present
            if 'acceleration' in etree:
                acceleration_data = etree['acceleration']
                self.acceleration['name'] = acceleration_data.get('name', 'IQN-ILS')
                self.acceleration['initial-relaxation'] = acceleration_data.get('initial-relaxation', 0.5)
                self.acceleration['preconditioner'] = acceleration_data.get('preconditioner', 'residual-sum')
                self.acceleration['filter'] = acceleration_data.get('filter', 'QR1')
                self.acceleration['max-used-iterations'] = acceleration_data.get('max-used-iterations', 50)
                self.acceleration['time-windows-reused'] = acceleration_data.get('time-windows-reused', 10)
        except:
            mylog.rep_error("Error in YAML initialization of the Simulator info.")
        pass