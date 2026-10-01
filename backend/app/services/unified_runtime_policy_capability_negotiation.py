from __future__ import annotations

from enum import Enum
from functools import lru_cache
from typing import Any, Literal

from pydantic import BaseModel, Field, model_validator

from .computational_runtime_objects import canonical_sha256
from .unified_entity_evidence_intelligence_runtime import (
    CONTRACT_VERSION as V390_CONTRACT,
    reference_unified_entity_evidence_intelligence_runtime_bundle,
)

CORE_RELEASE = "3.91.0"
CONTRACT_VERSION = "sc.core.unified-runtime-policy-capability-negotiation.v1"


def _unique(values: list[str], label: str) -> None:
    if len(values) != len(set(values)):
        raise ValueError(f"{label} must be unique")


class CapabilityAvailability(str, Enum):
    active = "active"
    degraded = "degraded"
    unavailable = "unavailable"


class CompatibilityStatus(str, Enum):
    compatible = "compatible"
    compatible_with_constraints = "compatible-with-constraints"
    degraded = "degraded"
    rejected = "rejected"


class FallbackMode(str, Enum):
    fail_closed = "fail-closed"
    reference_only = "reference-only"
    degraded_read_only = "degraded-read-only"


class ConsumerKind(str, Enum):
    workspace = "workspace"
    knowledge_library = "knowledge-library"
    research_librarian = "research-librarian"
    research_lab = "research-lab"
    workbench = "workbench"
    site_intelligence = "site-intelligence"
    decision_studio = "decision-studio"
    external = "external"


