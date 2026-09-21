#!/usr/bin/env bash
set -euo pipefail
BUNDLE="${1:?usage: $0 /path/to/sustainable-catalyst-platform-core-v2.96.0-release-bundle.zip}"
TMP="$(mktemp -d -t sc-platform-core-v2960-bundle.XXXXXX)"; trap 'rm -rf "$TMP"' EXIT
unzip -q "$BUNDLE" -d "$TMP"
cd "$TMP"
shasum -a 256 -c SHA256SUMS_V2960.txt
unzip -q sustainable-catalyst-platform-core-v2.96.0-repository.zip -d repo-extract
SRC="$TMP/repo-extract/sustainable-catalyst-platform-core-v2.96.0"
python3 -S "$SRC/scripts/validate_v2960_release.py"
python3 - "$SRC" <<'PY'
import json,hashlib,sys
from pathlib import Path
r=Path(sys.argv[1]); m=json.loads((r/'BUILD_MANIFEST.json').read_text())
for e in m['files']:
    p=r/e['path']
    assert p.is_file(), e['path']
    assert hashlib.sha256(p.read_bytes()).hexdigest()==e['sha256'], e['path']
print(f"PASS - clean extraction manifest verified: {m['file_count']} files")
PY
VENV="$TMP/v2960-venv"; python3 -m venv "$VENV"; "$VENV/bin/python" -m pip install --disable-pip-version-check -q -r "$SRC/backend/requirements.txt"
PYTHONPATH="$SRC/backend" "$VENV/bin/python" "$SRC/backend/scripts/validate_unified_research_runtime.py"
PYTHONPATH="$SRC/backend" "$VENV/bin/python" -m pytest -q "$SRC/backend/tests/test_unified_research_runtime_v2960.py" "$SRC/backend/tests/test_partial_0100_recovery_v2960.py"
"$VENV/bin/python" -m compileall -q "$SRC/backend/app" "$SRC/backend/scripts" "$SRC/backend/tests"
php -l "$SRC/wordpress-plugin/sustainable-catalyst-platform-core/sustainable-catalyst-platform-core.php" >/dev/null
node --check "$SRC/backend/public_sdk/javascript/index.mjs"
bash -n "$SRC/DEPLOY_PLATFORM_CORE_V2960_CONTABO.sh"
bash -n "$SRC/PUSH_PLATFORM_CORE_V2960_FINAL.sh"
echo "PASS - v2.96.0 release-critical validation complete"
