#!/usr/bin/env bash
set -euo pipefail
BUNDLE="${1:?usage: $0 /path/to/sustainable-catalyst-platform-core-v3.0.0-release-bundle.zip}"
TMP="$(mktemp -d -t sc-platform-core-v3000-bundle.XXXXXX)"; trap 'rm -rf "$TMP"' EXIT
unzip -q "$BUNDLE" -d "$TMP/bundle"
(cd "$TMP/bundle" && shasum -a 256 -c SHA256SUMS.txt)
unzip -q "$TMP/bundle/sustainable-catalyst-platform-core-v3.0.0-repository.zip" -d "$TMP/repo"
SRC="$TMP/repo/sustainable-catalyst-platform-core-v3.0.0"
python3 -S "$SRC/scripts/validate_v3000_release.py"
VENV="$TMP/venv"; python3 -m venv "$VENV"; "$VENV/bin/python" -m pip install --disable-pip-version-check -q -r "$SRC/backend/requirements.txt"
PYTHONPATH="$SRC/backend" "$VENV/bin/python" "$SRC/backend/scripts/validate_unified_research_scientific_runtime.py"
PYTHONPATH="$SRC/backend" "$VENV/bin/python" -m pytest -q "$SRC/backend/tests/test_unified_research_scientific_investigation_runtime_v3000.py" "$SRC/backend/tests/test_partial_0102_recovery_v3000.py"
echo "PASS - v3.0.0 release-critical validation complete"
