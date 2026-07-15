#!/usr/bin/env bash
set -euo pipefail

ORG="Content-Catalyst-LLC"
REPO="sustainable-catalyst-platform-core"
BRANCH="main"
REMOTE="git@github.com:${ORG}/${REPO}.git"

PACKAGE_ZIP="${1:-${HOME}/Downloads/sustainable-catalyst-platform-core-v2.7.3.zip}"
WORKDIR="${2:-${HOME}/Downloads/sustainable-catalyst-platform-core-repo}"
EXTRACT_DIR="${TMPDIR:-/tmp}/sc-platform-core-v273-extracted"

printf '%s\n' \
  "============================================================" \
  "PLATFORM CORE v2.7.3 — ECONOMICS AND OFFICIAL STATISTICS" \
  "============================================================" \
  "Package:    ${PACKAGE_ZIP}" \
  "Repository: ${WORKDIR}" \
  "Remote:     ${REMOTE}" \
  ""

for command_name in git unzip rsync grep find zip; do
  command -v "$command_name" >/dev/null 2>&1 || {
    echo "ERROR: Required command not found: ${command_name}"
    exit 1
  }
done

if command -v python3.12 >/dev/null 2>&1; then
  PYTHON_BIN="$(command -v python3.12)"
elif command -v python3 >/dev/null 2>&1; then
  PYTHON_BIN="$(command -v python3)"
else
  echo "ERROR: Python 3 was not found."
  exit 1
fi

[ -f "$PACKAGE_ZIP" ] || {
  echo "ERROR: Release ZIP not found: ${PACKAGE_ZIP}"
  exit 1
}

rm -rf "$EXTRACT_DIR"
mkdir -p "$EXTRACT_DIR"
unzip -q "$PACKAGE_ZIP" -d "$EXTRACT_DIR"
SOURCE_ROOT="$(find "$EXTRACT_DIR" -maxdepth 1 -type d -name 'sustainable-catalyst-platform-core-v2.7.3' | head -1)"

[ -n "$SOURCE_ROOT" ] && [ -f "$SOURCE_ROOT/backend/app/main.py" ] || {
  echo "ERROR: The ZIP does not contain the expected v2.7.3 repository root."
  exit 1
}

if [ -d "$WORKDIR/.git" ]; then
  cd "$WORKDIR"
  git remote set-url origin "$REMOTE"
  if ! git diff --quiet || ! git diff --cached --quiet || [ -n "$(git ls-files --others --exclude-standard)" ]; then
    git stash push -u -m "Automatic safety stash before Platform Core v2.7.3" >/dev/null || true
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

rsync -a --delete \
  --exclude='.git/' \
  --exclude='.venv/' \
  --exclude='.pytest_cache/' \
  --exclude='__pycache__/' \
  --exclude='*.db' \
  "$SOURCE_ROOT/" "$WORKDIR/"

cd "$WORKDIR"

echo "Validating v2.7.3 release markers..."
test -f backend/app/routers/economic_data.py
test -f backend/app/services/economic_data.py
test -f backend/tests/test_economics_connectors_v273.py
test -f schemas/economic-data-record-v1.schema.json
test -f docs/ECONOMICS_OFFICIAL_STATISTICS_CONNECTORS_V273.md
test -f RELEASE_NOTES_V273.md
test -f deployment/platform-core-v273.env.example
test -f backend/public_sdk/downloads/sc-platform-core-public-python-v2.7.3.zip
test -f backend/public_sdk/downloads/sc-platform-core-public-javascript-v2.7.3.zip
grep -q 'version: str = "2.7.3"' backend/app/config.py
grep -q '"0010"' backend/app/migrations.py
grep -q 'economic_data_record_store' backend/app/routers/meta.py
grep -q 'oecd.sdmx' backend/app/live_data_catalog.py
grep -q 'sec.companyfacts' backend/app/live_data_catalog.py
grep -q 'sdmx_csv_observations_v1' backend/app/connectors/adapters.py

echo "Verifying release manifest..."
"$PYTHON_BIN" - <<'PY'
from pathlib import Path
import hashlib, json, sys
root=Path('.')
manifest=json.loads((root/'BUILD_MANIFEST.json').read_text())
if manifest.get('release') != '2.7.3':
    raise SystemExit('ERROR: BUILD_MANIFEST.json release is not 2.7.3')
for item in manifest.get('files', []):
    path=root/item['path']
    if not path.is_file():
        raise SystemExit(f"ERROR: Manifest file missing: {path}")
    digest=hashlib.sha256(path.read_bytes()).hexdigest()
    if digest != item['sha256']:
        raise SystemExit(f"ERROR: Manifest hash mismatch: {path}")
print(f"Manifest verified across {manifest['file_count']} files.")
PY

