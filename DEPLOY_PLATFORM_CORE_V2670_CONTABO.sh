#!/usr/bin/env bash
set -euo pipefail
trap 'rc=$?; echo "ERROR: v2.67.0 deployment stopped at line $LINENO (exit $rc): $BASH_COMMAND" >&2; exit $rc' ERR
ROOT="${SC_CORE_ROOT:-/opt/sustainable-catalyst/core}"; COMPOSE="docker compose -f compose.yml -f compose.vps.yml"; cd "$ROOT"
echo "=== PLATFORM CORE v2.67.0 — VISUAL PREDICTIVE INTELLIGENCE ==="
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
[ "$(psqlq "SELECT EXISTS (SELECT 1 FROM schema_migrations WHERE version='0070');")" = t ] || { echo "STOP: migration 0070 missing; deploy v2.66.0 first"; exit 1; }
V266_TABLES=(visual_model_constructions visual_model_components visual_model_relationships visual_model_assumptions visual_model_constraints visual_model_interventions visual_model_handoffs visual_model_snapshots)
for t in "${V266_TABLES[@]}"; do [ "$(psqlq "SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema='public' AND table_name='$t');")" = t ] || { echo "STOP: predecessor table missing: $t"; exit 1; }; done
V267_TABLES=(visual_predictive_workspaces visual_forecast_overlays visual_uncertainty_displays visual_calibration_displays visual_ensemble_comparison_overlays visual_monitoring_overlays visual_spatial_temporal_forecast_layers visual_causal_predictive_overlays visual_decision_prediction_bindings visual_predictive_snapshots)
count=0; for t in "${V267_TABLES[@]}"; do v="$(psqlq "SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema='public' AND table_name='$t');")"; [ "$v" = t ] && count=$((count+1)); done
m71="$(psqlq "SELECT EXISTS (SELECT 1 FROM schema_migrations WHERE version='0071');")"
if [ "$m71" = f ] && [ "$count" -eq 0 ]; then echo "PASS: pristine pre-0071 state"; elif [ "$m71" = f ] && [ "$count" -eq 10 ]; then echo "PASS: recoverable partial-0071 state"; elif [ "$m71" = t ] && [ "$count" -eq 10 ]; then echo "PASS: already-complete 0071 state"; else echo "STOP: inconsistent 0071 state ($m71, $count/10)"; exit 1; fi
echo "=== BACKUP ===";mkdir -p /opt/sustainable-catalyst/backups/platform-core-v2670;stamp="$(date +%Y%m%d-%H%M%S)";docker exec -e PGPASSWORD="$DB_PASS" sc-postgres pg_dump -h 127.0.0.1 -U "$DB_USER" -d "$DB_NAME" -Fc > "/opt/sustainable-catalyst/backups/platform-core-v2670/core-${stamp}.dump";git rev-parse HEAD > "/opt/sustainable-catalyst/backups/platform-core-v2670/git-head-${stamp}.txt"
git fetch origin --tags; git pull --ff-only origin main; git tag --points-at HEAD | grep -qx 'v2.67.0' || { echo "STOP: production HEAD is not tagged v2.67.0"; exit 1; }
python3 -S scripts/validate_v2670_release.py
$COMPOSE build core
$COMPOSE run --rm --no-deps core python scripts/migrate.py | tee /tmp/sc-core-v2670-migrate.json
for t in "${V267_TABLES[@]}"; do [ "$(psqlq "SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema='public' AND table_name='$t');")" = t ] || { echo "STOP: $t missing after migration"; exit 1; }; done
[ "$(psqlq "SELECT EXISTS (SELECT 1 FROM schema_migrations WHERE version='0071');")" = t ] || { echo "STOP: migration 0071 not recorded"; exit 1; }
$COMPOSE up -d --no-deps --force-recreate core
for i in $(seq 1 40); do curl -fsS http://127.0.0.1:8090/health >/tmp/sc-core-v2670-health.json 2>/dev/null && break; sleep 2; done
curl -fsS http://127.0.0.1:8090/v1/visual-runtime/predictive/readiness | tee /tmp/sc-core-v2670-visual.json | python3 -m json.tool
python3 - <<'PY2'
import json
h=json.load(open('/tmp/sc-core-v2670-health.json'));r=json.load(open('/tmp/sc-core-v2670-visual.json'));assert h.get('ok') is True and h.get('version')=='2.67.0',h;assert r.get('release')=='2.67.0' and r.get('migration_0071_applied') is True,r
for k in ('visual_predictive_workspace_registry_by_core','visual_forecast_overlay_registry_by_core','visual_uncertainty_display_registry_by_core','visual_calibration_display_registry_by_core','visual_ensemble_comparison_registry_by_core','visual_monitoring_overlay_registry_by_core','visual_spatial_temporal_forecast_registry_by_core','visual_causal_predictive_overlay_registry_by_core','visual_decision_prediction_binding_registry_by_core','immutable_visual_predictive_snapshots_by_core'):assert r.get(k) is True,(k,r)
for k in ('forecast_execution_by_core','probabilistic_inference_by_core','calibration_computation_by_core','ensemble_combination_by_core','anomaly_detection_by_core','change_point_detection_by_core','spatial_prediction_by_core','counterfactual_execution_by_core','decision_optimization_by_core','visual_rendering_by_core','automatic_visual_inference'):assert r.get(k) is False,(k,r)
print('PASS - Platform Core v2.67.0 Visual Predictive Intelligence')
PY2
curl -fsS https://core.sustainablecatalyst.com/health | python3 -m json.tool
echo "PASS - PLATFORM CORE v2.67.0 BACKEND DEPLOYMENT COMPLETE"
