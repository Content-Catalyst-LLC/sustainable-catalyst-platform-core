#!/usr/bin/env bash
set -euo pipefail
trap 'rc=$?; echo "ERROR: v2.90.0 deployment stopped at line $LINENO (exit $rc): $BASH_COMMAND" >&2; exit $rc' ERR
echo "=== PLATFORM CORE v2.90.0 — RESEARCH WORKFLOW & ORCHESTRATION ENGINE ==="
cd /opt/sustainable-catalyst/core
COMPOSE="docker compose -f compose.yml -f compose.vps.yml"
DB_USER="${POSTGRES_USER:-sc_core}"; DB_NAME="${POSTGRES_DB:-sc_core}"; DB_PASS="${POSTGRES_PASSWORD:-}"
psqlq(){ docker exec -e PGPASSWORD="$DB_PASS" sc-postgres psql -h 127.0.0.1 -U "$DB_USER" -d "$DB_NAME" -Atqc "$1"; }
V289_TABLES=('research_quality_audits_v289' 'research_quality_audit_subjects_v289' 'research_quality_audit_checks_v289' 'research_quality_audit_findings_v289' 'research_quality_audit_evidence_v289' 'research_quality_bias_assessments_v289' 'research_quality_method_assessments_v289' 'research_quality_audit_responses_v289' 'research_quality_audit_revisions_v289' 'research_quality_audit_snapshots_v289')
V290_TABLES=('research_workflows_v290' 'research_workflow_stages_v290' 'research_workflow_transitions_v290' 'research_workflow_context_bindings_v290' 'research_workflow_handoffs_v290' 'research_workflow_checkpoints_v290' 'research_workflow_events_v290' 'research_workflow_policies_v290' 'research_workflow_revisions_v290' 'research_workflow_snapshots_v290')
echo "=== PREDECESSOR GATE ==="
[ "$(psqlq "SELECT EXISTS (SELECT 1 FROM schema_migrations WHERE version='0093');")" = t ] || { echo "STOP: migration 0093 is required before v2.90.0"; exit 1; }
for t in "${V289_TABLES[@]}"; do [ "$(psqlq "SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema='public' AND table_name='$t');")" = t ] || { echo "STOP: predecessor table $t missing"; exit 1; }; done
m94="$(psqlq "SELECT EXISTS (SELECT 1 FROM schema_migrations WHERE version='0094');")"; count=0; for t in "${V290_TABLES[@]}"; do [ "$(psqlq "SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema='public' AND table_name='$t');")" = t ] && count=$((count+1)); done
if [ "$m94" = f ] && [ "$count" -eq 0 ]; then echo "PASS: pristine pre-0094 state"; elif [ "$m94" = f ] && [ "$count" -eq 10 ]; then echo "PASS: recoverable partial-0094 state"; elif [ "$m94" = t ] && [ "$count" -eq 10 ]; then echo "PASS: already-complete 0094 state"; else echo "STOP: inconsistent 0094 state ($m94, $count/10)"; exit 1; fi
echo "=== BACKUP ==="; BACKUP_DIR="/opt/sustainable-catalyst/backups/platform-core-v2900"; mkdir -p "$BACKUP_DIR"; stamp="$(date +%Y%m%d-%H%M%S)"; docker exec -e PGPASSWORD="$DB_PASS" sc-postgres pg_dump -h 127.0.0.1 -U "$DB_USER" -d "$DB_NAME" -Fc > "$BACKUP_DIR/core-${stamp}.dump"; git rev-parse HEAD > "$BACKUP_DIR/git-head-${stamp}.txt"; tar --exclude='.git' --exclude='backend/.venv' -czf "$BACKUP_DIR/core-source-${stamp}.tar.gz" .
echo "=== PROMOTE TAGGED SOURCE ==="; git fetch origin --tags; git pull --ff-only origin main; git tag --points-at HEAD | grep -qx 'v2.90.0' || { echo "STOP: production HEAD is not tagged v2.90.0"; exit 1; }; python3 -S scripts/validate_v2900_release.py
echo "=== BUILD / MIGRATE ==="; $COMPOSE build core; $COMPOSE run --rm --no-deps core python scripts/migrate.py | tee /tmp/sc-core-v2900-migrate.json
for t in "${V290_TABLES[@]}"; do [ "$(psqlq "SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema='public' AND table_name='$t');")" = t ] || { echo "STOP: $t missing after migration"; exit 1; }; done
[ "$(psqlq "SELECT EXISTS (SELECT 1 FROM schema_migrations WHERE version='0094');")" = t ] || { echo "STOP: migration 0094 not recorded"; exit 1; }
$COMPOSE up -d --no-deps --force-recreate core
for i in $(seq 1 40); do curl -fsS http://127.0.0.1:8090/health >/tmp/sc-core-v2900-health.json 2>/dev/null && break; sleep 2; done
curl -fsS http://127.0.0.1:8090/v1/research/workflows/readiness | tee /tmp/sc-core-v2900-workflow.json | python3 -m json.tool
python3 - <<'PY2'
import json
h=json.load(open('/tmp/sc-core-v2900-health.json')); r=json.load(open('/tmp/sc-core-v2900-workflow.json'))
assert h.get('ok') is True and h.get('version')=='2.90.0',h; assert r.get('release')=='2.90.0' and r.get('migration_0094_applied') is True,r
for k in ('workflow_registry_by_core','stage_registry_by_core','declared_transition_registry_by_core','apply_declared_transition_by_core','cross_product_context_binding_by_core','handoff_state_registry_by_core','checkpoint_registry_by_core','workflow_event_timeline_by_core','workflow_policy_registry_by_core','workflow_revision_history_by_core','workflow_lineage_by_core','immutable_workflow_snapshots_by_core'): assert r.get(k) is True,(k,r)
for k in ('choose_research_path_by_core','autonomously_advance_workflow_by_core','execute_specialist_work_by_core','dispatch_external_handoff_by_core','infer_stage_completion_by_core','generate_findings_by_core','generate_claims_by_core','approve_scientific_validity_by_core','resolve_challenges_by_core','rank_research_paths_by_core','determine_truth_by_core'): assert r.get(k) is False,(k,r)
print('PASS - Platform Core v2.90.0 Research Workflow & Orchestration Engine')
PY2
curl -fsS https://core.sustainablecatalyst.com/health | python3 -m json.tool
echo "PASS - PLATFORM CORE v2.90.0 BACKEND DEPLOYMENT COMPLETE"
