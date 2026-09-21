#!/usr/bin/env bash
set -euo pipefail
trap 'rc=$?; echo "ERROR: v2.95.0 deployment stopped at line $LINENO (exit $rc): $BASH_COMMAND" >&2; exit $rc' ERR
echo "=== PLATFORM CORE v2.95.0 — SCHOLARLY INTEROPERABILITY & RESEARCH PACKAGING ==="
cd /opt/sustainable-catalyst/core; COMPOSE="docker compose -f compose.yml -f compose.vps.yml"
resolve_db_url(){ if [ -n "${SC_CORE_DATABASE_URL:-}" ]; then printf '%s' "$SC_CORE_DATABASE_URL"; return; fi; if docker ps --format '{{.Names}}' | grep -qx 'sc-core'; then local u; u="$(docker exec sc-core printenv SC_CORE_DATABASE_URL 2>/dev/null || true)"; [ -n "$u" ] && { printf '%s' "$u"; return; }; fi; if [ -f .env.production ]; then grep -m1 '^SC_CORE_DATABASE_URL=' .env.production | cut -d= -f2- | sed 's/^"//;s/"$//' | sed "s/^'//;s/'$//"; return; fi; return 1; }
CORE_DB_URL="$(resolve_db_url)" || { echo "STOP: SC_CORE_DATABASE_URL could not be resolved"; exit 1; }
eval "$(CORE_DB_URL="$CORE_DB_URL" python3 - <<'PYDB'
import os,shlex
from urllib.parse import urlparse,unquote
u=urlparse(os.environ['CORE_DB_URL'].replace('postgresql+psycopg://','postgresql://',1)); print('export DB_USER='+shlex.quote(unquote(u.username or ''))); print('export DB_PASS='+shlex.quote(unquote(u.password or ''))); print('export DB_NAME='+shlex.quote((u.path or '').lstrip('/')))
PYDB
)"
[ -n "$DB_USER" ] && [ -n "$DB_NAME" ] || { echo "STOP: database identity could not be parsed"; exit 1; }
psqlq(){ docker exec -e PGPASSWORD="$DB_PASS" sc-postgres psql -h 127.0.0.1 -U "$DB_USER" -d "$DB_NAME" -Atqc "$1"; }
V294_TABLES=('research_validation_challenges_v294' 'research_validation_targets_v294' 'research_alternative_hypotheses_v294' 'research_contradiction_tests_v294' 'research_counterevidence_v294' 'research_sensitivity_checks_v294' 'research_robustness_checks_v294' 'research_replication_attempts_v294' 'research_reviewer_challenges_v294' 'research_challenge_responses_v294' 'research_validation_revisions_v294' 'research_validation_snapshots_v294'); V295_TABLES=('scholarly_research_packages_v295' 'scholarly_package_members_v295' 'scholarly_citations_v295' 'scholarly_persistent_identifiers_v295' 'scholarly_dataset_descriptors_v295' 'scholarly_notebook_descriptors_v295' 'scholarly_provenance_manifests_v295' 'scholarly_metadata_profiles_v295' 'scholarly_export_profiles_v295' 'scholarly_publication_bindings_v295' 'scholarly_interoperability_validations_v295' 'scholarly_interoperability_revisions_v295' 'scholarly_interoperability_snapshots_v295')
echo "=== PREDECESSOR GATE ==="; [ "$(psqlq "SELECT EXISTS (SELECT 1 FROM schema_migrations WHERE version='0098');")" = t ] || { echo "STOP: migration 0098 is required before v2.95.0"; exit 1; }
for t in "${V294_TABLES[@]}"; do [ "$(psqlq "SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema='public' AND table_name='$t');")" = t ] || { echo "STOP: predecessor table $t missing"; exit 1; }; done
m99="$(psqlq "SELECT EXISTS (SELECT 1 FROM schema_migrations WHERE version='0099');")"; count=0; for t in "${V295_TABLES[@]}"; do [ "$(psqlq "SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema='public' AND table_name='$t');")" = t ] && count=$((count+1)); done
if [ "$m99" = f ] && [ "$count" -eq 0 ]; then echo "PASS: pristine pre-0099 state"; elif [ "$m99" = f ] && [ "$count" -eq 13 ]; then echo "PASS: recoverable partial-0099 state"; elif [ "$m99" = t ] && [ "$count" -eq 13 ]; then echo "PASS: already-complete 0099 state"; else echo "STOP: inconsistent 0099 state ($m99, $count/13)"; exit 1; fi
echo "=== BACKUP ==="; BACKUP_DIR="/opt/sustainable-catalyst/backups/platform-core-v2950"; mkdir -p "$BACKUP_DIR"; stamp="$(date +%Y%m%d-%H%M%S)"; docker exec -e PGPASSWORD="$DB_PASS" sc-postgres pg_dump -h 127.0.0.1 -U "$DB_USER" -d "$DB_NAME" -Fc > "$BACKUP_DIR/core-${stamp}.dump"; git rev-parse HEAD > "$BACKUP_DIR/git-head-${stamp}.txt"; tar --exclude='.git' --exclude='backend/.venv' -czf "$BACKUP_DIR/core-source-${stamp}.tar.gz" .
echo "=== PROMOTE TAGGED SOURCE ==="; git fetch origin --tags; git pull --ff-only origin main; git tag --points-at HEAD | grep -qx 'v2.95.0' || { echo "STOP: production HEAD is not tagged v2.95.0"; exit 1; }; python3 -S scripts/validate_v2950_release.py
echo "=== BUILD / MIGRATE ==="; $COMPOSE build core; $COMPOSE run --rm --no-deps core python scripts/migrate.py | tee /tmp/sc-core-v2950-migrate.json
for t in "${V295_TABLES[@]}"; do [ "$(psqlq "SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema='public' AND table_name='$t');")" = t ] || { echo "STOP: $t missing after migration"; exit 1; }; done; [ "$(psqlq "SELECT EXISTS (SELECT 1 FROM schema_migrations WHERE version='0099');")" = t ] || { echo "STOP: migration 0099 not recorded"; exit 1; }
$COMPOSE up -d --no-deps --force-recreate core; for i in $(seq 1 40); do curl -fsS http://127.0.0.1:8090/health >/tmp/sc-core-v2950-health.json 2>/dev/null && break; sleep 2; done
curl -fsS http://127.0.0.1:8090/v1/research/scholarly-packages/readiness | tee /tmp/sc-core-v2950-readiness.json | python3 -m json.tool
python3 - <<'PY2'
import json
h=json.load(open('/tmp/sc-core-v2950-health.json')); r=json.load(open('/tmp/sc-core-v2950-readiness.json')); assert h.get('ok') is True and h.get('version')=='2.95.0',h; assert r.get('release')=='2.95.0' and r.get('migration_0099_applied') is True,r
for k in ('scholarly_package_registry_by_core','citation_metadata_registry_by_core','persistent_identifier_registry_by_core','dataset_notebook_descriptor_registry_by_core','provenance_manifest_registry_by_core','metadata_export_profile_registry_by_core','publication_object_binding_registry_by_core','external_validation_evidence_registry_by_core','revision_history_by_core','immutable_interoperability_snapshots_by_core'): assert r.get(k) is True,(k,r)
for k in ('mint_identifier_by_core','register_doi_by_core','submit_publication_by_core','publish_package_by_core','resolve_citations_by_core','fetch_external_artifacts_by_core','transform_dataset_by_core','execute_notebook_by_core','certify_reproducibility_by_core','validate_scientific_content_by_core','infer_authorship_by_core','determine_truth_by_core'): assert r.get(k) is False,(k,r)
print('PASS - Platform Core v2.95.0 Scholarly Interoperability & Research Packaging')
PY2
curl -fsS https://core.sustainablecatalyst.com/health | python3 -m json.tool; echo "PASS - PLATFORM CORE v2.95.0 BACKEND DEPLOYMENT COMPLETE"
