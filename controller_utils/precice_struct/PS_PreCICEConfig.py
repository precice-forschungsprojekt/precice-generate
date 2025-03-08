from controller_utils.myutils.UT_PCErrorLogging import UT_PCErrorLogging
from controller_utils.ui_struct.UI_UserInput import UI_UserInput
from controller_utils.ui_struct.UI_Coupling import *
from controller_utils.precice_struct.PS_Mesh import *
from controller_utils.precice_struct.PS_ParticipantSolver import PS_ParticipantSolver
from controller_utils.precice_struct.PS_CouplingScheme import *
import xml.etree.ElementTree as etree
import xml.dom.minidom as my_minidom

class PS_PreCICEConfig(object):
    """Top main class for the preCICE config """

    def __init__(self):
        """ Ctor """
        # the overall coupling scheme
        # this contains all the coupling information between the solvers
        self.couplingScheme = None
        # here we enlist all the solvers including their meshes
        self.solvers = {} # empty dictionary with the solvers
        self.meshes = {} # dictionary with the meshes of the coupling scenario
        self.coupling_quantities = {} # ditionary with the coupling quantities
        self.exchanges = []    # list to store full exchange details
        self.mappings_read = []
        self.mappings_write = []
        pass

    def get_coupling_quantitiy(self, quantity_name:str, source_mesh_name:str, bc: str, solver, read:bool):
        """ returns the coupling quantity specified by name,
        the name is a combination of mesh_name + quantity name """
        # there could be more than one pressure or temperature therefore we
        # add always as a prefix the name of the mesh such that it will become unique
        # IMPORTANT: we need to specify the source mesh of the quantity not other mesh

        concat_quantity_name = quantity_name
        # print(" Q=", quantity_name, " T=", concat_quantity_name)
        if concat_quantity_name in self.coupling_quantities:
            ret = self.coupling_quantities[concat_quantity_name]
            ret.list_of_solvers[solver.name] = solver
            # print(" 1 source mesh = ", source_mesh_name, " read= ", read)
            # if this is the solver how reads it then we store it in a special way
            if read == True:
                # see which solver is set as source of this quantity
                # print(" Set Solver name ", solver.name, " for i=", concat_quantity_name)
                ret.source_solver = solver
                ret.source_mesh_name = source_mesh_name
            return  ret
        ret = get_quantity_object(quantity_name, bc, concat_quantity_name)
        self.coupling_quantities[concat_quantity_name] = ret
        ret.list_of_solvers[solver.name] = solver
        # print(" 2 source mesh = ", source_mesh_name, " read= " , read)
        # if this is the solver how reads it then we store it in a special way
        if read == True:
            # see which solver is set as source of this quantity
            # print(" Set Solver name ", solver.name, " for i=", concat_quantity_name)
            ret.source_solver = solver
            ret.source_mesh_name = source_mesh_name
        return ret

    def get_mesh_by_name(self, mesh_name: str):
        """ returns the mesh specified by name """
        # VERY IMPORTANT: the naming convention of the mesh !!!
        # Therefore the mesh name should be constructed only by the methods from this class
        if mesh_name in self.meshes:
            return self.meshes[mesh_name]
        # create a new mesh and add it to the dictionary
        new_mesh = PS_Mesh()
        new_mesh.name = mesh_name
        self.meshes[mesh_name] = new_mesh
        return self.meshes[mesh_name]

    def get_mesh_name_by_participants(self, source_participant:str, participant2:str):
        """ constructs the mash name out of the two participant names. """
        # IMPORTANT:  "ParticipantSource_Participant2_Mesh" -> naming convention is that the
        # first participant is the source (provider) of the mesh
        # list = [ participant1, participant2]
        # list.sort()
        mesh_name = source_participant + "-Mesh"
        return mesh_name

    def get_mesh_by_participant_names(self, source_participant:str, participant2:str):
        """ returns the mesh specified by the two participant names """
        mesh_name = self.get_mesh_name_by_participants(source_participant, participant2)
        mesh = self.get_mesh_by_name(mesh_name)
        return mesh

    def add_quantity_to_mesh(self, mesh_name: str, quantity: QuantityCouple):
        """ Adds the quantity to a given mesh"""
        if mesh_name in self.meshes:
            mesh = self.meshes[mesh_name]
            mesh.add_quantity(quantity)
        pass

    def get_solver(self, solver_name:str):
        """ returns the solver if exists """
        if solver_name in self.solvers:
            return self.solvers[solver_name]
        # TODO: create solver ... ?
        return None

    def create_config(self, user_input: UI_UserInput):
        """Creates the main preCICE config from the UI structure."""

        self.exchanges = user_input.exchanges.copy()

        # participants
        for participant_name in user_input.participants:
            participant_obj = user_input.participants[participant_name]
            list = participant_obj.list_of_couplings
            self.solvers[participant_name] = PS_ParticipantSolver(participant_obj, list[0], self)

        # should we do something for the couplings?
        # the couplings are added to the participants already
        max_coupling_value = 100
        for coupling in user_input.couplings:
            # for all couplings, configure the solvers properly
            participant1_name = coupling.partitcipant1.name
            participant2_name = coupling.partitcipant2.name
            participant1_solver = self.solvers[participant1_name]
            participant2_solver = self.solvers[participant2_name]
            max_coupling_value = min(max_coupling_value, coupling.coupling_type.value)

            temp_d = {}
            data_forward = ""
            data_backward = ""

            for d in self.exchanges:
                if d["from"] == participant1_name and d["to"] == participant2_name:
                    temp_d = d
                    data_forward = d["data"]
                if d["to"] == participant1_name and d["from"] == participant2_name:
                    temp_d = d
                    data_backward = d["data"]

            # ========== FSI =========
            if coupling.coupling_type == UI_CouplingType.fsi:
                # VERY IMPORTANT: we rely here on the fact that the participants are sorted alphabetically
                print("HIT 1")
                participant1_solver.make_participant_fsi_fluid(
                    self, coupling.boundaryC1, coupling.boundaryC2, participant2_solver.name )
                participant2_solver.make_participant_fsi_structure(
                    self, coupling.boundaryC1, coupling.boundaryC2, participant1_solver.name)
                pass
            # ========== F2S =========
            if coupling.coupling_type == UI_CouplingType.f2s:
                print("HIT 2")
                # VERY IMPORTANT: we rely here on the fact that the participants are sorted alphabetically
                participant1_solver.make_participant_f2s_fluid(
                    self, coupling.boundaryC1, coupling.boundaryC2, participant2_solver.name )
                participant2_solver.make_participant_f2s_structure(
                    self, coupling.boundaryC1, coupling.boundaryC2, participant1_solver.name)
                pass
            # ========== CHT =========
            if coupling.coupling_type == UI_CouplingType.cht:
                # VERY IMPORTANT: we rely here on the fact that the participants are sorted alphabetically
                print("PART 1: ", participant1_name)
                print("PART 2: ", participant2_name)
                participant1_solver.make_participant_cht_fluid(
                    self, coupling.boundaryC1, coupling.boundaryC2, participant2_solver.name, data_forward, data_backward)
                participant2_solver.make_participant_cht_structure(
                    self, coupling.boundaryC1, coupling.boundaryC2, participant1_solver.name, data_forward, data_backward)
                pass
            pass

        # Determine coupling scheme based on new coupling type logic or existing max_coupling_value
        if hasattr(user_input, 'coupling_type') and user_input.coupling_type is not None:
            if user_input.coupling_type == 'strong':
                self.couplingScheme = PS_ImplicitCoupling()
            elif user_input.coupling_type == 'weak':
                self.couplingScheme = PS_ExplicitCoupling()
            else:
                # Fallback to existing logic if invalid type
                self.couplingScheme = PS_ImplicitCoupling() if max_coupling_value < 2 else PS_ExplicitCoupling()
        else:
            # Use existing logic if no coupling type specified
            self.couplingScheme = PS_ImplicitCoupling() if max_coupling_value < 2 else PS_ExplicitCoupling()
            #throw an error if no coupling type is specified and the coupling scheme is not compatible with the coupling type
            #raise ValueError("No coupling type specified and coupling scheme is not compatible with the coupling type " + ("explicit" if self.couplingScheme is PS_ExplicitCoupling() else "implicit"))
        
        # Initialize coupling scheme with user input
        self.couplingScheme.initFromUI(user_input, self)

        pass

    def write_precice_xml_config(self, filename:str, log:UT_PCErrorLogging, sync_mode: str, mode: str):
        """ This is the main entry point to write preCICE config into an XML file"""

        self.sync_mode = sync_mode  # Store sync_mode
        self.mode = mode  # Store mode

        nsmap = {
            "data": "data",
            "mapping": "mapping",
            "coupling-scheme": "coupling-scheme",
            "post-processing": "post-processing",
            "m2n": "m2n",
            "master": "master"
        }

        precice_configuration_tag = etree.Element("precice-configuration", nsmap=nsmap)


        # write out:
        # first get the dimensionality of the coupling
        dimensionality = 0
        for solver_name in self.solvers:
            solver = self.solvers[solver_name]
            dimensionality = max ( dimensionality, solver.dimensionality )
            pass

        # 1 quantities
        for coupling_quantities_name in self.coupling_quantities:
            coupling_quantity = self.coupling_quantities[coupling_quantities_name]
            mystr = "scalar"
            if coupling_quantity.dim > 1:
                mystr = "vector"
                pass
            data_tag = etree.SubElement(precice_configuration_tag, etree.QName("data:"+mystr),
                                        name=coupling_quantity.name)
            pass

        # 2 meshes
        for mesh_name in self.meshes:
            mesh = self.meshes[mesh_name]
            mesh_tag = etree.SubElement(precice_configuration_tag, "mesh", name=mesh.name, dimensions=str(dimensionality))
            for quantities_name in mesh.quantities:
                quant = mesh.quantities[quantities_name]
                quant_tag = etree.SubElement(mesh_tag, "use-data", name=quant.instance_name)

        # Initialize dictionaries to store provide and receive meshes
        self.solver_provide_meshes = {}
        self.solver_receive_meshes = {}

        # 3 participants
        m2n_pairs_added = set()
        for solver_name in self.solvers:
            solver = self.solvers[solver_name]
            solver_tag = etree.SubElement(precice_configuration_tag,
                                          "participant", name=solver.name)

            # Initialize lists for this solver's provide and receive meshes
            self.solver_provide_meshes[solver_name] = []
            self.solver_receive_meshes[solver_name] = []

            # there are more then one meshes per participant
            for solvers_mesh_name in solver.meshes:
                # print("Mesh=", solvers_mesh_name)
                solver_mesh_tag = etree.SubElement(solver_tag,
                                              "provide-mesh", name=solvers_mesh_name)
                # Save provided meshes
                self.solver_provide_meshes[solver_name].append(solvers_mesh_name)

                list_of_solvers_with_higher_complexity = {}
                type_of_the_mapping = {} # for each solver for the mapping
                                        # we also save the type of mapping (conservative / consistent)
                list_of_solvers_with_higher_complexity_read = {}
                type_of_the_mapping_read = {}
                list_of_solvers_with_higher_complexity_write = {}
                type_of_the_mapping_write = {}
                # write out the quantities that are either read or written
                # -------------------------------------------------
                # | Collect all the solvers and mappings from the coupling
                # -------------------------------------------------
                used_meshes = {}
                for q_name in solver.quantities_read:
                    q = solver.quantities_read[q_name]
                    read_tag = etree.SubElement(solver_tag,
                                                       "read-data", name=q.name, mesh=solvers_mesh_name)
                    for other_solvers_name in q.list_of_solvers:
                        other_solver = q.list_of_solvers[other_solvers_name]
                        # consistent only read
                        if other_solvers_name != solver_name \
                                and q.is_consistent:
                            #print(" other solver:", other_solvers_name, " solver", solver_name)
                            list_of_solvers_with_higher_complexity[other_solvers_name] = other_solver
                            type_of_the_mapping[other_solvers_name] = q.mapping_string
                            list_of_solvers_with_higher_complexity_read[other_solvers_name] = other_solver
                            type_of_the_mapping_read[other_solvers_name] = q.mapping_string
                            # within one participant put the "use-mesh" only once there
                            if solvers_mesh_name != q.source_mesh_name and \
                                            q.source_mesh_name not in used_meshes:
                                solver_mesh_tag = etree.SubElement(solver_tag,
                                                                   "receive-mesh", name=q.source_mesh_name,
                                                                   from___=q.source_solver.name)
                                # Save received meshes
                                if solver_name not in self.solver_receive_meshes:
                                    self.solver_receive_meshes[solver_name] = []
                                if q.source_mesh_name not in self.solver_receive_meshes[solver_name]:
                                    self.solver_receive_meshes[solver_name].append(q.source_mesh_name)
                                used_meshes[q.source_mesh_name] = 1
                                pass
                    pass
                for q_name in solver.quantities_write:
                    q = solver.quantities_write[q_name]
                    write_tag = etree.SubElement(solver_tag,
                                                       "write-data", name=q.name, mesh=solvers_mesh_name)
                    for other_solvers_name in q.list_of_solvers:
                        other_solver = q.list_of_solvers[other_solvers_name]
                        # conservative only write
                        if other_solvers_name != solver_name \
                                and not q.is_consistent:
                            #print(" other solver:", other_solvers_name, " solver", solver_name)
                            list_of_solvers_with_higher_complexity[other_solvers_name] = other_solver
                            type_of_the_mapping[other_solvers_name] = q.mapping_string
                            list_of_solvers_with_higher_complexity_write[other_solvers_name] = other_solver
                            type_of_the_mapping_write[other_solvers_name] = q.mapping_string
                    pass

                # do the mesh mapping on the more "complex" side of the computations, to avoid data intensive traffic
                # for each mesh we look if the belonging solver has higher complexity

                # READS
                for other_solver_name in list_of_solvers_with_higher_complexity_read:
                    other_solver = list_of_solvers_with_higher_complexity_read[other_solver_name]
                    mapping_string = type_of_the_mapping_read[other_solver_name]
                    other_solver_mesh_name = self.get_mesh_name_by_participants(other_solver_name, solver_name)
                    mapped_tag = etree.SubElement(solver_tag, "mapping:nearest-neighbor", direction = "read",
                                                  from___ = other_solver_mesh_name, to= solvers_mesh_name,
                                                  constraint = mapping_string)
                    self.mappings_read.append({
                        'other_solver_name': other_solver_name,
                        'from': other_solver_mesh_name,
                        'to': solvers_mesh_name,
                        'constraint': mapping_string
                    })
                
                # WRITES
                for other_solver_name in list_of_solvers_with_higher_complexity_write:
                    other_solver = list_of_solvers_with_higher_complexity_write[other_solver_name]
                    mapping_string = type_of_the_mapping_write[other_solver_name]
                    other_solver_mesh_name = self.get_mesh_name_by_participants(other_solver_name, solver_name)
                    mapped_tag = etree.SubElement(solver_tag, "mapping:nearest-neighbor", direction="write",
                                              from___ = solvers_mesh_name, to = other_solver_mesh_name,
                                              constraint = mapping_string)
                    self.mappings_write.append({
                        'other_solver_name': other_solver_name,
                        'from': solvers_mesh_name,
                        'to': other_solver_mesh_name,
                        'constraint': mapping_string
                    })
                # treat M2N communications with other solver
                for other_solver_name in list_of_solvers_with_higher_complexity:
                    if solver_name == other_solver_name:
                        continue
                    # we also add the M2N construct that is mandatory for the configuration
                    # Check if this pair or its reverse has already been added
                    m2n_pair = tuple(sorted([solver_name, other_solver_name]))
                    if m2n_pair not in m2n_pairs_added:
                        m2n_tag = etree.SubElement(precice_configuration_tag, "m2n:sockets", 
                                                   acceptor=solver_name, 
                                                   connector=other_solver_name, 
                                                   exchange___directory="..")
                        m2n_pairs_added.add(m2n_pair)
                pass

        # 4 coupling scheme
        # TODO: later this migh be more complex !!!
        self.couplingScheme.write_precice_xml_config(precice_configuration_tag, self)

        # =========== generate XML ===========================

        xml_string = etree.tostring(precice_configuration_tag, #pretty_print=True, xml_declaration=True,
                                    encoding="UTF-8")
        # Remove xmlns:* attributes which are not recognized by preCICE
        # print( " STR: ", xml_string)
        from_index = xml_string.decode("ascii").find("<precice-configuration")
        to_index = xml_string.decode("ascii").find(">", from_index)
        xml_string = xml_string.decode("ascii")[0:from_index] + "<precice-configuration>" + xml_string.decode("ascii")[
                                                                                            to_index + 1:]
        # just a workaround of how to avoid problems with the parser
        # TODO: later we should find a more elegant solution
        replace_only_list = [("from___", "from"), ("exchange___directory", "exchange-directory")]
        for a,b in replace_only_list:
            xml_string = xml_string.replace(a, b)
        replace_list = [("data:", "data___"), ("mapping:nearest", "mapping___nearest"), ("m2n:", "m2n___" ),
                        ("coupling-scheme:","coupling-scheme___"), ("acceleration:", "acceleration___")]
        for a,b in replace_list:
            xml_string = xml_string.replace(a, b)

        # reformat the XML and add indents
        replaced_str = my_minidom.parseString(xml_string)
        xml_string = replaced_str.toprettyxml(indent="   ")

        for a,b in replace_list:
            xml_string = xml_string.replace(b, a)

        output_xml_file = open(filename, "w")
        output_xml_file.write(xml_string)
        output_xml_file.close()

        log.rep_info("Output XML file: " + filename)

        pass