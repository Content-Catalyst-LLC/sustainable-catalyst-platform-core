# Platform Core v2.72.0 Install and Test

## macOS validation and Git promotion
```bash
cd ~/Downloads
rm -rf sc-platform-core-v2.72.0-release
mkdir -p sc-platform-core-v2.72.0-release
unzip -q sustainable-catalyst-platform-core-v2.72.0-release-bundle.zip -d sc-platform-core-v2.72.0-release
cd sc-platform-core-v2.72.0-release
chmod +x deploy_and_validate_platform_core_v2_72_0_macos.sh
./deploy_and_validate_platform_core_v2_72_0_macos.sh "$HOME/Downloads/sustainable-catalyst-platform-core-v2.72.0-release-bundle.zip"
```

## VPS
```bash
cd /opt/sustainable-catalyst/core
git fetch origin --tags
git pull --ff-only origin main
git tag --points-at HEAD
chmod +x DEPLOY_PLATFORM_CORE_V2720_CONTABO.sh
bash DEPLOY_PLATFORM_CORE_V2720_CONTABO.sh
```
