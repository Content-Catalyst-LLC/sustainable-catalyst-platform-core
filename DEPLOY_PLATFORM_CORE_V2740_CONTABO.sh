#!/usr/bin/env bash
set -euo pipefail
trap 'rc=$?; echo "ERROR: v2.74.0 deployment stopped at line $LINENO (exit $rc): $BASH_COMMAND" >&2; exit $rc' ERR
ROOT="${SC_CORE_ROOT:-/opt/sustainable-catalyst/core}"; COMPOSE="docker compose -f compose.yml -f compose.vps.yml"; cd "$ROOT"
echo "=== PLATFORM CORE v2.74.0 — RESEARCH LINEAGE & PROVENANCE GRAPH ==="
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
[ "$(psqlq "SELECT EXISTS (SELECT 1 FROM schema_migrations WHERE version='0077');")" = t ] || { echo "STOP: migration 0077 missing; deploy v2.73.0 first"; exit 1; }
V273_TABLES=(research_lineage_graphs research_lineage_nodes research_lineage_edges research_lineage_activities research_lineage_transformations research_lineage_source_bindings research_lineage_traces research_lineage_snapshots)
for t in "${V273_TABLES[@]}"; do [ "$(psqlq "SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema='public' AND table_name='$t');")" = t ] || { echo "STOP: predecessor table missing: $t"; exit 1; }; done
V274_TABLES=(research_methodologies research_methodology_versions research_method_variables research_method_assumptions research_method_parameters research_execution_environments research_analysis_runs research_analysis_run_inputs research_analysis_run_outputs research_methodology_snapshots)
count=0; for t in "${V274_TABLES[@]}"; do [ "$(psqlq "SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema='public' AND table_name='$t');")" = t ] && count=$((count+1)); done
m78="$(psqlq "SELECT EXISTS (SELECT 1 FROM schema_migrations WHERE version='0078');")"
if [ "$m78" = f ] && [ "$count" -eq 0 ]; then echo "PASS: pristine pre-0078 state"; elif [ "$m78" = f ] && [ "$count" -eq 10 ]; then echo "PASS: recoverable partial-0078 state"; elif [ "$m78" = t ] && [ "$count" -eq 10 ]; then echo "PASS: already-complete 0078 state"; else echo "STOP: inconsistent 0078 state ($m78, $count/10)"; exit 1; fi
echo "=== BACKUP ==="; BACKUP_DIR="/opt/sustainable-catalyst/backups/platform-core-v2740"; mkdir -p "$BACKUP_DIR"; stamp="$(date +%Y%m%d-%H%M%S)"; docker exec -e PGPASSWORD="$DB_PASS" sc-postgres pg_dump -h 127.0.0.1 -U "$DB_USER" -d "$DB_NAME" -Fc > "$BACKUP_DIR/core-${stamp}.dump"; git rev-parse HEAD > "$BACKUP_DIR/git-head-${stamp}.txt"; tar --exclude='.git' --exclude='backend/.venv' -czf "$BACKUP_DIR/core-source-${stamp}.tar.gz" .
git fetch origin --tags; git pull --ff-only origin main; git tag --points-at HEAD | grep -qx 'v2.74.0' || { echo "STOP: production HEAD is not tagged v2.74.0"; exit 1; }
python3 -S scripts/validate_v2740_release.py
$COMPOSE build core
$COMPOSE run --rm --no-deps core python scripts/migrate.py | tee /tmp/sc-core-v2740-migrate.json
for t in "${V274_TABLES[@]}"; do [ "$(psqlq "SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema='public' AND table_name='$t');")" = t ] || { echo "STOP: $t missing after migration"; exit 1; }; done
[ "$(psqlq "SELECT EXISTS (SELECT 1 FROM schema_migrations WHERE version='0078');")" = t ] || { echo "STOP: migration 0078 not recorded"; exit 1; }
$COMPOSE up -d --no-deps --force-recreate core
for i in $(seq 1 40); do curl -fsS http://127.0.0.1:8090/health >/tmp/sc-core-v2740-health.json 2>/dev/null && break; sleep 2; done
curl -fsS http://127.0.0.1:8090/v1/research/methodology/readiness | tee /tmp/sc-core-v2740-methodology.json | python3 -m json.tool
python3 - <<'PY2'
import json
h=json.load(open('/tmp/sc-core-v2740-health.json'));r=json.load(open('/tmp/sc-core-v2740-methodology.json'));assert h.get('ok') is True and h.get('version')=='2.74.0',h;assert r.get('release')=='2.74.0' and r.get('migration_0078_applied') is True,r
for k in ('methodology_registry_by_core','methodology_version_registry_by_core','variable_registry_by_core','assumption_exclusion_registry_by_core','parameter_registry_by_core','execution_environment_registry_by_core','analysis_run_registry_by_core','run_input_output_registry_by_core','immutable_methodology_snapshots_by_core'):assert r.get(k) is True,(k,r)
for k in ('execute_analysis_by_core','validate_results_by_core','infer_causality_by_core','judge_research_quality_by_core','infer_method_validity_by_core','select_method_by_core','alter_external_results_by_core'):assert r.get(k) is False,(k,r)
print('PASS - Platform Core v2.74.0 Methodology & Analysis Run Registry')
PY2'
import json
h=json.load(open('/tmp/sc-core-v2740-health.json'));r=json.load(open('/tmp/sc-core-v2740-methodology.json'));assert h.get('ok') is True and h.get('version')=='2.73.0',h;assert r.get('release')=='2.73.0' and r.get('migration_0078_applied') is True,r
for k in ('lineage_graph_registry_by_core','lineage_node_registry_by_core','explicit_lineage_edge_registry_by_core','provenance_activity_registry_by_core','transformation_registry_by_core','source_binding_registry_by_core','deterministic_declared_trace_by_core','immutable_lineage_snapshots_by_core'):assert r.get(k) is True,(k,r)
for k in ('infer_missing_edges_by_core','infer_causality_by_core','generate_findings_by_core','promote_truth_by_core','infer_originality_by_core','execute_analysis_by_core','alter_source_evidence_by_core'):assert r.get(k) is False,(k,r)
print('PASS - Platform Core v2.74.0 Methodology & Analysis Run Registry')
PY2
curl -fsS https://core.sustainablecatalyst.com/health | python3 -m json.tool
echo "PASS - PLATFORM CORE v2.74.0 BACKEND DEPLOYMENT COMPLETE"
