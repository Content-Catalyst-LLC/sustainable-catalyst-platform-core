# Platform Core v2.19.0 — Install and Test

Use `deploy_and_validate_platform_core_v2_19_0_macos.sh` with the v2.19.0 release bundle. The installer verifies component checksums, clean extraction, the immutable manifest, file-by-file pytest execution, migrations through `0022`, operational validators, static syntax, secret scan, then commits/pushes only after all gates pass.
