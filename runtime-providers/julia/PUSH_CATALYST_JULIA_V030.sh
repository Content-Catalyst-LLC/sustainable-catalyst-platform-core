#!/usr/bin/env bash
set -euo pipefail

REPO="${1:-$HOME/Downloads/sustainable-catalyst-platform-core}"
SOURCE="${2:-$(cd "$(dirname "$0")" && pwd)}"
DEST="$REPO/runtime-providers/julia"

[[ -d "$REPO/.git" ]] || {
  echo "ERROR: Core repo not found at $REPO"
  exit 2
}

cd "$REPO"
git checkout main
git pull --ff-only origin main
git fetch origin --tags

git rev-parse -q --verify refs/tags/v3.23.0 >/dev/null || {
  echo "ERROR: Platform Core v3.23.0 tag is required before Julia v0.3.0."
  exit 3
}

if git rev-parse -q --verify refs/tags/catalyst-julia-v0.3.0 >/dev/null; then
  echo "ERROR: catalyst-julia-v0.3.0 already exists; refusing to rewrite tag."
  exit 4
fi

echo "=== STATIC RELEASE VALIDATION ==="
"$SOURCE/VALIDATE_RELEASE_V030.sh"

echo "=== INSTALL PROVIDER INTO PLATFORM CORE ==="
mkdir -p "$DEST"
rsync -a --delete \
  --exclude '.git' \
  --exclude '__pycache__' \
  --exclude '.pytest_cache' \
  "$SOURCE/" "$DEST/"

echo "=== VALIDATE INSTALLED PROVIDER COPY ==="
"$DEST/VALIDATE_RELEASE_V030.sh"

echo "=== COMMIT / PUSH / TAG ==="
git add runtime-providers/julia
git status --short

if git diff --cached --quiet; then
  echo "ERROR: no Julia v0.3.0 changes staged."
  exit 5
fi

git commit -m "Build Catalyst Julia Runtime v0.3.0 Core Runtime Contract Adapter"
git push origin main

git tag -a catalyst-julia-v0.3.0 \
  -m "Catalyst Julia Runtime v0.3.0 — Core Runtime Contract Adapter"
git push origin catalyst-julia-v0.3.0

echo "PASS - Catalyst Julia Runtime v0.3.0 pushed and tagged"
git log -1 --oneline --decorate
