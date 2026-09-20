#!/usr/bin/env bash
set -euo pipefail
trap 'rc=$?; echo "ERROR: v2.85.0 deployment stopped at line $LINENO (exit $rc): $BASH_COMMAND" >&2; exit $rc' ERR
ROOT="${SC_CORE_ROOT:-/opt/sustainable-catalyst/core}"; COMPOSE="docker compose -f compose.yml -f compose.vps.yml"; cd "$ROOT"
echo "=== PLATFORM CORE v2.85.0 — RESEARCH PORTFOLIO & INSTITUTIONAL KNOWLEDGE GOVERNANCE ==="
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
[ "$(psqlq "SELECT EXISTS (SELECT 1 FROM schema_migrations WHERE version='0088');")" = t ] || { echo "STOP: migration 0088 missing; deploy v2.84.0 first"; exit 1; }
V284_TABLES=(research_programs_v284 research_program_projects_v284 research_program_objectives_v284 research_program_milestones_v284 research_longitudinal_nodes_v284 research_longitudinal_edges_v284 research_knowledge_states_v284 research_evolution_events_v284 research_program_revisions_v284 research_program_snapshots_v284)
for t in "${V284_TABLES[@]}"; do [ "$(psqlq "SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema='public' AND table_name='$t');")" = t ] || { echo "STOP: predecessor table missing: $t"; exit 1; }; done
V285_TABLES=(research_portfolios_v285 research_portfolio_programs_v285 research_portfolio_themes_v285 research_portfolio_objectives_v285 research_portfolio_dependencies_v285 research_portfolio_resource_envelopes_v285 research_portfolio_risks_v285 research_portfolio_reviews_v285 research_portfolio_decisions_v285 research_portfolio_revisions_v285 research_portfolio_snapshots_v285)
count=0; for t in "${V285_TABLES[@]}"; do [ "$(psqlq "SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema='public' AND table_name='$t');")" = t ] && count=$((count+1)); done
m89="$(psqlq "SELECT EXISTS (SELECT 1 FROM schema_migrations WHERE version='0089');")"
if [ "$m89" = f ] && [ "$count" -eq 0 ]; then echo "PASS: pristine pre-0089 state"; elif [ "$m89" = f ] && [ "$count" -eq 11 ]; then echo "PASS: recoverable partial-0089 state"; elif [ "$m89" = t ] && [ "$count" -eq 11 ]; then echo "PASS: already-complete 0089 state"; else echo "STOP: inconsistent 0089 state ($m89, $count/11)"; exit 1; fi
echo "=== BACKUP ==="; BACKUP_DIR="/opt/sustainable-catalyst/backups/platform-core-v2850"; mkdir -p "$BACKUP_DIR"; stamp="$(date +%Y%m%d-%H%M%S)"; docker exec -e PGPASSWORD="$DB_PASS" sc-postgres pg_dump -h 127.0.0.1 -U "$DB_USER" -d "$DB_NAME" -Fc > "$BACKUP_DIR/core-${stamp}.dump"; git rev-parse HEAD > "$BACKUP_DIR/git-head-${stamp}.txt"; tar --exclude='.git' --exclude='backend/.venv' -czf "$BACKUP_DIR/core-source-${stamp}.tar.gz" .
echo "=== PROMOTE TAGGED SOURCE ==="; git fetch origin --tags; git pull --ff-only origin main; git tag --points-at HEAD | grep -qx 'v2.85.0' || { echo "STOP: production HEAD is not tagged v2.85.0"; exit 1; }; python3 -S scripts/validate_v2850_release.py
echo "=== BUILD / MIGRATE ==="; $COMPOSE build core; $COMPOSE run --rm --no-deps core python scripts/migrate.py | tee /tmp/sc-core-v2850-migrate.json
for t in "${V285_TABLES[@]}"; do [ "$(psqlq "SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema='public' AND table_name='$t');")" = t ] || { echo "STOP: $t missing after migration"; exit 1; }; done
[ "$(psqlq "SELECT EXISTS (SELECT 1 FROM schema_migrations WHERE version='0089');")" = t ] || { echo "STOP: migration 0089 not recorded"; exit 1; }
$COMPOSE up -d --no-deps --force-recreate core
for i in $(seq 1 40); do curl -fsS http://127.0.0.1:8090/health >/tmp/sc-core-v2850-health.json 2>/dev/null && break; sleep 2; done
curl -fsS http://127.0.0.1:8090/v1/research/portfolios/readiness | tee /tmp/sc-core-v2850-portfolio.json | python3 -m json.tool
python3 - <<'PY2'
import json
h=json.load(open('/tmp/sc-core-v2850-health.json')); r=json.load(open('/tmp/sc-core-v2850-portfolio.json'))
assert h.get('ok') is True and h.get('version')=='2.85.0',h; assert r.get('release')=='2.85.0' and r.get('migration_0089_applied') is True,r
for k in ('research_portfolio_registry_by_core','portfolio_program_membership_registry_by_core','portfolio_theme_registry_by_core','portfolio_objective_registry_by_core','declared_program_dependency_registry_by_core','declared_resource_envelope_registry_by_core','portfolio_risk_registry_by_core','portfolio_review_registry_by_core','researcher_authored_governance_decision_registry_by_core','descriptive_portfolio_map_by_core','portfolio_revision_history_by_core','portfolio_lineage_by_core','immutable_portfolio_snapshots_by_core'): assert r.get(k) is True,(k,r)
for k in ('prioritize_programs_by_core','allocate_resources_by_core','allocate_funding_by_core','rank_programs_by_core','score_programs_by_core','optimize_portfolio_by_core','decide_governance_by_core','infer_strategic_value_by_core','forecast_program_success_by_core','close_risks_by_core','infer_truth_by_core'): assert r.get(k) is False,(k,r)
print('PASS - Platform Core v2.85.0 Research Portfolio & Institutional Knowledge Governance')
PY2
curl -fsS https://core.sustainablecatalyst.com/health | python3 -m json.tool
echo "PASS - PLATFORM CORE v2.85.0 BACKEND DEPLOYMENT COMPLETE"
