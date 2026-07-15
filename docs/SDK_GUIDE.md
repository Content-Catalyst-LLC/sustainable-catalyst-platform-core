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
