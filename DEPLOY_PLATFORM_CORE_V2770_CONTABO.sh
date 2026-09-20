#!/usr/bin/env bash
set -euo pipefail
trap 'rc=$?; echo "ERROR: v2.77.0 deployment stopped at line $LINENO (exit $rc): $BASH_COMMAND" >&2; exit $rc' ERR
ROOT="${SC_CORE_ROOT:-/opt/sustainable-catalyst/core}";COMPOSE="docker compose -f compose.yml -f compose.vps.yml";cd "$ROOT"
echo "=== PLATFORM CORE v2.77.0 — FINDING, CLAIM & EVIDENCE INTELLIGENCE ==="
[ -f .env.production ] || { echo "STOP: .env.production missing";exit 1;}
if ! git diff --quiet || ! git diff --cached --quiet;then echo "STOP: production tree has local changes";exit 1;fi
CORE_DB_URL="$(grep -m1 '^SC_CORE_DATABASE_URL=' .env.production|cut -d= -f2-)"
eval "$(CORE_DB_URL="$CORE_DB_URL" python3 - <<'PY2'
import os,shlex
from urllib.parse import urlparse,unquote
u=urlparse(os.environ['CORE_DB_URL'].strip().strip('"').strip("'"));print('DB_USER='+shlex.quote(unquote(u.username or '')));print('DB_PASS='+shlex.quote(unquote(u.password or '')));print('DB_NAME='+shlex.quote((u.path or '').lstrip('/')))
PY2
)"
psqlq(){ docker exec -e PGPASSWORD="$DB_PASS" sc-postgres psql -h 127.0.0.1 -U "$DB_USER" -d "$DB_NAME" -Atqc "$1";}
echo "=== PREDECESSOR GATE ==="
[ "$(psqlq "SELECT EXISTS (SELECT 1 FROM schema_migrations WHERE version='0080');")" = t ] || { echo "STOP: migration 0080 missing; deploy v2.76.0 first";exit 1;}
V276_TABLES=(research_notebooks research_notebook_sections research_notebook_entries research_notebook_bindings research_notebook_citations research_analytical_narratives research_analytical_narrative_blocks research_notebook_revisions research_notebook_snapshots)
for t in "${V276_TABLES[@]}";do [ "$(psqlq "SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema='public' AND table_name='$t');")" = t ] || { echo "STOP: predecessor table missing: $t";exit 1;};done
V277_TABLES=(research_findings research_finding_revisions research_interpretations research_claims_v277 research_claim_revisions_v277 research_evidence_links_v277 research_derivation_links_v277 research_contradictions_v277 research_intelligence_snapshots_v277)
count=0;for t in "${V277_TABLES[@]}";do [ "$(psqlq "SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema='public' AND table_name='$t');")" = t ] && count=$((count+1));done
m81="$(psqlq "SELECT EXISTS (SELECT 1 FROM schema_migrations WHERE version='0081');")"
if [ "$m81" = f ] && [ "$count" -eq 0 ];then echo "PASS: pristine pre-0081 state";elif [ "$m81" = f ] && [ "$count" -eq 9 ];then echo "PASS: recoverable partial-0081 state";elif [ "$m81" = t ] && [ "$count" -eq 9 ];then echo "PASS: already-complete 0081 state";else echo "STOP: inconsistent 0081 state ($m81, $count/9)";exit 1;fi
echo "=== BACKUP ===";BACKUP_DIR="/opt/sustainable-catalyst/backups/platform-core-v2770";mkdir -p "$BACKUP_DIR";stamp="$(date +%Y%m%d-%H%M%S)";docker exec -e PGPASSWORD="$DB_PASS" sc-postgres pg_dump -h 127.0.0.1 -U "$DB_USER" -d "$DB_NAME" -Fc > "$BACKUP_DIR/core-${stamp}.dump";git rev-parse HEAD > "$BACKUP_DIR/git-head-${stamp}.txt";tar --exclude='.git' --exclude='backend/.venv' -czf "$BACKUP_DIR/core-source-${stamp}.tar.gz" .
git fetch origin --tags;git pull --ff-only origin main;git tag --points-at HEAD|grep -qx 'v2.77.0' || { echo "STOP: production HEAD is not tagged v2.77.0";exit 1;}
python3 -S scripts/validate_v2770_release.py
$COMPOSE build core
$COMPOSE run --rm --no-deps core python scripts/migrate.py | tee /tmp/sc-core-v2770-migrate.json
for t in "${V277_TABLES[@]}";do [ "$(psqlq "SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema='public' AND table_name='$t');")" = t ] || { echo "STOP: $t missing after migration";exit 1;};done
[ "$(psqlq "SELECT EXISTS (SELECT 1 FROM schema_migrations WHERE version='0081');")" = t ] || { echo "STOP: migration 0081 not recorded";exit 1;}
$COMPOSE up -d --no-deps --force-recreate core
for i in $(seq 1 40);do curl -fsS http://127.0.0.1:8090/health >/tmp/sc-core-v2770-health.json 2>/dev/null && break;sleep 2;done
curl -fsS http://127.0.0.1:8090/v1/research/intelligence/readiness | tee /tmp/sc-core-v2770-intelligence.json | python3 -m json.tool
python3 - <<'PY2'
import json
h=json.load(open('/tmp/sc-core-v2770-health.json'));r=json.load(open('/tmp/sc-core-v2770-intelligence.json'))
assert h.get('ok') is True and h.get('version')=='2.77.0',h
assert r.get('release')=='2.77.0' and r.get('migration_0081_applied') is True,r
for k in ('finding_registry_by_core','interpretation_registry_by_core','claim_registry_by_core','evidence_link_registry_by_core','finding_claim_version_history_by_core','derivation_lineage_registry_by_core','deterministic_structured_contradiction_candidates_by_core','immutable_research_intelligence_snapshots_by_core'):assert r.get(k) is True,(k,r)
for k in ('infer_truth_by_core','rank_claims_by_core','generate_claim_by_core','generate_finding_by_core','judge_evidence_by_core','semantic_contradiction_inference_by_core','resolve_contradiction_by_core','publish_by_core','alter_source_artifacts_by_core'):assert r.get(k) is False,(k,r)
print('PASS - Platform Core v2.77.0 Finding, Claim & Evidence Intelligence')
PY2
curl -fsS https://core.sustainablecatalyst.com/health | python3 -m json.tool
echo "PASS - PLATFORM CORE v2.77.0 BACKEND DEPLOYMENT COMPLETE"
