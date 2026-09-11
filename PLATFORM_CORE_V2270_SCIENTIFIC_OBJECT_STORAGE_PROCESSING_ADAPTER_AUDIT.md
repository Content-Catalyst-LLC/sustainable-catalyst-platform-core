# Platform Core v2.27.0 — Scientific Object Storage & Processing Adapter Audit

v2.27.0 is additive to the existing scientific asset registry. It introduces four persistent control-plane records: storage backends, stored scientific objects, processing adapters, and processing runs.

## Implemented

- migration `0030` and deterministic default registry seeds;
- bounded local filesystem ingestion with atomic writes and SHA-256 integrity hashing;
- stable external-reference records for `https`, `s3`, `gs`, and `az` URIs without fetching provider content;
- rejection of credential-bearing, query-bearing, or fragment-bearing provider URLs;
- parent/derived object lineage and processing-run provenance;
- deterministic built-in `builtin.object-manifest` processing adapter;
- contract-only xarray, GDAL, and Astropy adapters, explicitly non-executable in this release;
- internal read/write/process APIs and public-safe metadata-only APIs;
- certification/readiness hooks, Platform Core stats, SDK methods, WordPress status surface, and deployment configuration.

## Explicit non-capabilities

v2.27.0 does **not** execute arbitrary user code, persist credential values, retrieve provider-managed external objects, expose stored object bytes through the public API, provide native raster/scientific parsing workers, or claim S3/GCS/Azure write adapters. Those boundaries are deliberate.

## Security properties

Local object keys resolve beneath the configured storage root, upload size is bounded, object content is verified against its recorded SHA-256 hash on access, external references must be stable credential-free URIs, and public listings are restricted to records marked public.
