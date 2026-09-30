# Platform Core v3.84.0 — Install and Test

## Apply locally

```bash
cd ~/Downloads
rm -rf sc-core-v3.84.0-connection-paths
unzip -q platform-core-v3.84.0-explainable-connection-paths-evidence-chains-release-bundle.zip -d sc-core-v3.84.0-connection-paths
cd sc-core-v3.84.0-connection-paths
chmod +x REPAIR_PLATFORM_CORE_V3840.py APPLY_AND_PUSH_PLATFORM_CORE_V3840.sh DEPLOY_PLATFORM_CORE_V3840_CONTABO.sh PACKAGE_PLATFORM_CORE_V3840.sh
./APPLY_AND_PUSH_PLATFORM_CORE_V3840.sh "$HOME/Downloads/sustainable-catalyst-platform-core"
```

The repair accepts predecessor `3.83.0` or an already-applied `3.84.0` checkout.

## Backend deployment

```bash
scp -i ~/.ssh/id_ed25519 -o IdentitiesOnly=yes DEPLOY_PLATFORM_CORE_V3840_CONTABO.sh catalystadmin@94.72.113.77:/tmp/
ssh -i ~/.ssh/id_ed25519 -o IdentitiesOnly=yes catalystadmin@94.72.113.77
chmod +x /tmp/DEPLOY_PLATFORM_CORE_V3840_CONTABO.sh
/tmp/DEPLOY_PLATFORM_CORE_V3840_CONTABO.sh
```

## Expected verification

- Core health version `3.84.0`
- contract `sc.core.explainable-connection-paths-evidence-chains.v1`
- targeted validator PASS
- targeted pytest suite PASS
- public endpoint `/public/v1/connection-paths/contract`
- relationship/evidence/identity graph mutation flags remain false
