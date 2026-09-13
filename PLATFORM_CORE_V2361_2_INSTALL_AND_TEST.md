# Platform Core v2.36.1.2 — Install and Test

1. Run bundle-only validation on macOS.
2. Run release-critical validation and GitHub promotion.
3. Promote `main` and tag `v2.36.1.2`.
4. Copy `DEPLOY_PLATFORM_CORE_V2361_2_CONTABO.sh` to `/tmp` on the VPS.
5. Run the deployer; it verifies the v2.36 production uncertainty schema and safely accepts the partial-0040 table state from the failed v2.36.1.1 deployment.
6. Confirm migration `0040` is recorded with `pending: []`.
7. Install the v2.36.1.2 WordPress plugin and verify `[sc_platform_core_uncertainty_compute_status]`.
8. Continue with v2.37.0 only after backend verification.
