#!/usr/bin/env bash
set -euo pipefail
trap 'rc=$?; echo "ERROR: v2.37.0 Contabo deployment stopped at line $LINENO (exit $rc): $BASH_COMMAND" >&2; exit $rc' ERR
ROOT="/opt/sustainable-catalyst/core"; BACKUP_ROOT="/opt/sustainable-catalyst/backups"; COMPOSE="docker compose -f compose.yml -f compose.vps.yml"; STAMP="$(date +%Y%m%d-%H%M%S)"; BACKUP="${BACKUP_ROOT}/platform-core-v2.37.0-${STAMP}"
cd "$ROOT"
echo "============================================================"; echo " PLATFORM CORE v2.37.0 — CAUSAL SYSTEMS EXPLORER"; echo "============================================================"
echo; echo "=== CURRENT LIVE HEALTH ==="; curl -fsS http://127.0.0.1:8090/health | python3 -m json.tool
echo; echo "=== SAFETY CHECKS ==="
[ -f compose.yml ] || { echo "STOP: compose.yml missing"; exit 1; }; [ -f compose.vps.yml ] || { echo "STOP: compose.vps.yml missing"; exit 1; }; [ -f .env.production ] || { echo "STOP: .env.production missing"; exit 1; }
if ! git diff --quiet || ! git diff --cached --quiet; then echo "STOP: tracked production files have local changes."; git status --short; exit 1; fi
$COMPOSE config >/tmp/sc-core-v2370-compose.yml; grep -q '/data/scientific-objects' /tmp/sc-core-v2370-compose.yml || { echo "STOP: scientific-object persistent mount missing"; exit 1; }
CORE_DB_URL="$(grep -m1 '^SC_CORE_DATABASE_URL=' .env.production | cut -d= -f2-)"; [ -n "$CORE_DB_URL" ] || { echo "STOP: SC_CORE_DATABASE_URL not found"; exit 1; }
eval "$(CORE_DB_URL="$CORE_DB_URL" python3 - <<'PY'
import os,shlex
from urllib.parse import urlparse,unquote
u=urlparse(os.environ['CORE_DB_URL'].strip().strip('"').strip("'")); print('DB_USER='+shlex.quote(unquote(u.username or ''))); print('DB_PASS='+shlex.quote(unquote(u.password or ''))); print('DB_NAME='+shlex.quote((u.path or '').lstrip('/')))
PY
)"
psqlq(){ docker exec -e PGPASSWORD="$DB_PASS" sc-postgres psql -h 127.0.0.1 -U "$DB_USER" -d "$DB_NAME" -Atqc "$1"; }
echo; echo "=== PRODUCTION SCHEMA PREFLIGHT ==="
for check in \
 "sensitivity_studies:id" \
 "sensitivity_factors:study_id" \
 "sensitivity_measures:id" \
 "ensembles:id" \
 "uncertainty_compute_runs:sensitivity_study_id" \
 "uncertainty_compute_runs:ensemble_id"; do
  t="${check%%:*}"; c="${check##*:}"; v="$(psqlq "SELECT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema='public' AND table_name='$t' AND column_name='$c');")"; echo "$t.$c=$v"; [ "$v" = t ] || { echo "STOP: required production schema column missing: $t.$c"; exit 1; }
