from __future__ import annotations

from enum import Enum
from functools import lru_cache
from typing import Literal

from pydantic import BaseModel, Field, model_validator

from .computational_runtime_objects import canonical_sha256
from .semantic_synthesis_research_answer import (
    SemanticSynthesisResearchAnswerBundle,
    reference_semantic_synthesis_research_answer_bundle,
)

CORE_RELEASE = "4.20.0"
CONTRACT_VERSION = "sc.core.unified-contextual-reasoning-runtime.v1"
PREDECESSOR_CONTRACT = "sc.core.semantic-synthesis-research-answer-object.v1"


class ReasoningStageKind(str, Enum):
    contextual_memory = "contextual-memory"
    retrieval_relevance = "retrieval-relevance"
    claim_comparison = "claim-comparison"
    evidence_context = "evidence-context"
    causal_context = "causal-context"
    narrative_framing = "narrative-framing"
    source_reconciliation = "source-reconciliation"
    competing_explanations = "competing-explanations"
    semantic_synthesis = "semantic-synthesis"


class ReasoningStageState(str, Enum):
    completed = "completed"
    completed_with_qualifications = "completed-with-qualifications"
    unresolved = "unresolved"


class UnifiedReasoningPolicy(BaseModel):
    policy_id: str = Field(min_length=3)
    stage_order_is_governed: Literal[True] = True
    predecessor_objects_remain_immutable: Literal[True] = True
    qualifications_must_propagate_forward: Literal[True] = True
    unresolved_state_must_propagate_forward: Literal[True] = True
    original_language_remains_authoritative: Literal[True] = True
    translation_remains_derived: Literal[True] = True
    source_independence_must_be_preserved: Literal[True] = True
    runtime_trace_must_be_reproducible: Literal[True] = True
    stage_completion_establishes_truth: Literal[False] = False
    runtime_completion_establishes_truth: Literal[False] = False
    runtime_confidence_is_probability: Literal[False] = False
    synthesis_answer_is_evidence_record: Literal[False] = False
    automatic_evidence_promotion_authorized: Literal[False] = False
    automatic_hypothesis_selection_authorized: Literal[False] = False
    automatic_canonical_identity_merge_authorized: Literal[False] = False
    automatic_context_graph_mutation_authorized: Literal[False] = False
    automatic_evidence_graph_mutation_authorized: Literal[False] = False
    automatic_knowledge_graph_mutation_authorized: Literal[False] = False
    automatic_identity_graph_mutation_authorized: Literal[False] = False


