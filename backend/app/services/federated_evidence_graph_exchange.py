from __future__ import annotations

from enum import Enum
from typing import Any, Literal
from pydantic import BaseModel, Field, model_validator

from .computational_runtime_objects import canonical_sha256
from .reproducible_graph_investigation_package import (
    CONTRACT_VERSION as UPSTREAM_PACKAGE_CONTRACT_VERSION,
    reference_reproducible_graph_investigation_package_bundle,
)

CORE_RELEASE = "3.89.0"
CONTRACT_VERSION = "sc.core.federated-evidence-graph-exchange.v1"


def _unique(values: list[str], label: str) -> None:
    if len(values) != len(set(values)):
        raise ValueError(f"{label} must be unique")


class NodeTrustState(str, Enum):
    registered = "registered"
    authenticated = "authenticated"
    suspended = "suspended"
    revoked = "revoked"


class ExchangeDirection(str, Enum):
    export = "export"
    import_ = "import"


class ExchangeDisposition(str, Enum):
    reference_only = "reference-only"
    accepted_for_local_validation = "accepted-for-local-validation"
    quarantined = "quarantined"
    rejected = "rejected"


class ConflictDisposition(str, Enum):
    unresolved = "unresolved"
    locally_qualified = "locally-qualified"
    superseded_remote_version = "superseded-remote-version"


class FederationNodeIdentity(BaseModel):
    federation_node_id: str = Field(min_length=2, max_length=500)
    node_uri: str = Field(min_length=3, max_length=2000)
    operator_name: str = Field(min_length=2, max_length=1000)
    public_key_fingerprint_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    trust_state: NodeTrustState
    registered_at: str = Field(min_length=10, max_length=80)
    metadata: dict[str, Any] = Field(default_factory=dict)
    def fingerprint(self) -> str: return canonical_sha256(self)


class EvidenceGraphExchangePolicy(BaseModel):
    exchange_policy_id: str = Field(min_length=2, max_length=500)
    require_node_identity: Literal[True] = True
    require_manifest_hash: Literal[True] = True
    require_object_fingerprints: Literal[True] = True
    require_upstream_contract_identity: Literal[True] = True
    preserve_epistemic_state: Literal[True] = True
    preserve_source_provenance: Literal[True] = True
    preserve_contradictions: Literal[True] = True
    require_local_validation_before_promotion: Literal[True] = True
    allow_reference_first_exchange: Literal[True] = True
    node_trust_can_establish_content_truth: Literal[False] = False
    signature_validity_can_establish_content_truth: Literal[False] = False
    federation_consensus_can_establish_truth: Literal[False] = False
    remote_acceptance_can_create_local_evidence: Literal[False] = False
    remote_exchange_can_mutate_local_graph: Literal[False] = False
    metadata: dict[str, Any] = Field(default_factory=dict)
    def fingerprint(self) -> str: return canonical_sha256(self)


class FederatedObjectDescriptor(BaseModel):
    federated_object_descriptor_id: str = Field(min_length=2, max_length=500)
    source_node_ref: str = Field(min_length=2, max_length=500)
    upstream_contract: str = Field(min_length=3, max_length=500)
    object_type: str = Field(min_length=2, max_length=500)
    object_ref: str = Field(min_length=2, max_length=500)
    object_fingerprint_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    epistemic_state: str = Field(min_length=2, max_length=200)
    provenance_refs: list[str] = Field(min_length=1)
    as_of: str = Field(min_length=10, max_length=80)
    local_object_ref: str | None = Field(default=None, max_length=500)
    remote_state_preserved: Literal[True] = True
    descriptor_does_not_establish_local_truth: Literal[True] = True
    descriptor_does_not_create_local_graph_edge: Literal[True] = True
    metadata: dict[str, Any] = Field(default_factory=dict)
    @model_validator(mode="after")
    def validate_descriptor(self):
        _unique(self.provenance_refs, "provenance_refs")
        return self
    def fingerprint(self) -> str: return canonical_sha256(self)


