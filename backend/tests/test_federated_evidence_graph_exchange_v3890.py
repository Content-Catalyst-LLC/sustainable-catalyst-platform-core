import pytest
from pydantic import ValidationError
from app.services.federated_evidence_graph_exchange import (
    CORE_RELEASE, CONTRACT_VERSION, NodeTrustState, ExchangeDirection, ExchangeDisposition,
    ConflictDisposition, FederationNodeIdentity, FederatedObjectDescriptor, ExchangeManifest,
    FederatedEvidenceGraphExchangeBundle, reference_federated_evidence_graph_exchange_bundle,
    contract_document,
)

def ref(): return reference_federated_evidence_graph_exchange_bundle()

def test_release(): assert CORE_RELEASE == "3.89.0"
def test_contract(): assert CONTRACT_VERSION == "sc.core.federated-evidence-graph-exchange.v1"
def test_reference_valid(): assert ref().release == "3.89.0"
def test_reference_counts():
    b=ref(); assert (len(b.nodes),len(b.object_descriptors),len(b.package_references),len(b.manifests),len(b.integrity_attestations),len(b.conflicts),len(b.assessments),len(b.snapshots))==(2,5,1,1,1,1,1,1)
def test_bundle_fingerprint_stable(): assert ref().fingerprint()==ref().fingerprint()
def test_contract_fingerprint(): assert contract_document()["reference"]["bundle_fingerprint_sha256"]==ref().fingerprint()
def test_assessment_disposition(): assert ref().assessments[0].disposition==ExchangeDisposition.accepted_for_local_validation
def test_manifest_is_import(): assert ref().manifests[0].direction==ExchangeDirection.import_
def test_conflict_unresolved(): assert ref().conflicts[0].disposition==ConflictDisposition.unresolved
def test_nodes_authenticated(): assert all(x.trust_state==NodeTrustState.authenticated for x in ref().nodes)
def test_no_graph_mutation():
    b=ref(); assert not b.identity_graph_mutation_performed and not b.relationship_graph_mutation_performed and not b.evidence_graph_mutation_performed

def test_remote_descriptor_preserves_state(): assert all(x.remote_state_preserved for x in ref().object_descriptors)
def test_remote_descriptor_not_truth(): assert all(x.descriptor_does_not_establish_local_truth for x in ref().object_descriptors)
def test_remote_descriptor_not_edge(): assert all(x.descriptor_does_not_create_local_graph_edge for x in ref().object_descriptors)
def test_signature_verified_but_not_truth():
    a=ref().integrity_attestations[0]; assert a.signature_verified and a.signature_proves_bytes_not_truth and a.signature_does_not_establish_source_claim_accuracy
def test_package_reference_not_import(): assert ref().package_references[0].package_reference_is_not_local_import is True
def test_snapshot_remote_refs(): assert ref().snapshots[0].remote_objects_remain_remote_references is True
def test_snapshot_supersedable(): assert ref().snapshots[0].later_exchange_may_supersede_snapshot is True
def test_local_validation_required(): assert ref().assessments[0].local_validation_required is True
def test_acceptance_does_not_promote(): assert ref().assessments[0].acceptance_does_not_promote_remote_assertions is True
def test_compatibility_not_semantic_equivalence(): assert ref().assessments[0].compatibility_does_not_establish_semantic_equivalence is True

def test_unknown_descriptor_node_rejected():
    d=ref().model_dump(mode="python"); d["object_descriptors"][0]["source_node_ref"]="node:missing"
    with pytest.raises(ValidationError): FederatedEvidenceGraphExchangeBundle.model_validate(d)
def test_unknown_manifest_policy_rejected():
    d=ref().model_dump(mode="python"); d["manifests"][0]["exchange_policy_ref"]="policy:missing"
    with pytest.raises(ValidationError): FederatedEvidenceGraphExchangeBundle.model_validate(d)
def test_unknown_manifest_descriptor_rejected():
    d=ref().model_dump(mode="python"); d["manifests"][0]["object_descriptor_refs"].append("descriptor:missing")
    with pytest.raises(ValidationError): FederatedEvidenceGraphExchangeBundle.model_validate(d)
def test_unknown_attestation_manifest_rejected():
    d=ref().model_dump(mode="python"); d["integrity_attestations"][0]["exchange_manifest_ref"]="manifest:missing"
    with pytest.raises(ValidationError): FederatedEvidenceGraphExchangeBundle.model_validate(d)
def test_unknown_conflict_descriptor_rejected():
    d=ref().model_dump(mode="python"); d["conflicts"][0]["remote_object_descriptor_ref"]="descriptor:missing"
    with pytest.raises(ValidationError): FederatedEvidenceGraphExchangeBundle.model_validate(d)
