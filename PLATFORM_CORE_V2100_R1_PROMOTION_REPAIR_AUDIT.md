# Platform Core v2.10.0 R1 — Promotion Assertion & Lineage Repair

## Scope

This repair does not change the v2.10.0 Operational Evidence & Facility Registry runtime, schema, or migration lineage. It repairs the GitHub promotion script that runs after the already-passing v2.10.0 package validation.

## Defects repaired

1. `PUSH_PLATFORM_CORE_V2100_FINAL.sh` asserted that `BUILD_MANIFEST.json.release` was `2.9.0`, causing a correct v2.10.0 manifest to terminate promotion with `AssertionError: 2.10.0`.
2. The same push script shell-validated the v2.9.0 deploy installer instead of the current v2.10.0 installer.
3. The push test list referenced a nonexistent `test_streaming_alerts_reliability_v2100.py` instead of the inherited v2.9.0 reliability regression file `test_streaming_alerts_reliability_v290.py`.

## Repair invariants

- Core release remains `2.10.0`.
- Migration lineage remains through `0013`.
- Facility registry behavior is unchanged.
- Streaming/reliability behavior remains inherited from v2.9.0 and is regression-tested by its original test module.
- The rebuilt manifest must declare `2.10.0` and hash every repaired source file.
- Promotion must not proceed if the repaired script regresses to any of the stale targets above.
