#!/usr/bin/env python3
from pathlib import Path
import ast,re
ROOT=Path(__file__).resolve().parents[1]
CFG=(ROOT/'backend/app/config.py').read_text(); MIG=(ROOT/'backend/app/migrations.py').read_text(); MOD=(ROOT/'backend/app/models.py').read_text(); MAIN=(ROOT/'backend/app/main.py').read_text(); META=(ROOT/'backend/app/routers/meta.py').read_text(); ROUTER=(ROOT/'backend/app/routers/open_forensics.py').read_text(); SERVICE=(ROOT/'backend/app/services/open_forensics.py').read_text(); WP=(ROOT/'wordpress-plugin/sustainable-catalyst-platform-core/sustainable-catalyst-platform-core.php').read_text(); SDKPY=(ROOT/'backend/public_sdk/python/sc_platform_core_public/client.py').read_text(); SDKJS=(ROOT/'backend/public_sdk/javascript/index.mjs').read_text(); PKG=(ROOT/'backend/public_sdk/javascript/package.json').read_text(); PYPROJECT=(ROOT/'backend/public_sdk/python/pyproject.toml').read_text()
assert 'version: str = "2.42.0"' in CFG and 'SustainableCatalystPlatformCore/2.42.0' in CFG
assert 'open_forensics_enabled' in CFG and 'open_forensics_public_metadata_enabled' in CFG
mod=ast.parse(MIG); migrations=None
for n in mod.body:
    if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='MIGRATIONS' for t in n.targets): migrations=ast.literal_eval(n.value)
assert migrations; versions=[v for v,_ in migrations]; descriptions=dict(migrations); assert versions[-1]=='0046' and len(versions)==len(set(versions)); assert len(descriptions['0046'])<=300
for name in ['ForensicInvestigationRecord','ForensicObjectRecord','ForensicEvidenceItemRecord','ForensicEvidenceSourceBindingRecord','ForensicProvenanceActivityRecord','ForensicObjectRelationRecord','ForensicSnapshotRecord']: assert f'class {name}' in MOD
assert 'open_forensics.router' in MAIN and 'open_forensics.public_router' in MAIN and 'open_forensics' in META
for term in ['evidence_provenance_capture_by_core','content_hash_recording_by_core','chain_of_custody_by_core','authenticity_determination_by_core','identity_attribution_by_core','causal_conclusion_by_core','legal_conclusion_by_core','automatic_truth_promotion']: assert term in SERVICE
assert 'sc.open-forensics.investigation.v1' in SERVICE and 'sc.open-forensics.portable-investigation.v1' in SERVICE
assert '/v1/open-forensics' in ROUTER and '/api/v1/open-forensics' in ROUTER
assert 'Version: 2.42.0' in WP and 'sc_platform_core_open_forensics_status' in WP
assert 'open_forensics_readiness' in SDKPY and 'openForensicsReadiness' in SDKJS
assert '"version": "2.42.0"' in PKG and 'version = "2.42.0"' in PYPROJECT
print(f"PASS - dependency-free release contract; migration ledger max=300, 0046 chars={len(descriptions['0046'])}")
print('PASS - v2.42.0 Forensic Object Model & Evidence Provenance release contract')
