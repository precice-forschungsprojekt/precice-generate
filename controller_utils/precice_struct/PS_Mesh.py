from controller_utils.precice_struct.PS_QuantityCoupled import *
#from .PS_ParticipantSolver import PS_ParticipantSolver #-> this would result in circular reference

class PS_Mesh(object):
    """ The mesh object that is assigned to one or more solver"""
    def __init__(self):
        self.name = "" # name of the mesh
        self.quantities = {} # list of the quantities that are stored here
        self.list_of_solvers = {} # dictionary with all the solver (names) that use this mesh
        self.source_solver = None # The solver that provides this mesh
        pass

    def add_source_solver(self, source_solver):
        """ Sets the source solver that provides this mesh """
        self.source_solver = source_solver
        pass

    def add_solver(self, solver): # solver: PS_ParticipantSolver
        """ adds a solver to the list of solver """
        self.list_of_solvers[solver.solver_name] = solver
        pass

    def add_quantity(self, quantity: QuantityCouple):
        """ adds a quantity for coupling """
        #print(" add_quantity to Mesh ", self.name, " ", quantity.instance_name)
        self.quantities[quantity.instance_name] = quantity
        pass

    def get_solver(self, solver_name:str):
        """  returns the solver """
        if solver_name in self.list_of_solvers:
            return self.list_of_solvers[solver_name]
        else:
            return None

    def get_quantity(self, quantity_name:str):
        """ returns the quantity """
        if quantity_name in self.quantities:
            return self.quantities[quantity_name]
        else:
            return None
