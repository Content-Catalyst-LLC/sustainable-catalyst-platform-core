
from pathlib import Path
import json,zipfile
R=Path(__file__).resolve().parents[1]
def req(p): q=R/p; assert q.is_file(),p; return q
def has(p,t): assert t in req(p).read_text(),(p,t)
required=['backend/app/config.py','backend/app/models.py','backend/app/services/lifecycle.py','backend/app/routers/lifecycle.py','backend/app/migrations.py','backend/tests/test_data_lifecycle_preservation_v2220.py','backend/scripts/validate_data_lifecycle_preservation.py','deployment/platform-core-v2220.env.example','docs/DATA_LIFECYCLE_ARCHIVAL_INTEGRITY_PRESERVATION_V2220.md','RELEASE_NOTES_V2220.md','PLATFORM_CORE_V2220_INSTALL_AND_TEST.md','PLATFORM_CORE_V2220_DATA_LIFECYCLE_PRESERVATION_AUDIT.md','PLATFORM_CORE_V2220_TERMINAL_COMMANDS.txt','schemas/data-lifecycle-policy-v1.schema.json','schemas/preservation-archive-v1.schema.json','render.yaml','wordpress-plugin/sustainable-catalyst-platform-core/sustainable-catalyst-platform-core.php','backend/public_sdk/downloads/sc-platform-core-public-python-v2.22.0.zip','backend/public_sdk/downloads/sc-platform-core-public-javascript-v2.22.0.zip']
for x in required:req(x)
has('backend/app/config.py','version: str = "2.22.0"'); has('backend/app/migrations.py','("0025",'); has('backend/app/main.py','lifecycle.public_router'); has('backend/app/routers/meta.py','data_lifecycle_archival_integrity_preservation'); has('backend/app/services/lifecycle.py','hard_delete_enabled'); has('backend/app/services/lifecycle.py','automatic_source_overwrite'); has('backend/app/services/certification.py','certification_require_preservation_ready'); has('wordpress-plugin/sustainable-catalyst-platform-core/sustainable-catalyst-platform-core.php','Version: 2.22.0'); has('render.yaml','SC_CORE_DATA_LIFECYCLE_PRESERVATION_ENABLED')
assert json.loads(req('backend/public_sdk/javascript/package.json').read_text())['version']=='2.22.0'; assert 'version = "2.22.0"' in req('backend/public_sdk/python/pyproject.toml').read_text()
for z in ['backend/public_sdk/downloads/sc-platform-core-public-python-v2.22.0.zip','backend/public_sdk/downloads/sc-platform-core-public-javascript-v2.22.0.zip']:
    with zipfile.ZipFile(req(z)) as f: assert f.testzip() is None
for script in ['PUSH_PLATFORM_CORE_V2220_FINAL.sh','deploy_and_validate_platform_core_v2_22_0_macos.sh']:
    text=req(script).read_text(); assert 'v2.22.0' in text and 'v2_22_0' in text
print('PASS - v2.22.0 release contract')
