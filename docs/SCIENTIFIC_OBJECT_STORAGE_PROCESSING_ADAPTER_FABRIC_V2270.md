# Platform Core v2.27.0 — Scientific Object Storage & Processing Adapter Fabric

## Purpose

v2.27.0 closes the gap between the v2.8.0 scientific-asset registry and executable scientific workflows. Platform Core can now register where scientific bytes live, ingest bounded local objects, preserve integrity metadata and parent/derived lineage, and route processing through governed adapter contracts.

The release is intentionally provider-neutral. It does not require S3, Google Cloud Storage, Azure Blob Storage, GDAL, xarray, Astropy, or another paid service in order for Core to start and validate.

## New persistent objects

Migration `0030` adds four record families:

- `scientific_storage_backends` — provider-neutral backend capabilities, not credentials.
- `scientific_stored_objects` — stable scientific object metadata, integrity hashes, storage location, visibility, retention class, and lineage.
- `scientific_processing_adapters` — declared runtimes, formats, operations, and executable/contract-only state.
- `scientific_processing_runs` — idempotent processing requests, input/output lineage, parameters, state, and provenance.

## Storage modes

### Local filesystem

Development and test installations can ingest bounded object bytes directly into a configured storage root. Core:

- computes SHA-256 before persistence;
- generates the object key itself;
- writes atomically through a temporary file;
- prevents path traversal by resolving every path under the configured root;
- records an `sc-object://` canonical URI rather than exposing the local filesystem path;
- verifies the content hash before serving internal object bytes.

The default upload ceiling is 64 MiB and is configurable up to 1 GiB.

### External reference

Core can register stable credential-free references using `https`, `s3`, `gs`, and `az` schemes. External objects remain provider-managed in v2.27.0. Core does not fetch or mirror them automatically.

Query-bearing/signed URLs, URL user-info credentials, secrets, and private keys are not accepted as canonical scientific object references.

## Processing adapter registry

The migration seeds four adapters:

| Adapter | State | Purpose |
| --- | --- | --- |
| `builtin.object-manifest` | enabled + executable | Deterministic JSON manifest derived from a stored scientific object |
| `external.xarray` | contract only | Future NetCDF/Zarr/GRIB inspect, subset, aggregate, and rechunk worker |
| `external.gdal` | contract only | Future raster/vector translation, reprojection, overview, and tiling worker |
| `external.astropy` | contract only | Future FITS/VOTable inspection and extraction worker |

Contract-only adapters cannot execute. This prevents capability metadata from being mistaken for a configured scientific runtime.

## Derived-object lineage

Every processing result can point to a parent stored object. The built-in manifest adapter creates a new stored JSON object with:

- `derived = true`;
- `parent_object_id` set to the input object;
- the processing run ID in metadata/provenance;
- the input integrity and storage metadata embedded in the manifest.

Processing runs are idempotent on adapter + input object + operation + idempotency key.

## Routes

Internal:

```text
GET  /v1/scientific-objects/readiness
GET  /v1/scientific-objects
GET  /v1/scientific-objects/{object_id}
GET  /v1/scientific-objects/{object_id}/content
PUT  /v1/scientific-objects/upload/{format}
POST /v1/scientific-objects/register-reference
GET  /v1/scientific-objects/adapters
POST /v1/scientific-objects/process
GET  /v1/scientific-objects/processing-runs/{run_id}
```

Scoped public metadata:

```text
GET /api/v1/scientific-objects/readiness
GET /api/v1/scientific-objects
GET /api/v1/scientific-objects/{object_id}
GET /api/v1/scientific-objects/adapters
```

Public APIs expose metadata for public objects only. They never expose locally stored object bytes.

## Configuration

```text
SC_CORE_SCIENTIFIC_OBJECT_STORAGE_ENABLED=true
SC_CORE_SCIENTIFIC_OBJECT_STORAGE_ROOT=./var/scientific-objects
SC_CORE_SCIENTIFIC_OBJECT_MAX_UPLOAD_BYTES=67108864
SC_CORE_SCIENTIFIC_PROCESSING_ENABLED=true
SC_CORE_SCIENTIFIC_OBJECT_PUBLIC_METADATA_ENABLED=true
SC_CORE_CERTIFICATION_REQUIRE_SCIENTIFIC_OBJECT_STORAGE_READY=false
```

The storage root should be mounted on durable storage in production. v2.27.0 does not provision or purchase storage.

## Explicit boundaries

v2.27.0 does **not**:

- execute arbitrary user code;
- shell out to arbitrary commands;
- fetch external objects automatically;
- persist object-store credentials or signed URLs;
- claim native parsing of NetCDF, Zarr, FITS, GRIB2, COG, GeoParquet, or VOTable;
- enable the seeded xarray, GDAL, or Astropy contracts automatically;
- mutate source scientific assets when a derived object is created;
- provide automatic lifecycle deletion of scientific bytes;
- provide distributed object replication.

Those capabilities can be added behind the adapter/storage contracts in later releases without changing the scientific object identity model.

## Relationship to existing Core capabilities

v2.27.0 complements rather than replaces:

- v2.8.0 `ScientificDataAsset` registry and STAC fabric;
- v2.15.0 distributed processing/storage control plane;
- v2.22.0 lifecycle/preservation controls;
- v2.24.0 capacity governance;
- v2.26.0 workload admission controls.

The new scientific stored object is a governed storage/processing identity; the existing scientific asset remains the source-aware discovery and handoff record.
