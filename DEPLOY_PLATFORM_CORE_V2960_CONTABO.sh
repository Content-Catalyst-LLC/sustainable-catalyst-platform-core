#!/usr/bin/env bash
set -euo pipefail
trap 'rc=$?; echo "ERROR: v2.96.0 deployment stopped at line $LINENO (exit $rc): $BASH_COMMAND" >&2; exit $rc' ERR
echo "=== PLATFORM CORE v2.96.0 — UNIFIED RESEARCH RUNTIME CONTRACT ==="
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
V295_TABLES=('scholarly_research_packages_v295' 'scholarly_package_members_v295' 'scholarly_citations_v295' 'scholarly_persistent_identifiers_v295' 'scholarly_dataset_descriptors_v295' 'scholarly_notebook_descriptors_v295' 'scholarly_provenance_manifests_v295' 'scholarly_metadata_profiles_v295' 'scholarly_export_profiles_v295' 'scholarly_publication_bindings_v295' 'scholarly_interoperability_validations_v295' 'scholarly_interoperability_revisions_v295' 'scholarly_interoperability_snapshots_v295')
V296_TABLES=('research_runtime_contracts_v296' 'research_runtime_object_types_v296' 'research_runtime_operations_v296' 'research_runtime_capabilities_v296' 'research_runtime_product_bindings_v296' 'research_runtime_exchange_envelopes_v296' 'research_runtime_invocations_v296' 'research_runtime_result_bindings_v296' 'research_runtime_compatibility_assertions_v296' 'research_runtime_revisions_v296' 'research_runtime_snapshots_v296')
echo "=== PREDECESSOR GATE ==="; [ "$(psqlq "SELECT EXISTS (SELECT 1 FROM schema_migrations WHERE version='0099');")" = t ] || { echo "STOP: migration 0099 is required before v2.96.0"; exit 1; }
for t in "${V295_TABLES[@]}"; do [ "$(psqlq "SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema='public' AND table_name='$t');")" = t ] || { echo "STOP: predecessor table $t missing"; exit 1; }; done
m100="$(psqlq "SELECT EXISTS (SELECT 1 FROM schema_migrations WHERE version='0100');")"; count=0; for t in "${V296_TABLES[@]}"; do [ "$(psqlq "SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema='public' AND table_name='$t');")" = t ] && count=$((count+1)); done
if [ "$m100" = f ] && [ "$count" -eq 0 ]; then echo "PASS: pristine pre-0100 state"; elif [ "$m100" = f ] && [ "$count" -eq 11 ]; then echo "PASS: recoverable partial-0100 state"; elif [ "$m100" = t ] && [ "$count" -eq 11 ]; then echo "PASS: already-complete 0100 state"; else echo "STOP: inconsistent 0100 state ($m100, $count/11)"; exit 1; fi
echo "=== BACKUP ==="; BACKUP_DIR="/opt/sustainable-catalyst/backups/platform-core-v2960"; mkdir -p "$BACKUP_DIR"; stamp="$(date +%Y%m%d-%H%M%S)"; docker exec -e PGPASSWORD="$DB_PASS" sc-postgres pg_dump -h 127.0.0.1 -U "$DB_USER" -d "$DB_NAME" -Fc > "$BACKUP_DIR/core-${stamp}.dump"; git rev-parse HEAD > "$BACKUP_DIR/git-head-${stamp}.txt"; tar --exclude='.git' --exclude='backend/.venv' -czf "$BACKUP_DIR/core-source-${stamp}.tar.gz" .
echo "=== PROMOTE TAGGED SOURCE ==="; git fetch origin --tags; git pull --ff-only origin main; git tag --points-at HEAD | grep -qx 'v2.96.0' || { echo "STOP: production HEAD is not tagged v2.96.0"; exit 1; }; python3 -S scripts/validate_v2960_release.py
echo "=== BUILD / MIGRATE ==="; $COMPOSE build core; $COMPOSE run --rm --no-deps core python scripts/migrate.py | tee /tmp/sc-core-v2960-migrate.json
for t in "${V296_TABLES[@]}"; do [ "$(psqlq "SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema='public' AND table_name='$t');")" = t ] || { echo "STOP: $t missing after migration"; exit 1; }; done; [ "$(psqlq "SELECT EXISTS (SELECT 1 FROM schema_migrations WHERE version='0100');")" = t ] || { echo "STOP: migration 0100 not recorded"; exit 1; }
$COMPOSE up -d --no-deps --force-recreate core; for i in $(seq 1 40); do curl -fsS http://127.0.0.1:8090/health >/tmp/sc-core-v2960-health.json 2>/dev/null && break; sleep 2; done
curl -fsS http://127.0.0.1:8090/v1/research/runtime-contract/readiness | tee /tmp/sc-core-v2960-readiness.json | python3 -m json.tool
python3 - <<'PY2'
import json
h=json.load(open('/tmp/sc-core-v2960-health.json')); r=json.load(open('/tmp/sc-core-v2960-readiness.json')); assert h.get('ok') is True and h.get('version')=='2.96.0',h; assert r.get('release')=='2.96.0' and r.get('migration_0100_applied') is True,r
for k in ('runtime_contract_registry_by_core','runtime_object_type_registry_by_core','runtime_operation_registry_by_core','runtime_capability_registry_by_core','product_binding_registry_by_core','exchange_envelope_registry_by_core','invocation_lineage_registry_by_core','result_binding_registry_by_core','compatibility_assertion_registry_by_core','revision_history_by_core','immutable_runtime_snapshots_by_core'): assert r.get(k) is True,(k,r)
for k in ('execute_specialist_work_by_core','auto_route_requests_by_core','infer_object_schema_by_core','mutate_specialist_state_by_core','authorize_product_by_contract_by_core','validate_scientific_result_by_core','resolve_semantic_conflict_by_core','certify_reproducibility_by_core','invoke_external_runtime_by_core','determine_truth_by_core'): assert r.get(k) is False,(k,r)
print('PASS - Platform Core v2.96.0 Unified Research Runtime Contract')
PY2
curl -fsS https://core.sustainablecatalyst.com/health | python3 -m json.tool; echo "PASS - PLATFORM CORE v2.96.0 BACKEND DEPLOYMENT COMPLETE"
