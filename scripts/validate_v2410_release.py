#!/usr/bin/env python3
from pathlib import Path
import ast, re
ROOT=Path(__file__).resolve().parents[1]
CFG=(ROOT/'backend/app/config.py').read_text(); MIG=(ROOT/'backend/app/migrations.py').read_text(); MOD=(ROOT/'backend/app/models.py').read_text(); MAIN=(ROOT/'backend/app/main.py').read_text(); META=(ROOT/'backend/app/routers/meta.py').read_text(); ROUTER=(ROOT/'backend/app/routers/reproducible_visual_knowledge.py').read_text(); SERVICE=(ROOT/'backend/app/services/reproducible_visual_knowledge.py').read_text(); WP=(ROOT/'wordpress-plugin/sustainable-catalyst-platform-core/sustainable-catalyst-platform-core.php').read_text(); SDKPY=(ROOT/'backend/public_sdk/python/sc_platform_core_public/client.py').read_text(); SDKJS=(ROOT/'backend/public_sdk/javascript/index.mjs').read_text(); PKG=(ROOT/'backend/public_sdk/javascript/package.json').read_text(); PYPROJECT=(ROOT/'backend/public_sdk/python/pyproject.toml').read_text()
assert 'version: str = "2.41.0"' in CFG and 'SustainableCatalystPlatformCore/2.41.0' in CFG
assert 'reproducible_visual_knowledge_enabled' in CFG and 'reproducible_visual_knowledge_public_metadata_enabled' in CFG
mod=ast.parse(MIG); migrations=None
for n in mod.body:
    if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='MIGRATIONS' for t in n.targets): migrations=ast.literal_eval(n.value)
assert migrations; versions=[v for v,_ in migrations]; descriptions=dict(migrations); assert versions[-1]=='0045' and len(versions)==len(set(versions)); assert len(descriptions['0045'])<=300
for name in ['ReproducibleVisualKnowledgePackageRecord','ReproducibleVisualKnowledgeInputRecord','ReproducibleVisualKnowledgeEnvironmentRecord','ReproducibleVisualKnowledgeReplayPlanRecord','ReproducibleVisualKnowledgeVerificationRecord','ReproducibleVisualKnowledgeSnapshotRecord']: assert f'class {name}' in MOD
assert 'reproducible_visual_knowledge.router' in MAIN and 'reproducible_visual_knowledge.public_router' in MAIN
assert 'reproducible_visual_knowledge_layer' in META
for term in ['manifest_hashing_by_core','specialist_execution_by_core','replay_execution_by_core','output_equivalence_claim_by_core_without_external_evidence','automatic_truth_promotion']: assert term in SERVICE
assert 'sc.reproducible-visual-knowledge.v1' in SERVICE and 'sc.reproducible-visual-knowledge-package.v1' in SERVICE
assert '/v1/reproducible-visual-knowledge' in ROUTER and '/api/v1/reproducible-visual-knowledge' in ROUTER
assert 'Version: 2.41.0' in WP and 'sc_platform_core_reproducible_visual_knowledge_status' in WP
assert 'reproducible_visual_knowledge_readiness' in SDKPY and 'reproducibleVisualKnowledgeReadiness' in SDKJS
assert '"version": "2.41.0"' in PKG and 'version = "2.41.0"' in PYPROJECT
print(f"PASS - dependency-free release contract; migration ledger max=300, 0045 chars={len(descriptions['0045'])}")
print('PASS - v2.41.0 Reproducible Visual Knowledge Layer release contract')