class ReasoningStageRecord(BaseModel):
    stage_id: str = Field(min_length=3)
    ordinal: int = Field(ge=1, le=9)
    kind: ReasoningStageKind
    release: str = Field(pattern=r"^4\.(1[1-9])\.0$")
    contract: str = Field(min_length=3)
    state: ReasoningStageState
    input_artifact_kind: str = Field(min_length=3)
    output_artifact_kind: str = Field(min_length=3)
    predecessor_stage_ref: str | None = None
    qualification_refs: list[str] = Field(default_factory=list)
    unresolved_refs: list[str] = Field(default_factory=list)
    stage_output_is_advisory: Literal[True] = True
    stage_output_is_not_truth_promotion: Literal[True] = True

    @model_validator(mode="after")
    def validate_unique_refs(self):
        for values, label in ((self.qualification_refs, "qualification_refs"), (self.unresolved_refs, "unresolved_refs")):
            if len(values) != len(set(values)):
                raise ValueError(f"{label} must be unique")
        if self.state == ReasoningStageState.unresolved and not self.unresolved_refs:
            raise ValueError("unresolved stage requires unresolved_refs")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class UnifiedReasoningTrace(BaseModel):
    trace_id: str = Field(min_length=3)
    question: str = Field(min_length=3, max_length=5000)
    stage_refs: list[str] = Field(min_length=9, max_length=9)
    final_answer_ref: str = Field(min_length=3)
    final_disposition: str = Field(min_length=3)
    carried_qualification_refs: list[str] = Field(default_factory=list)
    unresolved_questions: list[str] = Field(default_factory=list)
    trace_is_audit_record_not_truth_verdict: Literal[True] = True
    final_answer_remains_governed_synthesis: Literal[True] = True

    @model_validator(mode="after")
    def validate_trace(self):
        if len(self.stage_refs) != len(set(self.stage_refs)):
            raise ValueError("stage_refs must be unique")
        if len(self.carried_qualification_refs) != len(set(self.carried_qualification_refs)):
            raise ValueError("carried_qualification_refs must be unique")
        if len(self.unresolved_questions) != len(set(self.unresolved_questions)):
            raise ValueError("unresolved_questions must be unique")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class UnifiedReasoningRuntimeProvenance(BaseModel):
    provenance_id: str = Field(min_length=3)
    predecessor_synthesis_fingerprint_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    stage_refs: list[str] = Field(min_length=9, max_length=9)
    trace_refs: list[str] = Field(min_length=1)
    method: str = Field(min_length=3, max_length=5000)
    runtime_provenance_is_not_truth_certification: Literal[True] = True

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class UnifiedReasoningRuntimeSnapshot(BaseModel):
    snapshot_id: str = Field(min_length=3)
    predecessor_synthesis_fingerprint_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    stage_fingerprints: dict[str, str]
    trace_fingerprints: dict[str, str]
    deterministic_runtime_fingerprint_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    supersedable: Literal[True] = True
    snapshot_is_not_truth_or_probability_certification: Literal[True] = True

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class UnifiedContextualReasoningRuntimeBundle(BaseModel):
    release: Literal["4.20.0"] = "4.20.0"
    contract: Literal[CONTRACT_VERSION] = CONTRACT_VERSION
    predecessor_contract: Literal[PREDECESSOR_CONTRACT] = PREDECESSOR_CONTRACT
    policy: UnifiedReasoningPolicy
    predecessor_synthesis: SemanticSynthesisResearchAnswerBundle
    stages: list[ReasoningStageRecord] = Field(min_length=9, max_length=9)
    traces: list[UnifiedReasoningTrace] = Field(min_length=1)
    provenance_records: list[UnifiedReasoningRuntimeProvenance] = Field(min_length=1)
    snapshots: list[UnifiedReasoningRuntimeSnapshot] = Field(min_length=1)
    database_migration: Literal["none"] = "none"

    @model_validator(mode="after")
    def validate_bundle(self):
        if self.predecessor_synthesis.release != "4.19.0" or self.predecessor_synthesis.contract != PREDECESSOR_CONTRACT:
            raise ValueError("v4.20 must preserve governed v4.19 synthesis predecessor")
        expected = [
            (1, ReasoningStageKind.contextual_memory, "4.11.0", "sc.core.contextual-memory-semantic-state-foundation.v1"),
            (2, ReasoningStageKind.retrieval_relevance, "4.12.0", "sc.core.context-retrieval-relevance-intelligence.v1"),
            (3, ReasoningStageKind.claim_comparison, "4.13.0", "sc.core.claim-alignment-agreement-contradiction-intelligence.v1"),
            (4, ReasoningStageKind.evidence_context, "4.14.0", "sc.core.evidence-context-integration-layer.v1"),
            (5, ReasoningStageKind.causal_context, "4.15.0", "sc.core.contextual-causal-language-mechanism-intelligence.v1"),
            (6, ReasoningStageKind.narrative_framing, "4.16.0", "sc.core.narrative-framing-perspective-intelligence.v1"),
            (7, ReasoningStageKind.source_reconciliation, "4.17.0", "sc.core.cross-source-semantic-reconciliation-engine.v1"),
            (8, ReasoningStageKind.competing_explanations, "4.18.0", "sc.core.contextual-hypothesis-competing-explanation-objects.v1"),
            (9, ReasoningStageKind.semantic_synthesis, "4.19.0", "sc.core.semantic-synthesis-research-answer-object.v1"),
        ]
        actual = [(x.ordinal, x.kind, x.release, x.contract) for x in self.stages]
        if actual != expected:
            raise ValueError("runtime stage inventory/order must remain v4.11 through v4.19")
        stage_ids = [x.stage_id for x in self.stages]
        if len(stage_ids) != len(set(stage_ids)):
            raise ValueError("stage ids must be unique")
        for i, stage in enumerate(self.stages):
            if i == 0:
                if stage.predecessor_stage_ref is not None:
                    raise ValueError("first stage may not reference predecessor stage")
            elif stage.predecessor_stage_ref != self.stages[i-1].stage_id:
                raise ValueError("stage predecessor chain must be contiguous")
        answers = {x.answer_id: x for x in self.predecessor_synthesis.research_answers}
        for trace in self.traces:
            if trace.stage_refs != stage_ids:
                raise ValueError("each trace must preserve the complete governed stage order")
            if trace.final_answer_ref not in answers:
                raise ValueError("trace final answer must resolve to v4.19 synthesis")
            if trace.question != answers[trace.final_answer_ref].question:
                raise ValueError("trace question must preserve predecessor answer question")
            if trace.final_disposition != answers[trace.final_answer_ref].disposition.value:
                raise ValueError("trace disposition must preserve predecessor answer disposition")
            if not set(answers[trace.final_answer_ref].qualification_refs).issubset(trace.carried_qualification_refs):
                raise ValueError("trace may not drop predecessor answer qualifications")
            if not set(answers[trace.final_answer_ref].unresolved_questions).issubset(trace.unresolved_questions):
                raise ValueError("trace may not drop predecessor unresolved questions")
        trace_ids = [x.trace_id for x in self.traces]
        if len(trace_ids) != len(set(trace_ids)):
            raise ValueError("trace ids must be unique")
        sf = {x.stage_id: x.fingerprint() for x in self.stages}
        tf = {x.trace_id: x.fingerprint() for x in self.traces}
        deterministic = canonical_sha256({"predecessor": self.predecessor_synthesis.fingerprint(), "stages": sf, "traces": tf})
        for p in self.provenance_records:
            if p.predecessor_synthesis_fingerprint_sha256 != self.predecessor_synthesis.fingerprint():
                raise ValueError("runtime provenance predecessor fingerprint mismatch")
            if p.stage_refs != stage_ids:
                raise ValueError("runtime provenance must preserve stage order")
            if not set(p.trace_refs).issubset(trace_ids):
                raise ValueError("runtime provenance trace refs must resolve")
        for s in self.snapshots:
            if s.predecessor_synthesis_fingerprint_sha256 != self.predecessor_synthesis.fingerprint():
                raise ValueError("runtime snapshot predecessor fingerprint mismatch")
            if s.stage_fingerprints != sf:
                raise ValueError("runtime snapshot stage fingerprints mismatch")
            if s.trace_fingerprints != tf:
                raise ValueError("runtime snapshot trace fingerprints mismatch")
            if s.deterministic_runtime_fingerprint_sha256 != deterministic:
                raise ValueError("runtime deterministic fingerprint mismatch")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


