from __future__ import annotations

import base64
from enum import Enum
from functools import lru_cache
from typing import Any, Literal

from pydantic import BaseModel, Field, model_validator

from .computational_runtime_objects import canonical_sha256
from .unified_entity_evidence_query_api import EpistemicState, ResultValidationState
from .cross_product_intelligence_handoff import (
    CONTRACT_VERSION as V394_CONTRACT,
    reference_cross_product_intelligence_handoff_bundle,
)
from .investigation_session_research_context_runtime import (
    CONTRACT_VERSION as V393_CONTRACT,
    reference_investigation_session_research_context_bundle,
)
from .unified_entity_evidence_query_api import (
    CONTRACT_VERSION as V392_CONTRACT,
    reference_unified_entity_evidence_query_bundle,
)
from .unified_entity_evidence_intelligence_runtime import (
    CONTRACT_VERSION as V390_CONTRACT,
    reference_unified_entity_evidence_intelligence_runtime_bundle,
)
from .unified_runtime_policy_capability_negotiation import (
    CONTRACT_VERSION as V391_CONTRACT,
    reference_unified_runtime_policy_capability_negotiation_bundle,
)
from .federated_evidence_graph_exchange import (
    CONTRACT_VERSION as V389_CONTRACT,
    reference_federated_evidence_graph_exchange_bundle,
)
from .reproducible_graph_investigation_package import (
    CONTRACT_VERSION as V388_CONTRACT,
    reference_reproducible_graph_investigation_package_bundle,
)

CORE_RELEASE = "3.95.0"
CONTRACT_VERSION = "sc.core.signed-runtime-artifacts-execution-attestations.v1"


def _unique(values: list[str], label: str) -> None:
    if len(values) != len(set(values)):
        raise ValueError(f"{label} must be unique")


def _sha(value: str, label: str) -> str:
    v = value.lower().strip()
    if len(v) != 64 or any(c not in "0123456789abcdef" for c in v):
        raise ValueError(f"{label} must be a lowercase SHA-256 hex digest")
    return v


def _b64(value: str, label: str) -> str:
    try:
        decoded = base64.b64decode(value, validate=True)
    except Exception as exc:
        raise ValueError(f"{label} must be valid base64") from exc
    if len(decoded) < 16:
        raise ValueError(f"{label} must contain at least 16 decoded bytes")
    return value


class SignatureAlgorithm(str, Enum):
    ed25519 = "ed25519"
    ecdsa_p256_sha256 = "ecdsa-p256-sha256"
    rsa_pss_sha256 = "rsa-pss-sha256"


class ArtifactKind(str, Enum):
    runtime_trace = "runtime-trace"
    query_result_set = "query-result-set"
    session_checkpoint = "session-checkpoint"
    session_snapshot = "session-snapshot"
    handoff_trace = "handoff-trace"
    investigation_package = "investigation-package"
    federation_snapshot = "federation-snapshot"
    capability_negotiation_trace = "capability-negotiation-trace"


class KeyLifecycleStatus(str, Enum):
    active = "active"
    revoked = "revoked"
    expired = "expired"


class AttestationStatementKind(str, Enum):
    artifact_integrity = "artifact-integrity"
    execution_provenance = "execution-provenance"
    environment_binding = "environment-binding"
    cross_product_handoff = "cross-product-handoff"


class VerificationDisposition(str, Enum):
    verified = "verified"
    verified_with_qualifications = "verified-with-qualifications"
    invalid = "invalid"
    unverifiable = "unverifiable"
    revoked = "revoked"
    expired = "expired"


