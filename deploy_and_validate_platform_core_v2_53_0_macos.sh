#!/usr/bin/env bash
set -euo pipefail
trap 'rc=$?; echo "ERROR: v2.53.0 validation stopped at line $LINENO (exit $rc): $BASH_COMMAND" >&2; exit $rc' ERR
BUNDLE="${1:-${HOME}/Downloads/sustainable-catalyst-platform-core-v2.53.0-release-bundle.zip}"
select_python(){ local c; for c in python3.12 python3.11 python3.10 python3; do if command -v "$c" >/dev/null 2>&1 && "$c" -c 'import sys; raise SystemExit(0 if sys.version_info >= (3,10) else 1)' >/dev/null 2>&1; then command -v "$c"; return 0; fi; done; echo "ERROR: Platform Core v2.53.0 requires Python 3.10+; Python 3.12 is preferred." >&2; return 1; }
[ -f "$BUNDLE" ] || { echo "ERROR: release bundle not found: $BUNDLE"; exit 1; }
for c in unzip shasum php node bash; do command -v "$c" >/dev/null 2>&1 || { echo "ERROR: required command not found: $c"; exit 1; }; done
PYTHON_BIN="$(select_python)"; echo "Using $($PYTHON_BIN --version 2>&1)"
WORK="$(mktemp -d "${TMPDIR:-/tmp}/sc-platform-core-v2530-bundle.XXXXXX")"; trap 'rm -rf "$WORK"' EXIT
unzip -q "$BUNDLE" -d "$WORK/bundle"; cd "$WORK/bundle"
[ -f SHA256SUMS.txt ] || { echo "ERROR: SHA256SUMS.txt missing"; exit 1; }; shasum -a 256 -c SHA256SUMS.txt
REPO_ZIP="sustainable-catalyst-platform-core-v2.53.0-repository.zip"; PLUGIN_ZIP="sustainable-catalyst-platform-core-v2.53.0-wordpress-plugin.zip"
unzip -t "$REPO_ZIP" >/dev/null; unzip -t "$PLUGIN_ZIP" >/dev/null
mkdir -p "$WORK/repo-extract"; unzip -q "$REPO_ZIP" -d "$WORK/repo-extract"
ROOT="$WORK/repo-extract/sustainable-catalyst-platform-core-v2.53.0"; [ -f "$ROOT/backend/app/main.py" ] || { echo "ERROR: repository root missing"; exit 1; }
cd "$ROOT"
"$PYTHON_BIN" -S scripts/validate_v2530_release.py
"$PYTHON_BIN" scripts/scan_push_safe_secrets.py .
"$PYTHON_BIN" - <<'PY2'
import hashlib,json,pathlib
m=json.loads(pathlib.Path('BUILD_MANIFEST.json').read_text()); assert m['release']=='2.53.0',m
for item in m['files']:
 p=pathlib.Path(item['path']); assert p.is_file(),item['path']; assert hashlib.sha256(p.read_bytes()).hexdigest()==item['sha256'],item['path']
print('PASS - clean extraction manifest verified:',m['file_count'],'files')
PY2
find backend -type f -name '*.py' -print0 | xargs -0 "$PYTHON_BIN" -m py_compile
php -l wordpress-plugin/sustainable-catalyst-platform-core/sustainable-catalyst-platform-core.php >/dev/null
node --check backend/public_sdk/javascript/index.mjs
bash -n PUSH_PLATFORM_CORE_V2530_FINAL.sh; bash -n deploy_and_validate_platform_core_v2_53_0_macos.sh; bash -n DEPLOY_PLATFORM_CORE_V2530_CONTABO.sh
if [ "${SC_CORE_BUNDLE_ONLY:-0}" = "1" ]; then echo "PASS - v2.53.0 bundle-only verification complete without backend dependencies"; exit 0; fi
"$PYTHON_BIN" -m venv backend/.venv
backend/.venv/bin/python -m pip install --upgrade pip >/dev/null
backend/.venv/bin/python -m pip install -r backend/requirements.txt >/dev/null
export PYTHONPATH="backend:backend/public_sdk/python" PYTEST_DISABLE_PLUGIN_AUTOLOAD=1
TEST_FILES="$(sed 's#^#backend/#' backend/release_v2530_testfiles.txt | tr '\n' ' ')"
backend/.venv/bin/python -m pytest -q $TEST_FILES
SMOKE_DB="$WORK/platform_core_v2530_smoke.db"; rm -f "$SMOKE_DB"
export SC_CORE_DATABASE_URL="sqlite:///${SMOKE_DB}" SC_CORE_ENVIRONMENT=test SC_CORE_SCIENTIFIC_OBJECT_STORAGE_ROOT="$WORK/scientific-objects"
backend/.venv/bin/python backend/scripts/migrate.py >/tmp/sc-core-v2530-migrate.json
PYTHONPATH=backend backend/.venv/bin/python backend/scripts/validate_predictive_time_series_backtesting.py
backend/.venv/bin/python - <<'PY2'
import json
m=json.load(open('/tmp/sc-core-v2530-migrate.json')); assert '0057' in m['applied'] and m['pending']==[],m
print('PASS - migration 0057 applied with pending=[]')
PY2
echo "PASS - v2.53.0 release-critical validation complete"
if [ "${SC_CORE_VALIDATE_ONLY:-0}" = "1" ]; then exit 0; fi
cd "$WORK/bundle"; chmod +x PUSH_PLATFORM_CORE_V2530_FINAL.sh; PYTHON_BIN="$PYTHON_BIN" ./PUSH_PLATFORM_CORE_V2530_FINAL.sh "$WORK/bundle/$REPO_ZIP"