def _stage_records() -> list[ReasoningStageRecord]:
    specs = [
        (1, ReasoningStageKind.contextual_memory, "4.11.0", "sc.core.contextual-memory-semantic-state-foundation.v1", "source-context", "contextual-memory-state", ReasoningStageState.completed_with_qualifications, ["stored-context-does-not-gain-truth-through-persistence"], []),
        (2, ReasoningStageKind.retrieval_relevance, "4.12.0", "sc.core.context-retrieval-relevance-intelligence.v1", "contextual-memory-state", "ranked-context-set", ReasoningStageState.completed_with_qualifications, ["relevance-rank-is-not-truth-or-authority"], []),
        (3, ReasoningStageKind.claim_comparison, "4.13.0", "sc.core.claim-alignment-agreement-contradiction-intelligence.v1", "ranked-context-set", "claim-comparison-set", ReasoningStageState.unresolved, ["agreement-is-not-truth"], ["strict-claim-conflict-remains-unresolved"]),
        (4, ReasoningStageKind.evidence_context, "4.14.0", "sc.core.evidence-context-integration-layer.v1", "claim-comparison-set", "evidence-context-assessment-set", ReasoningStageState.unresolved, ["evidence-link-is-not-evidence-verification", "derived-translation-is-not-independent-corroboration"], ["strict-evidence-conflict-remains-unresolved"]),
        (5, ReasoningStageKind.causal_context, "4.15.0", "sc.core.contextual-causal-language-mechanism-intelligence.v1", "evidence-context-assessment-set", "causal-context-assessment-set", ReasoningStageState.unresolved, ["causal-wording-is-not-causal-identification"], ["causal-identification-not-established"]),
        (6, ReasoningStageKind.narrative_framing, "4.16.0", "sc.core.narrative-framing-perspective-intelligence.v1", "causal-context-assessment-set", "perspective-comparison-set", ReasoningStageState.completed_with_qualifications, ["framing-is-not-truth-bias-or-motive"], []),
        (7, ReasoningStageKind.source_reconciliation, "4.17.0", "sc.core.cross-source-semantic-reconciliation-engine.v1", "perspective-comparison-set", "semantic-reconciliation-set", ReasoningStageState.unresolved, ["reconciliation-is-not-canonicalization"], ["identity-and-period-alignment-remain-partly-unresolved"]),
        (8, ReasoningStageKind.competing_explanations, "4.18.0", "sc.core.contextual-hypothesis-competing-explanation-objects.v1", "semantic-reconciliation-set", "competing-explanation-set", ReasoningStageState.unresolved, ["explanatory-fit-is-not-probability-or-truth"], ["multiple-live-explanations-remain"]),
        (9, ReasoningStageKind.semantic_synthesis, "4.19.0", "sc.core.semantic-synthesis-research-answer-object.v1", "competing-explanation-set", "research-answer-set", ReasoningStageState.completed_with_qualifications, ["research-answer-is-not-truth-verdict"], []),
    ]
    out=[]
    for ordinal, kind, release, contract, input_kind, output_kind, state, quals, unresolved in specs:
        out.append(ReasoningStageRecord(
            stage_id=f"reasoning-stage:{ordinal:02d}:{kind.value}", ordinal=ordinal, kind=kind,
            release=release, contract=contract, state=state, input_artifact_kind=input_kind,
            output_artifact_kind=output_kind,
            predecessor_stage_ref=None if ordinal == 1 else f"reasoning-stage:{ordinal-1:02d}:{specs[ordinal-2][1].value}",
            qualification_refs=quals, unresolved_refs=unresolved,
        ))
    return out


