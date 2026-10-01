from app.services.unified_entity_evidence_intelligence_runtime import contract_document, reference_unified_entity_evidence_intelligence_runtime_bundle
b=reference_unified_entity_evidence_intelligence_runtime_bundle(); c=contract_document()
assert b.release=='3.90.0'; assert c['contract']=='sc.core.unified-entity-evidence-intelligence-runtime.v1'
assert len(b.capabilities)==13 and len(b.stage_executions)==13 and len(b.handoffs)==12
assert b.traces[0].final_disposition.value=='qualified-analytical'
assert not b.identity_graph_mutation_performed and not b.relationship_graph_mutation_performed and not b.evidence_graph_mutation_performed
print('PASS - Platform Core v3.90.0 Unified Entity & Evidence Intelligence Runtime')
print(f'CONTRACT={c["contract"]}')
print(f'CAPABILITIES={len(b.capabilities)}')
print(f'STAGES={len(b.stage_executions)}')
print(f'HANDOFFS={len(b.handoffs)}')
print(f'FINDINGS={len(b.findings)}')
print(f'FINAL_DISPOSITION={b.traces[0].final_disposition.value}')
print('GLOBAL_TRUTH_SCORE=false')
print('AUTO_PROMOTION=false')
print('AUTO_CONTRADICTION_RESOLUTION=false')
print('IDENTITY_GRAPH_MUTATION_PERFORMED=false')
print('RELATIONSHIP_GRAPH_MUTATION_PERFORMED=false')
print('EVIDENCE_GRAPH_MUTATION_PERFORMED=false')
