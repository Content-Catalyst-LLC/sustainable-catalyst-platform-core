from __future__ import annotations

from enum import Enum
from functools import lru_cache
from typing import Any, Literal

from pydantic import BaseModel, Field, model_validator

from .computational_runtime_objects import canonical_sha256
from .unified_entity_evidence_query_api import (
    CONTRACT_VERSION as V392_CONTRACT,
    EpistemicState,
    ResultValidationState,
    reference_unified_entity_evidence_query_bundle,
)

CORE_RELEASE = "3.93.0"
CONTRACT_VERSION = "sc.core.investigation-session-research-context-runtime.v1"


def _unique(values: list[str], label: str) -> None:
    if len(values) != len(set(values)):
        raise ValueError(f"{label} must be unique")


class SessionStatus(str, Enum):
    active = "active"
    paused = "paused"
    closed = "closed"
    archived = "archived"


class ContextBindingKind(str, Enum):
    entity = "entity"
    source = "source"
    query = "query"
    query_result = "query-result"
    hypothesis = "hypothesis"
    reasoning_trace = "reasoning-trace"
    contradiction = "contradiction"
    timeline = "timeline"
    investigation_package = "investigation-package"
    federation_reference = "federation-reference"
    runtime_metadata = "runtime-metadata"


class ContributionActorKind(str, Enum):
    human = "human"
    assistant = "assistant"
    runtime = "runtime"
    system = "system"


class HypothesisState(str, Enum):
    open = "open"
    supported = "supported"
    qualified = "qualified"
    contradicted = "contradicted"
    closed = "closed"


