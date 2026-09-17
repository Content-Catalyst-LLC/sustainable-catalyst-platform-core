#!/usr/bin/env python3
from pathlib import Path
import ast
ROOT=Path(__file__).resolve().parents[1]
CFG=(ROOT/'backend/app/config.py').read_text(); MIG=(ROOT/'backend/app/migrations.py').read_text(); MOD=(ROOT/'backend/app/models.py').read_text(); MAIN=(ROOT/'backend/app/main.py').read_text(); ROUTER=(ROOT/'backend/app/routers/open_forensics.py').read_text(); SERVICE=(ROOT/'backend/app/services/open_forensics.py').read_text(); WP=(ROOT/'wordpress-plugin/sustainable-catalyst-platform-core/sustainable-catalyst-platform-core.php').read_text(); SDKPY=(ROOT/'backend/public_sdk/python/sc_platform_core_public/client.py').read_text(); SDKJS=(ROOT/'backend/public_sdk/javascript/index.mjs').read_text(); PKG=(ROOT/'backend/public_sdk/javascript/package.json').read_text(); PYPROJECT=(ROOT/'backend/public_sdk/python/pyproject.toml').read_text()
assert 'version: str = "2.50.0"' in CFG and 'SustainableCatalystPlatformCore/2.50.0' in CFG
mod=ast.parse(MIG); migrations=None
for n in mod.body:
    if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='MIGRATIONS' for t in n.targets): migrations=ast.literal_eval(n.value)
assert migrations; versions=[v for v,_ in migrations]; descriptions=dict(migrations); assert versions[-1]=='0054' and len(versions)==len(set(versions)); assert len(descriptions['0054'])<=300
for name in ['ForensicResearchGraphRecord','ForensicResearchGraphNodeRecord','ForensicResearchGraphEdgeRecord','ForensicResearchGraphViewRecord','ForensicResearchGraphHandoffRecord','ForensicResearchGraphSnapshotRecord','ForensicResearchGraphPackageRecord']: assert f'class {name}' in MOD,name
for term in ['forensic_research_graph_registry_by_core','cross_forensics_node_binding_by_core','explicit_graph_edge_registry_by_core','renderer_neutral_forensic_graph_specification_by_core','cross_product_graph_handoffs_by_core','immutable_forensic_graph_snapshots_by_core','portable_forensic_graph_packages_by_core','automatic_graph_edge_inference_by_core','automatic_entity_resolution_by_core','automatic_identity_resolution_by_core','automatic_causal_inference_by_core','relationship_truth_determination_by_core','graph_analytics_execution_by_core','remote_product_fetch_by_core']: assert term in SERVICE,term
for term in ['/research-graphs','/research-graph-inventory','/nodes','/edges','/views','/visual-spec','/handoffs','/snapshots','/packages']: assert term in ROUTER,term
assert 'forensic research graph' in MAIN.lower()
assert 'Version: 2.50.0' in WP and 'sc_platform_core_forensic_research_graph_status' in WP
assert 'open_forensics_research_graph' in SDKPY and 'openForensicsResearchGraph' in SDKJS
assert '"version": "2.50.0"' in PKG and 'version = "2.50.0"' in PYPROJECT
assert (ROOT/'backend/public_sdk/downloads/sc-platform-core-public-python-v2.50.0.zip').is_file()
assert (ROOT/'backend/public_sdk/downloads/sc-platform-core-public-javascript-v2.50.0.zip').is_file()
print(f"PASS - dependency-free release contract; migration ledger max=300, 0054 chars={len(descriptions['0054'])}")
print('PASS - v2.50.0 Forensic Research Graph release contract')
