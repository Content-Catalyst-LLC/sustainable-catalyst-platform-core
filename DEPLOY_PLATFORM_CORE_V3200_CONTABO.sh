#!/usr/bin/env bash
set -euo pipefail
trap 'rc=$?; echo "ERROR: v3.2.0 deployment stopped at line $LINENO (exit $rc): $BASH_COMMAND" >&2; exit $rc' ERR
cd /opt/sustainable-catalyst/core
COMPOSE="docker compose"
echo "=== PLATFORM CORE v3.2.0 — ANALYTICAL RESULT & PROVENANCE INTEGRATION ==="
CORE_DB_URL="${SC_CORE_DATABASE_URL:-}"
if [ -z "$CORE_DB_URL" ] && docker ps --format '{{.Names}}' | grep -qx sc-core; then CORE_DB_URL="$(docker exec sc-core sh -lc 'printf %s "$SC_CORE_DATABASE_URL"' 2>/dev/null || true)"; fi
if [ -z "$CORE_DB_URL" ] && [ -f .env.production ]; then CORE_DB_URL="$(grep -m1 '^SC_CORE_DATABASE_URL=' .env.production | cut -d= -f2- | sed 's/^"//;s/"$//')"; fi
[ -n "$CORE_DB_URL" ] || { echo "STOP: SC_CORE_DATABASE_URL could not be resolved"; exit 1; }
eval "$(CORE_DB_URL="$CORE_DB_URL" python3 - <<'PYDB'
import os,shlex
from urllib.parse import urlparse,unquote
u=urlparse(os.environ['CORE_DB_URL'].replace('postgresql+psycopg://','postgresql://',1)); print('export DB_USER='+shlex.quote(unquote(u.username or ''))); print('export DB_PASS='+shlex.quote(unquote(u.password or ''))); print('export DB_NAME='+shlex.quote((u.path or '').lstrip('/')))
PYDB
)"
psqlq(){ docker exec -e PGPASSWORD="$DB_PASS" sc-postgres psql -h 127.0.0.1 -U "$DB_USER" -d "$DB_NAME" -Atqc "$1"; }
V320_TABLES=('analytical_result_objects_v320' 'analytical_estimates_v320' 'analytical_uncertainty_objects_v320' 'analytical_lineage_bindings_v320' 'analytical_result_ingestion_receipts_v320' 'analytical_result_snapshots_v320')
echo "=== PREDECESSOR GATE ==="; [ "$(psqlq "SELECT EXISTS (SELECT 1 FROM schema_migrations WHERE version='0103');")" = t ] || { echo "STOP: migration 0103 is required before v3.2.0"; exit 1; }
echo "=== BACKUP ==="; BACKUP_DIR="/opt/sustainable-catalyst/backups/platform-core-v3200"; mkdir -p "$BACKUP_DIR"; stamp="$(date +%Y%m%d-%H%M%S)"; docker exec -e PGPASSWORD="$DB_PASS" sc-postgres pg_dump -h 127.0.0.1 -U "$DB_USER" -d "$DB_NAME" -Fc > "$BACKUP_DIR/core-${stamp}.dump"; git rev-parse HEAD > "$BACKUP_DIR/git-head-${stamp}.txt"
echo "=== PROMOTE TAGGED SOURCE ==="; git fetch origin --tags; git checkout main; git pull --ff-only origin main; git tag --points-at HEAD | grep -qx 'v3.2.0' || { echo "STOP: production HEAD is not tagged v3.2.0"; exit 1; }; python3 -S scripts/validate_v3200_release.py
echo "=== BUILD / MIGRATE ==="; $COMPOSE build core; $COMPOSE run --rm --no-deps core python scripts/migrate.py | tee /tmp/sc-core-v3200-migrate.json
for t in "${V320_TABLES[@]}"; do [ "$(psqlq "SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema='public' AND table_name='$t');")" = t ] || { echo "STOP: $t missing after migration"; exit 1; }; done
[ "$(psqlq "SELECT EXISTS (SELECT 1 FROM schema_migrations WHERE version='0104');")" = t ] || { echo "STOP: migration 0104 not recorded"; exit 1; }
[ "$(psqlq "SELECT EXISTS (SELECT 1 FROM analytical_runtime_providers_v310 WHERE provider_key='catalystanalyticsr' AND provider_version='2.1.0' AND runtime='r' AND execution_host='workspace');")" = t ] || { echo "STOP: Catalyst Analytics R 2.1.0 provider promotion missing"; exit 1; }
$COMPOSE up -d --no-deps --force-recreate core; for i in $(seq 1 40); do curl -fsS http://127.0.0.1:8090/health >/tmp/sc-core-v3200-health.json 2>/dev/null && break; sleep 2; done
curl -fsS http://127.0.0.1:8090/v1/analytics/results/readiness | tee /tmp/sc-core-v3200-readiness.json | python3 -m json.tool
curl -fsS http://127.0.0.1:8090/v1/analytics/runtime-providers/providers/catalystanalyticsr | tee /tmp/sc-core-v3200-provider.json | python3 -m json.tool
python3 - <<'PY2'
import json
h=json.load(open('/tmp/sc-core-v3200-health.json')); r=json.load(open('/tmp/sc-core-v3200-readiness.json')); p=json.load(open('/tmp/sc-core-v3200-provider.json'))
assert h.get('ok') is True and h.get('version')=='3.2.0',h
assert r.get('release')=='3.2.0' and r.get('migration_0104_applied') is True,r
assert r.get('catalyst_analytics_r_version')=='2.1.0' and r.get('workspace_adapter_release')=='3.5.0',r
assert r.get('core_records_results_but_does_not_execute') is True and r.get('execute_r_by_core') is False,r
assert p['provider']['runtime']=='r' and p['provider']['execution_host']=='workspace' and p['provider']['provider_version']=='2.1.0',p
print('PASS - Platform Core v3.2.0 Analytical Result & Provenance Integration')
PY2
curl -fsS https://core.sustainablecatalyst.com/health | python3 -m json.tool
echo "PASS - PLATFORM CORE v3.2.0 BACKEND DEPLOYMENT COMPLETE"
