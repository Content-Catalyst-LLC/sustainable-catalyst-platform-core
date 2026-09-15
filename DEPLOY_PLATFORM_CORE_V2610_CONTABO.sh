#!/usr/bin/env bash
set -euo pipefail
trap 'rc=$?; echo "ERROR: v2.61.0 deployment stopped at line $LINENO (exit $rc): $BASH_COMMAND" >&2; exit $rc' ERR
ROOT="${SC_CORE_ROOT:-/opt/sustainable-catalyst/core}"; BACKUP_ROOT="${SC_CORE_BACKUP_ROOT:-/opt/sustainable-catalyst/backups}"; COMPOSE="docker compose -f compose.yml -f compose.vps.yml"; STAMP="$(date +%Y%m%d-%H%M%S)"; BACKUP="${BACKUP_ROOT}/platform-core-v2.61.0-${STAMP}"
cd "$ROOT"
echo "============================================================"; echo " PLATFORM CORE v2.61.0 — VISUAL REASONING RUNTIME & SCENE GRAPH"; echo "============================================================"
echo; echo "=== CURRENT LIVE HEALTH ==="; curl -fsS http://127.0.0.1:8090/health | python3 -m json.tool
echo; echo "=== SAFETY CHECKS ==="; [ -f compose.yml ] || { echo "STOP: compose.yml missing"; exit 1; }; [ -f compose.vps.yml ] || { echo "STOP: compose.vps.yml missing"; exit 1; }; [ -f .env.production ] || { echo "STOP: .env.production missing"; exit 1; }
if ! git diff --quiet || ! git diff --cached --quiet; then echo "STOP: tracked production files have local changes."; git status --short; exit 1; fi
$COMPOSE config >/tmp/sc-core-v2610-compose.yml; grep -q '/data/scientific-objects' /tmp/sc-core-v2610-compose.yml || { echo "STOP: scientific-object persistent mount missing"; exit 1; }
CORE_DB_URL="$(grep -m1 '^SC_CORE_DATABASE_URL=' .env.production | cut -d= -f2-)"; [ -n "$CORE_DB_URL" ] || { echo "STOP: SC_CORE_DATABASE_URL not found"; exit 1; }
eval "$(CORE_DB_URL="$CORE_DB_URL" python3 - <<'PY2'
import os,shlex
from urllib.parse import urlparse,unquote
u=urlparse(os.environ['CORE_DB_URL'].strip().strip('"').strip("'")); print('DB_USER='+shlex.quote(unquote(u.username or ''))); print('DB_PASS='+shlex.quote(unquote(u.password or ''))); print('DB_NAME='+shlex.quote((u.path or '').lstrip('/')))
PY2
)"
psqlq(){ docker exec -e PGPASSWORD="$DB_PASS" sc-postgres psql -h 127.0.0.1 -U "$DB_USER" -d "$DB_NAME" -Atqc "$1"; }
echo; echo "=== PRODUCTION PREDECESSOR PREFLIGHT ==="
M64="$(psqlq "SELECT EXISTS (SELECT 1 FROM schema_migrations WHERE version='0064');")"; echo "schema_migrations.0064=$M64"; [ "$M64" = t ] || { echo "STOP: migration 0064 is not recorded; v2.60.0 must be deployed first"; exit 1; }
V260_TABLES=(predictive_intelligence_packages predictive_intelligence_package_components predictive_intelligence_package_artifacts predictive_intelligence_package_environments predictive_intelligence_package_verifications predictive_intelligence_package_reviews predictive_intelligence_package_snapshots)
for t in "${V260_TABLES[@]}"; do v="$(psqlq "SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema='public' AND table_name='$t');")"; echo "$t=$v"; [ "$v" = t ] || { echo "STOP: predecessor v2.60 table missing: $t"; exit 1; }; done
V261_TABLES=(visual_runtime_scenes visual_runtime_layers visual_runtime_nodes visual_runtime_edges visual_runtime_annotations visual_runtime_views visual_runtime_bindings visual_runtime_snapshots)
v261_count=0
for t in "${V261_TABLES[@]}"; do v="$(psqlq "SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema='public' AND table_name='$t');")"; echo "$t=$v"; [ "$v" = t ] && v261_count=$((v261_count+1)); done
M65="$(psqlq "SELECT EXISTS (SELECT 1 FROM schema_migrations WHERE version='0065');")"; echo "schema_migrations.0065=$M65"; echo "visual_runtime_tables_present=$v261_count/8"
if [ "$M65" = f ] && [ "$v261_count" -eq 0 ]; then echo "PASS: pristine pre-0065 visual-runtime state accepted"; elif [ "$M65" = f ] && [ "$v261_count" -eq 8 ]; then echo "PASS: safe partial-0065 table state detected and accepted"; elif [ "$M65" = t ] && [ "$v261_count" -eq 8 ]; then echo "PASS: migration 0065 already recorded with complete visual-runtime schema"; else echo "STOP: inconsistent v2.61 migration state (0065=$M65, tables=$v261_count/8)"; exit 1; fi
echo; echo "=== BACKUP CURRENT CORE + DATABASE ==="; mkdir -p "$BACKUP"; tar --exclude='.git' -czf "$BACKUP/core-before-v2.61.0.tar.gz" .; docker exec -e PGPASSWORD="$DB_PASS" sc-postgres pg_dump -h 127.0.0.1 -U "$DB_USER" -d "$DB_NAME" -Fc > "$BACKUP/platform-core-before-v2.61.0.dump"; ls -lh "$BACKUP"/*
echo; echo "=== FETCH EXACT v2.61.0 RELEASE ==="; git fetch origin --tags; git rev-parse v2.61.0 >/dev/null 2>&1 || { echo "STOP: v2.61.0 tag is not available from GitHub"; exit 1; }; git pull --ff-only origin main; echo "HEAD: $(git log -1 --oneline)"; git tag --points-at HEAD | grep -qx 'v2.61.0' || { echo "STOP: production HEAD is not exactly tagged v2.61.0"; exit 1; }
head_commit="$(git rev-parse HEAD)"; tag_commit="$(git rev-list -n 1 v2.61.0)"; [ "$head_commit" = "$tag_commit" ] || { echo "STOP: v2.61.0 does not resolve to production HEAD"; exit 1; }
python3 -S scripts/validate_v2610_release.py
echo; echo "=== BUILD CORE v2.61.0 ==="; $COMPOSE build core
echo; echo "=== APPLY / REPAIR MIGRATION 0065 ==="; $COMPOSE run --rm --no-deps core python scripts/migrate.py | tee /tmp/sc-core-v2610-migrations.json
echo; echo "=== VERIFY DATABASE CONTRACT BEFORE RECREATE ==="
for t in "${V261_TABLES[@]}"; do [ "$(psqlq "SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema='public' AND table_name='$t');")" = t ] || { echo "STOP: $t missing after migration 0065"; exit 1; }; done
M65_POST="$(psqlq "SELECT EXISTS (SELECT 1 FROM schema_migrations WHERE version='0065');")"; [ "$M65_POST" = t ] || { echo "STOP: migration 0065 not recorded"; exit 1; }; D65_LEN="$(psqlq "SELECT length(description) FROM schema_migrations WHERE version='0065';")"; echo "schema_migrations.0065.description_length=$D65_LEN"; [ "$D65_LEN" -le 300 ] || { echo "STOP: stored 0065 description exceeds production contract"; exit 1; }
echo "PASS: migration 0065 complete; v2.60 reproducible predictive package schema preserved"
echo; echo "=== RECREATE sc-core ==="; $COMPOSE up -d --no-deps --force-recreate core
for i in $(seq 1 40); do if curl -fsS http://127.0.0.1:8090/health >/tmp/sc-core-v2610-health.json 2>/dev/null; then break; fi; [ "$i" -lt 40 ] || { docker logs --tail 200 sc-core; exit 1; }; sleep 2; done
for i in $(seq 1 40); do state="$(docker inspect --format '{{if .State.Health}}{{.State.Health.Status}}{{else}}none{{end}}' sc-core)"; echo "health=$state"; [ "$state" = healthy ] && break; [ "$state" != unhealthy ] || { docker logs --tail 200 sc-core; exit 1; }; [ "$i" -lt 40 ] || { docker logs --tail 200 sc-core; exit 1; }; sleep 2; done
echo; echo "=== LIVE HEALTH ==="; python3 -m json.tool </tmp/sc-core-v2610-health.json
echo; echo "=== VISUAL RUNTIME READINESS ==="; curl -fsS http://127.0.0.1:8090/v1/visual-runtime/readiness | tee /tmp/sc-core-v2610-visual.json | python3 -m json.tool
python3 - <<'PY2'
import json
h=json.load(open('/tmp/sc-core-v2610-health.json')); r=json.load(open('/tmp/sc-core-v2610-visual.json'))
assert h.get('ok') is True and h.get('version')=='2.61.0',h
assert r.get('release')=='2.61.0' and r.get('migration_0065_applied') is True,r
for key in ('scene_registry_by_core','scene_graph_node_registry_by_core','scene_graph_edge_registry_by_core','scene_layer_registry_by_core','scene_annotation_registry_by_core','viewport_selection_state_by_core','cross_product_visual_bindings_by_core','immutable_scene_snapshots_by_core','renderer_neutral_scene_contract_by_core'): assert r.get(key) is True,(key,r)
for key in ('layout_computation_by_core','canvas_svg_webgl_rendering_by_core','animation_execution_by_core','gpu_execution_by_core','hit_testing_by_core','visual_inference_by_core','automatic_visual_truth_promotion'): assert r.get(key) is False,(key,r)
print('PASS: Platform Core v2.61.0'); print('PASS: Visual Reasoning Runtime & Scene Graph'); print('PASS: migration 0065 additive with renderer-neutral boundaries intact')
PY2
echo; echo "=== VERIFY MIGRATION STATE ==="; docker exec sc-core python scripts/migrate.py | tee /tmp/sc-core-v2610-migration-state.json
python3 - <<'PY2'
import json
m=json.load(open('/tmp/sc-core-v2610-migration-state.json')); assert '0065' in m.get('applied',[]) and m.get('pending')==[],m; print('PASS: migration 0065 applied and pending=[]')
PY2
echo; echo "=== PERSISTENT SCIENTIFIC STORAGE ==="; docker exec sc-core sh -lc 'test -d /data/scientific-objects; touch /data/scientific-objects/.v2610-write-test; rm /data/scientific-objects/.v2610-write-test; echo "PASS: persistent scientific-object storage writable"'
echo; echo "=== PUBLIC CADDY ROUTE ==="; curl -fsS https://core.sustainablecatalyst.com/health | python3 -c 'import json,sys;d=json.load(sys.stdin);assert d.get("version")=="2.61.0",d;print("PASS: public Core health 2.61.0")'; curl -fsS https://core.sustainablecatalyst.com/v1/visual-runtime/readiness | python3 -c 'import json,sys;d=json.load(sys.stdin);assert d.get("release")=="2.61.0" and d.get("migration_0065_applied") is True,d;print("PASS: public Visual Reasoning Runtime readiness")'
echo; echo "=== FINAL CONTAINER ==="; docker ps --filter name=sc-core --format 'table {{.Names}}\t{{.Image}}\t{{.Status}}\t{{.Ports}}'
echo "Backup retained at: $BACKUP"
echo "============================================================"; echo " PLATFORM CORE v2.61.0 BACKEND DEPLOYMENT COMPLETE"; echo "============================================================"