class SignedRuntimeArtifactPolicy(BaseModel):
    policy_id: str = Field(min_length=3, max_length=500)
    require_content_addressed_artifacts: Literal[True] = True
    require_source_contract_identity: Literal[True] = True
    require_source_object_reference: Literal[True] = True
    require_provenance_preservation: Literal[True] = True
    require_epistemic_state_preservation: Literal[True] = True
    require_validation_state_preservation: Literal[True] = True
    require_explicit_signer_identity: Literal[True] = True
    require_key_lifecycle_state: Literal[True] = True
    require_detached_attestation: Literal[True] = True
    require_verification_record: Literal[True] = True
    require_explicit_execution_manifest: Literal[True] = True
    require_canonical_signable_payload: Literal[True] = True
    require_revocation_and_expiry_awareness: Literal[True] = True
    allow_signature_to_create_evidence: Literal[False] = False
    allow_signature_to_promote_epistemic_state: Literal[False] = False
    allow_signature_to_bypass_validation: Literal[False] = False
    allow_signature_to_bypass_review: Literal[False] = False
    allow_key_identity_to_expand_authority_scope: Literal[False] = False
    allow_revoked_key_to_verify_as_current: Literal[False] = False
    allow_expired_key_to_verify_as_current: Literal[False] = False
    allow_attestation_to_mutate_governed_graphs: Literal[False] = False
    metadata: dict[str, Any] = Field(default_factory=dict)

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class SignerIdentityReference(BaseModel):
    signer_id: str = Field(min_length=3, max_length=500)
    principal_kind: Literal["service", "operator", "federation-node", "system"]
    display_name: str = Field(min_length=2, max_length=500)
    authority_scopes: list[str] = Field(min_length=1)
    signer_identity_is_not_content_truth: Literal[True] = True
    signer_identity_does_not_expand_object_authority: Literal[True] = True
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_signer(self):
        _unique(self.authority_scopes, "authority_scopes")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class SigningKeyReference(BaseModel):
    key_ref: str = Field(min_length=3, max_length=500)
    signer_ref: str = Field(min_length=3, max_length=500)
    algorithm: SignatureAlgorithm
    key_version: str = Field(min_length=1, max_length=120)
    public_key_fingerprint_sha256: str
    issued_at: str = Field(min_length=10, max_length=80)
    not_before: str = Field(min_length=10, max_length=80)
    expires_at: str = Field(min_length=10, max_length=80)
    status: KeyLifecycleStatus
    revocation_ref: str | None = Field(default=None, max_length=500)
    private_key_material_stored_in_core: Literal[False] = False
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_key(self):
        self.public_key_fingerprint_sha256 = _sha(self.public_key_fingerprint_sha256, "public_key_fingerprint_sha256")
        if self.status == KeyLifecycleStatus.revoked and not self.revocation_ref:
            raise ValueError("revoked key requires revocation_ref")
        if self.status == KeyLifecycleStatus.active and self.revocation_ref:
            raise ValueError("active key cannot have revocation_ref")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class KeyRevocationRecord(BaseModel):
    revocation_id: str = Field(min_length=3, max_length=500)
    key_ref: str = Field(min_length=3, max_length=500)
    revoked_at: str = Field(min_length=10, max_length=80)
    reason: str = Field(min_length=3, max_length=1000)
    superseding_key_ref: str | None = Field(default=None, max_length=500)
    revocation_requires_future_verifications_to_reflect_status: Literal[True] = True
    revocation_does_not_rewrite_historical_artifact_bytes: Literal[True] = True
    metadata: dict[str, Any] = Field(default_factory=dict)

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class RuntimeArtifactDescriptor(BaseModel):
    artifact_id: str = Field(min_length=3, max_length=500)
    artifact_kind: ArtifactKind
    source_contract: str = Field(min_length=3, max_length=500)
    source_object_ref: str = Field(min_length=3, max_length=1000)
    media_type: str = Field(min_length=3, max_length=255)
    content_sha256: str
    byte_length: int = Field(ge=1)
    generated_at: str = Field(min_length=10, max_length=80)
    provenance_refs: list[str] = Field(min_length=1)
    epistemic_state: EpistemicState
    validation_state: ResultValidationState
    immutable: Literal[True] = True
    content_hash_is_not_content_truth: Literal[True] = True
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_artifact(self):
        self.content_sha256 = _sha(self.content_sha256, "content_sha256")
        _unique(self.provenance_refs, "provenance_refs")
        if self.epistemic_state == EpistemicState.remote_reference and self.validation_state != ResultValidationState.local_validation_required:
            raise ValueError("remote-reference artifact requires local-validation-required")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class RuntimeExecutionManifest(BaseModel):
    execution_manifest_id: str = Field(min_length=3, max_length=500)
    runtime_release: str = Field(min_length=1, max_length=120)
    runtime_contract: str = Field(min_length=3, max_length=500)
    request_ref: str = Field(min_length=3, max_length=1000)
    input_artifact_refs: list[str] = Field(min_length=1)
    output_artifact_refs: list[str] = Field(min_length=1)
    policy_refs: list[str] = Field(min_length=1)
    capability_contracts: list[str] = Field(min_length=1)
    execution_trace_refs: list[str] = Field(min_length=1)
    environment_fingerprint_sha256: str
    started_at: str = Field(min_length=10, max_length=80)
    completed_at: str = Field(min_length=10, max_length=80)
    manifest_sha256: str
    execution_manifest_is_not_correctness_certification: Literal[True] = True
    execution_manifest_is_not_truth_certification: Literal[True] = True
    metadata: dict[str, Any] = Field(default_factory=dict)

    def signable_payload(self) -> dict[str, Any]:
        return self.model_dump(mode="json", exclude={"manifest_sha256"}, exclude_none=True)

    @model_validator(mode="after")
    def validate_manifest(self):
        for label, values in [
            ("input_artifact_refs", self.input_artifact_refs),
            ("output_artifact_refs", self.output_artifact_refs),
            ("policy_refs", self.policy_refs),
            ("capability_contracts", self.capability_contracts),
            ("execution_trace_refs", self.execution_trace_refs),
        ]:
            _unique(values, label)
        self.environment_fingerprint_sha256 = _sha(self.environment_fingerprint_sha256, "environment_fingerprint_sha256")
        self.manifest_sha256 = _sha(self.manifest_sha256, "manifest_sha256")
        if self.manifest_sha256 != canonical_sha256(self.signable_payload()):
            raise ValueError("manifest_sha256 does not match canonical signable payload")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class DetachedExecutionAttestation(BaseModel):
    attestation_id: str = Field(min_length=3, max_length=500)
    statement_kind: AttestationStatementKind
    subject_ref: str = Field(min_length=3, max_length=1000)
    subject_sha256: str
    signer_ref: str = Field(min_length=3, max_length=500)
    key_ref: str = Field(min_length=3, max_length=500)
    algorithm: SignatureAlgorithm
    canonicalization: Literal["sc-canonical-json-v1"] = "sc-canonical-json-v1"
    signature_encoding: Literal["base64"] = "base64"
    signature_value_b64: str
    signing_provider_ref: str = Field(min_length=3, max_length=500)
    signed_at: str = Field(min_length=10, max_length=80)
    detached: Literal[True] = True
    attestation_asserts_integrity_and_signer_association_only: Literal[True] = True
    attestation_is_not_content_truth: Literal[True] = True
    attestation_is_not_epistemic_promotion: Literal[True] = True
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_attestation(self):
        self.subject_sha256 = _sha(self.subject_sha256, "subject_sha256")
        self.signature_value_b64 = _b64(self.signature_value_b64, "signature_value_b64")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class AttestationVerificationRecord(BaseModel):
    verification_id: str = Field(min_length=3, max_length=500)
    attestation_ref: str = Field(min_length=3, max_length=500)
    subject_ref: str = Field(min_length=3, max_length=1000)
    expected_subject_sha256: str
    observed_subject_sha256: str
    key_ref: str = Field(min_length=3, max_length=500)
    verified_at: str = Field(min_length=10, max_length=80)
    cryptographic_verification_performed: bool
    signature_matches: bool
    key_status_at_verification: KeyLifecycleStatus
    disposition: VerificationDisposition
    qualifications: list[str] = Field(min_length=1)
    verification_is_not_content_truth: Literal[True] = True
    verification_is_not_scientific_validity: Literal[True] = True
    verification_is_not_evidence_promotion: Literal[True] = True
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_verification(self):
        self.expected_subject_sha256 = _sha(self.expected_subject_sha256, "expected_subject_sha256")
        self.observed_subject_sha256 = _sha(self.observed_subject_sha256, "observed_subject_sha256")
        _unique(self.qualifications, "qualifications")
        if self.disposition in {VerificationDisposition.verified, VerificationDisposition.verified_with_qualifications}:
            if not self.cryptographic_verification_performed or not self.signature_matches:
                raise ValueError("verified disposition requires cryptographic verification and matching signature")
            if self.expected_subject_sha256 != self.observed_subject_sha256:
                raise ValueError("verified disposition requires matching subject digest")
            if self.key_status_at_verification != KeyLifecycleStatus.active:
                raise ValueError("verified disposition requires active key")
        if self.key_status_at_verification == KeyLifecycleStatus.revoked and self.disposition != VerificationDisposition.revoked:
            raise ValueError("revoked key requires revoked verification disposition")
        if self.key_status_at_verification == KeyLifecycleStatus.expired and self.disposition != VerificationDisposition.expired:
            raise ValueError("expired key requires expired verification disposition")
        if not self.signature_matches and self.disposition not in {VerificationDisposition.invalid, VerificationDisposition.unverifiable}:
            raise ValueError("non-matching signature requires invalid/unverifiable disposition")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class ExecutionAttestationChain(BaseModel):
    chain_id: str = Field(min_length=3, max_length=500)
    execution_manifest_ref: str = Field(min_length=3, max_length=500)
    artifact_refs: list[str] = Field(min_length=1)
    attestation_refs: list[str] = Field(min_length=1)
    verification_refs: list[str] = Field(min_length=1)
    parent_chain_ref: str | None = Field(default=None, max_length=500)
    chain_root_sha256: str
    chain_preserves_artifact_epistemic_state: Literal[True] = True
    chain_preserves_artifact_validation_state: Literal[True] = True
    chain_is_not_independent_corroboration: Literal[True] = True
    chain_is_not_truth_certification: Literal[True] = True
    immutable: Literal[True] = True
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_chain(self):
        for label, values in [("artifact_refs",self.artifact_refs),("attestation_refs",self.attestation_refs),("verification_refs",self.verification_refs)]:
            _unique(values, label)
        self.chain_root_sha256 = _sha(self.chain_root_sha256, "chain_root_sha256")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class SignedRuntimeAttestationSnapshot(BaseModel):
    snapshot_id: str = Field(min_length=3, max_length=500)
    policy_ref: str = Field(min_length=3, max_length=500)
    signer_refs: list[str] = Field(min_length=1)
    key_refs: list[str] = Field(min_length=1)
    artifact_refs: list[str] = Field(min_length=1)
    execution_manifest_refs: list[str] = Field(min_length=1)
    attestation_refs: list[str] = Field(min_length=1)
    verification_refs: list[str] = Field(min_length=1)
    chain_refs: list[str] = Field(min_length=1)
    as_of: str = Field(min_length=10, max_length=80)
    immutable: Literal[True] = True
    supersedable: Literal[True] = True
    snapshot_is_not_truth_certification: Literal[True] = True
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_snapshot(self):
        for label, values in [
            ("signer_refs",self.signer_refs),("key_refs",self.key_refs),("artifact_refs",self.artifact_refs),
            ("execution_manifest_refs",self.execution_manifest_refs),("attestation_refs",self.attestation_refs),
            ("verification_refs",self.verification_refs),("chain_refs",self.chain_refs),
        ]: _unique(values,label)
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class SignedRuntimeArtifactsExecutionAttestationsBundle(BaseModel):
    release: Literal["3.95.0"] = "3.95.0"
    contract: Literal["sc.core.signed-runtime-artifacts-execution-attestations.v1"] = CONTRACT_VERSION
    policies: list[SignedRuntimeArtifactPolicy] = Field(min_length=1)
    signers: list[SignerIdentityReference] = Field(min_length=1)
    keys: list[SigningKeyReference] = Field(min_length=1)
    revocations: list[KeyRevocationRecord] = Field(default_factory=list)
    artifacts: list[RuntimeArtifactDescriptor] = Field(min_length=1)
    execution_manifests: list[RuntimeExecutionManifest] = Field(min_length=1)
    attestations: list[DetachedExecutionAttestation] = Field(min_length=1)
    verifications: list[AttestationVerificationRecord] = Field(min_length=1)
    chains: list[ExecutionAttestationChain] = Field(min_length=1)
    snapshots: list[SignedRuntimeAttestationSnapshot] = Field(min_length=1)
    identity_graph_mutation_performed: Literal[False] = False
    relationship_graph_mutation_performed: Literal[False] = False
    evidence_graph_mutation_performed: Literal[False] = False

    @model_validator(mode="after")
    def validate_bundle(self):
        groups = {
            "policies":[x.policy_id for x in self.policies], "signers":[x.signer_id for x in self.signers],
            "keys":[x.key_ref for x in self.keys], "revocations":[x.revocation_id for x in self.revocations],
            "artifacts":[x.artifact_id for x in self.artifacts], "execution_manifests":[x.execution_manifest_id for x in self.execution_manifests],
            "attestations":[x.attestation_id for x in self.attestations], "verifications":[x.verification_id for x in self.verifications],
            "chains":[x.chain_id for x in self.chains], "snapshots":[x.snapshot_id for x in self.snapshots],
        }
        for label, values in groups.items(): _unique(values,label)
        signers={x.signer_id:x for x in self.signers}; keys={x.key_ref:x for x in self.keys}; revs={x.revocation_id:x for x in self.revocations}
        artifacts={x.artifact_id:x for x in self.artifacts}; manifests={x.execution_manifest_id:x for x in self.execution_manifests}
        atts={x.attestation_id:x for x in self.attestations}; vers={x.verification_id:x for x in self.verifications}; chains={x.chain_id:x for x in self.chains}
        for k in self.keys:
            if k.signer_ref not in signers: raise ValueError("key signer_ref missing")
            if k.revocation_ref and k.revocation_ref not in revs: raise ValueError("key revocation_ref missing")
        for r in self.revocations:
            if r.key_ref not in keys: raise ValueError("revocation key_ref missing")
        all_subjects={a.artifact_id:a.content_sha256 for a in self.artifacts}|{m.execution_manifest_id:m.manifest_sha256 for m in self.execution_manifests}
        for m in self.execution_manifests:
            if not set(m.input_artifact_refs).issubset(artifacts): raise ValueError("manifest input artifact missing")
            if not set(m.output_artifact_refs).issubset(artifacts): raise ValueError("manifest output artifact missing")
        for a in self.attestations:
            if a.signer_ref not in signers or a.key_ref not in keys: raise ValueError("attestation signer/key missing")
            k=keys[a.key_ref]
            if k.signer_ref != a.signer_ref: raise ValueError("attestation signer/key mismatch")
            if k.algorithm != a.algorithm: raise ValueError("attestation algorithm/key mismatch")
            if a.subject_ref not in all_subjects: raise ValueError("attestation subject missing")
            if a.subject_sha256 != all_subjects[a.subject_ref]: raise ValueError("attestation subject digest mismatch")
        for v in self.verifications:
            if v.attestation_ref not in atts or v.key_ref not in keys: raise ValueError("verification attestation/key missing")
            a=atts[v.attestation_ref]
            if v.key_ref != a.key_ref or v.subject_ref != a.subject_ref: raise ValueError("verification subject/key mismatch")
            if v.expected_subject_sha256 != a.subject_sha256: raise ValueError("verification expected digest mismatch")
        for c in self.chains:
            if c.execution_manifest_ref not in manifests: raise ValueError("chain manifest missing")
            if not set(c.artifact_refs).issubset(artifacts): raise ValueError("chain artifact missing")
            if not set(c.attestation_refs).issubset(atts): raise ValueError("chain attestation missing")
            if not set(c.verification_refs).issubset(vers): raise ValueError("chain verification missing")
            if c.parent_chain_ref and c.parent_chain_ref not in chains: raise ValueError("chain parent missing")
        for s in self.snapshots:
            if s.policy_ref not in groups["policies"]: raise ValueError("snapshot policy missing")
            if not set(s.signer_refs).issubset(signers): raise ValueError("snapshot signer missing")
            if not set(s.key_refs).issubset(keys): raise ValueError("snapshot key missing")
            if not set(s.artifact_refs).issubset(artifacts): raise ValueError("snapshot artifact missing")
            if not set(s.execution_manifest_refs).issubset(manifests): raise ValueError("snapshot manifest missing")
            if not set(s.attestation_refs).issubset(atts): raise ValueError("snapshot attestation missing")
            if not set(s.verification_refs).issubset(vers): raise ValueError("snapshot verification missing")
            if not set(s.chain_refs).issubset(chains): raise ValueError("snapshot chain missing")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


