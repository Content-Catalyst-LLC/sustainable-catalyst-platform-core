# Scientific Data Connector Pack v2.7.2

Sustainable Catalyst Platform Core v2.7.2 extends the governed free live-data gateway with normalized discovery and ingestion for Earth science, climate, hydrology, biomedical science, chemistry, biodiversity, materials science, and astronomy.

## Design rules

- Only free-access providers are registered.
- Credit-card-required services are excluded.
- Free-registration credentials remain optional or fail closed until configured.
- Product applications use Core APIs rather than provider-specific code.
- Raw responses are bounded, hashed, and linked to normalized records.
- Provider identifiers, licenses, attribution, access links, and retrieval timestamps are retained.
- TAP/ADQL requests are read-only and reject destructive or non-`SELECT` statements.
- Scientific records are discovery and evidence records; they do not imply scientific validation or clinical suitability.

## Connector inventory

| Connector | Domain | Default access | Output |
|---|---|---:|---|
| `nasa.cmr-collections` | Earth science | Configured | Earth-science dataset records |
| `nasa.apod` | Astronomy | Configured with `DEMO_KEY` | Astronomy image records |
| `noaa.ncei-data` | Weather and climate | Configured | Environmental observations |
| `ecmwf.open-data-index` | Weather and climate | Configured | Forecast-field metadata |
| `usgs.water-instantaneous` | Hydrology | Configured | Water observations |
| `ncbi.entrez-search` | Biomedical | Configured; optional key | Biomedical database identifiers |
| `pubchem.compound-properties` | Chemistry | Configured | Chemical compound records |
| `gbif.occurrences` | Biodiversity | Configured | Biodiversity occurrence records |
| `materials-project.summary` | Materials science | Free key required | Material records |
| `mast.observations` | Astronomy | Configured | Telescope observation records |
| `heasarc.xamin` | Astronomy | Configured | Astronomy catalog records |
| `irsa.tap` | Astronomy | Configured | TAP astronomy catalog records |
| `eso.tap` | Astronomy | Configured | TAP astronomy catalog records |

The pack adds 13 connectors over 12 official scientific source records. IRSA and ESO share the governed read-only TAP adapter.

## Configuration

```env
SC_CORE_NASA_API_KEY=DEMO_KEY
SC_CORE_NCBI_API_KEY=
SC_CORE_MATERIALS_PROJECT_API_KEY=
```

`SC_CORE_NASA_API_KEY=DEMO_KEY` is suitable for development. A free registered key can replace it without changing connector code. NCBI operates without a key at lower request allowance. Materials Project remains `credential_required` until a free API key is configured.

## Normalized scientific record

Migration `0009` adds `scientific_data_records`. Each record can preserve:

- source and connector identifiers
- raw-response provenance
- provider record identifier
- record type and scientific discipline
- title and summary
- dataset, collection, mission, instrument, and target
- DOI and provider access links
- geometry and observation period
- identifiers, keywords, variables, and file formats
- quality status, license, and attribution
- stable content hash and provider metadata
- public visibility and timestamps

The schema is published at `schemas/scientific-data-record-v1.schema.json`.

## Internal APIs

```text
GET /v1/science/records
GET /v1/science/records/{record_id}
GET /v1/science/provenance/{record_id}
GET /v1/science/record-types
GET /v1/science/stats
```

Record filters include:

- `record_type`
- `discipline`
- `source_id`
- `connector_id`
- `collection`
- `mission`
- `instrument`
- `target`
- `dataset_id`
- free-text `query`
- observation `start` and `end`

## Scoped public APIs

The following routes require a Unified Public API credential with `data:read`:

```text
GET /api/v1/science/records
GET /api/v1/science/records/{record_id}
GET /api/v1/science/record-types
```

Private records and raw provider payloads are not exposed through public routes.

## Example ingestion commands

```bash
python backend/scripts/sync_live_data.py \
  --connector nasa.cmr-collections \
  --run-type manual \
  --parameters '{"keyword":"climate","page_size":10}'

python backend/scripts/sync_live_data.py \
  --connector pubchem.compound-properties \
  --run-type manual \
  --parameters '{"compound":"aspirin"}'

python backend/scripts/sync_live_data.py \
  --connector mast.observations \
  --run-type manual \
  --parameters '{"target":"M31","limit":25}'

python backend/scripts/sync_live_data.py \
  --connector irsa.tap \
  --run-type manual \
  --parameters '{"query":"SELECT TOP 25 * FROM fp_psc"}'
```

Provider query fields are validated and bounded. The TAP connector accepts only a single read-only `SELECT` statement.

## Product handoffs

- **Site Intelligence:** climate, water, hazard, biodiversity, and map-ready observation discovery.
- **Research Lab:** scientific datasets, compounds, materials, telescope observations, and reproducible analysis inputs.
- **Workbench:** time-series, physical, chemical, statistical, and astronomical calculations.
- **Decision Studio:** source-aware scientific evidence for decision packets.
- **Knowledge Library:** dataset, method, license, citation, and provenance records.
- **Research Librarian:** cross-source scientific discovery and product routing.

## Operational boundaries

Core stores metadata and bounded provider responses. It does not mirror unrestricted scientific archives, bypass provider limits, or treat metadata discovery as permission to redistribute every referenced file. Large FITS, NetCDF, Zarr, GeoTIFF, and related scientific assets remain provider-hosted until the v2.8.0 scientific-file fabric introduces explicit storage and retention policies.
