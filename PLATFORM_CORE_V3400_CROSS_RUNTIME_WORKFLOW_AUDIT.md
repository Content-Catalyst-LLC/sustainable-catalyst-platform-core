# Platform Core v3.40.0 Audit

PASS criteria:
- workflow graph identities are unique;
- dependency graph is acyclic;
- runtime bindings are explicit and versioned;
- computational steps require runtime bindings;
- runtime handoffs match workflow dependencies;
- source/target runtimes match source/target steps;
- readiness blocks hard/data dependencies until complete;
- readiness blocks cross-runtime targets until handoff verification;
- topological ordering is deterministic;
- execution events preserve provenance;
- completed workflow requires verification;
- workflow verification fingerprints steps and handoffs;
- portable packages bind definition and run fingerprints;
- workflow package can bridge into v3.38 Scientific Artifact Registry;
- Core does not execute steps or schedule jobs;
- Core does not autonomously choose runtimes/formats;
- no database migration is introduced.
