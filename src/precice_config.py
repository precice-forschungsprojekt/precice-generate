from topology_input import TopologyInput
import xml.etree.ElementTree as etree
from controller_utils.myutils.UT_PCErrorLogging import UT_PCErrorLogging

class PreciceConfig:
    """Class to represent the preCICE configuration."""

    def __init__(self):
        """ Ctor """
        self.topology = TopologyInput()
        self.meshes = {}
        pass

    def init_participants(self):
        """ Initialize participants """
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