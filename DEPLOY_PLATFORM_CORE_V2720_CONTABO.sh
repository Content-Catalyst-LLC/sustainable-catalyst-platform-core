#!/usr/bin/env bash
set -euo pipefail
trap 'rc=$?; echo "ERROR: v2.72.0 deployment stopped at line $LINENO (exit $rc): $BASH_COMMAND" >&2; exit $rc' ERR
ROOT="${SC_CORE_ROOT:-/opt/sustainable-catalyst/core}"; COMPOSE="docker compose -f compose.yml -f compose.vps.yml"; cd "$ROOT"
echo "=== PLATFORM CORE v2.72.0 — UNIFIED RESEARCH PROJECT OBJECT MODEL ==="
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
[ "$(psqlq "SELECT EXISTS (SELECT 1 FROM schema_migrations WHERE version='0075');")" = t ] || { echo "STOP: migration 0075 missing; deploy v2.71.0 first"; exit 1; }
V271_TABLES=(cross_product_visual_runtime_integrations cross_product_visual_object_bindings cross_product_visual_context_bindings cross_product_visual_capability_bindings cross_product_visual_view_bindings cross_product_visual_handoff_routes cross_product_visual_sync_records cross_product_visual_integration_snapshots)
for t in "${V271_TABLES[@]}"; do [ "$(psqlq "SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema='public' AND table_name='$t');")" = t ] || { echo "STOP: predecessor table missing: $t"; exit 1; }; done
V272_TABLES=(unified_research_project_profiles unified_research_questions unified_research_objectives unified_research_components unified_research_relationships unified_research_provenance_records unified_research_runtime_handoffs unified_research_project_snapshots)
count=0; for t in "${V272_TABLES[@]}"; do [ "$(psqlq "SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema='public' AND table_name='$t');")" = t ] && count=$((count+1)); done
m76="$(psqlq "SELECT EXISTS (SELECT 1 FROM schema_migrations WHERE version='0076');")"
if [ "$m76" = f ] && [ "$count" -eq 0 ]; then echo "PASS: pristine pre-0076 state"; elif [ "$m76" = f ] && [ "$count" -eq 8 ]; then echo "PASS: recoverable partial-0076 state"; elif [ "$m76" = t ] && [ "$count" -eq 8 ]; then echo "PASS: already-complete 0076 state"; else echo "STOP: inconsistent 0076 state ($m76, $count/8)"; exit 1; fi
echo "=== BACKUP ==="; BACKUP_DIR="/opt/sustainable-catalyst/backups/platform-core-v2720"; mkdir -p "$BACKUP_DIR"; stamp="$(date +%Y%m%d-%H%M%S)"; docker exec -e PGPASSWORD="$DB_PASS" sc-postgres pg_dump -h 127.0.0.1 -U "$DB_USER" -d "$DB_NAME" -Fc > "$BACKUP_DIR/core-${stamp}.dump"; git rev-parse HEAD > "$BACKUP_DIR/git-head-${stamp}.txt"; tar --exclude='.git' --exclude='backend/.venv' -czf "$BACKUP_DIR/core-source-${stamp}.tar.gz" .
git fetch origin --tags; git pull --ff-only origin main; git tag --points-at HEAD | grep -qx 'v2.72.0' || { echo "STOP: production HEAD is not tagged v2.72.0"; exit 1; }
python3 -S scripts/validate_v2720_release.py
$COMPOSE build core
$COMPOSE run --rm --no-deps core python scripts/migrate.py | tee /tmp/sc-core-v2720-migrate.json
for t in "${V272_TABLES[@]}"; do [ "$(psqlq "SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema='public' AND table_name='$t');")" = t ] || { echo "STOP: $t missing after migration"; exit 1; }; done
[ "$(psqlq "SELECT EXISTS (SELECT 1 FROM schema_migrations WHERE version='0076');")" = t ] || { echo "STOP: migration 0076 not recorded"; exit 1; }
$COMPOSE up -d --no-deps --force-recreate core
for i in $(seq 1 40); do curl -fsS http://127.0.0.1:8090/health >/tmp/sc-core-v2720-health.json 2>/dev/null && break; sleep 2; done
curl -fsS http://127.0.0.1:8090/v1/research/projects/readiness | tee /tmp/sc-core-v2720-research.json | python3 -m json.tool
python3 - <<'PY2'
import json
h=json.load(open('/tmp/sc-core-v2720-health.json'));r=json.load(open('/tmp/sc-core-v2720-research.json'));assert h.get('ok') is True and h.get('version')=='2.72.0',h;assert r.get('release')=='2.72.0' and r.get('migration_0076_applied') is True,r
for k in ('research_project_registry_by_core','question_registry_by_core','objective_registry_by_core','typed_component_registry_by_core','research_relationship_registry_by_core','research_provenance_registry_by_core','runtime_handoff_registry_by_core','immutable_project_snapshots_by_core'):assert r.get(k) is True,(k,r)
for k in ('execute_analysis_by_core','generate_findings_by_core','promote_conclusion_by_core','infer_originality_by_core','automatic_truth_promotion','execute_handoff_by_core'):assert r.get(k) is False,(k,r)
print('PASS - Platform Core v2.72.0 Unified Research Project Object Model')
PY2
curl -fsS https://core.sustainablecatalyst.com/health | python3 -m json.tool
echo "PASS - PLATFORM CORE v2.72.0 BACKEND DEPLOYMENT COMPLETE"
