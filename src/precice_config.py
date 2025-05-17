from topology_input import TopologyInput
import xml.etree.ElementTree as etree
from controller_utils.myutils.UT_PCErrorLogging import UT_PCErrorLogging

class PreciceConfig:
    """Class to represent the preCICE configuration."""

    def __init__(self):
        """ Ctor """
        self.topology = TopologyInput()
        pass

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