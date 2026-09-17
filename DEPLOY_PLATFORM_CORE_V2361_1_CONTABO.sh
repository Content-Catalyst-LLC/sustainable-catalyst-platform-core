#!/usr/bin/env bash
set -euo pipefail
trap 'rc=$?; echo "ERROR: v2.36.1.1 Contabo deployment stopped at line $LINENO (exit $rc): $BASH_COMMAND" >&2; exit $rc' ERR
ROOT="/opt/sustainable-catalyst/core"
BACKUP_ROOT="/opt/sustainable-catalyst/backups"
COMPOSE="docker compose -f compose.yml -f compose.vps.yml"
STAMP="$(date +%Y%m%d-%H%M%S)"
BACKUP="${BACKUP_ROOT}/platform-core-v2.36.1.1-${STAMP}"
cd "$ROOT"
echo "============================================================"
echo " PLATFORM CORE v2.36.1.1 — PRODUCTION SCHEMA REPAIR"
echo "============================================================"
echo; echo "=== CURRENT LIVE HEALTH ==="
curl -fsS http://127.0.0.1:8090/health | python3 -m json.tool
echo; echo "=== SAFETY CHECKS ==="
[ -f compose.yml ] || { echo "STOP: compose.yml missing"; exit 1; }
[ -f compose.vps.yml ] || { echo "STOP: compose.vps.yml missing"; exit 1; }
[ -f .env.production ] || { echo "STOP: .env.production missing"; exit 1; }
if ! git diff --quiet || ! git diff --cached --quiet; then
  echo "STOP: tracked production files have local changes."
  git status --short
  exit 1
