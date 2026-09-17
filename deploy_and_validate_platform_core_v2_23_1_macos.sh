#!/usr/bin/env bash
set -euo pipefail
trap 'rc=$?; echo "ERROR: v2.23.1 validation stopped at line $LINENO (exit $rc): $BASH_COMMAND" >&2; exit $rc' ERR

BUNDLE="${1:-${HOME}/Downloads/sustainable-catalyst-platform-core-v2.23.1-release-bundle.zip}"
[ -f "$BUNDLE" ] || { echo "ERROR: release bundle not found: $BUNDLE"; exit 1; }
for c in unzip shasum php node bash; do command -v "$c" >/dev/null 2>&1 || { echo "ERROR: Required command not found: $c"; exit 1; }; done
if command -v python3.12 >/dev/null 2>&1; then PYTHON_BIN="$(command -v python3.12)"; else PYTHON_BIN="$(command -v python3)"; fi

WORK="$(mktemp -d "${TMPDIR:-/tmp}/sc-platform-core-v2231-bundle.XXXXXX")"
trap 'rm -rf "$WORK"' EXIT
unzip -q "$BUNDLE" -d "$WORK/bundle"
cd "$WORK/bundle"
[ -f SHA256SUMS.txt ] || { echo "ERROR: SHA256SUMS.txt missing"; exit 1; }
shasum -a 256 -c SHA256SUMS.txt

REPO_ZIP="sustainable-catalyst-platform-core-v2.23.1-repository.zip"
PLUGIN_ZIP="sustainable-catalyst-platform-core-v2.23.1-wordpress-plugin.zip"
unzip -t "$REPO_ZIP" >/dev/null
unzip -t "$PLUGIN_ZIP" >/dev/null

mkdir -p "$WORK/repo-extract"
unzip -q "$REPO_ZIP" -d "$WORK/repo-extract"
ROOT="$WORK/repo-extract/sustainable-catalyst-platform-core-v2.23.1"
[ -f "$ROOT/backend/app/main.py" ] || { echo "ERROR: repository root missing"; exit 1; }
cd "$ROOT"

"$PYTHON_BIN" scripts/validate_v2231_release.py
"$PYTHON_BIN" - <<'PY'
import hashlib, json, pathlib
m = json.loads(pathlib.Path('BUILD_MANIFEST.json').read_text())
assert m['release'] == '2.23.1'
for item in m['files']:
    p = pathlib.Path(item['path'])
    assert p.is_file() and hashlib.sha256(p.read_bytes()).hexdigest() == item['sha256'], item['path']
print('PASS - clean extraction manifest verified:', m['file_count'], 'files')
PY

find backend -type f -name '*.py' -print0 | xargs -0 "$PYTHON_BIN" -m py_compile
php -l wordpress-plugin/sustainable-catalyst-platform-core/sustainable-catalyst-platform-core.php >/dev/null
node --check backend/public_sdk/javascript/index.mjs
bash -n PUSH_PLATFORM_CORE_V2231_FINAL.sh
bash -n deploy_and_validate_platform_core_v2_23_1_macos.sh

if [ "${SC_CORE_BUNDLE_ONLY:-0}" = "1" ]; then
  echo "PASS - v2.23.1 bundle-only verification complete"
  exit 0
fi

"$PYTHON_BIN" -m venv backend/.venv
backend/.venv/bin/python -m pip install -r backend/requirements.txt >/dev/null
export PYTHONPATH="backend:backend/public_sdk/python" PYTEST_DISABLE_PLUGIN_AUTOLOAD=1
for f in backend/tests/test_*.py; do
  echo "==> $f"
  backend/.venv/bin/python -m pytest -q "$f"
done

SMOKE_DB="$WORK/platform_core_v2231_smoke.db"
rm -f "$SMOKE_DB"
export SC_CORE_DATABASE_URL="sqlite:///${SMOKE_DB}" SC_CORE_ENVIRONMENT=test
backend/.venv/bin/python backend/scripts/migrate.py
backend/.venv/bin/python scripts/validate_v2231_release.py
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
backend/.venv/bin/python backend/scripts/run_connector_worker.py --once
rm -f "$SMOKE_DB"
echo "PASS - v2.23.1 deterministic validation complete"

if [ "${SC_CORE_VALIDATE_ONLY:-0}" = "1" ]; then
  exit 0
fi

cd "$WORK/bundle"
chmod +x PUSH_PLATFORM_CORE_V2231_FINAL.sh
./PUSH_PLATFORM_CORE_V2231_FINAL.sh "$WORK/bundle/$REPO_ZIP"
