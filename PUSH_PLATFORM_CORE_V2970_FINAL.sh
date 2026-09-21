#!/usr/bin/env bash
set -euo pipefail
trap 'rc=$?; echo "ERROR: v2.97.0 promotion stopped at line $LINENO (exit $rc): $BASH_COMMAND" >&2; exit $rc' ERR
ARCHIVE="${1:?usage: $0 /path/to/sustainable-catalyst-platform-core-v2.97.0-repository.zip}"
REPO="${SC_CORE_REPO:-$HOME/Downloads/sustainable-catalyst-platform-core}"; TAG=v2.97.0
[ -f "$ARCHIVE" ] || { echo "STOP: repository archive not found: $ARCHIVE"; exit 1; }
TMP="$(mktemp -d)"; cleanup(){ rm -rf "$TMP"; }; trap cleanup EXIT
unzip -q "$ARCHIVE" -d "$TMP"; SRC="$(find "$TMP" -maxdepth 1 -type d -name 'sustainable-catalyst-platform-core-v2.97.0' | head -1)"; [ -n "$SRC" ] || { echo "STOP: archive root not found"; exit 1; }
python3 -S "$SRC/scripts/validate_v2970_release.py"
echo "=== BOOTSTRAP V2.97 VALIDATION ENVIRONMENT ==="; VENV="$TMP/v2970-venv"; python3 -m venv "$VENV"; "$VENV/bin/python" -m pip install --disable-pip-version-check -q -r "$SRC/backend/requirements.txt"
PYTHONPATH="$SRC/backend" "$VENV/bin/python" "$SRC/backend/scripts/validate_platform_research_integration_certification.py"
source_migration_sha="$(shasum -a 256 "$SRC/backend/app/migrations.py" | awk '{print $1}')"
[ -d "$REPO/.git" ] || { echo "STOP: Git checkout not found at $REPO"; exit 1; }
cd "$REPO"; git fetch origin --tags; git checkout main; git pull --ff-only origin main
git tag -l "$TAG" | grep -q . && { echo "STOP: local tag $TAG already exists"; exit 1; }; git ls-remote --exit-code --tags origin "refs/tags/$TAG" >/dev/null 2>&1 && { echo "STOP: remote tag $TAG already exists"; exit 1; } || true
rsync -a --delete --exclude='.git/' "$SRC/" "$REPO/"
python3 -S scripts/validate_v2970_release.py; PYTHONPATH="$REPO/backend" "$VENV/bin/python" backend/scripts/validate_platform_research_integration_certification.py; "$VENV/bin/python" -m compileall -q backend/app backend/scripts backend/tests; php -l wordpress-plugin/sustainable-catalyst-platform-core/sustainable-catalyst-platform-core.php >/dev/null; node --check backend/public_sdk/javascript/index.mjs; bash -n DEPLOY_PLATFORM_CORE_V2970_CONTABO.sh
git add -A; if git diff --cached --quiet; then echo "No repository changes need to be committed."; else git commit -m "Build Platform Core v2.97.0 Platform Research Integration Certification"; fi
git push origin main; head_commit="$(git rev-parse HEAD)"; git_file_sha="$(git show HEAD:backend/app/migrations.py | shasum -a 256 | awk '{print $1}')"; [ "$git_file_sha" = "$source_migration_sha" ] || { echo "STOP: committed migrations.py differs from frozen archive"; exit 1; }
git tag -a "$TAG" -m "Platform Core v2.97.0 Platform Research Integration Certification"; git push origin "$TAG"; tag_commit="$(git rev-list -n 1 "$TAG")"; [ "$tag_commit" = "$head_commit" ] || { echo "STOP: tag does not resolve to promoted HEAD"; exit 1; }
echo "PASS - archive migrations.py matches committed/tagged migrations.py"; echo "PASS - tag v2.97.0 resolves to exact promoted HEAD $head_commit"; echo "PASS - Platform Core v2.97.0 pushed successfully"
