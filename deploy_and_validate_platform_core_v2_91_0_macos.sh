#!/usr/bin/env bash
set -euo pipefail
ROOT="${1:-$PWD}"; cd "$ROOT"
python3 -S scripts/validate_v2910_release.py
TMP="$(mktemp -d)"; trap 'rm -rf "$TMP"' EXIT
python3 -m venv "$TMP/venv"; "$TMP/venv/bin/python" -m pip install --disable-pip-version-check -q -r backend/requirements.txt
PYTHONPATH=backend "$TMP/venv/bin/python" backend/scripts/validate_research_context_handoffs.py
PYTHONPATH=backend "$TMP/venv/bin/python" -m pytest -q backend/tests/test_research_context_handoffs_v2910.py backend/tests/test_partial_0095_recovery_v2910.py
