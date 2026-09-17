#!/usr/bin/env bash
set -euo pipefail
trap 'rc=$?; echo "ERROR: v2.40.0 Contabo deployment stopped at line $LINENO (exit $rc): $BASH_COMMAND" >&2; exit $rc' ERR
ROOT="/opt/sustainable-catalyst/core"; BACKUP_ROOT="/opt/sustainable-catalyst/backups"; COMPOSE="docker compose -f compose.yml -f compose.vps.yml"; STAMP="$(date +%Y%m%d-%H%M%S)"; BACKUP="${BACKUP_ROOT}/platform-core-v2.40.0-${STAMP}"
cd "$ROOT"
echo "============================================================"; echo " PLATFORM CORE v2.40.0 — CROSS-PRODUCT VISUAL RESEARCH OBJECTS"; echo "============================================================"
echo; echo "=== CURRENT LIVE HEALTH ==="; curl -fsS http://127.0.0.1:8090/health | python3 -m json.tool
echo; echo "=== SAFETY CHECKS ==="; [ -f compose.yml ] || { echo "STOP: compose.yml missing"; exit 1; }; [ -f compose.vps.yml ] || { echo "STOP: compose.vps.yml missing"; exit 1; }; [ -f .env.production ] || { echo "STOP: .env.production missing"; exit 1; }
if ! git diff --quiet || ! git diff --cached --quiet; then echo "STOP: tracked production files have local changes."; git status --short; exit 1; fi
$COMPOSE config >/tmp/sc-core-v2400-compose.yml; grep -q '/data/scientific-objects' /tmp/sc-core-v2400-compose.yml || { echo "STOP: scientific-object persistent mount missing"; exit 1; }
CORE_DB_URL="$(grep -m1 '^SC_CORE_DATABASE_URL=' .env.production | cut -d= -f2-)"; [ -n "$CORE_DB_URL" ] || { echo "STOP: SC_CORE_DATABASE_URL not found"; exit 1; }
eval "$(CORE_DB_URL="$CORE_DB_URL" python3 - <<'PY2'
import os,shlex
from urllib.parse import urlparse,unquote
u=urlparse(os.environ['CORE_DB_URL'].strip().strip('"').strip("'")); print('DB_USER='+shlex.quote(unquote(u.username or ''))); print('DB_PASS='+shlex.quote(unquote(u.password or ''))); print('DB_NAME='+shlex.quote((u.path or '').lstrip('/')))
PY2
)"
psqlq(){ docker exec -e PGPASSWORD="$DB_PASS" sc-postgres psql -h 127.0.0.1 -U "$DB_USER" -d "$DB_NAME" -Atqc "$1"; }

echo; echo "=== PRODUCTION PREDECESSOR PREFLIGHT ==="
M43="$(psqlq "SELECT EXISTS (SELECT 1 FROM schema_migrations WHERE version='0043');")"; echo "schema_migrations.0043=$M43"; [ "$M43" = t ] || { echo "STOP: migration 0043 is not recorded; v2.39.0 must be deployed first"; exit 1; }
EXPLANATION_TABLES=(research_visual_explanations research_explanation_nodes research_explanation_relations research_explanation_citations research_explanation_views research_explanation_snapshots)
for t in "${EXPLANATION_TABLES[@]}"; do v="$(psqlq "SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema='public' AND table_name='$t');")"; echo "$t=$v"; [ "$v" = t ] || { echo "STOP: predecessor v2.39 table missing: $t"; exit 1; }; done
V240_TABLES=(cross_product_visual_research_objects cross_product_visual_research_members cross_product_visual_research_relations cross_product_visual_research_views cross_product_visual_research_snapshots)
v240_count=0
for t in "${V240_TABLES[@]}"; do v="$(psqlq "SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema='public' AND table_name='$t');")"; echo "$t=$v"; [ "$v" = t ] && v240_count=$((v240_count+1)); done
M44="$(psqlq "SELECT EXISTS (SELECT 1 FROM schema_migrations WHERE version='0044');")"; echo "schema_migrations.0044=$M44"; echo "cross_product_visual_research_tables_present=$v240_count/5"
if [ "$M44" = f ] && [ "$v240_count" -eq 0 ]; then echo "PASS: pristine pre-0044 cross-product visual-research state accepted";
elif [ "$M44" = f ] && [ "$v240_count" -eq 5 ]; then echo "PASS: safe partial-0044 cross-product visual-research table state detected and accepted";
elif [ "$M44" = t ] && [ "$v240_count" -eq 5 ]; then echo "PASS: migration 0044 already recorded with complete cross-product visual-research schema";
else echo "STOP: inconsistent cross-product visual-research migration state (0044=$M44, tables=$v240_count/5)"; exit 1; fi

