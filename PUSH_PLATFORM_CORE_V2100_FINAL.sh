#!/usr/bin/env bash
set -euo pipefail

ORG="Content-Catalyst-LLC"
REPO="sustainable-catalyst-platform-core"
BRANCH="main"
REMOTE="git@github.com:${ORG}/${REPO}.git"

PACKAGE_ZIP="${1:-${HOME}/Downloads/sustainable-catalyst-platform-core-v2.10.0-repository.zip}"
WORKDIR="${2:-${HOME}/Downloads/sustainable-catalyst-platform-core-repo}"
EXTRACT_DIR="${TMPDIR:-/tmp}/sc-platform-core-v2100-extracted"

printf '%s\n' \
  "============================================================" \
  "PLATFORM CORE v2.10.0 — OPERATIONAL EVIDENCE & FACILITY REGISTRY" \
  "============================================================" \
  "Package:    ${PACKAGE_ZIP}" \
  "Repository: ${WORKDIR}" \
  "Remote:     ${REMOTE}" \
  ""

for command_name in git unzip rsync grep find zip shasum php; do
  command -v "$command_name" >/dev/null 2>&1 || { echo "ERROR: Required command not found: ${command_name}"; exit 1; }
done
if command -v python3.12 >/dev/null 2>&1; then PYTHON_BIN="$(command -v python3.12)"; else PYTHON_BIN="$(command -v python3)"; fi

[ -f "$PACKAGE_ZIP" ] || { echo "ERROR: Release ZIP not found: $PACKAGE_ZIP"; exit 1; }
rm -rf "$EXTRACT_DIR"; mkdir -p "$EXTRACT_DIR"
unzip -q "$PACKAGE_ZIP" -d "$EXTRACT_DIR"
SOURCE_ROOT="$(find "$EXTRACT_DIR" -maxdepth 1 -type d -name 'sustainable-catalyst-platform-core-v2.10.0' | head -1)"
[ -n "$SOURCE_ROOT" ] && [ -f "$SOURCE_ROOT/backend/app/main.py" ] || { echo "ERROR: Expected v2.10.0 repository root was not found."; exit 1; }

if [ -d "$WORKDIR/.git" ]; then
  cd "$WORKDIR"
  git remote set-url origin "$REMOTE"
  if ! git diff --quiet || ! git diff --cached --quiet || [ -n "$(git ls-files --others --exclude-standard)" ]; then
    git stash push -u -m "Automatic safety stash before Platform Core v2.10.0" >/dev/null || true
  fi
  git fetch origin --prune
  git checkout "$BRANCH"
  git pull --ff-only origin "$BRANCH"
else
  rm -rf "$WORKDIR"
  git clone --branch "$BRANCH" "$REMOTE" "$WORKDIR"
fi

find "$WORKDIR" -type d -name '__pycache__' -prune -exec rm -rf {} + 2>/dev/null || true
rm -rf "$WORKDIR/backend/.venv" "$WORKDIR/.pytest_cache" "$WORKDIR/backend/.pytest_cache"
rsync -a --delete --exclude='.git/' --exclude='.venv/' --exclude='.pytest_cache/' --exclude='__pycache__/' --exclude='*.db' "$SOURCE_ROOT/" "$WORKDIR/"
cd "$WORKDIR"

"$PYTHON_BIN" scripts/validate_v2100_release.py
"$PYTHON_BIN" - <<'PY'
from pathlib import Path
import hashlib,json
root=Path('.')
m=json.loads((root/'BUILD_MANIFEST.json').read_text())
assert m.get('release')=='2.10.0', m.get('release')
for item in m.get('files',[]):
    p=root/item['path']
    if not p.is_file(): raise SystemExit(f"ERROR: Manifest file missing: {p}")
    if hashlib.sha256(p.read_bytes()).hexdigest()!=item['sha256']: raise SystemExit(f"ERROR: Manifest hash mismatch: {p}")
print(f"PASS - Manifest verified across {m['file_count']} files")
PY

SECRET_HITS="$({ grep -RInE '(sk-proj-[A-Za-z0-9_-]{20,}|sk-[A-Za-z0-9_-]{30,}|AIza[0-9A-Za-z_-]{20,}|gh[opusr]_[A-Za-z0-9_]{20,}|Authorization:[[:space:]]*Bearer[[:space:]]+[A-Za-z0-9._-]{24,}|X-SC-Service-Token:[[:space:]]*[A-Za-z0-9._-]{20,})' . --exclude-dir=.git --exclude-dir=.venv --exclude-dir=.pytest_cache --exclude-dir=__pycache__ --exclude='*.zip' --exclude='*.pyc' --exclude='.env.example' --exclude='platform-core-v2100.env.example' --exclude='PUSH_PLATFORM_CORE_V*_FINAL*.sh' || true; } | grep -viE '(placeholder|replace[-_ ]?me|change[-_ ]?me|DEMO_KEY|test-secret|secret-token|hidden)' || true)"
if [ -n "$SECRET_HITS" ]; then printf '%s\n' "$SECRET_HITS"; echo "ERROR: Potential secret found. Nothing was pushed."; exit 1; fi

