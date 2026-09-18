# Platform Core v2.71.0 — Install and Test

Use `deploy_and_validate_platform_core_v2_71_0_macos.sh` against the exact release bundle. The validator verifies bundle checksums, repository/plugin/backend ZIP integrity, the frozen build manifest, dependency-free release invariants, secret scanning, Python/PHP/JavaScript/Bash syntax, the full historical regression list, a clean migration `0075` smoke database, and Cross-Product Visual Runtime Integration invariants before Git promotion.

Production deployment uses `DEPLOY_PLATFORM_CORE_V2710_CONTABO.sh`. It requires migration `0074` and all nine v2.70 Unified Visual Reasoning Engine tables before migration `0075` can be applied.