class InvestigationSessionPolicy(BaseModel):
    policy_id: str = Field(min_length=3, max_length=500)
    preserve_source_contract_identity: Literal[True] = True
    preserve_epistemic_state: Literal[True] = True
    preserve_validation_state: Literal[True] = True
    preserve_provenance: Literal[True] = True
    preserve_contradictions: Literal[True] = True
    preserve_remote_reference_state: Literal[True] = True
    require_attributed_context_changes: Literal[True] = True
    immutable_checkpoints: Literal[True] = True
    checkpoints_may_be_superseded: Literal[True] = True
    session_context_is_not_evidence: Literal[True] = True
    persisted_hypothesis_is_not_graph_fact: Literal[True] = True
    persisted_conclusion_is_not_truth_verdict: Literal[True] = True
    allow_epistemic_state_promotion: Literal[False] = False
    allow_validation_bypass: Literal[False] = False
    allow_remote_reference_promotion: Literal[False] = False
    allow_graph_mutation_from_session_state: Literal[False] = False
    metadata: dict[str, Any] = Field(default_factory=dict)

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class InvestigationSession(BaseModel):
    session_id: str = Field(min_length=3, max_length=500)
    policy_ref: str = Field(min_length=3, max_length=500)
    consumer_ref: str = Field(min_length=3, max_length=500)
    title: str = Field(min_length=3, max_length=1000)
    research_question: str = Field(min_length=3, max_length=8000)
    status: SessionStatus
    opened_at: str = Field(min_length=10, max_length=80)
    updated_at: str = Field(min_length=10, max_length=80)
    parent_session_ref: str | None = Field(default=None, max_length=500)
    session_is_working_context_not_evidence: Literal[True] = True
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_time(self):
        if self.updated_at < self.opened_at:
            raise ValueError("updated_at must not precede opened_at")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class ResearchContextBinding(BaseModel):
    binding_id: str = Field(min_length=3, max_length=500)
    session_ref: str = Field(min_length=3, max_length=500)
    binding_kind: ContextBindingKind
    source_contract: str = Field(min_length=3, max_length=500)
    source_object_ref: str = Field(min_length=3, max_length=1000)
    epistemic_state: EpistemicState
    validation_state: ResultValidationState
    provenance_refs: list[str] = Field(min_length=1)
    binding_role: str = Field(min_length=3, max_length=500)
    selected_at: str = Field(min_length=10, max_length=80)
    selected_by_contribution_ref: str = Field(min_length=3, max_length=500)
    context_selection_does_not_promote_source_state: Literal[True] = True
    context_selection_is_not_evidence_creation: Literal[True] = True
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_binding(self):
        _unique(self.provenance_refs, "provenance_refs")
        if self.epistemic_state == EpistemicState.remote_reference and self.validation_state != ResultValidationState.local_validation_required:
            raise ValueError("remote references require local-validation-required state")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class ResearchContextFilter(BaseModel):
    filter_id: str = Field(min_length=3, max_length=500)
    session_ref: str = Field(min_length=3, max_length=500)
    target_domains: list[str] = Field(min_length=1)
    allowed_epistemic_states: list[EpistemicState] = Field(min_length=1)
    include_remote_references: bool = False
    include_contradictions: bool = True
    valid_time_start: str | None = Field(default=None, max_length=80)
    valid_time_end: str | None = Field(default=None, max_length=80)
    filter_is_not_truth_filter: Literal[True] = True
    omitted_context_does_not_imply_nonexistence: Literal[True] = True
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_filter(self):
        _unique(self.target_domains, "target_domains")
        _unique([x.value for x in self.allowed_epistemic_states], "allowed_epistemic_states")
        if self.valid_time_start and self.valid_time_end and self.valid_time_start > self.valid_time_end:
            raise ValueError("valid_time_start must not follow valid_time_end")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class SessionHypothesis(BaseModel):
    hypothesis_id: str = Field(min_length=3, max_length=500)
    session_ref: str = Field(min_length=3, max_length=500)
    statement: str = Field(min_length=3, max_length=8000)
    state: HypothesisState
    supporting_binding_refs: list[str] = Field(default_factory=list)
    contradicting_binding_refs: list[str] = Field(default_factory=list)
    created_by_contribution_ref: str = Field(min_length=3, max_length=500)
    last_updated_by_contribution_ref: str = Field(min_length=3, max_length=500)
    persisted_hypothesis_is_not_graph_fact: Literal[True] = True
    hypothesis_state_is_not_truth_verdict: Literal[True] = True
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_hypothesis(self):
        _unique(self.supporting_binding_refs, "supporting_binding_refs")
        _unique(self.contradicting_binding_refs, "contradicting_binding_refs")
        if set(self.supporting_binding_refs) & set(self.contradicting_binding_refs):
            raise ValueError("binding cannot simultaneously support and contradict one hypothesis state")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class SessionContribution(BaseModel):
    contribution_id: str = Field(min_length=3, max_length=500)
    session_ref: str = Field(min_length=3, max_length=500)
    actor_kind: ContributionActorKind
    actor_ref: str = Field(min_length=3, max_length=500)
    action: str = Field(min_length=3, max_length=1000)
    input_refs: list[str] = Field(default_factory=list)
    created_or_updated_refs: list[str] = Field(default_factory=list)
    contributed_at: str = Field(min_length=10, max_length=80)
    attribution_is_not_authority: Literal[True] = True
    contribution_is_not_evidence: Literal[True] = True
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_contribution(self):
        _unique(self.input_refs, "input_refs")
        _unique(self.created_or_updated_refs, "created_or_updated_refs")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class InvestigationSessionCheckpoint(BaseModel):
    checkpoint_id: str = Field(min_length=3, max_length=500)
    session_ref: str = Field(min_length=3, max_length=500)
    ordinal: int = Field(ge=1)
    binding_refs: list[str] = Field(min_length=1)
    filter_refs: list[str] = Field(default_factory=list)
    hypothesis_refs: list[str] = Field(default_factory=list)
    contribution_refs: list[str] = Field(min_length=1)
    query_refs: list[str] = Field(default_factory=list)
    captured_at: str = Field(min_length=10, max_length=80)
    deterministic_context_fingerprint_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    immutable: Literal[True] = True
    supersedable: Literal[True] = True
    checkpoint_is_not_truth_certification: Literal[True] = True
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_checkpoint(self):
        for label, values in [
            ("binding_refs", self.binding_refs), ("filter_refs", self.filter_refs),
            ("hypothesis_refs", self.hypothesis_refs), ("contribution_refs", self.contribution_refs),
            ("query_refs", self.query_refs),
        ]:
            _unique(values, label)
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class InvestigationSessionRuntimeTrace(BaseModel):
    trace_id: str = Field(min_length=3, max_length=500)
    session_ref: str = Field(min_length=3, max_length=500)
    checkpoint_refs: list[str] = Field(min_length=1)
    query_refs: list[str] = Field(default_factory=list)
    reasoning_trace_refs: list[str] = Field(default_factory=list)
    contradiction_refs: list[str] = Field(default_factory=list)
    timeline_refs: list[str] = Field(default_factory=list)
    started_at: str = Field(min_length=10, max_length=80)
    ended_at: str = Field(min_length=10, max_length=80)
    final_session_status: SessionStatus
    deterministic_trace_fingerprint_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    trace_preserves_epistemic_state: Literal[True] = True
    trace_preserves_provenance: Literal[True] = True
    trace_preserves_contradictions: Literal[True] = True
    trace_is_not_truth_assessment: Literal[True] = True
    graph_mutation_performed: Literal[False] = False
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_trace(self):
        if self.ended_at < self.started_at:
            raise ValueError("ended_at must not precede started_at")
        for label, values in [
            ("checkpoint_refs", self.checkpoint_refs), ("query_refs", self.query_refs),
            ("reasoning_trace_refs", self.reasoning_trace_refs), ("contradiction_refs", self.contradiction_refs),
            ("timeline_refs", self.timeline_refs),
        ]:
            _unique(values, label)
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class ResearchContextSnapshot(BaseModel):
    snapshot_id: str = Field(min_length=3, max_length=500)
    session_ref: str = Field(min_length=3, max_length=500)
    checkpoint_ref: str = Field(min_length=3, max_length=500)
    trace_ref: str = Field(min_length=3, max_length=500)
    as_of: str = Field(min_length=10, max_length=80)
    immutable: Literal[True] = True
    later_context_may_supersede_snapshot: Literal[True] = True
    later_evidence_may_supersede_context: Literal[True] = True
    snapshot_is_not_evidence: Literal[True] = True
    snapshot_is_not_truth_certification: Literal[True] = True
    metadata: dict[str, Any] = Field(default_factory=dict)

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class InvestigationSessionResearchContextBundle(BaseModel):
    release: Literal["3.93.0"] = "3.93.0"
    contract: Literal["sc.core.investigation-session-research-context-runtime.v1"] = CONTRACT_VERSION
    query_contract: Literal["sc.core.unified-entity-evidence-query-api.v1"] = V392_CONTRACT
    policies: list[InvestigationSessionPolicy] = Field(min_length=1)
    sessions: list[InvestigationSession] = Field(min_length=1)
    bindings: list[ResearchContextBinding] = Field(min_length=1)
    filters: list[ResearchContextFilter] = Field(min_length=1)
    hypotheses: list[SessionHypothesis] = Field(min_length=1)
    contributions: list[SessionContribution] = Field(min_length=1)
    checkpoints: list[InvestigationSessionCheckpoint] = Field(min_length=1)
    traces: list[InvestigationSessionRuntimeTrace] = Field(min_length=1)
    snapshots: list[ResearchContextSnapshot] = Field(min_length=1)
    identity_graph_mutation_performed: Literal[False] = False
    relationship_graph_mutation_performed: Literal[False] = False
    evidence_graph_mutation_performed: Literal[False] = False

    @model_validator(mode="after")
    def validate_bundle(self):
        groups = {
            "policy": [x.policy_id for x in self.policies],
            "session": [x.session_id for x in self.sessions],
            "binding": [x.binding_id for x in self.bindings],
            "filter": [x.filter_id for x in self.filters],
            "hypothesis": [x.hypothesis_id for x in self.hypotheses],
            "contribution": [x.contribution_id for x in self.contributions],
            "checkpoint": [x.checkpoint_id for x in self.checkpoints],
            "trace": [x.trace_id for x in self.traces],
            "snapshot": [x.snapshot_id for x in self.snapshots],
        }
        for label, vals in groups.items():
            _unique(vals, f"{label} ids")
        ids={k:set(v) for k,v in groups.items()}
        sessions={x.session_id:x for x in self.sessions}
        bindings={x.binding_id:x for x in self.bindings}
        filters={x.filter_id:x for x in self.filters}
        hyps={x.hypothesis_id:x for x in self.hypotheses}
        contribs={x.contribution_id:x for x in self.contributions}
        checkpoints={x.checkpoint_id:x for x in self.checkpoints}
        traces={x.trace_id:x for x in self.traces}
        upstream=reference_unified_entity_evidence_query_bundle()
        upstream_query_ids={x.query_id for x in upstream.queries}
        upstream_results={x.result_id:x for x in upstream.results}
        upstream_prov={x.provenance_ref_id for x in upstream.provenance_refs}
        for s in self.sessions:
            if s.policy_ref not in ids["policy"]:
                raise ValueError("session policy unresolved")
            if s.parent_session_ref and s.parent_session_ref not in ids["session"]:
                raise ValueError("parent session unresolved")
        for c in self.contributions:
            if c.session_ref not in ids["session"]:
                raise ValueError("contribution session unresolved")
        for b in self.bindings:
            if b.session_ref not in ids["session"] or b.selected_by_contribution_ref not in ids["contribution"]:
                raise ValueError("binding reference unresolved")
            if contribs[b.selected_by_contribution_ref].session_ref != b.session_ref:
                raise ValueError("binding contribution belongs to another session")
            if not set(b.provenance_refs) <= upstream_prov:
                raise ValueError("binding provenance reference unresolved")
            if b.binding_kind == ContextBindingKind.query_result:
                if b.source_object_ref not in upstream_results:
                    raise ValueError("query-result binding source object unresolved")
                r=upstream_results[b.source_object_ref]
                if b.source_contract != r.source_contract or b.epistemic_state != r.epistemic_state or b.validation_state != r.validation_state:
                    raise ValueError("query-result binding must preserve upstream contract/state")
        for f in self.filters:
            if f.session_ref not in ids["session"]:
                raise ValueError("filter session unresolved")
        for h in self.hypotheses:
            if h.session_ref not in ids["session"]:
                raise ValueError("hypothesis session unresolved")
            if not set(h.supporting_binding_refs+h.contradicting_binding_refs) <= ids["binding"]:
                raise ValueError("hypothesis binding unresolved")
            if h.created_by_contribution_ref not in ids["contribution"] or h.last_updated_by_contribution_ref not in ids["contribution"]:
                raise ValueError("hypothesis contribution unresolved")
            if any(bindings[x].session_ref != h.session_ref for x in h.supporting_binding_refs+h.contradicting_binding_refs):
                raise ValueError("hypothesis mixes session bindings")
        seen_ordinals: dict[str,set[int]]={}
        for cp in self.checkpoints:
            if cp.session_ref not in ids["session"]:
                raise ValueError("checkpoint session unresolved")
            if not set(cp.binding_refs) <= ids["binding"] or not set(cp.filter_refs) <= ids["filter"] or not set(cp.hypothesis_refs) <= ids["hypothesis"] or not set(cp.contribution_refs) <= ids["contribution"]:
                raise ValueError("checkpoint context reference unresolved")
            if not set(cp.query_refs) <= upstream_query_ids:
                raise ValueError("checkpoint query unresolved")
            if any(bindings[x].session_ref != cp.session_ref for x in cp.binding_refs):
                raise ValueError("checkpoint mixes session bindings")
            if any(filters[x].session_ref != cp.session_ref for x in cp.filter_refs):
                raise ValueError("checkpoint mixes session filters")
            if any(hyps[x].session_ref != cp.session_ref for x in cp.hypothesis_refs):
                raise ValueError("checkpoint mixes session hypotheses")
            if any(contribs[x].session_ref != cp.session_ref for x in cp.contribution_refs):
                raise ValueError("checkpoint mixes session contributions")
            ords=seen_ordinals.setdefault(cp.session_ref,set())
            if cp.ordinal in ords:
                raise ValueError("checkpoint ordinal must be unique per session")
            ords.add(cp.ordinal)
        for tr in self.traces:
            if tr.session_ref not in ids["session"] or not set(tr.checkpoint_refs) <= ids["checkpoint"] or not set(tr.query_refs) <= upstream_query_ids:
                raise ValueError("session trace reference unresolved")
            if any(checkpoints[x].session_ref != tr.session_ref for x in tr.checkpoint_refs):
                raise ValueError("trace mixes session checkpoints")
        for sn in self.snapshots:
            if sn.session_ref not in ids["session"] or sn.checkpoint_ref not in ids["checkpoint"] or sn.trace_ref not in ids["trace"]:
                raise ValueError("snapshot reference unresolved")
            if checkpoints[sn.checkpoint_ref].session_ref != sn.session_ref or traces[sn.trace_ref].session_ref != sn.session_ref:
                raise ValueError("snapshot mixes session identities")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


