#!/usr/bin/env bash
set -euo pipefail

ORG="Content-Catalyst-LLC"
REPO="sustainable-catalyst-platform-core"
BRANCH="main"
REMOTE="git@github.com:${ORG}/${REPO}.git"

PACKAGE_ZIP="${1:-${HOME}/Downloads/sustainable-catalyst-platform-core-v2.7.1.zip}"
WORKDIR="${2:-${HOME}/Downloads/sustainable-catalyst-platform-core-repo}"
EXTRACT_DIR="${TMPDIR:-/tmp}/sc-platform-core-v271-extracted"

printf '%s\n' \
  "============================================================" \
  "PLATFORM CORE v2.7.1 — INTERNATIONAL LAW AND UN CONNECTORS" \
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
SOURCE_ROOT="$(find "$EXTRACT_DIR" -maxdepth 1 -type d -name 'sustainable-catalyst-platform-core-v2.7.1' | head -1)"

[ -n "$SOURCE_ROOT" ] && [ -f "$SOURCE_ROOT/backend/app/main.py" ] || {
  echo "ERROR: The ZIP does not contain the expected v2.7.1 repository root."
  exit 1
}

if [ -d "$WORKDIR/.git" ]; then
  cd "$WORKDIR"
  git remote set-url origin "$REMOTE"
  if ! git diff --quiet || ! git diff --cached --quiet || [ -n "$(git ls-files --others --exclude-standard)" ]; then
    git stash push -u -m "Automatic safety stash before Platform Core v2.7.1" >/dev/null || true
  fi
  git fetch origin --prune
  git checkout "$BRANCH"
  git pull --ff-only origin "$BRANCH"
else
  rm -rf "$WORKDIR"
  git clone --branch "$BRANCH" "$REMOTE" "$WORKDIR"
fi

find "$WORKDIR" -type d -name '__pycache__' -prune -exec rm -rf {} + 2>/dev/null || true
rm -rf "$WORKDIR/backend/.venv" "$WORKDIR/backend/.pytest_cache"

rsync -a --delete \
  --exclude='.git/' \
  --exclude='.venv/' \
  --exclude='.pytest_cache/' \
  --exclude='__pycache__/' \
  --exclude='*.db' \
  "$SOURCE_ROOT/" "$WORKDIR/"

cd "$WORKDIR"

echo "Validating v2.7.1 release markers..."
test -f backend/app/routers/international_law.py
test -f backend/app/services/international_law.py
test -f backend/tests/test_international_law_un_v271.py
test -f schemas/international-law-record-v1.schema.json
test -f docs/INTERNATIONAL_LAW_UN_CONNECTORS_V271.md
test -f RELEASE_NOTES_V271.md
test -f deployment/platform-core-v271.env.example
test -f backend/public_sdk/downloads/sc-platform-core-public-python-v2.7.1.zip
test -f backend/public_sdk/downloads/sc-platform-core-public-javascript-v2.7.1.zip
grep -q 'version: str = "2.7.1"' backend/app/config.py
grep -q '"0008"' backend/app/migrations.py
grep -q 'international_law_record_store' backend/app/routers/meta.py
grep -q 'un.digital-library' backend/app/live_data_catalog.py
grep -q 'official_security_council_resolution' backend/app/services/international_law.py

printf '%s\n' "Running a push-safe secret scan..."
SECRET_HITS="$({
  grep -RInE \
    '(sk-proj-[A-Za-z0-9_-]{20,}|sk-[A-Za-z0-9_-]{30,}|AIza[0-9A-Za-z_-]{20,}|gh[opusr]_[A-Za-z0-9_]{20,}|SC_CORE_WRITE_API_KEY=[^<[:space:]]{16,}|SC_CORE_FRED_API_KEY=[A-Za-z0-9]{20,}|Authorization:[[:space:]]*Bearer[[:space:]]+[A-Za-z0-9._-]{24,})' \
    . \
    --exclude-dir=.git \
    --exclude-dir=.venv \
    --exclude-dir=.pytest_cache \
    --exclude='*.zip' \
    --exclude='*.pyc' \
    --exclude='.env.example' \
    --exclude='platform-core-v271.env.example' \
    --exclude='PUSH_PLATFORM_CORE_V271_FINAL.sh' \
    || true
} | grep -viE \
  '(your[-_ ]?(write[-_ ]?)?key|your[-_ ]?fred[-_ ]?api[-_ ]?key|replace[-_ ]?me|change[-_ ]?me|example[-_ ]?key|placeholder|generate-a-long-random-secret|RECORD_ID)' \
  || true)"

if [ -n "$SECRET_HITS" ]; then
  printf '%s\n' "$SECRET_HITS"
  echo "ERROR: A potential secret was found. Nothing was pushed."
  exit 1
fi

"$PYTHON_BIN" -m venv backend/.venv
backend/.venv/bin/python -m pip install --upgrade pip
backend/.venv/bin/python -m pip install -r backend/requirements.txt
PYTHONPATH="backend:backend/public_sdk/python" DD_TRACE_ENABLED=false \
  backend/.venv/bin/python -m pytest -q -p no:ddtrace backend/tests

SMOKE_DB="$WORKDIR/backend/platform_core_v271_push_smoke.db"
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
  zip -qr ../dist/sustainable-catalyst-platform-core-plugin-v2.7.1.zip sustainable-catalyst-platform-core
)
cp backend/public_sdk/downloads/sc-platform-core-public-python-v2.7.1.zip dist/
cp backend/public_sdk/downloads/sc-platform-core-public-javascript-v2.7.1.zip dist/
cp backend/public_sdk/postman/Sustainable_Catalyst_Public_API_v1.postman_collection.json dist/

git add -A
if git diff --cached --quiet; then
  echo "No repository changes need to be committed."
else
  git commit -m "Build Platform Core v2.7.1 international law and UN connector pack"
fi

git push --set-upstream origin "$BRANCH"

printf '%s\n' \
  "" \
  "============================================================" \
  "PLATFORM CORE v2.7.1 PUSHED SUCCESSFULLY" \
  "============================================================" \
  "Repository: https://github.com/${ORG}/${REPO}" \
  "Local path: ${WORKDIR}"
