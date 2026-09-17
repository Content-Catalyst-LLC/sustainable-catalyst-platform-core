#!/usr/bin/env bash
set -euo pipefail
trap 'rc=$?; echo "ERROR: v2.69.0 deployment stopped at line $LINENO (exit $rc): $BASH_COMMAND" >&2; exit $rc' ERR
ROOT="${SC_CORE_ROOT:-/opt/sustainable-catalyst/core}"; COMPOSE="docker compose -f compose.yml -f compose.vps.yml"; cd "$ROOT"
echo "=== PLATFORM CORE v2.69.0 — VISUAL DECISION INTELLIGENCE ==="
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
[ "$(psqlq "SELECT EXISTS (SELECT 1 FROM schema_migrations WHERE version='0072');")" = t ] || { echo "STOP: migration 0072 missing; deploy v2.68.0 first"; exit 1; }
V268_TABLES=(visual_forensic_workspaces visual_forensic_evidence_bindings visual_forensic_claim_overlays visual_forensic_timeline_layers visual_forensic_spatial_temporal_layers visual_forensic_media_layers visual_forensic_reconstruction_bindings visual_forensic_documentary_bindings visual_forensic_graph_bindings visual_forensic_snapshots)
for t in "${V268_TABLES[@]}"; do [ "$(psqlq "SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema='public' AND table_name='$t');")" = t ] || { echo "STOP: predecessor table missing: $t"; exit 1; }; done
V269_TABLES=(visual_decision_workspaces visual_decision_alternatives visual_decision_criteria visual_decision_evidence_bindings visual_decision_scenario_bindings visual_decision_risk_overlays visual_decision_tradeoffs visual_decision_rationales visual_decision_handoffs visual_decision_snapshots)
count=0; for t in "${V269_TABLES[@]}"; do [ "$(psqlq "SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema='public' AND table_name='$t');")" = t ] && count=$((count+1)); done
m73="$(psqlq "SELECT EXISTS (SELECT 1 FROM schema_migrations WHERE version='0073');")"
if [ "$m73" = f ] && [ "$count" -eq 0 ]; then echo "PASS: pristine pre-0073 state"; elif [ "$m73" = f ] && [ "$count" -eq 10 ]; then echo "PASS: recoverable partial-0073 state"; elif [ "$m73" = t ] && [ "$count" -eq 10 ]; then echo "PASS: already-complete 0073 state"; else echo "STOP: inconsistent 0073 state ($m73, $count/10)"; exit 1; fi
echo "=== BACKUP ==="; mkdir -p /opt/sustainable-catalyst/backups/platform-core-v2690; stamp="$(date +%Y%m%d-%H%M%S)"; docker exec -e PGPASSWORD="$DB_PASS" sc-postgres pg_dump -h 127.0.0.1 -U "$DB_USER" -d "$DB_NAME" -Fc > "/opt/sustainable-catalyst/backups/platform-core-v2690/core-${stamp}.dump"; git rev-parse HEAD > "/opt/sustainable-catalyst/backups/platform-core-v2690/git-head-${stamp}.txt"
git fetch origin --tags; git pull --ff-only origin main; git tag --points-at HEAD | grep -qx 'v2.69.0' || { echo "STOP: production HEAD is not tagged v2.69.0"; exit 1; }
python3 -S scripts/validate_v2690_release.py
$COMPOSE build core
$COMPOSE run --rm --no-deps core python scripts/migrate.py | tee /tmp/sc-core-v2690-migrate.json
for t in "${V269_TABLES[@]}"; do [ "$(psqlq "SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema='public' AND table_name='$t');")" = t ] || { echo "STOP: $t missing after migration"; exit 1; }; done
[ "$(psqlq "SELECT EXISTS (SELECT 1 FROM schema_migrations WHERE version='0073');")" = t ] || { echo "STOP: migration 0073 not recorded"; exit 1; }
$COMPOSE up -d --no-deps --force-recreate core
for i in $(seq 1 40); do curl -fsS http://127.0.0.1:8090/health >/tmp/sc-core-v2690-health.json 2>/dev/null && break; sleep 2; done
curl -fsS http://127.0.0.1:8090/v1/visual-runtime/decision/readiness | tee /tmp/sc-core-v2690-visual.json | python3 -m json.tool
python3 - <<'PY2'
import json
h=json.load(open('/tmp/sc-core-v2690-health.json'));r=json.load(open('/tmp/sc-core-v2690-visual.json'));assert h.get('ok') is True and h.get('version')=='2.69.0',h;assert r.get('release')=='2.69.0' and r.get('migration_0073_applied') is True,r
for k in ('visual_decision_workspace_registry_by_core','visual_decision_alternative_registry_by_core','visual_decision_criterion_registry_by_core','visual_decision_evidence_registry_by_core','visual_decision_scenario_registry_by_core','visual_decision_risk_registry_by_core','visual_decision_tradeoff_registry_by_core','visual_decision_rationale_registry_by_core','visual_decision_handoff_registry_by_core','immutable_visual_decision_snapshots_by_core'):assert r.get(k) is True,(k,r)
for k in ('utility_computation_by_core','option_ranking_by_core','recommendation_generation_by_core','objective_optimization_by_core','policy_selection_by_core','decision_execution_by_core','automatic_visual_inference'):assert r.get(k) is False,(k,r)
print('PASS - Platform Core v2.69.0 Visual Decision Intelligence')
PY2
curl -fsS https://core.sustainablecatalyst.com/health | python3 -m json.tool
echo "PASS - PLATFORM CORE v2.69.0 BACKEND DEPLOYMENT COMPLETE"
