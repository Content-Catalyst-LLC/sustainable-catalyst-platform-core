# International Law and United Nations Connector Pack v2.7.1

Platform Core v2.7.1 extends the free live-data gateway with official UN document, human-rights, humanitarian, demographic, displacement, trade, and SDG methodology integrations.

## Active connectors

- `un.digital-library`
- `un.sdg-metadata`
- `ocha.reliefweb-reports` — requires a free pre-approved `SC_CORE_RELIEFWEB_APPNAME`
- `ocha.hdx-hapi`
- `un.population-data`
- `un.comtrade`
- `unhcr.population`
- `ohchr.uhri-recommendations` — requires the free endpoint information supplied by OHCHR in `SC_CORE_UHRI_API_URL`

## Governed metadata-only sources

The UN Treaty Collection, International Court of Justice, and International Law Commission are registered as official sources, but v2.7.1 does not scrape them because no general public API is documented. Future connectors must preserve the same access and licensing gate.

## Authority model

The dedicated `international_law_records` table separates treaty obligations, reviewed Security Council decisions, official Security Council resolutions whose binding effect still requires legal review, judgments, advisory opinions, recommendatory resolutions, human-rights recommendations, official reports, humanitarian reporting, statistical observations, and commentary. This prevents legally different sources from being displayed as equivalent.

## APIs

Internal:

- `GET /v1/international-law/records`
- `GET /v1/international-law/records/{id}`
- `GET /v1/international-law/provenance/{id}`
- `GET /v1/international-law/authority-taxonomy`
- `GET /v1/international-law/stats`

Scoped public:

- `GET /api/v1/international-law/records`
- `GET /api/v1/international-law/records/{id}`
- `GET /api/v1/international-law/authority-taxonomy`

Public routes require the existing `data:read` scope.


## Legal caution

The connector classifies `S/RES/...` records as official Security Council resolutions, but it does not automatically label them binding. Binding effect requires reviewed analysis of the UN Charter basis, operative language, addressees, and legal context. The source connector performs metadata normalization, not legal advice or autonomous legal conclusions.

## Configuration states

- `configured`: connector can run with the current environment.
- `registration_required`: the free ReliefWeb application name has not been configured.
- `endpoint_registration_required`: OHCHR has not yet supplied/configured the free UHRI endpoint documentation.
- `credential_required`: the optional free FRED key has not been configured.

Connectors fail closed when required registration details are missing.
