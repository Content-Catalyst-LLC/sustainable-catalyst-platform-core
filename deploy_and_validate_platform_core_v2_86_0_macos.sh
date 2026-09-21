#!/usr/bin/env bash
set -euo pipefail
BUNDLE="${1:?usage: $0 /path/to/sustainable-catalyst-platform-core-v2.86.0-release-bundle.zip}"
TMP="$(mktemp -d -t sc-platform-core-v2860-bundle.XXXXXX)"; trap 'rm -rf "$TMP"' EXIT
unzip -q "$BUNDLE" -d "$TMP/bundle"
cd "$TMP/bundle"
shasum -a 256 -c SHA256SUMS.txt
unzip -q sustainable-catalyst-platform-core-v2.86.0-repository.zip -d "$TMP/repo-extract"
R="$TMP/repo-extract/sustainable-catalyst-platform-core-v2.86.0"
python3 -S "$R/scripts/validate_v2860_release.py"
VENV="$TMP/venv"; python3 -m venv "$VENV"; "$VENV/bin/python" -m pip install --disable-pip-version-check -q -r "$R/backend/requirements.txt"
PYTHONPATH="$R/backend" "$VENV/bin/python" "$R/backend/scripts/validate_research_protocols.py"
cd "$R"
for t in test_readiness test_experimental_protocol_components test_forensic_and_literature_protocols_are_universal test_deviation_revision_snapshot_and_guardrails test_public_boundary; do PYTHONPATH=backend "$VENV/bin/python" -m pytest -q "backend/tests/test_scientific_study_investigation_protocol_v2860.py::$t"; done
PYTHONPATH=backend "$VENV/bin/python" -m pytest -q backend/tests/test_partial_0090_recovery_v2860.py
echo "PASS - v2.86.0 bundle-only verification complete"
