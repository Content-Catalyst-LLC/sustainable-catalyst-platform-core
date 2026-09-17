from pathlib import Path
import json,zipfile
R=Path(__file__).resolve().parents[1]
def req(x): p=R/x; assert p.exists(),x; return p
def has(x,t): assert t in req(x).read_text(),(x,t)
for p in ['backend/app/config.py','backend/app/models.py','backend/app/services/observability.py','backend/app/routers/observability.py','backend/app/request_tracing.py','backend/app/migrations.py','backend/tests/test_observability_slo_v2180.py','backend/scripts/validate_observability_control_plane.py','deployment/platform-core-v2180.env.example','docs/OBSERVABILITY_SLO_PRODUCTION_OPERATIONS_V2180.md','RELEASE_NOTES_V2180.md','PLATFORM_CORE_V2180_INSTALL_AND_TEST.md','PLATFORM_CORE_V2180_OBSERVABILITY_AUDIT.md','render.yaml','wordpress-plugin/sustainable-catalyst-platform-core/sustainable-catalyst-platform-core.php','backend/public_sdk/downloads/sc-platform-core-public-python-v2.18.0.zip','backend/public_sdk/downloads/sc-platform-core-public-javascript-v2.18.0.zip']:
 req(p)
has('backend/app/config.py','version: str = "2.18.0"'); has('backend/app/migrations.py','("0021",'); has('backend/app/main.py','observability.public_router'); has('backend/app/routers/meta.py','observability_slo_production_operations'); has('wordpress-plugin/sustainable-catalyst-platform-core/sustainable-catalyst-platform-core.php','Version: 2.18.0'); has('render.yaml','SC_CORE_OBSERVABILITY_CONTROL_PLANE_ENABLED')
assert json.loads(req('backend/public_sdk/javascript/package.json').read_text())['version']=='2.18.0'
assert 'version = "2.18.0"' in req('backend/public_sdk/python/pyproject.toml').read_text()
for z in ['backend/public_sdk/downloads/sc-platform-core-public-python-v2.18.0.zip','backend/public_sdk/downloads/sc-platform-core-public-javascript-v2.18.0.zip']:
 with zipfile.ZipFile(req(z)) as f: assert f.testzip() is None
print('PASS - v2.18.0 release contract')
