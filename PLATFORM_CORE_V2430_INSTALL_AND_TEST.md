# Install and test v2.43.0

1. Run `SC_CORE_BUNDLE_ONLY=1 ./deploy_and_validate_platform_core_v2_43_0_macos.sh <bundle>`.
2. Run the same validator without `SC_CORE_BUNDLE_ONLY` to execute tests and promote GitHub.
3. Deploy the backend with `DEPLOY_PLATFORM_CORE_V2430_CONTABO.sh`.
4. Install the WordPress plugin only after backend deployment succeeds.
