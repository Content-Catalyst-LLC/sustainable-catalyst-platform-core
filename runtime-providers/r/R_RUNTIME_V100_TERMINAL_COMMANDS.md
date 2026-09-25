# Sustainable Catalyst R Runtime v1.0.0 — Terminal Commands

The R provider normally deploys automatically as part of Platform Core v3.36.0.

For a provider-only redeploy after v3.36.0 has been pushed:

```bash
ssh -i ~/.ssh/id_ed25519 -o IdentitiesOnly=yes catalystadmin@94.72.113.77

cd /opt/sustainable-catalyst/core
git checkout main
git pull --ff-only origin main

chmod +x runtime-providers/r/deploy/DEPLOY_SC_RUNTIME_R_V100_CONTABO.sh
chmod +x runtime-providers/r/deploy/VERIFY_SC_RUNTIME_R_V100.sh

runtime-providers/r/deploy/DEPLOY_SC_RUNTIME_R_V100_CONTABO.sh   /opt/sustainable-catalyst/core/runtime-providers/r
```

Live verification only:

```bash
cd /opt/sustainable-catalyst/core
runtime-providers/r/deploy/VERIFY_SC_RUNTIME_R_V100.sh
```

Targets:

`PASS - SUSTAINABLE CATALYST R RUNTIME v1.0.0 LIVE VERIFICATION COMPLETE`

`PASS - SUSTAINABLE CATALYST R RUNTIME v1.0.0 BACKEND DEPLOYMENT COMPLETE`
