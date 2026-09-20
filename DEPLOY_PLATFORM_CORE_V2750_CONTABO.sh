#!/usr/bin/env bash
set -euo pipefail
trap 'rc=$?; echo "ERROR: v2.75.0 deployment stopped at line $LINENO (exit $rc): $BASH_COMMAND" >&2; exit $rc' ERR
ROOT="${SC_CORE_ROOT:-/opt/sustainable-catalyst/core}"; COMPOSE="docker compose -f compose.yml -f compose.vps.yml"; cd "$ROOT"
echo "=== PLATFORM CORE v2.75.0 — REPRODUCIBLE RESEARCH PACKAGE RUNTIME ==="
[ -f .env.production ] || { echo "STOP: .env.production missing"; exit 1; }
if ! git diff --quiet || ! git diff --cached --quiet; then echo "STOP: production tree has local changes"; exit 1; fi
CORE_DB_URL="$(grep -m1 '^SC_CORE_DATABASE_URL=' .env.production | cut -d= -f2-)"
eval "$(CORE_DB_URL="$CORE_DB_URL" python3 - <<'PY2'
import os,shlex
from urllib.parse import urlparse,unquote
u=urlparse(os.environ['CORE_DB_URL'].strip().strip('"').strip("'"));print('DB_USER='+shlex.quote(unquote(u.username or '')));print('DB_PASS='+shlex.quote(unquote(u.password or '')));print('DB_NAME='+shlex.quote((u.path or '').lstrip('/')))
PY2
)"
psqlq(){ docker exec -e PGPASSWORD="$DB_PASS" sc-postgres psql -h 127.0.0.1 -U "$DB_USER" -d "$DB_NAME" -Atqc "$1"; }
echo "=== PREDECESSOR GATE ==="
[ "$(psqlq "SELECT EXISTS (SELECT 1 FROM schema_migrations WHERE version='0078');")" = t ] || { echo "STOP: migration 0078 missing; deploy v2.74.0 first"; exit 1; }
V274_TABLES=(research_methodologies research_methodology_versions research_method_variables research_method_assumptions research_method_parameters research_execution_environments research_analysis_runs research_analysis_run_inputs research_analysis_run_outputs research_methodology_snapshots)
for t in "${V274_TABLES[@]}"; do [ "$(psqlq "SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema='public' AND table_name='$t');")" = t ] || { echo "STOP: predecessor table missing: $t"; exit 1; }; done
V275_TABLES=(reproducible_research_packages reproducible_research_package_components reproducible_research_package_artifacts reproducible_research_package_environments reproducible_research_replay_plans reproducible_research_verifications reproducible_research_reviews reproducible_research_snapshots)
count=0; for t in "${V275_TABLES[@]}"; do [ "$(psqlq "SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema='public' AND table_name='$t');")" = t ] && count=$((count+1)); done
m79="$(psqlq "SELECT EXISTS (SELECT 1 FROM schema_migrations WHERE version='0079');")"
if [ "$m79" = f ] && [ "$count" -eq 0 ]; then echo "PASS: pristine pre-0079 state"; elif [ "$m79" = f ] && [ "$count" -eq 8 ]; then echo "PASS: recoverable partial-0079 state"; elif [ "$m79" = t ] && [ "$count" -eq 8 ]; then echo "PASS: already-complete 0079 state"; else echo "STOP: inconsistent 0079 state ($m79, $count/8)"; exit 1; fi
echo "=== BACKUP ==="; BACKUP_DIR="/opt/sustainable-catalyst/backups/platform-core-v2750"; mkdir -p "$BACKUP_DIR"; stamp="$(date +%Y%m%d-%H%M%S)"; docker exec -e PGPASSWORD="$DB_PASS" sc-postgres pg_dump -h 127.0.0.1 -U "$DB_USER" -d "$DB_NAME" -Fc > "$BACKUP_DIR/core-${stamp}.dump"; git rev-parse HEAD > "$BACKUP_DIR/git-head-${stamp}.txt"; tar --exclude='.git' --exclude='backend/.venv' -czf "$BACKUP_DIR/core-source-${stamp}.tar.gz" .
git fetch origin --tags; git pull --ff-only origin main; git tag --points-at HEAD | grep -qx 'v2.75.0' || { echo "STOP: production HEAD is not tagged v2.75.0"; exit 1; }
python3 -S scripts/validate_v2750_release.py
$COMPOSE build core
$COMPOSE run --rm --no-deps core python scripts/migrate.py | tee /tmp/sc-core-v2750-migrate.json
for t in "${V275_TABLES[@]}"; do [ "$(psqlq "SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema='public' AND table_name='$t');")" = t ] || { echo "STOP: $t missing after migration"; exit 1; }; done
[ "$(psqlq "SELECT EXISTS (SELECT 1 FROM schema_migrations WHERE version='0079');")" = t ] || { echo "STOP: migration 0079 not recorded"; exit 1; }
$COMPOSE up -d --no-deps --force-recreate core
for i in $(seq 1 40); do curl -fsS http://127.0.0.1:8090/health >/tmp/sc-core-v2750-health.json 2>/dev/null && break; sleep 2; done
curl -fsS http://127.0.0.1:8090/v1/research/reproducibility/readiness | tee /tmp/sc-core-v2750-repro.json | python3 -m json.tool
python3 - <<'PY2'
import json
h=json.load(open('/tmp/sc-core-v2750-health.json'));r=json.load(open('/tmp/sc-core-v2750-repro.json'))
assert h.get('ok') is True and h.get('version')=='2.75.0',h
assert r.get('release')=='2.75.0' and r.get('migration_0079_applied') is True,r
for k in ('package_registry_by_core','component_manifest_by_core','artifact_registry_by_core','environment_capture_by_core','replay_plan_registry_by_core','verification_evidence_registry_by_core','review_registry_by_core','immutable_package_snapshots_by_core'): assert r.get(k) is True,(k,r)
for k in ('execute_replay_by_core','reproduce_analysis_by_core','validate_finding_by_core','certify_scientific_truth_by_core','alter_artifacts_by_core','execute_handoff_by_core','infer_reproducibility_by_core'): assert r.get(k) is False,(k,r)
print('PASS - Platform Core v2.75.0 Reproducible Research Package Runtime')
PY2
curl -fsS https://core.sustainablecatalyst.com/health | python3 -m json.tool
echo "PASS - PLATFORM CORE v2.75.0 BACKEND DEPLOYMENT COMPLETE"
