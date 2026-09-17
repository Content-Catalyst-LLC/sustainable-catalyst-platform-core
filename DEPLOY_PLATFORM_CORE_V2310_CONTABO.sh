#!/usr/bin/env bash
set -euo pipefail
trap 'rc=$?; echo "ERROR: v2.31.0 Contabo deployment stopped at line $LINENO (exit $rc): $BASH_COMMAND" >&2; exit $rc' ERR

ROOT="/opt/sustainable-catalyst/core"
BACKUP_ROOT="/opt/sustainable-catalyst/backups"
COMPOSE="docker compose -f compose.yml -f compose.vps.yml"
STAMP="$(date +%Y%m%d-%H%M%S)"
BACKUP="${BACKUP_ROOT}/platform-core-v2.31.0-${STAMP}"

cd "$ROOT"

echo "============================================================"
echo " PLATFORM CORE v2.31.0 — CONTABO PRODUCTION DEPLOYMENT"
echo "============================================================"

echo
echo "=== CURRENT LIVE HEALTH ==="
curl -fsS http://127.0.0.1:8090/health | python3 -m json.tool

echo
echo "=== SAFETY CHECKS ==="
[ -f compose.yml ] || { echo "STOP: compose.yml missing"; exit 1; }
[ -f compose.vps.yml ] || { echo "STOP: compose.vps.yml missing; persistent scientific storage override must be preserved"; exit 1; }
[ -f .env.production ] || { echo "STOP: .env.production missing"; exit 1; }
if ! git diff --quiet || ! git diff --cached --quiet; then
  echo "STOP: tracked production files have local changes."
  git status --short
  exit 1
fi
$COMPOSE config >/tmp/sc-core-v2310-compose.yml
grep -q '/data/scientific-objects' /tmp/sc-core-v2310-compose.yml || { echo "STOP: scientific-object persistent mount missing from effective Compose configuration"; exit 1; }

echo
echo "=== BACKUP CURRENT CORE + DATABASE ==="
mkdir -p "$BACKUP"
tar --exclude='.git' -czf "$BACKUP/core-before-v2.31.0.tar.gz" .
CORE_DB_URL="$(grep -m1 '^SC_CORE_DATABASE_URL=' .env.production | cut -d= -f2-)"
[ -n "$CORE_DB_URL" ] || { echo "STOP: SC_CORE_DATABASE_URL not found"; exit 1; }
eval "$(CORE_DB_URL="$CORE_DB_URL" python3 - <<'PY'
import os, shlex
from urllib.parse import urlparse, unquote
raw=os.environ['CORE_DB_URL'].strip().strip('"').strip("'")
u=urlparse(raw)
print('DB_USER='+shlex.quote(unquote(u.username or '')))
print('DB_PASS='+shlex.quote(unquote(u.password or '')))
print('DB_NAME='+shlex.quote((u.path or '').lstrip('/')))
PY
)"
docker exec -e PGPASSWORD="$DB_PASS" sc-postgres pg_dump -h 127.0.0.1 -U "$DB_USER" -d "$DB_NAME" -Fc > "$BACKUP/platform-core-before-v2.31.0.dump"
ls -lh "$BACKUP/core-before-v2.31.0.tar.gz" "$BACKUP/platform-core-before-v2.31.0.dump"

echo
echo "=== FETCH EXACT v2.31.0 RELEASE ==="
git fetch origin --tags
git rev-parse v2.31.0 >/dev/null 2>&1 || { echo "STOP: v2.31.0 tag is not available from GitHub"; exit 1; }
git pull --ff-only origin main
echo "HEAD: $(git log -1 --oneline)"
echo "Tags at HEAD:"
git tag --points-at HEAD
if ! git tag --points-at HEAD | grep -qx 'v2.31.0'; then
  echo "STOP: production HEAD is not exactly tagged v2.31.0"
  exit 1
fi