@lru_cache(maxsize=1)
def reference_investigation_session_research_context_bundle() -> InvestigationSessionResearchContextBundle:
    upstream=reference_unified_entity_evidence_query_bundle()
    policy=InvestigationSessionPolicy(policy_id="session-policy:default:v1")
    session=InvestigationSession(
        session_id="investigation-session:synthetic:v1", policy_ref=policy.policy_id,
        consumer_ref="consumer:workspace", title="Synthetic entity/evidence investigation session",
        research_question="What governed entity, documentary, relationship, contradiction, timeline, and federated context is relevant to the synthetic investigation question?",
        status=SessionStatus.active, opened_at="2026-10-01T01:00:00Z", updated_at="2026-10-01T01:08:00Z",
    )
    c1=SessionContribution(contribution_id="session-contribution:01",session_ref=session.session_id,actor_kind=ContributionActorKind.human,actor_ref="researcher:synthetic",action="opened investigation session and defined research question",contributed_at="2026-10-01T01:00:00Z")
    c2=SessionContribution(contribution_id="session-contribution:02",session_ref=session.session_id,actor_kind=ContributionActorKind.runtime,actor_ref="sc-core:v3.93.0",action="bound governed query results into research context",input_refs=[upstream.queries[0].query_id],contributed_at="2026-10-01T01:03:00Z")
    bindings=[]
    for i,r in enumerate(upstream.results,1):
        kind = ContextBindingKind.federation_reference if r.epistemic_state==EpistemicState.remote_reference else ContextBindingKind.query_result
        bindings.append(ResearchContextBinding(
            binding_id=f"session-binding:{i:02d}", session_ref=session.session_id, binding_kind=kind,
            source_contract=r.source_contract, source_object_ref=r.result_id, epistemic_state=r.epistemic_state,
            validation_state=r.validation_state, provenance_refs=list(r.provenance_refs), binding_role="selected-query-context",
            selected_at="2026-10-01T01:03:00Z", selected_by_contribution_ref=c2.contribution_id,
        ))
    filt=ResearchContextFilter(
        filter_id="session-filter:01",session_ref=session.session_id,
        target_domains=[r.target_kind.value for r in upstream.results],
        allowed_epistemic_states=sorted({r.epistemic_state for r in upstream.results}, key=lambda x:x.value),
        include_remote_references=True,include_contradictions=True,
    )
    c3=SessionContribution(contribution_id="session-contribution:03",session_ref=session.session_id,actor_kind=ContributionActorKind.human,actor_ref="researcher:synthetic",action="recorded working hypothesis with supporting and contradicting context",input_refs=[bindings[4].binding_id,bindings[5].binding_id,bindings[9].binding_id],created_or_updated_refs=["session-hypothesis:01"],contributed_at="2026-10-01T01:05:00Z")
    hyp=SessionHypothesis(
        hypothesis_id="session-hypothesis:01",session_ref=session.session_id,
        statement="The selected source-observed and documentary context may support a bounded relationship hypothesis, subject to contradiction and validation boundaries.",
        state=HypothesisState.qualified,supporting_binding_refs=[bindings[4].binding_id,bindings[5].binding_id],contradicting_binding_refs=[bindings[9].binding_id],
        created_by_contribution_ref=c3.contribution_id,last_updated_by_contribution_ref=c3.contribution_id,
    )
    c4=SessionContribution(contribution_id="session-contribution:04",session_ref=session.session_id,actor_kind=ContributionActorKind.system,actor_ref="sc-core:checkpoint-runtime",action="captured immutable research-context checkpoint",input_refs=[x.binding_id for x in bindings],created_or_updated_refs=["session-checkpoint:01"],contributed_at="2026-10-01T01:08:00Z")
    contributions=[c1,c2,c3,c4]
    seed={"session":session.session_id,"bindings":[x.fingerprint() for x in bindings],"filter":filt.fingerprint(),"hypothesis":hyp.fingerprint(),"query":upstream.queries[0].fingerprint()}
    cp=InvestigationSessionCheckpoint(
        checkpoint_id="session-checkpoint:01",session_ref=session.session_id,ordinal=1,binding_refs=[x.binding_id for x in bindings],
        filter_refs=[filt.filter_id],hypothesis_refs=[hyp.hypothesis_id],contribution_refs=[x.contribution_id for x in contributions],
        query_refs=[upstream.queries[0].query_id],captured_at="2026-10-01T01:08:00Z",deterministic_context_fingerprint_sha256=canonical_sha256(seed),
    )
    trace_seed={"session":session.session_id,"checkpoints":[cp.checkpoint_id],"query_refs":cp.query_refs,"started":"2026-10-01T01:00:00Z","ended":"2026-10-01T01:08:01Z"}
    trace=InvestigationSessionRuntimeTrace(
        trace_id="session-trace:synthetic:v1",session_ref=session.session_id,checkpoint_refs=[cp.checkpoint_id],query_refs=cp.query_refs,
        reasoning_trace_refs=["multi-hop-reasoning-trace:synthetic:v1"],contradiction_refs=["contradiction-set:identity:synthetic:v1"],timeline_refs=["entity-timeline:synthetic:v1"],
        started_at="2026-10-01T01:00:00Z",ended_at="2026-10-01T01:08:01Z",final_session_status=SessionStatus.active,
        deterministic_trace_fingerprint_sha256=canonical_sha256(trace_seed),
    )
    snap=ResearchContextSnapshot(snapshot_id="session-snapshot:synthetic:v1",session_ref=session.session_id,checkpoint_ref=cp.checkpoint_id,trace_ref=trace.trace_id,as_of="2026-10-01T01:08:01Z")
    return InvestigationSessionResearchContextBundle(
        policies=[policy],sessions=[session],bindings=bindings,filters=[filt],hypotheses=[hyp],contributions=contributions,checkpoints=[cp],traces=[trace],snapshots=[snap]
    )


