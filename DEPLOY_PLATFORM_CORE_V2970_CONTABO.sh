#!/usr/bin/env bash
set -euo pipefail
trap 'rc=$?; echo "ERROR: v2.97.0 deployment stopped at line $LINENO (exit $rc): $BASH_COMMAND" >&2; exit $rc' ERR
echo "=== PLATFORM CORE v2.97.0 — PLATFORM RESEARCH INTEGRATION CERTIFICATION ==="
cd /opt/sustainable-catalyst/core; COMPOSE="docker compose -f compose.yml -f compose.vps.yml"
resolve_db_url(){ if [ -n "${SC_CORE_DATABASE_URL:-}" ]; then printf '%s' "$SC_CORE_DATABASE_URL"; return; fi; if docker ps --format '{{.Names}}' | grep -qx 'sc-core'; then local u; u="$(docker exec sc-core printenv SC_CORE_DATABASE_URL 2>/dev/null || true)"; [ -n "$u" ] && { printf '%s' "$u"; return; }; fi; if [ -f .env.production ]; then grep -m1 '^SC_CORE_DATABASE_URL=' .env.production | cut -d= -f2- | sed 's/^"//;s/"$//' | sed "s/^'//;s/'$//"; return; fi; return 1; }
CORE_DB_URL="$(resolve_db_url)" || { echo "STOP: SC_CORE_DATABASE_URL could not be resolved"; exit 1; }
eval "$(CORE_DB_URL="$CORE_DB_URL" python3 - <<'PYDB'
import os,shlex
from urllib.parse import urlparse,unquote
u=urlparse(os.environ['CORE_DB_URL'].replace('postgresql+psycopg://','postgresql://',1)); print('export DB_USER='+shlex.quote(unquote(u.username or ''))); print('export DB_PASS='+shlex.quote(unquote(u.password or ''))); print('export DB_NAME='+shlex.quote((u.path or '').lstrip('/')))
PYDB
)"
[ -n "$DB_USER" ] && [ -n "$DB_NAME" ] || { echo "STOP: database identity could not be parsed"; exit 1; }
psqlq(){ docker exec -e PGPASSWORD="$DB_PASS" sc-postgres psql -h 127.0.0.1 -U "$DB_USER" -d "$DB_NAME" -Atqc "$1"; }
V296_TABLES=('research_runtime_contracts_v296' 'research_runtime_object_types_v296' 'research_runtime_operations_v296' 'research_runtime_capabilities_v296' 'research_runtime_product_bindings_v296' 'research_runtime_exchange_envelopes_v296' 'research_runtime_invocations_v296' 'research_runtime_result_bindings_v296' 'research_runtime_compatibility_assertions_v296' 'research_runtime_revisions_v296' 'research_runtime_snapshots_v296')
V297_TABLES=('research_integration_certification_suites_v297' 'research_integration_certification_products_v297' 'research_integration_certification_cases_v297' 'research_integration_certification_runs_v297' 'research_integration_certification_case_results_v297' 'research_integration_certification_exchange_checks_v297' 'research_integration_certification_trace_checks_v297' 'research_integration_certification_reproduction_checks_v297' 'research_integration_certification_evidence_v297' 'research_integration_certification_findings_v297' 'research_integration_certification_revisions_v297' 'research_integration_certification_snapshots_v297')
echo "=== PREDECESSOR GATE ==="; [ "$(psqlq "SELECT EXISTS (SELECT 1 FROM schema_migrations WHERE version='0100');")" = t ] || { echo "STOP: migration 0100 is required before v2.97.0"; exit 1; }
for t in "${V296_TABLES[@]}"; do [ "$(psqlq "SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema='public' AND table_name='$t');")" = t ] || { echo "STOP: predecessor table $t missing"; exit 1; }; done
m101="$(psqlq "SELECT EXISTS (SELECT 1 FROM schema_migrations WHERE version='0101');")"; count=0; for t in "${V297_TABLES[@]}"; do [ "$(psqlq "SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema='public' AND table_name='$t');")" = t ] && count=$((count+1)); done
if [ "$m101" = f ] && [ "$count" -eq 0 ]; then echo "PASS: pristine pre-0101 state"; elif [ "$m101" = f ] && [ "$count" -eq 12 ]; then echo "PASS: recoverable partial-0101 state"; elif [ "$m101" = t ] && [ "$count" -eq 12 ]; then echo "PASS: already-complete 0101 state"; else echo "STOP: inconsistent 0101 state ($m101, $count/12)"; exit 1; fi
echo "=== BACKUP ==="; BACKUP_DIR="/opt/sustainable-catalyst/backups/platform-core-v2970"; mkdir -p "$BACKUP_DIR"; stamp="$(date +%Y%m%d-%H%M%S)"; docker exec -e PGPASSWORD="$DB_PASS" sc-postgres pg_dump -h 127.0.0.1 -U "$DB_USER" -d "$DB_NAME" -Fc > "$BACKUP_DIR/core-${stamp}.dump"; git rev-parse HEAD > "$BACKUP_DIR/git-head-${stamp}.txt"; tar --exclude='.git' --exclude='backend/.venv' -czf "$BACKUP_DIR/core-source-${stamp}.tar.gz" .
echo "=== PROMOTE TAGGED SOURCE ==="; git fetch origin --tags; git pull --ff-only origin main; git tag --points-at HEAD | grep -qx 'v2.97.0' || { echo "STOP: production HEAD is not tagged v2.97.0"; exit 1; }; python3 -S scripts/validate_v2970_release.py
echo "=== BUILD / MIGRATE ==="; $COMPOSE build core; $COMPOSE run --rm --no-deps core python scripts/migrate.py | tee /tmp/sc-core-v2970-migrate.json
for t in "${V297_TABLES[@]}"; do [ "$(psqlq "SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema='public' AND table_name='$t');")" = t ] || { echo "STOP: $t missing after migration"; exit 1; }; done; [ "$(psqlq "SELECT EXISTS (SELECT 1 FROM schema_migrations WHERE version='0101');")" = t ] || { echo "STOP: migration 0101 not recorded"; exit 1; }
$COMPOSE up -d --no-deps --force-recreate core; for i in $(seq 1 40); do curl -fsS http://127.0.0.1:8090/health >/tmp/sc-core-v2970-health.json 2>/dev/null && break; sleep 2; done
curl -fsS http://127.0.0.1:8090/v1/research/integration-certification/readiness | tee /tmp/sc-core-v2970-readiness.json | python3 -m json.tool
python3 - <<'PY2'
import json
h=json.load(open('/tmp/sc-core-v2970-health.json')); r=json.load(open('/tmp/sc-core-v2970-readiness.json')); assert h.get('ok') is True and h.get('version')=='2.97.0',h; assert r.get('release')=='2.97.0' and r.get('migration_0101_applied') is True,r
for k in ('certification_suite_registry_by_core','certification_product_registry_by_core','conformance_case_registry_by_core','conformance_run_registry_by_core','conformance_result_registry_by_core','exchange_check_registry_by_core','trace_check_registry_by_core','reproduction_check_registry_by_core','certification_evidence_registry_by_core','certification_finding_registry_by_core','revision_history_by_core','immutable_certification_snapshots_by_core'): assert r.get(k) is True,(k,r)
for k in ('invoke_product_by_core','execute_conformance_case_by_core','certify_scientific_validity_by_core','certify_product_quality_by_core','authorize_product_by_certification_by_core','rank_products_by_core','infer_missing_evidence_by_core','infer_reproducibility_by_core','resolve_failed_case_by_core','determine_truth_by_core'): assert r.get(k) is False,(k,r)
print('PASS - Platform Core v2.97.0 Platform Research Integration Certification')
PY2
curl -fsS https://core.sustainablecatalyst.com/health | python3 -m json.tool; echo "PASS - PLATFORM CORE v2.97.0 BACKEND DEPLOYMENT COMPLETE"
