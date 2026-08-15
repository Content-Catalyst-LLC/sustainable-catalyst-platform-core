# Sustainable Catalyst Platform Core v2.10.0 R1
## Promotion Assertion & Lineage Repair

R1 is a packaging/promotion repair for the already-validated v2.10.0 Operational Evidence & Facility Registry release.

The original v2.10.0 deployment completed bundle validation, manifest verification, deterministic tests, and migration 0013, but GitHub promotion stopped after the release contract because `PUSH_PLATFORM_CORE_V2100_FINAL.sh` incorrectly asserted that the v2.10.0 build manifest should report release `2.9.0`.

R1 repairs that assertion and two latent promotion-lineage defects that the first failure prevented the script from reaching:

- current deploy-installer syntax validation now targets `deploy_and_validate_platform_core_v2_10_0_macos.sh`;
- inherited streaming/reliability regression execution now correctly targets `backend/tests/test_streaming_alerts_reliability_v290.py`.

No facility-registry runtime behavior, API contract, schema, migration, governed source, or connector definition is changed by R1. Core remains version 2.10.0 with migration lineage through 0013.