def contract_document() -> dict[str, Any]:
    b=reference_investigation_session_research_context_bundle()
    remote=sum(1 for x in b.bindings if x.epistemic_state==EpistemicState.remote_reference)
    return {
        "ok":True,"release":CORE_RELEASE,"contract":CONTRACT_VERSION,"query_contract":V392_CONTRACT,
        "principles":{
            "persistent_governed_research_context":True,
            "source_contract_identity_preserved":True,
            "epistemic_state_preserved":True,
            "validation_state_preserved":True,
            "provenance_preserved":True,
            "contradictions_preserved":True,
            "remote_reference_state_preserved":True,
            "context_changes_are_attributed":True,
            "checkpoints_are_immutable":True,
            "checkpoints_are_supersedable":True,
            "query_context_is_reproducible":True,
            "session_state_is_working_context":True,
        },
        "boundaries":{
            "session_context_is_evidence":False,
            "persisted_hypothesis_is_graph_fact":False,
            "persisted_conclusion_is_truth_verdict":False,
            "context_selection_promotes_epistemic_state":False,
            "session_can_bypass_validation":False,
            "remote_reference_becomes_local_evidence_by_persistence":False,
            "saved_context_proves_completeness":False,
            "checkpoint_is_truth_certification":False,
            "identity_graph_mutation_performed":False,
            "relationship_graph_mutation_performed":False,
            "evidence_graph_mutation_performed":False,
        },
        "reference":{
            "policies":len(b.policies),"sessions":len(b.sessions),"bindings":len(b.bindings),"filters":len(b.filters),
            "hypotheses":len(b.hypotheses),"contributions":len(b.contributions),"checkpoints":len(b.checkpoints),
            "traces":len(b.traces),"snapshots":len(b.snapshots),"remote_references":remote,
            "session_status":b.sessions[0].status.value,"hypothesis_state":b.hypotheses[0].state.value,
            "bundle_fingerprint_sha256":b.fingerprint(),
        },
        "database_migration":"none",
    }
