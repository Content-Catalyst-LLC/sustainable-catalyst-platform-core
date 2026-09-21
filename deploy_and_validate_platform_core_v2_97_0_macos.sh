#!/usr/bin/env bash
set -euo pipefail
BUNDLE="${1:?usage: $0 /path/to/sustainable-catalyst-platform-core-v2.97.0-release-bundle.zip}"
TMP="$(mktemp -d -t sc-platform-core-v2970-bundle.XXXXXX)"; trap 'rm -rf "$TMP"' EXIT
unzip -q "$BUNDLE" -d "$TMP/bundle"
(cd "$TMP/bundle" && shasum -a 256 -c SHA256SUMS.txt)
unzip -q "$TMP/bundle/sustainable-catalyst-platform-core-v2.97.0-repository.zip" -d "$TMP/repo"
SRC="$TMP/repo/sustainable-catalyst-platform-core-v2.97.0"
python3 -S "$SRC/scripts/validate_v2970_release.py"
VENV="$TMP/venv"; python3 -m venv "$VENV"; "$VENV/bin/python" -m pip install --disable-pip-version-check -q -r "$SRC/backend/requirements.txt"
PYTHONPATH="$SRC/backend" "$VENV/bin/python" "$SRC/backend/scripts/validate_platform_research_integration_certification.py"
PYTHONPATH="$SRC/backend" "$VENV/bin/python" -m pytest -q "$SRC/backend/tests/test_platform_research_integration_certification_v2970.py" "$SRC/backend/tests/test_partial_0101_recovery_v2970.py"
echo "PASS - v2.97.0 release-critical validation complete"