class FederatedPackageReference(BaseModel):
    federated_package_reference_id: str = Field(min_length=2, max_length=500)
    source_node_ref: str = Field(min_length=2, max_length=500)
    package_manifest_ref: str = Field(min_length=2, max_length=500)
    package_manifest_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    package_root_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    contract_version: str = Field(min_length=3, max_length=500)
    as_of: str = Field(min_length=10, max_length=80)
    package_reference_is_not_truth_verdict: Literal[True] = True
    package_reference_is_not_local_import: Literal[True] = True
    metadata: dict[str, Any] = Field(default_factory=dict)
    def fingerprint(self) -> str: return canonical_sha256(self)


class ExchangeManifest(BaseModel):
    exchange_manifest_id: str = Field(min_length=2, max_length=500)
    exchange_policy_ref: str = Field(min_length=2, max_length=500)
    source_node_ref: str = Field(min_length=2, max_length=500)
    destination_node_ref: str = Field(min_length=2, max_length=500)
    direction: ExchangeDirection
    object_descriptor_refs: list[str] = Field(min_length=1)
    package_reference_refs: list[str] = Field(default_factory=list)
    created_at: str = Field(min_length=10, max_length=80)
    manifest_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    schema_version: Literal["1.0"] = "1.0"
    reference_first: Literal[True] = True
    manifest_is_not_evidence: Literal[True] = True
    metadata: dict[str, Any] = Field(default_factory=dict)
    @model_validator(mode="after")
    def validate_manifest(self):
        _unique(self.object_descriptor_refs, "object_descriptor_refs")
        _unique(self.package_reference_refs, "package_reference_refs")
        if self.source_node_ref == self.destination_node_ref:
            raise ValueError("source and destination nodes must differ")
        return self
    def fingerprint(self) -> str: return canonical_sha256(self)


class ExchangeIntegrityAttestation(BaseModel):
    exchange_integrity_attestation_id: str = Field(min_length=2, max_length=500)
    exchange_manifest_ref: str = Field(min_length=2, max_length=500)
    signing_node_ref: str = Field(min_length=2, max_length=500)
    signing_key_fingerprint_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    manifest_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    signature_algorithm: str = Field(min_length=2, max_length=100)
    signature_value_b64: str = Field(min_length=8, max_length=12000)
    signature_verified: bool
    verified_at: str = Field(min_length=10, max_length=80)
    signature_proves_bytes_not_truth: Literal[True] = True
    signature_does_not_establish_source_claim_accuracy: Literal[True] = True
    metadata: dict[str, Any] = Field(default_factory=dict)
    def fingerprint(self) -> str: return canonical_sha256(self)


class FederatedConflictRecord(BaseModel):
    federated_conflict_record_id: str = Field(min_length=2, max_length=500)
    local_object_ref: str = Field(min_length=2, max_length=500)
    remote_object_descriptor_ref: str = Field(min_length=2, max_length=500)
    conflict_type: str = Field(min_length=2, max_length=500)
    description: str = Field(min_length=3, max_length=8000)
    local_fingerprint_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    remote_fingerprint_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    disposition: ConflictDisposition
    conflict_preserved: Literal[True] = True
    remote_version_does_not_silently_overwrite_local: Literal[True] = True
    metadata: dict[str, Any] = Field(default_factory=dict)
    def fingerprint(self) -> str: return canonical_sha256(self)


class InboundExchangeAssessment(BaseModel):
    inbound_exchange_assessment_id: str = Field(min_length=2, max_length=500)
    exchange_manifest_ref: str = Field(min_length=2, max_length=500)
    integrity_attestation_ref: str = Field(min_length=2, max_length=500)
    assessed_object_descriptor_refs: list[str] = Field(min_length=1)
    conflict_refs: list[str] = Field(default_factory=list)
    disposition: ExchangeDisposition
    assessed_at: str = Field(min_length=10, max_length=80)
    compatibility_note: str = Field(min_length=3, max_length=8000)
    local_validation_required: Literal[True] = True
    acceptance_does_not_promote_remote_assertions: Literal[True] = True
    compatibility_does_not_establish_semantic_equivalence: Literal[True] = True
    metadata: dict[str, Any] = Field(default_factory=dict)
    @model_validator(mode="after")
    def validate_assessment(self):
        _unique(self.assessed_object_descriptor_refs, "assessed_object_descriptor_refs")
        _unique(self.conflict_refs, "conflict_refs")
        return self
    def fingerprint(self) -> str: return canonical_sha256(self)


