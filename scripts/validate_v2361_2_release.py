#!/usr/bin/env python3
from pathlib import Path
import json
from importlib.util import spec_from_file_location, module_from_spec
ROOT=Path(__file__).resolve().parents[1]
def req(path):
    p=ROOT/path; assert p.is_file(),f"missing required file: {path}"; return p
def has(path,text): assert text in req(path).read_text(errors='replace'),f"{path} missing: {text}"
for path in [
 'RELEASE_NOTES_V2361_2.md','PLATFORM_CORE_V2361_2_INSTALL_AND_TEST.md','PLATFORM_CORE_V2361_2_MIGRATION_METADATA_REPAIR_AUDIT.md',
 'PLATFORM_CORE_V2361_2_TERMINAL_COMMANDS.txt','backend/app/services/uncertainty_compute.py','backend/app/routers/uncertainty_compute.py',
 'backend/tests/test_uncertainty_compute_runtime_v2361_1.py','backend/tests/test_uncertainty_compute_schema_compatibility_v2361_1.py',
 'backend/tests/test_migration_metadata_length_v2361_2.py','backend/tests/test_partial_0040_recovery_v2361_2.py','backend/scripts/validate_uncertainty_compute.py',
 'deploy_and_validate_platform_core_v2_36_1_2_macos.sh','PUSH_PLATFORM_CORE_V2361_2_FINAL.sh','DEPLOY_PLATFORM_CORE_V2361_2_CONTABO.sh',
 'platform-core-v2361-2.env.example','backend/public_sdk/downloads/sc-platform-core-public-python-v2.36.1.2.zip',
 'backend/public_sdk/downloads/sc-platform-core-public-javascript-v2.36.1.2.zip']:
    req(path)
has('backend/app/config.py','version: str = "2.36.1.2"')
has('backend/app/migrations.py','("0040", "Reproducible uncertainty compute runtime with Monte Carlo/LHS sampling')
has('backend/app/models.py','class UncertaintyComputeRunRecord(Base):')
has('backend/app/models.py','ForeignKey("sensitivity_studies.id"')
has('backend/app/models.py','ForeignKey("ensembles.id"')
has('backend/app/models.py','class SensitivityMeasureRecord(Base):')
assert 'class SensitivityResultRecord(Base):' not in req('backend/app/models.py').read_text(), 'incompatible v2.36.1 sensitivity_results model still present'
assert not (ROOT/'schemas/sensitivity-result-v1.schema.json').exists(), 'incompatible sensitivity-result schema must not ship'
has('backend/app/main.py','uncertainty_compute.router')
has('backend/app/routers/meta.py','"uncertainty_compute_runtime_integration"')
has('wordpress-plugin/sustainable-catalyst-platform-core/sustainable-catalyst-platform-core.php','Version: 2.36.1.2')
has('wordpress-plugin/sustainable-catalyst-platform-core/sustainable-catalyst-platform-core.php','sc_platform_core_uncertainty_compute_status')
has('backend/public_sdk/javascript/package.json','"version": "2.36.1.2"')
has('backend/public_sdk/javascript/index.mjs','uncertaintyComputeReadiness()')
has('backend/public_sdk/python/pyproject.toml','version = "2.36.1.2"')
has('backend/public_sdk/python/sc_platform_core_public/client.py','uncertainty_compute_readiness')
has('backend/app/routers/developer_portal.py','sc-platform-core-public-python-v2.36.1.2.zip')
has('docs/ROADMAP.md','v2.42.0 — Forensic Object Model & Evidence Provenance')
# Enforce the production migration metadata storage contract without importing the full app.
text=req('backend/app/migrations.py').read_text()
import ast
module=ast.parse(text)
migrations=None
for node in module.body:
    if isinstance(node,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='MIGRATIONS' for t in node.targets):
        migrations=ast.literal_eval(node.value);break
assert migrations is not None
violations=[(v,len(d)) for v,d in migrations if len(d)>300]
assert not violations,f'migration descriptions exceed VARCHAR(300): {violations}'
assert len(dict(migrations)['0040'])==239
for name in ['uncertainty-compute-run-v1.schema.json','uncertainty-sampling-design-v1.schema.json','uncertainty-runtime-handoff-v1.schema.json']:
    doc=json.loads(req('schemas/'+name).read_text()); assert doc['type']=='object',name
print('PASS - v2.36.1.2 migration metadata length repair release contract')
