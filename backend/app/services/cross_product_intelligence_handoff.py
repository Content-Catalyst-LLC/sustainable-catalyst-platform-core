from __future__ import annotations

from enum import Enum
from functools import lru_cache
from typing import Any, Literal

from pydantic import BaseModel, Field, model_validator

from .computational_runtime_objects import canonical_sha256
from .unified_entity_evidence_query_api import EpistemicState, ResultValidationState
from .unified_runtime_policy_capability_negotiation import (
    CONTRACT_VERSION as V391_CONTRACT,
    ConsumerKind,
    CompatibilityStatus,
    reference_unified_runtime_policy_capability_negotiation_bundle,
)
from .investigation_session_research_context_runtime import (
    CONTRACT_VERSION as V393_CONTRACT,
    reference_investigation_session_research_context_bundle,
)

CORE_RELEASE = "3.94.0"
CONTRACT_VERSION = "sc.core.cross-product-intelligence-handoff.v1"


def _unique(values: list[str], label: str) -> None:
    if len(values) != len(set(values)):
        raise ValueError(f"{label} must be unique")


class HandoffAction(str, Enum):
    continue_investigation = "continue-investigation"
    resolve_sources = "resolve-sources"
    research_guidance = "research-guidance"
    experimental_analysis = "experimental-analysis"
    computational_analysis = "computational-analysis"
    geospatial_analysis = "geospatial-analysis"
    decision_analysis = "decision-analysis"


class HandoffStatus(str, Enum):
    accepted = "accepted"
    accepted_with_constraints = "accepted-with-constraints"
    rejected = "rejected"


class ReturnObjectKind(str, Enum):
    derived_context = "derived-context"
    analytical_result = "analytical-result"
    source_reference = "source-reference"
    experiment_result = "experiment-result"
    computational_result = "computational-result"
    geospatial_result = "geospatial-result"
    decision_context = "decision-context"


