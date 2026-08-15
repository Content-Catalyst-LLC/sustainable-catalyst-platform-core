# Sustainable Catalyst Core v2.10.0 — Operational Evidence & Facility Registry

Released: 2026-08-14

This release makes physical and civic facilities first-class evidence objects. Facility identity is stable; operational conditions are dated observations. Core never treats absence of a report as normal operation and does not merge different observation dimensions into a synthetic status.

## Facility classes
Hospital, clinic, health center, school, university, shelter, water facility, power facility, crossing, port, airport, communications facility, food distribution, warehouse, and other governed facilities.

## Observation dimensions
Operational status, damage status, access status, service status, capacity status, supply status, and other explicitly described status evidence.

## Provenance
Every observation can preserve publisher, source/connector, source-record ID, source URL, evidence class, geography, methodology, confidence, services, constraints, details and provenance metadata.

## Migration
Additive migration `0013`; no destructive migration.

## API surface

Internal/operator:
- `GET /v1/facilities/readiness`
- `POST /v1/facilities`
- `GET /v1/facilities`
- `GET /v1/facilities/{facility_id}`
- `POST /v1/facilities/{facility_id}/observations`
- `GET /v1/facilities/{facility_id}/observations`

Public/scoped:
- `GET /api/v1/facilities`
- `GET /api/v1/facilities/{facility_id}`
- `GET /api/v1/facilities/{facility_id}/observations`

A facility observation can emit a persisted `facility.observation.created` event into the inherited v2.9.0 reliability stream.
