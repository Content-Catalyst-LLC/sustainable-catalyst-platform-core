# Platform Core v2.35.0 — Install and Test

Use the release bundle and `deploy_and_validate_platform_core_v2_35_0_macos.sh` for local verification and GitHub promotion. After the GitHub tag exists, deploy the backend with `DEPLOY_PLATFORM_CORE_V2350_CONTABO.sh`, then update the WordPress plugin and verify `[sc_platform_core_scenario_compute_status]`.

The default Mac path runs only the release-critical dependency suite. Set `SC_CORE_FULL_CERTIFICATION=1` only for periodic full historical certification.
