# Platform Core v2.54.0 — Install and Test

## 1. Validate and promote from macOS

```bash
cd ~/Downloads
chmod +x deploy_and_validate_platform_core_v2_54_0_macos.sh
./deploy_and_validate_platform_core_v2_54_0_macos.sh \
  "$HOME/Downloads/sustainable-catalyst-platform-core-v2.54.0-release-bundle.zip"
```

Set `SC_CORE_VALIDATE_ONLY=1` to run package, migration, SDK, PHP/JS, and Python test validation without committing/tagging/pushing. Set `SC_CORE_BUNDLE_ONLY=1` to verify frozen package integrity without installing Python dependencies.

## 2. Deploy the tagged release on Contabo

After the macOS promotion script has pushed and tagged `v2.54.0`:

```bash
ssh -i ~/.ssh/id_ed25519 -o IdentitiesOnly=yes catalystadmin@94.72.113.77
cd /opt/sustainable-catalyst/core
bash DEPLOY_PLATFORM_CORE_V2540_CONTABO.sh
```

The server deployment requires migration 0057 and all v2.53 backtesting tables before applying/repairing additive migration 0058. It backs up both source and PostgreSQL before migration and recreates only the Core container.

## 3. WordPress

Upload `sustainable-catalyst-platform-core-v2.54.0-wordpress-plugin.zip`, replace the prior Platform Core connector, activate it, and use `[sc_platform_core_predictive_calibration_status]` wherever a release-console/status surface is desired.
