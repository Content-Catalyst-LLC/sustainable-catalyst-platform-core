# Platform Core v3.47.0 — Octave Runtime

v3.47.0 adds a governed GNU Octave runtime to the Platform Core runtime fabric.

Core contract: `sc.core.octave-runtime.v1`  
Runtime ID: `sc-runtime-octave`  
Adapter ID: `adapter:sc-runtime-octave`  
Provider version: `1.0.0`  
Native runtime: GNU Octave 8.4.0

## v1 operations

- matrix multiplication
- linear-system solving
- eigenvalue analysis
- singular-value decomposition
- fast Fourier transform
- polynomial roots

The provider generates fixed Octave programs internally from validated numeric
payloads. It does not accept arbitrary Octave source, shell commands, caller
filesystem paths, or runtime package installation.

## Product integration

Octave is added to the v3.44 unified runtime catalog.

Core-side clients:
- Workspace
- Research Lab
- Workbench

Workbench gains Octave specifically for numerical engineering and linear
algebra, while Stan remains excluded from the Workbench profile.

## Execution boundary

Platform Core owns runtime identity, adapter registration, security and
environment contracts, runtime discovery/binding, provenance and exchange.

The Octave provider executes the fixed native numerical operations.

Workspace or another execution host owns orchestration.

Products own method selection and scientific interpretation.

No database migration.

Next mapped build:
Platform Core v3.48.0 — gretl/hansl Runtime.
