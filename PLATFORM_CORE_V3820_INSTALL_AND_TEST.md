# Platform Core v3.82.0 Install and Test

## Mac apply / Git push

```bash
cd ~/Downloads
rm -rf sc-core-v3.82.0-relationship-discovery
unzip -q platform-core-v3.82.0-relationship-discovery-connection-hypothesis-objects-release-bundle.zip -d sc-core-v3.82.0-relationship-discovery
cd sc-core-v3.82.0-relationship-discovery
chmod +x REPAIR_PLATFORM_CORE_V3820.py APPLY_AND_PUSH_PLATFORM_CORE_V3820.sh DEPLOY_PLATFORM_CORE_V3820_CONTABO.sh PACKAGE_PLATFORM_CORE_V3820.sh
./APPLY_AND_PUSH_PLATFORM_CORE_V3820.sh "$HOME/Downloads/sustainable-catalyst-platform-core"
```

## Contabo deployment

Copy `DEPLOY_PLATFORM_CORE_V3820_CONTABO.sh` to `/tmp`, SSH to the Core host, then run it. The deployer validates the tagged source, rebuilds the Core service, runs the v3.82 validator and targeted test suite, and verifies the local and public contract endpoints.

Database migration: none.
