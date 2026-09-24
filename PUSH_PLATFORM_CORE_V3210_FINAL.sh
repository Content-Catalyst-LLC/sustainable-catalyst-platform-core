#!/usr/bin/env bash
set -euo pipefail
ARCHIVE="${1:?usage: $0 /path/to/sustainable-catalyst-platform-core-v3.21.0-repository.zip}"
REPO="${SC_CORE_REPO:-$HOME/Downloads/sustainable-catalyst-platform-core}"
TAG=v3.21.0
TMP="$(mktemp -d)"; trap 'rm -rf "$TMP"' EXIT
unzip -q "$ARCHIVE" -d "$TMP"
SRC="$(find "$TMP" -maxdepth 1 -type d -name 'sustainable-catalyst-platform-core-v3.21.0' | head -1)"
[ -n "$SRC" ] || { echo 'STOP: archive root not found'; exit 1; }
python3 -S "$SRC/scripts/validate_v3210_release.py"
VENV="$TMP/v3210-venv"; python3 -m venv "$VENV"; "$VENV/bin/python" -m pip install --disable-pip-version-check -q -r "$SRC/backend/requirements.txt"
PYTHONPATH="$SRC/backend" "$VENV/bin/python" "$SRC/backend/scripts/validate_uncertainty_probabilistic_evidence_v3_21_0.py"
PYTHONPATH="$SRC/backend" "$VENV/bin/python" -m pytest -q "$SRC/backend/tests/test_uncertainty_probabilistic_evidence_v3210.py" "$SRC/backend/tests/test_analytical_result_provenance_v3200.py" "$SRC/backend/tests/test_statistical_reasoning_v3300.py"
cd "$REPO"; git fetch origin --tags; git checkout main; git pull --ff-only origin main
if git ls-remote --exit-code --tags origin "refs/tags/$TAG" >/dev/null 2>&1; then echo "STOP: remote tag $TAG already exists"; exit 1; fi
rsync -a --delete --exclude='.git/' "$SRC/" "$REPO/"
python3 -S scripts/validate_v3210_release.py
python3 -m compileall -q backend/app backend/scripts backend/tests
php -l wordpress-plugin/sustainable-catalyst-platform-core/sustainable-catalyst-platform-core.php >/dev/null
bash -n DEPLOY_PLATFORM_CORE_V3210_CONTABO.sh
git add -A
git diff --cached --quiet || git commit -m "Build Platform Core v3.21.0 Uncertainty & Probabilistic Evidence Integration"
git push origin main
git tag -a "$TAG" -m "Platform Core v3.21.0 Uncertainty & Probabilistic Evidence Integration"
git push origin "$TAG"
git log -1 --decorate --oneline
echo "PASS - Platform Core v3.21.0 pushed and tagged successfully"