def _artifact(artifact_id: str, kind: ArtifactKind, contract: str, object_ref: str, seed: Any, epistemic: EpistemicState, validation: ResultValidationState, provenance: list[str], byte_length: int) -> RuntimeArtifactDescriptor:
    return RuntimeArtifactDescriptor(
        artifact_id=artifact_id, artifact_kind=kind, source_contract=contract, source_object_ref=object_ref,
        media_type="application/vnd.sustainable-catalyst.runtime-object+json", content_sha256=canonical_sha256(seed),
        byte_length=byte_length, generated_at="2026-10-01T04:05:00Z", provenance_refs=provenance,
        epistemic_state=epistemic, validation_state=validation,
    )


def _manifest(**kwargs: Any) -> RuntimeExecutionManifest:
    base={**kwargs, "manifest_sha256":"0"*64}
    m=RuntimeExecutionManifest.model_construct(**base)
    base["manifest_sha256"]=canonical_sha256(m.signable_payload())
    return RuntimeExecutionManifest.model_validate(base)


def _sig(seed: Any) -> str:
    return base64.b64encode(bytes.fromhex(canonical_sha256(seed))).decode("ascii")


@lru_cache(maxsize=1)
def reference_signed_runtime_artifacts_execution_attestations_bundle() -> SignedRuntimeArtifactsExecutionAttestationsBundle:
    v394=reference_cross_product_intelligence_handoff_bundle(); v393=reference_investigation_session_research_context_bundle()
    v392=reference_unified_entity_evidence_query_bundle(); v390=reference_unified_entity_evidence_intelligence_runtime_bundle()
    v391=reference_unified_runtime_policy_capability_negotiation_bundle(); v389=reference_federated_evidence_graph_exchange_bundle()
    v388=reference_reproducible_graph_investigation_package_bundle()
    policy=SignedRuntimeArtifactPolicy(policy_id="signed-runtime-artifact-policy:default:v1")
    signers=[
        SignerIdentityReference(signer_id="signer:platform-core-runtime",principal_kind="service",display_name="Sustainable Catalyst Platform Core Runtime",authority_scopes=["attest:runtime-artifact","attest:execution-manifest"]),
        SignerIdentityReference(signer_id="signer:release-operator",principal_kind="operator",display_name="Sustainable Catalyst Release Operator",authority_scopes=["attest:release-manifest"]),
        SignerIdentityReference(signer_id="signer:federation-node-alpha",principal_kind="federation-node",display_name="Reference Federation Node Alpha",authority_scopes=["attest:federated-reference"]),
    ]
    rev=KeyRevocationRecord(revocation_id="key-revocation:federation-node-alpha:v1",key_ref="key:federation-node-alpha:v1",revoked_at="2026-09-30T23:50:00Z",reason="synthetic key rotation demonstration",superseding_key_ref="key:federation-node-alpha:v2")
    keys=[
        SigningKeyReference(key_ref="key:platform-core-runtime:v1",signer_ref=signers[0].signer_id,algorithm=SignatureAlgorithm.ed25519,key_version="1",public_key_fingerprint_sha256=canonical_sha256("platform-core-runtime-public-key-v1"),issued_at="2026-09-01T00:00:00Z",not_before="2026-09-01T00:00:00Z",expires_at="2027-09-01T00:00:00Z",status=KeyLifecycleStatus.active),
        SigningKeyReference(key_ref="key:release-operator:v1",signer_ref=signers[1].signer_id,algorithm=SignatureAlgorithm.ed25519,key_version="1",public_key_fingerprint_sha256=canonical_sha256("release-operator-public-key-v1"),issued_at="2026-09-01T00:00:00Z",not_before="2026-09-01T00:00:00Z",expires_at="2027-09-01T00:00:00Z",status=KeyLifecycleStatus.active),
        SigningKeyReference(key_ref="key:federation-node-alpha:v1",signer_ref=signers[2].signer_id,algorithm=SignatureAlgorithm.ed25519,key_version="1",public_key_fingerprint_sha256=canonical_sha256("federation-node-alpha-public-key-v1"),issued_at="2026-06-01T00:00:00Z",not_before="2026-06-01T00:00:00Z",expires_at="2027-06-01T00:00:00Z",status=KeyLifecycleStatus.revoked,revocation_ref=rev.revocation_id),
        SigningKeyReference(key_ref="key:federation-node-alpha:v2",signer_ref=signers[2].signer_id,algorithm=SignatureAlgorithm.ed25519,key_version="2",public_key_fingerprint_sha256=canonical_sha256("federation-node-alpha-public-key-v2"),issued_at="2026-09-30T23:50:00Z",not_before="2026-09-30T23:50:00Z",expires_at="2027-09-30T23:50:00Z",status=KeyLifecycleStatus.active),
    ]
    artifacts=[
        _artifact("runtime-artifact:unified-runtime-trace:v1",ArtifactKind.runtime_trace,V390_CONTRACT,v390.traces[0].unified_runtime_execution_trace_id,v390.traces[0],EpistemicState.analytical,ResultValidationState.analytical_only,[v390.traces[0].unified_runtime_execution_trace_id],1800),
        _artifact("runtime-artifact:query-result-set:v1",ArtifactKind.query_result_set,V392_CONTRACT,v392.result_sets[0].result_set_id,v392.result_sets[0],EpistemicState.qualified,ResultValidationState.governed_reference,[v392.traces[0].trace_id],2400),
        _artifact("runtime-artifact:session-checkpoint:v1",ArtifactKind.session_checkpoint,V393_CONTRACT,v393.checkpoints[0].checkpoint_id,v393.checkpoints[0],EpistemicState.qualified,ResultValidationState.governed_reference,[v393.traces[0].trace_id],2100),
        _artifact("runtime-artifact:session-snapshot:v1",ArtifactKind.session_snapshot,V393_CONTRACT,v393.snapshots[0].snapshot_id,v393.snapshots[0],EpistemicState.qualified,ResultValidationState.governed_reference,[v393.checkpoints[0].checkpoint_id],1900),
        _artifact("runtime-artifact:handoff-trace:v1",ArtifactKind.handoff_trace,V394_CONTRACT,v394.traces[0].trace_id,v394.traces[0],EpistemicState.runtime_metadata,ResultValidationState.metadata_only,[v394.requests[0].request_id,v394.receipts[0].receipt_id],1700),
        _artifact("runtime-artifact:investigation-package:v1",ArtifactKind.investigation_package,V388_CONTRACT,v388.snapshots[0].graph_investigation_snapshot_id,v388.snapshots[0],EpistemicState.qualified,ResultValidationState.governed_reference,[v388.manifests[0].investigation_manifest_id],3600),
        _artifact("runtime-artifact:federation-snapshot:v1",ArtifactKind.federation_snapshot,V389_CONTRACT,v389.snapshots[0].federation_exchange_snapshot_id,v389.snapshots[0],EpistemicState.remote_reference,ResultValidationState.local_validation_required,[v389.manifests[0].exchange_manifest_id],2200),
        _artifact("runtime-artifact:capability-negotiation:v1",ArtifactKind.capability_negotiation_trace,V391_CONTRACT,v391.traces[0].trace_id,v391.traces[0],EpistemicState.runtime_metadata,ResultValidationState.metadata_only,[v391.policies[0].policy_id],1600),
    ]
    env=canonical_sha256({"core_release":CORE_RELEASE,"python":"3.12","contract":CONTRACT_VERSION,"mode":"provider-neutral-signing"})
    m1=_manifest(execution_manifest_id="execution-manifest:entity-evidence-query-session:v1",runtime_release=CORE_RELEASE,runtime_contract=CONTRACT_VERSION,request_ref=v392.queries[0].query_id,input_artifact_refs=[artifacts[0].artifact_id,artifacts[7].artifact_id],output_artifact_refs=[artifacts[1].artifact_id,artifacts[2].artifact_id,artifacts[3].artifact_id],policy_refs=[policy.policy_id],capability_contracts=[V390_CONTRACT,V391_CONTRACT,V392_CONTRACT,V393_CONTRACT],execution_trace_refs=[v390.traces[0].unified_runtime_execution_trace_id,v392.traces[0].trace_id,v393.traces[0].trace_id],environment_fingerprint_sha256=env,started_at="2026-10-01T04:05:00Z",completed_at="2026-10-01T04:05:02Z")
    m2=_manifest(execution_manifest_id="execution-manifest:cross-product-handoff:v1",runtime_release=CORE_RELEASE,runtime_contract=CONTRACT_VERSION,request_ref=v394.requests[0].request_id,input_artifact_refs=[artifacts[2].artifact_id,artifacts[3].artifact_id,artifacts[6].artifact_id],output_artifact_refs=[artifacts[4].artifact_id,artifacts[5].artifact_id],policy_refs=[policy.policy_id],capability_contracts=[V393_CONTRACT,V394_CONTRACT,V388_CONTRACT,V389_CONTRACT],execution_trace_refs=[v394.traces[0].trace_id],environment_fingerprint_sha256=env,started_at="2026-10-01T04:05:03Z",completed_at="2026-10-01T04:05:04Z")
    manifests=[m1,m2]
    def att(aid,kind,subject_ref,subject_sha,signer,key,signed_at,provider):
        return DetachedExecutionAttestation(attestation_id=aid,statement_kind=kind,subject_ref=subject_ref,subject_sha256=subject_sha,signer_ref=signer,key_ref=key.key_ref,algorithm=key.algorithm,signature_value_b64=_sig({"subject":subject_sha,"key":key.public_key_fingerprint_sha256,"time":signed_at}),signing_provider_ref=provider,signed_at=signed_at)
    atts=[
        att("attestation:execution-manifest-query:v1",AttestationStatementKind.execution_provenance,m1.execution_manifest_id,m1.manifest_sha256,signers[0].signer_id,keys[0],"2026-10-01T04:05:05Z","signing-provider:platform-core"),
        att("attestation:execution-manifest-handoff:v1",AttestationStatementKind.execution_provenance,m2.execution_manifest_id,m2.manifest_sha256,signers[0].signer_id,keys[0],"2026-10-01T04:05:06Z","signing-provider:platform-core"),
        att("attestation:session-snapshot:v1",AttestationStatementKind.artifact_integrity,artifacts[3].artifact_id,artifacts[3].content_sha256,signers[1].signer_id,keys[1],"2026-10-01T04:05:07Z","signing-provider:release-operator"),
        att("attestation:federation-snapshot:historical:v1",AttestationStatementKind.artifact_integrity,artifacts[6].artifact_id,artifacts[6].content_sha256,signers[2].signer_id,keys[2],"2026-09-30T23:40:00Z","signing-provider:federation-node-alpha"),
        att("attestation:federation-snapshot:current:v2",AttestationStatementKind.artifact_integrity,artifacts[6].artifact_id,artifacts[6].content_sha256,signers[2].signer_id,keys[3],"2026-10-01T04:05:08Z","signing-provider:federation-node-alpha"),
    ]
    vers=[
        AttestationVerificationRecord(verification_id="verification:query-manifest:v1",attestation_ref=atts[0].attestation_id,subject_ref=m1.execution_manifest_id,expected_subject_sha256=m1.manifest_sha256,observed_subject_sha256=m1.manifest_sha256,key_ref=keys[0].key_ref,verified_at="2026-10-01T04:05:10Z",cryptographic_verification_performed=True,signature_matches=True,key_status_at_verification=KeyLifecycleStatus.active,disposition=VerificationDisposition.verified,qualifications=["integrity-and-signer-association-only"]),
        AttestationVerificationRecord(verification_id="verification:handoff-manifest:v1",attestation_ref=atts[1].attestation_id,subject_ref=m2.execution_manifest_id,expected_subject_sha256=m2.manifest_sha256,observed_subject_sha256=m2.manifest_sha256,key_ref=keys[0].key_ref,verified_at="2026-10-01T04:05:11Z",cryptographic_verification_performed=True,signature_matches=True,key_status_at_verification=KeyLifecycleStatus.active,disposition=VerificationDisposition.verified,qualifications=["integrity-and-signer-association-only"]),
        AttestationVerificationRecord(verification_id="verification:session-snapshot:v1",attestation_ref=atts[2].attestation_id,subject_ref=artifacts[3].artifact_id,expected_subject_sha256=artifacts[3].content_sha256,observed_subject_sha256=artifacts[3].content_sha256,key_ref=keys[1].key_ref,verified_at="2026-10-01T04:05:12Z",cryptographic_verification_performed=True,signature_matches=True,key_status_at_verification=KeyLifecycleStatus.active,disposition=VerificationDisposition.verified_with_qualifications,qualifications=["integrity-only","does-not-certify-research-validity"]),
        AttestationVerificationRecord(verification_id="verification:federation-historical:v1",attestation_ref=atts[3].attestation_id,subject_ref=artifacts[6].artifact_id,expected_subject_sha256=artifacts[6].content_sha256,observed_subject_sha256=artifacts[6].content_sha256,key_ref=keys[2].key_ref,verified_at="2026-10-01T04:05:13Z",cryptographic_verification_performed=True,signature_matches=True,key_status_at_verification=KeyLifecycleStatus.revoked,disposition=VerificationDisposition.revoked,qualifications=["key-revoked-after-historical-signature","remote-reference-remains-local-validation-required"]),
        AttestationVerificationRecord(verification_id="verification:federation-current:v2",attestation_ref=atts[4].attestation_id,subject_ref=artifacts[6].artifact_id,expected_subject_sha256=artifacts[6].content_sha256,observed_subject_sha256=artifacts[6].content_sha256,key_ref=keys[3].key_ref,verified_at="2026-10-01T04:05:14Z",cryptographic_verification_performed=True,signature_matches=True,key_status_at_verification=KeyLifecycleStatus.active,disposition=VerificationDisposition.verified_with_qualifications,qualifications=["remote-reference-only","local-validation-required-before-promotion"]),
    ]
    c1seed={"manifest":m1.manifest_sha256,"artifacts":[artifacts[i].content_sha256 for i in [0,1,2,3,7]],"attestations":[x.fingerprint() for x in atts[:3]],"verifications":[x.fingerprint() for x in vers[:3]]}
    c1=ExecutionAttestationChain(chain_id="attestation-chain:query-session:v1",execution_manifest_ref=m1.execution_manifest_id,artifact_refs=[artifacts[i].artifact_id for i in [0,1,2,3,7]],attestation_refs=[x.attestation_id for x in atts[:3]],verification_refs=[x.verification_id for x in vers[:3]],chain_root_sha256=canonical_sha256(c1seed))
    c2seed={"manifest":m2.manifest_sha256,"artifacts":[artifacts[i].content_sha256 for i in [2,3,4,5,6]],"attestations":[x.fingerprint() for x in atts[3:]],"verifications":[x.fingerprint() for x in vers[3:]],"parent":c1.chain_root_sha256}
    c2=ExecutionAttestationChain(chain_id="attestation-chain:cross-product-handoff:v1",execution_manifest_ref=m2.execution_manifest_id,artifact_refs=[artifacts[i].artifact_id for i in [2,3,4,5,6]],attestation_refs=[x.attestation_id for x in atts[3:]],verification_refs=[x.verification_id for x in vers[3:]],parent_chain_ref=c1.chain_id,chain_root_sha256=canonical_sha256(c2seed))
    snap=SignedRuntimeAttestationSnapshot(snapshot_id="signed-runtime-attestation-snapshot:synthetic:v1",policy_ref=policy.policy_id,signer_refs=[x.signer_id for x in signers],key_refs=[x.key_ref for x in keys],artifact_refs=[x.artifact_id for x in artifacts],execution_manifest_refs=[x.execution_manifest_id for x in manifests],attestation_refs=[x.attestation_id for x in atts],verification_refs=[x.verification_id for x in vers],chain_refs=[c1.chain_id,c2.chain_id],as_of="2026-10-01T04:05:15Z")
    return SignedRuntimeArtifactsExecutionAttestationsBundle(policies=[policy],signers=signers,keys=keys,revocations=[rev],artifacts=artifacts,execution_manifests=manifests,attestations=atts,verifications=vers,chains=[c1,c2],snapshots=[snap])


