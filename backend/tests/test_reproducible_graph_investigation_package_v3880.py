import copy
import pytest
from pydantic import ValidationError
from app.services.reproducible_graph_investigation_package import (
    CONTRACT_VERSION, CORE_RELEASE, EpistemicState, PackagingRole, VerificationDisposition,
    InvestigationObjectBinding, PackageIntegrityRecord,
    reference_reproducible_graph_investigation_package_bundle, contract_document,
)

def ref(): return reference_reproducible_graph_investigation_package_bundle()

def test_release(): assert CORE_RELEASE=='3.88.0'
def test_contract(): assert CONTRACT_VERSION=='sc.core.reproducible-graph-investigation-package.v1'
def test_reference_bundle_valid(): assert len(ref().object_bindings)==12
def test_reference_counts():
    b=ref(); assert (len(b.questions),len(b.artifacts),len(b.reproduction_steps),len(b.manifests),len(b.integrity_records),len(b.verification_records),len(b.snapshots))==(1,4,6,1,1,1,1)
def test_bundle_fingerprint_stable(): assert ref().fingerprint()==ref().fingerprint()
def test_contract_reference_fingerprint(): assert contract_document()['reference']['bundle_fingerprint_sha256']==ref().fingerprint()
def test_package_root_stable(): assert ref().integrity_records[0].package_root_sha256==ref().integrity_records[0].package_root_sha256

def test_primary_path_preserved_source_observed():
    b=ref(); x=[v for v in b.object_bindings if v.object_ref=='connection-path:synthetic:primary:v1'][0]; assert x.epistemic_state==EpistemicState.source_observed
def test_alternative_path_preserved_hypothesis():
    b=ref(); x=[v for v in b.object_bindings if v.object_ref=='connection-path:synthetic:alternative:v1'][0]; assert x.epistemic_state==EpistemicState.hypothesis
def test_identity_resolution_preserved_partial():
    b=ref(); x=[v for v in b.object_bindings if v.object_ref=='contradiction-decision:synthetic:identity:v1'][0]; assert x.epistemic_state==EpistemicState.partially_resolved
def test_relationship_resolution_preserved_handoff():
    b=ref(); x=[v for v in b.object_bindings if v.object_ref=='contradiction-decision:synthetic:relationship:v1'][0]; assert x.epistemic_state==EpistemicState.resolved_for_handoff
def test_two_timelines_packaged(): assert len([x for x in ref().object_bindings if x.object_type=='EntityTimeline'])==2
def test_document_segments_packaged(): assert len([x for x in ref().object_bindings if x.object_type=='DocumentSegmentAnchor'])==2
def test_replay_non_mutating(): assert all(x.replay_does_not_mutate_graph for x in ref().reproduction_steps)
def test_integrity_not_truth(): assert ref().integrity_records[0].integrity_verification_is_not_truth_verification is True
def test_byte_identical_not_independent(): assert ref().verification_records[0].byte_identical_replay_is_not_independent_corroboration is True
def test_snapshot_later_revision_allowed(): assert ref().snapshots[0].later_revisions_may_supersede_snapshot is True
def test_no_graph_mutation():
    b=ref(); assert not b.identity_graph_mutation_performed and not b.relationship_graph_mutation_performed and not b.evidence_graph_mutation_performed

def test_manifest_all_bindings(): assert set(ref().manifests[0].object_binding_refs)=={x.object_binding_id for x in ref().object_bindings}
def test_manifest_all_artifacts(): assert set(ref().manifests[0].artifact_refs)=={x.artifact_id for x in ref().artifacts}
def test_manifest_all_steps(): assert set(ref().manifests[0].reproduction_step_refs)=={x.reproduction_step_id for x in ref().reproduction_steps}
def test_integrity_all_artifacts(): assert set(ref().integrity_records[0].ordered_artifact_refs)=={x.artifact_id for x in ref().artifacts}
def test_verification_all_steps(): assert set(ref().verification_records[0].reproduced_step_refs)=={x.reproduction_step_id for x in ref().reproduction_steps}
def test_verification_qualified(): assert ref().verification_records[0].disposition==VerificationDisposition.verified_with_qualifications
def test_verification_has_qualifications(): assert len(ref().verification_records[0].qualifications)==3

def test_unknown_binding_rejected():
    d=ref().model_dump(mode='python'); d['object_bindings'][0]['object_ref']='unknown:object';
    with pytest.raises(ValidationError): type(ref()).model_validate(d)