class FederationExchangeSnapshot(BaseModel):
    federation_exchange_snapshot_id: str = Field(min_length=2, max_length=500)
    exchange_manifest_ref: str = Field(min_length=2, max_length=500)
    assessment_ref: str = Field(min_length=2, max_length=500)
    node_refs: list[str] = Field(min_length=2)
    object_descriptor_refs: list[str] = Field(min_length=1)
    package_reference_refs: list[str] = Field(default_factory=list)
    conflict_refs: list[str] = Field(default_factory=list)
    as_of: str = Field(min_length=10, max_length=80)
    immutable: Literal[True] = True
    remote_objects_remain_remote_references: Literal[True] = True
    later_exchange_may_supersede_snapshot: Literal[True] = True
    snapshot_is_not_truth_verdict: Literal[True] = True
    metadata: dict[str, Any] = Field(default_factory=dict)
    @model_validator(mode="after")
    def validate_snapshot(self):
        for vals,label in ((self.node_refs,"node_refs"),(self.object_descriptor_refs,"object_descriptor_refs"),(self.package_reference_refs,"package_reference_refs"),(self.conflict_refs,"conflict_refs")):
            _unique(vals,label)
        return self
    def fingerprint(self) -> str: return canonical_sha256(self)


class FederatedEvidenceGraphExchangeBundle(BaseModel):
    release: Literal["3.89.0"] = "3.89.0"
    contract: Literal["sc.core.federated-evidence-graph-exchange.v1"] = CONTRACT_VERSION
    nodes: list[FederationNodeIdentity] = Field(min_length=2)
    policies: list[EvidenceGraphExchangePolicy] = Field(min_length=1)
    object_descriptors: list[FederatedObjectDescriptor] = Field(min_length=1)
    package_references: list[FederatedPackageReference] = Field(default_factory=list)
    manifests: list[ExchangeManifest] = Field(min_length=1)
    integrity_attestations: list[ExchangeIntegrityAttestation] = Field(min_length=1)
    conflicts: list[FederatedConflictRecord] = Field(default_factory=list)
    assessments: list[InboundExchangeAssessment] = Field(min_length=1)
    snapshots: list[FederationExchangeSnapshot] = Field(min_length=1)
    identity_graph_mutation_performed: Literal[False] = False
    relationship_graph_mutation_performed: Literal[False] = False
    evidence_graph_mutation_performed: Literal[False] = False

    @model_validator(mode="after")
    def validate_bundle(self):
        groups = {
            "node": [x.federation_node_id for x in self.nodes],
            "policy": [x.exchange_policy_id for x in self.policies],
            "descriptor": [x.federated_object_descriptor_id for x in self.object_descriptors],
            "package": [x.federated_package_reference_id for x in self.package_references],
            "manifest": [x.exchange_manifest_id for x in self.manifests],
            "attestation": [x.exchange_integrity_attestation_id for x in self.integrity_attestations],
            "conflict": [x.federated_conflict_record_id for x in self.conflicts],
            "assessment": [x.inbound_exchange_assessment_id for x in self.assessments],
            "snapshot": [x.federation_exchange_snapshot_id for x in self.snapshots],
        }
        for label, vals in groups.items(): _unique(vals, f"{label} ids")
        nodes, policies, descs, packages, manifests, attest, conflicts, assessments = map(set,[groups["node"],groups["policy"],groups["descriptor"],groups["package"],groups["manifest"],groups["attestation"],groups["conflict"],groups["assessment"]])
        for d in self.object_descriptors:
            if d.source_node_ref not in nodes: raise ValueError("unknown descriptor source node")
        for p in self.package_references:
            if p.source_node_ref not in nodes: raise ValueError("unknown package source node")
        for m in self.manifests:
            if m.exchange_policy_ref not in policies or m.source_node_ref not in nodes or m.destination_node_ref not in nodes: raise ValueError("manifest reference unresolved")
            if not set(m.object_descriptor_refs) <= descs or not set(m.package_reference_refs) <= packages: raise ValueError("manifest payload reference unresolved")
        for a in self.integrity_attestations:
            if a.exchange_manifest_ref not in manifests or a.signing_node_ref not in nodes: raise ValueError("attestation reference unresolved")
        for c in self.conflicts:
            if c.remote_object_descriptor_ref not in descs: raise ValueError("conflict descriptor unresolved")
        for a in self.assessments:
            if a.exchange_manifest_ref not in manifests or a.integrity_attestation_ref not in attest: raise ValueError("assessment reference unresolved")
            if not set(a.assessed_object_descriptor_refs) <= descs or not set(a.conflict_refs) <= conflicts: raise ValueError("assessment payload unresolved")
        for s in self.snapshots:
            if s.exchange_manifest_ref not in manifests or s.assessment_ref not in assessments: raise ValueError("snapshot reference unresolved")
            if not set(s.node_refs) <= nodes or not set(s.object_descriptor_refs) <= descs or not set(s.package_reference_refs) <= packages or not set(s.conflict_refs) <= conflicts: raise ValueError("snapshot payload unresolved")
        return self
    def fingerprint(self) -> str: return canonical_sha256(self)


