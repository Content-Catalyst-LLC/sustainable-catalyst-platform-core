#!/usr/bin/env bash
set -euo pipefail
ORG="Content-Catalyst-LLC"; REPO="sustainable-catalyst-platform-core"; BRANCH="main"; REMOTE="git@github.com:${ORG}/${REPO}.git"
PACKAGE_ZIP="${1:-${HOME}/Downloads/sustainable-catalyst-platform-core-v2.13.0-repository.zip}"
WORKDIR="${2:-${HOME}/Downloads/sustainable-catalyst-platform-core-repo}"
EXTRACT_DIR="${TMPDIR:-/tmp}/sc-platform-core-v2130-extracted"
printf '%s\n' "============================================================" "PLATFORM CORE v2.13.0 — EARTH, OCEAN, SPACE & SCIENTIFIC SERVICE FABRIC" "============================================================" "Package:    ${PACKAGE_ZIP}" "Repository: ${WORKDIR}" "Remote:     ${REMOTE}" ""
for command_name in git unzip rsync grep find zip shasum php bash; do command -v "$command_name" >/dev/null 2>&1 || { echo "ERROR: Required command not found: ${command_name}"; exit 1; }; done
if command -v python3.12 >/dev/null 2>&1; then PYTHON_BIN="$(command -v python3.12)"; else PYTHON_BIN="$(command -v python3)"; fi
[ -f "$PACKAGE_ZIP" ] || { echo "ERROR: Release ZIP not found: $PACKAGE_ZIP"; exit 1; }
rm -rf "$EXTRACT_DIR"; mkdir -p "$EXTRACT_DIR"; unzip -q "$PACKAGE_ZIP" -d "$EXTRACT_DIR"
SOURCE_ROOT="$(find "$EXTRACT_DIR" -maxdepth 1 -type d -name 'sustainable-catalyst-platform-core-v2.13.0' | head -1)"
[ -n "$SOURCE_ROOT" ] && [ -f "$SOURCE_ROOT/backend/app/main.py" ] || { echo "ERROR: Expected v2.13.0 repository root was not found."; exit 1; }
if [ -d "$WORKDIR/.git" ]; then
  cd "$WORKDIR"; git remote set-url origin "$REMOTE"
  if ! git diff --quiet || ! git diff --cached --quiet || [ -n "$(git ls-files --others --exclude-standard)" ]; then git stash push -u -m "Automatic safety stash before Platform Core v2.13.0" >/dev/null || true; fi
  git fetch origin --prune; git checkout "$BRANCH"; git pull --ff-only origin "$BRANCH"
else
  rm -rf "$WORKDIR"; git clone --branch "$BRANCH" "$REMOTE" "$WORKDIR"
fi
find "$WORKDIR" -type d -name '__pycache__' -prune -exec rm -rf {} + 2>/dev/null || true
rm -rf "$WORKDIR/backend/.venv" "$WORKDIR/.pytest_cache" "$WORKDIR/backend/.pytest_cache"
rsync -a --delete --exclude='.git/' --exclude='.venv/' --exclude='.pytest_cache/' --exclude='__pycache__/' --exclude='*.db' "$SOURCE_ROOT/" "$WORKDIR/"
cd "$WORKDIR"
"$PYTHON_BIN" scripts/validate_v2130_release.py
"$PYTHON_BIN" - <<'PY'
from pathlib import Path
import hashlib,json
root=Path('.'); m=json.loads((root/'BUILD_MANIFEST.json').read_text()); assert m.get('release')=='2.13.0',m.get('release')
for item in m.get('files',[]):
    p=root/item['path']
    if not p.is_file(): raise SystemExit(f"ERROR: Manifest file missing: {p}")
    if hashlib.sha256(p.read_bytes()).hexdigest()!=item['sha256']: raise SystemExit(f"ERROR: Manifest hash mismatch: {p}")