class CrossProductHandoffPolicy(BaseModel):
    policy_id: str = Field(min_length=3, max_length=500)
    preserve_source_contract_identity: Literal[True] = True
    preserve_epistemic_state: Literal[True] = True
    preserve_validation_state: Literal[True] = True
    preserve_provenance: Literal[True] = True
    preserve_contradictions: Literal[True] = True
    preserve_remote_reference_state: Literal[True] = True
    require_destination_capability_negotiation: Literal[True] = True
    require_explicit_requested_action: Literal[True] = True
    require_explicit_return_contract: Literal[True] = True
    require_attributed_handoff_trace: Literal[True] = True
    returned_outputs_require_validation_before_promotion: Literal[True] = True
    allow_epistemic_state_promotion_in_transit: Literal[False] = False
    allow_validation_bypass: Literal[False] = False
    allow_remote_reference_promotion: Literal[False] = False
    allow_destination_authority_escalation: Literal[False] = False
    allow_session_context_to_become_evidence: Literal[False] = False
    allow_graph_mutation_from_handoff: Literal[False] = False
    metadata: dict[str, Any] = Field(default_factory=dict)

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class ProductEndpointDescriptor(BaseModel):
    product_id: str = Field(min_length=3, max_length=500)
    consumer_ref: str = Field(min_length=3, max_length=500)
    consumer_kind: ConsumerKind
    negotiation_trace_ref: str = Field(min_length=3, max_length=500)
    accepted_actions: list[HandoffAction] = Field(min_length=1)
    declared_scopes: list[str] = Field(min_length=1)
    accepts_governed_context: Literal[True] = True
    preserves_epistemic_state: Literal[True] = True
    preserves_validation_state: Literal[True] = True
    preserves_provenance: Literal[True] = True
    requires_local_validation_for_remote_references: Literal[True] = True
    may_promote_epistemic_state_on_receipt: Literal[False] = False
    may_mutate_governed_graphs_on_receipt: Literal[False] = False
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_descriptor(self):
        _unique([x.value for x in self.accepted_actions], "accepted_actions")
        _unique(self.declared_scopes, "declared_scopes")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class HandoffPayloadBinding(BaseModel):
    payload_binding_id: str = Field(min_length=3, max_length=500)
    session_binding_ref: str = Field(min_length=3, max_length=500)
    source_contract: str = Field(min_length=3, max_length=500)
    source_object_ref: str = Field(min_length=3, max_length=1000)
    epistemic_state: EpistemicState
    validation_state: ResultValidationState
    provenance_refs: list[str] = Field(min_length=1)
    handoff_role: str = Field(min_length=3, max_length=500)
    payload_preserves_source_state: Literal[True] = True
    payload_is_not_evidence_creation: Literal[True] = True
    payload_is_not_truth_certification: Literal[True] = True
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_payload(self):
        _unique(self.provenance_refs, "provenance_refs")
        if self.epistemic_state == EpistemicState.remote_reference and self.validation_state != ResultValidationState.local_validation_required:
            raise ValueError("remote-reference payload requires local-validation-required")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class HandoffCapabilityRequirement(BaseModel):
    requirement_id: str = Field(min_length=3, max_length=500)
    destination_ref: str = Field(min_length=3, max_length=500)
    required_negotiation_trace_ref: str = Field(min_length=3, max_length=500)
    requested_action: HandoffAction
    requested_scopes: list[str] = Field(min_length=1)
    requires_epistemic_state_preservation: Literal[True] = True
    requires_validation_state_preservation: Literal[True] = True
    requires_provenance_preservation: Literal[True] = True
    requires_review_gate_preservation: Literal[True] = True
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_requirement(self):
        _unique(self.requested_scopes, "requested_scopes")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class HandoffReturnContract(BaseModel):
    return_contract_id: str = Field(min_length=3, max_length=500)
    destination_ref: str = Field(min_length=3, max_length=500)
    allowed_return_kinds: list[ReturnObjectKind] = Field(min_length=1)
    return_to_session_ref: str = Field(min_length=3, max_length=500)
    return_to_checkpoint_ref: str = Field(min_length=3, max_length=500)
    returned_outputs_are_derived_not_upstream_facts: Literal[True] = True
    preserve_input_provenance_links: Literal[True] = True
    preserve_remote_reference_state: Literal[True] = True
    require_validation_before_epistemic_promotion: Literal[True] = True
    require_explicit_merge_or_acceptance_step: Literal[True] = True
    may_overwrite_session_checkpoint: Literal[False] = False
    may_mutate_governed_graphs: Literal[False] = False
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_return(self):
        _unique([x.value for x in self.allowed_return_kinds], "allowed_return_kinds")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class CrossProductIntelligenceHandoffRequest(BaseModel):
    request_id: str = Field(min_length=3, max_length=500)
    policy_ref: str = Field(min_length=3, max_length=500)
    destination_ref: str = Field(min_length=3, max_length=500)
    session_ref: str = Field(min_length=3, max_length=500)
    checkpoint_ref: str = Field(min_length=3, max_length=500)
    payload_binding_refs: list[str] = Field(min_length=1)
    capability_requirement_ref: str = Field(min_length=3, max_length=500)
    return_contract_ref: str = Field(min_length=3, max_length=500)
    action: HandoffAction
    requested_scopes: list[str] = Field(min_length=1)
    requested_at: str = Field(min_length=10, max_length=80)
    session_context_remains_working_context: Literal[True] = True
    request_does_not_promote_payload_state: Literal[True] = True
    request_does_not_authorize_graph_mutation: Literal[True] = True
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_request(self):
        _unique(self.payload_binding_refs, "payload_binding_refs")
        _unique(self.requested_scopes, "requested_scopes")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class CrossProductHandoffReceipt(BaseModel):
    receipt_id: str = Field(min_length=3, max_length=500)
    request_ref: str = Field(min_length=3, max_length=500)
    destination_ref: str = Field(min_length=3, max_length=500)
    status: HandoffStatus
    accepted_payload_refs: list[str] = Field(default_factory=list)
    rejected_payload_refs: list[str] = Field(default_factory=list)
    granted_scopes: list[str] = Field(default_factory=list)
    applied_constraints: list[str] = Field(min_length=1)
    received_at: str = Field(min_length=10, max_length=80)
    receipt_is_not_content_validation: Literal[True] = True
    receipt_is_not_truth_assessment: Literal[True] = True
    receipt_does_not_promote_payload_state: Literal[True] = True
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_receipt(self):
        for label, values in [
            ("accepted_payload_refs", self.accepted_payload_refs),
            ("rejected_payload_refs", self.rejected_payload_refs),
            ("granted_scopes", self.granted_scopes),
            ("applied_constraints", self.applied_constraints),
        ]:
            _unique(values, label)
        if set(self.accepted_payload_refs) & set(self.rejected_payload_refs):
            raise ValueError("payload cannot be both accepted and rejected")
        if self.status == HandoffStatus.rejected and self.granted_scopes:
            raise ValueError("rejected handoff cannot grant scopes")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class CrossProductHandoffTrace(BaseModel):
    trace_id: str = Field(min_length=3, max_length=500)
    request_ref: str = Field(min_length=3, max_length=500)
    receipt_ref: str = Field(min_length=3, max_length=500)
    return_contract_ref: str = Field(min_length=3, max_length=500)
    negotiation_trace_ref: str = Field(min_length=3, max_length=500)
    session_trace_ref: str = Field(min_length=3, max_length=500)
    started_at: str = Field(min_length=10, max_length=80)
    ended_at: str = Field(min_length=10, max_length=80)
    deterministic_trace_fingerprint_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    source_contracts_preserved: Literal[True] = True
    epistemic_states_preserved: Literal[True] = True
    validation_states_preserved: Literal[True] = True
    provenance_preserved: Literal[True] = True
    contradictions_preserved: Literal[True] = True
    remote_reference_state_preserved: Literal[True] = True
    graph_mutation_performed: Literal[False] = False
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_trace(self):
        if self.ended_at < self.started_at:
            raise ValueError("ended_at must not precede started_at")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class CrossProductHandoffSnapshot(BaseModel):
    snapshot_id: str = Field(min_length=3, max_length=500)
    policy_ref: str = Field(min_length=3, max_length=500)
    request_refs: list[str] = Field(min_length=1)
    receipt_refs: list[str] = Field(min_length=1)
    trace_refs: list[str] = Field(min_length=1)
    as_of: str = Field(min_length=10, max_length=80)
    immutable: Literal[True] = True
    supersedable: Literal[True] = True
    snapshot_is_not_truth_certification: Literal[True] = True
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_snapshot(self):
        _unique(self.request_refs, "request_refs")
        _unique(self.receipt_refs, "receipt_refs")
        _unique(self.trace_refs, "trace_refs")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class CrossProductIntelligenceHandoffBundle(BaseModel):
    release: Literal["3.94.0"] = "3.94.0"
    contract: Literal["sc.core.cross-product-intelligence-handoff.v1"] = CONTRACT_VERSION
    session_contract: Literal["sc.core.investigation-session-research-context-runtime.v1"] = V393_CONTRACT
    negotiation_contract: Literal["sc.core.unified-runtime-policy-capability-negotiation.v1"] = V391_CONTRACT
    policies: list[CrossProductHandoffPolicy] = Field(min_length=1)
    products: list[ProductEndpointDescriptor] = Field(min_length=1)
    payload_bindings: list[HandoffPayloadBinding] = Field(min_length=1)
    capability_requirements: list[HandoffCapabilityRequirement] = Field(min_length=1)
    return_contracts: list[HandoffReturnContract] = Field(min_length=1)
    requests: list[CrossProductIntelligenceHandoffRequest] = Field(min_length=1)
    receipts: list[CrossProductHandoffReceipt] = Field(min_length=1)
    traces: list[CrossProductHandoffTrace] = Field(min_length=1)
    snapshots: list[CrossProductHandoffSnapshot] = Field(min_length=1)
    identity_graph_mutation_performed: Literal[False] = False
    relationship_graph_mutation_performed: Literal[False] = False
    evidence_graph_mutation_performed: Literal[False] = False

    @model_validator(mode="after")
    def validate_bundle(self):
        groups = {
            "policy": [x.policy_id for x in self.policies],
            "product": [x.product_id for x in self.products],
            "payload": [x.payload_binding_id for x in self.payload_bindings],
            "requirement": [x.requirement_id for x in self.capability_requirements],
            "return": [x.return_contract_id for x in self.return_contracts],
            "request": [x.request_id for x in self.requests],
            "receipt": [x.receipt_id for x in self.receipts],
            "trace": [x.trace_id for x in self.traces],
            "snapshot": [x.snapshot_id for x in self.snapshots],
        }
        for label, vals in groups.items():
            _unique(vals, f"{label} ids")
        ids = {k: set(v) for k, v in groups.items()}
        product_by = {x.product_id: x for x in self.products}
        payload_by = {x.payload_binding_id: x for x in self.payload_bindings}
        requirement_by = {x.requirement_id: x for x in self.capability_requirements}
        return_by = {x.return_contract_id: x for x in self.return_contracts}
        request_by = {x.request_id: x for x in self.requests}
        receipt_by = {x.receipt_id: x for x in self.receipts}

        session_bundle = reference_investigation_session_research_context_bundle()
        session_ids = {x.session_id for x in session_bundle.sessions}
        checkpoint_ids = {x.checkpoint_id for x in session_bundle.checkpoints}
        session_trace_ids = {x.trace_id for x in session_bundle.traces}
        source_bindings = {x.binding_id: x for x in session_bundle.bindings}

        negotiation = reference_unified_runtime_policy_capability_negotiation_bundle()
        consumers = {x.consumer_id: x for x in negotiation.consumers}
        negotiation_traces = {x.trace_id: x for x in negotiation.traces}

        for p in self.products:
            if p.consumer_ref not in consumers or p.negotiation_trace_ref not in negotiation_traces:
                raise ValueError("product negotiation reference unresolved")
            consumer = consumers[p.consumer_ref]
            trace = negotiation_traces[p.negotiation_trace_ref]
            if consumer.consumer_kind != p.consumer_kind or trace.consumer_ref != p.consumer_ref:
                raise ValueError("product descriptor must preserve negotiated consumer identity")
            if set(p.declared_scopes) != set(consumer.declared_scopes):
                raise ValueError("product descriptor must preserve consumer declared scopes")

        for pb in self.payload_bindings:
            if pb.session_binding_ref not in source_bindings:
                raise ValueError("payload source binding unresolved")
            src = source_bindings[pb.session_binding_ref]
            if (
                pb.source_contract != src.source_contract
                or pb.source_object_ref != src.source_object_ref
                or pb.epistemic_state != src.epistemic_state
                or pb.validation_state != src.validation_state
                or set(pb.provenance_refs) != set(src.provenance_refs)
            ):
                raise ValueError("payload binding must preserve upstream session binding state")

        for req in self.capability_requirements:
            if req.destination_ref not in ids["product"] or req.required_negotiation_trace_ref not in negotiation_traces:
                raise ValueError("handoff capability requirement unresolved")
            product = product_by[req.destination_ref]
            if req.required_negotiation_trace_ref != product.negotiation_trace_ref:
                raise ValueError("handoff requirement must use destination negotiation trace")
            if req.requested_action not in product.accepted_actions:
                raise ValueError("destination does not accept requested action")
            if not set(req.requested_scopes) <= set(product.declared_scopes):
                raise ValueError("handoff requirement exceeds destination declared scopes")

        for rc in self.return_contracts:
            if rc.destination_ref not in ids["product"] or rc.return_to_session_ref not in session_ids or rc.return_to_checkpoint_ref not in checkpoint_ids:
                raise ValueError("return contract reference unresolved")

        for rq in self.requests:
            if rq.policy_ref not in ids["policy"] or rq.destination_ref not in ids["product"]:
                raise ValueError("handoff request policy/product unresolved")
            if rq.session_ref not in session_ids or rq.checkpoint_ref not in checkpoint_ids:
                raise ValueError("handoff request session context unresolved")
            if not set(rq.payload_binding_refs) <= ids["payload"]:
                raise ValueError("handoff request payload unresolved")
            if rq.capability_requirement_ref not in ids["requirement"] or rq.return_contract_ref not in ids["return"]:
                raise ValueError("handoff request control reference unresolved")
            req = requirement_by[rq.capability_requirement_ref]
            rc = return_by[rq.return_contract_ref]
            if req.destination_ref != rq.destination_ref or rc.destination_ref != rq.destination_ref:
                raise ValueError("handoff request control objects target another destination")
            if req.requested_action != rq.action or set(req.requested_scopes) != set(rq.requested_scopes):
                raise ValueError("handoff request must match capability requirement")
            if not set(rq.requested_scopes) <= set(product_by[rq.destination_ref].declared_scopes):
                raise ValueError("handoff request exceeds destination scopes")
            # Any remote reference remains explicitly local-validation-required in transit.
            for pid in rq.payload_binding_refs:
                p = payload_by[pid]
                if p.epistemic_state == EpistemicState.remote_reference and p.validation_state != ResultValidationState.local_validation_required:
                    raise ValueError("remote reference validation boundary weakened in handoff")

        for rr in self.receipts:
            if rr.request_ref not in ids["request"] or rr.destination_ref not in ids["product"]:
                raise ValueError("handoff receipt reference unresolved")
            rq = request_by[rr.request_ref]
            if rr.destination_ref != rq.destination_ref:
                raise ValueError("handoff receipt destination mismatch")
            if not set(rr.accepted_payload_refs + rr.rejected_payload_refs) <= set(rq.payload_binding_refs):
                raise ValueError("handoff receipt contains payload outside request")
            if set(rr.granted_scopes) - set(rq.requested_scopes):
                raise ValueError("handoff receipt escalates scopes")
            if rr.status != HandoffStatus.rejected and set(rr.accepted_payload_refs) | set(rr.rejected_payload_refs) != set(rq.payload_binding_refs):
                raise ValueError("handoff receipt must disposition every requested payload")

        for tr in self.traces:
            if tr.request_ref not in ids["request"] or tr.receipt_ref not in ids["receipt"] or tr.return_contract_ref not in ids["return"]:
                raise ValueError("handoff trace reference unresolved")
            rq = request_by[tr.request_ref]
            rr = receipt_by[tr.receipt_ref]
            if rr.request_ref != rq.request_id or tr.return_contract_ref != rq.return_contract_ref:
                raise ValueError("handoff trace objects do not describe same request")
            if tr.negotiation_trace_ref != product_by[rq.destination_ref].negotiation_trace_ref:
                raise ValueError("handoff trace negotiation reference mismatch")
            if tr.session_trace_ref not in session_trace_ids:
                raise ValueError("handoff trace session trace unresolved")

        for sn in self.snapshots:
            if sn.policy_ref not in ids["policy"] or not set(sn.request_refs) <= ids["request"] or not set(sn.receipt_refs) <= ids["receipt"] or not set(sn.trace_refs) <= ids["trace"]:
                raise ValueError("handoff snapshot reference unresolved")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


