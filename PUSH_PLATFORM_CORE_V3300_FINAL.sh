#!/usr/bin/env bash
set -euo pipefail
trap 'rc=$?; echo "ERROR: v3.3.0 promotion stopped at line $LINENO (exit $rc): $BASH_COMMAND" >&2; exit $rc' ERR
ARCHIVE="${1:?usage: $0 /path/to/sustainable-catalyst-platform-core-v3.3.0-repository.zip}"
REPO="${SC_CORE_REPO:-$HOME/Downloads/sustainable-catalyst-platform-core}"
TAG="v3.3.0"
[ -f "$ARCHIVE" ] || { echo "STOP: repository archive not found: $ARCHIVE"; exit 1; }
TMP="$(mktemp -d)"; trap 'rm -rf "$TMP"' EXIT
unzip -q "$ARCHIVE" -d "$TMP"
SRC="$(find "$TMP" -maxdepth 1 -type d -name 'sustainable-catalyst-platform-core-v3.3.0' | head -1)"
[ -n "$SRC" ] || { echo "STOP: archive root not found"; exit 1; }
python3 -S "$SRC/scripts/validate_v3300_release.py"
VENV="$TMP/v3300-venv"; python3 -m venv "$VENV"; "$VENV/bin/python" -m pip install --disable-pip-version-check -q -r "$SRC/backend/requirements.txt"
PYTHONPATH="$SRC/backend" "$VENV/bin/python" "$SRC/backend/scripts/validate_statistical_reasoning.py"
cd "$REPO"; git fetch origin --tags; git checkout main; git pull --ff-only origin main
git tag -l "$TAG" | grep -q . && { echo "STOP: local tag $TAG already exists"; exit 1; } || true
git ls-remote --exit-code --tags origin "refs/tags/$TAG" >/dev/null 2>&1 && { echo "STOP: remote tag $TAG already exists"; exit 1; } || true
rsync -a --delete --exclude='.git/' "$SRC/" "$REPO/"
python3 -S scripts/validate_v3300_release.py
PYTHONPATH="$REPO/backend" "$VENV/bin/python" backend/scripts/validate_statistical_reasoning.py
PYTHONPATH="$REPO/backend" "$VENV/bin/python" -u backend/scripts/run_v3300_release_tests.py
"$VENV/bin/python" -m compileall -q backend/app backend/scripts backend/tests backend/public_sdk/python
php -l wordpress-plugin/sustainable-catalyst-platform-core/sustainable-catalyst-platform-core.php >/dev/null
node --check backend/public_sdk/javascript/index.mjs
bash -n DEPLOY_PLATFORM_CORE_V3300_CONTABO.sh
python3 scripts/build_v3300_manifest.py
git add -A
if ! git diff --cached --quiet; then git commit -m "Build Platform Core v3.3.0 Statistical Reasoning Object Model"; fi
git push origin main
git tag -a "$TAG" -m "Platform Core v3.3.0 Statistical Reasoning Object Model"
git push origin "$TAG"
echo "PASS - Platform Core v3.3.0 pushed and tagged successfully"
