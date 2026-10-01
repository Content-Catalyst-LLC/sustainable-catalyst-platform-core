# Platform Core v3.91.0 — Unified Runtime Policy & Capability Negotiation

## Purpose

v3.91.0 adds the governed control plane around the v3.90 unified entity/evidence runtime. It describes runtime capabilities, consumer requirements, version/contract compatibility, scope negotiation, explicit degradation, fail-closed/reference-only fallbacks, and reproducible negotiation traces.

## Architectural rules

- Capability discovery is descriptive, not a truth or authority signal.
- Negotiation must preserve upstream contract identity, epistemic state, provenance, review gates, and local-validation gates.
- Granted scopes are limited to the intersection of the consumer declaration and capability requirement.
- Degraded operation must be explicit and may only preserve or reduce authority.
- Contract compatibility is not content validation and does not establish factual truth.
- Candidate/hypothesis/evidence status may not be promoted by negotiation.
- No identity, relationship, or evidence graph mutation is performed.

## Reference control plane

The synthetic reference registry exposes 14 capabilities (v3.77–v3.90), seven downstream consumers, 17 capability requirements/decisions, one explicit federation degradation fallback, seven auditable negotiation traces, and one immutable capability-registry snapshot.

## Database migration

None.
