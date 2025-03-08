from controller_utils.myutils.UT_PCErrorLogging import UT_PCErrorLogging
from controller_utils.precice_struct.PS_ParticipantSolver import PS_ParticipantSolver
from controller_utils.ui_struct.UI_UserInput import UI_UserInput
import xml.etree.ElementTree as etree

class PS_CouplingScheme(object):
    """Class to represent the Coupling schemes """
    def __init__(self):
        """Ctor to initialize all the fields """
        self.firstSolver = None
        self.secondSolver = None
        pass

    def init_from_UI(self, ui_config:UI_UserInput, conf): # : PS_PreCICEConfig
        """ This method should be overwritten by the subclasses """
        pass

    def write_precice_xml_config(self, tag: etree, config): # config: PS_PreCICEConfig
        """ parent function to write out XML file """
        pass

    def write_participants_and_coupling_scheme(self, tag: etree, config, coupling_str:str ):
        """ write out the config XMl file """
        if len(config.solvers) <= 2:
            # for only
            coupling_scheme = etree.SubElement(tag, "coupling-scheme:" + coupling_str)
            # print the participants, ASSUMPTION! we assume there is at least two
            mylist = ["NONE", "NONE"]
            mycomplexity = [-1, -1]
            myindex = 0
            for participant_name in config.solvers:
                p = config.solvers[participant_name]
                mylist[myindex] = participant_name
                mycomplexity[myindex] = p.solver_domain.value
                myindex = myindex + 1
                pass
            # the solver with the higher complexity should be first
            if mycomplexity[0] < mycomplexity[1]:
                i = etree.SubElement(coupling_scheme, "participants", first=mylist[0],
                                     second=mylist[1])
            else:
                i = etree.SubElement(coupling_scheme, "participants", first=mylist[1],
                                     second=mylist[0])
        else:
            # TODO: is "multi" good for all
            coupling_scheme = etree.SubElement(tag, "coupling-scheme:multi")
            # first find the solver with the most meshes and this should be the one who controls the coupling
            nr_max_meshes = -1
            control_participant_name = "NONE"
            for participant_name in config.solvers:
                participant = config.solvers[participant_name]
                # TODO: we should select the solver with the most meshes ?
                if len(participant.meshes) > nr_max_meshes:
                    nr_max_meshes = len(participant.meshes)
                    control_participant_name = participant.name
                pass
            # second print all the participants
            for participant_name in config.solvers:
                participant = config.solvers[participant_name]
                if participant.name == control_participant_name:
                    i = etree.SubElement(coupling_scheme, "participants", name=participant_name, control="yes")
                else:
                    i = etree.SubElement(coupling_scheme, "participants", name=participant_name)
                    pass
                pass
            pass
        return coupling_scheme

    def write_exchange_and_convergance(self, config, coupling_scheme, relative_conv_str:str):
        """ Writes to the XML the exchange list """
        # select the solver with minimal complexity
        simple_solver = None
        solver_simplicity = -2
        for q_name in config.coupling_quantities:
            q = config.coupling_quantities[q_name]
            solver = q.source_solver
            if solver_simplicity < solver.solver_domain.value:
                simple_solver = solver

        # For each quantity, specify the exchange and the convergence
        for q_name in config.coupling_quantities:
            q = config.coupling_quantities[q_name]
            solver = q.source_solver

            # look for the second solver in the list of solvers within the quantity
            other_solver_for_coupling = None
            other_mesh_name = None  # Initialize other mesh name
            for oq in q.list_of_solvers:
                other_solver = q.list_of_solvers[oq]
                if other_solver.name != solver.name:
                    other_solver_for_coupling = other_solver
                    for allm in other_solver.meshes:
                        if allm != q.source_mesh_name:
                            other_mesh_name = allm

            # Determine the coupled mesh that both participants share
            coupled_mesh_name = None

            # Get mesh names for both solvers
            solver_mesh_names = list(solver.meshes.keys())
            other_solver_mesh_names = list(other_solver_for_coupling.meshes.keys())

            #print("Current solver " + solver.name + " meshes: " + str(solver_mesh_names))
            #print("Other solver " + other_solver_for_coupling.name + " meshes: " + str(other_solver_mesh_names))

            # Get all source meshes from quantities
            solver_source_meshes = set()
            for q_name in solver.quantities_read:
                q = solver.quantities_read[q_name]
                solver_source_meshes.add(q.source_mesh_name)
            for q_name in solver.quantities_write:
                q = solver.quantities_write[q_name]
                solver_source_meshes.add(q.source_mesh_name)

            other_solver_source_meshes = set()
            for q_name in other_solver_for_coupling.quantities_read:
                q = other_solver_for_coupling.quantities_read[q_name]
                other_solver_source_meshes.add(q.source_mesh_name)
            for q_name in other_solver_for_coupling.quantities_write:
                q = other_solver_for_coupling.quantities_write[q_name]
                other_solver_source_meshes.add(q.source_mesh_name)

            # print("Current solver " + solver.name + " source meshes: " + str(solver_source_meshes))
            # print("Other solver " + other_solver_for_coupling.name + " source meshes: " + str(other_solver_source_meshes))

            coupled_meshes = []
            for mesh in solver_mesh_names:
                # Check if this mesh is shared by both solvers
                if mesh in other_solver_source_meshes:
                    # Use the provide and receive meshes from the config
                    is_solver_providing_mesh = mesh in config.solver_provide_meshes[solver.name]
                    is_other_solver_receiving_mesh = mesh in config.solver_receive_meshes[other_solver_for_coupling.name]
                    is_solver_receiving_mesh = mesh in config.solver_receive_meshes[solver.name]
                    is_other_solver_providing_mesh = mesh in config.solver_provide_meshes[other_solver_for_coupling.name]

                    # Check if meshes are provided/received in complementary ways
                    if (is_solver_providing_mesh and is_other_solver_receiving_mesh) or \
                    (is_solver_receiving_mesh and is_other_solver_providing_mesh):
                        coupled_meshes.append(mesh)

            # the from and to attributes
            from_s = "___"
            to_s = "__"
            exchange_mesh_name = q.source_mesh_name


            for exchange in config.exchanges:
                if exchange.get('data') == q_name:
                    from_s = exchange.get('from')
                    to_s = exchange.get('to')

            read_mappings = [m.copy() for m in config.mappings_read]
            write_mappings = [m.copy() for m in config.mappings_write]

            read_mapping = next((m for m in read_mappings if 
                                (m['from'] == from_s + '-Mesh' and m['to'] == to_s + '-Mesh') ), None)
            write_mapping = next((m for m in write_mappings if 
                                (m['from'] == from_s + '-Mesh' and m['to'] == to_s + '-Mesh')), None)

            # # Choose mesh based on mapping constraint
            if read_mapping and read_mapping['constraint'] == 'conservative':
                exchange_mesh_name = read_mapping['to']
            elif read_mapping and read_mapping['constraint'] == 'consistent':
                exchange_mesh_name = read_mapping['from']
            elif write_mapping and write_mapping['constraint'] == 'conservative':
                exchange_mesh_name = write_mapping['to']
            elif write_mapping and write_mapping['constraint'] == 'consistent':
                exchange_mesh_name = write_mapping['from']
            else:
                exchange_mesh_name = q.source_mesh_name
                if solver.name != simple_solver.name:
                    exchange_mesh_name = other_mesh_name

            e = etree.SubElement(coupling_scheme, "exchange", data=q_name, mesh=exchange_mesh_name
                                 ,from___ = from_s, to=to_s)
            
            # Use the same mesh for the relative convergence measure
            if relative_conv_str != "":
                c = etree.SubElement(coupling_scheme, "relative-convergence-measure",
                                 limit=relative_conv_str, mesh=exchange_mesh_name
                                 ,data=q_name)
            pass


