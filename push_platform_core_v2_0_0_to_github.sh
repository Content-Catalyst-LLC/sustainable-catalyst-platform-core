#!/usr/bin/env bash
set -euo pipefail

ORG="Content-Catalyst-LLC"
REPO="sustainable-catalyst-platform-core"
BRANCH="main"
DOWNLOADS="${HOME}/Downloads"
PACKAGE_ZIP="${DOWNLOADS}/sustainable-catalyst-platform-core-v2.0.0-repo.zip"
WORKDIR="${DOWNLOADS}/sustainable-catalyst-platform-core-repo"
EXTRACT_DIR="${DOWNLOADS}/sc-platform-core-v2.0.0-package"
SSH_URL="git@github.com:${ORG}/${REPO}.git"
HTTPS_URL="https://github.com/${ORG}/${REPO}.git"

echo "Sustainable Catalyst Platform Core v2.0.0"
echo "Target: ${SSH_URL}"

for cmd in git unzip rsync python3 grep; do
  command -v "$cmd" >/dev/null 2>&1 || {
    echo "Required command not found: $cmd"
    exit 1
  }
done

if [ ! -f "$PACKAGE_ZIP" ]; then
  echo "Could not find package zip:"
  echo "  $PACKAGE_ZIP"
  echo "Download it into ~/Downloads, then rerun this script."
  exit 1
fi

rm -rf "$EXTRACT_DIR"
mkdir -p "$EXTRACT_DIR"
unzip -q "$PACKAGE_ZIP" -d "$EXTRACT_DIR"

SOURCE_ROOT="$(find "$EXTRACT_DIR" -maxdepth 1 -type d -name 'sustainable-catalyst-platform-core-v2.0.0' | head -1)"
if [ -z "$SOURCE_ROOT" ] || [ ! -f "$SOURCE_ROOT/backend/app/main.py" ]; then
  echo "Could not locate the Platform Core source folder in the zip."
  exit 1
fi

if [ -d "$WORKDIR/.git" ]; then
  echo "Using existing repository: $WORKDIR"
  cd "$WORKDIR"
  git remote set-url origin "$SSH_URL"
  git fetch origin "$BRANCH"
  git checkout "$BRANCH"
  git pull --rebase origin "$BRANCH"
else
  rm -rf "$WORKDIR"
  echo "Cloning repository..."
  if ! git clone --branch "$BRANCH" "$SSH_URL" "$WORKDIR"; then
    echo "SSH clone failed. Trying HTTPS."
    git clone --branch "$BRANCH" "$HTTPS_URL" "$WORKDIR"
  fi
fi

echo "Replacing repository contents with v2.0.0..."
rsync -a --delete \
  --exclude='.git' \
  "$SOURCE_ROOT/" "$WORKDIR/"

cd "$WORKDIR"

echo "Checking required build markers..."
test -f backend/app/main.py
test -f backend/app/models.py
test -f backend/data/platform_core_seed_v2.0.0.json
test -f wordpress-plugin/sustainable-catalyst-platform-core/sustainable-catalyst-platform-core.php
grep -q 'version: str = "2.0.0"' backend/app/config.py
grep -q 'Universal Entity Registry' README.md

echo "Running push-safe secret scan..."
if grep -RInE \
  '(sk-proj-[A-Za-z0-9_-]{20,}|sk-[A-Za-z0-9_-]{30,}|AIza[0-9A-Za-z_-]{20,}|SC_CORE_WRITE_API_KEY=[^<[:space:]]{16,})' \
  . \
  --exclude-dir=.git \
  --exclude='.env.example'; then
  echo "Potential secret found. Aborting."
  exit 1
fi

echo "Running backend tests..."
(
  cd backend
  if [ ! -d .venv ]; then
    python3 -m venv .venv
  fi
  source .venv/bin/activate
  python -m pip install --upgrade pip
  pip install -r requirements.txt
  pytest -q
)

echo "Building WordPress plugin zip..."
mkdir -p dist
rm -f dist/sustainable-catalyst-platform-core-plugin-v2.0.0.zip
(
  cd wordpress-plugin
  zip -qr ../dist/sustainable-catalyst-platform-core-plugin-v2.0.0.zip \
    sustainable-catalyst-platform-core
)

git add .
if git diff --cached --quiet; then
  echo "No changes to commit."
else
  git commit -m "Build Platform Core v2.0.0 universal entity registry foundation"
fi

git push origin "$BRANCH"

echo ""
echo "Platform Core v2.0.0 pushed successfully."
echo "Repository: https://github.com/${ORG}/${REPO}"
echo "WordPress plugin: ${WORKDIR}/dist/sustainable-catalyst-platform-core-plugin-v2.0.0.zip"
