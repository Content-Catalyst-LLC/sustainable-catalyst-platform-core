#!/usr/bin/env bash
set -euo pipefail
ROOT="${1:-$PWD}"; cd "$ROOT"
python3 -S scripts/validate_v2920_release.py
TMP="$(mktemp -d)"; trap 'rm -rf "$TMP"' EXIT
python3 -m venv "$TMP/venv"; "$TMP/venv/bin/python" -m pip install --disable-pip-version-check -q -r backend/requirements.txt
PYTHONPATH=backend "$TMP/venv/bin/python" backend/scripts/validate_research_project_state.py
"$TMP/venv/bin/python" -m pytest -q backend/tests/test_research_project_state_v2920.py backend/tests/test_partial_0096_recovery_v2920.py
