# Platform Core v2.29.0 — Install & Test

## macOS verification

```bash
cd ~/Downloads
chmod +x deploy_and_validate_platform_core_v2_29_0_macos.sh
SC_CORE_BUNDLE_ONLY=1 ./deploy_and_validate_platform_core_v2_29_0_macos.sh \
  "$HOME/Downloads/sustainable-catalyst-platform-core-v2.29.0-release-bundle.zip"
```

## Full validation + GitHub promotion

```bash
cd ~/Downloads
./deploy_and_validate_platform_core_v2_29_0_macos.sh \
  "$HOME/Downloads/sustainable-catalyst-platform-core-v2.29.0-release-bundle.zip"
```

## VPS deployment

After GitHub promotion and a production backup:

```bash
cd /opt/sustainable-catalyst/core
git fetch origin --tags
git pull --ff-only origin main
COMPOSE="docker compose -f compose.yml -f compose.vps.yml"
$COMPOSE build core
$COMPOSE run --rm --no-deps core python scripts/migrate.py
$COMPOSE up -d --no-deps --force-recreate core
curl -fsS http://127.0.0.1:8090/health | python3 -m json.tool
curl -fsS http://127.0.0.1:8090/v1/visual-reasoning/readiness | python3 -m json.tool
```

Expected production release: `2.29.0`. Expected migration head: `0032` with no pending migrations.
