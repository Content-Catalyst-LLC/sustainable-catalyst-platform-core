# Platform Core v2.27.0 — Scientific Object Storage & Processing Adapter Fabric

- Adds migration `0030` with scientific storage backends, stored objects, processing adapters, and processing runs.
- Adds bounded local scientific-object ingestion with SHA-256 integrity verification and generated content-addressed object keys.
- Adds credential-free provider-managed references for stable `https`, `s3`, `gs`, and `az` object URIs.
- Adds parent/derived object lineage and idempotent processing-run provenance.
- Adds an executable deterministic `builtin.object-manifest` adapter.
- Registers xarray, GDAL, and Astropy processing contracts as disabled/non-executable until real workers are configured.
- Adds internal object metadata/content APIs and scoped public metadata APIs; public object bytes are not exposed.
- Adds Python and JavaScript SDK helpers, WordPress status surface, deployment settings, release validation, and regression tests.
- Adds optional production-certification readiness gating for the scientific object storage layer.
- Arbitrary code execution, automatic external fetching, credential persistence, native scientific-file parsing, storage purchasing, and automatic distributed replication remain disabled.
