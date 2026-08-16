# Platform Core v2.23.1 Capability Metadata / Documentation / Release-Lineage Audit

## Observed drift

The v2.23.0 repository had a current runtime at `2.23.0`, but its top-level README still opened at v2.19.0. More importantly, `/v1/meta` still listed two v2.9.0-delivered capabilities as deferred:

- `distributed_connector_workers`
- `server_sent_live_data_events`

The repository itself contained runtime and regression evidence for both capabilities.

## Repair

v2.23.1 aligns all current release surfaces and promotes those two capability identifiers into the implemented capability list. It adds a dedicated regression test and release validator so implemented and deferred sets must remain disjoint and the repaired capabilities must retain runtime implementation evidence.

## Schema and semantic boundary

No migration is added. Migration head remains `0026`. The release does not alter data models, federation trust semantics, evidence precedence, governance policy, preservation policy, or public/private exposure rules.

## Promotion gate

Promotion requires:

- release contract validation;
- immutable manifest verification;
- Python/PHP/JavaScript/shell syntax checks;
- the complete backend test suite;
- migration application through `0026` with zero pending migrations;
- all existing operational validators;
- capability-lineage validator;
- secret scan;
- clean release bundle checksum verification.
