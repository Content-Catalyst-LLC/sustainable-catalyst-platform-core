# Platform Core v3.25.0 — Unified Computational Job Runtime

Added:
- `sc.core.computational-job.v1`
- governed cross-runtime computational jobs;
- explicit runtime-adapter/provider binding;
- deterministic job fingerprints;
- validated job lifecycle transitions;
- attempt lineage;
- event lineage;
- retry policy;
- environment requirement binding;
- provider-neutral dispatch envelopes;
- result identity validation;
- artifact binding model;
- Julia v0.3.0 reference job;
- public job-runtime contract endpoint;
- 13 focused release tests.

No database migration is introduced in v3.25.0.

Execution remains external to Core. Workspace/runtime providers execute jobs;
Core governs their identity, contracts, lineage and reproducibility.

Next: Platform Core v3.26.0 — Julia Runtime Core Integration.
