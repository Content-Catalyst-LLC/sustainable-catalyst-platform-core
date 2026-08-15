from pathlib import Path
import json,zipfile
R=Path(__file__).resolve().parents[1]
def req(x): p=R/x; assert p.exists(),x; return p
def has(x,t): assert t in req(x).read_text(),(x,t)
for p in ['backend/app/config.py','backend/app/models.py','backend/app/services/certification.py','backend/app/routers/certification.py','backend/app/routers/meta.py','backend/app/migrations.py','backend/tests/test_production_certification_v2170.py','backend/scripts/validate_production_certification.py','deployment/platform-core-v2170.env.example','docs/PRODUCTION_CERTIFICATION_MIGRATION_RECOVERY_V2170.md','RELEASE_NOTES_V2170.md','PLATFORM_CORE_V2170_INSTALL_AND_TEST.md','PLATFORM_CORE_V2170_PRODUCTION_CERTIFICATION_AUDIT.md','render.yaml','wordpress-plugin/sustainable-catalyst-platform-core/sustainable-catalyst-platform-core.php','backend/public_sdk/downloads/sc-platform-core-public-python-v2.17.0.zip','backend/public_sdk/downloads/sc-platform-core-public-javascript-v2.17.0.zip']:
 req(p)
has('backend/app/config.py','version: str = "2.17.0"'); has('backend/app/migrations.py','("0020",'); has('backend/app/main.py','certification.public_router'); has('backend/app/routers/meta.py','production_certification_migration_recovery'); has('wordpress-plugin/sustainable-catalyst-platform-core/sustainable-catalyst-platform-core.php','Version: 2.17.0'); has('render.yaml','SC_CORE_PRODUCTION_CERTIFICATION_ENABLED')
assert json.loads(req('backend/public_sdk/javascript/package.json').read_text())['version']=='2.17.0'
assert 'version = "2.17.0"' in req('backend/public_sdk/python/pyproject.toml').read_text()
for z in ['backend/public_sdk/downloads/sc-platform-core-public-python-v2.17.0.zip','backend/public_sdk/downloads/sc-platform-core-public-javascript-v2.17.0.zip']:
 with zipfile.ZipFile(req(z)) as f: assert f.testzip() is None
print('PASS - v2.17.0 release contract')
