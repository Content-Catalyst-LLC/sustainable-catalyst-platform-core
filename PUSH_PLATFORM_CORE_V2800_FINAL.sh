#!/usr/bin/env bash
set -euo pipefail
trap 'rc=$?; echo "ERROR: v2.80.0 promotion stopped at line $LINENO (exit $rc): $BASH_COMMAND" >&2; exit $rc' ERR

PACKAGE_ZIP="${1:-${HOME}/Downloads/sustainable-catalyst-platform-core-v2.80.0-repository.zip}"
WORKDIR="${SC_CORE_REPO_DIR:-${HOME}/Downloads/sustainable-catalyst-platform-core}"
REMOTE="${SC_CORE_GIT_REMOTE:-git@github.com:Content-Catalyst-LLC/sustainable-catalyst-platform-core.git}"
TAG="v2.80.0"
PYTHON_BIN="${PYTHON_BIN:-python3}"

[ -f "$PACKAGE_ZIP" ] || { echo "ERROR: repository package not found: $PACKAGE_ZIP"; exit 1; }
[ -d "$WORKDIR/.git" ] || { echo "ERROR: local Git checkout not found: $WORKDIR"; exit 1; }
for c in unzip rsync git php node bash shasum; do command -v "$c" >/dev/null 2>&1 || { echo "ERROR: required command not found: $c"; exit 1; }; done

TMP="$(mktemp -d "${TMPDIR:-/tmp}/sc-platform-core-v2800-push.XXXXXX")"
trap 'rm -rf "$TMP"' EXIT
unzip -q "$PACKAGE_ZIP" -d "$TMP"
SOURCE_ROOT="$TMP/sustainable-catalyst-platform-core-v2.80.0"
[ -f "$SOURCE_ROOT/backend/app/main.py" ] || { echo "ERROR: expected v2.80.0 source root missing"; exit 1; }

source_migration_sha="$(shasum -a 256 "$SOURCE_ROOT/backend/app/migrations.py" | awk '{print $1}')"
cd "$SOURCE_ROOT"
"$PYTHON_BIN" -S scripts/validate_v2800_release.py
"$PYTHON_BIN" scripts/scan_push_safe_secrets.py .

cd "$WORKDIR"
git remote get-url origin >/dev/null 2>&1 || git remote add origin "$REMOTE"
git checkout main
git fetch origin main --tags
git pull --ff-only origin main
if ! git diff --quiet || ! git diff --cached --quiet || [ -n "$(git ls-files --others --exclude-standard)" ]; then
  echo "STOP: local repository has uncommitted changes; promotion will not overwrite them."
  git status --short
  exit 1
fi
if git rev-parse -q --verify "refs/tags/$TAG" >/dev/null 2>&1 || git ls-remote --exit-code --tags origin "refs/tags/$TAG" >/dev/null 2>&1; then
  echo "STOP: tag $TAG already exists; refusing to reuse or move a release tag."
  exit 1
fi

rsync -a --delete --exclude='.git/' --exclude='backend/.venv/' --exclude='__pycache__/' --exclude='.pytest_cache/' "$SOURCE_ROOT/" "$WORKDIR/"
work_migration_sha="$(shasum -a 256 backend/app/migrations.py | awk '{print $1}')"
[ "$source_migration_sha" = "$work_migration_sha" ] || { echo "STOP: promoted migrations.py does not match frozen archive"; exit 1; }
"$PYTHON_BIN" -S scripts/validate_v2800_release.py
"$PYTHON_BIN" scripts/scan_push_safe_secrets.py .
php -l wordpress-plugin/sustainable-catalyst-platform-core/sustainable-catalyst-platform-core.php >/dev/null
node --check backend/public_sdk/javascript/index.mjs
bash -n deploy_and_validate_platform_core_v2_80_0_macos.sh
bash -n DEPLOY_PLATFORM_CORE_V2800_CONTABO.sh

git add -A
if git diff --cached --quiet; then
  echo "No repository changes need to be committed."
else
  git commit -m "Build Platform Core v2.80.0 Research Decision Trace & Conclusion Governance"
fi
git push origin main
head_commit="$(git rev-parse HEAD)"
git_file_sha="$(git show HEAD:backend/app/migrations.py | shasum -a 256 | awk '{print $1}')"
[ "$git_file_sha" = "$source_migration_sha" ] || { echo "STOP: committed migrations.py differs from frozen archive"; exit 1; }
git tag -a "$TAG" -m "Platform Core v2.80.0 Research Decision Trace & Conclusion Governance"
git push origin "$TAG"
tag_commit="$(git rev-list -n 1 "$TAG")"
[ "$tag_commit" = "$head_commit" ] || { echo "STOP: tag does not resolve to promoted HEAD"; exit 1; }

echo "PASS - archive migrations.py matches committed/tagged migrations.py"
echo "PASS - tag v2.80.0 resolves to exact promoted HEAD $head_commit"
echo "PASS - Platform Core v2.80.0 pushed successfully"
