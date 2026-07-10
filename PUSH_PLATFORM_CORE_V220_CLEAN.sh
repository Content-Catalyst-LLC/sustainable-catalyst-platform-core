#!/usr/bin/env bash
set -euo pipefail

ORG="Content-Catalyst-LLC"
REPO="sustainable-catalyst-platform-core"
BRANCH="main"

REPO_SLUG="${ORG}/${REPO}"
SSH_REMOTE="git@github.com:${REPO_SLUG}.git"
WEB_URL="https://github.com/${REPO_SLUG}"

DOWNLOADS="${HOME}/Downloads"
PACKAGE_ZIP="${DOWNLOADS}/sustainable-catalyst-platform-core-v2.2.0-repo.zip"
WORKDIR="${DOWNLOADS}/sustainable-catalyst-platform-core-repo"
EXTRACT_DIR="${DOWNLOADS}/sc-platform-core-v2.2.0-clean-extracted"

echo "============================================================"
echo "PLATFORM CORE v2.2.0 — CLEAN EVIDENCE LEDGER PUSH"
echo "============================================================"
echo "Repository: ${WEB_URL}"
echo "Git remote: ${SSH_REMOTE}"
echo ""

for command_name in gh git ssh unzip rsync grep zip find; do
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

echo "Using Python:"
"$PYTHON_BIN" --version

echo "Checking GitHub CLI authentication..."
gh auth status --hostname github.com >/dev/null 2>&1 || {
  echo "ERROR: GitHub CLI is not authenticated."
  echo "Run: gh auth login --hostname github.com --git-protocol ssh --web"
  exit 1
}

echo "Checking GitHub SSH authentication..."
SSH_CHECK_OUTPUT="$(ssh -T git@github.com 2>&1 || true)"
if ! printf '%s\n' "$SSH_CHECK_OUTPUT" | grep -q "successfully authenticated"; then
  echo "ERROR: GitHub SSH authentication did not verify."
  printf '%s\n' "$SSH_CHECK_OUTPUT"
  exit 1
fi

if [ ! -f "$PACKAGE_ZIP" ]; then
  echo "ERROR: Package ZIP was not found:"
  echo "  ${PACKAGE_ZIP}"
  exit 1
fi

if ! gh repo view "$REPO_SLUG" >/dev/null 2>&1; then
  echo "Creating the missing GitHub repository..."
  gh repo create "$REPO_SLUG" \
    --public \
    --description "Shared entity registry, knowledge graph, evidence ledger, provenance, and trust infrastructure for Sustainable Catalyst." \
    --disable-wiki
fi

echo "Extracting Platform Core v2.2.0..."
rm -rf "$EXTRACT_DIR"
mkdir -p "$EXTRACT_DIR"
unzip -q "$PACKAGE_ZIP" -d "$EXTRACT_DIR"

SOURCE_ROOT="$(
  find "$EXTRACT_DIR" \
    -maxdepth 1 \
    -type d \
    -name "sustainable-catalyst-platform-core-v2.2.0" \
    | head -1
)"

if [ -z "${SOURCE_ROOT:-}" ] || [ ! -f "$SOURCE_ROOT/backend/app/main.py" ]; then
  echo "ERROR: Could not locate Platform Core v2.2.0 inside the ZIP."
  exit 1
fi

REMOTE_HAS_MAIN=false
if git ls-remote --exit-code --heads "$SSH_REMOTE" "$BRANCH" >/dev/null 2>&1; then
  REMOTE_HAS_MAIN=true
fi

if [ -d "$WORKDIR/.git" ]; then
  echo "Using the existing local repository."
  cd "$WORKDIR"
  git remote set-url origin "$SSH_REMOTE"

  if ! git diff --quiet || ! git diff --cached --quiet || [ -n "$(git ls-files --others --exclude-standard)" ]; then
    echo "Saving unfinished local changes in a safety stash..."
    git stash push -u -m "Automatic safety stash before Platform Core v2.2.0" || true
  fi

  git fetch origin --prune

  if [ "$REMOTE_HAS_MAIN" = true ]; then
    git checkout -B "$BRANCH" "origin/$BRANCH"
  else
    git checkout -B "$BRANCH"
  fi
else
  rm -rf "$WORKDIR"

  if [ "$REMOTE_HAS_MAIN" = true ]; then
    echo "Cloning the repository through SSH..."
    git clone --branch "$BRANCH" "$SSH_REMOTE" "$WORKDIR"
  else
    echo "The remote repository is empty. Initializing main locally..."
    mkdir -p "$WORKDIR"
    cd "$WORKDIR"
    git init -b "$BRANCH"
    git remote add origin "$SSH_REMOTE"
  fi
