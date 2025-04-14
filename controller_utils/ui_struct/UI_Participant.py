from controller_utils.myutils.UT_PCErrorLogging import UT_PCErrorLogging
from controller_utils.ui_struct.UI_Coupling import UI_Coupling

class UI_Participant(object):
    """
    This class represents one participant as it is declared on the user input level
    """
    def __init__(self):
        """The constructor."""
        self.name = ""
        self.solverName = ""
        self.list_of_couplings = [] # list of empty couplings
        self.solver_domain = "" # this shows if this participant is a fluid or structure or else solver
        self.data_type = "scalar"
        pass

    def init_from_yaml(self, etree, participant_name: str, mylog: UT_PCErrorLogging):
        """ Method to initialize fields from a parsed YAML file node """
        # catch the exceptions
        try:
            self.name = participant_name
            self.solverName = etree["solver"]
            self.data_type = etree["data-type"]
        except:
            mylog.rep_error("Error in YAML initialization of the Participant.")
        pass