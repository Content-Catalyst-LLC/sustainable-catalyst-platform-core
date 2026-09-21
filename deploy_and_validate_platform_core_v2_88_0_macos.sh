#!/usr/bin/env bash
set -euo pipefail
BUNDLE="${1:?usage: $0 /path/to/sustainable-catalyst-platform-core-v2.88.0-release-bundle.zip}"
TMP="$(mktemp -d -t sc-platform-core-v2880-bundle.XXXXXX)"; trap 'rm -rf "$TMP"' EXIT
unzip -q "$BUNDLE" -d "$TMP/bundle"; cd "$TMP/bundle"; shasum -a 256 -c SHA256SUMS.txt
unzip -q sustainable-catalyst-platform-core-v2.88.0-repository.zip -d "$TMP/repo-extract"
R="$TMP/repo-extract/sustainable-catalyst-platform-core-v2.88.0"
python3 -S "$R/scripts/validate_v2880_release.py"
VENV="$TMP/venv"; python3 -m venv "$VENV"; "$VENV/bin/python" -m pip install --disable-pip-version-check -q -r "$R/backend/requirements.txt"
PYTHONPATH="$R/backend" "$VENV/bin/python" "$R/backend/scripts/validate_unified_inference.py"
cd "$R"
PYTHONPATH=backend "$VENV/bin/python" -m pytest -q backend/tests/test_partial_0092_recovery_v2880.py
printf '%s\n' 'PASS - v2.88.0 bundle-only verification complete'
