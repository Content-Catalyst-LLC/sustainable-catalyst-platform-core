# Platform Core v2.56.0 Install & Test

1. Run `deploy_and_validate_platform_core_v2_56_0_macos.sh` against the release bundle.
2. Confirm the full release regression set passes and Git tag `v2.56.0` is created.
3. On Contabo run `DEPLOY_PLATFORM_CORE_V2560_CONTABO.sh`.
4. Verify `/health` reports `2.56.0` and `/v1/predictive-intelligence/readiness` reports `migration_0060_applied: true`.
