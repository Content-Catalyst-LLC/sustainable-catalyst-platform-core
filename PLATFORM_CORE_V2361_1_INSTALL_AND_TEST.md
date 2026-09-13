# Platform Core v2.36.1.1 — Install and Test

1. Run bundle-only validation on macOS.
2. Run the 83-test release-critical gate and schema-contract compatibility tests.
3. Promote `main` and tag `v2.36.1.1`.
4. Copy `DEPLOY_PLATFORM_CORE_V2361_1_CONTABO.sh` to `/tmp` on the VPS.
5. Run the deployer. It backs up the repository and PostgreSQL, verifies the existing v2.36.0 production schema before migration, applies migration 0040, recreates Core, and validates public readiness.
6. Install the v2.36.1.1 WordPress plugin and verify `[sc_platform_core_uncertainty_compute_status]`.

The v2.36.1 deployment attempt failed before container recreation. Do not manually alter the production sensitivity/ensemble tables to make v2.36.1 fit; use this repair release instead.
