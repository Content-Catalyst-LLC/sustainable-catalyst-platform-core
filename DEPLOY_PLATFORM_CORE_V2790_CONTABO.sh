#!/usr/bin/env bash
set -euo pipefail
trap 'rc=$?; echo "ERROR: v2.79.0 deployment stopped at line $LINENO (exit $rc): $BASH_COMMAND" >&2; exit $rc' ERR

ROOT="${SC_CORE_ROOT:-/opt/sustainable-catalyst/core}"
COMPOSE="docker compose -f compose.yml -f compose.vps.yml"
cd "$ROOT"
echo "=== PLATFORM CORE v2.79.0 — RESEARCH ARGUMENT & EVIDENTIARY SYNTHESIS ENGINE ==="
[ -f .env.production ] || { echo "STOP: .env.production missing"; exit 1; }
if ! git diff --quiet || ! git diff --cached --quiet; then echo "STOP: production tree has local changes"; exit 1; fi

CORE_DB_URL="$(grep -m1 '^SC_CORE_DATABASE_URL=' .env.production | cut -d= -f2-)"
eval "$(CORE_DB_URL="$CORE_DB_URL" python3 - <<'PY2'
import os, shlex
from urllib.parse import urlparse, unquote
u = urlparse(os.environ['CORE_DB_URL'].strip().strip('"').strip("'"))
print('DB_USER=' + shlex.quote(unquote(u.username or '')))
print('DB_PASS=' + shlex.quote(unquote(u.password or '')))
print('DB_NAME=' + shlex.quote((u.path or '').lstrip('/')))
PY2
)"
psqlq(){ docker exec -e PGPASSWORD="$DB_PASS" sc-postgres psql -h 127.0.0.1 -U "$DB_USER" -d "$DB_NAME" -Atqc "$1"; }

echo "=== PREDECESSOR GATE ==="
[ "$(psqlq "SELECT EXISTS (SELECT 1 FROM schema_migrations WHERE version='0082');")" = t ] || { echo "STOP: migration 0082 missing; deploy v2.78.0 first"; exit 1; }
V278_TABLES=(research_hypothesis_sets_v278 research_hypotheses_v278 research_hypothesis_revisions_v278 research_hypothesis_evidence_assessments_v278 research_hypothesis_predictions_v278 research_hypothesis_assumptions_v278 research_hypothesis_relations_v278 research_hypothesis_discrimination_gaps_v278 research_hypothesis_snapshots_v278)
for t in "${V278_TABLES[@]}"; do
  [ "$(psqlq "SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema='public' AND table_name='$t');")" = t ] || { echo "STOP: predecessor table missing: $t"; exit 1; }
done

V279_TABLES=(research_arguments_v279 research_argument_nodes_v279 research_argument_edges_v279 research_evidentiary_syntheses_v279 research_synthesis_components_v279 research_counterarguments_v279 research_argument_tensions_v279 research_argument_revisions_v279 research_argument_snapshots_v279)
count=0
for t in "${V279_TABLES[@]}"; do
  [ "$(psqlq "SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema='public' AND table_name='$t');")" = t ] && count=$((count+1))
done
m83="$(psqlq "SELECT EXISTS (SELECT 1 FROM schema_migrations WHERE version='0083');")"
if [ "$m83" = f ] && [ "$count" -eq 0 ]; then
  echo "PASS: pristine pre-0083 state"
elif [ "$m83" = f ] && [ "$count" -eq 9 ]; then
  echo "PASS: recoverable partial-0083 state"
elif [ "$m83" = t ] && [ "$count" -eq 9 ]; then
  echo "PASS: already-complete 0083 state"
else
  echo "STOP: inconsistent 0083 state ($m83, $count/9)"
  exit 1
fi

echo "=== BACKUP ==="
BACKUP_DIR="/opt/sustainable-catalyst/backups/platform-core-v2790"
mkdir -p "$BACKUP_DIR"
stamp="$(date +%Y%m%d-%H%M%S)"
docker exec -e PGPASSWORD="$DB_PASS" sc-postgres pg_dump -h 127.0.0.1 -U "$DB_USER" -d "$DB_NAME" -Fc > "$BACKUP_DIR/core-${stamp}.dump"
git rev-parse HEAD > "$BACKUP_DIR/git-head-${stamp}.txt"
tar --exclude='.git' --exclude='backend/.venv' -czf "$BACKUP_DIR/core-source-${stamp}.tar.gz" .

echo "=== PROMOTE TAGGED SOURCE ==="
git fetch origin --tags
git pull --ff-only origin main
git tag --points-at HEAD | grep -qx 'v2.79.0' || { echo "STOP: production HEAD is not tagged v2.79.0"; exit 1; }
python3 -S scripts/validate_v2790_release.py

echo "=== BUILD / MIGRATE ==="
$COMPOSE build core
$COMPOSE run --rm --no-deps core python scripts/migrate.py | tee /tmp/sc-core-v2790-migrate.json
for t in "${V279_TABLES[@]}"; do
  [ "$(psqlq "SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema='public' AND table_name='$t');")" = t ] || { echo "STOP: $t missing after migration"; exit 1; }
done
[ "$(psqlq "SELECT EXISTS (SELECT 1 FROM schema_migrations WHERE version='0083');")" = t ] || { echo "STOP: migration 0083 not recorded"; exit 1; }

$COMPOSE up -d --no-deps --force-recreate core
for i in $(seq 1 40); do
  curl -fsS http://127.0.0.1:8090/health >/tmp/sc-core-v2790-health.json 2>/dev/null && break
  sleep 2
done
curl -fsS http://127.0.0.1:8090/v1/research/arguments/readiness | tee /tmp/sc-core-v2790-arguments.json | python3 -m json.tool
python3 - <<'PY2'
import json
h = json.load(open('/tmp/sc-core-v2790-health.json'))
r = json.load(open('/tmp/sc-core-v2790-arguments.json'))
assert h.get('ok') is True and h.get('version') == '2.79.0', h
assert r.get('release') == '2.79.0' and r.get('migration_0083_applied') is True, r
for k in (
    'argument_registry_by_core', 'declared_argument_graph_by_core',
    'researcher_authored_synthesis_registry_by_core', 'counterargument_registry_by_core',
    'unresolved_tension_registry_by_core', 'descriptive_coverage_summary_by_core',
    'argument_version_history_by_core', 'immutable_argument_snapshots_by_core',
):
    assert r.get(k) is True, (k, r)
for k in (
    'generate_argument_by_core', 'generate_synthesis_by_core', 'infer_argument_relation_by_core',
    'score_evidence_by_core', 'rank_arguments_by_core', 'select_best_argument_by_core',
    'resolve_tensions_by_core', 'infer_truth_by_core', 'publish_by_core',
):
    assert r.get(k) is False, (k, r)
print('PASS - Platform Core v2.79.0 Research Argument & Evidentiary Synthesis Engine')
PY2
curl -fsS https://core.sustainablecatalyst.com/health | python3 -m json.tool
echo "PASS - PLATFORM CORE v2.79.0 BACKEND DEPLOYMENT COMPLETE"
