#!/usr/bin/env bash
set -euo pipefail

ORG="Content-Catalyst-LLC"
REPO="sustainable-catalyst-platform-core"
BRANCH="main"
REMOTE="git@github.com:${ORG}/${REPO}.git"

PACKAGE_ZIP="${1:-${HOME}/Downloads/sustainable-catalyst-platform-core-v2.8.1-repository.zip}"
WORKDIR="${2:-${HOME}/Downloads/sustainable-catalyst-platform-core-repo}"
EXTRACT_DIR="${TMPDIR:-/tmp}/sc-platform-core-v281-extracted"

printf '%s\n' \
  "============================================================" \
  "PLATFORM CORE v2.8.1 — PRODUCTION INTEGRATION & READINESS" \
  "============================================================" \
  "Package:    ${PACKAGE_ZIP}" \
  "Repository: ${WORKDIR}" \
  "Remote:     ${REMOTE}" \
  ""

for command_name in git unzip rsync grep find zip shasum; do
  command -v "$command_name" >/dev/null 2>&1 || {
    echo "ERROR: Required command not found: ${command_name}"
    exit 1
  }
done

if command -v python3.12 >/dev/null 2>&1; then
  PYTHON_BIN="$(command -v python3.12)"
else
  PYTHON_BIN="$(command -v python3)"
fi

[ -f "$PACKAGE_ZIP" ] || { echo "ERROR: Release ZIP not found: $PACKAGE_ZIP"; exit 1; }

rm -rf "$EXTRACT_DIR"
mkdir -p "$EXTRACT_DIR"
unzip -q "$PACKAGE_ZIP" -d "$EXTRACT_DIR"
SOURCE_ROOT="$(find "$EXTRACT_DIR" -maxdepth 1 -type d -name 'sustainable-catalyst-platform-core-v2.8.1' | head -1)"
[ -n "$SOURCE_ROOT" ] && [ -f "$SOURCE_ROOT/backend/app/main.py" ] || {
  echo "ERROR: Expected v2.8.1 repository root was not found."
  exit 1
}

if [ -d "$WORKDIR/.git" ]; then
  cd "$WORKDIR"
  git remote set-url origin "$REMOTE"
  if ! git diff --quiet || ! git diff --cached --quiet || [ -n "$(git ls-files --others --exclude-standard)" ]; then
    git stash push -u -m "Automatic safety stash before Platform Core v2.8.1" >/dev/null || true
  fi
  git fetch origin --prune
  git checkout "$BRANCH"
  git pull --ff-only origin "$BRANCH"
else
  rm -rf "$WORKDIR"
  git clone --branch "$BRANCH" "$REMOTE" "$WORKDIR"
fi

find "$WORKDIR" -type d -name '__pycache__' -prune -exec rm -rf {} + 2>/dev/null || true
rm -rf "$WORKDIR/backend/.venv" "$WORKDIR/.pytest_cache" "$WORKDIR/backend/.pytest_cache"

rsync -a --delete \
  --exclude='.git/' \
  --exclude='.venv/' \
  --exclude='.pytest_cache/' \
  --exclude='__pycache__/' \
  --exclude='*.db' \
  "$SOURCE_ROOT/" "$WORKDIR/"

cd "$WORKDIR"

echo "Validating v2.8.1 release contract..."
"$PYTHON_BIN" scripts/validate_v281_release.py

"$PYTHON_BIN" - <<'PY'
from pathlib import Path
import hashlib, json
root=Path('.')
manifest=json.loads((root/'BUILD_MANIFEST.json').read_text())
if manifest.get('release') != '2.8.1':
    raise SystemExit('ERROR: BUILD_MANIFEST.json release is not 2.8.1')
for item in manifest.get('files', []):
    path=root/item['path']
    if not path.is_file():
        raise SystemExit(f"ERROR: Manifest file missing: {path}")
    digest=hashlib.sha256(path.read_bytes()).hexdigest()
    if digest != item['sha256']:
        raise SystemExit(f"ERROR: Manifest hash mismatch: {path}")
print(f"PASS - Manifest verified across {manifest['file_count']} files")
PY

