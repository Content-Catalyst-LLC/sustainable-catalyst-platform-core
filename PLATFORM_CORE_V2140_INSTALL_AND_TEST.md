# Platform Core v2.14.0 — Install and Test

Use the release bundle with `deploy_and_validate_platform_core_v2_14_0_macos.sh`.

The installer verifies component checksums, the immutable repository manifest, Python/PHP/Bash syntax, the complete file-by-file Core regression line, migrations through `0017`, and the cross-product exchange validator before promotion.

Set `SC_CORE_BUNDLE_ONLY=1` to verify the release bundle without installing dependencies or pushing GitHub.


## R1 promotion repair
Use `repair_and_resume_platform_core_v2_14_0_r1_macos.sh` with the `REPAIRED-R1` bundle when resuming the interrupted v2.14.0 promotion. R1 changes release-validation lineage only; Core remains v2.14.0 with migration 0017.
