#!/usr/bin/env bash
set -euo pipefail

ORG="Content-Catalyst-LLC"
REPO="sustainable-catalyst-platform-core"
BRANCH="main"
REPO_SLUG="${ORG}/${REPO}"
SSH_REMOTE="git@github.com:${REPO_SLUG}.git"
WEB_URL="https://github.com/${REPO_SLUG}"

DOWNLOADS="${HOME}/Downloads"
PACKAGE_ZIP="${DOWNLOADS}/sustainable-catalyst-platform-core-v2.1.0-repo.zip"
WORKDIR="${DOWNLOADS}/sustainable-catalyst-platform-core-repo"
EXTRACT_DIR="${DOWNLOADS}/sc-platform-core-v2.1.0-extracted"

echo "============================================================"
echo "PLATFORM CORE v2.1.0 UPDATE — SSH ONLY"
echo "============================================================"
echo "Repository: ${WEB_URL}"

for cmd in gh git unzip rsync python3 grep zip find ssh; do
  command -v "$cmd" >/dev/null 2>&1 || { echo "ERROR: Required command not found: $cmd"; exit 1; }
done

gh auth status --hostname github.com >/dev/null 2>&1 || { echo "ERROR: GitHub CLI is not authenticated."; exit 1; }
ssh -T git@github.com 2>&1 | grep -q "successfully authenticated" || { echo "ERROR: GitHub SSH authentication did not verify."; exit 1; }

if [ ! -f "$PACKAGE_ZIP" ]; then
  echo "ERROR: Package ZIP not found: $PACKAGE_ZIP"
  exit 1
fi

if ! gh repo view "$REPO_SLUG" >/dev/null 2>&1; then
  gh repo create "$REPO_SLUG" --public --description "Shared entity registry, knowledge graph, provenance foundation, and integration layer for Sustainable Catalyst." --disable-wiki
fi

rm -rf "$EXTRACT_DIR"
mkdir -p "$EXTRACT_DIR"
unzip -q "$PACKAGE_ZIP" -d "$EXTRACT_DIR"

SOURCE_ROOT="$(find "$EXTRACT_DIR" -maxdepth 1 -type d -name "sustainable-catalyst-platform-core-v2.1.0" | head -1)"
if [ -z "${SOURCE_ROOT:-}" ] || [ ! -f "$SOURCE_ROOT/backend/app/main.py" ]; then
  echo "ERROR: Could not locate Platform Core v2.1.0 in the ZIP."
  exit 1
fi

if [ -d "$WORKDIR/.git" ]; then
  cd "$WORKDIR"
  git remote set-url origin "$SSH_REMOTE"
  git fetch origin --prune
  git checkout "$BRANCH"
  git pull --rebase origin "$BRANCH"
else
  rm -rf "$WORKDIR"
  git clone "$SSH_REMOTE" "$WORKDIR"
  cd "$WORKDIR"
  git checkout "$BRANCH"
fi

rsync -a --delete --exclude=".git" --exclude="__pycache__" --exclude=".pytest_cache" "$SOURCE_ROOT/" "$WORKDIR/"
cd "$WORKDIR"

test -f backend/app/predicate_catalog.py
test -f backend/app/routers/explorer.py
test -f backend/tests/test_graph_engine_v210.py
test -f backend/data/platform_core_seed_v2.1.0.json
grep -q 'version: str = "2.1.0"' backend/app/config.py

if grep -RInE '(sk-proj-[A-Za-z0-9_-]{20,}|sk-[A-Za-z0-9_-]{30,}|AIza[0-9A-Za-z_-]{20,}|SC_CORE_WRITE_API_KEY=[^<[:space:]]{16,})' . --exclude-dir=.git --exclude=".env.example"; then
  echo "ERROR: Potential secret found."
  exit 1
fi

(
  cd backend
  if [ ! -d .venv ]; then python3 -m venv .venv; fi
  source .venv/bin/activate
  python -m pip install --upgrade pip
  pip install -r requirements.txt
  pytest -q
)

mkdir -p dist
rm -f dist/sustainable-catalyst-platform-core-plugin-v2.1.0.zip
(
  cd wordpress-plugin
  zip -qr ../dist/sustainable-catalyst-platform-core-plugin-v2.1.0.zip sustainable-catalyst-platform-core
)

git add .
if git diff --cached --quiet; then
  echo "No changes to commit."
else
  git commit -m "Build Platform Core v2.1.0 knowledge graph and relationship engine"
fi
git push origin "$BRANCH"

echo "Platform Core v2.1.0 pushed successfully."
echo "GitHub repository: ${WEB_URL}"
echo "Local repository:  ${WORKDIR}"
echo "SSH remote:        $(git remote get-url origin)"
