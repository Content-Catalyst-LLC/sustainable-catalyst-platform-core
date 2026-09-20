#!/usr/bin/env bash
set -euo pipefail
trap 'rc=$?; echo "ERROR: v2.80.0 deployment stopped at line $LINENO (exit $rc): $BASH_COMMAND" >&2; exit $rc' ERR
ROOT="${SC_CORE_ROOT:-/opt/sustainable-catalyst/core}"; COMPOSE="docker compose -f compose.yml -f compose.vps.yml"; cd "$ROOT"
echo "=== PLATFORM CORE v2.80.0 — RESEARCH DECISION TRACE & CONCLUSION GOVERNANCE ==="
[ -f .env.production ] || { echo "STOP: .env.production missing"; exit 1; }
if ! git diff --quiet || ! git diff --cached --quiet; then echo "STOP: production tree has local changes"; exit 1; fi
CORE_DB_URL="$(grep -m1 '^SC_CORE_DATABASE_URL=' .env.production | cut -d= -f2-)"
eval "$(CORE_DB_URL="$CORE_DB_URL" python3 - <<'PY2'
import os,shlex
from urllib.parse import urlparse,unquote
u=urlparse(os.environ['CORE_DB_URL'].strip().strip('"').strip("'")); print('DB_USER='+shlex.quote(unquote(u.username or ''))); print('DB_PASS='+shlex.quote(unquote(u.password or ''))); print('DB_NAME='+shlex.quote((u.path or '').lstrip('/')))
PY2
)"
psqlq(){ docker exec -e PGPASSWORD="$DB_PASS" sc-postgres psql -h 127.0.0.1 -U "$DB_USER" -d "$DB_NAME" -Atqc "$1"; }
echo "=== PREDECESSOR GATE ==="
[ "$(psqlq "SELECT EXISTS (SELECT 1 FROM schema_migrations WHERE version='0083');")" = t ] || { echo "STOP: migration 0083 missing; deploy v2.79.0 first"; exit 1; }
V279_TABLES=(research_arguments_v279 research_argument_nodes_v279 research_argument_edges_v279 research_evidentiary_syntheses_v279 research_synthesis_components_v279 research_counterarguments_v279 research_argument_tensions_v279 research_argument_revisions_v279 research_argument_snapshots_v279)
for t in "${V279_TABLES[@]}"; do [ "$(psqlq "SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema='public' AND table_name='$t');")" = t ] || { echo "STOP: predecessor table missing: $t"; exit 1; }; done
V280_TABLES=(research_conclusions_v280 research_conclusion_evidence_bindings_v280 research_conclusion_caveats_v280 research_conclusion_dissent_v280 research_decision_traces_v280 research_conclusion_reviews_v280 research_conclusion_revisions_v280 research_conclusion_snapshots_v280)
count=0; for t in "${V280_TABLES[@]}"; do [ "$(psqlq "SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema='public' AND table_name='$t');")" = t ] && count=$((count+1)); done
m84="$(psqlq "SELECT EXISTS (SELECT 1 FROM schema_migrations WHERE version='0084');")"
if [ "$m84" = f ] && [ "$count" -eq 0 ]; then echo "PASS: pristine pre-0084 state"; elif [ "$m84" = f ] && [ "$count" -eq 8 ]; then echo "PASS: recoverable partial-0084 state"; elif [ "$m84" = t ] && [ "$count" -eq 8 ]; then echo "PASS: already-complete 0084 state"; else echo "STOP: inconsistent 0084 state ($m84, $count/8)"; exit 1; fi
echo "=== BACKUP ==="; BACKUP_DIR="/opt/sustainable-catalyst/backups/platform-core-v2800"; mkdir -p "$BACKUP_DIR"; stamp="$(date +%Y%m%d-%H%M%S)"; docker exec -e PGPASSWORD="$DB_PASS" sc-postgres pg_dump -h 127.0.0.1 -U "$DB_USER" -d "$DB_NAME" -Fc > "$BACKUP_DIR/core-${stamp}.dump"; git rev-parse HEAD > "$BACKUP_DIR/git-head-${stamp}.txt"; tar --exclude='.git' --exclude='backend/.venv' -czf "$BACKUP_DIR/core-source-${stamp}.tar.gz" .
echo "=== PROMOTE TAGGED SOURCE ==="; git fetch origin --tags; git pull --ff-only origin main; git tag --points-at HEAD | grep -qx 'v2.80.0' || { echo "STOP: production HEAD is not tagged v2.80.0"; exit 1; }; python3 -S scripts/validate_v2800_release.py
echo "=== BUILD / MIGRATE ==="; $COMPOSE build core; $COMPOSE run --rm --no-deps core python scripts/migrate.py | tee /tmp/sc-core-v2800-migrate.json
for t in "${V280_TABLES[@]}"; do [ "$(psqlq "SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema='public' AND table_name='$t');")" = t ] || { echo "STOP: $t missing after migration"; exit 1; }; done
[ "$(psqlq "SELECT EXISTS (SELECT 1 FROM schema_migrations WHERE version='0084');")" = t ] || { echo "STOP: migration 0084 not recorded"; exit 1; }
$COMPOSE up -d --no-deps --force-recreate core
for i in $(seq 1 40); do curl -fsS http://127.0.0.1:8090/health >/tmp/sc-core-v2800-health.json 2>/dev/null && break; sleep 2; done
curl -fsS http://127.0.0.1:8090/v1/research/conclusions/readiness | tee /tmp/sc-core-v2800-conclusions.json | python3 -m json.tool
python3 - <<'PY2'
import json
h=json.load(open('/tmp/sc-core-v2800-health.json')); r=json.load(open('/tmp/sc-core-v2800-conclusions.json'))
assert h.get('ok') is True and h.get('version')=='2.80.0',h; assert r.get('release')=='2.80.0' and r.get('migration_0084_applied') is True,r
for k in ('researcher_authored_conclusion_registry_by_core','declared_evidence_binding_registry_by_core','caveat_registry_by_core','dissent_registry_by_core','decision_trace_registry_by_core','review_registry_by_core','descriptive_governance_summary_by_core','conclusion_version_history_by_core','immutable_conclusion_snapshots_by_core'): assert r.get(k) is True,(k,r)
for k in ('generate_conclusion_by_core','choose_conclusion_by_core','score_conclusion_by_core','rank_conclusions_by_core','certify_conclusion_by_core','resolve_dissent_by_core','auto_accept_review_by_core','infer_truth_by_core','publish_by_core'): assert r.get(k) is False,(k,r)
print('PASS - Platform Core v2.80.0 Research Decision Trace & Conclusion Governance')
PY2
curl -fsS https://core.sustainablecatalyst.com/health | python3 -m json.tool
echo "PASS - PLATFORM CORE v2.80.0 BACKEND DEPLOYMENT COMPLETE"
