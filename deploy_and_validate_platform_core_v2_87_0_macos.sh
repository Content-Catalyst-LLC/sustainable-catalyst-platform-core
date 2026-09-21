#!/usr/bin/env bash
set -euo pipefail
BUNDLE="${1:?usage: $0 /path/to/sustainable-catalyst-platform-core-v2.87.0-release-bundle.zip}"
TMP="$(mktemp -d -t sc-platform-core-v2870-bundle.XXXXXX)"; trap 'rm -rf "$TMP"' EXIT
unzip -q "$BUNDLE" -d "$TMP/bundle"; cd "$TMP/bundle"; shasum -a 256 -c SHA256SUMS.txt
unzip -q sustainable-catalyst-platform-core-v2.87.0-repository.zip -d "$TMP/repo-extract"
R="$TMP/repo-extract/sustainable-catalyst-platform-core-v2.87.0"
python3 -S "$R/scripts/validate_v2870_release.py"
VENV="$TMP/venv"; python3 -m venv "$VENV"; "$VENV/bin/python" -m pip install --disable-pip-version-check -q -r "$R/backend/requirements.txt"
PYTHONPATH="$R/backend" "$VENV/bin/python" "$R/backend/scripts/validate_computation_lineage.py"
cd "$R"
for t in test_readiness test_python_execution_full_lineage test_multi_runtime_dependencies_and_verification test_revision_snapshot_and_guardrails test_public_boundary; do PYTHONPATH=backend "$VENV/bin/python" -m pytest -q "backend/tests/test_computation_analysis_execution_lineage_v2870.py::$t"; done
PYTHONPATH=backend "$VENV/bin/python" -m pytest -q backend/tests/test_partial_0091_recovery_v2870.py
echo "PASS - v2.87.0 bundle-only verification complete"
