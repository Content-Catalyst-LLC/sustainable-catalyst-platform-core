# SDK Guide

## Python

Download:

```text
/developers/sdk/python.zip
```

Example:

```python
from sc_platform_core_public import PublicApiClient

client = PublicApiClient(
    "https://YOUR-PLATFORM-CORE.onrender.com",
    "scpk_your_key",
)

print(client.status())
print(client.entities(entity_type="product"))
print(client.verify_ledger())
```

## JavaScript

Download:

```text
/developers/sdk/javascript.zip
```

Example:

```javascript
import { PublicApiClient } from "./index.mjs";

const client = new PublicApiClient(
  "https://YOUR-PLATFORM-CORE.onrender.com",
  "scpk_your_key"
);

console.log(await client.status());
console.log(await client.entities({ entity_type: "product" }));
```

## Direct HTTP

The SDKs intentionally remain thin. Any standards-compliant HTTP client can use the public API directly.

## Signature dossiers and workflows

Python:

```python
print(client.workflow_definitions())
print(client.workflow_run("sc:workflow-run:..."))
print(client.dossiers())
print(client.dossier("sc:dossier:..."))
print(client.verify_dossier("sc:dossier:..."))
```

JavaScript:

```javascript
console.log(await client.workflowDefinitions());
console.log(await client.workflowRun("sc:workflow-run:..."));
console.log(await client.dossiers());
console.log(await client.dossier("sc:dossier:..."));
console.log(await client.verifyDossier("sc:dossier:..."));
```


## International Law and UN v2.7.1

- `GET /api/v1/international-law/records`
- `GET /api/v1/international-law/records/{record_id}`
- `GET /api/v1/international-law/authority-taxonomy`

These routes use the existing `data:read` scope. They return normalized public legal records; raw provider payloads and internal connector configuration remain private.

## Scientific data v2.7.2

Python:

```python
print(client.scientific_records(discipline="astronomy", limit=25))
print(client.scientific_record("RECORD_ID"))
print(client.scientific_record_types())
```

JavaScript:

```javascript
console.log(await client.scientificRecords({ discipline: "astronomy", limit: 25 }));
console.log(await client.scientificRecord("RECORD_ID"));
console.log(await client.scientificRecordTypes());
```

These public methods use `data:read`. Raw provider payloads and internal provenance are intentionally excluded from the public SDK.


## Economics and official statistics v2.7.3

Python:

```python
print(client.economic_records(indicator_code="GDP", geography_code="USA", limit=25))
print(client.economic_record("RECORD_ID"))
print(client.economic_record_types())
```

JavaScript:

```javascript
console.log(await client.economicRecords({ indicator_code: "GDP", geography_code: "USA", limit: 25 }));
console.log(await client.economicRecord("RECORD_ID"));
console.log(await client.economicRecordTypes());
```

These methods use `data:read`. Raw provider payloads and internal connector configuration are intentionally excluded from the public SDK.


## Data fabric v2.8.0

The public SDKs expose fabric capabilities, geospatial features, time-series definitions and points, scientific assets, map layers, and raw STAC catalog/search methods. All methods require `data:read`.

## Scientific object metadata v2.27.0

Python:

```python
print(client.scientific_object_storage_readiness())
print(client.scientific_stored_objects(format="netcdf", limit=25))
print(client.scientific_stored_object("OBJECT_ID"))
print(client.scientific_processing_adapters())
```

JavaScript:

```javascript
console.log(await client.scientificObjectStorageReadiness());
console.log(await client.scientificStoredObjects({ format: "netcdf", limit: 25 }));
console.log(await client.scientificStoredObject("OBJECT_ID"));
console.log(await client.scientificProcessingAdapters());
```

The public SDK exposes public-safe metadata only. Scientific object upload, byte retrieval, processing execution, and processing-run details remain authenticated internal Core operations.

## Research object and model metadata v2.28.0

Python:

```python
print(client.research_object_readiness())
print(client.research_objects(object_type="model", limit=25))
print(client.research_object("sc:model:..."))
print(client.research_project_bundle("sc:research-project:..."))
```

JavaScript:

```javascript
console.log(await client.researchObjectReadiness());
console.log(await client.researchObjects({ object_type: "model", limit: 25 }));
console.log(await client.researchObject("sc:model:..."));
console.log(await client.researchProjectBundle("sc:research-project:..."));
```

These methods use `data:read` and return public-safe research metadata. Lab, Workbench, or external execution services perform model execution; Platform Core records governed model/run/result structure and provenance references.