class RuntimeCapabilityDescriptor(BaseModel):
    capability_id: str = Field(min_length=3, max_length=500)
    release: str = Field(pattern=r"^3\.(?:7[7-9]|8[0-9]|90)\.0$")
    contract: str = Field(min_length=3, max_length=500)
    endpoint: str = Field(min_length=2, max_length=1000)
    availability: CapabilityAvailability
    required_scopes: list[str] = Field(default_factory=list)
    governance_constraints: list[str] = Field(min_length=1)
    dependency_refs: list[str] = Field(default_factory=list)
    schema_fingerprint_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    degraded_mode_supported: bool = False
    preserves_upstream_contract_identity: Literal[True] = True
    preserves_epistemic_state: Literal[True] = True
    preserves_provenance: Literal[True] = True
    capability_availability_is_not_truth_signal: Literal[True] = True
    may_mutate_governed_graphs: Literal[False] = False
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_descriptor(self):
        _unique(self.required_scopes, "required_scopes")
        _unique(self.governance_constraints, "governance_constraints")
        _unique(self.dependency_refs, "dependency_refs")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class ConsumerCapabilityRequirement(BaseModel):
    requirement_id: str = Field(min_length=3, max_length=500)
    capability_ref: str = Field(min_length=3, max_length=500)
    minimum_release: str = Field(pattern=r"^3\.(?:7[7-9]|8[0-9]|90)\.0$")
    required_contract: str = Field(min_length=3, max_length=500)
    required_scopes: list[str] = Field(default_factory=list)
    optional: bool = False
    allow_degraded: bool = False
    allow_reference_only: bool = False
    requires_epistemic_state_preservation: Literal[True] = True
    requires_provenance_preservation: Literal[True] = True
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_requirement(self):
        _unique(self.required_scopes, "required_scopes")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class RuntimeConsumerProfile(BaseModel):
    consumer_id: str = Field(min_length=3, max_length=500)
    consumer_kind: ConsumerKind
    requirement_refs: list[str] = Field(min_length=1)
    declared_scopes: list[str] = Field(min_length=1)
    accepts_degraded_mode: bool = False
    accepts_reference_only_outputs: bool = False
    preserve_epistemic_state: Literal[True] = True
    preserve_provenance: Literal[True] = True
    no_graph_mutation_requested: Literal[True] = True
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_profile(self):
        _unique(self.requirement_refs, "requirement_refs")
        _unique(self.declared_scopes, "declared_scopes")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class RuntimeNegotiationPolicy(BaseModel):
    policy_id: str = Field(min_length=3, max_length=500)
    require_exact_contract_identity: Literal[True] = True
    enforce_minimum_release: Literal[True] = True
    grant_only_declared_scope_intersection: Literal[True] = True
    preserve_upstream_epistemic_state: Literal[True] = True
    preserve_upstream_provenance: Literal[True] = True
    preserve_review_and_validation_gates: Literal[True] = True
    require_explicit_degradation: Literal[True] = True
    require_explicit_fallback: Literal[True] = True
    require_auditable_decision_trace: Literal[True] = True
    allow_scope_escalation: Literal[False] = False
    allow_boundary_weakening: Literal[False] = False
    allow_candidate_promotion: Literal[False] = False
    allow_hypothesis_promotion: Literal[False] = False
    allow_local_validation_bypass: Literal[False] = False
    allow_human_review_bypass: Literal[False] = False
    metadata: dict[str, Any] = Field(default_factory=dict)

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class RuntimeFallbackRule(BaseModel):
    fallback_rule_id: str = Field(min_length=3, max_length=500)
    capability_ref: str = Field(min_length=3, max_length=500)
    trigger_availability: list[CapabilityAvailability] = Field(min_length=1)
    mode: FallbackMode
    output_epistemic_state: str = Field(min_length=3, max_length=500)
    granted_scope_ceiling: list[str] = Field(default_factory=list)
    reason: str = Field(min_length=3, max_length=4000)
    fallback_may_not_increase_authority: Literal[True] = True
    fallback_may_not_promote_graph_fact: Literal[True] = True
    fallback_preserves_provenance: Literal[True] = True
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_fallback(self):
        _unique([x.value for x in self.trigger_availability], "trigger_availability")
        _unique(self.granted_scope_ceiling, "granted_scope_ceiling")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class CapabilityNegotiationDecision(BaseModel):
    decision_id: str = Field(min_length=3, max_length=500)
    policy_ref: str = Field(min_length=3, max_length=500)
    consumer_ref: str = Field(min_length=3, max_length=500)
    requirement_ref: str = Field(min_length=3, max_length=500)
    capability_ref: str = Field(min_length=3, max_length=500)
    status: CompatibilityStatus
    granted_scopes: list[str] = Field(default_factory=list)
    applied_constraints: list[str] = Field(min_length=1)
    fallback_ref: str | None = None
    contract_identity_preserved: Literal[True] = True
    release_requirement_satisfied: Literal[True] = True
    epistemic_boundaries_preserved: Literal[True] = True
    provenance_preserved: Literal[True] = True
    review_gates_preserved: Literal[True] = True
    decision_is_not_content_validation: Literal[True] = True
    decision_is_not_truth_assessment: Literal[True] = True
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_decision(self):
        _unique(self.granted_scopes, "granted_scopes")
        _unique(self.applied_constraints, "applied_constraints")
        if self.status == CompatibilityStatus.degraded and not self.fallback_ref:
            raise ValueError("degraded decisions require fallback_ref")
        if self.status == CompatibilityStatus.rejected and self.granted_scopes:
            raise ValueError("rejected decisions may not grant scopes")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class RuntimeNegotiationTrace(BaseModel):
    trace_id: str = Field(min_length=3, max_length=500)
    policy_ref: str = Field(min_length=3, max_length=500)
    consumer_ref: str = Field(min_length=3, max_length=500)
    decision_refs: list[str] = Field(min_length=1)
    fallback_refs: list[str] = Field(default_factory=list)
    final_status: CompatibilityStatus
    negotiated_at: str = Field(min_length=10, max_length=80)
    deterministic_trace_fingerprint_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    trace_is_not_authorization_to_weaken_policy: Literal[True] = True
    trace_is_not_content_validation: Literal[True] = True
    trace_is_not_truth_assessment: Literal[True] = True
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_trace(self):
        _unique(self.decision_refs, "decision_refs")
        _unique(self.fallback_refs, "fallback_refs")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class CapabilityRegistrySnapshot(BaseModel):
    snapshot_id: str = Field(min_length=3, max_length=500)
    policy_ref: str = Field(min_length=3, max_length=500)
    capability_refs: list[str] = Field(min_length=1)
    consumer_refs: list[str] = Field(min_length=1)
    trace_refs: list[str] = Field(min_length=1)
    as_of: str = Field(min_length=10, max_length=80)
    immutable: Literal[True] = True
    snapshot_is_not_runtime_authority: Literal[True] = True
    availability_state_is_not_truth_signal: Literal[True] = True
    later_capability_state_may_supersede_snapshot: Literal[True] = True
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_snapshot(self):
        _unique(self.capability_refs, "capability_refs")
        _unique(self.consumer_refs, "consumer_refs")
        _unique(self.trace_refs, "trace_refs")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class UnifiedRuntimePolicyCapabilityNegotiationBundle(BaseModel):
    release: Literal["3.91.0"] = "3.91.0"
    contract: Literal["sc.core.unified-runtime-policy-capability-negotiation.v1"] = CONTRACT_VERSION
    capabilities: list[RuntimeCapabilityDescriptor] = Field(min_length=14, max_length=14)
    requirements: list[ConsumerCapabilityRequirement] = Field(min_length=1)
    consumers: list[RuntimeConsumerProfile] = Field(min_length=1)
    policies: list[RuntimeNegotiationPolicy] = Field(min_length=1)
    fallback_rules: list[RuntimeFallbackRule] = Field(default_factory=list)
    decisions: list[CapabilityNegotiationDecision] = Field(min_length=1)
    traces: list[RuntimeNegotiationTrace] = Field(min_length=1)
    snapshots: list[CapabilityRegistrySnapshot] = Field(min_length=1)
    identity_graph_mutation_performed: Literal[False] = False
    relationship_graph_mutation_performed: Literal[False] = False
    evidence_graph_mutation_performed: Literal[False] = False

    @model_validator(mode="after")
    def validate_bundle(self):
        groups = {
            "capability": [x.capability_id for x in self.capabilities],
            "requirement": [x.requirement_id for x in self.requirements],
            "consumer": [x.consumer_id for x in self.consumers],
            "policy": [x.policy_id for x in self.policies],
            "fallback": [x.fallback_rule_id for x in self.fallback_rules],
            "decision": [x.decision_id for x in self.decisions],
            "trace": [x.trace_id for x in self.traces],
            "snapshot": [x.snapshot_id for x in self.snapshots],
        }
        for label, vals in groups.items():
            _unique(vals, f"{label} ids")
        caps=set(groups["capability"]); reqs=set(groups["requirement"]); consumers=set(groups["consumer"])
        policies=set(groups["policy"]); fallbacks=set(groups["fallback"]); decisions=set(groups["decision"]); traces=set(groups["trace"])
        for cap in self.capabilities:
            if not set(cap.dependency_refs) <= caps:
                raise ValueError("capability dependency reference unresolved")
        req_by_id={x.requirement_id:x for x in self.requirements}
        cap_by_id={x.capability_id:x for x in self.capabilities}
        for req in self.requirements:
            if req.capability_ref not in caps:
                raise ValueError("requirement capability reference unresolved")
            cap=cap_by_id[req.capability_ref]
            if req.required_contract != cap.contract:
                raise ValueError("requirement contract does not match capability contract")
        consumer_by_id={x.consumer_id:x for x in self.consumers}
        for consumer in self.consumers:
            if not set(consumer.requirement_refs) <= reqs:
                raise ValueError("consumer requirement reference unresolved")
        fallback_by_id={x.fallback_rule_id:x for x in self.fallback_rules}
        for rule in self.fallback_rules:
            if rule.capability_ref not in caps:
                raise ValueError("fallback capability reference unresolved")
        decision_by_id={x.decision_id:x for x in self.decisions}
        for d in self.decisions:
            if d.policy_ref not in policies or d.consumer_ref not in consumers or d.requirement_ref not in reqs or d.capability_ref not in caps:
                raise ValueError("decision reference unresolved")
            req=req_by_id[d.requirement_ref]
            consumer=consumer_by_id[d.consumer_ref]
            if req.capability_ref != d.capability_ref or d.requirement_ref not in consumer.requirement_refs:
                raise ValueError("decision does not match consumer requirement")
            if not set(d.granted_scopes) <= set(req.required_scopes) & set(consumer.declared_scopes):
                raise ValueError("decision grants scope outside requirement/consumer intersection")
            if d.fallback_ref:
                if d.fallback_ref not in fallbacks or fallback_by_id[d.fallback_ref].capability_ref != d.capability_ref:
                    raise ValueError("decision fallback reference unresolved or mismatched")
        for tr in self.traces:
            if tr.policy_ref not in policies or tr.consumer_ref not in consumers or not set(tr.decision_refs) <= decisions or not set(tr.fallback_refs) <= fallbacks:
                raise ValueError("negotiation trace reference unresolved")
            if any(decision_by_id[x].consumer_ref != tr.consumer_ref for x in tr.decision_refs):
                raise ValueError("trace decision belongs to another consumer")
        for sn in self.snapshots:
            if sn.policy_ref not in policies or not set(sn.capability_refs) <= caps or not set(sn.consumer_refs) <= consumers or not set(sn.trace_refs) <= traces:
                raise ValueError("snapshot reference unresolved")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


