# Platform Core v2.57.0 Install & Test

1. Validate the release bundle on macOS with `deploy_and_validate_platform_core_v2_57_0_macos.sh`.
2. Promotion is allowed only after the full historical regression list passes.
3. Deploy to Contabo with `DEPLOY_PLATFORM_CORE_V2570_CONTABO.sh` only after v2.56.0 / migration 0060 is live.
4. Verify `/health` and `/v1/predictive-intelligence/readiness` report release 2.57.0 and migration 0061.
