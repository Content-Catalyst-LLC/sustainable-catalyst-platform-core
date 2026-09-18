#!/usr/bin/env bash
set -euo pipefail
trap 'rc=$?; echo "ERROR: v2.71.0 deployment stopped at line $LINENO (exit $rc): $BASH_COMMAND" >&2; exit $rc' ERR
ROOT="${SC_CORE_ROOT:-/opt/sustainable-catalyst/core}"; COMPOSE="docker compose -f compose.yml -f compose.vps.yml"; cd "$ROOT"
echo "=== PLATFORM CORE v2.71.0 — CROSS-PRODUCT VISUAL RUNTIME INTEGRATION ==="
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
[ "$(psqlq "SELECT EXISTS (SELECT 1 FROM schema_migrations WHERE version='0074');")" = t ] || { echo "STOP: migration 0074 missing; deploy v2.70.0 first"; exit 1; }
V270_TABLES=(unified_visual_reasoning_workspaces unified_visual_layer_bindings unified_visual_reasoning_paths unified_visual_state_bridges unified_visual_evidence_chains unified_visual_runtime_handoffs unified_visual_package_bindings unified_visual_replay_states unified_visual_reasoning_snapshots)
for t in "${V270_TABLES[@]}"; do [ "$(psqlq "SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema='public' AND table_name='$t');")" = t ] || { echo "STOP: predecessor table missing: $t"; exit 1; }; done
V271_TABLES=(cross_product_visual_runtime_integrations cross_product_visual_object_bindings cross_product_visual_context_bindings cross_product_visual_capability_bindings cross_product_visual_view_bindings cross_product_visual_handoff_routes cross_product_visual_sync_records cross_product_visual_integration_snapshots)
count=0; for t in "${V271_TABLES[@]}"; do [ "$(psqlq "SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema='public' AND table_name='$t');")" = t ] && count=$((count+1)); done
m75="$(psqlq "SELECT EXISTS (SELECT 1 FROM schema_migrations WHERE version='0075');")"
if [ "$m75" = f ] && [ "$count" -eq 0 ]; then echo "PASS: pristine pre-0075 state"; elif [ "$m75" = f ] && [ "$count" -eq 8 ]; then echo "PASS: recoverable partial-0075 state"; elif [ "$m75" = t ] && [ "$count" -eq 8 ]; then echo "PASS: already-complete 0075 state"; else echo "STOP: inconsistent 0075 state ($m75, $count/8)"; exit 1; fi
echo "=== BACKUP ==="; BACKUP_DIR="/opt/sustainable-catalyst/backups/platform-core-v2710"; mkdir -p "$BACKUP_DIR"; stamp="$(date +%Y%m%d-%H%M%S)"; docker exec -e PGPASSWORD="$DB_PASS" sc-postgres pg_dump -h 127.0.0.1 -U "$DB_USER" -d "$DB_NAME" -Fc > "$BACKUP_DIR/core-${stamp}.dump"; git rev-parse HEAD > "$BACKUP_DIR/git-head-${stamp}.txt"; tar --exclude='.git' --exclude='backend/.venv' -czf "$BACKUP_DIR/core-source-${stamp}.tar.gz" .
git fetch origin --tags; git pull --ff-only origin main; git tag --points-at HEAD | grep -qx 'v2.71.0' || { echo "STOP: production HEAD is not tagged v2.71.0"; exit 1; }
python3 -S scripts/validate_v2710_release.py
$COMPOSE build core
$COMPOSE run --rm --no-deps core python scripts/migrate.py | tee /tmp/sc-core-v2710-migrate.json
for t in "${V271_TABLES[@]}"; do [ "$(psqlq "SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema='public' AND table_name='$t');")" = t ] || { echo "STOP: $t missing after migration"; exit 1; }; done
[ "$(psqlq "SELECT EXISTS (SELECT 1 FROM schema_migrations WHERE version='0075');")" = t ] || { echo "STOP: migration 0075 not recorded"; exit 1; }
$COMPOSE up -d --no-deps --force-recreate core
for i in $(seq 1 40); do curl -fsS http://127.0.0.1:8090/health >/tmp/sc-core-v2710-health.json 2>/dev/null && break; sleep 2; done
curl -fsS http://127.0.0.1:8090/v1/visual-runtime/integrations/readiness | tee /tmp/sc-core-v2710-visual.json | python3 -m json.tool
python3 - <<'PY2'
import json
h=json.load(open('/tmp/sc-core-v2710-health.json'));r=json.load(open('/tmp/sc-core-v2710-visual.json'));assert h.get('ok') is True and h.get('version')=='2.71.0',h;assert r.get('release')=='2.71.0' and r.get('migration_0075_applied') is True,r
for k in ('product_integration_registry_by_core','shared_object_binding_registry_by_core','research_context_binding_registry_by_core','visual_capability_contract_registry_by_core','cross_product_view_binding_registry_by_core','handoff_route_registry_by_core','synchronization_evidence_registry_by_core','immutable_cross_product_visual_snapshots_by_core'):assert r.get(k) is True,(k,r)
for k in ('render_by_core','compute_by_core','mutate_specialist_state_by_core','execute_handoff_by_core','automatic_cross_product_sync','automatic_visual_inference','automatic_truth_promotion'):assert r.get(k) is False,(k,r)
assert len(r.get('products',[]))==7,r
print('PASS - Platform Core v2.71.0 Cross-Product Visual Runtime Integration')
PY2
curl -fsS https://core.sustainablecatalyst.com/health | python3 -m json.tool
echo "PASS - PLATFORM CORE v2.71.0 BACKEND DEPLOYMENT COMPLETE"
