#!/usr/bin/env bash
set -euo pipefail
trap 'rc=$?; echo "ERROR: v2.26.0 promotion stopped at line $LINENO (exit $rc): $BASH_COMMAND" >&2; exit $rc' ERR

ORG="Content-Catalyst-LLC"
REPO="sustainable-catalyst-platform-core"
BRANCH="main"
REMOTE="git@github.com:${ORG}/${REPO}.git"
PACKAGE_ZIP="${1:-${HOME}/Downloads/sustainable-catalyst-platform-core-v2.26.0-repository.zip}"
WORKDIR="${2:-${HOME}/Downloads/sustainable-catalyst-platform-core-repo}"
EXTRACT_DIR="${TMPDIR:-/tmp}/sc-platform-core-v2260-extracted"

printf '%s\n' "============================================================" "PLATFORM CORE v2.26.0 — DISTRIBUTED QUOTAS / ADMISSION / WORKLOAD GOVERNANCE" "============================================================" "Package:    ${PACKAGE_ZIP}" "Repository: ${WORKDIR}" "Remote:     ${REMOTE}" ""
for c in git unzip rsync grep find zip shasum php bash node curl; do command -v "$c" >/dev/null 2>&1 || { echo "ERROR: Required command not found: $c"; exit 1; }; done
if command -v python3.12 >/dev/null 2>&1; then PYTHON_BIN="$(command -v python3.12)"; else PYTHON_BIN="$(command -v python3)"; fi
[ -f "$PACKAGE_ZIP" ] || { echo "ERROR: Release ZIP not found: $PACKAGE_ZIP"; exit 1; }

rm -rf "$EXTRACT_DIR"; mkdir -p "$EXTRACT_DIR"; unzip -q "$PACKAGE_ZIP" -d "$EXTRACT_DIR"
SOURCE_ROOT="$(find "$EXTRACT_DIR" -maxdepth 1 -type d -name 'sustainable-catalyst-platform-core-v2.26.0' | head -1)"
[ -n "$SOURCE_ROOT" ] && [ -f "$SOURCE_ROOT/backend/app/main.py" ] || { echo "ERROR: Expected v2.26.0 repository root was not found."; exit 1; }

if [ -d "$WORKDIR/.git" ]; then
  cd "$WORKDIR"; git remote set-url origin "$REMOTE"
  if ! git diff --quiet || ! git diff --cached --quiet || [ -n "$(git ls-files --others --exclude-standard)" ]; then git stash push -u -m "Automatic safety stash before Platform Core v2.26.0" >/dev/null || true; fi
  git fetch origin --prune; git checkout "$BRANCH"; git pull --ff-only origin "$BRANCH"
else
  rm -rf "$WORKDIR"; git clone --branch "$BRANCH" "$REMOTE" "$WORKDIR"
fi

find "$WORKDIR" -type d -name '__pycache__' -prune -exec rm -rf {} + 2>/dev/null || true
rm -rf "$WORKDIR/backend/.venv" "$WORKDIR/.pytest_cache" "$WORKDIR/backend/.pytest_cache"
rsync -a --delete --exclude='.git/' --exclude='.venv/' --exclude='.pytest_cache/' --exclude='__pycache__/' --exclude='*.db' "$SOURCE_ROOT/" "$WORKDIR/"
cd "$WORKDIR"

"$PYTHON_BIN" scripts/validate_v2260_release.py
"$PYTHON_BIN" scripts/scan_push_safe_secrets.py .
"$PYTHON_BIN" - <<'PY'
from pathlib import Path
import hashlib, json
m=json.loads(Path('BUILD_MANIFEST.json').read_text()); assert m.get('release')=='2.26.0'
for item in m['files']:
 p=Path(item['path']); assert p.is_file(), item['path']; assert hashlib.sha256(p.read_bytes()).hexdigest()==item['sha256'], item['path']
print(f"PASS - Manifest verified across {m['file_count']} files")
PY
find backend -type f -name '*.py' -not -path '*/.venv/*' -print0 | xargs -0 "$PYTHON_BIN" -m py_compile
php -l wordpress-plugin/sustainable-catalyst-platform-core/sustainable-catalyst-platform-core.php >/dev/null
node --check backend/public_sdk/javascript/index.mjs
bash -n PUSH_PLATFORM_CORE_V2260_FINAL.sh
bash -n deploy_and_validate_platform_core_v2_25_0_macos.sh

