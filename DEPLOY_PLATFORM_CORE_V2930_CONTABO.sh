#!/usr/bin/env bash
set -euo pipefail
trap 'rc=$?; echo "ERROR: v2.93.0 deployment stopped at line $LINENO (exit $rc): $BASH_COMMAND" >&2; exit $rc' ERR
echo "=== PLATFORM CORE v2.93.0 — RESEARCH ROLES, AGENTS & CONTRIBUTOR PROVENANCE FRAMEWORK ==="
cd /opt/sustainable-catalyst/core
COMPOSE="docker compose -f compose.yml -f compose.vps.yml"
resolve_db_url(){
  if [ -n "${SC_CORE_DATABASE_URL:-}" ]; then printf '%s' "$SC_CORE_DATABASE_URL"; return; fi
  if docker ps --format '{{.Names}}' | grep -qx 'sc-core'; then local u; u="$(docker exec sc-core printenv SC_CORE_DATABASE_URL 2>/dev/null || true)"; [ -n "$u" ] && { printf '%s' "$u"; return; }; fi
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
V292_TABLES=('research_project_states_v292' 'research_project_state_versions_v292' 'research_project_state_bindings_v292' 'research_project_state_dependencies_v292' 'research_project_state_environments_v292' 'research_project_state_checkpoints_v292' 'research_project_reconstruction_plans_v292' 'research_project_reconstruction_verifications_v292' 'research_project_state_revisions_v292' 'research_project_state_snapshots_v292')
V293_TABLES=('research_contributors_v293' 'research_role_definitions_v293' 'research_role_assignments_v293' 'research_contributions_v293' 'research_agent_profiles_v293' 'research_agent_actions_v293' 'research_authorship_assertions_v293' 'research_responsibility_statements_v293' 'research_contribution_reviews_v293' 'research_contributor_revisions_v293' 'research_contributor_snapshots_v293')
echo "=== PREDECESSOR GATE ==="
[ "$(psqlq "SELECT EXISTS (SELECT 1 FROM schema_migrations WHERE version='0096');")" = t ] || { echo "STOP: migration 0096 is required before v2.93.0"; exit 1; }
for t in "${V292_TABLES[@]}"; do [ "$(psqlq "SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema='public' AND table_name='$t');")" = t ] || { echo "STOP: predecessor table $t missing"; exit 1; }; done
m97="$(psqlq "SELECT EXISTS (SELECT 1 FROM schema_migrations WHERE version='0097');")"; count=0; for t in "${V293_TABLES[@]}"; do [ "$(psqlq "SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema='public' AND table_name='$t');")" = t ] && count=$((count+1)); done
if [ "$m97" = f ] && [ "$count" -eq 0 ]; then echo "PASS: pristine pre-0097 state"; elif [ "$m97" = f ] && [ "$count" -eq 11 ]; then echo "PASS: recoverable partial-0097 state"; elif [ "$m97" = t ] && [ "$count" -eq 11 ]; then echo "PASS: already-complete 0097 state"; else echo "STOP: inconsistent 0097 state ($m97, $count/11)"; exit 1; fi
echo "=== BACKUP ==="; BACKUP_DIR="/opt/sustainable-catalyst/backups/platform-core-v2930"; mkdir -p "$BACKUP_DIR"; stamp="$(date +%Y%m%d-%H%M%S)"; docker exec -e PGPASSWORD="$DB_PASS" sc-postgres pg_dump -h 127.0.0.1 -U "$DB_USER" -d "$DB_NAME" -Fc > "$BACKUP_DIR/core-${stamp}.dump"; git rev-parse HEAD > "$BACKUP_DIR/git-head-${stamp}.txt"; tar --exclude='.git' --exclude='backend/.venv' -czf "$BACKUP_DIR/core-source-${stamp}.tar.gz" .
echo "=== PROMOTE TAGGED SOURCE ==="; git fetch origin --tags; git pull --ff-only origin main; git tag --points-at HEAD | grep -qx 'v2.93.0' || { echo "STOP: production HEAD is not tagged v2.93.0"; exit 1; }; python3 -S scripts/validate_v2930_release.py
echo "=== BUILD / MIGRATE ==="; $COMPOSE build core; $COMPOSE run --rm --no-deps core python scripts/migrate.py | tee /tmp/sc-core-v2930-migrate.json
for t in "${V293_TABLES[@]}"; do [ "$(psqlq "SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema='public' AND table_name='$t');")" = t ] || { echo "STOP: $t missing after migration"; exit 1; }; done
[ "$(psqlq "SELECT EXISTS (SELECT 1 FROM schema_migrations WHERE version='0097');")" = t ] || { echo "STOP: migration 0097 not recorded"; exit 1; }
$COMPOSE up -d --no-deps --force-recreate core
for i in $(seq 1 40); do curl -fsS http://127.0.0.1:8090/health >/tmp/sc-core-v2930-health.json 2>/dev/null && break; sleep 2; done
curl -fsS http://127.0.0.1:8090/v1/research/contributors/readiness | tee /tmp/sc-core-v2930-contributors.json | python3 -m json.tool
python3 - <<'PY2'
import json
h=json.load(open('/tmp/sc-core-v2930-health.json')); r=json.load(open('/tmp/sc-core-v2930-contributors.json'))
assert h.get('ok') is True and h.get('version')=='2.93.0',h; assert r.get('release')=='2.93.0' and r.get('migration_0097_applied') is True,r
for k in ('contributor_registry_by_core','role_definition_registry_by_core','scoped_role_assignment_registry_by_core','contribution_provenance_registry_by_core','credit_taxonomy_registry_by_core','controlled_agent_profile_registry_by_core','agent_action_audit_registry_by_core','authorship_assertion_registry_by_core','responsibility_statement_registry_by_core','contribution_review_registry_by_core','human_ai_tool_distinction_by_core','revision_history_by_core','immutable_contributor_snapshots_by_core'): assert r.get(k) is True,(k,r)
for k in ('assign_roles_by_core','authorize_agents_by_core','execute_agent_actions_by_core','infer_contributor_identity_by_core','infer_authorship_by_core','rank_contributors_by_core','score_contributions_by_core','infer_responsibility_by_core','grant_permissions_by_core','decide_credit_by_core','determine_truth_by_core'): assert r.get(k) is False,(k,r)
print('PASS - Platform Core v2.93.0 Research Roles, Agents & Contributor Provenance Framework')
PY2
curl -fsS https://core.sustainablecatalyst.com/health | python3 -m json.tool
echo "PASS - PLATFORM CORE v2.93.0 BACKEND DEPLOYMENT COMPLETE"
