# v2.30.0 Visualization Specification & Renderer Registry Audit

- Migration `0033`: required.
- Visualization specifications: immutable revision records with SHA-256 state hashes.
- Renderer definitions: contract metadata only; authorized registration APIs are supported.
- Renderer package installation: not asserted.
- Renderer execution by Core: false.
- Layout execution by Core: false.
- Render-output generation/storage by Core: false.
- Compatibility selection: deterministic and advisory.
- Resolution history: persisted with rationale and `execution_performed=false`.
- v2.29 visual reasoning semantics: retained and now report the Core renderer registry as available.
- Automatic truth promotion: not introduced.
