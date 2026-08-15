# Platform Core v2.16.0 Install and Test

Run `deploy_and_validate_platform_core_v2_16_0_macos.sh sustainable-catalyst-platform-core-v2.16.0-release-bundle.zip`. The installer verifies checksums and manifest, runs each backend test file independently, migrates a fresh smoke database through 0019, runs inherited operational validators, validates governance, then promotes to GitHub unless validation-only mode is set.
