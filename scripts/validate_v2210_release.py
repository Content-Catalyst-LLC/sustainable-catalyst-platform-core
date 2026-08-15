from pathlib import Path
import json,zipfile
R=Path(__file__).resolve().parents[1]
def req(x): p=R/x; assert p.exists(),x; return p
def has(x,t): assert t in req(x).read_text(),(x,t)
required=['backend/app/config.py','backend/app/models.py','backend/app/services/resilience.py','backend/app/routers/resilience.py','backend/app/migrations.py','backend/tests/test_multi_region_resilience_v2210.py','backend/scripts/validate_multi_region_resilience.py','deployment/platform-core-v2210.env.example','docs/MULTI_REGION_RESILIENCE_FAILOVER_COORDINATION_V2210.md','RELEASE_NOTES_V2210.md','PLATFORM_CORE_V2210_INSTALL_AND_TEST.md','PLATFORM_CORE_V2210_MULTI_REGION_RESILIENCE_AUDIT.md','PLATFORM_CORE_V2210_TERMINAL_COMMANDS.txt','schemas/region-service-status-v1.schema.json','schemas/failover-assessment-v1.schema.json','render.yaml','wordpress-plugin/sustainable-catalyst-platform-core/sustainable-catalyst-platform-core.php','backend/public_sdk/downloads/sc-platform-core-public-python-v2.21.0.zip','backend/public_sdk/downloads/sc-platform-core-public-javascript-v2.21.0.zip']
for x in required:req(x)
has('backend/app/config.py','version: str = "2.21.0"'); has('backend/app/migrations.py','("0024",'); has('backend/app/main.py','resilience.public_router'); has('backend/app/routers/meta.py','multi_region_resilience_failover_coordination'); has('backend/app/services/resilience.py','automatic_execution=False'); has('backend/app/services/resilience.py','write_failover_requires_replication_safety'); has('backend/app/services/certification.py','certification_require_multi_region_ready'); has('wordpress-plugin/sustainable-catalyst-platform-core/sustainable-catalyst-platform-core.php','Version: 2.21.0'); has('render.yaml','SC_CORE_MULTI_REGION_RESILIENCE_ENABLED')
assert json.loads(req('backend/public_sdk/javascript/package.json').read_text())['version']=='2.21.0'; assert 'version = "2.21.0"' in req('backend/public_sdk/python/pyproject.toml').read_text()
for z in ['backend/public_sdk/downloads/sc-platform-core-public-python-v2.21.0.zip','backend/public_sdk/downloads/sc-platform-core-public-javascript-v2.21.0.zip']:
    with zipfile.ZipFile(req(z)) as f: assert f.testzip() is None
for script in ['PUSH_PLATFORM_CORE_V2210_FINAL.sh','deploy_and_validate_platform_core_v2_21_0_macos.sh']:
    text=req(script).read_text(); assert 'v2.21.0' in text and 'v2_21_0' in text
print('PASS - v2.21.0 release contract')
