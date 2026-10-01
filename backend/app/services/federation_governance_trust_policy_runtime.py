from __future__ import annotations

from enum import Enum
from functools import lru_cache
from typing import Any, Literal

from pydantic import BaseModel, Field, model_validator

from .computational_runtime_objects import canonical_sha256
from .federated_evidence_graph_exchange import (
    CONTRACT_VERSION as V389_CONTRACT,
    NodeTrustState,
    reference_federated_evidence_graph_exchange_bundle,
)
from .unified_runtime_policy_capability_negotiation import CONTRACT_VERSION as V391_CONTRACT
from .signed_runtime_artifacts_execution_attestations import (
    CONTRACT_VERSION as V395_CONTRACT,
    VerificationDisposition,
    reference_signed_runtime_artifacts_execution_attestations_bundle,
)

CORE_RELEASE = "3.96.0"
CONTRACT_VERSION = "sc.core.federation-governance-trust-policy-runtime.v1"


def _unique(values: list[str], label: str) -> None:
    if len(values) != len(set(values)):
        raise ValueError(f"{label} must be unique")


class GovernanceNodeState(str, Enum):
    active = "active"
    constrained = "constrained"
    suspended = "suspended"
    revoked = "revoked"


class TrustScopeKind(str, Enum):
    identity = "identity"
    documentary_reference = "documentary-reference"
    investigation_package = "investigation-package"
    query_reference = "query-reference"
    runtime_attestation = "runtime-attestation"
    capability_metadata = "capability-metadata"


class PermissionEffect(str, Enum):
    allow = "allow"
    deny = "deny"
    reference_only = "reference-only"
    local_validation_required = "local-validation-required"


class GovernanceDecisionDisposition(str, Enum):
    allowed = "allowed"
    allowed_with_constraints = "allowed-with-constraints"
    reference_only = "reference-only"
    quarantined = "quarantined"
    denied = "denied"


class FederationGovernancePolicy(BaseModel):
    policy_id: str = Field(min_length=3, max_length=500)
    require_registered_node_identity: Literal[True] = True
    require_current_node_state: Literal[True] = True
    require_scoped_trust: Literal[True] = True
    require_capability_permission: Literal[True] = True
    require_contract_allowlist: Literal[True] = True
    require_signature_verification_when_attested: Literal[True] = True
    require_local_validation_for_remote_content: Literal[True] = True
    require_conflict_preservation: Literal[True] = True
    require_explicit_revocation_and_suspension: Literal[True] = True
    require_auditable_policy_decisions: Literal[True] = True
    allow_global_unscoped_trust: Literal[False] = False
    allow_trust_to_establish_content_truth: Literal[False] = False
    allow_signature_to_establish_content_truth: Literal[False] = False
    allow_policy_approval_to_create_local_evidence: Literal[False] = False
    allow_remote_content_to_bypass_local_validation: Literal[False] = False
    allow_conflict_overwrite: Literal[False] = False
    allow_suspended_node_to_exchange: Literal[False] = False
    allow_revoked_node_to_exchange: Literal[False] = False
    allow_policy_to_mutate_governed_graphs: Literal[False] = False
    metadata: dict[str, Any] = Field(default_factory=dict)
    def fingerprint(self) -> str: return canonical_sha256(self)


class FederationGovernedNode(BaseModel):
    governed_node_id: str = Field(min_length=3, max_length=500)
    federation_node_ref: str = Field(min_length=3, max_length=500)
    operator_name: str = Field(min_length=2, max_length=1000)
    governance_state: GovernanceNodeState
    underlying_exchange_trust_state: NodeTrustState
    active_key_refs: list[str] = Field(default_factory=list)
    trust_scope_refs: list[str] = Field(default_factory=list)
    permission_refs: list[str] = Field(default_factory=list)
    state_effective_at: str = Field(min_length=10, max_length=80)
    node_state_is_not_content_truth: Literal[True] = True
    node_state_does_not_expand_content_authority: Literal[True] = True
    metadata: dict[str, Any] = Field(default_factory=dict)
    @model_validator(mode="after")
    def validate_node(self):
        _unique(self.active_key_refs, "active_key_refs"); _unique(self.trust_scope_refs, "trust_scope_refs"); _unique(self.permission_refs, "permission_refs")
        if self.governance_state == GovernanceNodeState.revoked and self.underlying_exchange_trust_state != NodeTrustState.revoked:
            raise ValueError("revoked governed node requires revoked exchange trust state")
        return self
    def fingerprint(self) -> str: return canonical_sha256(self)


