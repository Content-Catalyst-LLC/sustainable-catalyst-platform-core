# Sustainable Catalyst Platform Core v2.14.0 R1
## Validator Lineage & Promotion Resume Repair

R1 repairs the promotion path for the already-built v2.14.0 Cross-Product Evidence Exchange release.

The original v2.14.0 bundle, manifest, tests and migration 0017 were valid, but deployment stopped after migration because `backend/scripts/validate_streaming_reliability.py` still required the running Core version to equal `2.13.0`. Three later inherited validators carried the same exact-version pattern and would have failed next.

R1 makes inherited feature validators forward-compatible by minimum feature version:

- streaming/reliability requires Core >= 2.9.0;
- operational facilities requires Core >= 2.10.0;
- country evidence requires Core >= 2.12.0;
- Earth/Ocean/Space scientific fabric requires Core >= 2.13.0.

The cross-product exchange runtime, APIs, schemas, migration 0017, source registry and connector registry are unchanged. Core remains version 2.14.0.
