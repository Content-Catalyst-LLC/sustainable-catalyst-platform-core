# Platform Core v4.21.0 — Parameterized Connector Execution Profiles

## Purpose

v4.21.0 turns the parameter requirements already declared by Platform Core's live-data connectors into governed, named execution profiles.

The release does **not** convert arbitrary search APIs into uncontrolled polling. It preserves the v4.20.3 split between:

1. zero-parameter scheduled connectors,
2. periodic connectors that require governed parameter sets, and
3. manual/search connectors.

## Contract

Contract: `sc.core.parameterized-connector-execution-profile.v1`

The reference registry covers the 22 non-manual connectors whose catalog contracts require parameters or one-of selectors.

Each profile declares connector identity, domain, execution mode, bounded parameters, required caller bindings, refresh policy, scheduler eligibility, priority, retry policy, explicit scope, tags, provenance, deterministic fingerprint, and epistemic boundaries.

## Execution modes

`scheduled` profiles resolve all connector requirements without user input and may be considered by the parameterized scheduler.

`template` profiles intentionally require a research selection such as a place, SDG series, dataset, company, table, energy route, FAOSTAT domain, or SDMX key. They never auto-execute.

## Safe scheduler activation

Parameterized scheduling is disabled by default:

```text
SC_CORE_PARAMETERIZED_PROFILE_SCHEDULER_ENABLED=false
```

An optional allowlist further constrains automatic execution:

```text
SC_CORE_PARAMETERIZED_PROFILE_IDS=profile:nasa-cmr:climate-collections,profile:world-bank:us-gdp-per-capita
```

Backpressure is explicit:

```text
SC_CORE_PARAMETERIZED_PROFILE_MAX_PER_PASS=12
```

The existing zero-parameter scheduler remains unchanged.

## Profile execution lineage

Each queued profile uses:

```text
requested_by=connector-profile:<profile-id>
```

This gives every profile an independent activity clock and duplicate-work boundary even when multiple future profiles share a connector.

## Dynamic parameters

The resolver supports bounded runtime tokens:

- `{{today}}`
- `{{current_year}}`
- `{{year_minus_N}}`
- `{{date_minus_Nd}}`
- `{{ecmwf_date}}`
- `{{ecmwf_run}}`

The ECMWF resolver applies an eight-hour lag before choosing the latest six-hour operational cycle, reducing premature requests for files that may not yet be fully published.

## Reference registry

The 22 profiles cover:

- MET Norway
- World Bank
- FRED
- UN SDG Metadata
- UN Population
- UN Comtrade
- NASA CMR
- NOAA NCEI
- ECMWF
- USGS Water
- IMF
- OECD
- Eurostat
- ECB
- BIS
- BEA
- BLS
- U.S. Census
- SEC EDGAR
- EIA
- FAOSTAT
- ILOSTAT

Nine profiles are scheduler-eligible reference candidates. Thirteen remain caller-bound templates.

Because scheduling is disabled by default, scheduler eligibility is not a claim that a provider profile has already passed production ingestion. Readiness and one-shot smoke testing remain required before enablement.

## API surfaces

Internal:

- `GET /v1/connector-profiles/contract`
- `GET /v1/connector-profiles/profiles`
- `GET /v1/connector-profiles/profiles/{profile_id}`
- `GET /v1/connector-profiles/readiness`
- `POST /v1/connector-profiles/profiles/{profile_id}/queue`
- `GET /v1/connector-profiles/reference`

Public read-only:

- `GET /public/v1/connector-profiles/contract`
- `GET /public/v1/connector-profiles/profiles`

## Credential boundary

Credentials never belong in profile parameters or durable work items. FRED, BEA, EIA, IMF and other provider credentials continue to come only from deployment settings. Credential-like keys are rejected by the profile resolver.

## Epistemic boundary

A profile is a reproducible provider-request contract, not a truth claim.

Execution success does not establish that a source is correct, does not automatically promote observations into evidence, and does not imply global coverage beyond the declared profile scope.

Manual/search connectors remain manual in v4.21.0.

## Database

No database migration.
