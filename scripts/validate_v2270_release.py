from pathlib import Path
import json, re, zipfile
R=Path(__file__).resolve().parents[1]
def req(path):
    p=R/path
    assert p.is_file(), path
    return p
def has(path,text):
    assert text in req(path).read_text(), (path,text)

required=[
'backend/app/config.py','backend/app/models.py','backend/app/migrations.py','backend/app/routers/scientific_objects.py','backend/app/services/scientific_objects.py','backend/app/services/certification.py',
'backend/scripts/validate_scientific_object_storage.py','backend/tests/test_scientific_object_storage_processing_v2270.py',
'schemas/scientific-storage-backend-v1.schema.json','schemas/scientific-stored-object-v1.schema.json','schemas/scientific-processing-adapter-v1.schema.json','schemas/scientific-processing-run-v1.schema.json',
'docs/SCIENTIFIC_OBJECT_STORAGE_PROCESSING_ADAPTER_FABRIC_V2270.md','RELEASE_NOTES_V2270.md','PLATFORM_CORE_V2270_INSTALL_AND_TEST.md','PLATFORM_CORE_V2270_SCIENTIFIC_OBJECT_STORAGE_PROCESSING_ADAPTER_AUDIT.md','PLATFORM_CORE_V2270_TERMINAL_COMMANDS.txt','deployment/platform-core-v2270.env.example',
'render.yaml','wordpress-plugin/sustainable-catalyst-platform-core/sustainable-catalyst-platform-core.php',
'backend/public_sdk/downloads/sc-platform-core-public-python-v2.27.0.zip','backend/public_sdk/downloads/sc-platform-core-public-javascript-v2.27.0.zip',
'PUSH_PLATFORM_CORE_V2270_FINAL.sh','deploy_and_validate_platform_core_v2_27_0_macos.sh']
for path in required: req(path)

has('backend/app/config.py','version: str = "2.27.0"')
has('backend/app/migrations.py','("0030", "Scientific object storage backends')
has('backend/app/main.py','scientific_objects.public_router')
has('backend/app/routers/meta.py','"scientific_object_storage_processing_adapter_fabric"')
has('backend/app/routers/scientific_objects.py','/api/v1/scientific-objects')
has('backend/app/services/scientific_objects.py','ALLOWED_EXTERNAL_SCHEMES = {"https", "s3", "gs", "az"}')
has('backend/app/services/scientific_objects.py','"arbitrary_code_execution": False')
has('backend/app/services/scientific_objects.py','"external_fetch_by_core": False')
has('backend/app/services/scientific_objects.py','"credential_values_persisted": False')
has('backend/app/services/certification.py','scientific_object_storage_ready')
has('wordpress-plugin/sustainable-catalyst-platform-core/sustainable-catalyst-platform-core.php','Version: 2.27.0')
has('wordpress-plugin/sustainable-catalyst-platform-core/sustainable-catalyst-platform-core.php','sc_platform_core_scientific_object_storage_status')
has('render.yaml','SustainableCatalystPlatformCore/2.27.0')
has('render.yaml','SC_CORE_SCIENTIFIC_OBJECT_STORAGE_ENABLED')
has('render.yaml','SC_CORE_SCIENTIFIC_OBJECT_STORAGE_ROOT')
assert json.loads(req('backend/public_sdk/javascript/package.json').read_text())['version']=='2.27.0'
assert 'version = "2.27.0"' in req('backend/public_sdk/python/pyproject.toml').read_text()
assert req('README.md').read_text().startswith('# Sustainable Catalyst Platform Core v2.27.0')
has('docs/ROADMAP.md','## v2.27.0 — Scientific Object Storage & Processing Adapter Fabric')
has('docs/ROADMAP.md','Next planned: v2.28.0 — Research Object & Model Foundation.')

meta=req('backend/app/routers/meta.py').read_text()
implemented_block=meta.split('capabilities=[',1)[1].split('deferred_capabilities=[',1)[0]
deferred_block=meta.split('deferred_capabilities=[',1)[1].split(']',1)[0]
implemented=re.findall(r'"([a-z0-9_]+)"',implemented_block)
deferred=re.findall(r'"([a-z0-9_]+)"',deferred_block)
assert len(implemented)==len(set(implemented))
assert len(deferred)==len(set(deferred))
assert set(implemented).isdisjoint(deferred)
for cap in (
    'scientific_object_storage_processing_adapter_fabric','scientific_storage_backend_registry','scientific_local_object_store',
    'scientific_external_reference_store','scientific_object_integrity_hashing','scientific_derived_object_lineage',
    'scientific_processing_adapter_registry','scientific_processing_run_ledger','builtin_scientific_object_manifest_adapter',
    'credential_free_scientific_object_references','public_safe_scientific_object_metadata'):
    assert cap in implemented and cap not in deferred, cap
assert 'scientific_object_storage_adapter' not in deferred
for schema in (
    'schemas/scientific-storage-backend-v1.schema.json','schemas/scientific-stored-object-v1.schema.json',
    'schemas/scientific-processing-adapter-v1.schema.json','schemas/scientific-processing-run-v1.schema.json'):
    json.loads(req(schema).read_text())
for z in ('backend/public_sdk/downloads/sc-platform-core-public-python-v2.27.0.zip','backend/public_sdk/downloads/sc-platform-core-public-javascript-v2.27.0.zip'):
    with zipfile.ZipFile(req(z)) as a:
        assert a.testzip() is None
for script in ('PUSH_PLATFORM_CORE_V2270_FINAL.sh','deploy_and_validate_platform_core_v2_27_0_macos.sh'):
    text=req(script).read_text()
    assert 'v2.27.0' in text and 'v2270' in text and 'validate_scientific_object_storage.py' in text and 'scan_push_safe_secrets.py' in text
    assert 'python3.12' in text and 'python3.10' in text
print('PASS - v2.27.0 scientific object storage and processing adapter fabric release contract')
