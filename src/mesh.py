class Mesh:
    """Class to represent a mesh in preCICE"""
    def __init__(self, name):
        self.name = name
        self.quantities = {}