class FederationTrustScope(BaseModel):
    trust_scope_id: str = Field(min_length=3, max_length=500)
    node_ref: str = Field(min_length=3, max_length=500)
    scope_kind: TrustScopeKind
    allowed_contracts: list[str] = Field(min_length=1)
    allowed_object_types: list[str] = Field(min_length=1)
    valid_from: str = Field(min_length=10, max_length=80)
    valid_until: str | None = Field(default=None, max_length=80)
    reference_only: bool = False
    local_validation_required: Literal[True] = True
    trust_scope_is_not_truth_assessment: Literal[True] = True
    trust_scope_is_not_evidence_promotion: Literal[True] = True
    metadata: dict[str, Any] = Field(default_factory=dict)
    @model_validator(mode="after")
    def validate_scope(self):
        _unique(self.allowed_contracts, "allowed_contracts"); _unique(self.allowed_object_types, "allowed_object_types")
        return self
    def fingerprint(self) -> str: return canonical_sha256(self)


class FederationCapabilityPermission(BaseModel):
    permission_id: str = Field(min_length=3, max_length=500)
    node_ref: str = Field(min_length=3, max_length=500)
    capability: str = Field(min_length=3, max_length=500)
    effect: PermissionEffect
    trust_scope_ref: str = Field(min_length=3, max_length=500)
    required_contract: str = Field(min_length=3, max_length=500)
    constraints: list[str] = Field(min_length=1)
    granted_at: str = Field(min_length=10, max_length=80)
    permission_is_not_content_validation: Literal[True] = True
    permission_is_not_truth_assessment: Literal[True] = True
    permission_cannot_increase_epistemic_authority: Literal[True] = True
    metadata: dict[str, Any] = Field(default_factory=dict)
    @model_validator(mode="after")
    def validate_permission(self):
        _unique(self.constraints, "constraints")
        return self
    def fingerprint(self) -> str: return canonical_sha256(self)


class FederationRevocationSuspensionRecord(BaseModel):
    action_id: str = Field(min_length=3, max_length=500)
    node_ref: str = Field(min_length=3, max_length=500)
    action: Literal["suspend", "revoke", "restore"]
    effective_at: str = Field(min_length=10, max_length=80)
    reason: str = Field(min_length=3, max_length=2000)
    supersedes_action_ref: str | None = Field(default=None, max_length=500)
    future_policy_decisions_must_reflect_action: Literal[True] = True
    historical_records_remain_immutable: Literal[True] = True
    action_does_not_rewrite_remote_content: Literal[True] = True
    metadata: dict[str, Any] = Field(default_factory=dict)
    def fingerprint(self) -> str: return canonical_sha256(self)


class FederationIntakeRule(BaseModel):
    intake_rule_id: str = Field(min_length=3, max_length=500)
    trust_scope_ref: str = Field(min_length=3, max_length=500)
    object_contract: str = Field(min_length=3, max_length=500)
    object_type: str = Field(min_length=2, max_length=500)
    required_verification_dispositions: list[VerificationDisposition] = Field(min_length=1)
    default_disposition: GovernanceDecisionDisposition
    preserve_remote_epistemic_state: Literal[True] = True
    preserve_remote_provenance: Literal[True] = True
    require_local_validation: Literal[True] = True
    metadata: dict[str, Any] = Field(default_factory=dict)
    @model_validator(mode="after")
    def validate_rule(self):
        _unique([x.value for x in self.required_verification_dispositions], "required_verification_dispositions")
        return self
    def fingerprint(self) -> str: return canonical_sha256(self)


