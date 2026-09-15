# Platform Core v2.55.0 — Install and Test

## 1. Validate and promote from macOS

```bash
cd ~/Downloads
rm -rf sc-platform-core-v2.55.0-release
mkdir -p sc-platform-core-v2.55.0-release
unzip -q sustainable-catalyst-platform-core-v2.55.0-release-bundle.zip -d sc-platform-core-v2.55.0-release
cd sc-platform-core-v2.55.0-release
chmod +x deploy_and_validate_platform_core_v2_55_0_macos.sh
./deploy_and_validate_platform_core_v2_55_0_macos.sh "$HOME/Downloads/sustainable-catalyst-platform-core-v2.55.0-release-bundle.zip"
```

Set `SC_CORE_VALIDATE_ONLY=1` for validation without Git promotion or `SC_CORE_BUNDLE_ONLY=1` for frozen-package integrity checks only.

## 2. Deploy backend to Contabo

After `v2.55.0` exists in GitHub:

```bash
ssh -i ~/.ssh/id_ed25519 -o IdentitiesOnly=yes catalystadmin@94.72.113.77
cd /opt/sustainable-catalyst/core
bash DEPLOY_PLATFORM_CORE_V2550_CONTABO.sh
```

The server deployment requires migration 0058 and the complete v2.54 probabilistic/calibration schema before applying/repairing additive migration 0059. It backs up source and PostgreSQL before recreating only the Core container.

## 3. WordPress

Upload `sustainable-catalyst-platform-core-v2.55.0-wordpress-plugin.zip`, replace the prior connector, activate it, and use `[sc_platform_core_predictive_ensembles_status]` for the new status surface.