fi

echo "Removing any damaged local virtual environment..."
chmod -R u+w "$WORKDIR/backend/.venv" 2>/dev/null || true
rm -rf "$WORKDIR/backend/.venv"
rm -rf "$WORKDIR/backend/.pytest_cache"
find "$WORKDIR" -type d -name "__pycache__" -prune -exec rm -rf {} + 2>/dev/null || true

echo "Replacing repository contents with v2.2.0..."
rsync -a --delete \
  --exclude=".git/" \
  --exclude=".venv/" \
  --exclude=".pytest_cache/" \
  --exclude="__pycache__/" \
  "$SOURCE_ROOT/" "$WORKDIR/"

cd "$WORKDIR"

echo "Validating release markers..."
test -f backend/app/services/evidence.py
test -f backend/app/services/ledger.py
test -f backend/app/routers/evidence.py
test -f backend/app/routers/ledger.py
test -f backend/app/routers/evidence_explorer.py
test -f backend/tests/test_evidence_ledger_v220.py
test -f backend/data/platform_core_seed_v2.2.0.json
grep -q 'version: str = "2.2.0"' backend/app/config.py
grep -q "tamper_evident_ledger" backend/app/routers/meta.py

echo "Running push-safe secret scan..."
if grep -RInE \
  '(sk-proj-[A-Za-z0-9_-]{20,}|sk-[A-Za-z0-9_-]{30,}|AIza[0-9A-Za-z_-]{20,}|SC_CORE_WRITE_API_KEY=[^<[:space:]]{16,})' \
  . \
  --exclude-dir=.git \
  --exclude-dir=.venv \
  --exclude=".env.example"; then
  echo "ERROR: A potential secret was found. Nothing was pushed."
  exit 1
fi

echo "Creating a clean virtual environment..."
rm -rf backend/.venv
"$PYTHON_BIN" -m venv backend/.venv

if [ ! -x "backend/.venv/bin/python" ]; then
  echo "ERROR: The clean virtual environment was not created correctly."
  exit 1
fi

echo "Installing dependencies..."
backend/.venv/bin/python -m pip install --upgrade pip
backend/.venv/bin/python -m pip install -r backend/requirements.txt

echo "Running the full test suite..."
backend/.venv/bin/python -m pytest -q backend/tests

echo "Running a clean migration and seed smoke test..."
SMOKE_DB="${WORKDIR}/backend/platform_core_v220_push_smoke.db"
rm -f "$SMOKE_DB"
SC_CORE_DATABASE_URL="sqlite:///${SMOKE_DB}" \
SC_CORE_ENVIRONMENT="test" \
SC_CORE_WRITE_API_KEY="push-smoke-only" \
backend/.venv/bin/python backend/scripts/migrate.py

SC_CORE_DATABASE_URL="sqlite:///${SMOKE_DB}" \
SC_CORE_ENVIRONMENT="test" \
SC_CORE_WRITE_API_KEY="push-smoke-only" \
backend/.venv/bin/python backend/scripts/seed_registry.py

rm -f "$SMOKE_DB"

echo "Building the WordPress connector ZIP..."
mkdir -p dist
rm -f dist/sustainable-catalyst-platform-core-plugin-v2.2.0.zip
(
  cd wordpress-plugin
  zip -qr \
    ../dist/sustainable-catalyst-platform-core-plugin-v2.2.0.zip \
    sustainable-catalyst-platform-core
)

echo "Committing Platform Core v2.2.0..."
git add -A

if git diff --cached --quiet; then
  echo "No new repository changes need to be committed."
else
  git commit -m "Build Platform Core v2.2.0 evidence ledger and provenance records"
fi

echo "Pushing main through SSH..."
git push --set-upstream origin "$BRANCH"

echo ""
echo "============================================================"
echo "PLATFORM CORE v2.2.0 PUSHED SUCCESSFULLY"
echo "============================================================"
echo "GitHub repository: ${WEB_URL}"
echo "Local repository:  ${WORKDIR}"
echo "SSH remote:        $(git remote get-url origin)"
echo "Python used:       $("$PYTHON_BIN" --version 2>&1)"
echo "WordPress plugin:  ${WORKDIR}/dist/sustainable-catalyst-platform-core-plugin-v2.2.0.zip"
