# Platform Core v2.28.0 Research Object & Model Foundation Audit

## Release intent

Add research/model semantics to Platform Core without duplicating the Universal Entity Registry, Evidence Ledger, Knowledge Graph, Calculation Trace, Provenance Activity, or scientific-object storage systems.

## Architecture checks

- PASS — all eight research types are Universal Entity Registry objects.
- PASS — typed extension tables are additive and use migration `0031`.
- PASS — graph lineage uses existing predicates rather than a second graph model.
- PASS — model versions carry deterministic specification hashes.
- PASS — model runs can reference existing provenance and calculation traces.
- PASS — results can reference existing scientific stored objects.
- PASS — public API is metadata-only and filters private/internal objects.
- PASS — model execution remains outside Platform Core.
- PASS — no automatic evidence/truth promotion exists.
- PASS — no visualization renderer is introduced in this release.

## Product boundary

Lab and Workbench remain the compute systems. Platform Core is the shared identity, provenance, graph, contract, and orchestration foundation.
