# Platform Core v3.25.0 Audit

PASS criteria:
- predecessor v3.24.0 contract remains intact;
- one computational job abstraction spans runtime providers;
- job provider selection is explicit;
- job lifecycle transitions are validated;
- terminal jobs cannot be reopened;
- attempts retain runtime/environment lineage;
- jobs can bind v3.24 environment requirements;
- job fingerprints exclude mutable lifecycle state;
- dispatch envelope is provider-neutral;
- result identity is bound to the originating request/runtime;
- Core remains a semantic/governance layer, not the execution host;
- no duplicate execution persistence tables are created.
