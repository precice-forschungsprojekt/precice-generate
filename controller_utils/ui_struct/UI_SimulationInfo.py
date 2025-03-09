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
        self.acceleration = None
        self.mode = "on"
        self.sync_mode = "fundamental"
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
        except:
            mylog.rep_error("Error in YAML initialization of the Simulator info.")
        pass