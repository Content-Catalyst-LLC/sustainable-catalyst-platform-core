#!/usr/bin/env python3
from pathlib import Path
import ast
ROOT=Path(__file__).resolve().parents[1]
CFG=(ROOT/'backend/app/config.py').read_text(); MIG=(ROOT/'backend/app/migrations.py').read_text(); MOD=(ROOT/'backend/app/models.py').read_text(); MAIN=(ROOT/'backend/app/main.py').read_text(); ROUTER=(ROOT/'backend/app/routers/open_forensics.py').read_text(); SERVICE=(ROOT/'backend/app/services/open_forensics.py').read_text(); WP=(ROOT/'wordpress-plugin/sustainable-catalyst-platform-core/sustainable-catalyst-platform-core.php').read_text(); SDKPY=(ROOT/'backend/public_sdk/python/sc_platform_core_public/client.py').read_text(); SDKJS=(ROOT/'backend/public_sdk/javascript/index.mjs').read_text(); PKG=(ROOT/'backend/public_sdk/javascript/package.json').read_text(); PYPROJECT=(ROOT/'backend/public_sdk/python/pyproject.toml').read_text()
assert 'version: str = "2.44.0"' in CFG and 'SustainableCatalystPlatformCore/2.44.0' in CFG
mod=ast.parse(MIG); migrations=None
for n in mod.body:
    if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='MIGRATIONS' for t in n.targets): migrations=ast.literal_eval(n.value)
assert migrations; versions=[v for v,_ in migrations]; descriptions=dict(migrations); assert versions[-1]=='0048' and len(versions)==len(set(versions)); assert len(descriptions['0048'])<=300
for name in ['ForensicClaimRecord','ForensicClaimEvidenceAssessmentRecord','ForensicContradictionRecord','ForensicHypothesisRecord','ForensicHypothesisEvidenceAssessmentRecord','ForensicHypothesisRelationRecord','ForensicReasoningSnapshotRecord']: assert f'class {name}' in MOD
for term in ['structured_claim_registry_by_core','claim_evidence_position_mapping_by_core','explicit_contradiction_registry_by_core','competing_hypothesis_registry_by_core','descriptive_hypothesis_comparison_matrix_by_core','automatic_contradiction_detection_by_core','claim_truth_determination_by_core','hypothesis_probability_assignment_by_core','hypothesis_ranking_by_core','verdict_generation_by_core','automatic_truth_promotion']: assert term in SERVICE
for term in ['/claims','/evidence-assessments','/contradictions','/hypotheses','/hypothesis-relations','/claim-map','/hypothesis-matrix','/reasoning-snapshots']: assert term in ROUTER
assert 'structured claims, explicit contradictions, competing hypotheses' in MAIN
assert 'Version: 2.44.0' in WP and 'sc_platform_core_forensic_hypothesis_status' in WP
assert 'open_forensics_claim_map' in SDKPY and 'openForensicsClaimMap' in SDKJS
assert '"version": "2.44.0"' in PKG and 'version = "2.44.0"' in PYPROJECT
print(f"PASS - dependency-free release contract; migration ledger max=300, 0048 chars={len(descriptions['0048'])}")
print('PASS - v2.44.0 Claims, Contradictions & Competing Hypotheses release contract')
