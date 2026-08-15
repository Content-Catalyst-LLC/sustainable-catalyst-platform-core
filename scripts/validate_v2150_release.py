from pathlib import Path
import json, zipfile
R=Path(__file__).resolve().parents[1]
def req(p):
    q=R/p; assert q.is_file(),p; return q
def has(p,text): assert text in req(p).read_text(),(p,text)
for p in ['backend/app/config.py','backend/app/models.py','backend/app/services/scale.py','backend/app/routers/scale.py','backend/app/routers/meta.py','backend/app/migrations.py','backend/tests/test_distributed_scale_v2150.py','backend/scripts/validate_scale_control_plane.py','deployment/platform-core-v2150.env.example','docs/DISTRIBUTED_PROCESSING_STORAGE_SCALE_V2150.md','schemas/scale-processing-job-v1.schema.json','RELEASE_NOTES_V2150.md','PLATFORM_CORE_V2150_INSTALL_AND_TEST.md','PLATFORM_CORE_V2150_DISTRIBUTED_SCALE_AUDIT.md','render.yaml','wordpress-plugin/sustainable-catalyst-platform-core/sustainable-catalyst-platform-core.php','backend/public_sdk/downloads/sc-platform-core-public-python-v2.15.0.zip','backend/public_sdk/downloads/sc-platform-core-public-javascript-v2.15.0.zip']:
    req(p)
has('backend/app/config.py','version: str = "2.15.0"'); has('backend/app/migrations.py','("0018",'); has('backend/app/main.py','scale.public_router'); has('backend/app/routers/meta.py','distributed_processing_storage_scale'); has('wordpress-plugin/sustainable-catalyst-platform-core/sustainable-catalyst-platform-core.php','Version: 2.15.0'); has('render.yaml','SC_CORE_SCALE_CONTROL_PLANE_ENABLED')
assert json.loads(req('backend/public_sdk/javascript/package.json').read_text())['version']=='2.15.0'
assert 'version = "2.15.0"' in req('backend/public_sdk/python/pyproject.toml').read_text()
for z in ['backend/public_sdk/downloads/sc-platform-core-public-python-v2.15.0.zip','backend/public_sdk/downloads/sc-platform-core-public-javascript-v2.15.0.zip']:
    with zipfile.ZipFile(req(z)) as f: assert f.testzip() is None
print('PASS - v2.15.0 release contract')