def contract_document() -> dict[str, Any]:
    b=reference_signed_runtime_artifacts_execution_attestations_bundle()
    return {
        "ok":True,"release":CORE_RELEASE,"contract":CONTRACT_VERSION,
        "upstream_contracts":{"investigation_package":V388_CONTRACT,"federation_exchange":V389_CONTRACT,"unified_runtime":V390_CONTRACT,"capability_negotiation":V391_CONTRACT,"query_api":V392_CONTRACT,"investigation_session":V393_CONTRACT,"cross_product_handoff":V394_CONTRACT},
        "principles":{
            "runtime_artifacts_are_content_addressed":True,"execution_manifests_are_canonical_and_signable":True,
            "private_key_material_stays_outside_core":True,"signer_and_key_identity_are_explicit":True,
            "detached_attestations_bind_subject_digest_and_signer_key":True,"verification_records_are_explicit":True,
            "revocation_and_expiry_are_first_class":True,"epistemic_state_is_preserved_across_signing":True,
            "validation_state_is_preserved_across_signing":True,"attestation_chains_are_reproducible":True,
        },
        "boundaries":{
            "valid_signature_establishes_content_truth":False,"valid_signature_establishes_scientific_validity":False,
            "content_hash_establishes_factual_correctness":False,"attestation_creates_evidence":False,
            "attestation_promotes_epistemic_state":False,"attestation_bypasses_validation":False,
            "attestation_bypasses_review":False,"key_identity_expands_authority_scope":False,
            "signed_remote_reference_becomes_local_evidence":False,"execution_attestation_proves_correctness":False,
            "attestation_chain_is_independent_corroboration":False,"revoked_key_verifies_as_current":False,
            "expired_key_verifies_as_current":False,"identity_graph_mutation_performed":False,
            "relationship_graph_mutation_performed":False,"evidence_graph_mutation_performed":False,
        },
        "reference":{"policies":len(b.policies),"signers":len(b.signers),"keys":len(b.keys),"revocations":len(b.revocations),"artifacts":len(b.artifacts),"execution_manifests":len(b.execution_manifests),"attestations":len(b.attestations),"verifications":len(b.verifications),"chains":len(b.chains),"snapshots":len(b.snapshots),"revoked_verifications":sum(1 for x in b.verifications if x.disposition==VerificationDisposition.revoked),"remote_reference_artifacts":sum(1 for x in b.artifacts if x.epistemic_state==EpistemicState.remote_reference),"bundle_fingerprint_sha256":b.fingerprint()},
        "database_migration":"none",
    }
