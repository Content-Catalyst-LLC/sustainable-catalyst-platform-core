#!/usr/bin/env bash
set -euo pipefail
trap 'rc=$?; echo "ERROR: v2.84.0 validation stopped at line $LINENO (exit $rc): $BASH_COMMAND" >&2; exit $rc' ERR
BUNDLE="${1:-${HOME}/Downloads/sustainable-catalyst-platform-core-v2.84.0-release-bundle.zip}"
select_python(){ local c; for c in python3.13 python3.12 python3.11 python3.10 python3; do if command -v "$c" >/dev/null 2>&1 && "$c" -c 'import sys; raise SystemExit(0 if sys.version_info >= (3,10) else 1)' >/dev/null 2>&1; then command -v "$c"; return 0; fi; done; echo "ERROR: Platform Core v2.84.0 requires Python 3.10+." >&2; return 1; }
PYTHON_BIN="$(select_python)"; [ -f "$BUNDLE" ] || { echo "ERROR: release bundle not found: $BUNDLE"; exit 1; }
WORK="$(mktemp -d "${TMPDIR:-/tmp}/sc-core-v2840-validate.XXXXXX")"; trap 'rm -rf "$WORK"' EXIT
unzip -q "$BUNDLE" -d "$WORK/bundle"; B="$WORK/bundle"; cd "$B"; shasum -a 256 -c SHA256SUMS_V2840.txt
REPO_ZIP="sustainable-catalyst-platform-core-v2.84.0-repository.zip"; PLUGIN_ZIP="sustainable-catalyst-platform-core-v2.84.0-wordpress-plugin.zip"; BACKEND_ZIP="sustainable-catalyst-platform-core-backend-v2.84.0.zip"
unzip -tq "$REPO_ZIP" >/dev/null; unzip -tq "$PLUGIN_ZIP" >/dev/null; unzip -tq "$BACKEND_ZIP" >/dev/null; unzip -q "$REPO_ZIP" -d "$WORK/repo-extract"; ROOT="$WORK/repo-extract/sustainable-catalyst-platform-core-v2.84.0"; cd "$ROOT"
"$PYTHON_BIN" -S scripts/validate_v2840_release.py; "$PYTHON_BIN" scripts/scan_push_safe_secrets.py .; php -l wordpress-plugin/sustainable-catalyst-platform-core/sustainable-catalyst-platform-core.php >/dev/null; node --check backend/public_sdk/javascript/index.mjs; bash -n PUSH_PLATFORM_CORE_V2840_FINAL.sh; bash -n DEPLOY_PLATFORM_CORE_V2840_CONTABO.sh
"$PYTHON_BIN" scripts/build_v2840_manifest.py >/dev/null
"$PYTHON_BIN" - <<'PY2'
import hashlib,json
from pathlib import Path
r=Path('.'); m=json.loads((r/'BUILD_MANIFEST.json').read_text()); assert m['release']=='2.84.0'; assert m['file_count']>1800
for x in m['files']:
 p=r/x['path']; assert p.exists(),x['path']; assert hashlib.sha256(p.read_bytes()).hexdigest()==x['sha256'],x['path']
print('PASS - manifest verified',m['file_count'],'files')
PY2
if "$PYTHON_BIN" -c 'import sqlalchemy' >/dev/null 2>&1; then
  PYTHONPATH=backend "$PYTHON_BIN" backend/scripts/validate_research_program_longitudinal_graph.py
else echo "PASS - v2.84.0 bundle-only verification complete without backend dependencies"; fi
echo "PASS - v2.84.0 release-critical validation complete"
