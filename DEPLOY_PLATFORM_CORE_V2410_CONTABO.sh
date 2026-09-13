#!/usr/bin/env bash
set -euo pipefail
trap 'rc=$?; echo "ERROR: v2.41.0 Contabo deployment stopped at line $LINENO (exit $rc): $BASH_COMMAND" >&2; exit $rc' ERR
ROOT="/opt/sustainable-catalyst/core"; BACKUP_ROOT="/opt/sustainable-catalyst/backups"; COMPOSE="docker compose -f compose.yml -f compose.vps.yml"; STAMP="$(date +%Y%m%d-%H%M%S)"; BACKUP="${BACKUP_ROOT}/platform-core-v2.41.0-${STAMP}"
cd "$ROOT"
echo "============================================================"; echo " PLATFORM CORE v2.41.0 — REPRODUCIBLE VISUAL KNOWLEDGE LAYER"; echo "============================================================"
echo; echo "=== CURRENT LIVE HEALTH ==="; curl -fsS http://127.0.0.1:8090/health | python3 -m json.tool
echo; echo "=== SAFETY CHECKS ==="; [ -f compose.yml ] || { echo "STOP: compose.yml missing"; exit 1; }; [ -f compose.vps.yml ] || { echo "STOP: compose.vps.yml missing"; exit 1; }; [ -f .env.production ] || { echo "STOP: .env.production missing"; exit 1; }
if ! git diff --quiet || ! git diff --cached --quiet; then echo "STOP: tracked production files have local changes."; git status --short; exit 1; fi
$COMPOSE config >/tmp/sc-core-v2410-compose.yml; grep -q '/data/scientific-objects' /tmp/sc-core-v2410-compose.yml || { echo "STOP: scientific-object persistent mount missing"; exit 1; }
CORE_DB_URL="$(grep -m1 '^SC_CORE_DATABASE_URL=' .env.production | cut -d= -f2-)"; [ -n "$CORE_DB_URL" ] || { echo "STOP: SC_CORE_DATABASE_URL not found"; exit 1; }
eval "$(CORE_DB_URL="$CORE_DB_URL" python3 - <<'PY2'
import os,shlex
from urllib.parse import urlparse,unquote
u=urlparse(os.environ['CORE_DB_URL'].strip().strip('"').strip("'")); print('DB_USER='+shlex.quote(unquote(u.username or ''))); print('DB_PASS='+shlex.quote(unquote(u.password or ''))); print('DB_NAME='+shlex.quote((u.path or '').lstrip('/')))
PY2
)"
psqlq(){ docker exec -e PGPASSWORD="$DB_PASS" sc-postgres psql -h 127.0.0.1 -U "$DB_USER" -d "$DB_NAME" -Atqc "$1"; }

echo; echo "=== PRODUCTION PREDECESSOR PREFLIGHT ==="
M44="$(psqlq "SELECT EXISTS (SELECT 1 FROM schema_migrations WHERE version='0044');")"; echo "schema_migrations.0044=$M44"; [ "$M44" = t ] || { echo "STOP: migration 0044 is not recorded; v2.40.0 must be deployed first"; exit 1; }
V240_TABLES=(cross_product_visual_research_objects cross_product_visual_research_members cross_product_visual_research_relations cross_product_visual_research_views cross_product_visual_research_snapshots)
for t in "${V240_TABLES[@]}"; do v="$(psqlq "SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema='public' AND table_name='$t');")"; echo "$t=$v"; [ "$v" = t ] || { echo "STOP: predecessor v2.40 table missing: $t"; exit 1; }; done
V241_TABLES=(reproducible_visual_knowledge_packages reproducible_visual_knowledge_inputs reproducible_visual_knowledge_environments reproducible_visual_knowledge_replay_plans reproducible_visual_knowledge_verifications reproducible_visual_knowledge_snapshots)
v241_count=0
for t in "${V241_TABLES[@]}"; do v="$(psqlq "SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema='public' AND table_name='$t');")"; echo "$t=$v"; [ "$v" = t ] && v241_count=$((v241_count+1)); done
M45="$(psqlq "SELECT EXISTS (SELECT 1 FROM schema_migrations WHERE version='0045');")"; echo "schema_migrations.0045=$M45"; echo "reproducible_visual_knowledge_tables_present=$v241_count/6"
if [ "$M45" = f ] && [ "$v241_count" -eq 0 ]; then echo "PASS: pristine pre-0045 reproducible-visual-knowledge state accepted";
elif [ "$M45" = f ] && [ "$v241_count" -eq 6 ]; then echo "PASS: safe partial-0045 reproducibility table state detected and accepted";
elif [ "$M45" = t ] && [ "$v241_count" -eq 6 ]; then echo "PASS: migration 0045 already recorded with complete reproducibility schema";
else echo "STOP: inconsistent reproducible-visual-knowledge migration state (0045=$M45, tables=$v241_count/6)"; exit 1; fi