_ENDPOINTS = {
    "3.77.0": "/public/v1/entity-resolution/contract",
    "3.78.0": "/public/v1/temporal-identity/contract",
    "3.79.0": "/public/v1/record-linkage/contract",
    "3.80.0": "/public/v1/entity-reconciliation/contract",
    "3.81.0": "/public/v1/documentary-sources/contract",
    "3.82.0": "/public/v1/relationship-discovery/contract",
    "3.83.0": "/public/v1/network-intelligence/contract",
    "3.84.0": "/public/v1/connection-paths/contract",
    "3.85.0": "/public/v1/multi-hop-reasoning/contract",
    "3.86.0": "/public/v1/contradiction-resolution/contract",
    "3.87.0": "/public/v1/entity-timeline/contract",
    "3.88.0": "/public/v1/graph-investigation-package/contract",
    "3.89.0": "/public/v1/federated-evidence-graph-exchange/contract",
    "3.90.0": "/public/v1/unified-entity-evidence-runtime/contract",
}


def _scope_for_release(release: str) -> list[str]:
    if release == "3.88.0": return ["read:provenance", "export:investigation-package"]
    if release == "3.89.0": return ["read:provenance", "read:federation"]
    if release == "3.90.0": return ["read:provenance", "execute:unified-runtime"]
    if release in {"3.83.0", "3.84.0", "3.85.0"}: return ["read:provenance", "execute:graph-analysis"]
    return ["read:provenance", "read:governed-objects"]