@lru_cache(maxsize=1)
def reference_unified_contextual_reasoning_runtime_bundle() -> UnifiedContextualReasoningRuntimeBundle:
    pred = reference_semantic_synthesis_research_answer_bundle()
    policy = UnifiedReasoningPolicy(policy_id="unified-contextual-reasoning-runtime-policy:v1")
    stages = _stage_records()
    stage_refs = [x.stage_id for x in stages]
    traces=[]
    for answer in pred.research_answers:
        carried = list(dict.fromkeys(answer.qualification_refs + [q for s in stages for q in s.qualification_refs]))
        unresolved = list(dict.fromkeys(answer.unresolved_questions + [u for s in stages for u in s.unresolved_refs]))
        traces.append(UnifiedReasoningTrace(
            trace_id=f"reasoning-trace:{answer.answer_id.split(':',1)[1]}",
            question=answer.question,
            stage_refs=stage_refs,
            final_answer_ref=answer.answer_id,
            final_disposition=answer.disposition.value,
            carried_qualification_refs=carried,
            unresolved_questions=unresolved,
        ))
    prov = UnifiedReasoningRuntimeProvenance(
        provenance_id="unified-reasoning-provenance:reference",
        predecessor_synthesis_fingerprint_sha256=pred.fingerprint(),
        stage_refs=stage_refs,
        trace_refs=[x.trace_id for x in traces],
        method="Execute the governed v4.11-v4.19 contextual reasoning sequence as an auditable contract pipeline. Preserve predecessor object identity, original-language authority, translation lineage, source independence, counterevidence, qualifications, unresolved state, competing explanations, and final v4.19 research-answer disposition. Runtime orchestration does not authorize truth promotion, evidence promotion, hypothesis selection, canonical identity merge, or graph mutation.",
    )
    sf={x.stage_id:x.fingerprint() for x in stages}
    tf={x.trace_id:x.fingerprint() for x in traces}
    det=canonical_sha256({"predecessor":pred.fingerprint(),"stages":sf,"traces":tf})
    snap=UnifiedReasoningRuntimeSnapshot(
        snapshot_id="unified-reasoning-snapshot:reference",
        predecessor_synthesis_fingerprint_sha256=pred.fingerprint(),
        stage_fingerprints=sf,
        trace_fingerprints=tf,
        deterministic_runtime_fingerprint_sha256=det,
    )
    return UnifiedContextualReasoningRuntimeBundle(policy=policy, predecessor_synthesis=pred, stages=stages, traces=traces, provenance_records=[prov], snapshots=[snap])


