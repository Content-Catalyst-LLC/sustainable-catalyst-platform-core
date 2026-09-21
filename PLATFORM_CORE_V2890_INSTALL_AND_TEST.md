# Install and Test v2.89.0

1. Validate the release bundle with `deploy_and_validate_platform_core_v2_89_0_macos.sh`.
2. Promote with `PUSH_PLATFORM_CORE_V2890_FINAL.sh`.
3. Deploy on Contabo with `DEPLOY_PLATFORM_CORE_V2890_CONTABO.sh`.
4. Verify `/health` and `/v1/research/quality-audits/readiness`.
