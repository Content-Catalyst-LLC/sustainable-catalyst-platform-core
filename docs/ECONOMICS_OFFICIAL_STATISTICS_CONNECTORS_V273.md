# Economics and Official Statistics Connector Pack v2.7.3

Sustainable Catalyst Core v2.7.3 adds a provider-neutral economics record layer and governed free connectors for IMF, OECD, Eurostat, ECB, BIS, BEA, BLS, Census, SEC EDGAR, EIA, FAOSTAT, and ILOSTAT. Existing World Bank, FRED, and UN Comtrade connectors remain available.

## Free-source policy

No connector requires a paid subscription or credit card. IMF current API access, BEA, and EIA are fail-closed until their free registration details are configured through environment variables. Optional BLS and Census keys are also environment-only. Census and BLS can operate without a key at public limits. SEC access uses an identifying User-Agent and bounded requests.

## Record model

Migration `0010` creates `economic_data_records`. Records preserve indicator and dataset identifiers, geography and counterpart codes, period and frequency, value and unit, seasonal and price bases, release/vintage context, dimensions, source links, license, attribution, content hashes, visibility, and raw-ingestion provenance.

## Routes

- `GET /v1/economics/records`
- `GET /v1/economics/records/{record_id}`
- `GET /v1/economics/provenance/{record_id}`
- `GET /v1/economics/record-types`
- `GET /v1/economics/stats`
- `GET /api/v1/economics/records`
- `GET /api/v1/economics/records/{record_id}`
- `GET /api/v1/economics/record-types`

Public routes require `data:read`.

## Freshness and market-data boundary

The pack integrates official statistics, releases, filings, revisions, energy observations, and delayed or periodic indicators. It does not claim free real-time exchange market data. Interfaces must display the source-reported frequency and release/vintage context.


## Credential handling

Provider credentials are read only from environment settings. Ingestion-run parameters are recursively redacted before persistence, and normalized source URLs remove credential-bearing query values. BLS and Census request payloads cannot override the environment-managed registration keys.
