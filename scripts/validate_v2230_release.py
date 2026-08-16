from pathlib import Path
import json,zipfile
R=Path(__file__).resolve().parents[1]
def req(p): q=R/p; assert q.is_file(),p; return q
def has(p,t): assert t in req(p).read_text(),(p,t)
required=['backend/app/config.py','backend/app/models.py','backend/app/services/federation.py','backend/app/routers/federation.py','backend/app/migrations.py','backend/tests/test_federated_core_trusted_node_exchange_v2230.py','backend/scripts/validate_federated_core_exchange.py','deployment/platform-core-v2230.env.example','docs/FEDERATED_CORE_TRUSTED_NODE_EXCHANGE_V2230.md','RELEASE_NOTES_V2230.md','PLATFORM_CORE_V2230_INSTALL_AND_TEST.md','PLATFORM_CORE_V2230_FEDERATED_CORE_AUDIT.md','PLATFORM_CORE_V2230_TERMINAL_COMMANDS.txt','schemas/federation-node-v1.schema.json','schemas/federation-exchange-manifest-v1.schema.json','render.yaml','wordpress-plugin/sustainable-catalyst-platform-core/sustainable-catalyst-platform-core.php','backend/public_sdk/downloads/sc-platform-core-public-python-v2.23.0.zip','backend/public_sdk/downloads/sc-platform-core-public-javascript-v2.23.0.zip']
for x in required:req(x)
has('backend/app/config.py','version: str = "2.23.0"'); has('backend/app/migrations.py','("0026",'); has('backend/app/main.py','federation.public_router'); has('backend/app/routers/meta.py','federated_core_trusted_node_exchange'); has('backend/app/services/federation.py','reference_first'); has('backend/app/services/federation.py','trust_secrets_persisted'); has('backend/app/services/federation.py','automatic_truth_promotion'); has('backend/app/services/certification.py','certification_require_federation_ready'); has('wordpress-plugin/sustainable-catalyst-platform-core/sustainable-catalyst-platform-core.php','Version: 2.23.0'); has('render.yaml','SC_CORE_FEDERATION_TRUSTED_NODE_EXCHANGE_ENABLED')
assert json.loads(req('backend/public_sdk/javascript/package.json').read_text())['version']=='2.23.0'; assert 'version = "2.23.0"' in req('backend/public_sdk/python/pyproject.toml').read_text()
for z in ['backend/public_sdk/downloads/sc-platform-core-public-python-v2.23.0.zip','backend/public_sdk/downloads/sc-platform-core-public-javascript-v2.23.0.zip']:
    with zipfile.ZipFile(req(z)) as f: assert f.testzip() is None
for script in ['PUSH_PLATFORM_CORE_V2230_FINAL.sh','deploy_and_validate_platform_core_v2_23_0_macos.sh']:
    text=req(script).read_text(); assert 'v2.23.0' in text and 'v2_23_0' in text
print('PASS - v2.23.0 release contract')
