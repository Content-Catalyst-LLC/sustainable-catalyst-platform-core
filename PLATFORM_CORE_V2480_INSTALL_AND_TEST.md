# Platform Core v2.48.0 — Install and Test

1. Run the bundle-only validation gate.
2. Run the full macOS validation/promotion script to execute release-critical tests and promote `main` + immutable tag `v2.48.0`.
3. Confirm v2.47.0 is already live in production.
4. Copy `DEPLOY_PLATFORM_CORE_V2480_CONTABO.sh` to the VPS and run it.
5. Install the v2.48.0 WordPress plugin after backend deployment succeeds.
6. Optional status shortcode: `[sc_platform_core_forensic_quantitative_reconstruction_status]`.

The Contabo deployer accepts only a pristine pre-0052 state, a safe partial state where all eight v2.48 tables exist but the `0052` ledger row is missing, or an already-complete `0052` state.
