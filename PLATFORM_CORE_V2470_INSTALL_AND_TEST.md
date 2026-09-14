# Platform Core v2.47.0 — Install and Test

1. Verify the release bundle with `SC_CORE_BUNDLE_ONLY=1 ./deploy_and_validate_platform_core_v2_47_0_macos.sh <bundle>`.
2. Run the same script without bundle-only mode to execute release-critical tests and promote to GitHub.
3. Deploy the backend before WordPress using `DEPLOY_PLATFORM_CORE_V2470_CONTABO.sh`.
4. Production must already contain migration `0050` and all eight v2.46 forensic spatial/temporal tables.
5. Install the WordPress plugin only after backend readiness is green.
