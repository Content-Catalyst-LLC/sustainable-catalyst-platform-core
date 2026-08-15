from pathlib import Path
import json,zipfile
R=Path(__file__).resolve().parents[1]
def req(p): q=R/p; assert q.is_file(),p; return q
def has(p,text): assert text in req(p).read_text(),(p,text)
for p in ['backend/app/config.py','backend/app/models.py','backend/app/services/governance.py','backend/app/routers/governance.py','backend/app/routers/meta.py','backend/app/migrations.py','backend/tests/test_governance_access_audit_v2160.py','backend/scripts/validate_governance_control_plane.py','deployment/platform-core-v2160.env.example','docs/GOVERNANCE_ACCESS_AUDIT_CONTROL_PLANE_V2160.md','schemas/governance-policy-v1.schema.json','schemas/governance-decision-v1.schema.json','schemas/governance-audit-event-v1.schema.json','RELEASE_NOTES_V2160.md','PLATFORM_CORE_V2160_INSTALL_AND_TEST.md','PLATFORM_CORE_V2160_GOVERNANCE_AUDIT.md','render.yaml','wordpress-plugin/sustainable-catalyst-platform-core/sustainable-catalyst-platform-core.php','backend/public_sdk/downloads/sc-platform-core-public-python-v2.16.0.zip','backend/public_sdk/downloads/sc-platform-core-public-javascript-v2.16.0.zip']:
 req(p)
has('backend/app/config.py','version: str = "2.16.0"'); has('backend/app/migrations.py','("0019",'); has('backend/app/main.py','governance.public_router'); has('backend/app/routers/meta.py','governance_access_audit_control_plane'); has('wordpress-plugin/sustainable-catalyst-platform-core/sustainable-catalyst-platform-core.php','Version: 2.16.0'); has('render.yaml','SC_CORE_GOVERNANCE_CONTROL_PLANE_ENABLED')
assert json.loads(req('backend/public_sdk/javascript/package.json').read_text())['version']=='2.16.0'
assert 'version = "2.16.0"' in req('backend/public_sdk/python/pyproject.toml').read_text()
for z in ['backend/public_sdk/downloads/sc-platform-core-public-python-v2.16.0.zip','backend/public_sdk/downloads/sc-platform-core-public-javascript-v2.16.0.zip']:
 with zipfile.ZipFile(req(z)) as f: assert f.testzip() is None
print('PASS - v2.16.0 release contract')
