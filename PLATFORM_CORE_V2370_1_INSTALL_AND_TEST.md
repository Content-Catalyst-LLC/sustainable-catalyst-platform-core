# Platform Core v2.37.0.1 — Install and Test

1. Run bundle-only validation.
2. Run release-critical validation and GitHub promotion.
3. Copy `DEPLOY_PLATFORM_CORE_V2370_1_CONTABO.sh` to `/tmp/` on Contabo.
4. Run it from the VPS. The preflight accepts a pristine causal state, the safe partial-0041 state, or an already-recorded 0041 state; mixed causal-table states hard-stop.
5. Install the v2.37.0.1 WordPress plugin after backend success.