def contract_document() -> dict:
    b=reference_unified_contextual_reasoning_runtime_bundle()
    return {
        "ok": True,
        "release": CORE_RELEASE,
        "contract": CONTRACT_VERSION,
        "predecessor_contract": PREDECESSOR_CONTRACT,
        "identity": {"product":"Sustainable Catalyst Platform Core","build":"Unified Contextual Reasoning Runtime","major_api":"v4"},
        "principles": {
            "v411_v419_stage_order_is_governed": True,
            "qualifications_propagate_forward": True,
            "unresolved_state_propagates_forward": True,
            "original_language_remains_authoritative": True,
            "translation_remains_derived": True,
            "source_independence_is_preserved": True,
            "runtime_trace_is_reproducible": True,
        },
        "boundaries": {
            "stage_completion_establishes_truth": False,
            "runtime_completion_establishes_truth": False,
            "runtime_confidence_is_probability": False,
            "synthesis_answer_is_evidence_record": False,
            "automatic_evidence_promotion_performed": False,
            "automatic_hypothesis_selection_performed": False,
            "automatic_canonical_identity_merge_performed": False,
            "automatic_context_graph_mutation_performed": False,
            "automatic_evidence_graph_mutation_performed": False,
            "automatic_knowledge_graph_mutation_performed": False,
            "automatic_identity_graph_mutation_performed": False,
        },
        "milestone": {
            "contextual_reasoning_arc_complete": True,
            "reasoning_arc_from_release": "4.11.0",
            "reasoning_arc_through_release": "4.20.0",
            "recommended_core_feature_expansion_pause": True,
        },
        "reference": {
            "predecessor_release": "4.19.0",
            "predecessor_fingerprint_sha256": b.predecessor_synthesis.fingerprint(),
            "reasoning_stages": len(b.stages),
            "reasoning_traces": len(b.traces),
            "final_research_answers": len(b.predecessor_synthesis.research_answers),
            "unresolved_stage_records": sum(x.state == ReasoningStageState.unresolved for x in b.stages),
            "traces_with_unresolved_questions": sum(bool(x.unresolved_questions) for x in b.traces),
            "snapshots": len(b.snapshots),
            "bundle_fingerprint_sha256": b.fingerprint(),
        },
        "database_migration": "none",
    }
