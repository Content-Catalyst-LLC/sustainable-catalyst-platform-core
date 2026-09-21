#!/usr/bin/env bash
set -euo pipefail
trap 'rc=$?; echo "ERROR: v3.0.0 deployment stopped at line $LINENO (exit $rc): $BASH_COMMAND" >&2; exit $rc' ERR
cd /opt/sustainable-catalyst/core
COMPOSE="docker compose"
echo "=== PLATFORM CORE v3.0.0 — UNIFIED RESEARCH, SCIENTIFIC COMPUTING & INVESTIGATION RUNTIME ==="
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
[ -n "$DB_USER" ] && [ -n "$DB_NAME" ] || { echo "STOP: database identity could not be parsed"; exit 1; }
psqlq(){ docker exec -e PGPASSWORD="$DB_PASS" sc-postgres psql -h 127.0.0.1 -U "$DB_USER" -d "$DB_NAME" -Atqc "$1"; }
V297_TABLES=('research_integration_certification_suites_v297' 'research_integration_certification_products_v297' 'research_integration_certification_cases_v297' 'research_integration_certification_runs_v297' 'research_integration_certification_case_results_v297' 'research_integration_certification_exchange_checks_v297' 'research_integration_certification_trace_checks_v297' 'research_integration_certification_reproduction_checks_v297' 'research_integration_certification_evidence_v297' 'research_integration_certification_findings_v297' 'research_integration_certification_revisions_v297' 'research_integration_certification_snapshots_v297')
V300_TABLES=('unified_research_runtime_sessions_v300' 'unified_research_runtime_object_bindings_v300' 'unified_research_runtime_product_bindings_v300' 'unified_research_runtime_execution_bindings_v300' 'unified_research_runtime_investigation_bindings_v300' 'unified_research_runtime_visual_bindings_v300' 'unified_research_runtime_validation_bindings_v300' 'unified_research_runtime_package_bindings_v300' 'unified_research_runtime_handoff_bindings_v300' 'unified_research_runtime_milestones_v300' 'unified_research_runtime_revisions_v300' 'unified_research_runtime_snapshots_v300')
echo "=== PREDECESSOR GATE ==="; [ "$(psqlq "SELECT EXISTS (SELECT 1 FROM schema_migrations WHERE version='0101');")" = t ] || { echo "STOP: migration 0101 is required before v3.0.0"; exit 1; }
for t in "${V297_TABLES[@]}"; do [ "$(psqlq "SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema='public' AND table_name='$t');")" = t ] || { echo "STOP: predecessor table $t missing"; exit 1; }; done
m102="$(psqlq "SELECT EXISTS (SELECT 1 FROM schema_migrations WHERE version='0102');")"; count=0; for t in "${V300_TABLES[@]}"; do [ "$(psqlq "SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema='public' AND table_name='$t');")" = t ] && count=$((count+1)); done
if [ "$m102" = f ] && [ "$count" -eq 0 ]; then echo "PASS: pristine pre-0102 state"; elif [ "$m102" = f ] && [ "$count" -eq 12 ]; then echo "PASS: recoverable partial-0102 state"; elif [ "$m102" = t ] && [ "$count" -eq 12 ]; then echo "PASS: already-complete 0102 state"; else echo "STOP: inconsistent 0102 state ($m102, $count/12)"; exit 1; fi
echo "=== BACKUP ==="; BACKUP_DIR="/opt/sustainable-catalyst/backups/platform-core-v3000"; mkdir -p "$BACKUP_DIR"; stamp="$(date +%Y%m%d-%H%M%S)"; docker exec -e PGPASSWORD="$DB_PASS" sc-postgres pg_dump -h 127.0.0.1 -U "$DB_USER" -d "$DB_NAME" -Fc > "$BACKUP_DIR/core-${stamp}.dump"; git rev-parse HEAD > "$BACKUP_DIR/git-head-${stamp}.txt"; tar --exclude='.git' --exclude='backend/.venv' -czf "$BACKUP_DIR/core-source-${stamp}.tar.gz" .
echo "=== PROMOTE TAGGED SOURCE ==="; git fetch origin --tags; git pull --ff-only origin main; git tag --points-at HEAD | grep -qx 'v3.0.0' || { echo "STOP: production HEAD is not tagged v3.0.0"; exit 1; }; python3 -S scripts/validate_v3000_release.py
echo "=== BUILD / MIGRATE ==="; $COMPOSE build core; $COMPOSE run --rm --no-deps core python scripts/migrate.py | tee /tmp/sc-core-v3000-migrate.json
for t in "${V300_TABLES[@]}"; do [ "$(psqlq "SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema='public' AND table_name='$t');")" = t ] || { echo "STOP: $t missing after migration"; exit 1; }; done; [ "$(psqlq "SELECT EXISTS (SELECT 1 FROM schema_migrations WHERE version='0102');")" = t ] || { echo "STOP: migration 0102 not recorded"; exit 1; }
$COMPOSE up -d --no-deps --force-recreate core; for i in $(seq 1 40); do curl -fsS http://127.0.0.1:8090/health >/tmp/sc-core-v3000-health.json 2>/dev/null && break; sleep 2; done
curl -fsS http://127.0.0.1:8090/v1/research/unified-runtime/readiness | tee /tmp/sc-core-v3000-readiness.json | python3 -m json.tool
python3 - <<'PY2'
import json
h=json.load(open('/tmp/sc-core-v3000-health.json')); r=json.load(open('/tmp/sc-core-v3000-readiness.json')); assert h.get('ok') is True and h.get('version')=='3.0.0',h; assert r.get('release')=='3.0.0' and r.get('migration_0102_applied') is True,r
for k in ('reference_first_runtime_by_core','unified_session_registry_by_core','research_object_binding_by_core','product_context_binding_by_core','computation_execution_binding_by_core','investigation_binding_by_core','visual_reasoning_binding_by_core','validation_challenge_binding_by_core','research_package_binding_by_core','cross_product_handoff_binding_by_core','milestone_registry_by_core','revision_history_by_core','immutable_runtime_snapshots_by_core','underlying_objects_remain_authoritative_in_specialist_layers'): assert r.get(k) is True,(k,r)
for k in ('execute_scientific_work_by_core','execute_code_by_core','run_investigation_by_core','infer_findings_by_core','infer_causality_by_core','select_hypothesis_by_core','rank_evidence_by_core','render_visuals_by_core','publish_research_by_core','authorize_access_by_core','certify_scientific_validity_by_core','determine_truth_by_core'): assert r.get(k) is False,(k,r)
print('PASS - Platform Core v3.0.0 Unified Research, Scientific Computing & Investigation Runtime')
PY2
curl -fsS https://core.sustainablecatalyst.com/health | python3 -m json.tool; echo "PASS - PLATFORM CORE v3.0.0 BACKEND DEPLOYMENT COMPLETE"