_ACTIONS = {
    ConsumerKind.workspace: HandoffAction.continue_investigation,
    ConsumerKind.knowledge_library: HandoffAction.resolve_sources,
    ConsumerKind.research_librarian: HandoffAction.research_guidance,
    ConsumerKind.research_lab: HandoffAction.experimental_analysis,
    ConsumerKind.workbench: HandoffAction.computational_analysis,
    ConsumerKind.site_intelligence: HandoffAction.geospatial_analysis,
    ConsumerKind.decision_studio: HandoffAction.decision_analysis,
}

_RETURN_KINDS = {
    ConsumerKind.workspace: [ReturnObjectKind.derived_context, ReturnObjectKind.analytical_result],
    ConsumerKind.knowledge_library: [ReturnObjectKind.source_reference, ReturnObjectKind.derived_context],
    ConsumerKind.research_librarian: [ReturnObjectKind.derived_context, ReturnObjectKind.source_reference],
    ConsumerKind.research_lab: [ReturnObjectKind.experiment_result, ReturnObjectKind.analytical_result],
    ConsumerKind.workbench: [ReturnObjectKind.computational_result, ReturnObjectKind.analytical_result],
    ConsumerKind.site_intelligence: [ReturnObjectKind.geospatial_result, ReturnObjectKind.derived_context],
    ConsumerKind.decision_studio: [ReturnObjectKind.decision_context, ReturnObjectKind.analytical_result],
}

