#!/usr/bin/env bash
set -euo pipefail
BUNDLE="${1:-sustainable-catalyst-platform-core-v2.12.0-release-bundle.zip}"
WORK="${TMPDIR:-/tmp}/sc-platform-core-v2120-bundle"
for cmd in unzip shasum python3 bash php; do command -v "$cmd" >/dev/null 2>&1 || { echo "ERROR: Required command not found: $cmd"; exit 1; }; done
[ -f "$BUNDLE" ] || { echo "ERROR: Bundle not found: $BUNDLE"; exit 1; }
rm -rf "$WORK"; mkdir -p "$WORK"; unzip -q "$BUNDLE" -d "$WORK"; cd "$WORK"
[ -f SHA256SUMS.txt ] || { echo "ERROR: SHA256SUMS.txt missing"; exit 1; }
shasum -a 256 -c SHA256SUMS.txt
REPO_ZIP="sustainable-catalyst-platform-core-v2.12.0-repository.zip"; PLUGIN_ZIP="sustainable-catalyst-platform-core-v2.12.0-wordpress-plugin.zip"
unzip -t "$REPO_ZIP" >/dev/null; unzip -t "$PLUGIN_ZIP" >/dev/null
rm -rf repo-extract; mkdir repo-extract; unzip -q "$REPO_ZIP" -d repo-extract
ROOT="repo-extract/sustainable-catalyst-platform-core-v2.12.0"; [ -f "$ROOT/backend/app/main.py" ] || { echo "ERROR: repository root missing"; exit 1; }
cd "$ROOT"; python3 scripts/validate_v2120_release.py
python3 -c 'import hashlib,json,pathlib; m=json.loads(pathlib.Path("BUILD_MANIFEST.json").read_text()); assert m["release"]=="2.12.0"; [(lambda p,i: (_ for _ in ()).throw(AssertionError(i["path"])) if (not p.is_file() or hashlib.sha256(p.read_bytes()).hexdigest()!=i["sha256"]) else None)(pathlib.Path(i["path"]),i) for i in m["files"]]; print("PASS - clean extraction manifest verified:",m["file_count"],"files")'
find backend -type f -name '*.py' -print0 | xargs -0 python3 -m py_compile
php -l wordpress-plugin/sustainable-catalyst-platform-core/sustainable-catalyst-platform-core.php >/dev/null
bash -n PUSH_PLATFORM_CORE_V2120_FINAL.sh; bash -n deploy_and_validate_platform_core_v2_12_0_macos.sh
if [ "${SC_CORE_BUNDLE_ONLY:-0}" = "1" ]; then echo "PASS - v2.12.0 bundle-only verification complete"; exit 0; fi
python3 -m venv backend/.venv; backend/.venv/bin/python -m pip install -r backend/requirements.txt >/dev/null
export PYTHONPATH="backend:backend/public_sdk/python" PYTEST_DISABLE_PLUGIN_AUTOLOAD=1
for f in backend/tests/test_*.py; do backend/.venv/bin/python -m pytest -q "$f"; done
SMOKE_DB="$WORK/platform_core_v2120_smoke.db"; rm -f "$SMOKE_DB"
SC_CORE_DATABASE_URL="sqlite:///${SMOKE_DB}" SC_CORE_ENVIRONMENT=test backend/.venv/bin/python backend/scripts/migrate.py
SC_CORE_DATABASE_URL="sqlite:///${SMOKE_DB}" SC_CORE_ENVIRONMENT=test backend/.venv/bin/python backend/scripts/validate_streaming_reliability.py
SC_CORE_DATABASE_URL="sqlite:///${SMOKE_DB}" SC_CORE_ENVIRONMENT=test backend/.venv/bin/python backend/scripts/validate_operational_facilities.py
SC_CORE_DATABASE_URL="sqlite:///${SMOKE_DB}" SC_CORE_ENVIRONMENT=test backend/.venv/bin/python backend/scripts/validate_humanitarian_access.py
SC_CORE_DATABASE_URL="sqlite:///${SMOKE_DB}" SC_CORE_ENVIRONMENT=test backend/.venv/bin/python backend/scripts/validate_country_evidence.py
rm -f "$SMOKE_DB"; echo "PASS - v2.12.0 deterministic validation complete"
if [ "${SC_CORE_VALIDATE_ONLY:-0}" = "1" ]; then exit 0; fi
cd "$WORK"; chmod +x PUSH_PLATFORM_CORE_V2120_FINAL.sh; ./PUSH_PLATFORM_CORE_V2120_FINAL.sh "$WORK/$REPO_ZIP"
