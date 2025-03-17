from controller_utils.myutils.UT_PCErrorLogging import UT_PCErrorLogging
from controller_utils.ui_struct.UI_Participant import UI_Participant
from controller_utils.ui_struct.UI_Coupling import UI_Coupling
from controller_utils.precice_struct.PS_QuantityCoupled import QuantityCouple
from controller_utils.precice_struct.PS_Mesh import PS_Mesh
from enum import Enum


class SolverDomain(Enum):
    """ enum type to represent the physical domain of the solver """
    Fluid = 0
    Solid = 1
    Heat = 2
    NotDefined = -1

class SolverDimension(Enum):
    """The dimension of the solver, the interface could be one dimension less
       but must not be """
    p1D = 1
    p2D = 2
    p3D = 3

class SolverNature(Enum):
    """
    Enum type to show if we have a transient problem or a stationary one
    Mostly they will be transient problems
    """
    STATIONARY = 0
    TRANSIENT = 1

class PS_ParticipantSolver(object):
    """Class to represent a participat in the preCICE data structure """

    # TODO: one solver might have more than one couplings!!!

    def __init__(self, participant: UI_Participant, coupling: UI_Coupling, conf ): # conf:PS_PreCICEConfig
        """ Ctor """
        self.solver_domain = SolverDomain.NotDefined
        
        # Use set_dimensionality method to set solver dimension
        self.set_dimensionality(participant.dimensionality)
        
        self.nature = SolverNature.STATIONARY
        self.quantities_read = {}  # list of quantities that are read by this solver
        self.quantities_write = {} # list of quantities that are writen by this solver

        self.meshes = {} # we have each mesh for each couling
        self.coupling_participants = {} # for each coupling we also store the name of the participant

        self.solver_type = participant.solverType
        self.solver_name = participant.solverName
        self.name = participant.name

        pass

    def set_dimensionality(self, dim: int):
        """ sets the dimensionality of the solver """
        if dim == 2:
            self.dim = SolverDimension.p2D
            self.dimensionality = 2
        else:
            self.dim = SolverDimension.p3D
            self.dimensionality = 3

    def create_mesh_for_coupling(self, conf, other_solver_name:str):
        """ generates the mesh for the coupling """
        # IMPORTANT: we call the function with the source participant first and then the rest
        coupling_mesh = conf.get_mesh_by_participant_names(self.name,other_solver_name)
        # IMPORTANT: store the current mesh name such that later we a
        # print("!!! Mesh = ", coupling_mesh.name)
        self.meshes[coupling_mesh.name] = conf.get_mesh_by_participant_names(self.name,other_solver_name)
        self.coupling_participants[other_solver_name] = 1
        pass

    def add_quantities_for_coupling(self, conf, boundary_code1:str, boundary_code2:str, other_solver_name:str,
                                    r_list:list, w_list:list):
        # there should be at least one coupling quantity, therefore no early exit
        # add mesh
        source_mesh_name = conf.get_mesh_name_by_participants(self.name, other_solver_name)
        other_mesh_name = conf.get_mesh_name_by_participants(other_solver_name, self.name)
        self.create_mesh_for_coupling(conf, other_solver_name )
        
        # Determine reading and writing quantities based on exchanges
        for exchange in conf.exchanges:
            if exchange['from'] == self.name:
                # This participant is writing data
                if exchange['data'] in w_list:
                    w = conf.get_coupling_quantitiy(exchange['data'], source_mesh_name, boundary_code2, self, True)
                    conf.add_quantity_to_mesh(other_mesh_name, w)
                    conf.add_quantity_to_mesh(source_mesh_name, w)
                    self.quantities_write[w.name] = w
            elif exchange['to'] == self.name:
                # This participant is reading data
                if exchange['data'] in r_list:
                    r = conf.get_coupling_quantitiy(exchange['data'], other_mesh_name, boundary_code1, self, False)
                    conf.add_quantity_to_mesh(other_mesh_name, r)
                    conf.add_quantity_to_mesh(source_mesh_name, r)
                    self.quantities_read[r.name] = r
        pass

    def make_participant_fsi_fluid(self, conf, boundary_code1:str, boundary_code2:str, other_solver_name:str):
        """ This method should setup the participant as a fluid solver for FSI """
        self.add_quantities_for_coupling(conf, boundary_code1, boundary_code2, other_solver_name,
                                    ["Displacement"], ["Force"])
        # set the type of the solver/participant
        self.solver_domain = SolverDomain.Fluid
        self.nature = SolverNature.TRANSIENT
        pass

    def make_participant_fsi_structure(self, conf, boundary_code1:str, boundary_code2:str, other_solver_name:str):
        """ This method should setup the participant as a structure solver for FSI """
        self.add_quantities_for_coupling(conf, boundary_code1, boundary_code2, other_solver_name,
                                    ["Force"], ["Displacement"])
        # set the type of the participant
        self.solver_domain = SolverDomain.Solid
        self.nature = SolverNature.TRANSIENT
        pass

    def make_participant_f2s_fluid(self, conf, boundary_code1:str, boundary_code2:str, other_solver_name:str):
        """ This method should setup the participant as a fluid solver for F2S """
        self.add_quantities_for_coupling(conf, boundary_code1, boundary_code2, other_solver_name,
                                    [], ["Force"])
        # set the type of the solver/participant
        self.solver_domain = SolverDomain.Fluid
        self.nature = SolverNature.TRANSIENT
        pass

    def make_participant_f2s_structure(self, conf, boundary_code1:str, boundary_code2:str, other_solver_name:str):
        """ This method should setup the participant as a structure solver for F2S """
        self.add_quantities_for_coupling(conf, boundary_code1, boundary_code2, other_solver_name,
                                    ["Force"], [])
        # set the type of the participant
        self.solver_domain = SolverDomain.Solid
        self.nature = SolverNature.TRANSIENT
        pass

    def make_participant_cht_fluid(self, conf, boundary_code1: str, boundary_code2: str, other_solver_name: str,
                                   data_forward: str, data_backward: str):
        """ makes a change heat fluid solver from the participant """
        #print("CHT FLUID")
        heat_str = data_forward if "HeatTransfer" in data_forward else data_backward
        temperature_str = data_forward if "Temperature" in data_forward else data_backward

        self.add_quantities_for_coupling(conf, boundary_code1, boundary_code2, other_solver_name,
                                    [heat_str, temperature_str], [heat_str, temperature_str])
        # set the type of the participant
        self.solver_domain = SolverDomain.Fluid
        self.nature = SolverNature.TRANSIENT
        pass

    def make_participant_cht_structure(self, conf, boundary_code1: str, boundary_code2: str, other_solver_name: str,
                                       data_forward: str, data_backward: str):
        """ makes a change heat structure solver from the participant """
        #print("CHT STRUCTURE")
        heat_str = data_forward if "HeatTransfer" in data_forward else data_backward
        temperature_str = data_forward if "Temperature" in data_forward else data_backward

        self.add_quantities_for_coupling(conf, boundary_code1, boundary_code2, other_solver_name,
                                    [heat_str, temperature_str], [heat_str, temperature_str])
        # set the type of the participant
        self.solver_domain = SolverDomain.Solid
        self.nature = SolverNature.TRANSIENT
        pass