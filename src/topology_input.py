from pathlib import Path
import yaml

class TopologyInput:
    """Class to read a topology YAML file and extract the necessary information."""

    def __init__(self, topology_path: Path):
        """Initialize the topology input with the path to the topology YAML file."""
        self.topology_path = topology_path

    def create_etree(self, etree) -> dict:
        """Create a etreeuration dictionary from the topology YAML file."""

        # Set default values for coupling-scheme
        coupling_scheme = etree.get('coupling-scheme', {})
        if not coupling_scheme.get('display_standard_values', False):
            coupling_scheme.setdefault('max-time', 1e-3)
            coupling_scheme.setdefault('time-window-size', 1e-3)
            coupling_scheme.setdefault('max-iterations', 50)
            coupling_scheme.setdefault('coupling', 'parallel')
            coupling_scheme.setdefault('display_standard_values', False)

        # Set default values for acceleration
        acceleration = etree.get('acceleration', {})
        if not acceleration.get('display_standard_values', False):
            acceleration.setdefault('name', 'IQN-ILS')
            if 'initial-relaxation' in acceleration:
                initial_relaxation = acceleration['initial-relaxation']
                initial_relaxation.setdefault('enforce', False)
            if 'preconditioner' in acceleration:
                preconditioner = acceleration['preconditioner']
                preconditioner.setdefault('freeze-after', -1)
            if 'filter' in acceleration:
                filter_etree = acceleration['filter']
                filter_etree.setdefault('limit', 1e-16)
            if 'imvj-restart-mode' in acceleration:
                restart_mode = acceleration['imvj-restart-mode']
                restart_mode.setdefault('truncation-threshold', 0.0001)
                restart_mode.setdefault('chunk-size', 8)
                restart_mode.setdefault('reused-time-windows-at-restart', 8)
                restart_mode.setdefault('type', 'RS-SVD')
            acceleration.setdefault('display_standard_values', False)

        # Set default values for participants
        participants = etree.get('participants', [])
        for participant in participants:
            participant.setdefault('dimensionality', 3)

        # Set default values for exchanges
        exchanges = etree.get('exchanges', [])
        for exchange in exchanges:
            exchange.setdefault('data-type', 'scalar')

        # Set the processed etree back
        etree['coupling-scheme'] = coupling_scheme
        etree['acceleration'] = acceleration
        etree['participants'] = participants
        etree['exchanges'] = exchanges

        return etree
        
