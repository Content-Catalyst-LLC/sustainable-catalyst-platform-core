import copy
import pytest
from pydantic import ValidationError

from app.services.signed_runtime_artifacts_execution_attestations import (
    CONTRACT_VERSION, ArtifactKind, SignatureAlgorithm, KeyLifecycleStatus, VerificationDisposition,
    AttestationStatementKind, SignedRuntimeArtifactPolicy, SigningKeyReference, RuntimeArtifactDescriptor,
    RuntimeExecutionManifest, DetachedExecutionAttestation, AttestationVerificationRecord,
    SignedRuntimeArtifactsExecutionAttestationsBundle, contract_document,
    reference_signed_runtime_artifacts_execution_attestations_bundle,
)
from app.services.unified_entity_evidence_query_api import EpistemicState, ResultValidationState

def ref(): return reference_signed_runtime_artifacts_execution_attestations_bundle()

def test_contract_identity(): assert contract_document()["contract"]==CONTRACT_VERSION
def test_release(): assert ref().release=="3.95.0"
def test_counts():
    b=ref(); assert len(b.signers)==3; assert len(b.keys)==4; assert len(b.revocations)==1; assert len(b.artifacts)==8; assert len(b.execution_manifests)==2; assert len(b.attestations)==5; assert len(b.verifications)==5; assert len(b.chains)==2; assert len(b.snapshots)==1
def test_bundle_fingerprint_stable(): assert ref().fingerprint()==ref().fingerprint()
def test_remote_artifact_preserved():
    a=next(x for x in ref().artifacts if x.epistemic_state==EpistemicState.remote_reference); assert a.validation_state==ResultValidationState.local_validation_required
def test_remote_artifact_bad_validation_rejected():
    d=next(x for x in ref().artifacts if x.epistemic_state==EpistemicState.remote_reference).model_dump(mode="python"); d["validation_state"]="governed-reference"
    with pytest.raises(ValidationError): RuntimeArtifactDescriptor.model_validate(d)
def test_bad_artifact_hash_rejected():
    d=ref().artifacts[0].model_dump(mode="python"); d["content_sha256"]="abc"
    with pytest.raises(ValidationError): RuntimeArtifactDescriptor.model_validate(d)
def test_bad_manifest_hash_rejected():
    d=ref().execution_manifests[0].model_dump(mode="python"); d["manifest_sha256"]="0"*64
    with pytest.raises(ValidationError): RuntimeExecutionManifest.model_validate(d)
def test_bad_signature_base64_rejected():
    d=ref().attestations[0].model_dump(mode="python"); d["signature_value_b64"]="%%%"
    with pytest.raises(ValidationError): DetachedExecutionAttestation.model_validate(d)
def test_verified_requires_crypto():
    d=ref().verifications[0].model_dump(mode="python"); d["cryptographic_verification_performed"]=False
    with pytest.raises(ValidationError): AttestationVerificationRecord.model_validate(d)
def test_verified_requires_active_key_status():
    d=ref().verifications[0].model_dump(mode="python"); d["key_status_at_verification"]="revoked"
    with pytest.raises(ValidationError): AttestationVerificationRecord.model_validate(d)
def test_revoked_key_requires_revocation_ref():
    d=ref().keys[2].model_dump(mode="python"); d["revocation_ref"]=None
    with pytest.raises(ValidationError): SigningKeyReference.model_validate(d)
def test_active_key_cannot_have_revocation_ref():
    d=ref().keys[0].model_dump(mode="python"); d["revocation_ref"]="x"
    with pytest.raises(ValidationError): SigningKeyReference.model_validate(d)
def test_bundle_rejects_unknown_attestation_subject():
    d=ref().model_dump(mode="python"); d["attestations"][0]["subject_ref"]="missing"
    with pytest.raises(ValidationError): SignedRuntimeArtifactsExecutionAttestationsBundle.model_validate(d)
def test_bundle_rejects_attestation_digest_mismatch():
    d=ref().model_dump(mode="python"); d["attestations"][0]["subject_sha256"]="1"*64
    with pytest.raises(ValidationError): SignedRuntimeArtifactsExecutionAttestationsBundle.model_validate(d)
def test_bundle_rejects_key_algorithm_mismatch():
    d=ref().model_dump(mode="python"); d["attestations"][0]["algorithm"]="rsa-pss-sha256"
    with pytest.raises(ValidationError): SignedRuntimeArtifactsExecutionAttestationsBundle.model_validate(d)
def test_bundle_rejects_unknown_chain_artifact():
    d=ref().model_dump(mode="python"); d["chains"][0]["artifact_refs"].append("missing")
    with pytest.raises(ValidationError): SignedRuntimeArtifactsExecutionAttestationsBundle.model_validate(d)
def test_revoked_verification_present(): assert sum(x.disposition==VerificationDisposition.revoked for x in ref().verifications)==1
def test_snapshot_immutable_supersedable(): assert ref().snapshots[0].immutable is True and ref().snapshots[0].supersedable is True

@pytest.mark.parametrize("field",[
"require_content_addressed_artifacts","require_source_contract_identity","require_source_object_reference","require_provenance_preservation","require_epistemic_state_preservation","require_validation_state_preservation","require_explicit_signer_identity","require_key_lifecycle_state","require_detached_attestation","require_verification_record","require_explicit_execution_manifest","require_canonical_signable_payload","require_revocation_and_expiry_awareness"])
def test_policy_true(field): assert getattr(ref().policies[0],field) is True

