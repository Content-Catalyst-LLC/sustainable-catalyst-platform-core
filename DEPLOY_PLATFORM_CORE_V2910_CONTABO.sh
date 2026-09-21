#!/usr/bin/env bash
set -euo pipefail
trap 'rc=$?; echo "ERROR: v2.91.0 deployment stopped at line $LINENO (exit $rc): $BASH_COMMAND" >&2; exit $rc' ERR
echo "=== PLATFORM CORE v2.91.0 — CROSS-PRODUCT RESEARCH CONTEXT & HANDOFF PROTOCOL ==="
cd /opt/sustainable-catalyst/core
COMPOSE="docker compose -f compose.yml -f compose.vps.yml"
resolve_db_url(){
  if [ -n "${SC_CORE_DATABASE_URL:-}" ]; then printf '%s' "$SC_CORE_DATABASE_URL"; return; fi
  if docker ps --format '{{.Names}}' | grep -qx 'sc-core'; then
    local u; u="$(docker exec sc-core printenv SC_CORE_DATABASE_URL 2>/dev/null || true)"; [ -n "$u" ] && { printf '%s' "$u"; return; }
  fi
  if [ -f .env.production ]; then grep -m1 '^SC_CORE_DATABASE_URL=' .env.production | cut -d= -f2- | sed 's/^"//;s/"$//' | sed "s/^'//;s/'$//"; return; fi
  return 1
}
CORE_DB_URL="$(resolve_db_url)" || { echo "STOP: SC_CORE_DATABASE_URL could not be resolved"; exit 1; }
eval "$(CORE_DB_URL="$CORE_DB_URL" python3 - <<'PYDB'
import os,shlex
from urllib.parse import urlparse,unquote
u=urlparse(os.environ['CORE_DB_URL'].replace('postgresql+psycopg://','postgresql://',1))
print('export DB_USER='+shlex.quote(unquote(u.username or '')))
print('export DB_PASS='+shlex.quote(unquote(u.password or '')))
print('export DB_NAME='+shlex.quote((u.path or '').lstrip('/')))
PYDB
)"
[ -n "$DB_USER" ] && [ -n "$DB_NAME" ] || { echo "STOP: database identity could not be parsed"; exit 1; }
psqlq(){ docker exec -e PGPASSWORD="$DB_PASS" sc-postgres psql -h 127.0.0.1 -U "$DB_USER" -d "$DB_NAME" -Atqc "$1"; }
V290_TABLES=('research_workflows_v290' 'research_workflow_stages_v290' 'research_workflow_transitions_v290' 'research_workflow_context_bindings_v290' 'research_workflow_handoffs_v290' 'research_workflow_checkpoints_v290' 'research_workflow_events_v290' 'research_workflow_policies_v290' 'research_workflow_revisions_v290' 'research_workflow_snapshots_v290')
V291_TABLES=('research_context_envelopes_v291' 'research_context_object_bindings_v291' 'research_context_provenance_bindings_v291' 'research_context_state_markers_v291' 'research_handoff_protocols_v291' 'research_handoff_packages_v291' 'research_handoff_acknowledgements_v291' 'research_handoff_conflicts_v291' 'research_handoff_revisions_v291' 'research_handoff_snapshots_v291')
echo "=== PREDECESSOR GATE ==="
[ "$(psqlq "SELECT EXISTS (SELECT 1 FROM schema_migrations WHERE version='0094');")" = t ] || { echo "STOP: migration 0094 is required before v2.91.0"; exit 1; }
for t in "${V290_TABLES[@]}"; do [ "$(psqlq "SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema='public' AND table_name='$t');")" = t ] || { echo "STOP: predecessor table $t missing"; exit 1; }; done
m95="$(psqlq "SELECT EXISTS (SELECT 1 FROM schema_migrations WHERE version='0095');")"; count=0; for t in "${V291_TABLES[@]}"; do [ "$(psqlq "SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema='public' AND table_name='$t');")" = t ] && count=$((count+1)); done
if [ "$m95" = f ] && [ "$count" -eq 0 ]; then echo "PASS: pristine pre-0095 state"; elif [ "$m95" = f ] && [ "$count" -eq 10 ]; then echo "PASS: recoverable partial-0095 state"; elif [ "$m95" = t ] && [ "$count" -eq 10 ]; then echo "PASS: already-complete 0095 state"; else echo "STOP: inconsistent 0095 state ($m95, $count/10)"; exit 1; fi
echo "=== BACKUP ==="; BACKUP_DIR="/opt/sustainable-catalyst/backups/platform-core-v2910"; mkdir -p "$BACKUP_DIR"; stamp="$(date +%Y%m%d-%H%M%S)"; docker exec -e PGPASSWORD="$DB_PASS" sc-postgres pg_dump -h 127.0.0.1 -U "$DB_USER" -d "$DB_NAME" -Fc > "$BACKUP_DIR/core-${stamp}.dump"; git rev-parse HEAD > "$BACKUP_DIR/git-head-${stamp}.txt"; tar --exclude='.git' --exclude='backend/.venv' -czf "$BACKUP_DIR/core-source-${stamp}.tar.gz" .
echo "=== PROMOTE TAGGED SOURCE ==="; git fetch origin --tags; git pull --ff-only origin main; git tag --points-at HEAD | grep -qx 'v2.91.0' || { echo "STOP: production HEAD is not tagged v2.91.0"; exit 1; }; python3 -S scripts/validate_v2910_release.py
echo "=== BUILD / MIGRATE ==="; $COMPOSE build core; $COMPOSE run --rm --no-deps core python scripts/migrate.py | tee /tmp/sc-core-v2910-migrate.json
for t in "${V291_TABLES[@]}"; do [ "$(psqlq "SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema='public' AND table_name='$t');")" = t ] || { echo "STOP: $t missing after migration"; exit 1; }; done
[ "$(psqlq "SELECT EXISTS (SELECT 1 FROM schema_migrations WHERE version='0095');")" = t ] || { echo "STOP: migration 0095 not recorded"; exit 1; }
$COMPOSE up -d --no-deps --force-recreate core
for i in $(seq 1 40); do curl -fsS http://127.0.0.1:8090/health >/tmp/sc-core-v2910-health.json 2>/dev/null && break; sleep 2; done
curl -fsS http://127.0.0.1:8090/v1/research/context-handoffs/readiness | tee /tmp/sc-core-v2910-context.json | python3 -m json.tool
python3 - <<'PY2'
import json
h=json.load(open('/tmp/sc-core-v2910-health.json')); r=json.load(open('/tmp/sc-core-v2910-context.json'))
assert h.get('ok') is True and h.get('version')=='2.91.0',h; assert r.get('release')=='2.91.0' and r.get('migration_0095_applied') is True,r
for k in ('context_envelope_registry_by_core','object_binding_registry_by_core','provenance_binding_registry_by_core','state_marker_registry_by_core','handoff_protocol_registry_by_core','handoff_package_manifest_by_core','declared_contract_completeness_by_core','package_integrity_verification_by_core','acknowledgement_registry_by_core','conflict_registry_by_core','revision_history_by_core','context_lineage_by_core','immutable_context_snapshots_by_core'): assert r.get(k) is True,(k,r)
for k in ('auto_route_handoff_by_core','execute_handoff_by_core','dispatch_external_jobs_by_core','choose_target_product_by_core','mutate_source_objects_by_core','infer_missing_context_by_core','resolve_context_conflicts_by_core','authorize_access_by_core','infer_research_validity_by_core','determine_truth_by_core'): assert r.get(k) is False,(k,r)
print('PASS - Platform Core v2.91.0 Cross-Product Research Context & Handoff Protocol')
PY2
curl -fsS https://core.sustainablecatalyst.com/health | python3 -m json.tool
echo "PASS - PLATFORM CORE v2.91.0 BACKEND DEPLOYMENT COMPLETE"