find backend -type f -name '*.py' -not -path '*/.venv/*' -print0 | xargs -0 "$PYTHON_BIN" -m py_compile
php -l wordpress-plugin/sustainable-catalyst-platform-core/sustainable-catalyst-platform-core.php >/dev/null
bash -n PUSH_PLATFORM_CORE_V2100_FINAL.sh
bash -n deploy_and_validate_platform_core_v2_10_0_macos.sh

"$PYTHON_BIN" -m venv backend/.venv
backend/.venv/bin/python -m pip install --upgrade pip >/dev/null
backend/.venv/bin/python -m pip install -r backend/requirements.txt >/dev/null
export PYTHONPATH="backend:backend/public_sdk/python"
export PYTEST_DISABLE_PLUGIN_AUTOLOAD=1
for group in \
  "backend/tests/test_entities.py backend/tests/test_evidence_ledger_v220.py backend/tests/test_gateway_v260.py backend/tests/test_graph.py" \
  "backend/tests/test_graph_engine_v210.py backend/tests/test_health.py backend/tests/test_import_and_foundations.py backend/tests/test_international_law_un_v271.py" \
  "backend/tests/test_live_data_gateway_v270.py" \
  "backend/tests/test_predicates.py backend/tests/test_public_api_v230.py" \
  "backend/tests/test_production_integration_v281.py" \
  "backend/tests/test_data_fabric_v280.py backend/tests/test_economics_connectors_v273.py" \
  "backend/tests/test_scientific_connectors_v272.py" \
  "backend/tests/test_signature_dossiers_v250.py" \
  "backend/tests/test_trust_center_v240.py" \
  "backend/tests/test_streaming_alerts_reliability_v290.py"; do
  backend/.venv/bin/python -m pytest -q $group
done

SMOKE_DB="$WORKDIR/backend/platform_core_v2100_push_smoke.db"
rm -f "$SMOKE_DB"
SC_CORE_DATABASE_URL="sqlite:///${SMOKE_DB}" SC_CORE_ENVIRONMENT=test SC_CORE_WRITE_API_KEY=x SC_CORE_API_LOG_SALT=y SC_CORE_WEBHOOK_SIGNING_SECRET=z SC_CORE_DOSSIER_SIGNING_SECRET=q backend/.venv/bin/python backend/scripts/migrate.py
SC_CORE_DATABASE_URL="sqlite:///${SMOKE_DB}" SC_CORE_ENVIRONMENT=test backend/.venv/bin/python backend/scripts/validate_streaming_reliability.py
SC_CORE_DATABASE_URL="sqlite:///${SMOKE_DB}" SC_CORE_ENVIRONMENT=test backend/.venv/bin/python backend/scripts/validate_operational_facilities.py
SC_CORE_DATABASE_URL="sqlite:///${SMOKE_DB}" SC_CORE_ENVIRONMENT=test backend/.venv/bin/python backend/scripts/run_connector_worker.py --once
rm -f "$SMOKE_DB"

mkdir -p dist
(cd wordpress-plugin && zip -qr ../dist/sustainable-catalyst-platform-core-plugin-v2.10.0.zip sustainable-catalyst-platform-core)
cp backend/public_sdk/downloads/sc-platform-core-public-python-v2.10.0.zip dist/
cp backend/public_sdk/downloads/sc-platform-core-public-javascript-v2.10.0.zip dist/
cp backend/public_sdk/postman/Sustainable_Catalyst_Public_API_v1.postman_collection.json dist/

git add -A
if git diff --cached --quiet; then echo "No repository changes need to be committed."; else git commit -m "Build Platform Core v2.10.0 operational evidence and facility registry"; fi
git push --set-upstream origin "$BRANCH"

echo "PASS - Platform Core v2.10.0 pushed successfully"
if [ -n "${SC_CORE_PUBLIC_BASE_URL:-}" ]; then
  curl -fsS "${SC_CORE_PUBLIC_BASE_URL%/}/health" >/dev/null
  curl -fsS "${SC_CORE_PUBLIC_BASE_URL%/}/ready" | "$PYTHON_BIN" -c 'import json,sys; d=json.load(sys.stdin); assert d.get("ok") is True, d; assert d.get("streaming_alerts_source_reliability")=="ready", d; assert d.get("operational_evidence_facility_registry")=="ready", d; print("PASS - live /ready")'
  curl -fsS -H "X-SC-API-Key: ${SC_CORE_WRITE_API_KEY:-}" "${SC_CORE_PUBLIC_BASE_URL%/}/v1/facilities/readiness" | "$PYTHON_BIN" -c 'import json,sys; d=json.load(sys.stdin); assert d.get("release")=="2.10.0", d; assert d.get("status")=="ready", d; print("PASS - live facility registry readiness")'
else
  echo "Live verification skipped: export SC_CORE_PUBLIC_BASE_URL to enable it."
fi
