#!/usr/bin/env bash
set -euo pipefail
trap 'rc=$?; echo "ERROR: v2.38.0 Contabo deployment stopped at line $LINENO (exit $rc): $BASH_COMMAND" >&2; exit $rc' ERR
ROOT="/opt/sustainable-catalyst/core"; BACKUP_ROOT="/opt/sustainable-catalyst/backups"; COMPOSE="docker compose -f compose.yml -f compose.vps.yml"; STAMP="$(date +%Y%m%d-%H%M%S)"; BACKUP="${BACKUP_ROOT}/platform-core-v2.38.0-${STAMP}"
cd "$ROOT"
echo "============================================================"; echo " PLATFORM CORE v2.38.0 — SPATIAL & TEMPORAL VISUAL REASONING"; echo "============================================================"
echo; echo "=== CURRENT LIVE HEALTH ==="; curl -fsS http://127.0.0.1:8090/health | python3 -m json.tool
echo; echo "=== SAFETY CHECKS ==="; [ -f compose.yml ] || { echo "STOP: compose.yml missing"; exit 1; }; [ -f compose.vps.yml ] || { echo "STOP: compose.vps.yml missing"; exit 1; }; [ -f .env.production ] || { echo "STOP: .env.production missing"; exit 1; }
if ! git diff --quiet || ! git diff --cached --quiet; then echo "STOP: tracked production files have local changes."; git status --short; exit 1; fi
$COMPOSE config >/tmp/sc-core-v2380-compose.yml; grep -q '/data/scientific-objects' /tmp/sc-core-v2380-compose.yml || { echo "STOP: scientific-object persistent mount missing"; exit 1; }
CORE_DB_URL="$(grep -m1 '^SC_CORE_DATABASE_URL=' .env.production | cut -d= -f2-)"; [ -n "$CORE_DB_URL" ] || { echo "STOP: SC_CORE_DATABASE_URL not found"; exit 1; }
eval "$(CORE_DB_URL="$CORE_DB_URL" python3 - <<'PY2'
import os,shlex
from urllib.parse import urlparse,unquote
u=urlparse(os.environ['CORE_DB_URL'].strip().strip('"').strip("'")); print('DB_USER='+shlex.quote(unquote(u.username or ''))); print('DB_PASS='+shlex.quote(unquote(u.password or ''))); print('DB_NAME='+shlex.quote((u.path or '').lstrip('/')))
PY2
)"
psqlq(){ docker exec -e PGPASSWORD="$DB_PASS" sc-postgres psql -h 127.0.0.1 -U "$DB_USER" -d "$DB_NAME" -Atqc "$1"; }
echo; echo "=== PRODUCTION PREDECESSOR PREFLIGHT ==="
M41="$(psqlq "SELECT EXISTS (SELECT 1 FROM schema_migrations WHERE version='0041');")"; echo "schema_migrations.0041=$M41"; [ "$M41" = t ] || { echo "STOP: migration 0041 is not recorded; v2.37.0.2 must be deployed first"; exit 1; }
for t in causal_graphs causal_variables causal_edges causal_interventions causal_identifications causal_estimates causal_diagnostics; do v="$(psqlq "SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema='public' AND table_name='$t');")"; echo "$t=$v"; [ "$v" = t ] || { echo "STOP: predecessor causal table missing: $t"; exit 1; }; done
SPATIAL_TABLES=(spatial_temporal_scenes spatial_temporal_features spatial_temporal_events spatial_temporal_trajectories spatial_temporal_trajectory_points spatial_temporal_changes spatial_temporal_views)
spatial_count=0
for t in "${SPATIAL_TABLES[@]}"; do v="$(psqlq "SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema='public' AND table_name='$t');")"; echo "$t=$v"; [ "$v" = t ] && spatial_count=$((spatial_count+1)); done
M42="$(psqlq "SELECT EXISTS (SELECT 1 FROM schema_migrations WHERE version='0042');")"; echo "schema_migrations.0042=$M42"; echo "spatial_temporal_tables_present=$spatial_count/7"
if [ "$M42" = f ] && [ "$spatial_count" -eq 0 ]; then echo "PASS: pristine pre-0042 spatial-temporal state accepted";
elif [ "$M42" = f ] && [ "$spatial_count" -eq 7 ]; then echo "PASS: safe partial-0042 spatial-temporal table state detected and accepted";
elif [ "$M42" = t ] && [ "$spatial_count" -eq 7 ]; then echo "PASS: migration 0042 already recorded with complete spatial-temporal schema";
else echo "STOP: inconsistent spatial-temporal migration state (0042=$M42, tables=$spatial_count/7)"; exit 1; fi