done
BAD="$(psqlq "SELECT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema='public' AND table_name='sensitivity_studies' AND column_name='visual_entity_id');")"; echo "sensitivity_studies.visual_entity_id=$BAD"; [ "$BAD" = f ] || { echo "STOP: incompatible sensitivity schema detected"; exit 1; }
M40="$(psqlq "SELECT EXISTS (SELECT 1 FROM schema_migrations WHERE version='0040');")"; echo "schema_migrations.0040=$M40"; [ "$M40" = t ] || { echo "STOP: migration 0040 is not recorded; deploy v2.36.1.2 first"; exit 1; }
echo "PASS: deployed v2.36.1.2 uncertainty schema and migration 0040 confirmed"
echo; echo "=== BACKUP CURRENT CORE + DATABASE ==="; mkdir -p "$BACKUP"; tar --exclude='.git' -czf "$BACKUP/core-before-v2.37.0.tar.gz" .; docker exec -e PGPASSWORD="$DB_PASS" sc-postgres pg_dump -h 127.0.0.1 -U "$DB_USER" -d "$DB_NAME" -Fc > "$BACKUP/platform-core-before-v2.37.0.dump"; ls -lh "$BACKUP"/*
echo; echo "=== FETCH EXACT v2.37.0 RELEASE ==="; git fetch origin --tags; git rev-parse v2.37.0 >/dev/null 2>&1 || { echo "STOP: v2.37.0 tag is not available from GitHub"; exit 1; }; git pull --ff-only origin main; echo "HEAD: $(git log -1 --oneline)"; git tag --points-at HEAD | grep -qx 'v2.37.0' || { echo "STOP: production HEAD is not exactly tagged v2.37.0"; exit 1; }
echo; echo "=== BUILD CORE v2.37.0 ==="; $COMPOSE build core
echo; echo "=== APPLY ADDITIVE MIGRATION 0041 ==="; $COMPOSE run --rm --no-deps core python scripts/migrate.py | tee /tmp/sc-core-v2370-migrations.json
echo; echo "=== VERIFY DATABASE CONTRACT BEFORE RECREATE ==="
[ "$(psqlq "SELECT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema='public' AND table_name='sensitivity_studies' AND column_name='id');")" = t ]; [ "$(psqlq "SELECT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema='public' AND table_name='sensitivity_studies' AND column_name='visual_entity_id');")" = f ]
for t in causal_graphs causal_variables causal_edges causal_interventions causal_identifications causal_estimates causal_diagnostics; do [ "$(psqlq "SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema='public' AND table_name='$t');")" = t ] || { echo "STOP: $t missing after migration 0041"; exit 1; }; done
echo "PASS: migration 0041 is additive and causal-system tables exist"
echo; echo "=== RECREATE sc-core ==="; $COMPOSE up -d --no-deps --force-recreate core
for i in $(seq 1 40); do if curl -fsS http://127.0.0.1:8090/health >/tmp/sc-core-v2370-health.json 2>/dev/null; then break; fi; [ "$i" -lt 40 ] || { docker logs --tail 200 sc-core; exit 1; }; sleep 2; done
for i in $(seq 1 40); do state="$(docker inspect --format '{{if .State.Health}}{{.State.Health.Status}}{{else}}none{{end}}' sc-core)"; echo "health=$state"; [ "$state" = healthy ] && break; [ "$state" != unhealthy ] || { docker logs --tail 200 sc-core; exit 1; }; [ "$i" -lt 40 ] || { docker logs --tail 200 sc-core; exit 1; }; sleep 2; done
echo; echo "=== LIVE HEALTH ==="; python3 -m json.tool </tmp/sc-core-v2370-health.json
echo; echo "=== CAUSAL SYSTEMS READINESS ==="; curl -fsS http://127.0.0.1:8090/v1/causal-systems/readiness | tee /tmp/sc-core-v2370-causal.json | python3 -m json.tool
python3 - <<'PY'
import json
h=json.load(open('/tmp/sc-core-v2370-health.json')); c=json.load(open('/tmp/sc-core-v2370-causal.json'))
assert h.get('ok') is True and h.get('version')=='2.37.0',h
assert h.get('causal_systems_explorer') is True,h
assert c.get('release')=='2.37.0' and c.get('migration_0041_applied') is True,c
assert c.get('dag_validation_by_core') is True and c.get('path_reasoning_by_core') is True and c.get('adjustment_candidates_by_core') is True,c
assert c.get('automatic_causal_identification') is False and c.get('automatic_effect_estimation') is False and c.get('automatic_truth_promotion') is False,c
print('PASS: Platform Core v2.37.0'); print('PASS: Causal Systems Explorer')
PY
echo; echo "=== VERIFY MIGRATION STATE ==="; docker exec sc-core python scripts/migrate.py | tee /tmp/sc-core-v2370-migration-state.json
python3 - <<'PY'
import json
m=json.load(open('/tmp/sc-core-v2370-migration-state.json')); assert '0041' in m.get('applied',[]) and m.get('pending')==[],m; print('PASS: migration 0041 applied and pending=[]')
PY
echo; echo "=== VERIFY PERSISTENT SCIENTIFIC STORAGE MOUNT ==="; docker inspect sc-core --format '{{json .Mounts}}' | python3 -m json.tool; docker exec sc-core sh -lc 'test -d /data/scientific-objects; touch /data/scientific-objects/.v2370-write-test; rm /data/scientific-objects/.v2370-write-test; echo "PASS: persistent scientific-object storage writable"'
echo; echo "=== PUBLIC CADDY ROUTE ==="; curl -fsS https://core.sustainablecatalyst.com/health | python3 -c 'import json,sys;d=json.load(sys.stdin);assert d.get("version")=="2.37.0",d;print("PASS: public Core health 2.37.0")'; curl -fsS https://core.sustainablecatalyst.com/v1/causal-systems/readiness | python3 -c 'import json,sys;d=json.load(sys.stdin);assert d.get("migration_0041_applied") is True,d;print("PASS: public Causal Systems readiness")'
echo; echo "=== FINAL CONTAINER ==="; docker ps --filter name=sc-core --format 'table {{.Names}}\t{{.Image}}\t{{.Status}}\t{{.Ports}}'; echo; echo "Backup retained at: $BACKUP"; echo "============================================================"; echo " PLATFORM CORE v2.37.0 BACKEND DEPLOYMENT COMPLETE"; echo "============================================================"
