# precice-generate

## Project Overview

The precice-generate is a Python-based utility designed to automate the generation of preCICE configuration files from YAML topology descriptions. This tool simplifies the process of setting up multi-physics simulations by transforming user-defined YAML configurations into preCICE-compatible XML configuration files.

## Key Features

- Automated preCICE configuration generation
- YAML-based input parsing
- Flexible topology description support
- Comprehensive error logging and handling
- Simple command-line interface

## Prerequisites

- **Python 3.11** (Required - not compatible with Python 3.8 or earlier)
- preCICE library
- Dependencies listed in `requirements.txt`

## Installation

### Prerequisites
- Python 3.10 or higher
- pip
- venv

### Manual Installation

1. Clone the repository
```bash
git clone https://github.com/precice-forschungsprojekt/precice-generate.git
cd precice-generate
```

2. Create a virtual environment
```bash
# On Unix/macOS
python -m venv venv
source venv/bin/activate

# On Windows
python -m venv venv
.\venv\Scripts\activate
```

3. Install the project
```bash
# Upgrade pip and install build tools
python -m pip install --upgrade pip
pip install build

# Install the project in editable mode
pip install -e .
```

### Using Setup Scripts

#### Unix/macOS
```bash
./setup_scripts/install_dependencies.sh
```

#### Windows
```powershell
.\setup_scripts\install_dependencies.ps1
```

### Verifying Installation

- Test the CLI tool
```bash
precice-gen --help
```

## Usage

### Command-Line Interface

Generate a preCICE configuration file from a YAML topology:

```bash
precice-gen -f path/to/your/topology.yaml
```

> [!NOTE]
> You should validate your files by running them through [config-checker](https://github.com/precice-forschungsprojekt/config-checker) to avoid errors.

### Configuration

1. Prepare a YAML topology file describing your multi-physics simulation setup.
2. Use the command-line interface to generate the preCICE configuration.
3. The tool will create the necessary configuration files in the `_generated/` directory.


## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/new-feature`)
3. Commit your changes (`git commit -m 'Add new feature'`)
4. Push to the branch (`git push origin feature/new-feature`)
5. Open a Pull Request

## Troubleshooting

- Ensure all dependencies are correctly installed
- Verify the format of your input YAML file
- Check the generated logs for detailed error information

## Acknowledgements

This project was started with code from the [preCICE controller](https://github.com/precice/controller) repository.
The file `format_precice_config.py` was taken from [preCICE pre-commit hook file](https://github.com/precice/precice-pre-commit-hooks/blob/main/format_precice_config/format_precice_config.py)