class PS_ExplicitCoupling(PS_CouplingScheme):
    """ Explicit coupling scheme """
    def __init__(self):
        self.NrTimeStep = -1
        self.Dt = 1E-4
        pass

    def initFromUI(self, ui_config: UI_UserInput, conf):  # conf : PS_PreCICEConfig
        # call theinitialization from the UI data structures
        super(PS_ExplicitCoupling, self).init_from_UI(ui_config, conf)
        simulation_conf = ui_config.sim_info
        self.NrTimeStep = simulation_conf.NrTimeStep
        self.Dt = simulation_conf.Dt
        pass

    def write_precice_xml_config(self, tag:etree, config): # config: PS_PreCICEConfig
        """ write out the config XMl file """
        coupling_scheme = self.write_participants_and_coupling_scheme( tag, config, "parallel-explicit" )

        i = etree.SubElement(coupling_scheme, "max-time", value=str(self.NrTimeStep))
        attr = { "value": str(self.Dt)}
        i = etree.SubElement(coupling_scheme, "time-window-size", attr)

        # write out the exchange but not the convergence (if empty it will not be written)
        self.write_exchange_and_convergance(config, coupling_scheme, "")


class PS_ImplicitCoupling(PS_CouplingScheme):
    """ Implicit coupling scheme """
    def __init__(self):

        # TODO: define here only implicit coupling specific measures

        self.NrTimeStep = -1
        self.Dt = 1E-4
        self.maxIteration = 50
        self.relativeConverganceEps = 1E-4
        self.extrapolation_order = 2
        self.postProcessing = PS_ImplicitPostProcessing() # this is the postprocessing
        pass

    def initFromUI(self, ui_config:UI_UserInput, conf): # conf : PS_PreCICEConfig
        # call theinitialization from the UI data structures
        super(PS_ImplicitCoupling, self).init_from_UI(ui_config, conf)

        # TODO: should we add all quantities?
        # later do delte some quantities from the list?
        self.postProcessing.post_process_quantities = conf.coupling_quantities

        simulation_conf = ui_config.sim_info

        self.NrTimeStep = simulation_conf.NrTimeStep
        self.Dt = simulation_conf.Dt
        self.maxIteration = simulation_conf.max_iterations

        pass

    def write_precice_xml_config(self, tag:etree, config): # config: PS_PreCICEConfig
        """ write out the config XMl file """
        coupling_scheme = self.write_participants_and_coupling_scheme( tag, config, "parallel-implicit" )

        i = etree.SubElement(coupling_scheme, "max-time", value = str(self.NrTimeStep))
        attr = { "value": str(self.Dt)}
        i = etree.SubElement(coupling_scheme, "time-window-size", attr)
        i = etree.SubElement(coupling_scheme, "max-iterations", value=str(self.maxIteration))
        #i = etree.SubElement(coupling_scheme, "extrapolation-order", value=str(self.extrapolation_order))

        # write out the exchange and the convergance rate
        self.write_exchange_and_convergance(config, coupling_scheme, str(self.relativeConverganceEps))

        # finally we write out the post processing...
        self.postProcessing.write_precice_xml_config(coupling_scheme, config, self)

        pass


