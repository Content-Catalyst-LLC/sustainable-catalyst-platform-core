#!/usr/bin/env bash
set -euo pipefail
trap 'rc=$?; echo "ERROR: v2.94.0 deployment stopped at line $LINENO (exit $rc): $BASH_COMMAND" >&2; exit $rc' ERR
echo "=== PLATFORM CORE v2.94.0 — RESEARCH VALIDATION & CHALLENGE ENGINE ==="
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
V293_TABLES=('research_contributors_v293' 'research_role_definitions_v293' 'research_role_assignments_v293' 'research_contributions_v293' 'research_agent_profiles_v293' 'research_agent_actions_v293' 'research_authorship_assertions_v293' 'research_responsibility_statements_v293' 'research_contribution_reviews_v293' 'research_contributor_revisions_v293' 'research_contributor_snapshots_v293')
V294_TABLES=('research_validation_challenges_v294' 'research_validation_targets_v294' 'research_alternative_hypotheses_v294' 'research_contradiction_tests_v294' 'research_counterevidence_v294' 'research_sensitivity_checks_v294' 'research_robustness_checks_v294' 'research_replication_attempts_v294' 'research_reviewer_challenges_v294' 'research_challenge_responses_v294' 'research_validation_revisions_v294' 'research_validation_snapshots_v294')
echo "=== PREDECESSOR GATE ==="
[ "$(psqlq "SELECT EXISTS (SELECT 1 FROM schema_migrations WHERE version='0097');")" = t ] || { echo "STOP: migration 0097 is required before v2.94.0"; exit 1; }
for t in "${V293_TABLES[@]}"; do [ "$(psqlq "SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema='public' AND table_name='$t');")" = t ] || { echo "STOP: predecessor table $t missing"; exit 1; }; done
m98="$(psqlq "SELECT EXISTS (SELECT 1 FROM schema_migrations WHERE version='0098');")"; count=0; for t in "${V294_TABLES[@]}"; do [ "$(psqlq "SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema='public' AND table_name='$t');")" = t ] && count=$((count+1)); done
if [ "$m98" = f ] && [ "$count" -eq 0 ]; then echo "PASS: pristine pre-0098 state"; elif [ "$m98" = f ] && [ "$count" -eq 12 ]; then echo "PASS: recoverable partial-0098 state"; elif [ "$m98" = t ] && [ "$count" -eq 12 ]; then echo "PASS: already-complete 0098 state"; else echo "STOP: inconsistent 0098 state ($m98, $count/12)"; exit 1; fi
echo "=== BACKUP ==="; BACKUP_DIR="/opt/sustainable-catalyst/backups/platform-core-v2940"; mkdir -p "$BACKUP_DIR"; stamp="$(date +%Y%m%d-%H%M%S)"; docker exec -e PGPASSWORD="$DB_PASS" sc-postgres pg_dump -h 127.0.0.1 -U "$DB_USER" -d "$DB_NAME" -Fc > "$BACKUP_DIR/core-${stamp}.dump"; git rev-parse HEAD > "$BACKUP_DIR/git-head-${stamp}.txt"; tar --exclude='.git' --exclude='backend/.venv' -czf "$BACKUP_DIR/core-source-${stamp}.tar.gz" .
echo "=== PROMOTE TAGGED SOURCE ==="; git fetch origin --tags; git pull --ff-only origin main; git tag --points-at HEAD | grep -qx 'v2.94.0' || { echo "STOP: production HEAD is not tagged v2.94.0"; exit 1; }; python3 -S scripts/validate_v2940_release.py
echo "=== BUILD / MIGRATE ==="; $COMPOSE build core; $COMPOSE run --rm --no-deps core python scripts/migrate.py | tee /tmp/sc-core-v2940-migrate.json
for t in "${V294_TABLES[@]}"; do [ "$(psqlq "SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema='public' AND table_name='$t');")" = t ] || { echo "STOP: $t missing after migration"; exit 1; }; done
[ "$(psqlq "SELECT EXISTS (SELECT 1 FROM schema_migrations WHERE version='0098');")" = t ] || { echo "STOP: migration 0098 not recorded"; exit 1; }
$COMPOSE up -d --no-deps --force-recreate core
for i in $(seq 1 40); do curl -fsS http://127.0.0.1:8090/health >/tmp/sc-core-v2940-health.json 2>/dev/null && break; sleep 2; done
curl -fsS http://127.0.0.1:8090/v1/research/validation-challenges/readiness | tee /tmp/sc-core-v2940-validation.json | python3 -m json.tool
python3 - <<'PY2'
import json
h=json.load(open('/tmp/sc-core-v2940-health.json')); r=json.load(open('/tmp/sc-core-v2940-validation.json'))
assert h.get('ok') is True and h.get('version')=='2.94.0',h; assert r.get('release')=='2.94.0' and r.get('migration_0098_applied') is True,r
for k in ('validation_challenge_registry_by_core','target_binding_registry_by_core','alternative_hypothesis_registry_by_core','contradiction_test_registry_by_core','counterevidence_registry_by_core','sensitivity_check_registry_by_core','robustness_check_registry_by_core','replication_attempt_registry_by_core','reviewer_challenge_registry_by_core','challenge_response_registry_by_core','revision_history_by_core','immutable_validation_snapshots_by_core'): assert r.get(k) is True,(k,r)
for k in ('resolve_hypotheses_by_core','rank_hypotheses_by_core','declare_winner_by_core','certify_validity_by_core','certify_replication_by_core','infer_contradiction_by_core','infer_counterevidence_by_core','execute_sensitivity_by_core','execute_robustness_by_core','execute_replication_by_core','dismiss_challenges_by_core','determine_truth_by_core'): assert r.get(k) is False,(k,r)
print('PASS - Platform Core v2.94.0 Research Validation & Challenge Engine')
PY2
curl -fsS https://core.sustainablecatalyst.com/health | python3 -m json.tool
echo "PASS - PLATFORM CORE v2.94.0 BACKEND DEPLOYMENT COMPLETE"
