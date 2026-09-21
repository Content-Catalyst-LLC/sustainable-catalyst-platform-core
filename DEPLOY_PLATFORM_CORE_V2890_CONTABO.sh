#!/usr/bin/env bash
set -euo pipefail
trap 'rc=$?; echo "ERROR: v2.89.0 deployment stopped at line $LINENO (exit $rc): $BASH_COMMAND" >&2; exit $rc' ERR
ROOT="${SC_CORE_ROOT:-/opt/sustainable-catalyst/core}"; COMPOSE="docker compose -f compose.yml -f compose.vps.yml"; cd "$ROOT"
echo "=== PLATFORM CORE v2.89.0 — RESEARCH QUALITY, BIAS & METHODOLOGICAL AUDIT ENGINE ==="
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
[ "$(psqlq "SELECT EXISTS (SELECT 1 FROM schema_migrations WHERE version='0092');")" = t ] || { echo "STOP: migration 0092 missing; deploy v2.88.0 first"; exit 1; }
V288_TABLES=(research_inferences_v288 research_inference_classifications_v288 research_inference_basis_bindings_v288 research_inference_assumptions_v288 research_inference_uncertainty_v288 research_inference_relations_v288 research_inference_challenges_v288 research_inference_revisions_v288 research_inference_snapshots_v288)
for t in "${V288_TABLES[@]}"; do [ "$(psqlq "SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema='public' AND table_name='$t');")" = t ] || { echo "STOP: predecessor table missing: $t"; exit 1; }; done
V289_TABLES=(research_quality_audits_v289 research_quality_audit_subjects_v289 research_quality_audit_checks_v289 research_quality_audit_findings_v289 research_quality_audit_evidence_v289 research_quality_bias_assessments_v289 research_quality_method_assessments_v289 research_quality_audit_responses_v289 research_quality_audit_revisions_v289 research_quality_audit_snapshots_v289)
count=0; for t in "${V289_TABLES[@]}"; do [ "$(psqlq "SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema='public' AND table_name='$t');")" = t ] && count=$((count+1)); done
m93="$(psqlq "SELECT EXISTS (SELECT 1 FROM schema_migrations WHERE version='0093');")"
if [ "$m93" = f ] && [ "$count" -eq 0 ]; then echo "PASS: pristine pre-0093 state"; elif [ "$m93" = f ] && [ "$count" -eq 10 ]; then echo "PASS: recoverable partial-0093 state"; elif [ "$m93" = t ] && [ "$count" -eq 10 ]; then echo "PASS: already-complete 0093 state"; else echo "STOP: inconsistent 0093 state ($m93, $count/10)"; exit 1; fi
echo "=== BACKUP ==="; BACKUP_DIR="/opt/sustainable-catalyst/backups/platform-core-v2890"; mkdir -p "$BACKUP_DIR"; stamp="$(date +%Y%m%d-%H%M%S)"; docker exec -e PGPASSWORD="$DB_PASS" sc-postgres pg_dump -h 127.0.0.1 -U "$DB_USER" -d "$DB_NAME" -Fc > "$BACKUP_DIR/core-${stamp}.dump"; git rev-parse HEAD > "$BACKUP_DIR/git-head-${stamp}.txt"; tar --exclude='.git' --exclude='backend/.venv' -czf "$BACKUP_DIR/core-source-${stamp}.tar.gz" .
echo "=== PROMOTE TAGGED SOURCE ==="; git fetch origin --tags; git pull --ff-only origin main; git tag --points-at HEAD | grep -qx 'v2.89.0' || { echo "STOP: production HEAD is not tagged v2.89.0"; exit 1; }; python3 -S scripts/validate_v2890_release.py
echo "=== BUILD / MIGRATE ==="; $COMPOSE build core; $COMPOSE run --rm --no-deps core python scripts/migrate.py | tee /tmp/sc-core-v2890-migrate.json
for t in "${V289_TABLES[@]}"; do [ "$(psqlq "SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema='public' AND table_name='$t');")" = t ] || { echo "STOP: $t missing after migration"; exit 1; }; done
[ "$(psqlq "SELECT EXISTS (SELECT 1 FROM schema_migrations WHERE version='0093');")" = t ] || { echo "STOP: migration 0093 not recorded"; exit 1; }
$COMPOSE up -d --no-deps --force-recreate core
for i in $(seq 1 40); do curl -fsS http://127.0.0.1:8090/health >/tmp/sc-core-v2890-health.json 2>/dev/null && break; sleep 2; done
curl -fsS http://127.0.0.1:8090/v1/research/quality-audits/readiness | tee /tmp/sc-core-v2890-quality.json | python3 -m json.tool
python3 - <<'PY2'
import json
h=json.load(open('/tmp/sc-core-v2890-health.json')); r=json.load(open('/tmp/sc-core-v2890-quality.json'))
assert h.get('ok') is True and h.get('version')=='2.89.0',h; assert r.get('release')=='2.89.0' and r.get('migration_0093_applied') is True,r
for k in ('quality_audit_registry_by_core','audit_subject_registry_by_core','systematic_audit_check_registry_by_core','audit_finding_registry_by_core','audit_evidence_binding_by_core','declared_bias_assessment_registry_by_core','method_assessment_registry_by_core','audit_response_registry_by_core','audit_coverage_summary_by_core','audit_revision_history_by_core','audit_lineage_by_core','immutable_audit_snapshots_by_core'): assert r.get(k) is True,(k,r)
for k in ('infer_bias_by_core','score_research_quality_by_core','rank_studies_by_core','determine_method_validity_by_core','infer_confounding_by_core','determine_causal_validity_by_core','resolve_contradictions_by_core','verify_citation_support_by_core','certify_reproducibility_by_core','certify_ethics_by_core','reject_research_by_core','determine_truth_by_core'): assert r.get(k) is False,(k,r)
print('PASS - Platform Core v2.89.0 Research Quality, Bias & Methodological Audit Engine')
PY2
curl -fsS https://core.sustainablecatalyst.com/health | python3 -m json.tool
echo "PASS - PLATFORM CORE v2.89.0 BACKEND DEPLOYMENT COMPLETE"
