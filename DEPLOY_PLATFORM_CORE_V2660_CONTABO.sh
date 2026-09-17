#!/usr/bin/env bash
set -euo pipefail
trap 'rc=$?; echo "ERROR: v2.66.0 deployment stopped at line $LINENO (exit $rc): $BASH_COMMAND" >&2; exit $rc' ERR
ROOT="${SC_CORE_ROOT:-/opt/sustainable-catalyst/core}"; COMPOSE="docker compose -f compose.yml -f compose.vps.yml"; cd "$ROOT"
echo "=== PLATFORM CORE v2.66.0 — VISUAL MODEL CONSTRUCTION ==="
[ -f .env.production ] || { echo "STOP: .env.production missing"; exit 1; }
if ! git diff --quiet || ! git diff --cached --quiet; then echo "STOP: production tree has local changes"; exit 1; fi
CORE_DB_URL="$(grep -m1 '^SC_CORE_DATABASE_URL=' .env.production | cut -d= -f2-)"
eval "$(CORE_DB_URL="$CORE_DB_URL" python3 - <<'PY2'
import os,shlex
from urllib.parse import urlparse,unquote
u=urlparse(os.environ['CORE_DB_URL'].strip().strip('"').strip("'")); print('DB_USER='+shlex.quote(unquote(u.username or ''))); print('DB_PASS='+shlex.quote(unquote(u.password or ''))); print('DB_NAME='+shlex.quote((u.path or '').lstrip('/')))
PY2
)"
psqlq(){ docker exec -e PGPASSWORD="$DB_PASS" sc-postgres psql -h 127.0.0.1 -U "$DB_USER" -d "$DB_NAME" -Atqc "$1"; }
echo "=== PREDECESSOR GATE ==="
[ "$(psqlq "SELECT EXISTS (SELECT 1 FROM schema_migrations WHERE version='0069');")" = t ] || { echo "STOP: migration 0069 missing; deploy v2.65.0 first"; exit 1; }
V265_TABLES=(visual_exploration_sessions visual_query_targets visual_query_requests visual_query_predicates visual_traversal_requests visual_query_result_bindings visual_exploration_states visual_query_snapshots)
for t in "${V265_TABLES[@]}"; do [ "$(psqlq "SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema='public' AND table_name='$t');")" = t ] || { echo "STOP: predecessor table missing: $t"; exit 1; }; done
V266_TABLES=(visual_model_constructions visual_model_components visual_model_relationships visual_model_assumptions visual_model_constraints visual_model_interventions visual_model_handoffs visual_model_snapshots)
count=0; for t in "${V266_TABLES[@]}"; do v="$(psqlq "SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema='public' AND table_name='$t');")"; [ "$v" = t ] && count=$((count+1)); done
m70="$(psqlq "SELECT EXISTS (SELECT 1 FROM schema_migrations WHERE version='0070');")"
if [ "$m70" = f ] && [ "$count" -eq 0 ]; then echo "PASS: pristine pre-0070 state"; elif [ "$m70" = f ] && [ "$count" -eq 8 ]; then echo "PASS: recoverable partial-0070 state"; elif [ "$m70" = t ] && [ "$count" -eq 8 ]; then echo "PASS: already-complete 0070 state"; else echo "STOP: inconsistent 0070 state ($m70, $count/8)"; exit 1; fi
echo "=== BACKUP ==="
mkdir -p /opt/sustainable-catalyst/backups/platform-core-v2660
stamp="$(date +%Y%m%d-%H%M%S)"
docker exec -e PGPASSWORD="$DB_PASS" sc-postgres pg_dump -h 127.0.0.1 -U "$DB_USER" -d "$DB_NAME" -Fc > "/opt/sustainable-catalyst/backups/platform-core-v2660/core-${stamp}.dump"
git rev-parse HEAD > "/opt/sustainable-catalyst/backups/platform-core-v2660/git-head-${stamp}.txt"
git fetch origin --tags; git pull --ff-only origin main; git tag --points-at HEAD | grep -qx 'v2.66.0' || { echo "STOP: production HEAD is not tagged v2.66.0"; exit 1; }
python3 -S scripts/validate_v2660_release.py
$COMPOSE build core
$COMPOSE run --rm --no-deps core python scripts/migrate.py | tee /tmp/sc-core-v2660-migrate.json
for t in "${V266_TABLES[@]}"; do [ "$(psqlq "SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema='public' AND table_name='$t');")" = t ] || { echo "STOP: $t missing after migration"; exit 1; }; done
[ "$(psqlq "SELECT EXISTS (SELECT 1 FROM schema_migrations WHERE version='0070');")" = t ] || { echo "STOP: migration 0070 not recorded"; exit 1; }
$COMPOSE up -d --no-deps --force-recreate core
for i in $(seq 1 40); do curl -fsS http://127.0.0.1:8090/health >/tmp/sc-core-v2660-health.json 2>/dev/null && break; sleep 2; done
curl -fsS http://127.0.0.1:8090/v1/visual-runtime/model-construction/readiness | tee /tmp/sc-core-v2660-visual.json | python3 -m json.tool
python3 - <<'PY2'
import json
h=json.load(open('/tmp/sc-core-v2660-health.json')); r=json.load(open('/tmp/sc-core-v2660-visual.json'))
assert h.get('ok') is True and h.get('version')=='2.66.0',h
assert r.get('release')=='2.66.0' and r.get('migration_0070_applied') is True,r
for k in ('visual_model_construction_registry_by_core','visual_model_component_registry_by_core','visual_model_relationship_registry_by_core','visual_model_assumption_registry_by_core','visual_model_constraint_registry_by_core','visual_model_intervention_registry_by_core','visual_model_handoff_registry_by_core','immutable_visual_model_snapshots_by_core'): assert r.get(k) is True,(k,r)
for k in ('equation_execution_by_core','constraint_optimization_by_core','simulation_execution_by_core','model_execution_by_core','automatic_parameter_estimation','automatic_model_inference'): assert r.get(k) is False,(k,r)
print('PASS - Platform Core v2.66.0 Visual Model Construction')
PY2
curl -fsS https://core.sustainablecatalyst.com/health | python3 -m json.tool
echo "PASS - PLATFORM CORE v2.66.0 BACKEND DEPLOYMENT COMPLETE"