def reference_federated_evidence_graph_exchange_bundle() -> FederatedEvidenceGraphExchangeBundle:
    upstream = reference_reproducible_graph_investigation_package_bundle()
    now = "2026-09-30T20:00:00Z"
    node_a = FederationNodeIdentity(
        federation_node_id="federation-node:synthetic:local",
        node_uri="https://core.sustainablecatalyst.com",
        operator_name="Synthetic Local Research Node",
        public_key_fingerprint_sha256="1"*64,
        trust_state=NodeTrustState.authenticated,
        registered_at=now,
    )
    node_b = FederationNodeIdentity(
        federation_node_id="federation-node:synthetic:peer-a",
        node_uri="https://peer-a.invalid/core",
        operator_name="Synthetic Peer Research Node",
        public_key_fingerprint_sha256="2"*64,
        trust_state=NodeTrustState.authenticated,
        registered_at=now,
    )
    policy = EvidenceGraphExchangePolicy(exchange_policy_id="exchange-policy:synthetic:v1")
    selected = upstream.object_bindings[:5]
    descs=[]
    for i,b in enumerate(selected,1):
        descs.append(FederatedObjectDescriptor(
            federated_object_descriptor_id=f"fed-object:synthetic:{i}",
            source_node_ref=node_b.federation_node_id,
            upstream_contract=b.upstream_contract,
            object_type=b.object_type,
            object_ref=b.object_ref,
            object_fingerprint_sha256=b.object_fingerprint_sha256,
            epistemic_state=b.epistemic_state.value,
            provenance_refs=b.provenance_refs,
            as_of=b.as_of,
            local_object_ref=b.object_ref if i == 1 else None,
        ))
    pkg_manifest=upstream.manifests[0]
    pkg_integrity=upstream.integrity_records[0]
    pkg=FederatedPackageReference(
        federated_package_reference_id="federated-package:synthetic:v1",
        source_node_ref=node_b.federation_node_id,
        package_manifest_ref=pkg_manifest.investigation_manifest_id,
        package_manifest_sha256=pkg_integrity.manifest_sha256,
        package_root_sha256=pkg_integrity.package_root_sha256,
        contract_version=UPSTREAM_PACKAGE_CONTRACT_VERSION,
        as_of=pkg_manifest.as_of,
    )
    manifest_seed={"source":node_b.federation_node_id,"destination":node_a.federation_node_id,"objects":[d.federated_object_descriptor_id for d in descs],"package":pkg.federated_package_reference_id,"created_at":now}
    mh=canonical_sha256(manifest_seed)
    manifest=ExchangeManifest(
        exchange_manifest_id="exchange-manifest:synthetic:v1",
        exchange_policy_ref=policy.exchange_policy_id,
        source_node_ref=node_b.federation_node_id,
        destination_node_ref=node_a.federation_node_id,
        direction=ExchangeDirection.import_,
        object_descriptor_refs=[d.federated_object_descriptor_id for d in descs],
        package_reference_refs=[pkg.federated_package_reference_id],
        created_at=now,
        manifest_sha256=mh,
    )
    att=ExchangeIntegrityAttestation(
        exchange_integrity_attestation_id="exchange-attestation:synthetic:v1",
        exchange_manifest_ref=manifest.exchange_manifest_id,
        signing_node_ref=node_b.federation_node_id,
        signing_key_fingerprint_sha256=node_b.public_key_fingerprint_sha256,
        manifest_sha256=manifest.manifest_sha256,
        signature_algorithm="synthetic-ed25519-reference",
        signature_value_b64="c3ludGhldGljLXNpZ25hdHVyZS12YWx1ZQ==",
        signature_verified=True,
        verified_at=now,
    )
    conflict=FederatedConflictRecord(
        federated_conflict_record_id="federated-conflict:synthetic:v1",
        local_object_ref=descs[0].object_ref,
        remote_object_descriptor_ref=descs[0].federated_object_descriptor_id,
        conflict_type="version-or-state-mismatch",
        description="Remote reference is preserved separately because local state may have advanced after the peer package as-of time.",
        local_fingerprint_sha256="3"*64,
        remote_fingerprint_sha256=descs[0].object_fingerprint_sha256,
        disposition=ConflictDisposition.unresolved,
    )
    assessment=InboundExchangeAssessment(
        inbound_exchange_assessment_id="inbound-assessment:synthetic:v1",
        exchange_manifest_ref=manifest.exchange_manifest_id,
        integrity_attestation_ref=att.exchange_integrity_attestation_id,
        assessed_object_descriptor_refs=[d.federated_object_descriptor_id for d in descs],
        conflict_refs=[conflict.federated_conflict_record_id],
        disposition=ExchangeDisposition.accepted_for_local_validation,
        assessed_at=now,
        compatibility_note="Contracts and hashes are structurally compatible; every remote assertion remains reference-only pending local validation and conflict review.",
    )
    snap=FederationExchangeSnapshot(
        federation_exchange_snapshot_id="federation-exchange-snapshot:synthetic:v1",
        exchange_manifest_ref=manifest.exchange_manifest_id,
        assessment_ref=assessment.inbound_exchange_assessment_id,
        node_refs=[node_a.federation_node_id,node_b.federation_node_id],
        object_descriptor_refs=[d.federated_object_descriptor_id for d in descs],
        package_reference_refs=[pkg.federated_package_reference_id],
        conflict_refs=[conflict.federated_conflict_record_id],
        as_of=now,
    )
    return FederatedEvidenceGraphExchangeBundle(
        nodes=[node_a,node_b], policies=[policy], object_descriptors=descs,
        package_references=[pkg], manifests=[manifest], integrity_attestations=[att],
        conflicts=[conflict], assessments=[assessment], snapshots=[snap],
    )


