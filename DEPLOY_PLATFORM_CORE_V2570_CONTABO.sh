#!/usr/bin/env bash
set -euo pipefail
trap 'rc=$?; echo "ERROR: v2.57.0 deployment stopped at line $LINENO (exit $rc): $BASH_COMMAND" >&2; exit $rc' ERR
ROOT="${SC_CORE_ROOT:-/opt/sustainable-catalyst/core}"
BACKUP_ROOT="${SC_CORE_BACKUP_ROOT:-/opt/sustainable-catalyst/backups}"
COMPOSE="docker compose -f compose.yml -f compose.vps.yml"
STAMP="$(date +%Y%m%d-%H%M%S)"; BACKUP="${BACKUP_ROOT}/platform-core-v2.57.0-${STAMP}"
cd "$ROOT"
echo "============================================================"; echo " PLATFORM CORE v2.57.0 — SPATIAL-TEMPORAL PREDICTIVE INTELLIGENCE"; echo "============================================================"
echo; echo "=== CURRENT LIVE HEALTH ==="; curl -fsS http://127.0.0.1:8090/health | python3 -m json.tool
echo; echo "=== SAFETY CHECKS ==="; [ -f compose.yml ] || { echo "STOP: compose.yml missing"; exit 1; }; [ -f compose.vps.yml ] || { echo "STOP: compose.vps.yml missing"; exit 1; }; [ -f .env.production ] || { echo "STOP: .env.production missing"; exit 1; }
if ! git diff --quiet || ! git diff --cached --quiet; then echo "STOP: tracked production files have local changes."; git status --short; exit 1; fi
$COMPOSE config >/tmp/sc-core-v2570-compose.yml; grep -q '/data/scientific-objects' /tmp/sc-core-v2570-compose.yml || { echo "STOP: scientific-object persistent mount missing"; exit 1; }
CORE_DB_URL="$(grep -m1 '^SC_CORE_DATABASE_URL=' .env.production | cut -d= -f2-)"; [ -n "$CORE_DB_URL" ] || { echo "STOP: SC_CORE_DATABASE_URL not found"; exit 1; }
eval "$(CORE_DB_URL="$CORE_DB_URL" python3 - <<'PY2'
import os,shlex
from urllib.parse import urlparse,unquote
u=urlparse(os.environ['CORE_DB_URL'].strip().strip('"').strip("'")); print('DB_USER='+shlex.quote(unquote(u.username or ''))); print('DB_PASS='+shlex.quote(unquote(u.password or ''))); print('DB_NAME='+shlex.quote((u.path or '').lstrip('/')))
PY2
)"
psqlq(){ docker exec -e PGPASSWORD="$DB_PASS" sc-postgres psql -h 127.0.0.1 -U "$DB_USER" -d "$DB_NAME" -Atqc "$1"; }
echo; echo "=== PRODUCTION PREDECESSOR PREFLIGHT ==="
M60="$(psqlq "SELECT EXISTS (SELECT 1 FROM schema_migrations WHERE version='0060');")"; echo "schema_migrations.0060=$M60"; [ "$M60" = t ] || { echo "STOP: migration 0060 is not recorded; v2.56.0 must be deployed first"; exit 1; }
V256_TABLES=(predictive_monitoring_studies predictive_detection_rules predictive_anomaly_observations predictive_change_points predictive_early_warning_signals predictive_monitoring_episodes predictive_monitoring_packages)
for t in "${V256_TABLES[@]}"; do v="$(psqlq "SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema='public' AND table_name='$t');")"; echo "$t=$v"; [ "$v" = t ] || { echo "STOP: predecessor v2.56 table missing: $t"; exit 1; }; done
V257_TABLES=(predictive_spatial_temporal_studies predictive_spatial_units predictive_spatial_temporal_forecasts predictive_spatial_temporal_observations predictive_spatial_propagation_evidence predictive_spatial_hotspot_evidence predictive_spatial_temporal_evaluations predictive_spatial_temporal_packages)
v257_count=0
for t in "${V257_TABLES[@]}"; do v="$(psqlq "SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema='public' AND table_name='$t');")"; echo "$t=$v"; [ "$v" = t ] && v257_count=$((v257_count+1)); done
M61="$(psqlq "SELECT EXISTS (SELECT 1 FROM schema_migrations WHERE version='0061');")"; echo "schema_migrations.0061=$M61"; echo "spatial_temporal_tables_present=$v257_count/8"
if [ "$M61" = f ] && [ "$v257_count" -eq 0 ]; then echo "PASS: pristine pre-0061 spatial-temporal state accepted";
elif [ "$M61" = f ] && [ "$v257_count" -eq 8 ]; then echo "PASS: safe partial-0061 spatial-temporal table state detected and accepted";
elif [ "$M61" = t ] && [ "$v257_count" -eq 8 ]; then echo "PASS: migration 0061 already recorded with complete spatial-temporal schema";
else echo "STOP: inconsistent spatial-temporal migration state (0061=$M61, tables=$v257_count/8)"; exit 1; fi
echo; echo "=== BACKUP CURRENT CORE + DATABASE ==="; mkdir -p "$BACKUP"; tar --exclude='.git' -czf "$BACKUP/core-before-v2.57.0.tar.gz" .; docker exec -e PGPASSWORD="$DB_PASS" sc-postgres pg_dump -h 127.0.0.1 -U "$DB_USER" -d "$DB_NAME" -Fc > "$BACKUP/platform-core-before-v2.57.0.dump"; ls -lh "$BACKUP"/*
echo; echo "=== FETCH EXACT v2.57.0 RELEASE ==="; git fetch origin --tags; git rev-parse v2.57.0 >/dev/null 2>&1 || { echo "STOP: v2.57.0 tag is not available from GitHub"; exit 1; }; git pull --ff-only origin main; echo "HEAD: $(git log -1 --oneline)"; git tag --points-at HEAD | grep -qx 'v2.57.0' || { echo "STOP: production HEAD is not exactly tagged v2.57.0"; exit 1; }
head_commit="$(git rev-parse HEAD)"; tag_commit="$(git rev-list -n 1 v2.57.0)"; [ "$head_commit" = "$tag_commit" ] || { echo "STOP: v2.57.0 does not resolve to production HEAD"; exit 1; }
python3 -S scripts/validate_v2570_release.py
echo; echo "=== BUILD CORE v2.57.0 ==="; $COMPOSE build core
echo; echo "=== APPLY / REPAIR MIGRATION 0061 ==="; $COMPOSE run --rm --no-deps core python scripts/migrate.py | tee /tmp/sc-core-v2570-migrations.json
echo; echo "=== VERIFY DATABASE CONTRACT BEFORE RECREATE ==="
for t in "${V257_TABLES[@]}"; do [ "$(psqlq "SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema='public' AND table_name='$t');")" = t ] || { echo "STOP: $t missing after migration 0061"; exit 1; }; done
M61_POST="$(psqlq "SELECT EXISTS (SELECT 1 FROM schema_migrations WHERE version='0061');")"; [ "$M61_POST" = t ] || { echo "STOP: migration 0061 not recorded"; exit 1; }; D61_LEN="$(psqlq "SELECT length(description) FROM schema_migrations WHERE version='0061';")"; echo "schema_migrations.0061.description_length=$D61_LEN"; [ "$D61_LEN" -le 300 ] || { echo "STOP: stored 0061 description exceeds production contract"; exit 1; }
echo "PASS: migration 0061 complete; v2.56 monitoring schema preserved"
echo; echo "=== RECREATE sc-core ==="; $COMPOSE up -d --no-deps --force-recreate core
for i in $(seq 1 40); do if curl -fsS http://127.0.0.1:8090/health >/tmp/sc-core-v2570-health.json 2>/dev/null; then break; fi; [ "$i" -lt 40 ] || { docker logs --tail 200 sc-core; exit 1; }; sleep 2; done
for i in $(seq 1 40); do state="$(docker inspect --format '{{if .State.Health}}{{.State.Health.Status}}{{else}}none{{end}}' sc-core)"; echo "health=$state"; [ "$state" = healthy ] && break; [ "$state" != unhealthy ] || { docker logs --tail 200 sc-core; exit 1; }; [ "$i" -lt 40 ] || { docker logs --tail 200 sc-core; exit 1; }; sleep 2; done
echo; echo "=== LIVE HEALTH ==="; python3 -m json.tool </tmp/sc-core-v2570-health.json
echo; echo "=== PREDICTIVE INTELLIGENCE READINESS ==="; curl -fsS http://127.0.0.1:8090/v1/predictive-intelligence/readiness | tee /tmp/sc-core-v2570-predictive.json | python3 -m json.tool
python3 - <<'PY2'
import json
h=json.load(open('/tmp/sc-core-v2570-health.json')); r=json.load(open('/tmp/sc-core-v2570-predictive.json'))
assert h.get('ok') is True and h.get('version')=='2.57.0',h
assert h.get('predictive_anomaly_change_point_early_warning') is True and h.get('predictive_spatial_temporal_intelligence') is True,h
assert r.get('release')=='2.57.0' and r.get('migration_0060_applied') is True and r.get('migration_0061_applied') is True,r
for key in ('spatial_temporal_study_registry_by_core','spatial_unit_registry_by_core','spatial_temporal_forecast_provenance_by_core','spatial_temporal_observation_registry_by_core','propagation_evidence_registry_by_core','hotspot_evidence_registry_by_core','spatial_temporal_evaluation_evidence_by_core','reproducible_spatial_temporal_packages_by_core'): assert r.get(key) is True,(key,r)
for key in ('spatial_interpolation_by_core','spatial_inference_execution_by_core','trajectory_prediction_by_core','propagation_modeling_by_core','hotspot_detection_by_core','spatial_temporal_metric_computation_by_core','automatic_intervention_by_core','automatic_truth_promotion'): assert r.get(key) is False,(key,r)
print('PASS: Platform Core v2.57.0'); print('PASS: Spatial-Temporal Predictive Intelligence'); print('PASS: migration 0061 additive with external-compute/non-intervention boundaries intact')
PY2
echo; echo "=== VERIFY MIGRATION STATE ==="; docker exec sc-core python scripts/migrate.py | tee /tmp/sc-core-v2570-migration-state.json
python3 - <<'PY2'
import json
m=json.load(open('/tmp/sc-core-v2570-migration-state.json')); assert '0061' in m.get('applied',[]) and m.get('pending')==[],m; print('PASS: migration 0061 applied and pending=[]')
PY2
echo; echo "=== PERSISTENT SCIENTIFIC STORAGE ==="; docker exec sc-core sh -lc 'test -d /data/scientific-objects; touch /data/scientific-objects/.v2570-write-test; rm /data/scientific-objects/.v2570-write-test; echo "PASS: persistent scientific-object storage writable"'
echo; echo "=== PUBLIC CADDY ROUTE ==="; curl -fsS https://core.sustainablecatalyst.com/health | python3 -c 'import json,sys;d=json.load(sys.stdin);assert d.get("version")=="2.57.0",d;print("PASS: public Core health 2.57.0")'; curl -fsS https://core.sustainablecatalyst.com/v1/predictive-intelligence/readiness | python3 -c 'import json,sys;d=json.load(sys.stdin);assert d.get("release")=="2.57.0" and d.get("migration_0061_applied") is True,d;print("PASS: public Predictive Intelligence spatial-temporal readiness")'
echo; echo "=== FINAL CONTAINER ==="; docker ps --filter name=sc-core --format 'table {{.Names}}	{{.Image}}	{{.Status}}	{{.Ports}}'
echo "Backup retained at: $BACKUP"
echo "============================================================"; echo " PLATFORM CORE v2.57.0 BACKEND DEPLOYMENT COMPLETE"; echo "============================================================"
