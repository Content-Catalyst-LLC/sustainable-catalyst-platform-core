# Platform Core v2.40.0 — Cross-Product Visual Research Objects

v2.40.0 makes a visual research object portable across Sustainable Catalyst products without collapsing those products into one runtime.

A governed cross-product object contains product-scoped members, explicit semantic relations, saved composite views, provenance, immutable snapshots, and reference-first portability packages. Members may point to Platform Core, Knowledge Library, Research Librarian, Lab, Workbench, Site Intelligence, Decision Studio, Catalyst Data, or an external system.

Core preserves source-product identity and validates local bindings. Non-Core members must carry an explicit external reference or source-reference object. Core never silently fetches remote state or converts a remote reference into a local truth claim.

## Execution boundary

Platform Core owns semantics, provenance, validation, snapshots, portability, and renderer-neutral composition contracts. Remote product retrieval, numerical/model execution, specialist analysis, truth merging, layout execution, and rendering remain outside Core.
