# Platform Core v2.32.0 Install and Test

Run `deploy_and_validate_platform_core_v2_32_0_macos.sh` against the v2.32 release bundle. After GitHub promotion, deploy `DEPLOY_PLATFORM_CORE_V2320_CONTABO.sh` to the production VPS. Production migration head is `0035` and `/v1/flow-maps/readiness` must report `migration_0035_applied=true`.
