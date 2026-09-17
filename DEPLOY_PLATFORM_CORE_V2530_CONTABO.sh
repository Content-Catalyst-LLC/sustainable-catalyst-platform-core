#!/usr/bin/env bash
set -euo pipefail
trap 'rc=$?; echo "ERROR: v2.53.0 deployment stopped at line $LINENO (exit $rc): $BASH_COMMAND" >&2; exit $rc' ERR
ROOT="${SC_CORE_ROOT:-/opt/sustainable-catalyst/core}"
BACKUP_ROOT="${SC_CORE_BACKUP_ROOT:-/opt/sustainable-catalyst/backups}"
COMPOSE="docker compose -f compose.yml -f compose.vps.yml"
STAMP="$(date +%Y%m%d-%H%M%S)"; BACKUP="${BACKUP_ROOT}/platform-core-v2.53.0-${STAMP}"
cd "$ROOT"
echo "============================================================"; echo " PLATFORM CORE v2.53.0 — TIME-SERIES FORECASTING & BACKTESTING"; echo "============================================================"
echo; echo "=== CURRENT LIVE HEALTH ==="; curl -fsS http://127.0.0.1:8090/health | python3 -m json.tool
echo; echo "=== SAFETY CHECKS ==="; [ -f compose.yml ] || { echo "STOP: compose.yml missing"; exit 1; }; [ -f compose.vps.yml ] || { echo "STOP: compose.vps.yml missing"; exit 1; }; [ -f .env.production ] || { echo "STOP: .env.production missing"; exit 1; }
if ! git diff --quiet || ! git diff --cached --quiet; then echo "STOP: tracked production files have local changes."; git status --short; exit 1; fi
$COMPOSE config >/tmp/sc-core-v2530-compose.yml; grep -q '/data/scientific-objects' /tmp/sc-core-v2530-compose.yml || { echo "STOP: scientific-object persistent mount missing"; exit 1; }
CORE_DB_URL="$(grep -m1 '^SC_CORE_DATABASE_URL=' .env.production | cut -d= -f2-)"; [ -n "$CORE_DB_URL" ] || { echo "STOP: SC_CORE_DATABASE_URL not found"; exit 1; }
eval "$(CORE_DB_URL="$CORE_DB_URL" python3 - <<'PY2'
import os,shlex
from urllib.parse import urlparse,unquote
u=urlparse(os.environ['CORE_DB_URL'].strip().strip('"').strip("'")); print('DB_USER='+shlex.quote(unquote(u.username or ''))); print('DB_PASS='+shlex.quote(unquote(u.password or ''))); print('DB_NAME='+shlex.quote((u.path or '').lstrip('/')))
PY2
)"
psqlq(){ docker exec -e PGPASSWORD="$DB_PASS" sc-postgres psql -h 127.0.0.1 -U "$DB_USER" -d "$DB_NAME" -Atqc "$1"; }
echo; echo "=== PRODUCTION PREDECESSOR PREFLIGHT ==="
M56="$(psqlq "SELECT EXISTS (SELECT 1 FROM schema_migrations WHERE version='0056');")"; echo "schema_migrations.0056=$M56"; [ "$M56" = t ] || { echo "STOP: migration 0056 is not recorded; v2.52.0 must be deployed first"; exit 1; }
V252_TABLES=(predictive_models predictive_targets predictive_features predictive_training_windows predictive_forecast_runs predictive_forecast_observations predictive_evaluations predictive_runtime_handoffs predictive_forecast_snapshots)
for t in "${V252_TABLES[@]}"; do v="$(psqlq "SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema='public' AND table_name='$t');")"; echo "$t=$v"; [ "$v" = t ] || { echo "STOP: predecessor v2.52 table missing: $t"; exit 1; }; done
V253_TABLES=(predictive_time_series_datasets predictive_forecast_windows predictive_baseline_models predictive_backtest_plans predictive_backtest_folds predictive_backtest_observations predictive_backtest_evaluations predictive_backtest_packages)
v253_count=0
for t in "${V253_TABLES[@]}"; do v="$(psqlq "SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema='public' AND table_name='$t');")"; echo "$t=$v"; [ "$v" = t ] && v253_count=$((v253_count+1)); done
M57="$(psqlq "SELECT EXISTS (SELECT 1 FROM schema_migrations WHERE version='0057');")"; echo "schema_migrations.0057=$M57"; echo "backtest_tables_present=$v253_count/8"
if [ "$M57" = f ] && [ "$v253_count" -eq 0 ]; then echo "PASS: pristine pre-0057 backtesting state accepted";
elif [ "$M57" = f ] && [ "$v253_count" -eq 8 ]; then echo "PASS: safe partial-0057 backtesting table state detected and accepted";
elif [ "$M57" = t ] && [ "$v253_count" -eq 8 ]; then echo "PASS: migration 0057 already recorded with complete backtesting schema";
else echo "STOP: inconsistent backtesting migration state (0057=$M57, tables=$v253_count/8)"; exit 1; fi
echo; echo "=== BACKUP CURRENT CORE + DATABASE ==="; mkdir -p "$BACKUP"; tar --exclude='.git' -czf "$BACKUP/core-before-v2.53.0.tar.gz" .; docker exec -e PGPASSWORD="$DB_PASS" sc-postgres pg_dump -h 127.0.0.1 -U "$DB_USER" -d "$DB_NAME" -Fc > "$BACKUP/platform-core-before-v2.53.0.dump"; ls -lh "$BACKUP"/*
echo; echo "=== FETCH EXACT v2.53.0 RELEASE ==="; git fetch origin --tags; git rev-parse v2.53.0 >/dev/null 2>&1 || { echo "STOP: v2.53.0 tag is not available from GitHub"; exit 1; }; git pull --ff-only origin main; echo "HEAD: $(git log -1 --oneline)"; git tag --points-at HEAD | grep -qx 'v2.53.0' || { echo "STOP: production HEAD is not exactly tagged v2.53.0"; exit 1; }
head_commit="$(git rev-parse HEAD)"; tag_commit="$(git rev-list -n 1 v2.53.0)"; [ "$head_commit" = "$tag_commit" ] || { echo "STOP: v2.53.0 does not resolve to production HEAD"; exit 1; }
python3 - <<'PY2'
import ast,re
from pathlib import Path
mig=Path('backend/app/migrations.py'); tree=ast.parse(mig.read_text(),filename=str(mig)); migrations=None
for node in tree.body:
    if isinstance(node,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='MIGRATIONS' for t in node.targets): migrations=ast.literal_eval(node.value); break
assert migrations and migrations[-1][0]=='0057',migrations[-1]
models=Path('backend/app/models.py').read_text(); m=re.search(r'class\s+SchemaMigration\b.*?description:\s*Mapped\[str\]\s*=\s*mapped_column\(String\((\d+)\)',models,re.S); assert m
mx=int(m.group(1)); d=dict(migrations)['0057']; assert mx==300 and len(d)<=mx,(mx,len(d)); print(f'PASS: packaged 0057 migration description fits VARCHAR({mx}) at {len(d)} chars')
PY2
echo; echo "=== BUILD CORE v2.53.0 ==="; $COMPOSE build core
echo; echo "=== APPLY / REPAIR MIGRATION 0057 ==="; $COMPOSE run --rm --no-deps core python scripts/migrate.py | tee /tmp/sc-core-v2530-migrations.json
echo; echo "=== VERIFY DATABASE CONTRACT BEFORE RECREATE ==="
for t in "${V253_TABLES[@]}"; do [ "$(psqlq "SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema='public' AND table_name='$t');")" = t ] || { echo "STOP: $t missing after migration 0057"; exit 1; }; done
M57_POST="$(psqlq "SELECT EXISTS (SELECT 1 FROM schema_migrations WHERE version='0057');")"; [ "$M57_POST" = t ] || { echo "STOP: migration 0057 not recorded"; exit 1; }; D57_LEN="$(psqlq "SELECT length(description) FROM schema_migrations WHERE version='0057';")"; echo "schema_migrations.0057.description_length=$D57_LEN"; [ "$D57_LEN" -le 300 ] || { echo "STOP: stored 0057 description exceeds production contract"; exit 1; }; echo "PASS: migration 0057 complete; v2.52 predictive provenance schema preserved"
echo; echo "=== RECREATE sc-core ==="; $COMPOSE up -d --no-deps --force-recreate core
for i in $(seq 1 40); do if curl -fsS http://127.0.0.1:8090/health >/tmp/sc-core-v2530-health.json 2>/dev/null; then break; fi; [ "$i" -lt 40 ] || { docker logs --tail 200 sc-core; exit 1; }; sleep 2; done
for i in $(seq 1 40); do state="$(docker inspect --format '{{if .State.Health}}{{.State.Health.Status}}{{else}}none{{end}}' sc-core)"; echo "health=$state"; [ "$state" = healthy ] && break; [ "$state" != unhealthy ] || { docker logs --tail 200 sc-core; exit 1; }; [ "$i" -lt 40 ] || { docker logs --tail 200 sc-core; exit 1; }; sleep 2; done
echo; echo "=== LIVE HEALTH ==="; python3 -m json.tool </tmp/sc-core-v2530-health.json
echo; echo "=== PREDICTIVE INTELLIGENCE READINESS ==="; curl -fsS http://127.0.0.1:8090/v1/predictive-intelligence/readiness | tee /tmp/sc-core-v2530-predictive.json | python3 -m json.tool
python3 - <<'PY2'
import json
h=json.load(open('/tmp/sc-core-v2530-health.json')); r=json.load(open('/tmp/sc-core-v2530-predictive.json'))
assert h.get('ok') is True and h.get('version')=='2.53.0',h; assert h.get('predictive_model_object_model_forecast_provenance') is True,h; assert h.get('predictive_time_series_forecasting_backtesting') is True,h
assert r.get('release')=='2.53.0' and r.get('migration_0056_applied') is True and r.get('migration_0057_applied') is True,r
for key in ('time_series_dataset_registry_by_core','forecast_window_registry_by_core','baseline_model_reference_registry_by_core','rolling_expanding_backtest_semantics_by_core','temporal_leakage_guardrails_by_core','backtest_fold_provenance_by_core','prediction_actual_pair_recording_by_core','descriptive_backtest_evaluation_by_core','reproducible_backtest_packages_by_core'): assert r.get(key) is True,(key,r)
for key in ('model_fitting_by_core','forecast_inference_execution_by_core','backtest_execution_by_core','metric_computation_by_core','time_series_resampling_by_core','automatic_model_ranking_by_core','automatic_truth_promotion'): assert r.get(key) is False,(key,r)
print('PASS: Platform Core v2.53.0'); print('PASS: Time-Series Forecasting & Backtesting'); print('PASS: migration 0057 additive with temporal leakage guardrails and non-execution/non-ranking boundaries intact')
PY2
echo; echo "=== VERIFY MIGRATION STATE ==="; docker exec sc-core python scripts/migrate.py | tee /tmp/sc-core-v2530-migration-state.json
python3 - <<'PY2'
import json
m=json.load(open('/tmp/sc-core-v2530-migration-state.json')); assert '0057' in m.get('applied',[]) and m.get('pending')==[],m; print('PASS: migration 0057 applied and pending=[]')
PY2
echo; echo "=== VERIFY PERSISTENT SCIENTIFIC STORAGE MOUNT ==="; docker exec sc-core sh -lc 'test -d /data/scientific-objects; touch /data/scientific-objects/.v2530-write-test; rm /data/scientific-objects/.v2530-write-test; echo "PASS: persistent scientific-object storage writable"'
echo; echo "=== PUBLIC CADDY ROUTE ==="; curl -fsS https://core.sustainablecatalyst.com/health | python3 -c 'import json,sys;d=json.load(sys.stdin);assert d.get("version")=="2.53.0",d;print("PASS: public Core health 2.53.0")'; curl -fsS https://core.sustainablecatalyst.com/v1/predictive-intelligence/readiness | python3 -c 'import json,sys;d=json.load(sys.stdin);assert d.get("release")=="2.53.0" and d.get("migration_0057_applied") is True,d;print("PASS: public Predictive Intelligence backtesting readiness")'
echo; echo "=== FINAL CONTAINER ==="; docker ps --filter name=sc-core --format 'table {{.Names}}\t{{.Image}}\t{{.Status}}\t{{.Ports}}'
echo "Backup retained at: $BACKUP"
echo "============================================================"; echo " PLATFORM CORE v2.53.0 BACKEND DEPLOYMENT COMPLETE"; echo "============================================================"