"$PYTHON_BIN" -m venv backend/.venv
backend/.venv/bin/python -m pip install --upgrade pip >/dev/null
backend/.venv/bin/python -m pip install -r backend/requirements.txt >/dev/null
export PYTHONPATH="backend:backend/public_sdk/python" PYTEST_DISABLE_PLUGIN_AUTOLOAD=1
for f in backend/tests/test_*.py; do echo "==> $f"; backend/.venv/bin/python -m pytest -q "$f"; done

SMOKE_DB="$WORKDIR/backend/platform_core_v2260_push_smoke.db"; rm -f "$SMOKE_DB"
export SC_CORE_DATABASE_URL="sqlite:///${SMOKE_DB}" SC_CORE_ENVIRONMENT=test
backend/.venv/bin/python backend/scripts/migrate.py
backend/.venv/bin/python scripts/validate_v2260_release.py
backend/.venv/bin/python backend/scripts/validate_streaming_reliability.py
backend/.venv/bin/python backend/scripts/validate_operational_facilities.py
backend/.venv/bin/python backend/scripts/validate_humanitarian_access.py
backend/.venv/bin/python backend/scripts/validate_country_evidence.py
backend/.venv/bin/python backend/scripts/validate_scientific_service_fabric.py
backend/.venv/bin/python backend/scripts/validate_cross_product_exchange.py
backend/.venv/bin/python backend/scripts/validate_scale_control_plane.py
backend/.venv/bin/python backend/scripts/validate_governance_control_plane.py
backend/.venv/bin/python backend/scripts/validate_production_certification.py
backend/.venv/bin/python backend/scripts/validate_observability_control_plane.py
backend/.venv/bin/python backend/scripts/validate_incident_change_control.py
backend/.venv/bin/python backend/scripts/validate_continuity_disaster_recovery.py
backend/.venv/bin/python backend/scripts/validate_multi_region_resilience.py
backend/.venv/bin/python backend/scripts/validate_data_lifecycle_preservation.py
backend/.venv/bin/python backend/scripts/validate_federated_core_exchange.py
backend/.venv/bin/python backend/scripts/validate_capacity_resource_governance.py
backend/.venv/bin/python backend/scripts/validate_credential_key_lifecycle.py
backend/.venv/bin/python backend/scripts/validate_workload_governance.py
backend/.venv/bin/python backend/scripts/run_connector_worker.py --once
rm -f "$SMOKE_DB"

mkdir -p dist
(cd wordpress-plugin && zip -qr ../dist/sustainable-catalyst-platform-core-plugin-v2.26.0.zip sustainable-catalyst-platform-core)
cp backend/public_sdk/downloads/sc-platform-core-public-python-v2.26.0.zip dist/
cp backend/public_sdk/downloads/sc-platform-core-public-javascript-v2.26.0.zip dist/

git add -A
if git diff --cached --quiet; then echo "No repository changes need to be committed."; else git commit -m "Build Platform Core v2.26.0 distributed quotas admission and workload governance"; fi
git push --set-upstream origin "$BRANCH"
echo "PASS - Platform Core v2.26.0 pushed successfully"

if [ -n "${SC_CORE_PUBLIC_BASE_URL:-}" ]; then
  curl -fsS "${SC_CORE_PUBLIC_BASE_URL%/}/health" | "$PYTHON_BIN" -c 'import json,sys; d=json.load(sys.stdin); assert d.get("version")=="2.26.0",d; print("PASS - live /health")'
  curl -fsS "${SC_CORE_PUBLIC_BASE_URL%/}/v1/workload-governance/readiness" | "$PYTHON_BIN" -c 'import json,sys; d=json.load(sys.stdin); assert d.get("release")=="2.26.0",d; assert d.get("migration_0029_applied") is True,d; assert d.get("hard_admission_control") is True,d; print("PASS - live workload governance readiness")'
else
  echo "Live verification skipped: export SC_CORE_PUBLIC_BASE_URL to enable it."
fi
