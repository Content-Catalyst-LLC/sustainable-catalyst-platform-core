#!/usr/bin/env python3
from app.services.reproducible_graph_investigation_package import contract_document, reference_reproducible_graph_investigation_package_bundle
b=reference_reproducible_graph_investigation_package_bundle(); c=contract_document()
assert c['release']=='3.88.0' and c['contract']=='sc.core.reproducible-graph-investigation-package.v1'
assert len(b.object_bindings)==12 and len(b.artifacts)==4 and len(b.reproduction_steps)==6 and len(b.snapshots)==1
for k in ['reproducibility_preserves_epistemic_state','package_is_content_addressed','contradictions_are_preserved','source_provenance_is_preserved','reproduction_plan_is_explicit','later_revisions_may_supersede_package_state','integrity_verification_is_distinct_from_truth_verification','replay_is_non_mutating']:
    assert c['principles'][k] is True
for k in ['reproducibility_establishes_truth','reproducibility_establishes_authenticity','reproducibility_establishes_admissibility','package_hash_establishes_content_truth','replay_success_establishes_correctness','byte_identical_replay_is_independent_corroboration','package_freezes_future_truth_state','identity_graph_mutation_performed','relationship_graph_mutation_performed','evidence_graph_mutation_performed']:
    assert c['boundaries'][k] is False
print('PASS - Platform Core v3.88.0 Reproducible Graph Investigation Package')
print('CONTRACT='+c['contract'])
print('QUESTIONS='+str(len(b.questions)))
print('OBJECT_BINDINGS='+str(len(b.object_bindings)))
print('ARTIFACTS='+str(len(b.artifacts)))
print('REPRODUCTION_STEPS='+str(len(b.reproduction_steps)))
print('MANIFESTS='+str(len(b.manifests)))
print('INTEGRITY_RECORDS='+str(len(b.integrity_records)))
print('VERIFICATION_RECORDS='+str(len(b.verification_records)))
print('REPRODUCIBILITY_ESTABLISHES_TRUTH=false')
print('REPLAY_MUTATES_GRAPH=false')
