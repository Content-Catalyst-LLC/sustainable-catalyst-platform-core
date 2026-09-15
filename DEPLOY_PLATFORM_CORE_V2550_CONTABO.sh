#!/usr/bin/env bash
set -euo pipefail
trap 'rc=$?; echo "ERROR: v2.55.0 deployment stopped at line $LINENO (exit $rc): $BASH_COMMAND" >&2; exit $rc' ERR
ROOT="${SC_CORE_ROOT:-/opt/sustainable-catalyst/core}"
BACKUP_ROOT="${SC_CORE_BACKUP_ROOT:-/opt/sustainable-catalyst/backups}"
COMPOSE="docker compose -f compose.yml -f compose.vps.yml"
STAMP="$(date +%Y%m%d-%H%M%S)"; BACKUP="${BACKUP_ROOT}/platform-core-v2.55.0-${STAMP}"
cd "$ROOT"
echo "============================================================"; echo " PLATFORM CORE v2.55.0 — PREDICTIVE ENSEMBLES & MODEL COMPARISON"; echo "============================================================"
echo; echo "=== CURRENT LIVE HEALTH ==="; curl -fsS http://127.0.0.1:8090/health | python3 -m json.tool
echo; echo "=== SAFETY CHECKS ==="; [ -f compose.yml ] || { echo "STOP: compose.yml missing"; exit 1; }; [ -f compose.vps.yml ] || { echo "STOP: compose.vps.yml missing"; exit 1; }; [ -f .env.production ] || { echo "STOP: .env.production missing"; exit 1; }
if ! git diff --quiet || ! git diff --cached --quiet; then echo "STOP: tracked production files have local changes."; git status --short; exit 1; fi
$COMPOSE config >/tmp/sc-core-v2550-compose.yml; grep -q '/data/scientific-objects' /tmp/sc-core-v2550-compose.yml || { echo "STOP: scientific-object persistent mount missing"; exit 1; }
CORE_DB_URL="$(grep -m1 '^SC_CORE_DATABASE_URL=' .env.production | cut -d= -f2-)"; [ -n "$CORE_DB_URL" ] || { echo "STOP: SC_CORE_DATABASE_URL not found"; exit 1; }
eval "$(CORE_DB_URL="$CORE_DB_URL" python3 - <<'PY2'
import os,shlex
from urllib.parse import urlparse,unquote
u=urlparse(os.environ['CORE_DB_URL'].strip().strip('"').strip("'")); print('DB_USER='+shlex.quote(unquote(u.username or ''))); print('DB_PASS='+shlex.quote(unquote(u.password or ''))); print('DB_NAME='+shlex.quote((u.path or '').lstrip('/')))
PY2
)"
psqlq(){ docker exec -e PGPASSWORD="$DB_PASS" sc-postgres psql -h 127.0.0.1 -U "$DB_USER" -d "$DB_NAME" -Atqc "$1"; }
echo; echo "=== PRODUCTION PREDECESSOR PREFLIGHT ==="
M58="$(psqlq "SELECT EXISTS (SELECT 1 FROM schema_migrations WHERE version='0058');")"; echo "schema_migrations.0058=$M58"; [ "$M58" = t ] || { echo "STOP: migration 0058 is not recorded; v2.54.0 must be deployed first"; exit 1; }
V254_TABLES=(predictive_probabilistic_forecasts predictive_calibration_studies predictive_calibration_bins predictive_calibration_mappings predictive_probabilistic_evaluations predictive_calibration_packages)
for t in "${V254_TABLES[@]}"; do v="$(psqlq "SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema='public' AND table_name='$t');")"; echo "$t=$v"; [ "$v" = t ] || { echo "STOP: predecessor v2.54 table missing: $t"; exit 1; }; done
V255_TABLES=(predictive_ensembles predictive_ensemble_members predictive_ensemble_forecasts predictive_comparison_studies predictive_comparison_candidates predictive_comparison_evidence predictive_pairwise_comparisons predictive_comparison_packages)
v255_count=0
for t in "${V255_TABLES[@]}"; do v="$(psqlq "SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema='public' AND table_name='$t');")"; echo "$t=$v"; [ "$v" = t ] && v255_count=$((v255_count+1)); done
M59="$(psqlq "SELECT EXISTS (SELECT 1 FROM schema_migrations WHERE version='0059');")"; echo "schema_migrations.0059=$M59"; echo "ensemble_comparison_tables_present=$v255_count/8"
if [ "$M59" = f ] && [ "$v255_count" -eq 0 ]; then echo "PASS: pristine pre-0059 ensemble/comparison state accepted";
elif [ "$M59" = f ] && [ "$v255_count" -eq 8 ]; then echo "PASS: safe partial-0059 ensemble/comparison table state detected and accepted";
elif [ "$M59" = t ] && [ "$v255_count" -eq 8 ]; then echo "PASS: migration 0059 already recorded with complete ensemble/comparison schema";
else echo "STOP: inconsistent ensemble/comparison migration state (0059=$M59, tables=$v255_count/8)"; exit 1; fi
echo; echo "=== BACKUP CURRENT CORE + DATABASE ==="; mkdir -p "$BACKUP"; tar --exclude='.git' -czf "$BACKUP/core-before-v2.55.0.tar.gz" .; docker exec -e PGPASSWORD="$DB_PASS" sc-postgres pg_dump -h 127.0.0.1 -U "$DB_USER" -d "$DB_NAME" -Fc > "$BACKUP/platform-core-before-v2.55.0.dump"; ls -lh "$BACKUP"/*
echo; echo "=== FETCH EXACT v2.55.0 RELEASE ==="; git fetch origin --tags; git rev-parse v2.55.0 >/dev/null 2>&1 || { echo "STOP: v2.55.0 tag is not available from GitHub"; exit 1; }; git pull --ff-only origin main; echo "HEAD: $(git log -1 --oneline)"; git tag --points-at HEAD | grep -qx 'v2.55.0' || { echo "STOP: production HEAD is not exactly tagged v2.55.0"; exit 1; }
head_commit="$(git rev-parse HEAD)"; tag_commit="$(git rev-list -n 1 v2.55.0)"; [ "$head_commit" = "$tag_commit" ] || { echo "STOP: v2.55.0 does not resolve to production HEAD"; exit 1; }
python3 -S scripts/validate_v2550_release.py
echo; echo "=== BUILD CORE v2.55.0 ==="; $COMPOSE build core
echo; echo "=== APPLY / REPAIR MIGRATION 0059 ==="; $COMPOSE run --rm --no-deps core python scripts/migrate.py | tee /tmp/sc-core-v2550-migrations.json
echo; echo "=== VERIFY DATABASE CONTRACT BEFORE RECREATE ==="
for t in "${V255_TABLES[@]}"; do [ "$(psqlq "SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema='public' AND table_name='$t');")" = t ] || { echo "STOP: $t missing after migration 0059"; exit 1; }; done
M59_POST="$(psqlq "SELECT EXISTS (SELECT 1 FROM schema_migrations WHERE version='0059');")"; [ "$M59_POST" = t ] || { echo "STOP: migration 0059 not recorded"; exit 1; }; D59_LEN="$(psqlq "SELECT length(description) FROM schema_migrations WHERE version='0059';")"; echo "schema_migrations.0059.description_length=$D59_LEN"; [ "$D59_LEN" -le 300 ] || { echo "STOP: stored 0059 description exceeds production contract"; exit 1; }
echo "PASS: migration 0059 complete; v2.54 probabilistic/calibration schema preserved"
echo; echo "=== RECREATE sc-core ==="; $COMPOSE up -d --no-deps --force-recreate core
for i in $(seq 1 40); do if curl -fsS http://127.0.0.1:8090/health >/tmp/sc-core-v2550-health.json 2>/dev/null; then break; fi; [ "$i" -lt 40 ] || { docker logs --tail 200 sc-core; exit 1; }; sleep 2; done
for i in $(seq 1 40); do state="$(docker inspect --format '{{if .State.Health}}{{.State.Health.Status}}{{else}}none{{end}}' sc-core)"; echo "health=$state"; [ "$state" = healthy ] && break; [ "$state" != unhealthy ] || { docker logs --tail 200 sc-core; exit 1; }; [ "$i" -lt 40 ] || { docker logs --tail 200 sc-core; exit 1; }; sleep 2; done
echo; echo "=== LIVE HEALTH ==="; python3 -m json.tool </tmp/sc-core-v2550-health.json
echo; echo "=== PREDICTIVE INTELLIGENCE READINESS ==="; curl -fsS http://127.0.0.1:8090/v1/predictive-intelligence/readiness | tee /tmp/sc-core-v2550-predictive.json | python3 -m json.tool
python3 - <<'PY2'
import json
h=json.load(open('/tmp/sc-core-v2550-health.json')); r=json.load(open('/tmp/sc-core-v2550-predictive.json'))
assert h.get('ok') is True and h.get('version')=='2.55.0',h
assert h.get('predictive_model_object_model_forecast_provenance') is True and h.get('predictive_time_series_forecasting_backtesting') is True and h.get('predictive_probabilistic_forecasting_calibration') is True and h.get('predictive_ensembles_model_comparison') is True,h
assert r.get('release')=='2.55.0' and r.get('migration_0058_applied') is True and r.get('migration_0059_applied') is True,r
for key in ('ensemble_registry_by_core','ensemble_member_registry_by_core','ensemble_forecast_provenance_by_core','model_comparison_study_registry_by_core','comparison_candidate_registry_by_core','comparative_metric_evidence_by_core','pairwise_comparison_evidence_by_core','reproducible_model_comparison_packages_by_core'): assert r.get(key) is True,(key,r)
for key in ('model_fitting_by_core','ensemble_construction_by_core','ensemble_weight_optimization_by_core','ensemble_forecast_execution_by_core','model_comparison_metric_computation_by_core','statistical_significance_computation_by_core','model_ranking_by_core','automatic_model_selection','automatic_truth_promotion'): assert r.get(key) is False,(key,r)
print('PASS: Platform Core v2.55.0'); print('PASS: Predictive Ensembles & Model Comparison'); print('PASS: migration 0059 additive with external-compute/non-ranking/non-selection boundaries intact')
PY2
echo; echo "=== VERIFY MIGRATION STATE ==="; docker exec sc-core python scripts/migrate.py | tee /tmp/sc-core-v2550-migration-state.json
python3 - <<'PY2'
import json
m=json.load(open('/tmp/sc-core-v2550-migration-state.json')); assert '0059' in m.get('applied',[]) and m.get('pending')==[],m; print('PASS: migration 0059 applied and pending=[]')
PY2
echo; echo "=== PERSISTENT SCIENTIFIC STORAGE ==="; docker exec sc-core sh -lc 'test -d /data/scientific-objects; touch /data/scientific-objects/.v2550-write-test; rm /data/scientific-objects/.v2550-write-test; echo "PASS: persistent scientific-object storage writable"'
echo; echo "=== PUBLIC CADDY ROUTE ==="; curl -fsS https://core.sustainablecatalyst.com/health | python3 -c 'import json,sys;d=json.load(sys.stdin);assert d.get("version")=="2.55.0",d;print("PASS: public Core health 2.55.0")'; curl -fsS https://core.sustainablecatalyst.com/v1/predictive-intelligence/readiness | python3 -c 'import json,sys;d=json.load(sys.stdin);assert d.get("release")=="2.55.0" and d.get("migration_0059_applied") is True,d;print("PASS: public Predictive Intelligence ensemble/comparison readiness")'
echo; echo "=== FINAL CONTAINER ==="; docker ps --filter name=sc-core --format 'table {{.Names}}\t{{.Image}}\t{{.Status}}\t{{.Ports}}'
echo "Backup retained at: $BACKUP"
echo "============================================================"; echo " PLATFORM CORE v2.55.0 BACKEND DEPLOYMENT COMPLETE"; echo "============================================================"
