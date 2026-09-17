#!/usr/bin/env bash
set -euo pipefail
trap 'rc=$?; echo "ERROR: v2.48.0 deployment stopped at line $LINENO (exit $rc): $BASH_COMMAND" >&2; exit $rc' ERR
ROOT="${SC_CORE_ROOT:-/opt/sustainable-catalyst/core}"
BACKUP_ROOT="${SC_CORE_BACKUP_ROOT:-/opt/sustainable-catalyst/backups}"
COMPOSE="docker compose -f compose.yml -f compose.vps.yml"
STAMP="$(date +%Y%m%d-%H%M%S)"; BACKUP="${BACKUP_ROOT}/platform-core-v2.48.0-${STAMP}"
cd "$ROOT"
echo "============================================================"; echo " PLATFORM CORE v2.48.0 — QUANTITATIVE RECONSTRUCTION & REPRODUCTION HANDOFFS"; echo "============================================================"
echo; echo "=== CURRENT LIVE HEALTH ==="; curl -fsS http://127.0.0.1:8090/health | python3 -m json.tool
echo; echo "=== SAFETY CHECKS ==="; [ -f compose.yml ] || { echo "STOP: compose.yml missing"; exit 1; }; [ -f compose.vps.yml ] || { echo "STOP: compose.vps.yml missing"; exit 1; }; [ -f .env.production ] || { echo "STOP: .env.production missing"; exit 1; }
if ! git diff --quiet || ! git diff --cached --quiet; then echo "STOP: tracked production files have local changes."; git status --short; exit 1; fi
$COMPOSE config >/tmp/sc-core-v2480-compose.yml; grep -q '/data/scientific-objects' /tmp/sc-core-v2480-compose.yml || { echo "STOP: scientific-object persistent mount missing"; exit 1; }
CORE_DB_URL="$(grep -m1 '^SC_CORE_DATABASE_URL=' .env.production | cut -d= -f2-)"; [ -n "$CORE_DB_URL" ] || { echo "STOP: SC_CORE_DATABASE_URL not found"; exit 1; }
eval "$(CORE_DB_URL="$CORE_DB_URL" python3 - <<'PY2'
import os,shlex
from urllib.parse import urlparse,unquote
u=urlparse(os.environ['CORE_DB_URL'].strip().strip('"').strip("'")); print('DB_USER='+shlex.quote(unquote(u.username or ''))); print('DB_PASS='+shlex.quote(unquote(u.password or ''))); print('DB_NAME='+shlex.quote((u.path or '').lstrip('/')))
PY2
)"
psqlq(){ docker exec -e PGPASSWORD="$DB_PASS" sc-postgres psql -h 127.0.0.1 -U "$DB_USER" -d "$DB_NAME" -Atqc "$1"; }
echo; echo "=== PRODUCTION PREDECESSOR PREFLIGHT ==="
M51="$(psqlq "SELECT EXISTS (SELECT 1 FROM schema_migrations WHERE version='0051');")"; echo "schema_migrations.0051=$M51"; [ "$M51" = t ] || { echo "STOP: migration 0051 is not recorded; v2.47.0 must be deployed first"; exit 1; }
V247_TABLES=(forensic_media_artifacts forensic_media_derivations forensic_media_metadata_records forensic_media_fingerprints forensic_media_segments forensic_media_comparisons forensic_media_provenance_snapshots)
for t in "${V247_TABLES[@]}"; do v="$(psqlq "SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema='public' AND table_name='$t');")"; echo "$t=$v"; [ "$v" = t ] || { echo "STOP: predecessor v2.47 table missing: $t"; exit 1; }; done
V248_TABLES=(forensic_quantitative_reconstructions forensic_quantitative_measurements forensic_quantitative_assumptions forensic_quantitative_parameters forensic_quantitative_scenarios forensic_quantitative_handoffs forensic_quantitative_result_bindings forensic_quantitative_reproduction_packages)
v248_count=0
for t in "${V248_TABLES[@]}"; do v="$(psqlq "SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema='public' AND table_name='$t');")"; echo "$t=$v"; [ "$v" = t ] && v248_count=$((v248_count+1)); done
M52="$(psqlq "SELECT EXISTS (SELECT 1 FROM schema_migrations WHERE version='0052');")"; echo "schema_migrations.0052=$M52"; echo "forensic_quantitative_tables_present=$v248_count/8"
if [ "$M52" = f ] && [ "$v248_count" -eq 0 ]; then echo "PASS: pristine pre-0052 quantitative reconstruction state accepted";
elif [ "$M52" = f ] && [ "$v248_count" -eq 8 ]; then echo "PASS: safe partial-0052 quantitative table state detected and accepted";
elif [ "$M52" = t ] && [ "$v248_count" -eq 8 ]; then echo "PASS: migration 0052 already recorded with complete quantitative schema";
else echo "STOP: inconsistent quantitative migration state (0052=$M52, tables=$v248_count/8)"; exit 1; fi
echo; echo "=== BACKUP CURRENT CORE + DATABASE ==="; mkdir -p "$BACKUP"; tar --exclude='.git' -czf "$BACKUP/core-before-v2.48.0.tar.gz" .; docker exec -e PGPASSWORD="$DB_PASS" sc-postgres pg_dump -h 127.0.0.1 -U "$DB_USER" -d "$DB_NAME" -Fc > "$BACKUP/platform-core-before-v2.48.0.dump"; ls -lh "$BACKUP"/*
echo; echo "=== FETCH EXACT v2.48.0 RELEASE ==="; git fetch origin --tags; git rev-parse v2.48.0 >/dev/null 2>&1 || { echo "STOP: v2.48.0 tag is not available from GitHub"; exit 1; }; git pull --ff-only origin main; echo "HEAD: $(git log -1 --oneline)"; git tag --points-at HEAD | grep -qx 'v2.48.0' || { echo "STOP: production HEAD is not exactly tagged v2.48.0"; exit 1; }
head_commit="$(git rev-parse HEAD)"; tag_commit="$(git rev-list -n 1 v2.48.0)"; [ "$head_commit" = "$tag_commit" ] || { echo "STOP: v2.48.0 does not resolve to production HEAD"; exit 1; }
python3 - <<'PY2'
import ast,re
from pathlib import Path
mig=Path('backend/app/migrations.py'); tree=ast.parse(mig.read_text(),filename=str(mig)); migrations=None
for node in tree.body:
    if isinstance(node,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='MIGRATIONS' for t in node.targets): migrations=ast.literal_eval(node.value); break
assert migrations and migrations[-1][0]=='0052',migrations[-1]
models=Path('backend/app/models.py').read_text(); m=re.search(r'class\s+SchemaMigration\b.*?description:\s*Mapped\[str\]\s*=\s*mapped_column\(String\((\d+)\)',models,re.S); assert m
mx=int(m.group(1)); d=dict(migrations)['0052']; assert mx==300 and len(d)<=mx,(mx,len(d)); print(f'PASS: packaged 0052 migration description fits VARCHAR({mx}) at {len(d)} chars')
PY2
echo; echo "=== BUILD CORE v2.48.0 ==="; $COMPOSE build core
echo; echo "=== APPLY / REPAIR MIGRATION 0052 ==="; $COMPOSE run --rm --no-deps core python scripts/migrate.py | tee /tmp/sc-core-v2480-migrations.json
echo; echo "=== VERIFY DATABASE CONTRACT BEFORE RECREATE ==="
for t in "${V248_TABLES[@]}"; do [ "$(psqlq "SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema='public' AND table_name='$t');")" = t ] || { echo "STOP: $t missing after migration 0052"; exit 1; }; done
M52_POST="$(psqlq "SELECT EXISTS (SELECT 1 FROM schema_migrations WHERE version='0052');")"; [ "$M52_POST" = t ] || { echo "STOP: migration 0052 not recorded"; exit 1; }; D52_LEN="$(psqlq "SELECT length(description) FROM schema_migrations WHERE version='0052';")"; echo "schema_migrations.0052.description_length=$D52_LEN"; [ "$D52_LEN" -le 300 ] || { echo "STOP: stored 0052 description exceeds production contract"; exit 1; }; echo "PASS: migration 0052 complete; predecessor media provenance schema preserved"
echo; echo "=== RECREATE sc-core ==="; $COMPOSE up -d --no-deps --force-recreate core
for i in $(seq 1 40); do if curl -fsS http://127.0.0.1:8090/health >/tmp/sc-core-v2480-health.json 2>/dev/null; then break; fi; [ "$i" -lt 40 ] || { docker logs --tail 200 sc-core; exit 1; }; sleep 2; done
for i in $(seq 1 40); do state="$(docker inspect --format '{{if .State.Health}}{{.State.Health.Status}}{{else}}none{{end}}' sc-core)"; echo "health=$state"; [ "$state" = healthy ] && break; [ "$state" != unhealthy ] || { docker logs --tail 200 sc-core; exit 1; }; [ "$i" -lt 40 ] || { docker logs --tail 200 sc-core; exit 1; }; sleep 2; done
echo; echo "=== LIVE HEALTH ==="; python3 -m json.tool </tmp/sc-core-v2480-health.json
echo; echo "=== OPEN FORENSICS QUANTITATIVE READINESS ==="; curl -fsS http://127.0.0.1:8090/v1/open-forensics/readiness | tee /tmp/sc-core-v2480-forensics.json | python3 -m json.tool
python3 - <<'PY2'
import json
h=json.load(open('/tmp/sc-core-v2480-health.json')); r=json.load(open('/tmp/sc-core-v2480-forensics.json'))
assert h.get('ok') is True and h.get('version')=='2.48.0',h; assert h.get('open_forensics') is True,h; assert h.get('forensic_quantitative_reconstruction_reproduction_handoffs') is True,h
assert r.get('release')=='2.48.0' and r.get('migration_0052_applied') is True,r
for key in ('quantitative_reconstruction_registry_by_core','measurement_and_uncertainty_capture_by_core','assumption_parameter_registry_by_core','scenario_manifest_registry_by_core','workbench_lab_handoff_contracts_by_core','external_result_binding_by_core','reproducible_quantitative_packages_by_core'): assert r.get(key) is True,(key,r)
for key in ('quantitative_model_execution_by_core','numerical_solution_by_core','statistical_inference_execution_by_core','uncertainty_propagation_execution_by_core','sensitivity_execution_by_core','parameter_optimization_by_core','automatic_truth_promotion'): assert r.get(key) is False,(key,r)
print('PASS: Platform Core v2.48.0'); print('PASS: Quantitative Reconstruction & Reproduction Handoffs'); print('PASS: migration 0052 additive with external-runtime and non-execution/non-verdict boundaries intact')
PY2
echo; echo "=== VERIFY MIGRATION STATE ==="; docker exec sc-core python scripts/migrate.py | tee /tmp/sc-core-v2480-migration-state.json
python3 - <<'PY2'
import json
m=json.load(open('/tmp/sc-core-v2480-migration-state.json')); assert '0052' in m.get('applied',[]) and m.get('pending')==[],m; print('PASS: migration 0052 applied and pending=[]')
PY2
echo; echo "=== VERIFY PERSISTENT SCIENTIFIC STORAGE MOUNT ==="; docker exec sc-core sh -lc 'test -d /data/scientific-objects; touch /data/scientific-objects/.v2480-write-test; rm /data/scientific-objects/.v2480-write-test; echo "PASS: persistent scientific-object storage writable"'
echo; echo "=== PUBLIC CADDY ROUTE ==="; curl -fsS https://core.sustainablecatalyst.com/health | python3 -c 'import json,sys;d=json.load(sys.stdin);assert d.get("version")=="2.48.0",d;print("PASS: public Core health 2.48.0")'; curl -fsS https://core.sustainablecatalyst.com/v1/open-forensics/readiness | python3 -c 'import json,sys;d=json.load(sys.stdin);assert d.get("release")=="2.48.0" and d.get("migration_0052_applied") is True,d;print("PASS: public Quantitative Reconstruction & Reproduction Handoffs readiness")'
echo; echo "=== FINAL CONTAINER ==="; docker ps --filter name=sc-core --format 'table {{.Names}}\t{{.Image}}\t{{.Status}}\t{{.Ports}}'; echo; echo "Backup retained at: $BACKUP"; echo "============================================================"; echo " PLATFORM CORE v2.48.0 BACKEND DEPLOYMENT COMPLETE"; echo "============================================================"