class FederationPolicyDecision(BaseModel):
    decision_id: str = Field(min_length=3, max_length=500)
    policy_ref: str = Field(min_length=3, max_length=500)
    node_ref: str = Field(min_length=3, max_length=500)
    permission_ref: str = Field(min_length=3, max_length=500)
    trust_scope_ref: str = Field(min_length=3, max_length=500)
    intake_rule_ref: str = Field(min_length=3, max_length=500)
    remote_object_ref: str = Field(min_length=3, max_length=1000)
    signature_verification_ref: str | None = Field(default=None, max_length=500)
    disposition: GovernanceDecisionDisposition
    applied_constraints: list[str] = Field(min_length=1)
    local_validation_required: Literal[True] = True
    remote_epistemic_state_preserved: Literal[True] = True
    remote_provenance_preserved: Literal[True] = True
    decision_is_not_content_truth: Literal[True] = True
    decision_is_not_local_evidence_promotion: Literal[True] = True
    decided_at: str = Field(min_length=10, max_length=80)
    metadata: dict[str, Any] = Field(default_factory=dict)
    @model_validator(mode="after")
    def validate_decision(self):
        _unique(self.applied_constraints, "applied_constraints")
        if self.disposition == GovernanceDecisionDisposition.allowed and self.local_validation_required is not True:
            raise ValueError("remote intake always requires local validation")
        return self
    def fingerprint(self) -> str: return canonical_sha256(self)


class FederationConflictGovernanceRecord(BaseModel):
    conflict_governance_id: str = Field(min_length=3, max_length=500)
    source_conflict_ref: str = Field(min_length=3, max_length=500)
    node_ref: str = Field(min_length=3, max_length=500)
    decision_ref: str = Field(min_length=3, max_length=500)
    disposition: Literal["preserved-unresolved", "quarantined", "locally-qualified"]
    local_state_preserved: Literal[True] = True
    remote_state_preserved: Literal[True] = True
    silent_overwrite_allowed: Literal[False] = False
    conflict_is_not_truth_verdict: Literal[True] = True
    metadata: dict[str, Any] = Field(default_factory=dict)
    def fingerprint(self) -> str: return canonical_sha256(self)


class FederationGovernanceAuditEvent(BaseModel):
    audit_event_id: str = Field(min_length=3, max_length=500)
    event_type: Literal["node-state", "scope-evaluation", "permission-evaluation", "signature-check", "intake-decision", "conflict-preservation"]
    node_ref: str = Field(min_length=3, max_length=500)
    related_refs: list[str] = Field(min_length=1)
    recorded_at: str = Field(min_length=10, max_length=80)
    deterministic_event_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    event_is_audit_record_not_truth_assessment: Literal[True] = True
    metadata: dict[str, Any] = Field(default_factory=dict)
    @model_validator(mode="after")
    def validate_event(self):
        _unique(self.related_refs, "related_refs")
        return self
    def fingerprint(self) -> str: return canonical_sha256(self)


class FederationGovernanceSnapshot(BaseModel):
    snapshot_id: str = Field(min_length=3, max_length=500)
    policy_ref: str = Field(min_length=3, max_length=500)
    node_refs: list[str] = Field(min_length=1)
    trust_scope_refs: list[str] = Field(min_length=1)
    permission_refs: list[str] = Field(min_length=1)
    action_refs: list[str] = Field(default_factory=list)
    intake_rule_refs: list[str] = Field(min_length=1)
    decision_refs: list[str] = Field(min_length=1)
    conflict_governance_refs: list[str] = Field(default_factory=list)
    audit_event_refs: list[str] = Field(min_length=1)
    as_of: str = Field(min_length=10, max_length=80)
    immutable: Literal[True] = True
    supersedable: Literal[True] = True
    snapshot_is_not_truth_verdict: Literal[True] = True
    metadata: dict[str, Any] = Field(default_factory=dict)
    @model_validator(mode="after")
    def validate_snapshot(self):
        for vals,label in ((self.node_refs,"node_refs"),(self.trust_scope_refs,"trust_scope_refs"),(self.permission_refs,"permission_refs"),(self.action_refs,"action_refs"),(self.intake_rule_refs,"intake_rule_refs"),(self.decision_refs,"decision_refs"),(self.conflict_governance_refs,"conflict_governance_refs"),(self.audit_event_refs,"audit_event_refs")):
            _unique(vals,label)
        return self
    def fingerprint(self) -> str: return canonical_sha256(self)


