#!/usr/bin/env python3
from pathlib import Path
import ast
ROOT=Path(__file__).resolve().parents[1]
CFG=(ROOT/'backend/app/config.py').read_text(); MIG=(ROOT/'backend/app/migrations.py').read_text(); MOD=(ROOT/'backend/app/models.py').read_text(); MAIN=(ROOT/'backend/app/main.py').read_text(); ROUTER=(ROOT/'backend/app/routers/open_forensics.py').read_text(); SERVICE=(ROOT/'backend/app/services/open_forensics.py').read_text(); WP=(ROOT/'wordpress-plugin/sustainable-catalyst-platform-core/sustainable-catalyst-platform-core.php').read_text(); SDKPY=(ROOT/'backend/public_sdk/python/sc_platform_core_public/client.py').read_text(); SDKJS=(ROOT/'backend/public_sdk/javascript/index.mjs').read_text(); PKG=(ROOT/'backend/public_sdk/javascript/package.json').read_text(); PYPROJECT=(ROOT/'backend/public_sdk/python/pyproject.toml').read_text()
assert 'version: str = "2.49.0"' in CFG and 'SustainableCatalystPlatformCore/2.49.0' in CFG
mod=ast.parse(MIG); migrations=None
for n in mod.body:
    if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='MIGRATIONS' for t in n.targets): migrations=ast.literal_eval(n.value)
assert migrations; versions=[v for v,_ in migrations]; descriptions=dict(migrations); assert versions[-1]=='0053' and len(versions)==len(set(versions)); assert len(descriptions['0053'])<=300
for name in ['ForensicStatementRecord','ForensicStatementSourceContextRecord','ForensicDocumentRecord','ForensicDocumentAssertionRecord','ForensicStatementClaimBindingRecord','ForensicStatementRelationRecord','ForensicTemporalConsistencyRecord','ForensicDocumentarySnapshotRecord']: assert f'class {name}' in MOD,name
for term in ['statement_testimony_registry_by_core','documentary_evidence_registry_by_core','speaker_author_reference_binding_by_core','source_context_preservation_by_core','statement_claim_binding_by_core','explicit_corroboration_contradiction_relations_by_core','temporal_consistency_recording_by_core','immutable_documentary_snapshots_by_core','automatic_claim_extraction_by_core','automatic_speaker_identity_resolution_by_core','automatic_authorship_attribution_by_core','credibility_scoring_by_core']: assert term in SERVICE,term
for term in ['/statements','/source-contexts','/documents','/assertions','/claim-bindings','/statement-relations','/temporal-consistency','/documentary-evidence','/documentary-snapshots']: assert term in ROUTER,term
assert 'testimony, statements, and documentary evidence' in MAIN.lower()
assert 'Version: 2.49.0' in WP and 'sc_platform_core_forensic_documentary_evidence_status' in WP
assert 'open_forensics_documentary_evidence' in SDKPY and 'openForensicsDocumentaryEvidence' in SDKJS
assert '"version": "2.49.0"' in PKG and 'version = "2.49.0"' in PYPROJECT
print(f"PASS - dependency-free release contract; migration ledger max=300, 0053 chars={len(descriptions['0053'])}")
print('PASS - v2.49.0 Testimony, Statements & Documentary Evidence release contract')
