from pathlib import Path
import json,re,zipfile
R=Path(__file__).resolve().parents[1]
def req(path):
 p=R/path; assert p.is_file(),path; return p
def has(path,text): assert text in req(path).read_text(),(path,text)
required=[
'backend/app/config.py','backend/app/models.py','backend/app/migrations.py','backend/app/routers/workload_governance.py','backend/app/services/workload_governance.py','backend/app/services/certification.py',
'backend/scripts/validate_workload_governance.py','backend/tests/test_distributed_quota_admission_workload_governance_v2260.py',
'schemas/workload-class-v1.schema.json','schemas/distributed-quota-policy-v1.schema.json','schemas/workload-admission-decision-v1.schema.json',
'docs/DISTRIBUTED_QUOTAS_ADMISSION_WORKLOAD_GOVERNANCE_V2260.md','RELEASE_NOTES_V2260.md','PLATFORM_CORE_V2260_INSTALL_AND_TEST.md','PLATFORM_CORE_V2260_DISTRIBUTED_QUOTA_ADMISSION_AUDIT.md','PLATFORM_CORE_V2260_TERMINAL_COMMANDS.txt','deployment/platform-core-v2260.env.example',
'render.yaml','wordpress-plugin/sustainable-catalyst-platform-core/sustainable-catalyst-platform-core.php',
'backend/public_sdk/downloads/sc-platform-core-public-python-v2.26.0.zip','backend/public_sdk/downloads/sc-platform-core-public-javascript-v2.26.0.zip',
'PUSH_PLATFORM_CORE_V2260_FINAL.sh','deploy_and_validate_platform_core_v2_26_0_macos.sh']
for path in required:req(path)
has('backend/app/config.py','version: str = "2.26.0"')
has('backend/app/migrations.py','("0029", "Database-shared distributed quota policies')
has('backend/app/main.py','workload_governance.public_router')
has('backend/app/routers/meta.py','"distributed_quota_admission_workload_governance"')
has('backend/app/services/workload_governance.py','"distributed_quota_backend":"database-shared"')
has('backend/app/services/workload_governance.py','"hard_admission_control"')
has('backend/app/services/workload_governance.py','"automatic_scaling":False')
has('backend/app/services/certification.py','certification_require_workload_governance_ready')
has('wordpress-plugin/sustainable-catalyst-platform-core/sustainable-catalyst-platform-core.php','Version: 2.26.0')
has('wordpress-plugin/sustainable-catalyst-platform-core/sustainable-catalyst-platform-core.php','sc_platform_core_workload_governance_status')
has('render.yaml','SustainableCatalystPlatformCore/2.26.0')
has('render.yaml','SC_CORE_WORKLOAD_GOVERNANCE_ENABLED')
has('render.yaml','SC_CORE_CERTIFICATION_REQUIRE_WORKLOAD_GOVERNANCE_READY')
assert json.loads(req('backend/public_sdk/javascript/package.json').read_text())['version']=='2.26.0'
assert 'version = "2.26.0"' in req('backend/public_sdk/python/pyproject.toml').read_text()
assert req('README.md').read_text().startswith('# Sustainable Catalyst Platform Core v2.26.0')
has('docs/ROADMAP.md','## v2.26.0 — Distributed Quotas, Admission Control & Workload Governance')
has('docs/ROADMAP.md','Next planned: v2.27.0 — Scientific Object Storage & Processing Adapter Fabric.')
meta=req('backend/app/routers/meta.py').read_text(); implemented_block=meta.split('capabilities=[',1)[1].split('deferred_capabilities=[',1)[0]; deferred_block=meta.split('deferred_capabilities=[',1)[1].split(']',1)[0]
implemented=re.findall(r'"([a-z0-9_]+)"',implemented_block); deferred=re.findall(r'"([a-z0-9_]+)"',deferred_block)
assert len(implemented)==len(set(implemented)); assert len(deferred)==len(set(deferred)); assert set(implemented).isdisjoint(deferred)
for cap in ('distributed_quota_admission_workload_governance','database_shared_distributed_quota_backend','per_subject_quota_budgets','burst_quota_budgets','workload_priority_classes','expiring_concurrency_leases','slo_aware_admission_control','capacity_aware_admission_control','hard_admission_rejection','retry_after_guidance','idempotent_admission_decisions','public_safe_workload_governance_status','workload_governance_certification_gate'):
 assert cap in implemented and cap not in deferred,cap
assert 'distributed_rate_limit_backend' not in deferred
for schema in ('schemas/workload-class-v1.schema.json','schemas/distributed-quota-policy-v1.schema.json','schemas/workload-admission-decision-v1.schema.json'): json.loads(req(schema).read_text())
for z in ('backend/public_sdk/downloads/sc-platform-core-public-python-v2.26.0.zip','backend/public_sdk/downloads/sc-platform-core-public-javascript-v2.26.0.zip'):
 with zipfile.ZipFile(req(z)) as a: assert a.testzip() is None
for script in ('PUSH_PLATFORM_CORE_V2260_FINAL.sh','deploy_and_validate_platform_core_v2_26_0_macos.sh'):
 text=req(script).read_text(); assert 'v2.26.0' in text and 'v2260' in text and 'validate_workload_governance.py' in text and 'scan_push_safe_secrets.py' in text
print('PASS - v2.26.0 distributed quotas admission control and workload governance release contract')
