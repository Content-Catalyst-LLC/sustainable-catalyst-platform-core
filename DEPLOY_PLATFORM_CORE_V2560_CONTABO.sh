#!/usr/bin/env bash
set -euo pipefail
trap 'rc=$?; echo "ERROR: v2.56.0 deployment stopped at line $LINENO (exit $rc): $BASH_COMMAND" >&2; exit $rc' ERR
ROOT="${SC_CORE_ROOT:-/opt/sustainable-catalyst/core}"
BACKUP_ROOT="${SC_CORE_BACKUP_ROOT:-/opt/sustainable-catalyst/backups}"
COMPOSE="docker compose -f compose.yml -f compose.vps.yml"
STAMP="$(date +%Y%m%d-%H%M%S)"; BACKUP="${BACKUP_ROOT}/platform-core-v2.56.0-${STAMP}"
cd "$ROOT"
echo "============================================================"; echo " PLATFORM CORE v2.56.0 — ANOMALY / CHANGE-POINT / EARLY-WARNING"; echo "============================================================"
echo; echo "=== CURRENT LIVE HEALTH ==="; curl -fsS http://127.0.0.1:8090/health | python3 -m json.tool
echo; echo "=== SAFETY CHECKS ==="; [ -f compose.yml ] || { echo "STOP: compose.yml missing"; exit 1; }; [ -f compose.vps.yml ] || { echo "STOP: compose.vps.yml missing"; exit 1; }; [ -f .env.production ] || { echo "STOP: .env.production missing"; exit 1; }
if ! git diff --quiet || ! git diff --cached --quiet; then echo "STOP: tracked production files have local changes."; git status --short; exit 1; fi
$COMPOSE config >/tmp/sc-core-v2560-compose.yml; grep -q '/data/scientific-objects' /tmp/sc-core-v2560-compose.yml || { echo "STOP: scientific-object persistent mount missing"; exit 1; }
CORE_DB_URL="$(grep -m1 '^SC_CORE_DATABASE_URL=' .env.production | cut -d= -f2-)"; [ -n "$CORE_DB_URL" ] || { echo "STOP: SC_CORE_DATABASE_URL not found"; exit 1; }
eval "$(CORE_DB_URL="$CORE_DB_URL" python3 - <<'PY2'
import os,shlex
from urllib.parse import urlparse,unquote
u=urlparse(os.environ['CORE_DB_URL'].strip().strip('"').strip("'")); print('DB_USER='+shlex.quote(unquote(u.username or ''))); print('DB_PASS='+shlex.quote(unquote(u.password or ''))); print('DB_NAME='+shlex.quote((u.path or '').lstrip('/')))
PY2
)"
psqlq(){ docker exec -e PGPASSWORD="$DB_PASS" sc-postgres psql -h 127.0.0.1 -U "$DB_USER" -d "$DB_NAME" -Atqc "$1"; }
echo; echo "=== PRODUCTION PREDECESSOR PREFLIGHT ==="
M59="$(psqlq "SELECT EXISTS (SELECT 1 FROM schema_migrations WHERE version='0059');")"; echo "schema_migrations.0059=$M59"; [ "$M59" = t ] || { echo "STOP: migration 0059 is not recorded; v2.55.0 must be deployed first"; exit 1; }
V255_TABLES=(predictive_ensembles predictive_ensemble_members predictive_ensemble_forecasts predictive_comparison_studies predictive_comparison_candidates predictive_comparison_evidence predictive_pairwise_comparisons predictive_comparison_packages)
for t in "${V255_TABLES[@]}"; do v="$(psqlq "SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema='public' AND table_name='$t');")"; echo "$t=$v"; [ "$v" = t ] || { echo "STOP: predecessor v2.55 table missing: $t"; exit 1; }; done
V256_TABLES=(predictive_monitoring_studies predictive_detection_rules predictive_anomaly_observations predictive_change_points predictive_early_warning_signals predictive_monitoring_episodes predictive_monitoring_packages)
v256_count=0
for t in "${V256_TABLES[@]}"; do v="$(psqlq "SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema='public' AND table_name='$t');")"; echo "$t=$v"; [ "$v" = t ] && v256_count=$((v256_count+1)); done
M60="$(psqlq "SELECT EXISTS (SELECT 1 FROM schema_migrations WHERE version='0060');")"; echo "schema_migrations.0060=$M60"; echo "monitoring_tables_present=$v256_count/7"
if [ "$M60" = f ] && [ "$v256_count" -eq 0 ]; then echo "PASS: pristine pre-0060 monitoring state accepted";
elif [ "$M60" = f ] && [ "$v256_count" -eq 7 ]; then echo "PASS: safe partial-0060 monitoring table state detected and accepted";
elif [ "$M60" = t ] && [ "$v256_count" -eq 7 ]; then echo "PASS: migration 0060 already recorded with complete monitoring schema";
else echo "STOP: inconsistent monitoring migration state (0060=$M60, tables=$v256_count/7)"; exit 1; fi
echo; echo "=== BACKUP CURRENT CORE + DATABASE ==="; mkdir -p "$BACKUP"; tar --exclude='.git' -czf "$BACKUP/core-before-v2.56.0.tar.gz" .; docker exec -e PGPASSWORD="$DB_PASS" sc-postgres pg_dump -h 127.0.0.1 -U "$DB_USER" -d "$DB_NAME" -Fc > "$BACKUP/platform-core-before-v2.56.0.dump"; ls -lh "$BACKUP"/*
echo; echo "=== FETCH EXACT v2.56.0 RELEASE ==="; git fetch origin --tags; git rev-parse v2.56.0 >/dev/null 2>&1 || { echo "STOP: v2.56.0 tag is not available from GitHub"; exit 1; }; git pull --ff-only origin main; echo "HEAD: $(git log -1 --oneline)"; git tag --points-at HEAD | grep -qx 'v2.56.0' || { echo "STOP: production HEAD is not exactly tagged v2.56.0"; exit 1; }
head_commit="$(git rev-parse HEAD)"; tag_commit="$(git rev-list -n 1 v2.56.0)"; [ "$head_commit" = "$tag_commit" ] || { echo "STOP: v2.56.0 does not resolve to production HEAD"; exit 1; }
python3 -S scripts/validate_v2560_release.py
echo; echo "=== BUILD CORE v2.56.0 ==="; $COMPOSE build core
echo; echo "=== APPLY / REPAIR MIGRATION 0060 ==="; $COMPOSE run --rm --no-deps core python scripts/migrate.py | tee /tmp/sc-core-v2560-migrations.json
echo; echo "=== VERIFY DATABASE CONTRACT BEFORE RECREATE ==="
for t in "${V256_TABLES[@]}"; do [ "$(psqlq "SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema='public' AND table_name='$t');")" = t ] || { echo "STOP: $t missing after migration 0060"; exit 1; }; done
M60_POST="$(psqlq "SELECT EXISTS (SELECT 1 FROM schema_migrations WHERE version='0060');")"; [ "$M60_POST" = t ] || { echo "STOP: migration 0060 not recorded"; exit 1; }; D60_LEN="$(psqlq "SELECT length(description) FROM schema_migrations WHERE version='0060';")"; echo "schema_migrations.0060.description_length=$D60_LEN"; [ "$D60_LEN" -le 300 ] || { echo "STOP: stored 0060 description exceeds production contract"; exit 1; }
echo "PASS: migration 0060 complete; v2.55 ensemble/comparison schema preserved"
echo; echo "=== RECREATE sc-core ==="; $COMPOSE up -d --no-deps --force-recreate core
for i in $(seq 1 40); do if curl -fsS http://127.0.0.1:8090/health >/tmp/sc-core-v2560-health.json 2>/dev/null; then break; fi; [ "$i" -lt 40 ] || { docker logs --tail 200 sc-core; exit 1; }; sleep 2; done
for i in $(seq 1 40); do state="$(docker inspect --format '{{if .State.Health}}{{.State.Health.Status}}{{else}}none{{end}}' sc-core)"; echo "health=$state"; [ "$state" = healthy ] && break; [ "$state" != unhealthy ] || { docker logs --tail 200 sc-core; exit 1; }; [ "$i" -lt 40 ] || { docker logs --tail 200 sc-core; exit 1; }; sleep 2; done
echo; echo "=== LIVE HEALTH ==="; python3 -m json.tool </tmp/sc-core-v2560-health.json
echo; echo "=== PREDICTIVE INTELLIGENCE READINESS ==="; curl -fsS http://127.0.0.1:8090/v1/predictive-intelligence/readiness | tee /tmp/sc-core-v2560-predictive.json | python3 -m json.tool
python3 - <<'PY2'
import json
h=json.load(open('/tmp/sc-core-v2560-health.json')); r=json.load(open('/tmp/sc-core-v2560-predictive.json'))
assert h.get('ok') is True and h.get('version')=='2.56.0',h
assert h.get('predictive_model_object_model_forecast_provenance') is True and h.get('predictive_time_series_forecasting_backtesting') is True and h.get('predictive_probabilistic_forecasting_calibration') is True and h.get('predictive_ensembles_model_comparison') is True and h.get('predictive_anomaly_change_point_early_warning') is True,h
assert r.get('release')=='2.56.0' and r.get('migration_0059_applied') is True and r.get('migration_0060_applied') is True,r
for key in ('monitoring_study_registry_by_core','detection_rule_registry_by_core','anomaly_evidence_registry_by_core','change_point_evidence_registry_by_core','early_warning_signal_registry_by_core','monitoring_episode_registry_by_core','reproducible_monitoring_packages_by_core'): assert r.get(key) is True,(key,r)
for key in ('anomaly_detection_by_core','change_point_detection_by_core','early_warning_computation_by_core','threshold_optimization_by_core','alert_dispatch_by_core','causal_attribution_by_core','automatic_intervention_by_core','automatic_truth_promotion'): assert r.get(key) is False,(key,r)
print('PASS: Platform Core v2.56.0'); print('PASS: Anomaly, Change-Point & Early-Warning Intelligence'); print('PASS: migration 0060 additive with external-detection/non-intervention boundaries intact')
PY2
echo; echo "=== VERIFY MIGRATION STATE ==="; docker exec sc-core python scripts/migrate.py | tee /tmp/sc-core-v2560-migration-state.json
python3 - <<'PY2'
import json
m=json.load(open('/tmp/sc-core-v2560-migration-state.json')); assert '0060' in m.get('applied',[]) and m.get('pending')==[],m; print('PASS: migration 0060 applied and pending=[]')
PY2
echo; echo "=== PERSISTENT SCIENTIFIC STORAGE ==="; docker exec sc-core sh -lc 'test -d /data/scientific-objects; touch /data/scientific-objects/.v2560-write-test; rm /data/scientific-objects/.v2560-write-test; echo "PASS: persistent scientific-object storage writable"'
echo; echo "=== PUBLIC CADDY ROUTE ==="; curl -fsS https://core.sustainablecatalyst.com/health | python3 -c 'import json,sys;d=json.load(sys.stdin);assert d.get("version")=="2.56.0",d;print("PASS: public Core health 2.56.0")'; curl -fsS https://core.sustainablecatalyst.com/v1/predictive-intelligence/readiness | python3 -c 'import json,sys;d=json.load(sys.stdin);assert d.get("release")=="2.56.0" and d.get("migration_0060_applied") is True,d;print("PASS: public Predictive Intelligence monitoring readiness")'
echo; echo "=== FINAL CONTAINER ==="; docker ps --filter name=sc-core --format 'table {{.Names}}\t{{.Image}}\t{{.Status}}\t{{.Ports}}'
echo "Backup retained at: $BACKUP"
echo "============================================================"; echo " PLATFORM CORE v2.56.0 BACKEND DEPLOYMENT COMPLETE"; echo "============================================================"