@lru_cache(maxsize=1)
def reference_unified_runtime_policy_capability_negotiation_bundle() -> UnifiedRuntimePolicyCapabilityNegotiationBundle:
    upstream=reference_unified_entity_evidence_intelligence_runtime_bundle()
    caps=[]
    previous=None
    constraints=["preserve-epistemic-state","preserve-provenance","preserve-review-gates","no-governed-graph-mutation"]
    for binding in upstream.capabilities:
        cid=f"runtime-capability:{binding.release.replace('.','')}"
        caps.append(RuntimeCapabilityDescriptor(
            capability_id=cid, release=binding.release, contract=binding.contract,
            endpoint=_ENDPOINTS[binding.release], availability=CapabilityAvailability.active,
            required_scopes=_scope_for_release(binding.release), governance_constraints=constraints,
            dependency_refs=[] if previous is None else [previous], schema_fingerprint_sha256=binding.reference_bundle_fingerprint_sha256,
            degraded_mode_supported=binding.release in {"3.88.0","3.89.0"},
        ))
        previous=cid
    caps.append(RuntimeCapabilityDescriptor(
        capability_id="runtime-capability:3900", release="3.90.0", contract=V390_CONTRACT,
        endpoint=_ENDPOINTS["3.90.0"], availability=CapabilityAvailability.active,
        required_scopes=_scope_for_release("3.90.0"), governance_constraints=constraints,
        dependency_refs=["runtime-capability:3890"], schema_fingerprint_sha256=upstream.fingerprint(), degraded_mode_supported=False,
    ))
    # Simulate a degraded federation capability while preserving its descriptor/contract identity.
    cap389=next(x for x in caps if x.release=="3.89.0")
    cap389.availability=CapabilityAvailability.degraded

    policy=RuntimeNegotiationPolicy(policy_id="runtime-negotiation-policy:default:v1")
    specs={
        ConsumerKind.workspace:[("3900",["read:provenance","execute:unified-runtime"],False,False), ("3880",["read:provenance","export:investigation-package"],False,False)],
        ConsumerKind.knowledge_library:[("3810",["read:provenance","read:governed-objects"],False,False), ("3800",["read:provenance","read:governed-objects"],False,False), ("3890",["read:provenance","read:federation"],True,True)],
        ConsumerKind.research_librarian:[("3900",["read:provenance","execute:unified-runtime"],False,False), ("3840",["read:provenance","execute:graph-analysis"],False,False), ("3850",["read:provenance","execute:graph-analysis"],False,False)],
        ConsumerKind.research_lab:[("3900",["read:provenance","execute:unified-runtime"],False,False), ("3830",["read:provenance","execute:graph-analysis"],False,False), ("3850",["read:provenance","execute:graph-analysis"],False,False)],
        ConsumerKind.workbench:[("3900",["read:provenance","execute:unified-runtime"],False,False), ("3880",["read:provenance","export:investigation-package"],False,False)],
        ConsumerKind.site_intelligence:[("3870",["read:provenance","read:governed-objects"],False,False), ("3830",["read:provenance","execute:graph-analysis"],False,False)],
        ConsumerKind.decision_studio:[("3900",["read:provenance","execute:unified-runtime"],False,False), ("3860",["read:provenance","read:governed-objects"],False,False)],
    }
    requirements=[]; consumers=[]
    capmap={x.release.replace('.',''):x for x in caps}
    for kind, entries in specs.items():
        reqids=[]; declared=[]
        for idx,(relkey, scopes, allow_degraded, allow_ref) in enumerate(entries,1):
            cap=capmap[relkey]
            rid=f"requirement:{kind.value}:{idx}"
            requirements.append(ConsumerCapabilityRequirement(
                requirement_id=rid, capability_ref=cap.capability_id, minimum_release=cap.release,
                required_contract=cap.contract, required_scopes=scopes, optional=False,
                allow_degraded=allow_degraded, allow_reference_only=allow_ref,
            ))
            reqids.append(rid); declared.extend(scopes)
        consumers.append(RuntimeConsumerProfile(
            consumer_id=f"consumer:{kind.value}", consumer_kind=kind, requirement_refs=reqids,
            declared_scopes=sorted(set(declared)), accepts_degraded_mode=(kind==ConsumerKind.knowledge_library),
            accepts_reference_only_outputs=(kind==ConsumerKind.knowledge_library),
        ))
    fallback=RuntimeFallbackRule(
        fallback_rule_id="fallback:federation:reference-only", capability_ref="runtime-capability:3890",
        trigger_availability=[CapabilityAvailability.degraded,CapabilityAvailability.unavailable],
        mode=FallbackMode.reference_only, output_epistemic_state="remote-reference-pending-local-validation",
        granted_scope_ceiling=["read:provenance","read:federation"],
        reason="Federation degradation falls back to reference-only intake; no local evidence promotion is allowed.",
    )
    reqmap={x.requirement_id:x for x in requirements}; capby={x.capability_id:x for x in caps}
    decisions=[]; traces=[]; now="2026-09-30T23:55:00Z"
    for consumer in consumers:
        decision_refs=[]; fallback_refs=[]
        for rid in consumer.requirement_refs:
            req=reqmap[rid]; cap=capby[req.capability_ref]
            granted=sorted(set(req.required_scopes)&set(consumer.declared_scopes))
            if cap.availability==CapabilityAvailability.degraded:
                status=CompatibilityStatus.degraded
                fb=fallback.fallback_rule_id
                fallback_refs.append(fb)
                applied=["explicit-degradation","reference-only-local-validation-required","preserve-remote-epistemic-state"]
            else:
                status=CompatibilityStatus.compatible_with_constraints if cap.release=="3.90.0" else CompatibilityStatus.compatible
                fb=None
                applied=["preserve-epistemic-state","preserve-provenance","preserve-review-gates"]
                if cap.release=="3.90.0": applied.append("no-global-truth-score")
            did=f"decision:{consumer.consumer_kind.value}:{cap.release.replace('.','')}"
            decisions.append(CapabilityNegotiationDecision(
                decision_id=did, policy_ref=policy.policy_id, consumer_ref=consumer.consumer_id,
                requirement_ref=rid, capability_ref=cap.capability_id, status=status,
                granted_scopes=granted, applied_constraints=applied, fallback_ref=fb,
            ))
            decision_refs.append(did)
        final=CompatibilityStatus.degraded if fallback_refs else (CompatibilityStatus.compatible_with_constraints if any(next(x for x in decisions if x.decision_id==d).status==CompatibilityStatus.compatible_with_constraints for d in decision_refs) else CompatibilityStatus.compatible)
        seed={"consumer":consumer.consumer_id,"decisions":decision_refs,"fallbacks":fallback_refs,"status":final.value,"at":now}
        traces.append(RuntimeNegotiationTrace(
            trace_id=f"negotiation-trace:{consumer.consumer_kind.value}:v1", policy_ref=policy.policy_id,
            consumer_ref=consumer.consumer_id, decision_refs=decision_refs, fallback_refs=fallback_refs,
            final_status=final, negotiated_at=now, deterministic_trace_fingerprint_sha256=canonical_sha256(seed),
        ))
    snapshot=CapabilityRegistrySnapshot(
        snapshot_id="capability-registry-snapshot:synthetic:v1", policy_ref=policy.policy_id,
        capability_refs=[x.capability_id for x in caps], consumer_refs=[x.consumer_id for x in consumers],
        trace_refs=[x.trace_id for x in traces], as_of=now,
    )
    return UnifiedRuntimePolicyCapabilityNegotiationBundle(
        capabilities=caps, requirements=requirements, consumers=consumers, policies=[policy],
        fallback_rules=[fallback], decisions=decisions, traces=traces, snapshots=[snapshot],
    )