class FederationGovernanceTrustPolicyBundle(BaseModel):
    release: Literal["3.96.0"] = "3.96.0"
    contract: Literal[CONTRACT_VERSION] = CONTRACT_VERSION
    policies: list[FederationGovernancePolicy] = Field(min_length=1)
    nodes: list[FederationGovernedNode] = Field(min_length=1)
    trust_scopes: list[FederationTrustScope] = Field(min_length=1)
    permissions: list[FederationCapabilityPermission] = Field(min_length=1)
    actions: list[FederationRevocationSuspensionRecord] = Field(default_factory=list)
    intake_rules: list[FederationIntakeRule] = Field(min_length=1)
    decisions: list[FederationPolicyDecision] = Field(min_length=1)
    conflicts: list[FederationConflictGovernanceRecord] = Field(default_factory=list)
    audit_events: list[FederationGovernanceAuditEvent] = Field(min_length=1)
    snapshots: list[FederationGovernanceSnapshot] = Field(min_length=1)
    database_migration: Literal["none"] = "none"

    @model_validator(mode="after")
    def validate_bundle(self):
        groups=[
            (self.policies,"policy_id"),(self.nodes,"governed_node_id"),(self.trust_scopes,"trust_scope_id"),(self.permissions,"permission_id"),(self.actions,"action_id"),(self.intake_rules,"intake_rule_id"),(self.decisions,"decision_id"),(self.conflicts,"conflict_governance_id"),(self.audit_events,"audit_event_id"),(self.snapshots,"snapshot_id")]
        for items,field in groups: _unique([getattr(x,field) for x in items], field)
        policies={x.policy_id for x in self.policies}; nodes={x.governed_node_id for x in self.nodes}; scopes={x.trust_scope_id for x in self.trust_scopes}; perms={x.permission_id for x in self.permissions}; actions={x.action_id for x in self.actions}; rules={x.intake_rule_id for x in self.intake_rules}; decisions={x.decision_id for x in self.decisions}; conflicts={x.conflict_governance_id for x in self.conflicts}; audits={x.audit_event_id for x in self.audit_events}
        for n in self.nodes:
            if not set(n.trust_scope_refs) <= scopes or not set(n.permission_refs) <= perms: raise ValueError("node governance references unresolved")
        for s in self.trust_scopes:
            if s.node_ref not in nodes: raise ValueError("trust scope node unresolved")
        for p in self.permissions:
            if p.node_ref not in nodes or p.trust_scope_ref not in scopes: raise ValueError("permission references unresolved")
        for a in self.actions:
            if a.node_ref not in nodes or (a.supersedes_action_ref and a.supersedes_action_ref not in actions): raise ValueError("action references unresolved")
        for r in self.intake_rules:
            if r.trust_scope_ref not in scopes: raise ValueError("intake rule scope unresolved")
        for d in self.decisions:
            if d.policy_ref not in policies or d.node_ref not in nodes or d.permission_ref not in perms or d.trust_scope_ref not in scopes or d.intake_rule_ref not in rules: raise ValueError("decision references unresolved")
        for c in self.conflicts:
            if c.node_ref not in nodes or c.decision_ref not in decisions: raise ValueError("conflict governance references unresolved")
        for e in self.audit_events:
            if e.node_ref not in nodes: raise ValueError("audit node unresolved")
        for s in self.snapshots:
            if s.policy_ref not in policies or not set(s.node_refs)<=nodes or not set(s.trust_scope_refs)<=scopes or not set(s.permission_refs)<=perms or not set(s.action_refs)<=actions or not set(s.intake_rule_refs)<=rules or not set(s.decision_refs)<=decisions or not set(s.conflict_governance_refs)<=conflicts or not set(s.audit_event_refs)<=audits: raise ValueError("snapshot references unresolved")
        return self

    def fingerprint(self) -> str: return canonical_sha256(self)


def _h(label: str) -> str:
    import hashlib
    return hashlib.sha256(label.encode()).hexdigest()