printf '%s\n' "Running a push-safe secret scan..."
SECRET_HITS="$({
  grep -RInE \
    '(sk-proj-[A-Za-z0-9_-]{20,}|sk-[A-Za-z0-9_-]{30,}|AIza[0-9A-Za-z_-]{20,}|gh[opusr]_[A-Za-z0-9_]{20,}|SC_CORE_(WRITE|FRED|NASA|NCBI|MATERIALS_PROJECT|BEA|CENSUS|EIA)_API_KEY=[^<[:space:]]{16,}|SC_CORE_IMF_API_TOKEN=[^<[:space:]]{16,}|SC_CORE_BLS_REGISTRATION_KEY=[^<[:space:]]{16,}|Authorization:[[:space:]]*Bearer[[:space:]]+[A-Za-z0-9._-]{24,}|X-API-KEY:[[:space:]]*[A-Za-z0-9._-]{20,})' \
    . \
    --exclude-dir=.git \
    --exclude-dir=.venv \
    --exclude-dir=.pytest_cache \
    --exclude-dir=__pycache__ \
    --exclude='*.zip' \
    --exclude='*.pyc' \
    --exclude='.env.example' \
    --exclude='platform-core-v273.env.example' \
    --exclude='PUSH_PLATFORM_CORE_V*_FINAL*.sh' \
    || true
} | grep -viE \
  '(your[-_ ]?(write[-_ ]?)?key|your[-_ ]?api[-_ ]?key|replace[-_ ]?me|change[-_ ]?me|example[-_ ]?key|placeholder|generate-a-long-random-secret|DEMO_KEY|RECORD_ID|test-key|free-eia-key|free-bea-key)' \
  || true)"

if [ -n "$SECRET_HITS" ]; then
  printf '%s\n' "$SECRET_HITS"
  echo "ERROR: A potential secret was found. Nothing was pushed."
  exit 1
fi

"$PYTHON_BIN" -m venv backend/.venv
backend/.venv/bin/python -m pip install --upgrade pip
backend/.venv/bin/python -m pip install -r backend/requirements.txt

PYTEST_ENV=(env PYTHONPATH="backend:backend/public_sdk/python" DD_TRACE_ENABLED=false)
"${PYTEST_ENV[@]}" backend/.venv/bin/python -m pytest -q -p no:ddtrace \
  backend/tests/test_entities.py \
  backend/tests/test_evidence_ledger_v220.py \
  backend/tests/test_gateway_v260.py \
  backend/tests/test_graph.py \
  backend/tests/test_graph_engine_v210.py \
  backend/tests/test_health.py \
  backend/tests/test_import_and_foundations.py \
  backend/tests/test_international_law_un_v271.py \
  backend/tests/test_live_data_gateway_v270.py \
  backend/tests/test_predicates.py \
  backend/tests/test_public_api_v230.py

PYTHONPATH="backend:backend/public_sdk/python" PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 \
  backend/.venv/bin/python -m pytest -q \
  backend/tests/test_economics_connectors_v273.py \
  backend/tests/test_scientific_connectors_v272.py \
  backend/tests/test_signature_dossiers_v250.py

# Disable third-party pytest plugin autoload for the Trust Center group; this
# avoids an inherited instrumentation shutdown interaction without skipping tests.
PYTHONPATH="backend:backend/public_sdk/python" PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 \
  backend/.venv/bin/python -m pytest -q backend/tests/test_trust_center_v240.py

SMOKE_DB="$WORKDIR/backend/platform_core_v273_push_smoke.db"
rm -f "$SMOKE_DB"
SC_CORE_DATABASE_URL="sqlite:///${SMOKE_DB}" \
SC_CORE_ENVIRONMENT=test \
SC_CORE_WRITE_API_KEY=x \
SC_CORE_API_LOG_SALT=y \
SC_CORE_WEBHOOK_SIGNING_SECRET=z \
SC_CORE_DOSSIER_SIGNING_SECRET=q \
backend/.venv/bin/python backend/scripts/migrate.py
rm -f "$SMOKE_DB"

mkdir -p dist
(
  cd wordpress-plugin
  zip -qr ../dist/sustainable-catalyst-platform-core-plugin-v2.7.3.zip sustainable-catalyst-platform-core
)
cp backend/public_sdk/downloads/sc-platform-core-public-python-v2.7.3.zip dist/
cp backend/public_sdk/downloads/sc-platform-core-public-javascript-v2.7.3.zip dist/
cp backend/public_sdk/postman/Sustainable_Catalyst_Public_API_v1.postman_collection.json dist/

git add -A
if git diff --cached --quiet; then
  echo "No repository changes need to be committed."
else
  git commit -m "Build Platform Core v2.7.3 economics and official statistics connector pack"
fi

git push --set-upstream origin "$BRANCH"

printf '%s\n' \
  "" \
  "============================================================" \
  "PLATFORM CORE v2.7.3 PUSHED SUCCESSFULLY" \
  "============================================================" \
  "Repository: https://github.com/${ORG}/${REPO}" \
  "Local path: ${WORKDIR}"
