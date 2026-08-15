# v2.22.0 Install and Test

Run `deploy_and_validate_platform_core_v2_22_0_macos.sh sustainable-catalyst-platform-core-v2.22.0-release-bundle.zip`. The installer verifies bundle hashes, release contract, immutable manifest, syntax, the file-by-file backend test gate, migrations through 0025, all inherited validators, lifecycle preservation validation, connector worker smoke, and then invokes the GitHub push script unless validate-only mode is enabled.