fi
$COMPOSE config >/tmp/sc-core-v2361-1-compose.yml
grep -q '/data/scientific-objects' /tmp/sc-core-v2361-1-compose.yml || { echo "STOP: scientific-object persistent mount missing"; exit 1; }
CORE_DB_URL="$(grep -m1 '^SC_CORE_DATABASE_URL=' .env.production | cut -d= -f2-)"
[ -n "$CORE_DB_URL" ] || { echo "STOP: SC_CORE_DATABASE_URL not found"; exit 1; }
eval "$(CORE_DB_URL="$CORE_DB_URL" python3 - <<'PY'
import os,shlex
from urllib.parse import urlparse,unquote
u=urlparse(os.environ['CORE_DB_URL'].strip().strip('"').strip("'"))
print('DB_USER='+shlex.quote(unquote(u.username or '')))
print('DB_PASS='+shlex.quote(unquote(u.password or '')))
print('DB_NAME='+shlex.quote((u.path or '').lstrip('/')))
PY
)"
psqlq(){ docker exec -e PGPASSWORD="$DB_PASS" sc-postgres psql -h 127.0.0.1 -U "$DB_USER" -d "$DB_NAME" -Atqc "$1"; }
echo; echo "=== PRODUCTION SCHEMA COMPATIBILITY PREFLIGHT ==="
HAS_STUDY_ID="$(psqlq "SELECT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema='public' AND table_name='sensitivity_studies' AND column_name='id');")"
HAS_STUDY_VISUAL="$(psqlq "SELECT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema='public' AND table_name='sensitivity_studies' AND column_name='visual_entity_id');")"
HAS_MEASURES="$(psqlq "SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema='public' AND table_name='sensitivity_measures');")"
HAS_FACTOR_STUDY="$(psqlq "SELECT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema='public' AND table_name='sensitivity_factors' AND column_name='study_id');")"
HAS_ENSEMBLE_ID="$(psqlq "SELECT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema='public' AND table_name='ensembles' AND column_name='id');")"
echo "sensitivity_studies.id=$HAS_STUDY_ID"
echo "sensitivity_studies.visual_entity_id=$HAS_STUDY_VISUAL"
echo "sensitivity_measures=$HAS_MEASURES"
echo "sensitivity_factors.study_id=$HAS_FACTOR_STUDY"
echo "ensembles.id=$HAS_ENSEMBLE_ID"
[ "$HAS_STUDY_ID" = t ] || { echo "STOP: expected v2.36.0 sensitivity_studies.id missing"; exit 1; }
[ "$HAS_STUDY_VISUAL" = f ] || { echo "STOP: unexpected incompatible sensitivity_studies.visual_entity_id exists"; exit 1; }
[ "$HAS_MEASURES" = t ] || { echo "STOP: expected v2.36.0 sensitivity_measures table missing"; exit 1; }
[ "$HAS_FACTOR_STUDY" = t ] || { echo "STOP: expected v2.36.0 sensitivity_factors.study_id missing"; exit 1; }
[ "$HAS_ENSEMBLE_ID" = t ] || { echo "STOP: expected v2.36.0 ensembles.id missing"; exit 1; }
echo "PASS: deployed v2.36.0 uncertainty schema confirmed"
echo; echo "=== BACKUP CURRENT CORE + DATABASE ==="
mkdir -p "$BACKUP"
tar --exclude='.git' -czf "$BACKUP/core-before-v2.36.1.1.tar.gz" .
docker exec -e PGPASSWORD="$DB_PASS" sc-postgres pg_dump -h 127.0.0.1 -U "$DB_USER" -d "$DB_NAME" -Fc > "$BACKUP/platform-core-before-v2.36.1.1.dump"
ls -lh "$BACKUP"/*
echo; echo "=== FETCH EXACT v2.36.1.1 RELEASE ==="
git fetch origin --tags
git rev-parse v2.36.1.1 >/dev/null 2>&1 || { echo "STOP: v2.36.1.1 tag is not available from GitHub"; exit 1; }
git pull --ff-only origin main
echo "HEAD: $(git log -1 --oneline)"
git tag --points-at HEAD | grep -qx 'v2.36.1.1' || { echo "STOP: production HEAD is not exactly tagged v2.36.1.1"; exit 1; }
echo; echo "=== BUILD CORE v2.36.1.1 ==="
$COMPOSE build core
echo; echo "=== APPLY ADDITIVE MIGRATION 0040 ==="
$COMPOSE run --rm --no-deps core python scripts/migrate.py | tee /tmp/sc-core-v2361-1-migrations.json
echo; echo "=== VERIFY DATABASE CONTRACT BEFORE RECREATE ==="
[ "$(psqlq "SELECT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema='public' AND table_name='sensitivity_studies' AND column_name='id');")" = t ]
[ "$(psqlq "SELECT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema='public' AND table_name='sensitivity_studies' AND column_name='visual_entity_id');")" = f ]
[ "$(psqlq "SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema='public' AND table_name='sensitivity_measures');")" = t ]
[ "$(psqlq "SELECT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema='public' AND table_name='uncertainty_compute_runs' AND column_name='sensitivity_study_id');")" = t ]
[ "$(psqlq "SELECT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema='public' AND table_name='uncertainty_compute_runs' AND column_name='ensemble_id');")" = t ]
echo "PASS: migration 0040 is additive and v2.36.0 schema remains intact"
echo; echo "=== RECREATE sc-core ==="
$COMPOSE up -d --no-deps --force-recreate core
for i in $(seq 1 40); do
  if curl -fsS http://127.0.0.1:8090/health >/tmp/sc-core-v2361-1-health.json 2>/dev/null; then break; fi
  [ "$i" -lt 40 ] || { docker logs --tail 200 sc-core; exit 1; }
  sleep 2
done
for i in $(seq 1 40); do
  state="$(docker inspect --format '{{if .State.Health}}{{.State.Health.Status}}{{else}}none{{end}}' sc-core)"
  echo "health=$state"
  [ "$state" = healthy ] && break
  [ "$state" != unhealthy ] || { docker logs --tail 200 sc-core; exit 1; }
  [ "$i" -lt 40 ] || { docker logs --tail 200 sc-core; exit 1; }
  sleep 2
done
echo; echo "=== LIVE HEALTH ==="
python3 -m json.tool </tmp/sc-core-v2361-1-health.json
echo; echo "=== UNCERTAINTY REASONING READINESS ==="
curl -fsS http://127.0.0.1:8090/v1/uncertainty-reasoning/readiness | tee /tmp/sc-core-v2361-1-reasoning.json | python3 -m json.tool
echo; echo "=== UNCERTAINTY COMPUTE READINESS ==="
curl -fsS http://127.0.0.1:8090/v1/uncertainty-compute/readiness | tee /tmp/sc-core-v2361-1-compute.json | python3 -m json.tool
python3 - <<'PY'
import json
h=json.load(open('/tmp/sc-core-v2361-1-health.json'))
r=json.load(open('/tmp/sc-core-v2361-1-reasoning.json'))
c=json.load(open('/tmp/sc-core-v2361-1-compute.json'))
assert h.get('ok') is True and h.get('version')=='2.36.1.1',h
assert h.get('uncertainty_compute_runtime_integration') is True,h
assert r.get('release')=='2.36.1.1',r
assert r.get('sampling_by_core') is False and r.get('sensitivity_algorithm_execution_by_core') is False and r.get('ensemble_aggregation_by_core') is False,r
assert r.get('automatic_truth_promotion') is False,r
assert c.get('release')=='2.36.1.1' and c.get('migration_0040_applied') is True,c
assert c.get('monte_carlo_sampling') is True and c.get('latin_hypercube_sampling') is True,c
assert c.get('sobol_index_analysis') is True and c.get('morris_elementary_effect_analysis') is True,c
assert c.get('ensemble_weight_normalization') is True and c.get('empirical_probability_estimation') is True,c
assert c.get('model_execution_by_core') is False and c.get('arbitrary_code_execution_by_core') is False and c.get('automatic_truth_promotion') is False,c
print('PASS: Platform Core v2.36.1.1')
print('PASS: production schema compatibility repair')
print('PASS: Uncertainty Compute Runtime Integration')
PY
echo; echo "=== VERIFY MIGRATION STATE ==="
docker exec sc-core python scripts/migrate.py | tee /tmp/sc-core-v2361-1-migration-state.json
python3 - <<'PY'
import json
m=json.load(open('/tmp/sc-core-v2361-1-migration-state.json'))
assert '0040' in m.get('applied',[]) and m.get('pending')==[],m
print('PASS: migration 0040 applied and pending=[]')
PY
echo; echo "=== VERIFY PERSISTENT SCIENTIFIC STORAGE MOUNT ==="
docker inspect sc-core --format '{{json .Mounts}}' | python3 -m json.tool
docker exec sc-core sh -lc 'test -d /data/scientific-objects; touch /data/scientific-objects/.v2361-1-write-test; rm /data/scientific-objects/.v2361-1-write-test; echo "PASS: persistent scientific-object storage writable"'
echo; echo "=== PUBLIC CADDY ROUTE ==="
curl -fsS https://core.sustainablecatalyst.com/health | python3 -c 'import json,sys;d=json.load(sys.stdin);assert d.get("version")=="2.36.1.1",d;print("PASS: public Core health 2.36.1.1")'
curl -fsS https://core.sustainablecatalyst.com/v1/uncertainty-compute/readiness | python3 -c 'import json,sys;d=json.load(sys.stdin);assert d.get("migration_0040_applied") is True,d;print("PASS: public Uncertainty Compute readiness")'
echo; echo "=== FINAL CONTAINER ==="
docker ps --filter name=sc-core --format 'table {{.Names}}\t{{.Image}}\t{{.Status}}\t{{.Ports}}'
echo; echo "Backup retained at: $BACKUP"
echo "============================================================"
echo " PLATFORM CORE v2.36.1.1 BACKEND DEPLOYMENT COMPLETE"
echo "============================================================"