printf '%s\n' "Running push-safe secret scan..."
SECRET_HITS="$({
  grep -RInE \
    '(sk-proj-[A-Za-z0-9_-]{20,}|sk-[A-Za-z0-9_-]{30,}|AIza[0-9A-Za-z_-]{20,}|gh[opusr]_[A-Za-z0-9_]{20,}|Authorization:[[:space:]]*Bearer[[:space:]]+[A-Za-z0-9._-]{24,}|X-SC-Service-Token:[[:space:]]*[A-Za-z0-9._-]{20,})' \
    . \
    --exclude-dir=.git --exclude-dir=.venv --exclude-dir=.pytest_cache --exclude-dir=__pycache__ \
    --exclude='*.zip' --exclude='*.pyc' --exclude='.env.example' --exclude='platform-core-v281.env.example' \
    --exclude='PUSH_PLATFORM_CORE_V*_FINAL*.sh' || true
} | grep -viE '(placeholder|replace[-_ ]?me|change[-_ ]?me|DEMO_KEY|test-secret|secret-token|hidden)' || true)"
if [ -n "$SECRET_HITS" ]; then
  printf '%s\n' "$SECRET_HITS"
  echo "ERROR: Potential secret found. Nothing was pushed."
  exit 1
fi

echo "Running syntax checks..."
find backend -type f -name '*.py' -not -path '*/.venv/*' -print0 | xargs -0 "$PYTHON_BIN" -m py_compile
php -l wordpress-plugin/sustainable-catalyst-platform-core/sustainable-catalyst-platform-core.php >/dev/null
bash -n PUSH_PLATFORM_CORE_V281_FINAL.sh
bash -n deploy_and_validate_platform_core_v2_8_1_macos.sh

"$PYTHON_BIN" -m venv backend/.venv
backend/.venv/bin/python -m pip install --upgrade pip >/dev/null
backend/.venv/bin/python -m pip install -r backend/requirements.txt >/dev/null

export PYTHONPATH="backend:backend/public_sdk/python"
export PYTEST_DISABLE_PLUGIN_AUTOLOAD=1
for group in \
  "backend/tests/test_entities.py backend/tests/test_evidence_ledger_v220.py backend/tests/test_gateway_v260.py backend/tests/test_graph.py" \
  "backend/tests/test_graph_engine_v210.py backend/tests/test_health.py backend/tests/test_import_and_foundations.py backend/tests/test_international_law_un_v271.py" \
  "backend/tests/test_live_data_gateway_v270.py" \
  "backend/tests/test_predicates.py backend/tests/test_public_api_v230.py" \
  "backend/tests/test_production_integration_v281.py" \
  "backend/tests/test_data_fabric_v280.py backend/tests/test_economics_connectors_v273.py" \
  "backend/tests/test_scientific_connectors_v272.py" \
  "backend/tests/test_signature_dossiers_v250.py" \
  "backend/tests/test_trust_center_v240.py"; do
  backend/.venv/bin/python -m pytest -q $group
done

SMOKE_DB="$WORKDIR/backend/platform_core_v281_push_smoke.db"
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
  zip -qr ../dist/sustainable-catalyst-platform-core-plugin-v2.8.1.zip sustainable-catalyst-platform-core
)
cp backend/public_sdk/downloads/sc-platform-core-public-python-v2.8.1.zip dist/
cp backend/public_sdk/downloads/sc-platform-core-public-javascript-v2.8.1.zip dist/
cp backend/public_sdk/postman/Sustainable_Catalyst_Public_API_v1.postman_collection.json dist/

git add -A
if git diff --cached --quiet; then
  echo "No repository changes need to be committed."
else
  git commit -m "Build Platform Core v2.8.1 production integration and readiness repair"
fi

git push --set-upstream origin "$BRANCH"

printf '%s\n' \
  "" \
  "============================================================" \
  "PLATFORM CORE v2.8.1 PUSHED SUCCESSFULLY" \
  "============================================================" \
  "Repository: https://github.com/${ORG}/${REPO}" \
  "Local path: ${WORKDIR}" \
  ""

if [ -n "${SC_CORE_PUBLIC_BASE_URL:-}" ]; then
  echo "Checking live Core endpoints at ${SC_CORE_PUBLIC_BASE_URL} ..."
  curl -fsS "${SC_CORE_PUBLIC_BASE_URL%/}/health" >/dev/null
  curl -fsS "${SC_CORE_PUBLIC_BASE_URL%/}/ready" | "$PYTHON_BIN" -c 'import json,sys; d=json.load(sys.stdin); assert d.get("ok") is True, d; print("PASS - live /ready")'
  curl -fsS "${SC_CORE_PUBLIC_BASE_URL%/}/integration/readiness" | "$PYTHON_BIN" -c 'import json,sys; d=json.load(sys.stdin); assert d.get("ok") is True, d; print("PASS - live integration readiness")'
else
  echo "Live verification skipped: export SC_CORE_PUBLIC_BASE_URL to enable it."
fi
