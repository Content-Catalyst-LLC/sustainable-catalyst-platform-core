# Platform Core v3.77.0 Install and Test

## Required predecessor

Platform Core v3.76.0. The repair script is idempotent on v3.77.0.

## macOS apply

```bash
cd ~/Downloads
rm -rf sc-core-v3.77.0-entity-resolution
unzip -q platform-core-v3.77.0-entity-resolution-identity-graph-foundation-release-bundle.zip -d sc-core-v3.77.0-entity-resolution
cd sc-core-v3.77.0-entity-resolution
chmod +x REPAIR_PLATFORM_CORE_V3770.py APPLY_AND_PUSH_PLATFORM_CORE_V3770.sh DEPLOY_PLATFORM_CORE_V3770_CONTABO.sh PACKAGE_PLATFORM_CORE_V3770.sh
./APPLY_AND_PUSH_PLATFORM_CORE_V3770.sh "$HOME/Downloads/sustainable-catalyst-platform-core"
```

The apply script bootstraps/reuses `backend/.venv`, runs the validator and isolated targeted tests, checks route mounts, commits, pushes `main`, creates tag `v3.77.0`, and pushes the tag.

## Production backend

Copy `DEPLOY_PLATFORM_CORE_V3770_CONTABO.sh` to the VPS and run it as `catalystadmin`. The deploy script performs backup, source/tag validation, Docker build, targeted backend validation with `PYTHONPATH=/app`, backend recreation, local health/contract verification, then public verification.

Expected public contract:

`/public/v1/entity-resolution/contract`

Expected release: `3.77.0`

Expected contract: `sc.core.entity-resolution-identity-graph-foundation.v1`

Database migration: none.
