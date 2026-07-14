# Sustainable Catalyst Platform Core v2.7.2

## Scientific Data Connector Pack

Released: July 14, 2026

Platform Core v2.7.2 expands the free live-data gateway with governed scientific discovery across Earth science, climate, hydrology, biomedical science, chemistry, biodiversity, materials science, and astronomy.

## Added

- Migration `0009` and the `scientific_data_records` store.
- Thirteen new connector definitions over twelve official scientific sources.
- NASA CMR Earth-science collection discovery.
- NASA Astronomy Picture of the Day normalization.
- NOAA NCEI environmental-data access.
- ECMWF open forecast-index discovery.
- USGS instantaneous water observations.
- NCBI Entrez identifier search.
- PubChem compound-property discovery.
- GBIF biodiversity occurrence discovery.
- Materials Project summary discovery with a free-key configuration gate.
- MAST telescope observation discovery.
- HEASARC astronomy catalog discovery.
- Shared read-only TAP/ADQL discovery for IRSA and ESO.
- Scientific record filtering, statistics, and raw-ingestion provenance.
- Internal `/v1/science` and scoped public `/api/v1/science` routes.
- Python and JavaScript public SDK methods.
- Internal Python client methods.
- WordPress shortcode `[sc_platform_core_science_status]`.
- JSON Schema `scientific-data-record-v1.schema.json`.
- Deployment variables for NASA, NCBI, and Materials Project free keys.

## Governance and safety

- The strict free-source gate remains required.
- Credit-card-required services are not introduced.
- Materials Project fails closed until a free key is configured.
- NCBI can use an optional free key but does not require one.
- NASA APOD defaults to the documented development key setting and can use a free registered key.
- TAP and ADQL connectors accept read-only `SELECT` queries only.
- Provider record licenses and attribution remain attached to normalized records.
- Scientific discovery records do not imply peer review, clinical validity, or permission to redistribute linked scientific files.

## Compatibility

All v2.0.0 through v2.7.1 registry, graph, evidence, public API, trust, dossier, gateway, live-data, international-law, WordPress, and SDK behavior remains available.

## Validation target

- 86 backend tests across the complete regression suite.
- Migrations `0001` through `0009` on a clean database.
- 28 governed source records.
- 27 connector definitions.
- Python, PHP, JavaScript, Bash, and JSON syntax validation.
- Push-safe secret scanning and ZIP integrity validation.
