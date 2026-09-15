# Platform Core v2.60.0 Install and Test

Run the macOS release validator from the extracted release bundle. It verifies bundle hashes, the frozen repository manifest, the full historical regression list, migration `0064`, and reproducible-package invariants before promotion.

Production deployment requires v2.59.0 / migration `0063` and all eight predictive-decision tables. `DEPLOY_PLATFORM_CORE_V2600_CONTABO.sh` performs predecessor checks, backups, exact-tag validation, migration, Core rebuild, readiness checks, and public-route verification.
