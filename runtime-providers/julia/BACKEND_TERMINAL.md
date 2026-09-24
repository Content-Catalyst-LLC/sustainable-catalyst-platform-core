# Backend terminal — Catalyst Julia Runtime v0.3.0

## macOS

```bash
cd ~/Downloads
rm -rf catalyst-julia-runtime-v0.3.0-release
unzip -q catalyst-julia-runtime-v0.3.0-release-bundle.zip \
  -d catalyst-julia-runtime-v0.3.0-release

cd catalyst-julia-runtime-v0.3.0-release

chmod +x \
  PUSH_CATALYST_JULIA_V030.sh \
  VALIDATE_RELEASE_V030.sh \
  deploy/DEPLOY_CATALYST_JULIA_V030_CONTABO.sh \
  deploy/VERIFY_CATALYST_JULIA_V030.sh

./PUSH_CATALYST_JULIA_V030.sh \
  "$HOME/Downloads/sustainable-catalyst-platform-core"
```

## Copy release to Contabo

```bash
scp -i ~/.ssh/id_ed25519 \
  -o IdentitiesOnly=yes \
  catalyst-julia-runtime-v0.3.0-release-bundle.zip \
  catalystadmin@94.72.113.77:/tmp/

ssh -i ~/.ssh/id_ed25519 \
  -o IdentitiesOnly=yes \
  catalystadmin@94.72.113.77
```

## Contabo

```bash
cd /tmp
rm -rf catalyst-julia-runtime-v0.3.0-release
unzip -q catalyst-julia-runtime-v0.3.0-release-bundle.zip \
  -d catalyst-julia-runtime-v0.3.0-release

cd catalyst-julia-runtime-v0.3.0-release
chmod +x deploy/DEPLOY_CATALYST_JULIA_V030_CONTABO.sh \
  deploy/VERIFY_CATALYST_JULIA_V030.sh

./deploy/DEPLOY_CATALYST_JULIA_V030_CONTABO.sh "$PWD"
```

Target final line:

`PASS - CATALYST JULIA RUNTIME v0.3.0 BACKEND DEPLOYMENT COMPLETE`