print(f"PASS - Manifest verified across {m['file_count']} files")
PY
SECRET_HITS="$({ grep -RInE '(sk-proj-[A-Za-z0-9_-]{20,}|sk-[A-Za-z0-9_-]{30,}|AIza[0-9A-Za-z_-]{20,}|gh[opusr]_[A-Za-z0-9_]{20,}|Authorization:[[:space:]]*Bearer[[:space:]]+[A-Za-z0-9._-]{24,}|X-SC-Service-Token:[[:space:]]*[A-Za-z0-9._-]{20,})' . --exclude-dir=.git --exclude-dir=.venv --exclude-dir=.pytest_cache --exclude-dir=__pycache__ --exclude='*.zip' --exclude='*.pyc' --exclude='.env.example' --exclude='platform-core-v2130.env.example' --exclude='PUSH_PLATFORM_CORE_V*_FINAL*.sh' || true; } | grep -viE '(placeholder|replace[-_ ]?me|change[-_ ]?me|DEMO_KEY|test-secret|secret-token|hidden)' || true)"
if [ -n "$SECRET_HITS" ]; then printf '%s\n' "$SECRET_HITS"; echo "ERROR: Potential secret found. Nothing was pushed."; exit 1; fi
find backend -type f -name '*.py' -not -path '*/.venv/*' -print0 | xargs -0 "$PYTHON_BIN" -m py_compile
php -l wordpress-plugin/sustainable-catalyst-platform-core/sustainable-catalyst-platform-core.php >/dev/null
bash -n PUSH_PLATFORM_CORE_V2130_FINAL.sh; bash -n deploy_and_validate_platform_core_v2_13_0_macos.sh
"$PYTHON_BIN" -m venv backend/.venv; backend/.venv/bin/python -m pip install --upgrade pip >/dev/null; backend/.venv/bin/python -m pip install -r backend/requirements.txt >/dev/null
export PYTHONPATH="backend:backend/public_sdk/python" PYTEST_DISABLE_PLUGIN_AUTOLOAD=1
for f in backend/tests/test_*.py; do backend/.venv/bin/python -m pytest -q "$f"; done
SMOKE_DB="$WORKDIR/backend/platform_core_v2130_push_smoke.db"; rm -f "$SMOKE_DB"
SC_CORE_DATABASE_URL="sqlite:///${SMOKE_DB}" SC_CORE_ENVIRONMENT=test backend/.venv/bin/python backend/scripts/migrate.py
SC_CORE_DATABASE_URL="sqlite:///${SMOKE_DB}" SC_CORE_ENVIRONMENT=test backend/.venv/bin/python backend/scripts/validate_streaming_reliability.py
SC_CORE_DATABASE_URL="sqlite:///${SMOKE_DB}" SC_CORE_ENVIRONMENT=test backend/.venv/bin/python backend/scripts/validate_operational_facilities.py
SC_CORE_DATABASE_URL="sqlite:///${SMOKE_DB}" SC_CORE_ENVIRONMENT=test backend/.venv/bin/python backend/scripts/validate_humanitarian_access.py
SC_CORE_DATABASE_URL="sqlite:///${SMOKE_DB}" SC_CORE_ENVIRONMENT=test backend/.venv/bin/python backend/scripts/validate_country_evidence.py
SC_CORE_DATABASE_URL="sqlite:///${SMOKE_DB}" SC_CORE_ENVIRONMENT=test backend/.venv/bin/python backend/scripts/validate_scientific_service_fabric.py
SC_CORE_DATABASE_URL="sqlite:///${SMOKE_DB}" SC_CORE_ENVIRONMENT=test backend/.venv/bin/python backend/scripts/run_connector_worker.py --once
rm -f "$SMOKE_DB"
mkdir -p dist
(cd wordpress-plugin && zip -qr ../dist/sustainable-catalyst-platform-core-plugin-v2.13.0.zip sustainable-catalyst-platform-core)
cp backend/public_sdk/downloads/sc-platform-core-public-python-v2.13.0.zip dist/
cp backend/public_sdk/downloads/sc-platform-core-public-javascript-v2.13.0.zip dist/
cp backend/public_sdk/postman/Sustainable_Catalyst_Public_API_v1.postman_collection.json dist/
git add -A
if git diff --cached --quiet; then echo "No repository changes need to be committed."; else git commit -m "Build Platform Core v2.13.0 Earth Ocean Space scientific service fabric"; fi
git push --set-upstream origin "$BRANCH"
echo "PASS - Platform Core v2.13.0 pushed successfully"
if [ -n "${SC_CORE_PUBLIC_BASE_URL:-}" ]; then
  curl -fsS "${SC_CORE_PUBLIC_BASE_URL%/}/health" | "$PYTHON_BIN" -c 'import json,sys; d=json.load(sys.stdin); assert d.get("version")=="2.13.0",d; print("PASS - live /health")'
  curl -fsS "${SC_CORE_PUBLIC_BASE_URL%/}/ready" | "$PYTHON_BIN" -c 'import json,sys; d=json.load(sys.stdin); assert d.get("ok") is True,d; assert d.get("earth_ocean_space_scientific_service_fabric")=="ready",d; print("PASS - live /ready")'
  curl -fsS -H "X-SC-API-Key: ${SC_CORE_WRITE_API_KEY:-}" "${SC_CORE_PUBLIC_BASE_URL%/}/v1/scientific-fabric/readiness" | "$PYTHON_BIN" -c 'import json,sys; d=json.load(sys.stdin); assert d.get("release")=="2.13.0",d; assert d.get("status")=="ready",d; assert d.get("truth_precedence")=="none",d; print("PASS - live scientific fabric readiness")'
else
  echo "Live verification skipped: export SC_CORE_PUBLIC_BASE_URL to enable it."
fi