# Payload subsets intentionally overlap. Sharing context does not make independent corroboration.
_PAYLOAD_INDEXES = {
    ConsumerKind.workspace: list(range(15)),
    ConsumerKind.knowledge_library: [0, 3, 4, 9, 12, 13, 14],
    ConsumerKind.research_librarian: [0, 3, 4, 5, 7, 9, 10, 13],
    ConsumerKind.research_lab: [0, 5, 6, 7, 8, 9, 10],
    ConsumerKind.workbench: [0, 6, 7, 8, 10, 11],
    ConsumerKind.site_intelligence: [0, 4, 6, 9, 10, 12],
    ConsumerKind.decision_studio: [0, 5, 8, 9, 10, 11, 12],
}


@lru_cache(maxsize=1)
def reference_cross_product_intelligence_handoff_bundle() -> CrossProductIntelligenceHandoffBundle:
    sessions = reference_investigation_session_research_context_bundle()
    negotiation = reference_unified_runtime_policy_capability_negotiation_bundle()
    session = sessions.sessions[0]
    checkpoint = sessions.checkpoints[0]
    session_trace = sessions.traces[0]
    policy = CrossProductHandoffPolicy(policy_id="cross-product-handoff-policy:default:v1")

    traces_by_consumer = {x.consumer_ref: x for x in negotiation.traces}
    products: list[ProductEndpointDescriptor] = []
    for consumer in negotiation.consumers:
        if consumer.consumer_kind == ConsumerKind.external:
            continue
        products.append(ProductEndpointDescriptor(
            product_id=f"product:{consumer.consumer_kind.value}",
            consumer_ref=consumer.consumer_id,
            consumer_kind=consumer.consumer_kind,
            negotiation_trace_ref=traces_by_consumer[consumer.consumer_id].trace_id,
            accepted_actions=[_ACTIONS[consumer.consumer_kind]],
            declared_scopes=list(consumer.declared_scopes),
        ))

    payloads = [HandoffPayloadBinding(
        payload_binding_id=f"handoff-payload:{i:02d}",
        session_binding_ref=b.binding_id,
        source_contract=b.source_contract,
        source_object_ref=b.source_object_ref,
        epistemic_state=b.epistemic_state,
        validation_state=b.validation_state,
        provenance_refs=list(b.provenance_refs),
        handoff_role="governed-session-context",
    ) for i, b in enumerate(sessions.bindings, 1)]

    requirements: list[HandoffCapabilityRequirement] = []
    returns: list[HandoffReturnContract] = []
    requests: list[CrossProductIntelligenceHandoffRequest] = []
    receipts: list[CrossProductHandoffReceipt] = []
    handoff_traces: list[CrossProductHandoffTrace] = []
    now = "2026-10-01T03:30:00Z"
    end = "2026-10-01T03:30:01Z"

    for product in products:
        kind = product.consumer_kind
        action = _ACTIONS[kind]
        # Use all scopes needed for already-negotiated product operation. No new scope is introduced by handoff.
        requested_scopes = list(product.declared_scopes)
        req = HandoffCapabilityRequirement(
            requirement_id=f"handoff-requirement:{kind.value}:v1",
            destination_ref=product.product_id,
            required_negotiation_trace_ref=product.negotiation_trace_ref,
            requested_action=action,
            requested_scopes=requested_scopes,
        )
        rc = HandoffReturnContract(
            return_contract_id=f"handoff-return:{kind.value}:v1",
            destination_ref=product.product_id,
            allowed_return_kinds=_RETURN_KINDS[kind],
            return_to_session_ref=session.session_id,
            return_to_checkpoint_ref=checkpoint.checkpoint_id,
        )
        selected = [payloads[i].payload_binding_id for i in _PAYLOAD_INDEXES[kind]]
        rq = CrossProductIntelligenceHandoffRequest(
            request_id=f"handoff-request:{kind.value}:v1",
            policy_ref=policy.policy_id,
            destination_ref=product.product_id,
            session_ref=session.session_id,
            checkpoint_ref=checkpoint.checkpoint_id,
            payload_binding_refs=selected,
            capability_requirement_ref=req.requirement_id,
            return_contract_ref=rc.return_contract_id,
            action=action,
            requested_scopes=requested_scopes,
            requested_at=now,
        )
        includes_remote = any(next(x for x in payloads if x.payload_binding_id == pid).epistemic_state == EpistemicState.remote_reference for pid in selected)
        negotiation_trace = traces_by_consumer[product.consumer_ref]
        constrained = includes_remote or negotiation_trace.final_status in {CompatibilityStatus.degraded, CompatibilityStatus.compatible_with_constraints}
        status = HandoffStatus.accepted_with_constraints if constrained else HandoffStatus.accepted
        constraints = ["preserve-source-contract", "preserve-epistemic-state", "preserve-validation-state", "preserve-provenance", "no-governed-graph-mutation"]
        if includes_remote:
            constraints.extend(["remote-reference-remains-remote", "local-validation-required-before-promotion"])
        if negotiation_trace.final_status == CompatibilityStatus.degraded:
            constraints.append("respect-negotiated-degraded-mode")
        rr = CrossProductHandoffReceipt(
            receipt_id=f"handoff-receipt:{kind.value}:v1",
            request_ref=rq.request_id,
            destination_ref=product.product_id,
            status=status,
            accepted_payload_refs=selected,
            rejected_payload_refs=[],
            granted_scopes=requested_scopes,
            applied_constraints=constraints,
            received_at=end,
        )
        seed = {"request": rq.fingerprint(), "receipt": rr.fingerprint(), "return": rc.fingerprint(), "negotiation": product.negotiation_trace_ref, "session_trace": session_trace.trace_id}
        tr = CrossProductHandoffTrace(
            trace_id=f"handoff-trace:{kind.value}:v1",
            request_ref=rq.request_id,
            receipt_ref=rr.receipt_id,
            return_contract_ref=rc.return_contract_id,
            negotiation_trace_ref=product.negotiation_trace_ref,
            session_trace_ref=session_trace.trace_id,
            started_at=now,
            ended_at=end,
            deterministic_trace_fingerprint_sha256=canonical_sha256(seed),
        )
        requirements.append(req); returns.append(rc); requests.append(rq); receipts.append(rr); handoff_traces.append(tr)

    snap = CrossProductHandoffSnapshot(
        snapshot_id="cross-product-handoff-snapshot:synthetic:v1",
        policy_ref=policy.policy_id,
        request_refs=[x.request_id for x in requests],
        receipt_refs=[x.receipt_id for x in receipts],
        trace_refs=[x.trace_id for x in handoff_traces],
        as_of=end,
    )
    return CrossProductIntelligenceHandoffBundle(
        policies=[policy], products=products, payload_bindings=payloads, capability_requirements=requirements,
        return_contracts=returns, requests=requests, receipts=receipts, traces=handoff_traces, snapshots=[snap],
    )


