class Participant:
    def __init__(self, name, solver, dimensionality):
        self.name = name
        self.solver = solver
        self.dimensionality = dimensionality
        self.provided_meshes = []
        self.received_meshes = []
        self.write_data = []
        self.read_data = []
        self.mappings = []
