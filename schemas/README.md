# Multi-Physics Simulation Topology Schema

## Overview

This JSON schema provides a comprehensive configuration mechanism for defining multi-physics simulation topologies, specifically designed for complex coupling scenarios in scientific computing and engineering simulations.

## Schema Structure

The topology schema consists of four main sections:

### 1. Coupling Scheme Configuration
- Flexible time window and iteration controls
- Support for parallel and serial coupling modes
- Optional display of standard values
- Configurable maximum time and iterations

#### Key Parameters
- `max-time`: Maximum simulation time (integer or scientific notation)
- `time-window-size`: Size of time windows (number or scientific notation)
- `max-iterations`: Maximum coupling iterations
- `coupling`: Coupling mode (parallel/serial)

### 2. Acceleration Mechanisms
Advanced coupling acceleration with multiple configuration options:

#### Acceleration Methods
- Supported methods: `constant`, `aitken`, `IQN-ILS`, `IQN-IMVJ`
- Initial relaxation factor
- Preconditioner configuration
- Filtering options (QR1/QR2)

#### Advanced Features
- Iteration and time window reuse
- IMVJ restart mode configuration
- Singular value truncation
- Preconditioner freezing

### 3. Participants Configuration
Define simulation participants with detailed specifications:

- Mandatory fields: `name`, `solver`
- Optional fields: 
  - `dimensionality` (default: 3)
- Minimum of 2 participant required

### 4. Exchanges Configuration
Each exchange defines a one-way data transfer between participants:

#### Required Fields
- `from`: Name of the source participant sending data (must match a name in the participants section)
- `to`: Name of the target participant receiving data (must match a name in the participants section)
- `data`: Type of data being exchanged (e.g., Force, Displacement, Velocity)
- `type`: Coupling type defining the exchange interaction
  - `strong`: Tight coupling with immediate data synchronization
  - `weak`: Loose coupling with less frequent data exchange
- `from-patch`: Source Interface Surface
  - The physical boundary or interface region on the source participant's mesh where data is extracted.
  - Must correspond to a defined boundary condition in the source solver.
  - For fluids: Typically the fluid-structure interface (e.g., "interface")
  - For solids: Typically the surface contacting the fluid (e.g., "surface")
- `to-patch`: Target Interface Surface
  - The physical boundary or interface region on the target participant's mesh where data will be applied.
  - Must correspond to a defined boundary condition in the target solver.

#### Optional Fields
- `data-type`: Specifies the data representation
  - `scalar`: Single numeric value (default)
  - `vector`: Multi-dimensional numeric data

#### Data Type Constraints
- Supported data types: Force, Displacement, Velocity, Pressure, Temperature, HeatTransfer
- Naming follows the pattern: `[BaseType][OptionalModifier]`

#### Example
```yaml
coupling-scheme:
  display_standard_values: true
participants:
  - name: Fluid
    solver: SU2
  - name: Solid
    solver: Calculix
exchanges:
  - from: Fluid
    from-patch: interface      # Fluid side boundary where forces are measured
    to: Solid
    to-patch: surface         # Solid surface receiving fluid forces
    data: Force
    type: strong
  - from: Solid
    from-patch: surface       # Solid surface where displacements occur
    to: Fluid
    to-patch: interface      # Fluid boundary that adapts to displacements
    data: Displacement
    type: strong
```

## Schema Validation Rules

- Requires `coupling-scheme`, `participants`, and `exchanges`
- Optional `acceleration` configuration
- Supports scientific notation for numeric values
- Strict type and enumeration constraints

## Compatibility and Best Practices

- Designed for preCICE coupling framework
- Supports complex multi-physics simulations
- Flexible configuration for various scientific computing scenarios

## Limitations

- Predefined acceleration and exchange methods
- Strict schema validation

## Future Extensions

- Potential expansion of acceleration methods
- Enhanced data exchange types
- More flexible validation rules

## Contributing

Contributions to expand and improve the schema are welcome. Please follow the project's contribution guidelines.