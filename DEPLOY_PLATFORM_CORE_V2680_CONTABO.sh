#!/usr/bin/env bash
set -euo pipefail
trap 'rc=$?; echo "ERROR: v2.68.0 deployment stopped at line $LINENO (exit $rc): $BASH_COMMAND" >&2; exit $rc' ERR
ROOT="${SC_CORE_ROOT:-/opt/sustainable-catalyst/core}"; COMPOSE="docker compose -f compose.yml -f compose.vps.yml"; cd "$ROOT"
echo "=== PLATFORM CORE v2.68.0 — VISUAL FORENSICS WORKBENCH ==="
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
[ "$(psqlq "SELECT EXISTS (SELECT 1 FROM schema_migrations WHERE version='0071');")" = t ] || { echo "STOP: migration 0071 missing; deploy v2.67.0 first"; exit 1; }
V267_TABLES=(visual_predictive_workspaces visual_forecast_overlays visual_uncertainty_displays visual_calibration_displays visual_ensemble_comparison_overlays visual_monitoring_overlays visual_spatial_temporal_forecast_layers visual_causal_predictive_overlays visual_decision_prediction_bindings visual_predictive_snapshots)
for t in "${V267_TABLES[@]}"; do [ "$(psqlq "SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema='public' AND table_name='$t');")" = t ] || { echo "STOP: predecessor table missing: $t"; exit 1; }; done
V268_TABLES=(visual_forensic_workspaces visual_forensic_evidence_bindings visual_forensic_claim_overlays visual_forensic_timeline_layers visual_forensic_spatial_temporal_layers visual_forensic_media_layers visual_forensic_reconstruction_bindings visual_forensic_documentary_bindings visual_forensic_graph_bindings visual_forensic_snapshots)
count=0; for t in "${V268_TABLES[@]}"; do [ "$(psqlq "SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema='public' AND table_name='$t');")" = t ] && count=$((count+1)); done
m72="$(psqlq "SELECT EXISTS (SELECT 1 FROM schema_migrations WHERE version='0072');")"
if [ "$m72" = f ] && [ "$count" -eq 0 ]; then echo "PASS: pristine pre-0072 state"; elif [ "$m72" = f ] && [ "$count" -eq 10 ]; then echo "PASS: recoverable partial-0072 state"; elif [ "$m72" = t ] && [ "$count" -eq 10 ]; then echo "PASS: already-complete 0072 state"; else echo "STOP: inconsistent 0072 state ($m72, $count/10)"; exit 1; fi
echo "=== BACKUP ==="; mkdir -p /opt/sustainable-catalyst/backups/platform-core-v2680; stamp="$(date +%Y%m%d-%H%M%S)"; docker exec -e PGPASSWORD="$DB_PASS" sc-postgres pg_dump -h 127.0.0.1 -U "$DB_USER" -d "$DB_NAME" -Fc > "/opt/sustainable-catalyst/backups/platform-core-v2680/core-${stamp}.dump"; git rev-parse HEAD > "/opt/sustainable-catalyst/backups/platform-core-v2680/git-head-${stamp}.txt"
git fetch origin --tags; git pull --ff-only origin main; git tag --points-at HEAD | grep -qx 'v2.68.0' || { echo "STOP: production HEAD is not tagged v2.68.0"; exit 1; }
python3 -S scripts/validate_v2680_release.py
$COMPOSE build core
$COMPOSE run --rm --no-deps core python scripts/migrate.py | tee /tmp/sc-core-v2680-migrate.json
for t in "${V268_TABLES[@]}"; do [ "$(psqlq "SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema='public' AND table_name='$t');")" = t ] || { echo "STOP: $t missing after migration"; exit 1; }; done
[ "$(psqlq "SELECT EXISTS (SELECT 1 FROM schema_migrations WHERE version='0072');")" = t ] || { echo "STOP: migration 0072 not recorded"; exit 1; }
$COMPOSE up -d --no-deps --force-recreate core
for i in $(seq 1 40); do curl -fsS http://127.0.0.1:8090/health >/tmp/sc-core-v2680-health.json 2>/dev/null && break; sleep 2; done
curl -fsS http://127.0.0.1:8090/v1/visual-runtime/forensics/readiness | tee /tmp/sc-core-v2680-visual.json | python3 -m json.tool
python3 - <<'PY2'
import json
h=json.load(open('/tmp/sc-core-v2680-health.json'));r=json.load(open('/tmp/sc-core-v2680-visual.json'));assert h.get('ok') is True and h.get('version')=='2.68.0',h;assert r.get('release')=='2.68.0' and r.get('migration_0072_applied') is True,r
for k in ('visual_forensic_workspace_registry_by_core','visual_forensic_evidence_binding_registry_by_core','visual_forensic_claim_overlay_registry_by_core','visual_forensic_timeline_registry_by_core','visual_forensic_spatial_temporal_registry_by_core','visual_forensic_media_registry_by_core','visual_forensic_reconstruction_registry_by_core','visual_forensic_documentary_registry_by_core','visual_forensic_graph_registry_by_core','immutable_visual_forensic_snapshots_by_core'):assert r.get(k) is True,(k,r)
for k in ('evidence_authentication_by_core','guilt_inference_by_core','automatic_reconstruction_by_core','media_forensics_execution_by_core','quantitative_reconstruction_execution_by_core','graph_inference_by_core','visual_rendering_by_core','automatic_visual_inference'):assert r.get(k) is False,(k,r)
print('PASS - Platform Core v2.68.0 Visual Forensics Workbench')
PY2
curl -fsS https://core.sustainablecatalyst.com/health | python3 -m json.tool
echo "PASS - PLATFORM CORE v2.68.0 BACKEND DEPLOYMENT COMPLETE"
