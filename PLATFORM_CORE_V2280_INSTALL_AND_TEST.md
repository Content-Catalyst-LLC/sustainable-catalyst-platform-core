# Platform Core v2.28.0 Install & Test

## Mac validation and GitHub promotion

```bash
cd ~/Downloads
chmod +x deploy_and_validate_platform_core_v2_28_0_macos.sh

SC_CORE_BUNDLE_ONLY=1 \
./deploy_and_validate_platform_core_v2_28_0_macos.sh \
  "$HOME/Downloads/sustainable-catalyst-platform-core-v2.28.0-release-bundle.zip"

./deploy_and_validate_platform_core_v2_28_0_macos.sh \
  "$HOME/Downloads/sustainable-catalyst-platform-core-v2.28.0-release-bundle.zip"
```

## VPS upgrade outline

The existing `/opt/sustainable-catalyst/core` service is upgraded in place. No new VPS service is required.

```bash
cd /opt/sustainable-catalyst/core
git fetch origin --tags
git pull --ff-only origin main
git tag --points-at HEAD

docker compose -f compose.yml -f compose.vps.yml build core
docker compose -f compose.yml -f compose.vps.yml run --rm --no-deps core python scripts/migrate.py
docker compose -f compose.yml -f compose.vps.yml up -d --no-deps --force-recreate core

curl -fsS http://127.0.0.1:8090/health | python3 -m json.tool
curl -fsS http://127.0.0.1:8090/v1/research-objects/readiness | python3 -m json.tool
```

Expected release: `2.28.0`. Expected migration head: `0031`.