class PS_ImplicitPostProcessing(object):
    """ Class to model the post-processing part of the implicit coupling """
    def __init__(self):
        """ Ctor for the postprocessing """
        self.name = "IQN-ILS"
        self.precondition_type = "residual-sum"
        self.post_process_quantities = {} # The quantities that are in the acceleration

    def write_precice_xml_config(self, tag: etree.Element, config, parent):
        """ Write out the config XML file of the acceleration in case of implicit coupling
            Only for explicit coupling (one directional) this should not write out anything """

        post_processing = etree.SubElement(tag, "acceleration:" + self.name)

        # # Add acceleration parameters from UI input if they exist
        acceleration = config.acceleration
        if acceleration:
            if "initial-relaxation" in acceleration:
                etree.SubElement(post_processing, "initial-relaxation", value = str(acceleration["initial-relaxation"]) )
            if "max-used-iterations" in acceleration:
                etree.SubElement(post_processing, "max-used-iterations", value = str(acceleration["max-used-iterations"]) )
            if "time-window-reused" in acceleration:
                etree.SubElement(post_processing, "time-window-reused", value = str(acceleration["time-window-reused"]) )
            
            # Add filter configuration if present
            filter_config = acceleration.get("filter", {})
            if filter_config:
                if "type" in filter_config and "limit" in filter_config:
                    filter_elem = etree.SubElement(post_processing, "filter", type = filter_config["type"], limit = str(filter_config["limit"]))


        # Identify unique solvers and their meshes
        solver_meshes = {}
        for q_name, q in config.coupling_quantities.items():
            solver = q.source_solver
            if solver.name not in solver_meshes:
                solver_meshes[solver.name] = set()
            solver_meshes[solver.name].add(q.source_mesh_name)

        # Attempt to find the 'simplest' solver (e.g., solid solver)
        # This is a heuristic and might need adjustment based on specific use cases
        def solver_complexity(solver_name):
            complexity_map = {
                'solid': 1,
                'structural': 1,
                'fluid': 2,
                'thermal': 3
            }
            return complexity_map.get(solver_name.lower(), 10)

        sorted_solvers = sorted(solver_meshes.keys(), key=solver_complexity)
        
        # Choose the simplest solver's mesh
        simple_solver = sorted_solvers[0] if sorted_solvers else None
        
        if simple_solver:
            for q_name, q in config.coupling_quantities.items():
                # Use the first mesh from the simplest solver
                mesh_name = list(solver_meshes[simple_solver])[0]
                
                i = etree.SubElement(post_processing, "data", 
                                     name=q.instance_name, 
                                     mesh=mesh_name)