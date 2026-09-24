#!/usr/bin/env bash
set -euo pipefail
trap 'rc=$?; echo "ERROR: v3.21.0 deployment stopped at line $LINENO (exit $rc): $BASH_COMMAND" >&2; exit $rc' ERR
cd /opt/sustainable-catalyst/core
COMPOSE="docker compose"
echo "=== PLATFORM CORE v3.21.0 — UNCERTAINTY & PROBABILISTIC EVIDENCE INTEGRATION ==="
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
TABLES=(uncertainty_evidence_studies_v3210 uncertainty_distribution_evidence_v3210 probabilistic_summary_evidence_v3210 sensitivity_index_evidence_v3210 uncertainty_ensemble_evidence_v3210 uncertainty_evidence_interpretations_v3210 uncertainty_evidence_snapshots_v3210)
echo "=== PREDECESSOR GATE ==="
[ "$(psqlq "SELECT EXISTS (SELECT 1 FROM schema_migrations WHERE version='0107');")" = t ] || { echo "STOP: migration 0107 required"; exit 1; }
echo "=== BACKUP ==="
BACKUP_DIR="/opt/sustainable-catalyst/backups/platform-core-v3210"; mkdir -p "$BACKUP_DIR"; stamp="$(date +%Y%m%d-%H%M%S)"
docker exec -e PGPASSWORD="$DB_PASS" sc-postgres pg_dump -h 127.0.0.1 -U "$DB_USER" -d "$DB_NAME" -Fc > "$BACKUP_DIR/core-${stamp}.dump"
git rev-parse HEAD > "$BACKUP_DIR/git-head-${stamp}.txt"
echo "=== PROMOTE TAGGED SOURCE ==="
git fetch origin --tags; git checkout main; git pull --ff-only origin main; git tag --points-at HEAD | grep -qx v3.21.0 || { echo "STOP: production HEAD is not tagged v3.21.0"; exit 1; }
python3 -S scripts/validate_v3210_release.py
echo "=== BUILD / MIGRATE ==="
$COMPOSE build core
$COMPOSE run --rm --no-deps core python scripts/migrate.py | tee /tmp/sc-core-v3210-migrate.json
for t in "${TABLES[@]}"; do [ "$(psqlq "SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema='public' AND table_name='$t');")" = t ] || { echo "STOP: $t missing"; exit 1; }; done
[ "$(psqlq "SELECT EXISTS (SELECT 1 FROM schema_migrations WHERE version='0108');")" = t ] || { echo "STOP: migration 0108 not recorded"; exit 1; }
$COMPOSE up -d --no-deps --force-recreate core
for i in $(seq 1 40); do curl -fsS http://127.0.0.1:8090/health >/tmp/sc-core-v3210-health.json 2>/dev/null && break; sleep 2; done
curl -fsS http://127.0.0.1:8090/v1/analytics/uncertainty-evidence/readiness | tee /tmp/sc-core-v3210-ready.json | python3 -m json.tool
python3 - <<'PY'
import json
h=json.load(open('/tmp/sc-core-v3210-health.json')); r=json.load(open('/tmp/sc-core-v3210-ready.json'))
assert h.get('ok') is True and h.get('version')=='3.21.0',h
assert r.get('release')=='3.21.0' and r.get('migration_0108_applied') is True,r
assert r.get('contract')=='sc.core.uncertainty-probabilistic-evidence.v1',r
assert r.get('source_contract')=='sc.analytics-r.uncertainty-sensitivity-runtime.v1',r
assert set(r.get('methods',[]))=={'monte_carlo','latin_hypercube','morris','sobol'},r
for k in ('execute_uncertainty_by_core','infer_causality_by_core','rank_parameters_by_core','select_policy_by_core','certify_scientific_validity_by_core','determine_truth_by_core'): assert r.get(k) is False,(k,r)
print('PASS - Platform Core v3.21.0 Uncertainty & Probabilistic Evidence Integration')
PY
curl -fsS https://core.sustainablecatalyst.com/health | python3 -m json.tool || true
echo "PASS - PLATFORM CORE v3.21.0 BACKEND DEPLOYMENT COMPLETE"
