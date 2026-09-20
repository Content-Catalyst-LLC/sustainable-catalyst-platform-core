#!/usr/bin/env bash
set -euo pipefail
trap 'rc=$?; echo "ERROR: v2.82.0 deployment stopped at line $LINENO (exit $rc): $BASH_COMMAND" >&2; exit $rc' ERR
ROOT="${SC_CORE_ROOT:-/opt/sustainable-catalyst/core}"; COMPOSE="docker compose -f compose.yml -f compose.vps.yml"; cd "$ROOT"
echo "=== PLATFORM CORE v2.82.0 — PEER REVIEW, REPLICATION & REBUTTAL INTELLIGENCE ==="
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
[ "$(psqlq "SELECT EXISTS (SELECT 1 FROM schema_migrations WHERE version='0085');")" = t ] || { echo "STOP: migration 0085 missing; deploy v2.81.0 first"; exit 1; }
V281_TABLES=(research_publications_v281 research_publication_sections_v281 research_publication_references_v281 research_publication_citations_v281 research_publication_figures_v281 research_publication_supplements_v281 research_publication_identifiers_v281 research_publication_exports_v281 research_publication_revisions_v281 research_publication_snapshots_v281)
for t in "${V281_TABLES[@]}"; do [ "$(psqlq "SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema='public' AND table_name='$t');")" = t ] || { echo "STOP: predecessor table missing: $t"; exit 1; }; done
V282_TABLES=(research_peer_reviews_v282 research_peer_review_comments_v282 research_peer_review_responses_v282 research_replication_studies_v282 research_replication_attempts_v282 research_replication_comparisons_v282 research_rebuttals_v282 research_rebuttal_points_v282 research_peer_review_revisions_v282 research_peer_review_snapshots_v282)
count=0; for t in "${V282_TABLES[@]}"; do [ "$(psqlq "SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema='public' AND table_name='$t');")" = t ] && count=$((count+1)); done
m86="$(psqlq "SELECT EXISTS (SELECT 1 FROM schema_migrations WHERE version='0086');")"
if [ "$m86" = f ] && [ "$count" -eq 0 ]; then echo "PASS: pristine pre-0086 state"; elif [ "$m86" = f ] && [ "$count" -eq 10 ]; then echo "PASS: recoverable partial-0086 state"; elif [ "$m86" = t ] && [ "$count" -eq 10 ]; then echo "PASS: already-complete 0086 state"; else echo "STOP: inconsistent 0086 state ($m86, $count/10)"; exit 1; fi
echo "=== BACKUP ==="; BACKUP_DIR="/opt/sustainable-catalyst/backups/platform-core-v2820"; mkdir -p "$BACKUP_DIR"; stamp="$(date +%Y%m%d-%H%M%S)"; docker exec -e PGPASSWORD="$DB_PASS" sc-postgres pg_dump -h 127.0.0.1 -U "$DB_USER" -d "$DB_NAME" -Fc > "$BACKUP_DIR/core-${stamp}.dump"; git rev-parse HEAD > "$BACKUP_DIR/git-head-${stamp}.txt"; tar --exclude='.git' --exclude='backend/.venv' -czf "$BACKUP_DIR/core-source-${stamp}.tar.gz" .
echo "=== PROMOTE TAGGED SOURCE ==="; git fetch origin --tags; git pull --ff-only origin main; git tag --points-at HEAD | grep -qx 'v2.82.0' || { echo "STOP: production HEAD is not tagged v2.82.0"; exit 1; }; python3 -S scripts/validate_v2820_release.py
echo "=== BUILD / MIGRATE ==="; $COMPOSE build core; $COMPOSE run --rm --no-deps core python scripts/migrate.py | tee /tmp/sc-core-v2820-migrate.json
for t in "${V282_TABLES[@]}"; do [ "$(psqlq "SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema='public' AND table_name='$t');")" = t ] || { echo "STOP: $t missing after migration"; exit 1; }; done
[ "$(psqlq "SELECT EXISTS (SELECT 1 FROM schema_migrations WHERE version='0086');")" = t ] || { echo "STOP: migration 0086 not recorded"; exit 1; }
$COMPOSE up -d --no-deps --force-recreate core
for i in $(seq 1 40); do curl -fsS http://127.0.0.1:8090/health >/tmp/sc-core-v2820-health.json 2>/dev/null && break; sleep 2; done
curl -fsS http://127.0.0.1:8090/v1/research/peer-review/readiness | tee /tmp/sc-core-v2820-peer-review.json | python3 -m json.tool
python3 - <<'PY2'
import json
h=json.load(open('/tmp/sc-core-v2820-health.json')); r=json.load(open('/tmp/sc-core-v2820-peer-review.json'))
assert h.get('ok') is True and h.get('version')=='2.82.0',h; assert r.get('release')=='2.82.0' and r.get('migration_0086_applied') is True,r
for k in ('peer_review_registry_by_core','review_comment_response_traceability_by_core','declared_reviewer_recommendation_registry_by_core','replication_study_registry_by_core','replication_attempt_registry_by_core','declared_replication_comparison_by_core','rebuttal_registry_by_core','rebuttal_point_evidence_traceability_by_core','review_replication_rebuttal_lineage_by_core','review_revision_history_by_core','immutable_review_snapshots_by_core'): assert r.get(k) is True,(k,r)
for k in ('generate_peer_review_by_core','recommend_acceptance_by_core','score_manuscript_quality_by_core','infer_replication_success_by_core','resolve_rebuttal_by_core','rank_reviewer_arguments_by_core','decide_publication_by_core','infer_truth_by_core'): assert r.get(k) is False,(k,r)
print('PASS - Platform Core v2.82.0 Peer Review, Replication & Rebuttal Intelligence')
PY2
curl -fsS https://core.sustainablecatalyst.com/health | python3 -m json.tool
echo "PASS - PLATFORM CORE v2.82.0 BACKEND DEPLOYMENT COMPLETE"
