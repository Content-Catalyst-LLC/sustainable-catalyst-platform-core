#!/usr/bin/env bash
set -euo pipefail
trap 'rc=$?; echo "ERROR: v2.47.0 Contabo deployment stopped at line $LINENO (exit $rc): $BASH_COMMAND" >&2; exit $rc' ERR
ROOT="/opt/sustainable-catalyst/core"; BACKUP_ROOT="/opt/sustainable-catalyst/backups"; COMPOSE="docker compose -f compose.yml -f compose.vps.yml"; STAMP="$(date +%Y%m%d-%H%M%S)"; BACKUP="${BACKUP_ROOT}/platform-core-v2.47.0-${STAMP}"
cd "$ROOT"
echo "============================================================"; echo " PLATFORM CORE v2.47.0 — MEDIA ARTIFACT & DERIVATIVE PROVENANCE"; echo "============================================================"
echo; echo "=== CURRENT LIVE HEALTH ==="; curl -fsS http://127.0.0.1:8090/health | python3 -m json.tool
echo; echo "=== SAFETY CHECKS ==="; [ -f compose.yml ] || { echo "STOP: compose.yml missing"; exit 1; }; [ -f compose.vps.yml ] || { echo "STOP: compose.vps.yml missing"; exit 1; }; [ -f .env.production ] || { echo "STOP: .env.production missing"; exit 1; }
if ! git diff --quiet || ! git diff --cached --quiet; then echo "STOP: tracked production files have local changes."; git status --short; exit 1; fi
$COMPOSE config >/tmp/sc-core-v2470-compose.yml; grep -q '/data/scientific-objects' /tmp/sc-core-v2470-compose.yml || { echo "STOP: scientific-object persistent mount missing"; exit 1; }
CORE_DB_URL="$(grep -m1 '^SC_CORE_DATABASE_URL=' .env.production | cut -d= -f2-)"; [ -n "$CORE_DB_URL" ] || { echo "STOP: SC_CORE_DATABASE_URL not found"; exit 1; }
eval "$(CORE_DB_URL="$CORE_DB_URL" python3 - <<'PY2'
import os,shlex
from urllib.parse import urlparse,unquote
u=urlparse(os.environ['CORE_DB_URL'].strip().strip('"').strip("'")); print('DB_USER='+shlex.quote(unquote(u.username or ''))); print('DB_PASS='+shlex.quote(unquote(u.password or ''))); print('DB_NAME='+shlex.quote((u.path or '').lstrip('/')))
PY2
)"
psqlq(){ docker exec -e PGPASSWORD="$DB_PASS" sc-postgres psql -h 127.0.0.1 -U "$DB_USER" -d "$DB_NAME" -Atqc "$1"; }
echo; echo "=== PRODUCTION PREDECESSOR PREFLIGHT ==="
M50="$(psqlq "SELECT EXISTS (SELECT 1 FROM schema_migrations WHERE version='0050');")"; echo "schema_migrations.0050=$M50"; [ "$M50" = t ] || { echo "STOP: migration 0050 is not recorded; v2.46.0 must be deployed first"; exit 1; }
V246_TABLES=(forensic_places forensic_evidence_spatial_bindings forensic_event_place_bindings forensic_spatial_uncertainty_envelopes forensic_trajectory_evidence forensic_spatial_temporal_intersections forensic_spatial_temporal_views forensic_spatial_temporal_snapshots)
for t in "${V246_TABLES[@]}"; do v="$(psqlq "SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema='public' AND table_name='$t');")"; echo "$t=$v"; [ "$v" = t ] || { echo "STOP: predecessor v2.46 table missing: $t"; exit 1; }; done
V247_TABLES=(forensic_media_artifacts forensic_media_derivations forensic_media_metadata_records forensic_media_fingerprints forensic_media_segments forensic_media_comparisons forensic_media_provenance_snapshots)
v247_count=0
for t in "${V247_TABLES[@]}"; do v="$(psqlq "SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema='public' AND table_name='$t');")"; echo "$t=$v"; [ "$v" = t ] && v247_count=$((v247_count+1)); done
M51="$(psqlq "SELECT EXISTS (SELECT 1 FROM schema_migrations WHERE version='0051');")"; echo "schema_migrations.0051=$M51"; echo "forensic_media_tables_present=$v247_count/7"
if [ "$M51" = f ] && [ "$v247_count" -eq 0 ]; then echo "PASS: pristine pre-0051 forensic media provenance state accepted";
elif [ "$M51" = f ] && [ "$v247_count" -eq 7 ]; then echo "PASS: safe partial-0051 forensic media table state detected and accepted";
elif [ "$M51" = t ] && [ "$v247_count" -eq 7 ]; then echo "PASS: migration 0051 already recorded with complete forensic media schema";
else echo "STOP: inconsistent forensic media migration state (0051=$M51, tables=$v247_count/7)"; exit 1; fi
echo; echo "=== BACKUP CURRENT CORE + DATABASE ==="; mkdir -p "$BACKUP"; tar --exclude='.git' -czf "$BACKUP/core-before-v2.47.0.tar.gz" .; docker exec -e PGPASSWORD="$DB_PASS" sc-postgres pg_dump -h 127.0.0.1 -U "$DB_USER" -d "$DB_NAME" -Fc > "$BACKUP/platform-core-before-v2.47.0.dump"; ls -lh "$BACKUP"/*
echo; echo "=== FETCH EXACT v2.47.0 RELEASE ==="; git fetch origin --tags; git rev-parse v2.47.0 >/dev/null 2>&1 || { echo "STOP: v2.47.0 tag is not available from GitHub"; exit 1; }; git pull --ff-only origin main; echo "HEAD: $(git log -1 --oneline)"; git tag --points-at HEAD | grep -qx 'v2.47.0' || { echo "STOP: production HEAD is not exactly tagged v2.47.0"; exit 1; }
head_commit="$(git rev-parse HEAD)"; tag_commit="$(git rev-list -n 1 v2.47.0)"; [ "$head_commit" = "$tag_commit" ] || { echo "STOP: v2.47.0 does not resolve to production HEAD"; exit 1; }
python3 - <<'PY2'
import ast,re
from pathlib import Path
mig=Path('backend/app/migrations.py'); tree=ast.parse(mig.read_text(),filename=str(mig)); migrations=None
for node in tree.body:
    if isinstance(node,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='MIGRATIONS' for t in node.targets): migrations=ast.literal_eval(node.value); break
assert migrations and migrations[-1][0]=='0051',migrations[-1]
models=Path('backend/app/models.py').read_text(); m=re.search(r'class\s+SchemaMigration\b.*?description:\s*Mapped\[str\]\s*=\s*mapped_column\(String\((\d+)\)',models,re.S); assert m
mx=int(m.group(1)); d=dict(migrations)['0051']; assert mx==300 and len(d)<=mx,(mx,len(d)); print(f'PASS: packaged 0051 migration description fits VARCHAR({mx}) at {len(d)} chars')
PY2
echo; echo "=== BUILD CORE v2.47.0 ==="; $COMPOSE build core
echo; echo "=== APPLY / REPAIR MIGRATION 0051 ==="; $COMPOSE run --rm --no-deps core python scripts/migrate.py | tee /tmp/sc-core-v2470-migrations.json
echo; echo "=== VERIFY DATABASE CONTRACT BEFORE RECREATE ==="
for t in "${V247_TABLES[@]}"; do [ "$(psqlq "SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema='public' AND table_name='$t');")" = t ] || { echo "STOP: $t missing after migration 0051"; exit 1; }; done
M51_POST="$(psqlq "SELECT EXISTS (SELECT 1 FROM schema_migrations WHERE version='0051');")"; [ "$M51_POST" = t ] || { echo "STOP: migration 0051 not recorded"; exit 1; }; D51_LEN="$(psqlq "SELECT length(description) FROM schema_migrations WHERE version='0051';")"; echo "schema_migrations.0051.description_length=$D51_LEN"; [ "$D51_LEN" -le 300 ] || { echo "STOP: stored 0051 description exceeds production contract"; exit 1; }; echo "PASS: migration 0051 complete; predecessor forensic spatial-temporal schema preserved"
echo; echo "=== RECREATE sc-core ==="; $COMPOSE up -d --no-deps --force-recreate core
for i in $(seq 1 40); do if curl -fsS http://127.0.0.1:8090/health >/tmp/sc-core-v2470-health.json 2>/dev/null; then break; fi; [ "$i" -lt 40 ] || { docker logs --tail 200 sc-core; exit 1; }; sleep 2; done
for i in $(seq 1 40); do state="$(docker inspect --format '{{if .State.Health}}{{.State.Health.Status}}{{else}}none{{end}}' sc-core)"; echo "health=$state"; [ "$state" = healthy ] && break; [ "$state" != unhealthy ] || { docker logs --tail 200 sc-core; exit 1; }; [ "$i" -lt 40 ] || { docker logs --tail 200 sc-core; exit 1; }; sleep 2; done
echo; echo "=== LIVE HEALTH ==="; python3 -m json.tool </tmp/sc-core-v2470-health.json
echo; echo "=== OPEN FORENSICS MEDIA PROVENANCE READINESS ==="; curl -fsS http://127.0.0.1:8090/v1/open-forensics/readiness | tee /tmp/sc-core-v2470-forensics.json | python3 -m json.tool
python3 - <<'PY2'
import json
h=json.load(open('/tmp/sc-core-v2470-health.json')); r=json.load(open('/tmp/sc-core-v2470-forensics.json'))
assert h.get('ok') is True and h.get('version')=='2.47.0',h; assert h.get('open_forensics') is True,h; assert h.get('forensic_media_artifact_derivative_provenance') is True,h
assert r.get('release')=='2.47.0' and r.get('migration_0051_applied') is True,r
for key in ('media_artifact_registry_by_core','declared_derivative_lineage_by_core','media_metadata_preservation_by_core','cryptographic_fingerprint_recording_by_core','perceptual_fingerprint_recording_by_core','frame_segment_reference_registry_by_core','provenance_aware_media_comparisons_by_core','immutable_media_provenance_snapshots_by_core'): assert r.get(key) is True,(key,r)
for key in ('media_decoding_by_core','perceptual_fingerprint_computation_by_core','media_similarity_execution_by_core','derivative_detection_by_core','authenticity_determination_from_media_by_core','manipulation_intent_determination_by_core','media_authorship_attribution_by_core','automatic_truth_promotion'): assert r.get(key) is False,(key,r)
print('PASS: Platform Core v2.47.0'); print('PASS: Media Artifact & Derivative Provenance'); print('PASS: migration 0051 additive with media provenance and non-authenticity/non-attribution boundaries intact')
PY2
echo; echo "=== VERIFY MIGRATION STATE ==="; docker exec sc-core python scripts/migrate.py | tee /tmp/sc-core-v2470-migration-state.json
python3 - <<'PY2'
import json
m=json.load(open('/tmp/sc-core-v2470-migration-state.json')); assert '0051' in m.get('applied',[]) and m.get('pending')==[],m; print('PASS: migration 0051 applied and pending=[]')
PY2
echo; echo "=== VERIFY PERSISTENT SCIENTIFIC STORAGE MOUNT ==="; docker exec sc-core sh -lc 'test -d /data/scientific-objects; touch /data/scientific-objects/.v2470-write-test; rm /data/scientific-objects/.v2470-write-test; echo "PASS: persistent scientific-object storage writable"'
echo; echo "=== PUBLIC CADDY ROUTE ==="; curl -fsS https://core.sustainablecatalyst.com/health | python3 -c 'import json,sys;d=json.load(sys.stdin);assert d.get("version")=="2.47.0",d;print("PASS: public Core health 2.47.0")'; curl -fsS https://core.sustainablecatalyst.com/v1/open-forensics/readiness | python3 -c 'import json,sys;d=json.load(sys.stdin);assert d.get("release")=="2.47.0" and d.get("migration_0051_applied") is True,d;print("PASS: public Media Artifact & Derivative Provenance readiness")'
echo; echo "=== FINAL CONTAINER ==="; docker ps --filter name=sc-core --format 'table {{.Names}}\t{{.Image}}\t{{.Status}}\t{{.Ports}}'; echo; echo "Backup retained at: $BACKUP"; echo "============================================================"; echo " PLATFORM CORE v2.47.0 BACKEND DEPLOYMENT COMPLETE"; echo "============================================================"
