#!/usr/bin/env bash
set -euo pipefail
trap 'rc=$?; echo "ERROR: v2.63.0 deployment stopped at line $LINENO (exit $rc): $BASH_COMMAND" >&2; exit $rc' ERR
ROOT="${SC_CORE_ROOT:-/opt/sustainable-catalyst/core}"; COMPOSE="docker compose -f compose.yml -f compose.vps.yml"; cd "$ROOT"
echo "=== PLATFORM CORE v2.63.0 — ANALYTICAL VISUALIZATION GRAMMAR ==="
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
[ "$(psqlq "SELECT EXISTS (SELECT 1 FROM schema_migrations WHERE version='0066');")" = t ] || { echo "STOP: migration 0066 missing; deploy v2.62.0 first"; exit 1; }
V262_TABLES=(visual_renderer_profiles visual_view_compositions visual_view_assignments visual_view_link_groups visual_interaction_states visual_renderer_resolutions visual_composition_snapshots)
for t in "${V262_TABLES[@]}"; do [ "$(psqlq "SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema='public' AND table_name='$t');")" = t ] || { echo "STOP: predecessor table missing: $t"; exit 1; }; done
V263_TABLES=(visual_grammar_specifications visual_grammar_data_bindings visual_grammar_marks visual_grammar_scales visual_grammar_encodings visual_grammar_transforms visual_grammar_guides visual_grammar_snapshots)
count=0; for t in "${V263_TABLES[@]}"; do v="$(psqlq "SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema='public' AND table_name='$t');")"; [ "$v" = t ] && count=$((count+1)); done
m67="$(psqlq "SELECT EXISTS (SELECT 1 FROM schema_migrations WHERE version='0067');")"
if [ "$m67" = f ] && [ "$count" -eq 0 ]; then echo "PASS: pristine pre-0067 state"; elif [ "$m67" = f ] && [ "$count" -eq 8 ]; then echo "PASS: recoverable partial-0067 state"; elif [ "$m67" = t ] && [ "$count" -eq 8 ]; then echo "PASS: already-complete 0067 state"; else echo "STOP: inconsistent 0067 state ($m67, $count/8)"; exit 1; fi
git fetch origin --tags; git pull --ff-only origin main; git tag --points-at HEAD | grep -qx 'v2.63.0' || { echo "STOP: production HEAD is not tagged v2.63.0"; exit 1; }
python3 -S scripts/validate_v2630_release.py
$COMPOSE build core
$COMPOSE run --rm --no-deps core python scripts/migrate.py | tee /tmp/sc-core-v2630-migrate.json
for t in "${V263_TABLES[@]}"; do [ "$(psqlq "SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema='public' AND table_name='$t');")" = t ] || { echo "STOP: $t missing after migration"; exit 1; }; done
[ "$(psqlq "SELECT EXISTS (SELECT 1 FROM schema_migrations WHERE version='0067');")" = t ] || { echo "STOP: migration 0067 not recorded"; exit 1; }
$COMPOSE up -d --no-deps --force-recreate core
for i in $(seq 1 40); do curl -fsS http://127.0.0.1:8090/health >/tmp/sc-core-v2630-health.json 2>/dev/null && break; sleep 2; done
curl -fsS http://127.0.0.1:8090/v1/visual-runtime/grammar/readiness | tee /tmp/sc-core-v2630-visual.json | python3 -m json.tool
python3 - <<'PY2'
import json
h=json.load(open('/tmp/sc-core-v2630-health.json')); r=json.load(open('/tmp/sc-core-v2630-visual.json'))
assert h.get('ok') is True and h.get('version')=='2.63.0',h
assert r.get('release')=='2.63.0' and r.get('migration_0067_applied') is True,r
for k in ('grammar_specification_registry_by_core','data_binding_registry_by_core','mark_registry_by_core','encoding_registry_by_core','scale_registry_by_core','transform_spec_registry_by_core','guide_registry_by_core','immutable_grammar_snapshots_by_core'): assert r.get(k) is True,(k,r)
for k in ('transform_execution_by_core','aggregation_execution_by_core','binning_execution_by_core','scale_calculation_by_core','layout_computation_by_core','mark_drawing_by_core','gpu_execution_by_core','visual_inference_by_core','automatic_chart_generation_by_core'): assert r.get(k) is False,(k,r)
print('PASS - Platform Core v2.63.0 Analytical Visualization Grammar')
PY2
echo "PASS - PLATFORM CORE v2.63.0 BACKEND DEPLOYMENT COMPLETE"
