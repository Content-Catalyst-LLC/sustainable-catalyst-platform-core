#!/usr/bin/env bash
set -euo pipefail
ROOT="${1:-$PWD}"
cd "$ROOT"
python3 -S scripts/validate_v2850_release.py
TMP="$(mktemp -d)"
cleanup(){ rm -rf "$TMP"; }
trap cleanup EXIT
VENV="$TMP/v2850-venv"
python3 -m venv "$VENV"
"$VENV/bin/python" -m pip install --disable-pip-version-check -q -r backend/requirements.txt
PYTHONPATH=backend "$VENV/bin/python" backend/scripts/validate_research_portfolio_governance.py
PYTHONPATH=backend "$VENV/bin/python" -m pytest -q \
  backend/tests/test_research_portfolio_institutional_governance_v2850.py \
  backend/tests/test_partial_0089_recovery_v2850.py