def contract_document() -> dict[str, Any]:
    b=reference_federated_evidence_graph_exchange_bundle()
    return {
        "ok": True,
        "release": CORE_RELEASE,
        "contract": CONTRACT_VERSION,
        "principles": {
            "reference_first_exchange": True,
            "remote_epistemic_state_preserved": True,
            "source_provenance_preserved": True,
            "contradictions_preserved": True,
            "local_validation_required_before_promotion": True,
            "content_addressed_manifests": True,
            "remote_objects_remain_remote_references": True,
        },
        "boundaries": {
            "node_trust_establishes_content_truth": False,
            "signature_validity_establishes_content_truth": False,
            "federation_consensus_establishes_truth": False,
            "schema_compatibility_establishes_semantic_equivalence": False,
            "remote_acceptance_creates_local_evidence": False,
            "remote_reference_creates_local_graph_edge": False,
            "identity_graph_mutation_performed": False,
            "relationship_graph_mutation_performed": False,
            "evidence_graph_mutation_performed": False,
        },
        "reference": {
            "nodes": len(b.nodes),
            "object_descriptors": len(b.object_descriptors),
            "package_references": len(b.package_references),
            "manifests": len(b.manifests),
            "integrity_attestations": len(b.integrity_attestations),
            "conflicts": len(b.conflicts),
            "assessments": len(b.assessments),
            "snapshots": len(b.snapshots),
            "assessment_disposition": b.assessments[0].disposition.value,
            "bundle_fingerprint_sha256": b.fingerprint(),
        },
        "database_migration": "none",
    }
