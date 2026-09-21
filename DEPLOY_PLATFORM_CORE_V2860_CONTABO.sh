#!/usr/bin/env bash
set -euo pipefail
trap 'rc=$?; echo "ERROR: v2.86.0 deployment stopped at line $LINENO (exit $rc): $BASH_COMMAND" >&2; exit $rc' ERR
ROOT="${SC_CORE_ROOT:-/opt/sustainable-catalyst/core}"; COMPOSE="docker compose -f compose.yml -f compose.vps.yml"; cd "$ROOT"
echo "=== PLATFORM CORE v2.86.0 — SCIENTIFIC STUDY & INVESTIGATION PROTOCOL MODEL ==="
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
[ "$(psqlq "SELECT EXISTS (SELECT 1 FROM schema_migrations WHERE version='0089');")" = t ] || { echo "STOP: migration 0089 missing; deploy v2.85.0 first"; exit 1; }
V285_TABLES=(research_portfolios_v285 research_portfolio_programs_v285 research_portfolio_themes_v285 research_portfolio_objectives_v285 research_portfolio_dependencies_v285 research_portfolio_resource_envelopes_v285 research_portfolio_risks_v285 research_portfolio_reviews_v285 research_portfolio_decisions_v285 research_portfolio_revisions_v285 research_portfolio_snapshots_v285)
for t in "${V285_TABLES[@]}"; do [ "$(psqlq "SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema='public' AND table_name='$t');")" = t ] || { echo "STOP: predecessor table missing: $t"; exit 1; }; done
V286_TABLES=(scientific_research_protocols_v286 scientific_protocol_objectives_v286 scientific_protocol_scope_units_v286 scientific_protocol_measures_v286 scientific_protocol_source_plans_v286 scientific_protocol_acquisition_plans_v286 scientific_protocol_method_plans_v286 scientific_protocol_assumptions_v286 scientific_protocol_validation_plans_v286 scientific_protocol_output_plans_v286 scientific_protocol_deviations_v286 scientific_protocol_revisions_v286 scientific_protocol_snapshots_v286)
count=0; for t in "${V286_TABLES[@]}"; do [ "$(psqlq "SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema='public' AND table_name='$t');")" = t ] && count=$((count+1)); done
m90="$(psqlq "SELECT EXISTS (SELECT 1 FROM schema_migrations WHERE version='0090');")"
if [ "$m90" = f ] && [ "$count" -eq 0 ]; then echo "PASS: pristine pre-0090 state"; elif [ "$m90" = f ] && [ "$count" -eq 13 ]; then echo "PASS: recoverable partial-0090 state"; elif [ "$m90" = t ] && [ "$count" -eq 13 ]; then echo "PASS: already-complete 0090 state"; else echo "STOP: inconsistent 0090 state ($m90, $count/13)"; exit 1; fi
echo "=== BACKUP ==="; BACKUP_DIR="/opt/sustainable-catalyst/backups/platform-core-v2860"; mkdir -p "$BACKUP_DIR"; stamp="$(date +%Y%m%d-%H%M%S)"; docker exec -e PGPASSWORD="$DB_PASS" sc-postgres pg_dump -h 127.0.0.1 -U "$DB_USER" -d "$DB_NAME" -Fc > "$BACKUP_DIR/core-${stamp}.dump"; git rev-parse HEAD > "$BACKUP_DIR/git-head-${stamp}.txt"; tar --exclude='.git' --exclude='backend/.venv' -czf "$BACKUP_DIR/core-source-${stamp}.tar.gz" .
echo "=== PROMOTE TAGGED SOURCE ==="; git fetch origin --tags; git pull --ff-only origin main; git tag --points-at HEAD | grep -qx 'v2.86.0' || { echo "STOP: production HEAD is not tagged v2.86.0"; exit 1; }; python3 -S scripts/validate_v2860_release.py
echo "=== BUILD / MIGRATE ==="; $COMPOSE build core; $COMPOSE run --rm --no-deps core python scripts/migrate.py | tee /tmp/sc-core-v2860-migrate.json
for t in "${V286_TABLES[@]}"; do [ "$(psqlq "SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema='public' AND table_name='$t');")" = t ] || { echo "STOP: $t missing after migration"; exit 1; }; done
[ "$(psqlq "SELECT EXISTS (SELECT 1 FROM schema_migrations WHERE version='0090');")" = t ] || { echo "STOP: migration 0090 not recorded"; exit 1; }
$COMPOSE up -d --no-deps --force-recreate core
for i in $(seq 1 40); do curl -fsS http://127.0.0.1:8090/health >/tmp/sc-core-v2860-health.json 2>/dev/null && break; sleep 2; done
curl -fsS http://127.0.0.1:8090/v1/research/protocols/readiness | tee /tmp/sc-core-v2860-protocol.json | python3 -m json.tool
python3 - <<'PY2'
import json
h=json.load(open('/tmp/sc-core-v2860-health.json')); r=json.load(open('/tmp/sc-core-v2860-protocol.json'))
assert h.get('ok') is True and h.get('version')=='2.86.0',h; assert r.get('release')=='2.86.0' and r.get('migration_0090_applied') is True,r
for k in ('universal_protocol_registry_by_core','protocol_objective_registry_by_core','population_system_case_scope_registry_by_core','variable_measure_registry_by_core','source_data_plan_registry_by_core','sampling_acquisition_plan_registry_by_core','analytical_method_plan_registry_by_core','assumption_registry_by_core','validation_challenge_plan_registry_by_core','planned_output_registry_by_core','protocol_deviation_registry_by_core','protocol_revision_history_by_core','protocol_lineage_by_core','immutable_protocol_snapshots_by_core'): assert r.get(k) is True,(k,r)
for k in ('execute_protocol_by_core','recruit_participants_by_core','randomize_by_core','collect_data_by_core','acquire_evidence_by_core','run_analysis_by_core','compute_results_by_core','infer_results_by_core','infer_causality_by_core','judge_method_quality_by_core','certify_ethics_by_core','approve_protocol_by_core','infer_truth_by_core'): assert r.get(k) is False,(k,r)
print('PASS - Platform Core v2.86.0 Scientific Study & Investigation Protocol Model')
PY2
curl -fsS https://core.sustainablecatalyst.com/health | python3 -m json.tool
echo "PASS - PLATFORM CORE v2.86.0 BACKEND DEPLOYMENT COMPLETE"
