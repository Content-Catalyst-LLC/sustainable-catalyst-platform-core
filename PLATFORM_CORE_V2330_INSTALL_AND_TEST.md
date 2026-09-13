# Platform Core v2.33.0 Install and Test

Run `deploy_and_validate_platform_core_v2_33_0_macos.sh` against the v2.33 release bundle. After GitHub promotion, deploy `DEPLOY_PLATFORM_CORE_V2330_CONTABO.sh` to the production VPS. Production migration head is `0036` and `/v1/scenario-landscapes/readiness` must report `migration_0036_applied=true`.
