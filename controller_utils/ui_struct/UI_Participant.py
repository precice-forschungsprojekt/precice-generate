from controller_utils.myutils.UT_PCErrorLogging import UT_PCErrorLogging
from controller_utils.ui_struct.UI_Coupling import UI_Coupling


class UI_Participant(object):
    """
    This class represents one participant as it is declared on the user input level
    """

    def __init__(self, name: str = "", solver_name: str = "", list_of_couplings=None,
                 solver_domain: str = "", data_type: str = "scalar", dimensionality: int = None):
        if list_of_couplings is None:
            list_of_couplings = []

        self.name = name
        self.solver_name = solver_name
        self.list_of_couplings = list_of_couplings  # list of empty couplings
        self.solver_domain = solver_domain  # this shows if this participant is a fluid or structure or else solver
        self.data_type = data_type
        self.dimensionality = dimensionality

        pass

    @classmethod
    def from_yaml(cls, etree, participant_name: str, mylog: UT_PCErrorLogging):
        """ Method to initialize fields from a parsed YAML file node """
        self = cls()

        try:
            self.name = participant_name
            self.solver_name = etree["solver"]
            self.data_type = etree["data-type"]
        except:
            mylog.rep_error("Error in YAML initialization of the Participant.")
        pass

        return self
