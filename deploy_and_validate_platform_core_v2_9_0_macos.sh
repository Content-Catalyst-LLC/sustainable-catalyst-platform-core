#!/usr/bin/env bash
set -euo pipefail

BUNDLE="${1:-sustainable-catalyst-platform-core-v2.9.0-release-bundle.zip}"
WORK="${TMPDIR:-/tmp}/sc-platform-core-v290-bundle"
for cmd in unzip shasum python3 bash php; do command -v "$cmd" >/dev/null 2>&1 || { echo "ERROR: Required command not found: $cmd"; exit 1; }; done
[ -f "$BUNDLE" ] || { echo "ERROR: Bundle not found: $BUNDLE"; exit 1; }
rm -rf "$WORK"; mkdir -p "$WORK"; unzip -q "$BUNDLE" -d "$WORK"; cd "$WORK"
[ -f SHA256SUMS.txt ] || { echo "ERROR: SHA256SUMS.txt missing"; exit 1; }
shasum -a 256 -c SHA256SUMS.txt
REPO_ZIP="sustainable-catalyst-platform-core-v2.9.0-repository.zip"
PLUGIN_ZIP="sustainable-catalyst-platform-core-v2.9.0-wordpress-plugin.zip"
unzip -t "$REPO_ZIP" >/dev/null; unzip -t "$PLUGIN_ZIP" >/dev/null
rm -rf repo-extract; mkdir repo-extract; unzip -q "$REPO_ZIP" -d repo-extract
ROOT="repo-extract/sustainable-catalyst-platform-core-v2.9.0"
[ -f "$ROOT/backend/app/main.py" ] || { echo "ERROR: repository root missing"; exit 1; }
cd "$ROOT"
python3 scripts/validate_v290_release.py
python3 - <<'PY'
from pathlib import Path
import hashlib,json
root=Path('.')
m=json.loads((root/'BUILD_MANIFEST.json').read_text())
assert m['release']=='2.9.0'
for item in m['files']:
    p=root/item['path']; assert p.is_file(), item['path']; assert hashlib.sha256(p.read_bytes()).hexdigest()==item['sha256'], item['path']
print(f"PASS - clean extraction manifest verified: {m['file_count']} files")
PY
find backend -type f -name '*.py' -print0 | xargs -0 python3 -m py_compile
php -l wordpress-plugin/sustainable-catalyst-platform-core/sustainable-catalyst-platform-core.php >/dev/null
bash -n PUSH_PLATFORM_CORE_V290_FINAL.sh
bash -n deploy_and_validate_platform_core_v2_9_0_macos.sh

if [ "${SC_CORE_BUNDLE_ONLY:-0}" = "1" ]; then echo "PASS - v2.9.0 bundle-only verification complete"; exit 0; fi
python3 -m venv backend/.venv
backend/.venv/bin/python -m pip install --upgrade pip >/dev/null
backend/.venv/bin/python -m pip install -r backend/requirements.txt >/dev/null
export PYTHONPATH="backend:backend/public_sdk/python"; export PYTEST_DISABLE_PLUGIN_AUTOLOAD=1
for group in \
  "backend/tests/test_entities.py backend/tests/test_evidence_ledger_v220.py backend/tests/test_gateway_v260.py backend/tests/test_graph.py" \
  "backend/tests/test_graph_engine_v210.py backend/tests/test_health.py backend/tests/test_import_and_foundations.py backend/tests/test_international_law_un_v271.py" \
  "backend/tests/test_live_data_gateway_v270.py" \
  "backend/tests/test_predicates.py backend/tests/test_public_api_v230.py" \
  "backend/tests/test_production_integration_v281.py" \
  "backend/tests/test_data_fabric_v280.py backend/tests/test_economics_connectors_v273.py" \
  "backend/tests/test_scientific_connectors_v272.py" \
  "backend/tests/test_signature_dossiers_v250.py" \
  "backend/tests/test_trust_center_v240.py" \
  "backend/tests/test_streaming_alerts_reliability_v290.py"; do backend/.venv/bin/python -m pytest -q $group; done
SMOKE_DB="$WORK/platform_core_v290_installer_smoke.db"; rm -f "$SMOKE_DB"
SC_CORE_DATABASE_URL="sqlite:///${SMOKE_DB}" SC_CORE_ENVIRONMENT=test backend/.venv/bin/python backend/scripts/migrate.py
SC_CORE_DATABASE_URL="sqlite:///${SMOKE_DB}" SC_CORE_ENVIRONMENT=test backend/.venv/bin/python backend/scripts/validate_streaming_reliability.py
SC_CORE_DATABASE_URL="sqlite:///${SMOKE_DB}" SC_CORE_ENVIRONMENT=test backend/.venv/bin/python backend/scripts/run_connector_worker.py --once
rm -f "$SMOKE_DB"
echo "PASS - v2.9.0 deterministic validation complete"
if [ "${SC_CORE_VALIDATE_ONLY:-0}" = "1" ]; then exit 0; fi
cd "$WORK"; chmod +x PUSH_PLATFORM_CORE_V290_FINAL.sh; ./PUSH_PLATFORM_CORE_V290_FINAL.sh "$WORK/$REPO_ZIP"
