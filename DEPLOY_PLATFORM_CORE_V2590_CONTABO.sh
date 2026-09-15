#!/usr/bin/env bash
set -euo pipefail
trap 'rc=$?; echo "ERROR: v2.59.0 deployment stopped at line $LINENO (exit $rc): $BASH_COMMAND" >&2; exit $rc' ERR
ROOT="${SC_CORE_ROOT:-/opt/sustainable-catalyst/core}"; BACKUP_ROOT="${SC_CORE_BACKUP_ROOT:-/opt/sustainable-catalyst/backups}"; COMPOSE="docker compose -f compose.yml -f compose.vps.yml"; STAMP="$(date +%Y%m%d-%H%M%S)"; BACKUP="${BACKUP_ROOT}/platform-core-v2.59.0-${STAMP}"
cd "$ROOT"
echo "============================================================"; echo " PLATFORM CORE v2.59.0 — PREDICTIVE DECISION INTELLIGENCE"; echo "============================================================"
echo; echo "=== CURRENT LIVE HEALTH ==="; curl -fsS http://127.0.0.1:8090/health | python3 -m json.tool
echo; echo "=== SAFETY CHECKS ==="; [ -f compose.yml ] || { echo "STOP: compose.yml missing"; exit 1; }; [ -f compose.vps.yml ] || { echo "STOP: compose.vps.yml missing"; exit 1; }; [ -f .env.production ] || { echo "STOP: .env.production missing"; exit 1; }
if ! git diff --quiet || ! git diff --cached --quiet; then echo "STOP: tracked production files have local changes."; git status --short; exit 1; fi
$COMPOSE config >/tmp/sc-core-v2590-compose.yml; grep -q '/data/scientific-objects' /tmp/sc-core-v2590-compose.yml || { echo "STOP: scientific-object persistent mount missing"; exit 1; }
CORE_DB_URL="$(grep -m1 '^SC_CORE_DATABASE_URL=' .env.production | cut -d= -f2-)"; [ -n "$CORE_DB_URL" ] || { echo "STOP: SC_CORE_DATABASE_URL not found"; exit 1; }
eval "$(CORE_DB_URL="$CORE_DB_URL" python3 - <<'PY2'
import os,shlex
from urllib.parse import urlparse,unquote
u=urlparse(os.environ['CORE_DB_URL'].strip().strip('"').strip("'")); print('DB_USER='+shlex.quote(unquote(u.username or ''))); print('DB_PASS='+shlex.quote(unquote(u.password or ''))); print('DB_NAME='+shlex.quote((u.path or '').lstrip('/')))
PY2
)"
psqlq(){ docker exec -e PGPASSWORD="$DB_PASS" sc-postgres psql -h 127.0.0.1 -U "$DB_USER" -d "$DB_NAME" -Atqc "$1"; }
echo; echo "=== PRODUCTION PREDECESSOR PREFLIGHT ==="
M62="$(psqlq "SELECT EXISTS (SELECT 1 FROM schema_migrations WHERE version='0062');")"; echo "schema_migrations.0062=$M62"; [ "$M62" = t ] || { echo "STOP: migration 0062 is not recorded; v2.58.0 must be deployed first"; exit 1; }
V258_TABLES=(predictive_causal_studies predictive_causal_variable_bindings predictive_intervention_scenarios predictive_counterfactual_forecasts predictive_causal_effect_evidence predictive_causal_evaluations predictive_causal_handoffs predictive_causal_packages)
for t in "${V258_TABLES[@]}"; do v="$(psqlq "SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema='public' AND table_name='$t');")"; echo "$t=$v"; [ "$v" = t ] || { echo "STOP: predecessor v2.58 table missing: $t"; exit 1; }; done
V259_TABLES=(predictive_decision_studies predictive_decision_options predictive_decision_criteria predictive_decision_evidence_bindings predictive_decision_scenario_assessments predictive_decision_evaluations predictive_decision_handoffs predictive_decision_packages)
v259_count=0
for t in "${V259_TABLES[@]}"; do v="$(psqlq "SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema='public' AND table_name='$t');")"; echo "$t=$v"; [ "$v" = t ] && v259_count=$((v259_count+1)); done
M63="$(psqlq "SELECT EXISTS (SELECT 1 FROM schema_migrations WHERE version='0063');")"; echo "schema_migrations.0063=$M63"; echo "decision_tables_present=$v259_count/8"
if [ "$M63" = f ] && [ "$v259_count" -eq 0 ]; then echo "PASS: pristine pre-0063 predictive-decision state accepted"; elif [ "$M63" = f ] && [ "$v259_count" -eq 8 ]; then echo "PASS: safe partial-0063 table state detected and accepted"; elif [ "$M63" = t ] && [ "$v259_count" -eq 8 ]; then echo "PASS: migration 0063 already recorded with complete predictive-decision schema"; else echo "STOP: inconsistent predictive-decision migration state (0063=$M63, tables=$v259_count/8)"; exit 1; fi
echo; echo "=== BACKUP CURRENT CORE + DATABASE ==="; mkdir -p "$BACKUP"; tar --exclude='.git' -czf "$BACKUP/core-before-v2.59.0.tar.gz" .; docker exec -e PGPASSWORD="$DB_PASS" sc-postgres pg_dump -h 127.0.0.1 -U "$DB_USER" -d "$DB_NAME" -Fc > "$BACKUP/platform-core-before-v2.59.0.dump"; ls -lh "$BACKUP"/*
echo; echo "=== FETCH EXACT v2.59.0 RELEASE ==="; git fetch origin --tags; git rev-parse v2.59.0 >/dev/null 2>&1 || { echo "STOP: v2.59.0 tag is not available from GitHub"; exit 1; }; git pull --ff-only origin main; echo "HEAD: $(git log -1 --oneline)"; git tag --points-at HEAD | grep -qx 'v2.59.0' || { echo "STOP: production HEAD is not exactly tagged v2.59.0"; exit 1; }
head_commit="$(git rev-parse HEAD)"; tag_commit="$(git rev-list -n 1 v2.59.0)"; [ "$head_commit" = "$tag_commit" ] || { echo "STOP: v2.59.0 does not resolve to production HEAD"; exit 1; }
python3 -S scripts/validate_v2590_release.py
echo; echo "=== BUILD CORE v2.59.0 ==="; $COMPOSE build core
echo; echo "=== APPLY / REPAIR MIGRATION 0063 ==="; $COMPOSE run --rm --no-deps core python scripts/migrate.py | tee /tmp/sc-core-v2590-migrations.json
echo; echo "=== VERIFY DATABASE CONTRACT BEFORE RECREATE ==="
for t in "${V259_TABLES[@]}"; do [ "$(psqlq "SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema='public' AND table_name='$t');")" = t ] || { echo "STOP: $t missing after migration 0063"; exit 1; }; done
M63_POST="$(psqlq "SELECT EXISTS (SELECT 1 FROM schema_migrations WHERE version='0063');")"; [ "$M63_POST" = t ] || { echo "STOP: migration 0063 not recorded"; exit 1; }; D63_LEN="$(psqlq "SELECT length(description) FROM schema_migrations WHERE version='0063';")"; echo "schema_migrations.0063.description_length=$D63_LEN"; [ "$D63_LEN" -le 300 ] || { echo "STOP: stored 0063 description exceeds production contract"; exit 1; }
echo "PASS: migration 0063 complete; v2.58 causal-predictive schema preserved"
echo; echo "=== RECREATE sc-core ==="; $COMPOSE up -d --no-deps --force-recreate core
for i in $(seq 1 40); do if curl -fsS http://127.0.0.1:8090/health >/tmp/sc-core-v2590-health.json 2>/dev/null; then break; fi; [ "$i" -lt 40 ] || { docker logs --tail 200 sc-core; exit 1; }; sleep 2; done
for i in $(seq 1 40); do state="$(docker inspect --format '{{if .State.Health}}{{.State.Health.Status}}{{else}}none{{end}}' sc-core)"; echo "health=$state"; [ "$state" = healthy ] && break; [ "$state" != unhealthy ] || { docker logs --tail 200 sc-core; exit 1; }; [ "$i" -lt 40 ] || { docker logs --tail 200 sc-core; exit 1; }; sleep 2; done
echo; echo "=== LIVE HEALTH ==="; python3 -m json.tool </tmp/sc-core-v2590-health.json
echo; echo "=== PREDICTIVE INTELLIGENCE READINESS ==="; curl -fsS http://127.0.0.1:8090/v1/predictive-intelligence/readiness | tee /tmp/sc-core-v2590-predictive.json | python3 -m json.tool
python3 - <<'PY2'
import json
h=json.load(open('/tmp/sc-core-v2590-health.json')); r=json.load(open('/tmp/sc-core-v2590-predictive.json'))
assert h.get('ok') is True and h.get('version')=='2.59.0',h
assert h.get('predictive_causal_predictive_integration') is True and h.get('predictive_decision_intelligence') is True,h
assert r.get('release')=='2.59.0' and r.get('migration_0062_applied') is True and r.get('migration_0063_applied') is True,r
for key in ('predictive_decision_study_registry_by_core','decision_option_registry_by_core','decision_criterion_registry_by_core','decision_evidence_binding_registry_by_core','decision_scenario_assessment_registry_by_core','decision_evaluation_evidence_registry_by_core','decision_handoff_registry_by_core','reproducible_predictive_decision_packages_by_core'): assert r.get(key) is True,(key,r)
for key in ('decision_ranking_by_core','decision_recommendation_by_core','decision_optimization_by_core','utility_computation_by_core','regret_computation_by_core','constraint_solving_by_core','decision_action_execution_by_core','automatic_action_selection','automatic_intervention_by_core','automatic_truth_promotion'): assert r.get(key) is False,(key,r)
print('PASS: Platform Core v2.59.0'); print('PASS: Predictive Decision Intelligence'); print('PASS: migration 0063 additive with non-optimization/non-autonomy boundaries intact')
PY2
echo; echo "=== VERIFY MIGRATION STATE ==="; docker exec sc-core python scripts/migrate.py | tee /tmp/sc-core-v2590-migration-state.json
python3 - <<'PY2'
import json
m=json.load(open('/tmp/sc-core-v2590-migration-state.json')); assert '0063' in m.get('applied',[]) and m.get('pending')==[],m; print('PASS: migration 0063 applied and pending=[]')
PY2
echo; echo "=== PERSISTENT SCIENTIFIC STORAGE ==="; docker exec sc-core sh -lc 'test -d /data/scientific-objects; touch /data/scientific-objects/.v2590-write-test; rm /data/scientific-objects/.v2590-write-test; echo "PASS: persistent scientific-object storage writable"'
echo; echo "=== PUBLIC CADDY ROUTE ==="; curl -fsS https://core.sustainablecatalyst.com/health | python3 -c 'import json,sys;d=json.load(sys.stdin);assert d.get("version")=="2.59.0",d;print("PASS: public Core health 2.59.0")'; curl -fsS https://core.sustainablecatalyst.com/v1/predictive-intelligence/readiness | python3 -c 'import json,sys;d=json.load(sys.stdin);assert d.get("release")=="2.59.0" and d.get("migration_0063_applied") is True,d;print("PASS: public Predictive Decision Intelligence readiness")'
echo; echo "=== FINAL CONTAINER ==="; docker ps --filter name=sc-core --format 'table {{.Names}}\t{{.Image}}\t{{.Status}}\t{{.Ports}}'
echo "Backup retained at: $BACKUP"
echo "============================================================"; echo " PLATFORM CORE v2.59.0 BACKEND DEPLOYMENT COMPLETE"; echo "============================================================"
