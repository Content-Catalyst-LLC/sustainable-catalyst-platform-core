#!/usr/bin/env bash
set -euo pipefail

ORG="Content-Catalyst-LLC"
REPO="sustainable-catalyst-platform-core"
BRANCH="main"
REMOTE="git@github.com:${ORG}/${REPO}.git"

PACKAGE_ZIP="${1:-${HOME}/Downloads/sustainable-catalyst-platform-core-v2.7.0.zip}"
WORKDIR="${2:-${HOME}/Downloads/sustainable-catalyst-platform-core-repo}"
EXTRACT_DIR="${TMPDIR:-/tmp}/sc-platform-core-v270-extracted"

printf '%s\n' \
  "============================================================" \
  "PLATFORM CORE v2.7.0 — FREE LIVE DATA GATEWAY" \
  "============================================================" \
  "Package:    ${PACKAGE_ZIP}" \
  "Repository: ${WORKDIR}" \
  "Remote:     ${REMOTE}" \
  ""

for command_name in git unzip rsync grep find; do
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
SOURCE_ROOT="$(find "$EXTRACT_DIR" -maxdepth 1 -type d -name 'sustainable-catalyst-platform-core-v2.7.0' | head -1)"

[ -n "$SOURCE_ROOT" ] && [ -f "$SOURCE_ROOT/backend/app/main.py" ] || {
  echo "ERROR: The ZIP does not contain the expected v2.7.0 repository root."
  exit 1
}

if [ -d "$WORKDIR/.git" ]; then
  cd "$WORKDIR"
  git remote set-url origin "$REMOTE"
  if ! git diff --quiet || ! git diff --cached --quiet || [ -n "$(git ls-files --others --exclude-standard)" ]; then
    git stash push -u -m "Automatic safety stash before Platform Core v2.7.0" >/dev/null || true
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
  "$SOURCE_ROOT/" "$WORKDIR/"

cd "$WORKDIR"

echo "Validating v2.7.0 release markers..."
test -f backend/app/live_data_catalog.py
test -f backend/app/connectors/adapters.py
test -f backend/app/services/live_data.py
test -f backend/app/routers/live_data.py
test -f backend/tests/test_live_data_gateway_v270.py
test -f docs/FREE_LIVE_DATA_GATEWAY_V270.md
test -f RELEASE_NOTES_V270.md
test -f backend/public_sdk/downloads/sc-platform-core-public-python-v2.7.0.zip
test -f backend/public_sdk/downloads/sc-platform-core-public-javascript-v2.7.0.zip
grep -q 'version: str = "2.7.0"' backend/app/config.py
grep -q '"0007"' backend/app/migrations.py
grep -q 'free_live_data_gateway' backend/app/routers/meta.py

printf '%s\n' "Running a push-safe secret scan..."
if grep -RInE \
  '(sk-proj-[A-Za-z0-9_-]{20,}|sk-[A-Za-z0-9_-]{30,}|AIza[0-9A-Za-z_-]{20,}|gh[opusr]_[A-Za-z0-9_]{20,}|SC_CORE_WRITE_API_KEY=[^<[:space:]]{16,}|SC_CORE_FRED_API_KEY=[A-Za-z0-9]{20,})' \
  . \
  --exclude-dir=.git \
  --exclude-dir=.venv \
  --exclude='*.zip' \
  --exclude='.env.example' \
  --exclude='PUSH_PLATFORM_CORE_V270_FINAL.sh'; then
  echo "ERROR: A potential secret was found. Nothing was pushed."
  exit 1
fi

"$PYTHON_BIN" -m venv backend/.venv
backend/.venv/bin/python -m pip install --upgrade pip
backend/.venv/bin/python -m pip install -r backend/requirements.txt
backend/.venv/bin/python -m pytest -q backend/tests

SMOKE_DB="$WORKDIR/backend/platform_core_v270_push_smoke.db"
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
  zip -qr ../dist/sustainable-catalyst-platform-core-plugin-v2.7.0.zip sustainable-catalyst-platform-core
)
cp backend/public_sdk/downloads/sc-platform-core-public-python-v2.7.0.zip dist/
cp backend/public_sdk/downloads/sc-platform-core-public-javascript-v2.7.0.zip dist/
cp backend/public_sdk/postman/Sustainable_Catalyst_Public_API_v1.postman_collection.json dist/

git add -A
if git diff --cached --quiet; then
  echo "No repository changes need to be committed."
else
  git commit -m "Build Platform Core v2.7.0 free live data gateway"
fi

git push --set-upstream origin "$BRANCH"

printf '%s\n' \
  "" \
  "============================================================" \
  "PLATFORM CORE v2.7.0 PUSHED SUCCESSFULLY" \
  "============================================================" \
  "Repository: https://github.com/${ORG}/${REPO}" \
  "Local path: ${WORKDIR}"
