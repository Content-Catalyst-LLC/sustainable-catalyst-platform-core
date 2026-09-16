# Platform Core v2.64.0 Install and Test

Run `deploy_and_validate_platform_core_v2_64_0_macos.sh` against the complete release bundle. The validator verifies bundle SHA-256 hashes, the frozen repository manifest, push-safe secret scanning, language syntax, the full historical release test list, migration `0068`, and the Linked Views & Cross-Filtering invariant validator before GitHub promotion.

Production deployment uses `DEPLOY_PLATFORM_CORE_V2640_CONTABO.sh` and requires v2.63.0 / migration `0067` plus all eight Analytical Visualization Grammar tables.
