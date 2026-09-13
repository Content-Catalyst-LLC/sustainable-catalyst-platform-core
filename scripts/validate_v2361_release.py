#!/usr/bin/env python3
from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[1]
def req(path):
    p=ROOT/path; assert p.is_file(),f'missing required file: {path}'; return p
def has(path,text): assert text in req(path).read_text(errors='replace'),f'{path} missing: {text}'
for path in [
 'RELEASE_NOTES_V2361.md','PLATFORM_CORE_V2361_INSTALL_AND_TEST.md','PLATFORM_CORE_V2361_UNCERTAINTY_COMPUTE_RUNTIME_AUDIT.md',
 'docs/UNCERTAINTY_COMPUTE_RUNTIME_V2361.md','backend/app/services/uncertainty_compute.py','backend/app/routers/uncertainty_compute.py',
 'backend/tests/test_uncertainty_compute_runtime_v2361.py','backend/scripts/validate_uncertainty_compute.py',
 'deploy_and_validate_platform_core_v2_36_1_macos.sh','PUSH_PLATFORM_CORE_V2361_FINAL.sh','DEPLOY_PLATFORM_CORE_V2361_CONTABO.sh',
 'platform-core-v2361.env.example','backend/public_sdk/downloads/sc-platform-core-public-python-v2.36.1.zip',
 'backend/public_sdk/downloads/sc-platform-core-public-javascript-v2.36.1.zip']:
    req(path)
has('backend/app/config.py','version: str = "2.36.1"')
has('backend/app/migrations.py','("0040", "Reproducible uncertainty compute runtime integration')
has('backend/app/models.py','class UncertaintyComputeRunRecord(Base):')
has('backend/app/main.py','uncertainty_compute.router')
has('backend/app/routers/meta.py','"uncertainty_compute_runtime_integration"')
has('wordpress-plugin/sustainable-catalyst-platform-core/sustainable-catalyst-platform-core.php','Version: 2.36.1')
has('wordpress-plugin/sustainable-catalyst-platform-core/sustainable-catalyst-platform-core.php','sc_platform_core_uncertainty_compute_status')
has('wordpress-plugin/sustainable-catalyst-platform-core/readme.txt','Stable tag: 2.36.1')
has('backend/public_sdk/javascript/package.json','"version": "2.36.1"')
has('backend/public_sdk/javascript/index.mjs','uncertaintyComputeReadiness()')
has('backend/public_sdk/python/pyproject.toml','version = "2.36.1"')
has('backend/public_sdk/python/sc_platform_core_public/client.py','uncertainty_compute_readiness')
has('backend/app/routers/developer_portal.py','sc-platform-core-public-python-v2.36.1.zip')
has('backend/app/routers/developer_portal.py','sc-platform-core-public-javascript-v2.36.1.zip')
has('docs/ROADMAP.md','v2.42.0 — Forensic Object Model & Evidence Provenance')
for name in ['uncertainty-compute-run-v1.schema.json','uncertainty-sampling-design-v1.schema.json','uncertainty-runtime-handoff-v1.schema.json']:
    doc=json.loads(req('schemas/'+name).read_text()); assert doc['type']=='object',name
print('PASS - v2.36.1 Uncertainty Compute Runtime Integration release contract')
