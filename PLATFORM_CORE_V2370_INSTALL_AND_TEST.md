# Platform Core v2.37.0 — Install and Test

Platform Core v2.37.0 must be promoted from the deployed v2.36.1.2 baseline.

1. Run `deploy_and_validate_platform_core_v2_37_0_macos.sh` with `SC_CORE_BUNDLE_ONLY=1` to verify the downloaded release bundle.
2. Run the same script without `SC_CORE_BUNDLE_ONLY` to execute the release-critical test gate and promote `main` plus tag `v2.37.0`.
3. Copy `DEPLOY_PLATFORM_CORE_V2370_CONTABO.sh` to `/tmp/` on the Contabo VPS and execute it.
4. The deployer requires migration `0040` to be recorded, preserves the repaired v2.36 uncertainty schema, applies additive migration `0041`, recreates `sc-core`, and verifies local/public causal-system readiness.
5. Install the v2.37.0 WordPress plugin only after the backend completes successfully.

Expected shortcode: `[sc_platform_core_causal_systems_status]`.
