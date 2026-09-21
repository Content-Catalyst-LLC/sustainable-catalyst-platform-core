#!/usr/bin/env bash
set -euo pipefail
ROOT="${1:-$PWD}"; cd "$ROOT"; python3 -S scripts/validate_v2950_release.py; TMP="$(mktemp -d)"; trap 'rm -rf "$TMP"' EXIT; python3 -m venv "$TMP/venv"; "$TMP/venv/bin/python" -m pip install --disable-pip-version-check -q -r backend/requirements.txt; PYTHONPATH=backend "$TMP/venv/bin/python" backend/scripts/validate_scholarly_interoperability.py; PYTHONPATH=backend "$TMP/venv/bin/python" -m pytest -q backend/tests/test_scholarly_interoperability_v2950.py backend/tests/test_partial_0099_recovery_v2950.py
