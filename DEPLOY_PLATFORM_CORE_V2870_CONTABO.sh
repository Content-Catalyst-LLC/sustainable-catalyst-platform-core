#!/usr/bin/env bash
set -euo pipefail
trap 'rc=$?; echo "ERROR: v2.87.0 deployment stopped at line $LINENO (exit $rc): $BASH_COMMAND" >&2; exit $rc' ERR
ROOT="${SC_CORE_ROOT:-/opt/sustainable-catalyst/core}"; COMPOSE="docker compose -f compose.yml -f compose.vps.yml"; cd "$ROOT"
echo "=== PLATFORM CORE v2.87.0 — COMPUTATION, ANALYSIS & EXECUTION LINEAGE ==="
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
[ "$(psqlq "SELECT EXISTS (SELECT 1 FROM schema_migrations WHERE version='0090');")" = t ] || { echo "STOP: migration 0090 missing; deploy v2.86.0 first"; exit 1; }
V286_TABLES=(scientific_research_protocols_v286 scientific_protocol_objectives_v286 scientific_protocol_scope_units_v286 scientific_protocol_measures_v286 scientific_protocol_source_plans_v286 scientific_protocol_acquisition_plans_v286 scientific_protocol_method_plans_v286 scientific_protocol_assumptions_v286 scientific_protocol_validation_plans_v286 scientific_protocol_output_plans_v286 scientific_protocol_deviations_v286 scientific_protocol_revisions_v286 scientific_protocol_snapshots_v286)
for t in "${V286_TABLES[@]}"; do [ "$(psqlq "SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema='public' AND table_name='$t');")" = t ] || { echo "STOP: predecessor table missing: $t"; exit 1; }; done
V287_TABLES=(computation_executions_v287 computation_execution_inputs_v287 computation_execution_parameters_v287 computation_execution_assumptions_v287 computation_execution_environments_v287 computation_execution_steps_v287 computation_execution_outputs_v287 computation_research_bindings_v287 computation_execution_dependencies_v287 computation_execution_verifications_v287 computation_execution_revisions_v287 computation_execution_snapshots_v287)
count=0; for t in "${V287_TABLES[@]}"; do [ "$(psqlq "SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema='public' AND table_name='$t');")" = t ] && count=$((count+1)); done
m91="$(psqlq "SELECT EXISTS (SELECT 1 FROM schema_migrations WHERE version='0091');")"
if [ "$m91" = f ] && [ "$count" -eq 0 ]; then echo "PASS: pristine pre-0091 state"; elif [ "$m91" = f ] && [ "$count" -eq 12 ]; then echo "PASS: recoverable partial-0091 state"; elif [ "$m91" = t ] && [ "$count" -eq 12 ]; then echo "PASS: already-complete 0091 state"; else echo "STOP: inconsistent 0091 state ($m91, $count/12)"; exit 1; fi
echo "=== BACKUP ==="; BACKUP_DIR="/opt/sustainable-catalyst/backups/platform-core-v2870"; mkdir -p "$BACKUP_DIR"; stamp="$(date +%Y%m%d-%H%M%S)"; docker exec -e PGPASSWORD="$DB_PASS" sc-postgres pg_dump -h 127.0.0.1 -U "$DB_USER" -d "$DB_NAME" -Fc > "$BACKUP_DIR/core-${stamp}.dump"; git rev-parse HEAD > "$BACKUP_DIR/git-head-${stamp}.txt"; tar --exclude='.git' --exclude='backend/.venv' -czf "$BACKUP_DIR/core-source-${stamp}.tar.gz" .
echo "=== PROMOTE TAGGED SOURCE ==="; git fetch origin --tags; git pull --ff-only origin main; git tag --points-at HEAD | grep -qx 'v2.87.0' || { echo "STOP: production HEAD is not tagged v2.87.0"; exit 1; }; python3 -S scripts/validate_v2870_release.py
echo "=== BUILD / MIGRATE ==="; $COMPOSE build core; $COMPOSE run --rm --no-deps core python scripts/migrate.py | tee /tmp/sc-core-v2870-migrate.json
for t in "${V287_TABLES[@]}"; do [ "$(psqlq "SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema='public' AND table_name='$t');")" = t ] || { echo "STOP: $t missing after migration"; exit 1; }; done
[ "$(psqlq "SELECT EXISTS (SELECT 1 FROM schema_migrations WHERE version='0091');")" = t ] || { echo "STOP: migration 0091 not recorded"; exit 1; }
$COMPOSE up -d --no-deps --force-recreate core
for i in $(seq 1 40); do curl -fsS http://127.0.0.1:8090/health >/tmp/sc-core-v2870-health.json 2>/dev/null && break; sleep 2; done
curl -fsS http://127.0.0.1:8090/v1/research/computation-lineage/readiness | tee /tmp/sc-core-v2870-lineage.json | python3 -m json.tool
python3 - <<'PY2'
import json
h=json.load(open('/tmp/sc-core-v2870-health.json')); r=json.load(open('/tmp/sc-core-v2870-lineage.json'))
assert h.get('ok') is True and h.get('version')=='2.87.0',h; assert r.get('release')=='2.87.0' and r.get('migration_0091_applied') is True,r
for k in ('execution_registry_by_core','versioned_input_binding_by_core','parameter_binding_by_core','assumption_binding_by_core','software_environment_capture_by_core','execution_step_registry_by_core','output_binding_by_core','research_object_binding_by_core','cross_execution_dependency_registry_by_core','verification_evidence_registry_by_core','execution_revision_history_by_core','execution_lineage_by_core','immutable_execution_snapshots_by_core'): assert r.get(k) is True,(k,r)
for k in ('execute_code_by_core','run_python_by_core','run_r_by_core','run_julia_by_core','run_workbench_by_core','train_ml_by_core','transform_data_by_core','compute_statistics_by_core','fit_models_by_core','generate_outputs_by_core','infer_findings_by_core','infer_claims_by_core','validate_results_by_core','infer_reproducibility_by_core','infer_truth_by_core'): assert r.get(k) is False,(k,r)
print('PASS - Platform Core v2.87.0 Computation, Analysis & Execution Lineage')
PY2
curl -fsS https://core.sustainablecatalyst.com/health | python3 -m json.tool
echo "PASS - PLATFORM CORE v2.87.0 BACKEND DEPLOYMENT COMPLETE"