echo; echo "=== BACKUP CURRENT CORE + DATABASE ==="; mkdir -p "$BACKUP"; tar --exclude='.git' -czf "$BACKUP/core-before-v2.41.0.tar.gz" .; docker exec -e PGPASSWORD="$DB_PASS" sc-postgres pg_dump -h 127.0.0.1 -U "$DB_USER" -d "$DB_NAME" -Fc > "$BACKUP/platform-core-before-v2.41.0.dump"; ls -lh "$BACKUP"/*
echo; echo "=== FETCH EXACT v2.41.0 RELEASE ==="; git fetch origin --tags; git rev-parse v2.41.0 >/dev/null 2>&1 || { echo "STOP: v2.41.0 tag is not available from GitHub"; exit 1; }; git pull --ff-only origin main; echo "HEAD: $(git log -1 --oneline)"; git tag --points-at HEAD | grep -qx 'v2.41.0' || { echo "STOP: production HEAD is not exactly tagged v2.41.0"; exit 1; }
head_commit="$(git rev-parse HEAD)"; tag_commit="$(git rev-list -n 1 v2.41.0)"; [ "$head_commit" = "$tag_commit" ] || { echo "STOP: v2.41.0 does not resolve to production HEAD"; exit 1; }
python3 - <<'PY2'
import ast,re
from pathlib import Path
mig=Path('backend/app/migrations.py'); tree=ast.parse(mig.read_text(),filename=str(mig)); migrations=None
for node in tree.body:
    if isinstance(node,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='MIGRATIONS' for t in node.targets): migrations=ast.literal_eval(node.value); break
assert migrations and migrations[-1][0]=='0045',migrations[-1]
models=Path('backend/app/models.py').read_text(); m=re.search(r'class\s+SchemaMigration\b.*?description:\s*Mapped\[str\]\s*=\s*mapped_column\(String\((\d+)\)',models,re.S); assert m
mx=int(m.group(1)); d=dict(migrations)['0045']; assert mx==300 and len(d)<=mx,(mx,len(d)); print(f'PASS: packaged 0045 migration description fits VARCHAR({mx}) at {len(d)} chars')
PY2

echo; echo "=== BUILD CORE v2.41.0 ==="; $COMPOSE build core
echo; echo "=== APPLY / REPAIR MIGRATION 0045 ==="; $COMPOSE run --rm --no-deps core python scripts/migrate.py | tee /tmp/sc-core-v2410-migrations.json
echo; echo "=== VERIFY DATABASE CONTRACT BEFORE RECREATE ==="; for t in "${V241_TABLES[@]}"; do [ "$(psqlq "SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema='public' AND table_name='$t');")" = t ] || { echo "STOP: $t missing after migration 0045"; exit 1; }; done
M45_POST="$(psqlq "SELECT EXISTS (SELECT 1 FROM schema_migrations WHERE version='0045');")"; [ "$M45_POST" = t ] || { echo "STOP: migration 0045 not recorded"; exit 1; }; D45_LEN="$(psqlq "SELECT length(description) FROM schema_migrations WHERE version='0045';")"; echo "schema_migrations.0045.description_length=$D45_LEN"; [ "$D45_LEN" -le 300 ] || { echo "STOP: stored 0045 description exceeds production contract"; exit 1; }; echo "PASS: migration 0045 complete; predecessor schema preserved"

echo; echo "=== RECREATE sc-core ==="; $COMPOSE up -d --no-deps --force-recreate core
for i in $(seq 1 40); do if curl -fsS http://127.0.0.1:8090/health >/tmp/sc-core-v2410-health.json 2>/dev/null; then break; fi; [ "$i" -lt 40 ] || { docker logs --tail 200 sc-core; exit 1; }; sleep 2; done
for i in $(seq 1 40); do state="$(docker inspect --format '{{if .State.Health}}{{.State.Health.Status}}{{else}}none{{end}}' sc-core)"; echo "health=$state"; [ "$state" = healthy ] && break; [ "$state" != unhealthy ] || { docker logs --tail 200 sc-core; exit 1; }; [ "$i" -lt 40 ] || { docker logs --tail 200 sc-core; exit 1; }; sleep 2; done

echo; echo "=== LIVE HEALTH ==="; python3 -m json.tool </tmp/sc-core-v2410-health.json
echo; echo "=== REPRODUCIBLE VISUAL KNOWLEDGE READINESS ==="; curl -fsS http://127.0.0.1:8090/v1/reproducible-visual-knowledge/readiness | tee /tmp/sc-core-v2410-rvk.json | python3 -m json.tool
python3 - <<'PY2'
import json
h=json.load(open('/tmp/sc-core-v2410-health.json')); r=json.load(open('/tmp/sc-core-v2410-rvk.json'))
assert h.get('ok') is True and h.get('version')=='2.41.0',h
assert h.get('reproducible_visual_knowledge_layer') is True,h
assert r.get('release')=='2.41.0' and r.get('migration_0045_applied') is True,r
assert r.get('knowledge_state_capture_by_core') is True and r.get('manifest_hashing_by_core') is True and r.get('integrity_verification_by_core') is True,r
for key in ('specialist_execution_by_core','remote_product_fetch_by_core','arbitrary_code_execution_by_core','replay_execution_by_core','output_equivalence_claim_by_core_without_external_evidence','automatic_truth_promotion'):
    assert r.get(key) is False,(key,r)
print('PASS: Platform Core v2.41.0'); print('PASS: Reproducible Visual Knowledge Layer'); print('PASS: migration 0045 additive with reproducibility and execution boundaries intact')
PY2

echo; echo "=== VERIFY MIGRATION STATE ==="; docker exec sc-core python scripts/migrate.py | tee /tmp/sc-core-v2410-migration-state.json
python3 - <<'PY2'
import json
m=json.load(open('/tmp/sc-core-v2410-migration-state.json')); assert '0045' in m.get('applied',[]) and m.get('pending')==[],m; print('PASS: migration 0045 applied and pending=[]')
PY2

echo; echo "=== VERIFY PERSISTENT SCIENTIFIC STORAGE MOUNT ==="; docker exec sc-core sh -lc 'test -d /data/scientific-objects; touch /data/scientific-objects/.v2410-write-test; rm /data/scientific-objects/.v2410-write-test; echo "PASS: persistent scientific-object storage writable"'
echo; echo "=== PUBLIC CADDY ROUTE ==="; curl -fsS https://core.sustainablecatalyst.com/health | python3 -c 'import json,sys;d=json.load(sys.stdin);assert d.get("version")=="2.41.0",d;print("PASS: public Core health 2.41.0")'; curl -fsS https://core.sustainablecatalyst.com/v1/reproducible-visual-knowledge/readiness | python3 -c 'import json,sys;d=json.load(sys.stdin);assert d.get("release")=="2.41.0" and d.get("migration_0045_applied") is True,d;print("PASS: public Reproducible Visual Knowledge readiness")'
echo; echo "=== FINAL CONTAINER ==="; docker ps --filter name=sc-core --format 'table {{.Names}}\t{{.Image}}\t{{.Status}}\t{{.Ports}}'; echo; echo "Backup retained at: $BACKUP"; echo "============================================================"; echo " PLATFORM CORE v2.41.0 BACKEND DEPLOYMENT COMPLETE"; echo "============================================================"