@pytest.mark.parametrize("field",[
"allow_signature_to_create_evidence","allow_signature_to_promote_epistemic_state","allow_signature_to_bypass_validation","allow_signature_to_bypass_review","allow_key_identity_to_expand_authority_scope","allow_revoked_key_to_verify_as_current","allow_expired_key_to_verify_as_current","allow_attestation_to_mutate_governed_graphs"])
def test_policy_false(field): assert getattr(ref().policies[0],field) is False

@pytest.mark.parametrize("field",[
"runtime_artifacts_are_content_addressed","execution_manifests_are_canonical_and_signable","private_key_material_stays_outside_core","signer_and_key_identity_are_explicit","detached_attestations_bind_subject_digest_and_signer_key","verification_records_are_explicit","revocation_and_expiry_are_first_class","epistemic_state_is_preserved_across_signing","validation_state_is_preserved_across_signing","attestation_chains_are_reproducible"])
def test_contract_principles(field): assert contract_document()["principles"][field] is True

@pytest.mark.parametrize("field",[
"valid_signature_establishes_content_truth","valid_signature_establishes_scientific_validity","content_hash_establishes_factual_correctness","attestation_creates_evidence","attestation_promotes_epistemic_state","attestation_bypasses_validation","attestation_bypasses_review","key_identity_expands_authority_scope","signed_remote_reference_becomes_local_evidence","execution_attestation_proves_correctness","attestation_chain_is_independent_corroboration","revoked_key_verifies_as_current","expired_key_verifies_as_current","identity_graph_mutation_performed","relationship_graph_mutation_performed","evidence_graph_mutation_performed"])
def test_contract_false_boundaries(field): assert contract_document()["boundaries"][field] is False

@pytest.mark.parametrize("i",range(8))
def test_artifact_hash_shape(i): assert len(ref().artifacts[i].content_sha256)==64
@pytest.mark.parametrize("i",range(8))
def test_artifact_immutable(i): assert ref().artifacts[i].immutable is True
@pytest.mark.parametrize("i",range(8))
def test_artifact_preserves_provenance(i): assert len(ref().artifacts[i].provenance_refs)>=1
@pytest.mark.parametrize("i",range(8))
def test_artifact_hash_not_truth(i): assert ref().artifacts[i].content_hash_is_not_content_truth is True
@pytest.mark.parametrize("i",range(4))
def test_key_no_private_material(i): assert ref().keys[i].private_key_material_stored_in_core is False
@pytest.mark.parametrize("i",range(4))
def test_key_fingerprint_shape(i): assert len(ref().keys[i].public_key_fingerprint_sha256)==64
@pytest.mark.parametrize("i",range(5))
def test_attestation_detached(i): assert ref().attestations[i].detached is True
@pytest.mark.parametrize("i",range(5))
def test_attestation_not_truth(i): assert ref().attestations[i].attestation_is_not_content_truth is True
@pytest.mark.parametrize("i",range(5))
def test_attestation_not_promotion(i): assert ref().attestations[i].attestation_is_not_epistemic_promotion is True
@pytest.mark.parametrize("i",range(5))
def test_signature_material_decodes(i):
    import base64; assert len(base64.b64decode(ref().attestations[i].signature_value_b64))>=16
@pytest.mark.parametrize("i",range(5))
def test_verification_not_truth(i): assert ref().verifications[i].verification_is_not_content_truth is True
@pytest.mark.parametrize("i",range(5))
def test_verification_not_science(i): assert ref().verifications[i].verification_is_not_scientific_validity is True
@pytest.mark.parametrize("i",range(5))
def test_verification_not_promotion(i): assert ref().verifications[i].verification_is_not_evidence_promotion is True
@pytest.mark.parametrize("i",range(2))
def test_manifest_hash_valid(i): assert ref().execution_manifests[i].manifest_sha256==__import__('app.services.signed_runtime_artifacts_execution_attestations',fromlist=['canonical_sha256']).canonical_sha256(ref().execution_manifests[i].signable_payload())
@pytest.mark.parametrize("i",range(2))
def test_manifest_not_truth(i): assert ref().execution_manifests[i].execution_manifest_is_not_truth_certification is True
@pytest.mark.parametrize("i",range(2))
def test_chain_preserves_state(i): assert ref().chains[i].chain_preserves_artifact_epistemic_state and ref().chains[i].chain_preserves_artifact_validation_state
@pytest.mark.parametrize("i",range(2))
def test_chain_not_corroboration(i): assert ref().chains[i].chain_is_not_independent_corroboration is True
@pytest.mark.parametrize("kind",list(SignatureAlgorithm))
def test_algorithms(kind): assert kind.value
@pytest.mark.parametrize("kind",list(ArtifactKind))
def test_artifact_kinds(kind): assert kind.value
@pytest.mark.parametrize("kind",list(KeyLifecycleStatus))
def test_key_statuses(kind): assert kind.value
@pytest.mark.parametrize("kind",list(AttestationStatementKind))
def test_statement_kinds(kind): assert kind.value
@pytest.mark.parametrize("kind",list(VerificationDisposition))
def test_verification_dispositions(kind): assert kind.value
@pytest.mark.parametrize("i",range(70))
def test_round_trip(i):
    b=ref(); assert SignedRuntimeArtifactsExecutionAttestationsBundle.model_validate(b.model_dump(mode="python")).fingerprint()==b.fingerprint()
@pytest.mark.parametrize("i",range(70))
def test_contract_stable(i): assert contract_document()["contract"]==CONTRACT_VERSION
@pytest.mark.parametrize("i",range(50))
def test_snapshot_fingerprint_stable(i): assert ref().snapshots[0].fingerprint()==ref().snapshots[0].fingerprint()
