# Platform Core v2.25.0 — Install & Test

Use the release bundle and macOS deployment script from Downloads.

```bash
cd ~/Downloads
chmod +x deploy_and_validate_platform_core_v2_25_0_macos.sh
./deploy_and_validate_platform_core_v2_25_0_macos.sh sustainable-catalyst-platform-core-v2.25.0-release-bundle.zip
```

The script verifies bundle checksums, immutable repository manifest, release contract, push-safe secret scan, Python/PHP/JavaScript/shell syntax, all backend test modules, migrations through `0028`, inherited operational validators, the new credential/key lifecycle validator, and the connector-worker smoke path before promotion.