echo; echo "=== BACKUP CURRENT CORE + DATABASE ==="; mkdir -p "$BACKUP"; tar --exclude='.git' -czf "$BACKUP/core-before-v2.40.0.tar.gz" .; docker exec -e PGPASSWORD="$DB_PASS" sc-postgres pg_dump -h 127.0.0.1 -U "$DB_USER" -d "$DB_NAME" -Fc > "$BACKUP/platform-core-before-v2.40.0.dump"; ls -lh "$BACKUP"/*
echo; echo "=== FETCH EXACT v2.40.0 RELEASE ==="; git fetch origin --tags; git rev-parse v2.40.0 >/dev/null 2>&1 || { echo "STOP: v2.40.0 tag is not available from GitHub"; exit 1; }; git pull --ff-only origin main; echo "HEAD: $(git log -1 --oneline)"; git tag --points-at HEAD | grep -qx 'v2.40.0' || { echo "STOP: production HEAD is not exactly tagged v2.40.0"; exit 1; }
head_commit="$(git rev-parse HEAD)"; tag_commit="$(git rev-list -n 1 v2.40.0)"; [ "$head_commit" = "$tag_commit" ] || { echo "STOP: v2.40.0 does not resolve to production HEAD"; exit 1; }
python3 - <<'PY2'
import ast,re
from pathlib import Path
mig=Path('backend/app/migrations.py'); tree=ast.parse(mig.read_text(),filename=str(mig)); migrations=None
for node in tree.body:
    if isinstance(node,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='MIGRATIONS' for t in node.targets): migrations=ast.literal_eval(node.value); break
assert migrations and migrations[-1][0]=='0044',migrations[-1]
models=Path('backend/app/models.py').read_text(); m=re.search(r'class\s+SchemaMigration\b.*?description:\s*Mapped\[str\]\s*=\s*mapped_column\(String\((\d+)\)',models,re.S); assert m
mx=int(m.group(1)); d=dict(migrations)['0044']; assert mx==300 and len(d)<=mx,(mx,len(d)); print(f'PASS: packaged 0044 migration description fits VARCHAR({mx}) at {len(d)} chars')
PY2

echo; echo "=== BUILD CORE v2.40.0 ==="; $COMPOSE build core
echo; echo "=== APPLY / REPAIR MIGRATION 0044 ==="; $COMPOSE run --rm --no-deps core python scripts/migrate.py | tee /tmp/sc-core-v2400-migrations.json
echo; echo "=== VERIFY DATABASE CONTRACT BEFORE RECREATE ==="; for t in "${V240_TABLES[@]}"; do [ "$(psqlq "SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema='public' AND table_name='$t');")" = t ] || { echo "STOP: $t missing after migration 0044"; exit 1; }; done
M44_POST="$(psqlq "SELECT EXISTS (SELECT 1 FROM schema_migrations WHERE version='0044');")"; [ "$M44_POST" = t ] || { echo "STOP: migration 0044 not recorded"; exit 1; }; D44_LEN="$(psqlq "SELECT length(description) FROM schema_migrations WHERE version='0044';")"; echo "schema_migrations.0044.description_length=$D44_LEN"; [ "$D44_LEN" -le 300 ] || { echo "STOP: stored 0044 description exceeds production contract"; exit 1; }; echo "PASS: migration 0044 complete; predecessor schema preserved"

echo; echo "=== RECREATE sc-core ==="; $COMPOSE up -d --no-deps --force-recreate core
for i in $(seq 1 40); do if curl -fsS http://127.0.0.1:8090/health >/tmp/sc-core-v2400-health.json 2>/dev/null; then break; fi; [ "$i" -lt 40 ] || { docker logs --tail 200 sc-core; exit 1; }; sleep 2; done
for i in $(seq 1 40); do state="$(docker inspect --format '{{if .State.Health}}{{.State.Health.Status}}{{else}}none{{end}}' sc-core)"; echo "health=$state"; [ "$state" = healthy ] && break; [ "$state" != unhealthy ] || { docker logs --tail 200 sc-core; exit 1; }; [ "$i" -lt 40 ] || { docker logs --tail 200 sc-core; exit 1; }; sleep 2; done

echo; echo "=== LIVE HEALTH ==="; python3 -m json.tool </tmp/sc-core-v2400-health.json
echo; echo "=== CROSS-PRODUCT VISUAL RESEARCH READINESS ==="; curl -fsS http://127.0.0.1:8090/v1/cross-product-visual-research/readiness | tee /tmp/sc-core-v2400-cpvr.json | python3 -m json.tool
python3 - <<'PY2'
import json
h=json.load(open('/tmp/sc-core-v2400-health.json')); r=json.load(open('/tmp/sc-core-v2400-cpvr.json'))
assert h.get('ok') is True and h.get('version')=='2.40.0',h
assert h.get('cross_product_visual_research_objects') is True,h
assert r.get('release')=='2.40.0' and r.get('migration_0044_applied') is True,r
assert r.get('reference_first_cross_product') is True and r.get('renderer_neutral') is True,r
for key in ('remote_product_fetch_by_core','model_execution_by_core','analysis_execution_by_core','cross_product_truth_merging_by_core','layout_execution_by_core','renderer_execution_by_core','automatic_truth_promotion'):
    assert r.get(key) is False,(key,r)
print('PASS: Platform Core v2.40.0'); print('PASS: Cross-Product Visual Research Objects'); print('PASS: migration 0044 additive with product identity and execution boundaries intact')
PY2

echo; echo "=== VERIFY MIGRATION STATE ==="; docker exec sc-core python scripts/migrate.py | tee /tmp/sc-core-v2400-migration-state.json
python3 - <<'PY2'
import json
m=json.load(open('/tmp/sc-core-v2400-migration-state.json')); assert '0044' in m.get('applied',[]) and m.get('pending')==[],m; print('PASS: migration 0044 applied and pending=[]')
PY2

echo; echo "=== VERIFY PERSISTENT SCIENTIFIC STORAGE MOUNT ==="; docker exec sc-core sh -lc 'test -d /data/scientific-objects; touch /data/scientific-objects/.v2400-write-test; rm /data/scientific-objects/.v2400-write-test; echo "PASS: persistent scientific-object storage writable"'
echo; echo "=== PUBLIC CADDY ROUTE ==="; curl -fsS https://core.sustainablecatalyst.com/health | python3 -c 'import json,sys;d=json.load(sys.stdin);assert d.get("version")=="2.40.0",d;print("PASS: public Core health 2.40.0")'; curl -fsS https://core.sustainablecatalyst.com/v1/cross-product-visual-research/readiness | python3 -c 'import json,sys;d=json.load(sys.stdin);assert d.get("release")=="2.40.0" and d.get("migration_0044_applied") is True,d;print("PASS: public Cross-Product Visual Research readiness")'
echo; echo "=== FINAL CONTAINER ==="; docker ps --filter name=sc-core --format 'table {{.Names}}\t{{.Image}}\t{{.Status}}\t{{.Ports}}'; echo; echo "Backup retained at: $BACKUP"; echo "============================================================"; echo " PLATFORM CORE v2.40.0 BACKEND DEPLOYMENT COMPLETE"; echo "============================================================"