def contract_document() -> dict[str, Any]:
    b = reference_cross_product_intelligence_handoff_bundle()
    remote = sum(1 for x in b.payload_bindings if x.epistemic_state == EpistemicState.remote_reference)
    constrained = sum(1 for x in b.receipts if x.status == HandoffStatus.accepted_with_constraints)
    return {
        "ok": True,
        "release": CORE_RELEASE,
        "contract": CONTRACT_VERSION,
        "session_contract": V393_CONTRACT,
        "negotiation_contract": V391_CONTRACT,
        "principles": {
            "cross_product_handoff_is_contract_preserving": True,
            "source_contract_identity_preserved": True,
            "epistemic_state_preserved": True,
            "validation_state_preserved": True,
            "provenance_preserved": True,
            "contradictions_preserved": True,
            "remote_reference_state_preserved": True,
            "destination_capability_negotiation_required": True,
            "return_path_is_explicit": True,
            "returned_outputs_require_validation_before_promotion": True,
            "session_context_remains_working_context": True,
        },
        "boundaries": {
            "handoff_creates_evidence": False,
            "handoff_promotes_epistemic_state": False,
            "handoff_bypasses_validation": False,
            "handoff_bypasses_review": False,
            "handoff_escalates_destination_authority": False,
            "remote_reference_becomes_local_evidence": False,
            "receipt_is_content_validation": False,
            "receipt_is_truth_assessment": False,
            "returned_output_is_automatically_graph_fact": False,
            "shared_context_is_independent_corroboration": False,
            "identity_graph_mutation_performed": False,
            "relationship_graph_mutation_performed": False,
            "evidence_graph_mutation_performed": False,
        },
        "reference": {
            "policies": len(b.policies),
            "products": len(b.products),
            "payload_bindings": len(b.payload_bindings),
            "capability_requirements": len(b.capability_requirements),
            "return_contracts": len(b.return_contracts),
            "requests": len(b.requests),
            "receipts": len(b.receipts),
            "traces": len(b.traces),
            "snapshots": len(b.snapshots),
            "remote_reference_payloads": remote,
            "constrained_receipts": constrained,
            "bundle_fingerprint_sha256": b.fingerprint(),
        },
        "database_migration": "none",
    }