echo
echo "=== BUILD CORE v2.31.0 ==="
$COMPOSE build core

echo
echo "=== APPLY MIGRATIONS THROUGH 0034 ==="
$COMPOSE run --rm --no-deps core python scripts/migrate.py | tee /tmp/sc-core-v2310-migrations.json

echo
echo "=== RECREATE sc-core ==="
$COMPOSE up -d --no-deps --force-recreate core

echo
echo "=== WAIT FOR HTTP + DOCKER HEALTH ==="
for i in $(seq 1 40); do
  if curl -fsS http://127.0.0.1:8090/health >/tmp/sc-core-v2310-health.json 2>/dev/null; then break; fi
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

echo
echo "=== LIVE HEALTH ==="
python3 -m json.tool </tmp/sc-core-v2310-health.json

echo
echo "=== SYSTEM MAPS READINESS ==="
curl -fsS http://127.0.0.1:8090/v1/system-maps/readiness | tee /tmp/sc-core-v2310-visualization.json | python3 -m json.tool

echo
echo "=== ASSERT RELEASE CONTRACT ==="
python3 - <<'PY'
import json
health=json.load(open('/tmp/sc-core-v2310-health.json'))
ready=json.load(open('/tmp/sc-core-v2310-visualization.json'))
assert health.get('ok') is True, health
assert health.get('version') == '2.31.0', health
assert health.get('visual_reasoning_object_model') is True, health
assert health.get('visualization_specification_renderer_registry') is True, health
assert health.get('system_maps') is True, health
assert ready.get('release') == '2.31.0', ready
assert ready.get('enabled') is True, ready
assert ready.get('migration_0034_applied') is True, ready
assert ready.get('visual_kind') == 'system-map', ready
assert ready.get('renderer_neutral') is True, ready
assert ready.get('layout_engine_in_core') is False, ready
assert ready.get('causal_inference_by_core') is False, ready
assert ready.get('automatic_truth_promotion') is False, ready
print('PASS: Platform Core v2.31.0')
print('PASS: migration 0034')
print('PASS: System Maps')
print('PASS: Core remains non-rendering')
PY

echo
echo "=== VERIFY MIGRATION STATE ==="
docker exec sc-core python scripts/migrate.py | tee /tmp/sc-core-v2310-migration-state.json
python3 - <<'PY'
import json
m=json.load(open('/tmp/sc-core-v2310-migration-state.json'))
assert '0034' in m.get('applied', []), m
assert m.get('pending') == [], m
print('PASS: migration 0034 applied and pending=[]')
PY

echo
echo "=== VERIFY PERSISTENT SCIENTIFIC STORAGE MOUNT ==="
docker inspect sc-core --format '{{json .Mounts}}' | python3 -m json.tool
docker exec sc-core sh -lc 'test -d /data/scientific-objects; touch /data/scientific-objects/.v231-write-test; rm /data/scientific-objects/.v231-write-test; echo "PASS: persistent scientific-object storage writable"'

echo
echo "=== PUBLIC CADDY ROUTE ==="
curl -fsS https://core.sustainablecatalyst.com/health | python3 -c 'import json,sys; d=json.load(sys.stdin); assert d.get("version")=="2.31.0",d; print("PASS: public Core health 2.31.0")'
curl -fsS https://core.sustainablecatalyst.com/v1/system-maps/readiness | python3 -c 'import json,sys; d=json.load(sys.stdin); assert d.get("migration_0034_applied") is True,d; print("PASS: public System Maps readiness")'

echo
echo "=== FINAL CONTAINER ==="
docker ps --filter name=sc-core --format 'table {{.Names}}\t{{.Image}}\t{{.Status}}\t{{.Ports}}'
echo
echo "Backup retained at: $BACKUP"
echo "============================================================"
echo " PLATFORM CORE v2.31.0 BACKEND DEPLOYMENT COMPLETE"
echo "============================================================"
