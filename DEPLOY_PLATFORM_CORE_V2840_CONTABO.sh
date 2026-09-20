#!/usr/bin/env bash
set -euo pipefail
trap 'rc=$?; echo "ERROR: v2.84.0 deployment stopped at line $LINENO (exit $rc): $BASH_COMMAND" >&2; exit $rc' ERR
ROOT="${SC_CORE_ROOT:-/opt/sustainable-catalyst/core}"; COMPOSE="docker compose -f compose.yml -f compose.vps.yml"; cd "$ROOT"
echo "=== PLATFORM CORE v2.84.0 — RESEARCH PROGRAM & LONGITUDINAL KNOWLEDGE GRAPH ==="
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
[ "$(psqlq "SELECT EXISTS (SELECT 1 FROM schema_migrations WHERE version='0087');")" = t ] || { echo "STOP: migration 0087 missing; deploy v2.83.0 first"; exit 1; }
V283_TABLES=(research_evidence_syntheses_v283 research_synthesis_studies_v283 research_synthesis_outcomes_v283 research_synthesis_effects_v283 research_meta_analyses_v283 research_meta_research_assessments_v283 research_synthesis_relations_v283 research_evidence_gaps_v283 research_evidence_synthesis_revisions_v283 research_evidence_synthesis_snapshots_v283)
for t in "${V283_TABLES[@]}"; do [ "$(psqlq "SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema='public' AND table_name='$t');")" = t ] || { echo "STOP: predecessor table missing: $t"; exit 1; }; done
V284_TABLES=(research_programs_v284 research_program_projects_v284 research_program_objectives_v284 research_program_milestones_v284 research_longitudinal_nodes_v284 research_longitudinal_edges_v284 research_knowledge_states_v284 research_evolution_events_v284 research_program_revisions_v284 research_program_snapshots_v284)
count=0; for t in "${V284_TABLES[@]}"; do [ "$(psqlq "SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema='public' AND table_name='$t');")" = t ] && count=$((count+1)); done
m88="$(psqlq "SELECT EXISTS (SELECT 1 FROM schema_migrations WHERE version='0088');")"
if [ "$m88" = f ] && [ "$count" -eq 0 ]; then echo "PASS: pristine pre-0088 state"; elif [ "$m88" = f ] && [ "$count" -eq 10 ]; then echo "PASS: recoverable partial-0088 state"; elif [ "$m88" = t ] && [ "$count" -eq 10 ]; then echo "PASS: already-complete 0088 state"; else echo "STOP: inconsistent 0088 state ($m88, $count/10)"; exit 1; fi
echo "=== BACKUP ==="; BACKUP_DIR="/opt/sustainable-catalyst/backups/platform-core-v2840"; mkdir -p "$BACKUP_DIR"; stamp="$(date +%Y%m%d-%H%M%S)"; docker exec -e PGPASSWORD="$DB_PASS" sc-postgres pg_dump -h 127.0.0.1 -U "$DB_USER" -d "$DB_NAME" -Fc > "$BACKUP_DIR/core-${stamp}.dump"; git rev-parse HEAD > "$BACKUP_DIR/git-head-${stamp}.txt"; tar --exclude='.git' --exclude='backend/.venv' -czf "$BACKUP_DIR/core-source-${stamp}.tar.gz" .
echo "=== PROMOTE TAGGED SOURCE ==="; git fetch origin --tags; git pull --ff-only origin main; git tag --points-at HEAD | grep -qx 'v2.84.0' || { echo "STOP: production HEAD is not tagged v2.84.0"; exit 1; }; python3 -S scripts/validate_v2840_release.py
echo "=== BUILD / MIGRATE ==="; $COMPOSE build core; $COMPOSE run --rm --no-deps core python scripts/migrate.py | tee /tmp/sc-core-v2840-migrate.json
for t in "${V284_TABLES[@]}"; do [ "$(psqlq "SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema='public' AND table_name='$t');")" = t ] || { echo "STOP: $t missing after migration"; exit 1; }; done
[ "$(psqlq "SELECT EXISTS (SELECT 1 FROM schema_migrations WHERE version='0088');")" = t ] || { echo "STOP: migration 0088 not recorded"; exit 1; }
$COMPOSE up -d --no-deps --force-recreate core
for i in $(seq 1 40); do curl -fsS http://127.0.0.1:8090/health >/tmp/sc-core-v2840-health.json 2>/dev/null && break; sleep 2; done
curl -fsS http://127.0.0.1:8090/v1/research/programs/readiness | tee /tmp/sc-core-v2840-program.json | python3 -m json.tool
python3 - <<'PY2'
import json
h=json.load(open('/tmp/sc-core-v2840-health.json')); r=json.load(open('/tmp/sc-core-v2840-program.json'))
assert h.get('ok') is True and h.get('version')=='2.84.0',h; assert r.get('release')=='2.84.0' and r.get('migration_0088_applied') is True,r
for k in ('research_program_registry_by_core','program_project_membership_registry_by_core','program_objective_registry_by_core','program_milestone_registry_by_core','longitudinal_knowledge_node_registry_by_core','declared_longitudinal_edge_registry_by_core','knowledge_state_history_by_core','research_evolution_event_registry_by_core','descriptive_longitudinal_timeline_by_core','program_revision_history_by_core','program_lineage_by_core','immutable_program_snapshots_by_core'): assert r.get(k) is True,(k,r)
for k in ('prioritize_research_by_core','allocate_funding_by_core','rank_projects_by_core','auto_link_knowledge_graph_by_core','infer_research_direction_by_core','infer_causality_by_core','forecast_program_success_by_core','resolve_evidence_gaps_by_core','infer_knowledge_truth_by_core','infer_truth_by_core'): assert r.get(k) is False,(k,r)
print('PASS - Platform Core v2.84.0 Research Program & Longitudinal Knowledge Graph')
PY2
curl -fsS https://core.sustainablecatalyst.com/health | python3 -m json.tool
echo "PASS - PLATFORM CORE v2.84.0 BACKEND DEPLOYMENT COMPLETE"