def contract_document() -> dict[str, Any]:
    b=reference_unified_runtime_policy_capability_negotiation_bundle()
    degraded=sum(1 for x in b.capabilities if x.availability==CapabilityAvailability.degraded)
    return {
        "ok":True,"release":CORE_RELEASE,"contract":CONTRACT_VERSION,
        "principles":{
            "unified_control_plane_over_v3900_runtime":True,
            "capability_discovery_is_descriptive_not_authoritative":True,
            "negotiation_preserves_upstream_contract_identity":True,
            "negotiation_preserves_epistemic_state":True,
            "negotiation_preserves_provenance":True,
            "minimum_release_requirements_enforced":True,
            "permission_scope_intersection_enforced":True,
            "degradation_is_explicit":True,
            "fallbacks_reduce_or_preserve_authority_never_increase_it":True,
            "consumer_compatibility_is_auditable":True,
            "negotiation_trace_is_reproducible":True,
            "review_and_local_validation_gates_preserved":True,
        },
        "boundaries":{
            "negotiation_grants_undeclared_scope":False,
            "negotiation_weakens_epistemic_boundaries":False,
            "negotiation_converts_candidate_to_fact":False,
            "negotiation_converts_hypothesis_to_evidence":False,
            "negotiation_bypasses_local_validation":False,
            "negotiation_bypasses_human_review":False,
            "degraded_mode_increases_authority":False,
            "capability_availability_implies_truth":False,
            "contract_compatibility_implies_content_truth":False,
            "identity_graph_mutation_performed":False,
            "relationship_graph_mutation_performed":False,
            "evidence_graph_mutation_performed":False,
        },
        "reference":{
            "capabilities":len(b.capabilities),"requirements":len(b.requirements),"consumers":len(b.consumers),
            "decisions":len(b.decisions),"traces":len(b.traces),"fallback_rules":len(b.fallback_rules),
            "degraded_capabilities":degraded,"bundle_fingerprint_sha256":b.fingerprint(),
        },
        "database_migration":"none",
    }