echo; echo "=== BACKUP CURRENT CORE + DATABASE ==="; mkdir -p "$BACKUP"; tar --exclude='.git' -czf "$BACKUP/core-before-v2.38.0.tar.gz" .; docker exec -e PGPASSWORD="$DB_PASS" sc-postgres pg_dump -h 127.0.0.1 -U "$DB_USER" -d "$DB_NAME" -Fc > "$BACKUP/platform-core-before-v2.38.0.dump"; ls -lh "$BACKUP"/*
echo; echo "=== FETCH EXACT v2.38.0 RELEASE ==="; git fetch origin --tags; git rev-parse v2.38.0 >/dev/null 2>&1 || { echo "STOP: v2.38.0 tag is not available from GitHub"; exit 1; }; git pull --ff-only origin main; echo "HEAD: $(git log -1 --oneline)"; git tag --points-at HEAD | grep -qx 'v2.38.0' || { echo "STOP: production HEAD is not exactly tagged v2.38.0"; exit 1; }
head_commit="$(git rev-parse HEAD)"; tag_commit="$(git rev-list -n 1 v2.38.0)"; [ "$head_commit" = "$tag_commit" ] || { echo "STOP: v2.38.0 does not resolve to production HEAD"; exit 1; }
python3 - <<'PY2'
import ast,re
from pathlib import Path
mig=Path('backend/app/migrations.py'); tree=ast.parse(mig.read_text(),filename=str(mig)); migrations=None
for node in tree.body:
    if isinstance(node,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='MIGRATIONS' for t in node.targets): migrations=ast.literal_eval(node.value); break
assert migrations and migrations[-1][0]=='0042',migrations[-1]
models=Path('backend/app/models.py').read_text(); m=re.search(r'class\s+SchemaMigration\b.*?description:\s*Mapped\[str\]\s*=\s*mapped_column\(String\((\d+)\)',models,re.S); assert m
mx=int(m.group(1)); d=dict(migrations)['0042']; assert mx==300 and len(d)<=mx,(mx,len(d)); print(f'PASS: packaged 0042 migration description fits VARCHAR({mx}) at {len(d)} chars')
PY2
echo; echo "=== BUILD CORE v2.38.0 ==="; $COMPOSE build core
echo; echo "=== APPLY / REPAIR MIGRATION 0042 ==="; $COMPOSE run --rm --no-deps core python scripts/migrate.py | tee /tmp/sc-core-v2380-migrations.json
echo; echo "=== VERIFY DATABASE CONTRACT BEFORE RECREATE ==="; for t in "${SPATIAL_TABLES[@]}"; do [ "$(psqlq "SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema='public' AND table_name='$t');")" = t ] || { echo "STOP: $t missing after migration 0042"; exit 1; }; done
M42_POST="$(psqlq "SELECT EXISTS (SELECT 1 FROM schema_migrations WHERE version='0042');")"; [ "$M42_POST" = t ] || { echo "STOP: migration 0042 not recorded"; exit 1; }; D42_LEN="$(psqlq "SELECT length(description) FROM schema_migrations WHERE version='0042';")"; echo "schema_migrations.0042.description_length=$D42_LEN"; [ "$D42_LEN" -le 300 ] || { echo "STOP: stored 0042 description exceeds production contract"; exit 1; }; echo "PASS: migration 0042 complete; predecessor schema preserved"
echo; echo "=== RECREATE sc-core ==="; $COMPOSE up -d --no-deps --force-recreate core
for i in $(seq 1 40); do if curl -fsS http://127.0.0.1:8090/health >/tmp/sc-core-v2380-health.json 2>/dev/null; then break; fi; [ "$i" -lt 40 ] || { docker logs --tail 200 sc-core; exit 1; }; sleep 2; done
for i in $(seq 1 40); do state="$(docker inspect --format '{{if .State.Health}}{{.State.Health.Status}}{{else}}none{{end}}' sc-core)"; echo "health=$state"; [ "$state" = healthy ] && break; [ "$state" != unhealthy ] || { docker logs --tail 200 sc-core; exit 1; }; [ "$i" -lt 40 ] || { docker logs --tail 200 sc-core; exit 1; }; sleep 2; done
echo; echo "=== LIVE HEALTH ==="; python3 -m json.tool </tmp/sc-core-v2380-health.json
echo; echo "=== SPATIAL-TEMPORAL READINESS ==="; curl -fsS http://127.0.0.1:8090/v1/spatial-temporal/readiness | tee /tmp/sc-core-v2380-spatial.json | python3 -m json.tool
python3 - <<'PY2'
import json
h=json.load(open('/tmp/sc-core-v2380-health.json')); s=json.load(open('/tmp/sc-core-v2380-spatial.json'))
assert h.get('ok') is True and h.get('version')=='2.38.0',h
assert h.get('spatial_temporal_visual_reasoning') is True,h
assert s.get('release')=='2.38.0' and s.get('migration_0042_applied') is True,s
assert s.get('renderer_neutral') is True and s.get('spatial_analysis_by_core') is False and s.get('raster_processing_by_core') is False and s.get('remote_sensing_by_core') is False and s.get('temporal_model_execution_by_core') is False and s.get('automatic_truth_promotion') is False,s
print('PASS: Platform Core v2.38.0'); print('PASS: Spatial & Temporal Visual Reasoning'); print('PASS: migration 0042 additive with execution boundaries intact')
PY2
echo; echo "=== VERIFY MIGRATION STATE ==="; docker exec sc-core python scripts/migrate.py | tee /tmp/sc-core-v2380-migration-state.json
python3 - <<'PY2'
import json
m=json.load(open('/tmp/sc-core-v2380-migration-state.json')); assert '0042' in m.get('applied',[]) and m.get('pending')==[],m; print('PASS: migration 0042 applied and pending=[]')
PY2
echo; echo "=== VERIFY PERSISTENT SCIENTIFIC STORAGE MOUNT ==="; docker exec sc-core sh -lc 'test -d /data/scientific-objects; touch /data/scientific-objects/.v2380-write-test; rm /data/scientific-objects/.v2380-write-test; echo "PASS: persistent scientific-object storage writable"'
echo; echo "=== PUBLIC CADDY ROUTE ==="; curl -fsS https://core.sustainablecatalyst.com/health | python3 -c 'import json,sys;d=json.load(sys.stdin);assert d.get("version")=="2.38.0",d;print("PASS: public Core health 2.38.0")'; curl -fsS https://core.sustainablecatalyst.com/v1/spatial-temporal/readiness | python3 -c 'import json,sys;d=json.load(sys.stdin);assert d.get("release")=="2.38.0" and d.get("migration_0042_applied") is True,d;print("PASS: public Spatial-Temporal readiness")'
echo; echo "=== FINAL CONTAINER ==="; docker ps --filter name=sc-core --format 'table {{.Names}}\t{{.Image}}\t{{.Status}}\t{{.Ports}}'; echo; echo "Backup retained at: $BACKUP"; echo "============================================================"; echo " PLATFORM CORE v2.38.0 BACKEND DEPLOYMENT COMPLETE"; echo "============================================================"