def test_unknown_assessment_conflict_rejected():
    d=ref().model_dump(mode="python"); d["assessments"][0]["conflict_refs"].append("conflict:missing")
    with pytest.raises(ValidationError): FederatedEvidenceGraphExchangeBundle.model_validate(d)
def test_unknown_snapshot_node_rejected():
    d=ref().model_dump(mode="python"); d["snapshots"][0]["node_refs"].append("node:missing")
    with pytest.raises(ValidationError): FederatedEvidenceGraphExchangeBundle.model_validate(d)
def test_same_source_destination_rejected():
    d=ref().manifests[0].model_dump(mode="python"); d["destination_node_ref"]=d["source_node_ref"]
    with pytest.raises(ValidationError): ExchangeManifest.model_validate(d)
def test_duplicate_descriptor_provenance_rejected():
    d=ref().object_descriptors[0].model_dump(mode="python"); d["provenance_refs"]=["x","x"]
    with pytest.raises(ValidationError): FederatedObjectDescriptor.model_validate(d)
def test_bad_node_hash_rejected():
    d=ref().nodes[0].model_dump(mode="python"); d["public_key_fingerprint_sha256"]="bad"
    with pytest.raises(ValidationError): FederationNodeIdentity.model_validate(d)

@pytest.mark.parametrize("field",[
    "require_node_identity","require_manifest_hash","require_object_fingerprints","require_upstream_contract_identity",
    "preserve_epistemic_state","preserve_source_provenance","preserve_contradictions","require_local_validation_before_promotion","allow_reference_first_exchange"
])
def test_policy_requirements(field): assert getattr(ref().policies[0],field) is True

@pytest.mark.parametrize("field",[
    "node_trust_can_establish_content_truth","signature_validity_can_establish_content_truth","federation_consensus_can_establish_truth",
    "remote_acceptance_can_create_local_evidence","remote_exchange_can_mutate_local_graph"
])
def test_policy_prohibitions(field): assert getattr(ref().policies[0],field) is False

@pytest.mark.parametrize("field",[
    "reference_first_exchange","remote_epistemic_state_preserved","source_provenance_preserved","contradictions_preserved",
    "local_validation_required_before_promotion","content_addressed_manifests","remote_objects_remain_remote_references"
])
def test_contract_principles(field): assert contract_document()["principles"][field] is True

@pytest.mark.parametrize("field",[
    "node_trust_establishes_content_truth","signature_validity_establishes_content_truth","federation_consensus_establishes_truth",
    "schema_compatibility_establishes_semantic_equivalence","remote_acceptance_creates_local_evidence","remote_reference_creates_local_graph_edge",
    "identity_graph_mutation_performed","relationship_graph_mutation_performed","evidence_graph_mutation_performed"
])
def test_contract_boundaries(field): assert contract_document()["boundaries"][field] is False

@pytest.mark.parametrize("i",range(5))
def test_descriptor_hashes(i): assert len(ref().object_descriptors[i].object_fingerprint_sha256)==64
@pytest.mark.parametrize("i",range(5))
def test_descriptor_provenance(i): assert ref().object_descriptors[i].provenance_refs
@pytest.mark.parametrize("i",range(5))
def test_descriptor_as_of(i): assert ref().object_descriptors[i].as_of.endswith("Z")
@pytest.mark.parametrize("i",range(5))
def test_descriptor_remote_state(i): assert ref().object_descriptors[i].remote_state_preserved is True
@pytest.mark.parametrize("state",list(NodeTrustState))
def test_node_state_enum(state): assert state.value
@pytest.mark.parametrize("state",list(ExchangeDisposition))
def test_exchange_disposition_enum(state): assert state.value
@pytest.mark.parametrize("state",list(ConflictDisposition))
def test_conflict_disposition_enum(state): assert state.value
@pytest.mark.parametrize("field",["package_reference_is_not_truth_verdict","package_reference_is_not_local_import"])
def test_package_boundaries(field): assert getattr(ref().package_references[0],field) is True
@pytest.mark.parametrize("field",["signature_proves_bytes_not_truth","signature_does_not_establish_source_claim_accuracy"])
def test_signature_boundaries(field): assert getattr(ref().integrity_attestations[0],field) is True
@pytest.mark.parametrize("field",["conflict_preserved","remote_version_does_not_silently_overwrite_local"])
def test_conflict_boundaries(field): assert getattr(ref().conflicts[0],field) is True
@pytest.mark.parametrize("field",["local_validation_required","acceptance_does_not_promote_remote_assertions","compatibility_does_not_establish_semantic_equivalence"])
def test_assessment_boundaries(field): assert getattr(ref().assessments[0],field) is True
@pytest.mark.parametrize("field",["immutable","remote_objects_remain_remote_references","later_exchange_may_supersede_snapshot","snapshot_is_not_truth_verdict"])
def test_snapshot_boundaries(field): assert getattr(ref().snapshots[0],field) is True
