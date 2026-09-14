#!/usr/bin/env python3
from pathlib import Path
import ast
ROOT=Path(__file__).resolve().parents[1]
CFG=(ROOT/'backend/app/config.py').read_text(); MIG=(ROOT/'backend/app/migrations.py').read_text(); MOD=(ROOT/'backend/app/models.py').read_text(); MAIN=(ROOT/'backend/app/main.py').read_text(); ROUTER=(ROOT/'backend/app/routers/open_forensics.py').read_text(); SERVICE=(ROOT/'backend/app/services/open_forensics.py').read_text(); WP=(ROOT/'wordpress-plugin/sustainable-catalyst-platform-core/sustainable-catalyst-platform-core.php').read_text(); SDKPY=(ROOT/'backend/public_sdk/python/sc_platform_core_public/client.py').read_text(); SDKJS=(ROOT/'backend/public_sdk/javascript/index.mjs').read_text(); PKG=(ROOT/'backend/public_sdk/javascript/package.json').read_text(); PYPROJECT=(ROOT/'backend/public_sdk/python/pyproject.toml').read_text()
assert 'version: str = "2.43.0"' in CFG and 'SustainableCatalystPlatformCore/2.43.0' in CFG
mod=ast.parse(MIG); migrations=None
for n in mod.body:
    if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='MIGRATIONS' for t in n.targets): migrations=ast.literal_eval(n.value)
assert migrations; versions=[v for v,_ in migrations]; descriptions=dict(migrations); assert versions[-1]=='0047' and len(versions)==len(set(versions)); assert len(descriptions['0047'])<=300
for name in ['ForensicCustodianRecord','ForensicCustodyEventRecord','ForensicEvidenceSealRecord','ForensicIntegrityCheckRecord','ForensicCustodyContinuityAssessmentRecord','ForensicCustodySnapshotRecord']: assert f'class {name}' in MOD
for term in ['chain_of_custody_recording_by_core','tamper_evident_custody_event_chain_by_core','evidence_integrity_verification_by_core','seal_state_recording_by_core','custody_continuity_analysis_by_core','physical_transfer_verification_by_core','identity_verification_by_core','legal_admissibility_determination_by_core','automatic_truth_promotion']: assert term in SERVICE
for term in ['/custody-events','/custody-chain','/integrity-checks','/seals','/continuity-assessments','/custody-snapshots']: assert term in ROUTER
assert 'tamper-evident custody event chains' in MAIN
assert 'Version: 2.43.0' in WP and 'sc_platform_core_custody_integrity_status' in WP
assert 'open_forensics_custody_chain' in SDKPY and 'openForensicsCustodyChain' in SDKJS
assert '"version": "2.43.0"' in PKG and 'version = "2.43.0"' in PYPROJECT
print(f"PASS - dependency-free release contract; migration ledger max=300, 0047 chars={len(descriptions['0047'])}")
print('PASS - v2.43.0 Evidence Integrity & Chain of Custody release contract')
