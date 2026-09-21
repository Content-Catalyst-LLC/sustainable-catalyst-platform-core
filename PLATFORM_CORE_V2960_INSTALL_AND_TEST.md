# Platform Core v2.96.0 Install and Test

1. Promote the frozen repository using `PUSH_PLATFORM_CORE_V2960_FINAL.sh`.
2. Confirm tag `v2.96.0` at production HEAD.
3. Run `DEPLOY_PLATFORM_CORE_V2960_CONTABO.sh`.
4. Verify `/health` reports `2.96.0` and `/v1/research/runtime-contract/readiness` reports `migration_0100_applied: true`.
