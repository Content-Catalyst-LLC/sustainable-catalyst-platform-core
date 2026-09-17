#!/usr/bin/env bash
set -euo pipefail
trap 'rc=$?; echo "ERROR: v2.50.0 deployment stopped at line $LINENO (exit $rc): $BASH_COMMAND" >&2; exit $rc' ERR
ROOT="${SC_CORE_ROOT:-/opt/sustainable-catalyst/core}"
BACKUP_ROOT="${SC_CORE_BACKUP_ROOT:-/opt/sustainable-catalyst/backups}"
COMPOSE="docker compose -f compose.yml -f compose.vps.yml"
STAMP="$(date +%Y%m%d-%H%M%S)"; BACKUP="${BACKUP_ROOT}/platform-core-v2.50.0-${STAMP}"
cd "$ROOT"
echo "============================================================"; echo " PLATFORM CORE v2.50.0 — FORENSIC RESEARCH GRAPH"; echo "============================================================"
echo; echo "=== CURRENT LIVE HEALTH ==="; curl -fsS http://127.0.0.1:8090/health | python3 -m json.tool
echo; echo "=== SAFETY CHECKS ==="; [ -f compose.yml ] || { echo "STOP: compose.yml missing"; exit 1; }; [ -f compose.vps.yml ] || { echo "STOP: compose.vps.yml missing"; exit 1; }; [ -f .env.production ] || { echo "STOP: .env.production missing"; exit 1; }
if ! git diff --quiet || ! git diff --cached --quiet; then echo "STOP: tracked production files have local changes."; git status --short; exit 1; fi
$COMPOSE config >/tmp/sc-core-v2500-compose.yml; grep -q '/data/scientific-objects' /tmp/sc-core-v2500-compose.yml || { echo "STOP: scientific-object persistent mount missing"; exit 1; }
CORE_DB_URL="$(grep -m1 '^SC_CORE_DATABASE_URL=' .env.production | cut -d= -f2-)"; [ -n "$CORE_DB_URL" ] || { echo "STOP: SC_CORE_DATABASE_URL not found"; exit 1; }
eval "$(CORE_DB_URL="$CORE_DB_URL" python3 - <<'PY2'
import os,shlex
from urllib.parse import urlparse,unquote
u=urlparse(os.environ['CORE_DB_URL'].strip().strip('"').strip("'")); print('DB_USER='+shlex.quote(unquote(u.username or ''))); print('DB_PASS='+shlex.quote(unquote(u.password or ''))); print('DB_NAME='+shlex.quote((u.path or '').lstrip('/')))
PY2
)"
psqlq(){ docker exec -e PGPASSWORD="$DB_PASS" sc-postgres psql -h 127.0.0.1 -U "$DB_USER" -d "$DB_NAME" -Atqc "$1"; }
echo; echo "=== PRODUCTION PREDECESSOR PREFLIGHT ==="
M53="$(psqlq "SELECT EXISTS (SELECT 1 FROM schema_migrations WHERE version='0053');")"; echo "schema_migrations.0053=$M53"; [ "$M53" = t ] || { echo "STOP: migration 0053 is not recorded; v2.49.0 must be deployed first"; exit 1; }
V249_TABLES=(forensic_statements forensic_statement_source_contexts forensic_documents forensic_document_assertions forensic_statement_claim_bindings forensic_statement_relations forensic_temporal_consistency_assessments forensic_documentary_snapshots)
for t in "${V249_TABLES[@]}"; do v="$(psqlq "SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema='public' AND table_name='$t');")"; echo "$t=$v"; [ "$v" = t ] || { echo "STOP: predecessor v2.49 table missing: $t"; exit 1; }; done
V250_TABLES=(forensic_research_graphs forensic_research_graph_nodes forensic_research_graph_edges forensic_research_graph_views forensic_research_graph_handoffs forensic_research_graph_snapshots forensic_research_graph_packages)
v250_count=0
for t in "${V250_TABLES[@]}"; do v="$(psqlq "SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema='public' AND table_name='$t');")"; echo "$t=$v"; [ "$v" = t ] && v250_count=$((v250_count+1)); done
M54="$(psqlq "SELECT EXISTS (SELECT 1 FROM schema_migrations WHERE version='0054');")"; echo "schema_migrations.0054=$M54"; echo "forensic_research_graph_tables_present=$v250_count/7"
if [ "$M54" = f ] && [ "$v250_count" -eq 0 ]; then echo "PASS: pristine pre-0054 research-graph state accepted";
elif [ "$M54" = f ] && [ "$v250_count" -eq 7 ]; then echo "PASS: safe partial-0054 research-graph table state detected and accepted";
elif [ "$M54" = t ] && [ "$v250_count" -eq 7 ]; then echo "PASS: migration 0054 already recorded with complete research-graph schema";
else echo "STOP: inconsistent research-graph migration state (0054=$M54, tables=$v250_count/7)"; exit 1; fi
echo; echo "=== BACKUP CURRENT CORE + DATABASE ==="; mkdir -p "$BACKUP"; tar --exclude='.git' -czf "$BACKUP/core-before-v2.50.0.tar.gz" .; docker exec -e PGPASSWORD="$DB_PASS" sc-postgres pg_dump -h 127.0.0.1 -U "$DB_USER" -d "$DB_NAME" -Fc > "$BACKUP/platform-core-before-v2.50.0.dump"; ls -lh "$BACKUP"/*
echo; echo "=== FETCH EXACT v2.50.0 RELEASE ==="; git fetch origin --tags; git rev-parse v2.50.0 >/dev/null 2>&1 || { echo "STOP: v2.50.0 tag is not available from GitHub"; exit 1; }; git pull --ff-only origin main; echo "HEAD: $(git log -1 --oneline)"; git tag --points-at HEAD | grep -qx 'v2.50.0' || { echo "STOP: production HEAD is not exactly tagged v2.50.0"; exit 1; }
head_commit="$(git rev-parse HEAD)"; tag_commit="$(git rev-list -n 1 v2.50.0)"; [ "$head_commit" = "$tag_commit" ] || { echo "STOP: v2.50.0 does not resolve to production HEAD"; exit 1; }
python3 - <<'PY2'
import ast,re
from pathlib import Path
mig=Path('backend/app/migrations.py'); tree=ast.parse(mig.read_text(),filename=str(mig)); migrations=None
for node in tree.body:
    if isinstance(node,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='MIGRATIONS' for t in node.targets): migrations=ast.literal_eval(node.value); break
assert migrations and migrations[-1][0]=='0054',migrations[-1]
models=Path('backend/app/models.py').read_text(); m=re.search(r'class\s+SchemaMigration\b.*?description:\s*Mapped\[str\]\s*=\s*mapped_column\(String\((\d+)\)',models,re.S); assert m
mx=int(m.group(1)); d=dict(migrations)['0054']; assert mx==300 and len(d)<=mx,(mx,len(d)); print(f'PASS: packaged 0054 migration description fits VARCHAR({mx}) at {len(d)} chars')
PY2
echo; echo "=== BUILD CORE v2.50.0 ==="; $COMPOSE build core
echo; echo "=== APPLY / REPAIR MIGRATION 0054 ==="; $COMPOSE run --rm --no-deps core python scripts/migrate.py | tee /tmp/sc-core-v2500-migrations.json
echo; echo "=== VERIFY DATABASE CONTRACT BEFORE RECREATE ==="
for t in "${V250_TABLES[@]}"; do [ "$(psqlq "SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema='public' AND table_name='$t');")" = t ] || { echo "STOP: $t missing after migration 0054"; exit 1; }; done
M54_POST="$(psqlq "SELECT EXISTS (SELECT 1 FROM schema_migrations WHERE version='0054');")"; [ "$M54_POST" = t ] || { echo "STOP: migration 0054 not recorded"; exit 1; }; D54_LEN="$(psqlq "SELECT length(description) FROM schema_migrations WHERE version='0054';")"; echo "schema_migrations.0054.description_length=$D54_LEN"; [ "$D54_LEN" -le 300 ] || { echo "STOP: stored 0054 description exceeds production contract"; exit 1; }; echo "PASS: migration 0054 complete; predecessor documentary evidence schema preserved"
echo; echo "=== RECREATE sc-core ==="; $COMPOSE up -d --no-deps --force-recreate core
for i in $(seq 1 40); do if curl -fsS http://127.0.0.1:8090/health >/tmp/sc-core-v2500-health.json 2>/dev/null; then break; fi; [ "$i" -lt 40 ] || { docker logs --tail 200 sc-core; exit 1; }; sleep 2; done
for i in $(seq 1 40); do state="$(docker inspect --format '{{if .State.Health}}{{.State.Health.Status}}{{else}}none{{end}}' sc-core)"; echo "health=$state"; [ "$state" = healthy ] && break; [ "$state" != unhealthy ] || { docker logs --tail 200 sc-core; exit 1; }; [ "$i" -lt 40 ] || { docker logs --tail 200 sc-core; exit 1; }; sleep 2; done
echo; echo "=== LIVE HEALTH ==="; python3 -m json.tool </tmp/sc-core-v2500-health.json
echo; echo "=== FORENSIC RESEARCH GRAPH READINESS ==="; curl -fsS http://127.0.0.1:8090/v1/open-forensics/readiness | tee /tmp/sc-core-v2500-forensics.json | python3 -m json.tool
python3 - <<'PY2'
import json
h=json.load(open('/tmp/sc-core-v2500-health.json')); r=json.load(open('/tmp/sc-core-v2500-forensics.json'))
assert h.get('ok') is True and h.get('version')=='2.50.0',h; assert h.get('open_forensics') is True,h; assert h.get('forensic_research_graph') is True,h
assert r.get('release')=='2.50.0' and r.get('migration_0054_applied') is True,r
for key in ('forensic_research_graph_registry_by_core','cross_forensics_node_binding_by_core','explicit_graph_edge_registry_by_core','renderer_neutral_forensic_graph_specification_by_core','cross_product_graph_handoffs_by_core','immutable_forensic_graph_snapshots_by_core','portable_forensic_graph_packages_by_core'): assert r.get(key) is True,(key,r)
for key in ('automatic_graph_edge_inference_by_core','automatic_entity_resolution_by_core','automatic_identity_resolution_by_core','automatic_causal_inference_by_core','relationship_truth_determination_by_core','graph_analytics_execution_by_core','remote_product_fetch_by_core','automatic_truth_promotion'): assert r.get(key) is False,(key,r)
print('PASS: Platform Core v2.50.0'); print('PASS: Forensic Research Graph'); print('PASS: migration 0054 additive with explicit cross-forensics graph and non-inference boundaries intact')
PY2
echo; echo "=== VERIFY MIGRATION STATE ==="; docker exec sc-core python scripts/migrate.py | tee /tmp/sc-core-v2500-migration-state.json
python3 - <<'PY2'
import json
m=json.load(open('/tmp/sc-core-v2500-migration-state.json')); assert '0054' in m.get('applied',[]) and m.get('pending')==[],m; print('PASS: migration 0054 applied and pending=[]')
PY2
echo; echo "=== VERIFY PERSISTENT SCIENTIFIC STORAGE MOUNT ==="; docker exec sc-core sh -lc 'test -d /data/scientific-objects; touch /data/scientific-objects/.v2500-write-test; rm /data/scientific-objects/.v2500-write-test; echo "PASS: persistent scientific-object storage writable"'
echo; echo "=== PUBLIC CADDY ROUTE ==="; curl -fsS https://core.sustainablecatalyst.com/health | python3 -c 'import json,sys;d=json.load(sys.stdin);assert d.get("version")=="2.50.0",d;print("PASS: public Core health 2.50.0")'; curl -fsS https://core.sustainablecatalyst.com/v1/open-forensics/readiness | python3 -c 'import json,sys;d=json.load(sys.stdin);assert d.get("release")=="2.50.0" and d.get("migration_0054_applied") is True,d;print("PASS: public Forensic Research Graph readiness")'
echo; echo "=== FINAL CONTAINER ==="; docker ps --filter name=sc-core --format 'table {{.Names}}\t{{.Image}}\t{{.Status}}\t{{.Ports}}'
echo "Backup retained at: $BACKUP"; echo "============================================================"; echo " PLATFORM CORE v2.50.0 BACKEND DEPLOYMENT COMPLETE"; echo "============================================================"
