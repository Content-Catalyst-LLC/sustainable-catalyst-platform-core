#!/usr/bin/env bash
set -euo pipefail
trap 'rc=$?; echo "ERROR: v2.65.0 deployment stopped at line $LINENO (exit $rc): $BASH_COMMAND" >&2; exit $rc' ERR
ROOT="${SC_CORE_ROOT:-/opt/sustainable-catalyst/core}"; COMPOSE="docker compose -f compose.yml -f compose.vps.yml"; cd "$ROOT"
echo "=== PLATFORM CORE v2.65.0 — VISUAL QUERY & EXPLORATION ENGINE ==="
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
[ "$(psqlq "SELECT EXISTS (SELECT 1 FROM schema_migrations WHERE version='0068');")" = t ] || { echo "STOP: migration 0068 missing; deploy v2.64.0 first"; exit 1; }
V264_TABLES=(visual_link_policies visual_selection_sets visual_cross_filters visual_brush_ranges visual_focus_highlights visual_propagation_records visual_linked_view_snapshots)
for t in "${V264_TABLES[@]}"; do [ "$(psqlq "SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema='public' AND table_name='$t');")" = t ] || { echo "STOP: predecessor table missing: $t"; exit 1; }; done
V265_TABLES=(visual_exploration_sessions visual_query_targets visual_query_requests visual_query_predicates visual_traversal_requests visual_query_result_bindings visual_exploration_states visual_query_snapshots)
count=0; for t in "${V265_TABLES[@]}"; do v="$(psqlq "SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema='public' AND table_name='$t');")"; [ "$v" = t ] && count=$((count+1)); done
m69="$(psqlq "SELECT EXISTS (SELECT 1 FROM schema_migrations WHERE version='0069');")"
if [ "$m69" = f ] && [ "$count" -eq 0 ]; then echo "PASS: pristine pre-0069 state"; elif [ "$m69" = f ] && [ "$count" -eq 8 ]; then echo "PASS: recoverable partial-0069 state"; elif [ "$m69" = t ] && [ "$count" -eq 8 ]; then echo "PASS: already-complete 0069 state"; else echo "STOP: inconsistent 0069 state ($m69, $count/8)"; exit 1; fi
echo "=== BACKUP ==="
mkdir -p /opt/sustainable-catalyst/backups/platform-core-v2650
stamp="$(date +%Y%m%d-%H%M%S)"
docker exec -e PGPASSWORD="$DB_PASS" sc-postgres pg_dump -h 127.0.0.1 -U "$DB_USER" -d "$DB_NAME" -Fc > "/opt/sustainable-catalyst/backups/platform-core-v2650/core-${stamp}.dump"
git rev-parse HEAD > "/opt/sustainable-catalyst/backups/platform-core-v2650/git-head-${stamp}.txt"
git fetch origin --tags; git pull --ff-only origin main; git tag --points-at HEAD | grep -qx 'v2.65.0' || { echo "STOP: production HEAD is not tagged v2.65.0"; exit 1; }
python3 -S scripts/validate_v2650_release.py
$COMPOSE build core
$COMPOSE run --rm --no-deps core python scripts/migrate.py | tee /tmp/sc-core-v2650-migrate.json
for t in "${V265_TABLES[@]}"; do [ "$(psqlq "SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema='public' AND table_name='$t');")" = t ] || { echo "STOP: $t missing after migration"; exit 1; }; done
[ "$(psqlq "SELECT EXISTS (SELECT 1 FROM schema_migrations WHERE version='0069');")" = t ] || { echo "STOP: migration 0069 not recorded"; exit 1; }
$COMPOSE up -d --no-deps --force-recreate core
for i in $(seq 1 40); do curl -fsS http://127.0.0.1:8090/health >/tmp/sc-core-v2650-health.json 2>/dev/null && break; sleep 2; done
curl -fsS http://127.0.0.1:8090/v1/visual-runtime/query/readiness | tee /tmp/sc-core-v2650-visual.json | python3 -m json.tool
python3 - <<'PY2'
import json
h=json.load(open('/tmp/sc-core-v2650-health.json')); r=json.load(open('/tmp/sc-core-v2650-visual.json'))
assert h.get('ok') is True and h.get('version')=='2.65.0',h
assert r.get('release')=='2.65.0' and r.get('migration_0069_applied') is True,r
for k in ('visual_exploration_session_registry_by_core','visual_query_target_registry_by_core','visual_query_request_registry_by_core','visual_query_predicate_registry_by_core','visual_traversal_request_registry_by_core','visual_query_result_evidence_binding_by_core','saved_visual_exploration_state_by_core','immutable_visual_query_snapshots_by_core'): assert r.get(k) is True,(k,r)
for k in ('query_execution_by_core','graph_traversal_by_core','data_retrieval_by_core','data_filtering_by_core','aggregation_execution_by_core','result_ranking_by_core','result_recommendation_by_core','automatic_query_execution','visual_inference_by_core'): assert r.get(k) is False,(k,r)
print('PASS - Platform Core v2.65.0 Visual Query & Exploration Engine')
PY2
curl -fsS https://core.sustainablecatalyst.com/health | python3 -m json.tool
echo "PASS - PLATFORM CORE v2.65.0 BACKEND DEPLOYMENT COMPLETE"
