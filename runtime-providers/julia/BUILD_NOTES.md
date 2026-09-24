# Build notes — Catalyst Julia Runtime v0.3.0

Scope: Core Runtime Contract Adapter.

Implemented:
- Platform Core `sc.core.runtime-adapter.v1` identity.
- Platform Core computational runtime object contract identity.
- Ten required adapter lifecycle methods.
- Core-shaped execution request/run/result bridge.
- Registered provider status.
- Existing v0.2 environment reproducibility retained.
- Existing governed numerical operations retained.
- Backward-compatible v0.2 execution endpoints retained.
- Python adapter client expanded to the ten-method contract.
- VPS deployment proof validates prepare → execute → inspect → collect.

Not implemented:
- arbitrary Julia source execution;
- persistent universal execution registry;
- external file artifacts;
- package installation at execution time;
- distributed/GPU scheduling;
- autonomous scientific-method selection.

Those are deliberately outside this release.
