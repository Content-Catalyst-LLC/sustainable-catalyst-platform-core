#!/usr/bin/env bash
set -euo pipefail
trap 'rc=$?; echo "ERROR: v2.52.0 deployment stopped at line $LINENO (exit $rc): $BASH_COMMAND" >&2; exit $rc' ERR
ROOT="${SC_CORE_ROOT:-/opt/sustainable-catalyst/core}"
BACKUP_ROOT="${SC_CORE_BACKUP_ROOT:-/opt/sustainable-catalyst/backups}"
COMPOSE="docker compose -f compose.yml -f compose.vps.yml"
STAMP="$(date +%Y%m%d-%H%M%S)"; BACKUP="${BACKUP_ROOT}/platform-core-v2.52.0-${STAMP}"
cd "$ROOT"
echo "============================================================"; echo " PLATFORM CORE v2.52.0 — PREDICTIVE MODEL OBJECT MODEL & FORECAST PROVENANCE"; echo "============================================================"
echo; echo "=== CURRENT LIVE HEALTH ==="; curl -fsS http://127.0.0.1:8090/health | python3 -m json.tool
echo; echo "=== SAFETY CHECKS ==="; [ -f compose.yml ] || { echo "STOP: compose.yml missing"; exit 1; }; [ -f compose.vps.yml ] || { echo "STOP: compose.vps.yml missing"; exit 1; }; [ -f .env.production ] || { echo "STOP: .env.production missing"; exit 1; }
if ! git diff --quiet || ! git diff --cached --quiet; then echo "STOP: tracked production files have local changes."; git status --short; exit 1; fi
$COMPOSE config >/tmp/sc-core-v2520-compose.yml; grep -q '/data/scientific-objects' /tmp/sc-core-v2520-compose.yml || { echo "STOP: scientific-object persistent mount missing"; exit 1; }
CORE_DB_URL="$(grep -m1 '^SC_CORE_DATABASE_URL=' .env.production | cut -d= -f2-)"; [ -n "$CORE_DB_URL" ] || { echo "STOP: SC_CORE_DATABASE_URL not found"; exit 1; }
eval "$(CORE_DB_URL="$CORE_DB_URL" python3 - <<'PY2'
import os,shlex
from urllib.parse import urlparse,unquote
u=urlparse(os.environ['CORE_DB_URL'].strip().strip('"').strip("'")); print('DB_USER='+shlex.quote(unquote(u.username or ''))); print('DB_PASS='+shlex.quote(unquote(u.password or ''))); print('DB_NAME='+shlex.quote((u.path or '').lstrip('/')))
PY2
)"
psqlq(){ docker exec -e PGPASSWORD="$DB_PASS" sc-postgres psql -h 127.0.0.1 -U "$DB_USER" -d "$DB_NAME" -Atqc "$1"; }
echo; echo "=== PRODUCTION PREDECESSOR PREFLIGHT ==="
M55="$(psqlq "SELECT EXISTS (SELECT 1 FROM schema_migrations WHERE version='0055');")"; echo "schema_migrations.0055=$M55"; [ "$M55" = t ] || { echo "STOP: migration 0055 is not recorded; v2.51.0 must be deployed first"; exit 1; }
V251_TABLES=(forensic_investigation_packages forensic_investigation_package_components forensic_investigation_package_artifacts forensic_investigation_package_environments forensic_investigation_package_verifications forensic_investigation_package_reviews forensic_investigation_package_snapshots)
for t in "${V251_TABLES[@]}"; do v="$(psqlq "SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema='public' AND table_name='$t');")"; echo "$t=$v"; [ "$v" = t ] || { echo "STOP: predecessor v2.51 table missing: $t"; exit 1; }; done
V252_TABLES=(predictive_models predictive_targets predictive_features predictive_training_windows predictive_forecast_runs predictive_forecast_observations predictive_evaluations predictive_runtime_handoffs predictive_forecast_snapshots)
v252_count=0
for t in "${V252_TABLES[@]}"; do v="$(psqlq "SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema='public' AND table_name='$t');")"; echo "$t=$v"; [ "$v" = t ] && v252_count=$((v252_count+1)); done
M56="$(psqlq "SELECT EXISTS (SELECT 1 FROM schema_migrations WHERE version='0056');")"; echo "schema_migrations.0056=$M56"; echo "predictive_tables_present=$v252_count/9"
if [ "$M56" = f ] && [ "$v252_count" -eq 0 ]; then echo "PASS: pristine pre-0056 predictive state accepted";
elif [ "$M56" = f ] && [ "$v252_count" -eq 9 ]; then echo "PASS: safe partial-0056 predictive table state detected and accepted";
elif [ "$M56" = t ] && [ "$v252_count" -eq 9 ]; then echo "PASS: migration 0056 already recorded with complete predictive schema";
else echo "STOP: inconsistent predictive migration state (0056=$M56, tables=$v252_count/9)"; exit 1; fi
echo; echo "=== BACKUP CURRENT CORE + DATABASE ==="; mkdir -p "$BACKUP"; tar --exclude='.git' -czf "$BACKUP/core-before-v2.52.0.tar.gz" .; docker exec -e PGPASSWORD="$DB_PASS" sc-postgres pg_dump -h 127.0.0.1 -U "$DB_USER" -d "$DB_NAME" -Fc > "$BACKUP/platform-core-before-v2.52.0.dump"; ls -lh "$BACKUP"/*
echo; echo "=== FETCH EXACT v2.52.0 RELEASE ==="; git fetch origin --tags; git rev-parse v2.52.0 >/dev/null 2>&1 || { echo "STOP: v2.52.0 tag is not available from GitHub"; exit 1; }; git pull --ff-only origin main; echo "HEAD: $(git log -1 --oneline)"; git tag --points-at HEAD | grep -qx 'v2.52.0' || { echo "STOP: production HEAD is not exactly tagged v2.52.0"; exit 1; }
head_commit="$(git rev-parse HEAD)"; tag_commit="$(git rev-list -n 1 v2.52.0)"; [ "$head_commit" = "$tag_commit" ] || { echo "STOP: v2.52.0 does not resolve to production HEAD"; exit 1; }
python3 - <<'PY2'
import ast,re
from pathlib import Path
mig=Path('backend/app/migrations.py'); tree=ast.parse(mig.read_text(),filename=str(mig)); migrations=None
for node in tree.body:
    if isinstance(node,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='MIGRATIONS' for t in node.targets): migrations=ast.literal_eval(node.value); break
assert migrations and migrations[-1][0]=='0056',migrations[-1]
models=Path('backend/app/models.py').read_text(); m=re.search(r'class\s+SchemaMigration.*?description:\s*Mapped\[str\]\s*=\s*mapped_column\(String\((\d+)\)',models,re.S); assert m
mx=int(m.group(1)); d=dict(migrations)['0056']; assert mx==300 and len(d)<=mx,(mx,len(d)); print(f'PASS: packaged 0056 migration description fits VARCHAR({mx}) at {len(d)} chars')
PY2
echo; echo "=== BUILD CORE v2.52.0 ==="; $COMPOSE build core
echo; echo "=== APPLY / REPAIR MIGRATION 0056 ==="; $COMPOSE run --rm --no-deps core python scripts/migrate.py | tee /tmp/sc-core-v2520-migrations.json
echo; echo "=== VERIFY DATABASE CONTRACT BEFORE RECREATE ==="
for t in "${V252_TABLES[@]}"; do [ "$(psqlq "SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema='public' AND table_name='$t');")" = t ] || { echo "STOP: $t missing after migration 0056"; exit 1; }; done
M56_POST="$(psqlq "SELECT EXISTS (SELECT 1 FROM schema_migrations WHERE version='0056');")"; [ "$M56_POST" = t ] || { echo "STOP: migration 0056 not recorded"; exit 1; }; D56_LEN="$(psqlq "SELECT length(description) FROM schema_migrations WHERE version='0056';")"; echo "schema_migrations.0056.description_length=$D56_LEN"; [ "$D56_LEN" -le 300 ] || { echo "STOP: stored 0056 description exceeds production contract"; exit 1; }; echo "PASS: migration 0056 complete; v2.51 reproducible-investigation schema preserved"
echo; echo "=== RECREATE sc-core ==="; $COMPOSE up -d --no-deps --force-recreate core
for i in $(seq 1 40); do if curl -fsS http://127.0.0.1:8090/health >/tmp/sc-core-v2520-health.json 2>/dev/null; then break; fi; [ "$i" -lt 40 ] || { docker logs --tail 200 sc-core; exit 1; }; sleep 2; done
for i in $(seq 1 40); do state="$(docker inspect --format '{{if .State.Health}}{{.State.Health.Status}}{{else}}none{{end}}' sc-core)"; echo "health=$state"; [ "$state" = healthy ] && break; [ "$state" != unhealthy ] || { docker logs --tail 200 sc-core; exit 1; }; [ "$i" -lt 40 ] || { docker logs --tail 200 sc-core; exit 1; }; sleep 2; done
echo; echo "=== LIVE HEALTH ==="; python3 -m json.tool </tmp/sc-core-v2520-health.json
echo; echo "=== PREDICTIVE INTELLIGENCE READINESS ==="; curl -fsS http://127.0.0.1:8090/v1/predictive-intelligence/readiness | tee /tmp/sc-core-v2520-predictive.json | python3 -m json.tool
python3 - <<'PY2'
import json
h=json.load(open('/tmp/sc-core-v2520-health.json')); r=json.load(open('/tmp/sc-core-v2520-predictive.json'))
assert h.get('ok') is True and h.get('version')=='2.52.0',h; assert h.get('predictive_model_object_model_forecast_provenance') is True,h
assert r.get('release')=='2.52.0' and r.get('migration_0056_applied') is True,r
for key in ('predictive_model_registry_by_core','prediction_target_registry_by_core','feature_provenance_registry_by_core','training_window_manifest_by_core','forecast_provenance_capture_by_core','forecast_observation_binding_by_core','descriptive_evaluation_evidence_by_core','specialist_runtime_handoffs_by_core','immutable_forecast_snapshots_by_core'): assert r.get(key) is True,(key,r)
for key in ('model_fitting_by_core','forecast_inference_execution_by_core','probabilistic_calibration_by_core','ensemble_selection_by_core','automatic_model_ranking_by_core','automatic_truth_promotion'): assert r.get(key) is False,(key,r)
print('PASS: Platform Core v2.52.0'); print('PASS: Predictive Model Object Model & Forecast Provenance'); print('PASS: migration 0056 additive with forecast provenance and non-execution/non-ranking boundaries intact')
PY2
echo; echo "=== VERIFY MIGRATION STATE ==="; docker exec sc-core python scripts/migrate.py | tee /tmp/sc-core-v2520-migration-state.json
python3 - <<'PY2'
import json
m=json.load(open('/tmp/sc-core-v2520-migration-state.json')); assert '0056' in m.get('applied',[]) and m.get('pending')==[],m; print('PASS: migration 0056 applied and pending=[]')
PY2
echo; echo "=== VERIFY PERSISTENT SCIENTIFIC STORAGE MOUNT ==="; docker exec sc-core sh -lc 'test -d /data/scientific-objects; touch /data/scientific-objects/.v2520-write-test; rm /data/scientific-objects/.v2520-write-test; echo "PASS: persistent scientific-object storage writable"'
echo; echo "=== PUBLIC CADDY ROUTE ==="; curl -fsS https://core.sustainablecatalyst.com/health | python3 -c 'import json,sys;d=json.load(sys.stdin);assert d.get("version")=="2.52.0",d;print("PASS: public Core health 2.52.0")'; curl -fsS https://core.sustainablecatalyst.com/v1/predictive-intelligence/readiness | python3 -c 'import json,sys;d=json.load(sys.stdin);assert d.get("release")=="2.52.0" and d.get("migration_0056_applied") is True,d;print("PASS: public Predictive Intelligence readiness")'
echo; echo "=== FINAL CONTAINER ==="; docker ps --filter name=sc-core --format 'table {{.Names}}	{{.Image}}	{{.Status}}	{{.Ports}}'
echo "Backup retained at: $BACKUP"
echo "============================================================"; echo " PLATFORM CORE v2.52.0 BACKEND DEPLOYMENT COMPLETE"; echo "============================================================"
