# Platform Core v2.18.0 Install & Test

Run the bundled macOS deployment validator. It verifies SHA-256 checksums, the immutable repository manifest, syntax, the full test-file gate, migrations through `0021`, inherited operational validators, and the v2.18.0 observability validator before GitHub promotion.

## R1 promotion repair

If the original v2.18.0 promotion stopped in `test_production_certification_v2170.py`, use the R1 repair/resume bundle and `repair_and_resume_platform_core_v2_18_0_r1_macos.sh`. R1 corrects the migration-0019 fixture and current-installer promotion lineage; Core remains version 2.18.0.
