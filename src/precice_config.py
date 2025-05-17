from topology_input import TopologyInput
import xml.etree.ElementTree as etree
from controller_utils.myutils.UT_PCErrorLogging import UT_PCErrorLogging

class PreciceConfig:
    """Class to represent the preCICE configuration."""

    def __init__(self):
        """ Ctor """
        self.topology = TopologyInput()
        self.meshes = {}
        self.meshes_to_receive = {}
        pass

    def determine_mesh_reception(self):
        """ Identify which meshes each participant needs to receive """
        for exchange in self.topology.exchanges:
            receiver = exchange["to"]
            sender = exchange["from"]
            receiver_patch = exchange["to-patch"]
            sender_patch = exchange["from-patch"]
            
            # Ensure receiver gets the correct mesh from sender
            if receiver not in self.meshes_to_receive:
                self.meshes_to_receive[receiver] = {}
            
            self.meshes_to_receive[receiver][receiver_patch] = {
                "from": sender,
                "from_patch": sender_patch
            }

    def print_mesh_reception(self):
        """ Display mesh reception logic """
        for receiver, patches in self.meshes_to_receive.items():
            print(f"Participant {receiver} receives meshes at:")
            for patch, details in patches.items():
                print(f"  - Patch {patch} receives from {details['from']} (patch {details['from_patch']})")

    def init_participants(self):
        """ Initialize participants """
        #TODO receive mesh
        for exchange in self.topology.exchanges:
            for p in self.topology.participants:
                if exchange['from'] == p.name:
                    # This participant is writing data
                    if exchange['data'] not in p.write_data:
                        p.write_data.append(exchange['data'])
                elif exchange['to'] == p.name:
                    # This participant is reading data
                    if exchange['data'] not in p.read_data:
                        p.read_data.append(exchange['data'])

    def write_precice_xml_config(self, filename:str, log:UT_PCErrorLogging):
        """ This is the main entry point to write preCICE config into an XML file"""
        # create the root element
        root = etree.Element("precice-configuration")

        topology = self.topology

        for data, data_type in topology.data_from_exchanges:
            mystr = "scalar"
            if data_type is not None:
                mystr = data_type
            data_tag = etree.SubElement(root, etree.QName("data:"+mystr),
                                        name=data)
            pass

        # output_xml_file = open(filename, "w")
        # output_xml_file.write(etree.tostring(root, encoding="UTF-8", method="xml"))
        # output_xml_file.close()
        print(etree.tostring(root, encoding="UTF-8", method="xml"))