@lru_cache(maxsize=1)
def reference_federation_governance_trust_policy_bundle() -> FederationGovernanceTrustPolicyBundle:
    exchange=reference_federated_evidence_graph_exchange_bundle()
    signed=reference_signed_runtime_artifacts_execution_attestations_bundle()
    policy=FederationGovernancePolicy(policy_id="fgp-default-v1")
    nodes=[
        FederationGovernedNode(governed_node_id="node-local", federation_node_ref=exchange.nodes[0].federation_node_id, operator_name="Sustainable Catalyst", governance_state="active", underlying_exchange_trust_state="authenticated", active_key_refs=[signed.keys[0].key_ref], trust_scope_refs=["scope-local-attestation","scope-local-package"], permission_refs=["perm-local-attestation","perm-local-package"], state_effective_at="2026-09-30T23:00:00Z"),
        FederationGovernedNode(governed_node_id="node-peer-a", federation_node_ref=exchange.nodes[1].federation_node_id, operator_name="Federated Research Peer A", governance_state="constrained", underlying_exchange_trust_state="authenticated", active_key_refs=[signed.keys[-1].key_ref], trust_scope_refs=["scope-peer-doc","scope-peer-package","scope-peer-attestation"], permission_refs=["perm-peer-doc","perm-peer-package","perm-peer-attestation"], state_effective_at="2026-09-30T23:00:00Z"),
        FederationGovernedNode(governed_node_id="node-peer-revoked", federation_node_ref="federation-node-revoked-reference", operator_name="Historical Revoked Peer", governance_state="revoked", underlying_exchange_trust_state="revoked", active_key_refs=[], trust_scope_refs=["scope-revoked-reference"], permission_refs=["perm-revoked-deny"], state_effective_at="2026-09-30T23:00:00Z"),
    ]
    scopes=[
        FederationTrustScope(trust_scope_id="scope-local-attestation",node_ref="node-local",scope_kind="runtime-attestation",allowed_contracts=[V395_CONTRACT],allowed_object_types=["runtime-attestation","verification-record"],valid_from="2026-09-30T23:00:00Z"),
        FederationTrustScope(trust_scope_id="scope-local-package",node_ref="node-local",scope_kind="investigation-package",allowed_contracts=["sc.core.reproducible-graph-investigation-package.v1"],allowed_object_types=["investigation-package"],valid_from="2026-09-30T23:00:00Z"),
        FederationTrustScope(trust_scope_id="scope-peer-doc",node_ref="node-peer-a",scope_kind="documentary-reference",allowed_contracts=["sc.core.public-record-documentary-source-object-model.v1"],allowed_object_types=["documentary-source","documentary-interpretation"],valid_from="2026-09-30T23:00:00Z",reference_only=True),
        FederationTrustScope(trust_scope_id="scope-peer-package",node_ref="node-peer-a",scope_kind="investigation-package",allowed_contracts=["sc.core.reproducible-graph-investigation-package.v1"],allowed_object_types=["investigation-package"],valid_from="2026-09-30T23:00:00Z",reference_only=True),
        FederationTrustScope(trust_scope_id="scope-peer-attestation",node_ref="node-peer-a",scope_kind="runtime-attestation",allowed_contracts=[V395_CONTRACT],allowed_object_types=["runtime-attestation"],valid_from="2026-09-30T23:00:00Z",reference_only=True),
        FederationTrustScope(trust_scope_id="scope-revoked-reference",node_ref="node-peer-revoked",scope_kind="capability-metadata",allowed_contracts=[V389_CONTRACT],allowed_object_types=["historical-reference"],valid_from="2026-01-01T00:00:00Z",valid_until="2026-09-01T00:00:00Z",reference_only=True),
    ]
    permissions=[
        FederationCapabilityPermission(permission_id="perm-local-attestation",node_ref="node-local",capability="publish-runtime-attestation",effect="allow",trust_scope_ref="scope-local-attestation",required_contract=V395_CONTRACT,constraints=["signature-required","provenance-preserved"],granted_at="2026-09-30T23:00:00Z"),
        FederationCapabilityPermission(permission_id="perm-local-package",node_ref="node-local",capability="publish-investigation-package",effect="allow",trust_scope_ref="scope-local-package",required_contract="sc.core.reproducible-graph-investigation-package.v1",constraints=["content-addressed","provenance-preserved"],granted_at="2026-09-30T23:00:00Z"),
        FederationCapabilityPermission(permission_id="perm-peer-doc",node_ref="node-peer-a",capability="submit-documentary-reference",effect="reference-only",trust_scope_ref="scope-peer-doc",required_contract="sc.core.public-record-documentary-source-object-model.v1",constraints=["remote-reference","local-validation-required"],granted_at="2026-09-30T23:00:00Z"),
        FederationCapabilityPermission(permission_id="perm-peer-package",node_ref="node-peer-a",capability="submit-investigation-package",effect="local-validation-required",trust_scope_ref="scope-peer-package",required_contract="sc.core.reproducible-graph-investigation-package.v1",constraints=["reference-first","local-validation-required"],granted_at="2026-09-30T23:00:00Z"),
        FederationCapabilityPermission(permission_id="perm-peer-attestation",node_ref="node-peer-a",capability="submit-runtime-attestation",effect="reference-only",trust_scope_ref="scope-peer-attestation",required_contract=V395_CONTRACT,constraints=["verify-signature","local-validation-required"],granted_at="2026-09-30T23:00:00Z"),
        FederationCapabilityPermission(permission_id="perm-revoked-deny",node_ref="node-peer-revoked",capability="all-exchange",effect="deny",trust_scope_ref="scope-revoked-reference",required_contract=V389_CONTRACT,constraints=["node-revoked","exchange-denied"],granted_at="2026-09-30T23:00:00Z"),
    ]
    actions=[FederationRevocationSuspensionRecord(action_id="action-revoke-peer-old",node_ref="node-peer-revoked",action="revoke",effective_at="2026-09-01T00:00:00Z",reason="Governance authorization withdrawn; historical records retained.")]
    rules=[
        FederationIntakeRule(intake_rule_id="rule-peer-doc",trust_scope_ref="scope-peer-doc",object_contract="sc.core.public-record-documentary-source-object-model.v1",object_type="documentary-source",required_verification_dispositions=["verified","verified-with-qualifications"],default_disposition="reference-only"),
        FederationIntakeRule(intake_rule_id="rule-peer-package",trust_scope_ref="scope-peer-package",object_contract="sc.core.reproducible-graph-investigation-package.v1",object_type="investigation-package",required_verification_dispositions=["verified","verified-with-qualifications"],default_disposition="allowed-with-constraints"),
        FederationIntakeRule(intake_rule_id="rule-peer-attestation",trust_scope_ref="scope-peer-attestation",object_contract=V395_CONTRACT,object_type="runtime-attestation",required_verification_dispositions=["verified","verified-with-qualifications"],default_disposition="reference-only"),
        FederationIntakeRule(intake_rule_id="rule-revoked",trust_scope_ref="scope-revoked-reference",object_contract=V389_CONTRACT,object_type="historical-reference",required_verification_dispositions=["verified"],default_disposition="denied"),
    ]
    remote_desc=exchange.object_descriptors[0]
    ver_ok=next(v for v in signed.verifications if v.disposition in {VerificationDisposition.verified,VerificationDisposition.verified_with_qualifications})
    decisions=[
        FederationPolicyDecision(decision_id="decision-peer-doc",policy_ref=policy.policy_id,node_ref="node-peer-a",permission_ref="perm-peer-doc",trust_scope_ref="scope-peer-doc",intake_rule_ref="rule-peer-doc",remote_object_ref=remote_desc.federated_object_descriptor_id,signature_verification_ref=ver_ok.verification_id,disposition="reference-only",applied_constraints=["remote-reference","local-validation-required","no-graph-mutation"],decided_at="2026-09-30T23:15:00Z"),
        FederationPolicyDecision(decision_id="decision-peer-package",policy_ref=policy.policy_id,node_ref="node-peer-a",permission_ref="perm-peer-package",trust_scope_ref="scope-peer-package",intake_rule_ref="rule-peer-package",remote_object_ref=exchange.package_references[0].federated_package_reference_id,signature_verification_ref=ver_ok.verification_id,disposition="allowed-with-constraints",applied_constraints=["reference-first","local-validation-required","conflicts-preserved"],decided_at="2026-09-30T23:16:00Z"),
        FederationPolicyDecision(decision_id="decision-revoked-deny",policy_ref=policy.policy_id,node_ref="node-peer-revoked",permission_ref="perm-revoked-deny",trust_scope_ref="scope-revoked-reference",intake_rule_ref="rule-revoked",remote_object_ref="historical-reference-001",disposition="denied",applied_constraints=["node-revoked","exchange-denied"],decided_at="2026-09-30T23:17:00Z"),
    ]
    conflicts=[FederationConflictGovernanceRecord(conflict_governance_id="conflict-governance-001",source_conflict_ref=exchange.conflicts[0].federated_conflict_record_id,node_ref="node-peer-a",decision_ref="decision-peer-doc",disposition="preserved-unresolved")]
    audit_events=[]
    for i,(et,n,refs) in enumerate([
        ("node-state","node-peer-a",["scope-peer-doc"]),("scope-evaluation","node-peer-a",["scope-peer-doc","decision-peer-doc"]),("permission-evaluation","node-peer-a",["perm-peer-doc","decision-peer-doc"]),("signature-check","node-peer-a",[ver_ok.verification_id,"decision-peer-doc"]),("intake-decision","node-peer-a",["decision-peer-doc"]),("conflict-preservation","node-peer-a",["conflict-governance-001"]),("node-state","node-peer-revoked",["action-revoke-peer-old","decision-revoked-deny"])
    ],1):
        payload=f"{et}|{n}|{'|'.join(refs)}|{i}"
        audit_events.append(FederationGovernanceAuditEvent(audit_event_id=f"audit-{i:02d}",event_type=et,node_ref=n,related_refs=refs,recorded_at=f"2026-09-30T23:{20+i:02d}:00Z",deterministic_event_sha256=_h(payload)))
    snapshot=FederationGovernanceSnapshot(snapshot_id="federation-governance-snapshot-001",policy_ref=policy.policy_id,node_refs=[x.governed_node_id for x in nodes],trust_scope_refs=[x.trust_scope_id for x in scopes],permission_refs=[x.permission_id for x in permissions],action_refs=[x.action_id for x in actions],intake_rule_refs=[x.intake_rule_id for x in rules],decision_refs=[x.decision_id for x in decisions],conflict_governance_refs=[x.conflict_governance_id for x in conflicts],audit_event_refs=[x.audit_event_id for x in audit_events],as_of="2026-09-30T23:30:00Z")
    return FederationGovernanceTrustPolicyBundle(policies=[policy],nodes=nodes,trust_scopes=scopes,permissions=permissions,actions=actions,intake_rules=rules,decisions=decisions,conflicts=conflicts,audit_events=audit_events,snapshots=[snapshot])


