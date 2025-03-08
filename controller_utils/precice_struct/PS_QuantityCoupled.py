from controller_utils.myutils.UT_PCErrorLogging import UT_PCErrorLogging
from enum import Enum

class QuantityCouple(object):
    """ the quantity that is coupled """
    def __init__(self):
        self.name = "None"   # the name of the quantity as it is called physically
        self.instance_name = "None" # this will be the solver name "-" quantity name, example: "InnerSolver-Pressure"
        self.unit = "None"   # unit of the quantity
        self.BC = -1 # boundary code for the coupling
        self.relative_tolerance = 1E-4 # the relative convergence for coupling
        self.list_of_solvers = {} # list of solvers that use this quantity (either read or write)
        self.source_solver = None # the origin of this quantity the solver how creates it
        self.source_mesh_name = "None" # the source mesh name
        self.mapping_string = "ERROR" # conservative or consistent
        self.dim = 3 # the dimension of the quantity
        self.is_consistent = True # True if this quantity is consistent Falso if it is conservative
        self.category = "None" # The category of the quantity (Force, Displacement, etc.)
        pass


def get_quantity_object(name:str, bc:str, instance_name:str):
    """ Function to create coupling quantity """
    # Determine category from the name
    category = get_category_from_name(name)
    print(f"Creating quantity object for name: {name}, category: {category}")
    
    ret = None
    if category == "Force":
        ret = Force()
    elif category == "Displacement":
        ret = Displacement()
    elif category == "Velocity":
        ret = Velocity()
    elif category == "Pressure":
        ret = Pressure()
    elif category == "Temperature":
        ret = Temperature()
    elif category == "HeatTransfer":
        ret = HeatTransfer()
    
    if ret is None:
        print(f"Error: Unknown category {category} for name {name}")
        # TODO: report error
        return QuantityCouple()
    else:
        # set the boundary code at the source solver
        ret.BC = bc
        # the instance name is like "InnerSolver-Pressure" (a combination of solver name and quantity name)
        ret.instance_name = instance_name
        ret.name = name
        ret.category = category
        print(f"Created quantity object: name={name}, category={category}, instance_name={instance_name}")
        return ret


def get_category_from_name(name: str) -> str:
    """ Determine the category from the data name """
    print(f"Determining category for data name: {name}")
    
    # Handle specific data names from topology.yaml
    if "Temperature" in name:
        print(f"Found match: {name} contains Temperature")
        return "Temperature"
    elif "HeatTransfer" in name:
        print(f"Found match: {name} contains HeatTransfer")
        return "HeatTransfer"
    
    # Check if the name starts with any of our categories
    categories = ["Force", "Displacement", "Velocity", "Pressure", "Temperature", "HeatTransfer"]
    
    for category in categories:
        if name.lower().startswith(category.lower()):
            print(f"Found match: {name} starts with {category}")
            return category
    
    # If no match, check for common suffixes
    if name.lower().endswith("force"):
        print(f"Found match: {name} ends with force")
        return "Force"
    elif name.lower().endswith("displacement"):
        print(f"Found match: {name} ends with displacement")
        return "Displacement"
    elif name.lower().endswith("velocity"):
        print(f"Found match: {name} ends with velocity")
        return "Velocity"
    elif name.lower().endswith("pressure"):
        print(f"Found match: {name} ends with pressure")
        return "Pressure"
    elif name.lower().endswith("temperature"):
        print(f"Found match: {name} ends with temperature")
        return "Temperature"
    elif name.lower().endswith("heattransfer") or name.lower().endswith("heat_transfer"):
        print(f"Found match: {name} ends with heattransfer/heat_transfer")
        return "HeatTransfer"
    
    # If still no match, return the base name
    base_name = name.split("-")[0].split("_")[0].capitalize()
    print(f"No match found, using base name as category: {base_name}")
    return base_name


class Force(QuantityCouple):
    """ Forces """
    def __init__(self):
        super().__init__()
        self.name = "Force"
        self.unit = "N"
        self.mapping_string = "conservative"
        self.is_consistent = False
        pass


class Displacement(QuantityCouple):
    """ Displacements """
    def __init__(self):
        super().__init__()
        self.name = "Displacement"
        self.unit = "m"
        self.mapping_string = "consistent"
        pass


class Velocity(QuantityCouple):
    """ Velocities """
    def __init__(self):
        super().__init__()
        self.name = "Velocity"
        self.unit = "m/s"
        self.mapping_string = "consistent"
        pass


class Pressure(QuantityCouple):
    """ Pressures """
    def __init__(self):
        super().__init__()
        self.name = "Pressure"
        self.unit = "N/m^2"
        self.mapping_string = "consistent"
        self.dim = 1
        pass


class Temperature(QuantityCouple):
    """ temperature """
    def __init__(self):
        super().__init__()
        self.name = "Temperature"
        self.unit = "C"
        self.mapping_string = "consistent"
        self.dim = 1
        pass


class HeatTransfer(QuantityCouple):
    """ heat transfer """
    def __init__(self):
        super().__init__()
        self.name = "HeatTransfer"
        self.unit = "?"
        self.mapping_string = "consistent"
        self.dim = 1
        pass