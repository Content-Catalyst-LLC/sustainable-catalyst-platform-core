#!/usr/bin/env bash
set -euo pipefail
trap 'rc=$?; echo "ERROR: v2.36.1 promotion stopped at line $LINENO (exit $rc): $BASH_COMMAND" >&2; exit $rc' ERR
PACKAGE_ZIP="${1:-${HOME}/Downloads/sustainable-catalyst-platform-core-v2.36.1-repository.zip}"
WORKDIR="${SC_CORE_REPO_DIR:-${HOME}/Downloads/sustainable-catalyst-platform-core}"
REMOTE="${SC_CORE_GIT_REMOTE:-git@github.com:Content-Catalyst-LLC/sustainable-catalyst-platform-core.git}"
PYTHON_BIN="${PYTHON_BIN:-python3}"
[ -f "$PACKAGE_ZIP" ] || { echo "ERROR: repository package not found: $PACKAGE_ZIP"; exit 1; }
[ -d "$WORKDIR/.git" ] || { echo "ERROR: local Git checkout not found: $WORKDIR"; exit 1; }
for c in unzip rsync git php node bash; do command -v "$c" >/dev/null 2>&1 || { echo "ERROR: required command not found: $c"; exit 1; }; done
TMP="$(mktemp -d "${TMPDIR:-/tmp}/sc-platform-core-v2361-push.XXXXXX")"; trap 'rm -rf "$TMP"' EXIT
unzip -q "$PACKAGE_ZIP" -d "$TMP"
SOURCE_ROOT="$TMP/sustainable-catalyst-platform-core-v2.36.1"
[ -f "$SOURCE_ROOT/backend/app/main.py" ] || { echo "ERROR: expected v2.36.1 source root missing"; exit 1; }
cd "$WORKDIR"; git remote get-url origin >/dev/null 2>&1 || git remote add origin "$REMOTE"; git checkout main; git fetch origin main --tags; git pull --ff-only origin main
if ! git diff --quiet || ! git diff --cached --quiet || [ -n "$(git ls-files --others --exclude-standard)" ]; then echo "STOP: local repository has uncommitted changes; promotion will not overwrite them."; git status --short; exit 1; fi
rsync -a --delete --exclude='.git/' --exclude='backend/.venv/' --exclude='__pycache__/' --exclude='.pytest_cache/' "$SOURCE_ROOT/" "$WORKDIR/"
"$PYTHON_BIN" scripts/validate_v2361_release.py
"$PYTHON_BIN" scripts/scan_push_safe_secrets.py .
php -l wordpress-plugin/sustainable-catalyst-platform-core/sustainable-catalyst-platform-core.php >/dev/null
node --check backend/public_sdk/javascript/index.mjs
bash -n deploy_and_validate_platform_core_v2_36_1_macos.sh
bash -n DEPLOY_PLATFORM_CORE_V2361_CONTABO.sh
git add -A
if git diff --cached --quiet; then echo "No repository changes need to be committed."; else git commit -m "Build Platform Core v2.36.1 uncertainty compute runtime integration"; fi
git push origin main
if git rev-parse 'v2.36.1' >/dev/null 2>&1; then echo "Tag v2.36.1 already exists locally."; else git tag -a v2.36.1 -m "Platform Core v2.36.1 — Uncertainty Compute Runtime Integration"; fi
git push origin v2.36.1
echo "PASS - Platform Core v2.36.1 pushed successfully"