def contract_document() -> dict[str, Any]:
    b=reference_federation_governance_trust_policy_bundle()
    return {
        "ok": True,
        "release": CORE_RELEASE,
        "contract": CONTRACT_VERSION,
        "upstream_contracts": [V389_CONTRACT,V391_CONTRACT,V395_CONTRACT],
        "principles": {
            "trust_is_scoped_not_global": True,
            "node_state_is_revocable": True,
            "capability_permissions_are_explicit": True,
            "contract_allowlists_are_explicit": True,
            "signature_verification_is_separate_from_content_truth": True,
            "remote_content_requires_local_validation": True,
            "conflicts_are_preserved": True,
            "revocation_and_suspension_are_first_class": True,
            "policy_decisions_are_auditable": True,
            "historical_governance_records_are_immutable": True,
        },
        "boundaries": {
            "global_unscoped_trust_allowed": False,
            "trusted_node_establishes_content_truth": False,
            "valid_signature_establishes_content_truth": False,
            "policy_approval_creates_local_evidence": False,
            "remote_content_bypasses_local_validation": False,
            "federation_consensus_establishes_truth": False,
            "conflict_silent_overwrite_allowed": False,
            "suspended_node_may_exchange": False,
            "revoked_node_may_exchange": False,
            "governance_decision_promotes_epistemic_state": False,
            "identity_graph_mutation_performed": False,
            "relationship_graph_mutation_performed": False,
            "evidence_graph_mutation_performed": False,
        },
        "reference": {
            "nodes": len(b.nodes), "trust_scopes": len(b.trust_scopes), "permissions": len(b.permissions), "actions": len(b.actions), "intake_rules": len(b.intake_rules), "decisions": len(b.decisions), "conflicts": len(b.conflicts), "audit_events": len(b.audit_events), "snapshots": len(b.snapshots),
            "reference_only_decisions": sum(x.disposition==GovernanceDecisionDisposition.reference_only for x in b.decisions),
            "denied_decisions": sum(x.disposition==GovernanceDecisionDisposition.denied for x in b.decisions),
            "bundle_fingerprint_sha256": b.fingerprint(),
        },
        "database_migration": "none",
    }
