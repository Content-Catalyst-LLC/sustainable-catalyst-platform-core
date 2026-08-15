from pathlib import Path
import json,zipfile
R=Path(__file__).resolve().parents[1]
def req(x): p=R/x; assert p.exists(),x; return p
def has(x,t): assert t in req(x).read_text(),(x,t)
required=[
'backend/app/config.py','backend/app/models.py','backend/app/services/operations.py','backend/app/routers/operations.py','backend/app/migrations.py','backend/tests/test_incident_change_control_v2190.py','backend/scripts/validate_incident_change_control.py','deployment/platform-core-v2190.env.example','docs/INCIDENT_RESPONSE_CHANGE_CONTROL_ROLLBACK_V2190.md','RELEASE_NOTES_V2190.md','PLATFORM_CORE_V2190_INSTALL_AND_TEST.md','PLATFORM_CORE_V2190_INCIDENT_CHANGE_ROLLBACK_AUDIT.md','PLATFORM_CORE_V2190_TERMINAL_COMMANDS.txt','schemas/operations-incident-v1.schema.json','schemas/change-control-v1.schema.json','render.yaml','wordpress-plugin/sustainable-catalyst-platform-core/sustainable-catalyst-platform-core.php','backend/public_sdk/downloads/sc-platform-core-public-python-v2.19.0.zip','backend/public_sdk/downloads/sc-platform-core-public-javascript-v2.19.0.zip']
for x in required: req(x)
has('backend/app/config.py','version: str = "2.19.0"')
has('backend/app/migrations.py','("0022",')
has('backend/app/main.py','operations.public_router')
has('backend/app/routers/meta.py','incident_response_change_control_rollback')
has('backend/app/services/certification.py','SCHEMA_HEAD=MIGRATIONS[-1][0]')
has('backend/app/services/operations.py','automatic_execution=False')
has('backend/app/services/operations.py','causal_attribution=False')
has('wordpress-plugin/sustainable-catalyst-platform-core/sustainable-catalyst-platform-core.php','Version: 2.19.0')
has('render.yaml','SC_CORE_INCIDENT_CHANGE_CONTROL_ENABLED')
assert json.loads(req('backend/public_sdk/javascript/package.json').read_text())['version']=='2.19.0'
assert 'version = "2.19.0"' in req('backend/public_sdk/python/pyproject.toml').read_text()
for z in ['backend/public_sdk/downloads/sc-platform-core-public-python-v2.19.0.zip','backend/public_sdk/downloads/sc-platform-core-public-javascript-v2.19.0.zip']:
    with zipfile.ZipFile(req(z)) as f: assert f.testzip() is None
# Promotion-lineage guard: current scripts must name v2.19 artifacts, never the prior installer.
for script in ['PUSH_PLATFORM_CORE_V2190_FINAL.sh','deploy_and_validate_platform_core_v2_19_0_macos.sh']:
    if (R/script).exists():
        text=(R/script).read_text(); assert 'v2.19.0' in text and 'v2_19_0' in text
print('PASS - v2.19.0 release contract')