def test_unknown_question_entity_rejected():
    d=ref().model_dump(mode='python'); d['questions'][0]['entity_refs']=['entity:missing'];
    with pytest.raises(ValidationError): type(ref()).model_validate(d)
def test_unknown_manifest_binding_rejected():
    d=ref().model_dump(mode='python'); d['manifests'][0]['object_binding_refs'].append('binding:missing');
    with pytest.raises(ValidationError): type(ref()).model_validate(d)
def test_unknown_manifest_artifact_rejected():
    d=ref().model_dump(mode='python'); d['manifests'][0]['artifact_refs'].append('artifact:missing');
    with pytest.raises(ValidationError): type(ref()).model_validate(d)
def test_unknown_snapshot_ref_rejected():
    d=ref().model_dump(mode='python'); d['snapshots'][0]['event_timeline_snapshot_ref']='snapshot:missing';
    with pytest.raises(ValidationError): type(ref()).model_validate(d)
def test_integrity_list_alignment_rejected():
    d=ref().integrity_records[0].model_dump(mode='python'); d['ordered_artifact_sha256s']=d['ordered_artifact_sha256s'][:-1]
    with pytest.raises(ValidationError): PackageIntegrityRecord.model_validate(d)
def test_bad_sha_rejected():
    d=ref().object_bindings[0].model_dump(mode='python'); d['object_fingerprint_sha256']='bad'
    with pytest.raises(ValidationError): InvestigationObjectBinding.model_validate(d)

@pytest.mark.parametrize('field',['require_content_fingerprints','require_upstream_contract_identity','require_epistemic_state_preservation','require_source_provenance_preservation','require_contradiction_preservation','require_environment_manifest','require_reproduction_plan','require_as_of_time'])
def test_policy_requirements(field): assert getattr(ref().policies[0],field) is True
@pytest.mark.parametrize('field',['reproducibility_can_establish_truth','reproducibility_can_establish_authenticity','reproducibility_can_establish_admissibility','package_hash_can_establish_content_truth','replay_success_can_establish_correctness','automatic_graph_mutation_allowed'])
def test_policy_prohibitions(field): assert getattr(ref().policies[0],field) is False
@pytest.mark.parametrize('field',['reproducibility_preserves_epistemic_state','package_is_content_addressed','contradictions_are_preserved','source_provenance_is_preserved','reproduction_plan_is_explicit','later_revisions_may_supersede_package_state','integrity_verification_is_distinct_from_truth_verification','replay_is_non_mutating'])
def test_contract_principles(field): assert contract_document()['principles'][field] is True
@pytest.mark.parametrize('field',['reproducibility_establishes_truth','reproducibility_establishes_authenticity','reproducibility_establishes_admissibility','package_hash_establishes_content_truth','replay_success_establishes_correctness','byte_identical_replay_is_independent_corroboration','package_freezes_future_truth_state','identity_graph_mutation_performed','relationship_graph_mutation_performed','evidence_graph_mutation_performed'])
def test_contract_boundaries(field): assert contract_document()['boundaries'][field] is False
@pytest.mark.parametrize('i',range(12))
def test_bindings_have_64_char_hash(i): assert len(ref().object_bindings[i].object_fingerprint_sha256)==64
@pytest.mark.parametrize('i',range(12))
def test_bindings_preserve_state(i): assert ref().object_bindings[i].source_state_preserved is True and ref().object_bindings[i].packaging_does_not_promote_epistemic_state is True
@pytest.mark.parametrize('i',range(12))
def test_bindings_have_provenance(i): assert ref().object_bindings[i].provenance_refs
@pytest.mark.parametrize('i',range(4))
def test_artifacts_have_hash(i): assert len(ref().artifacts[i].content_sha256)==64
@pytest.mark.parametrize('i',range(4))
def test_artifact_hash_not_truth(i): assert ref().artifacts[i].content_hash_verifies_bytes_not_truth is True
@pytest.mark.parametrize('i',range(6))
def test_steps_have_stop_condition(i): assert len(ref().reproduction_steps[i].stopping_condition)>10
@pytest.mark.parametrize('i',range(6))
def test_steps_success_not_truth(i): assert ref().reproduction_steps[i].successful_step_is_not_truth_validation is True
@pytest.mark.parametrize('i',range(6))
def test_step_sequences(i): assert ref().reproduction_steps[i].sequence==i+1
@pytest.mark.parametrize('state',[s for s in EpistemicState])
def test_epistemic_enum_values(state): assert isinstance(state.value,str) and state.value
@pytest.mark.parametrize('role',[r for r in PackagingRole])
def test_packaging_role_values(role): assert isinstance(role.value,str) and role.value
