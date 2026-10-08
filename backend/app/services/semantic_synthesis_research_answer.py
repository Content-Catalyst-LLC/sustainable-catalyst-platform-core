from __future__ import annotations

from enum import Enum
from functools import lru_cache
from typing import Literal

from pydantic import BaseModel, Field, model_validator

from .computational_runtime_objects import canonical_sha256
from .contextual_hypothesis_competing_explanations import (
    ContextualHypothesisCompetingExplanationBundle,
    HypothesisReviewState,
    reference_contextual_hypothesis_competing_explanation_bundle,
)

CORE_RELEASE = "4.19.0"
CONTRACT_VERSION = "sc.core.semantic-synthesis-research-answer-object.v1"
PREDECESSOR_CONTRACT = "sc.core.contextual-hypothesis-competing-explanation-objects.v1"


class AnswerDisposition(str, Enum):
    supported_with_qualifications = "supported-with-qualifications"
    unresolved = "unresolved"
    mixed = "mixed"
    provenance_resolved_claim_unresolved = "provenance-resolved-claim-unresolved"


class SynthesisClaimRole(str, Enum):
    answer = "answer"
    support = "support"
    counterevidence = "counterevidence"
    qualification = "qualification"
    unresolved = "unresolved"


class ResearchAnswerPolicy(BaseModel):
    policy_id: str = Field(min_length=3)
    predecessor_hypothesis_context_remains_immutable: Literal[True] = True
    synthesis_must_preserve_counterevidence: Literal[True] = True
    synthesis_must_preserve_live_competing_explanations: Literal[True] = True
    synthesis_must_preserve_source_independence_and_translation_lineage: Literal[True] = True
    synthesis_must_preserve_original_language_authority: Literal[True] = True
    answer_confidence_is_qualification_not_probability: Literal[True] = True
    concise_answer_may_not_drop_material_uncertainty: Literal[True] = True
    answer_disposition_establishes_truth: Literal[False] = False
    answer_confidence_establishes_probability: Literal[False] = False
    majority_source_count_establishes_truth: Literal[False] = False
    rejected_explanation_establishes_opposite_truth: Literal[False] = False
    automatic_evidence_promotion_authorized: Literal[False] = False
    automatic_hypothesis_selection_authorized: Literal[False] = False
    automatic_context_graph_mutation_authorized: Literal[False] = False
    automatic_evidence_graph_mutation_authorized: Literal[False] = False
    automatic_knowledge_graph_mutation_authorized: Literal[False] = False
    automatic_identity_graph_mutation_authorized: Literal[False] = False


class SynthesisClaim(BaseModel):
    synthesis_claim_id: str = Field(min_length=3)
    answer_ref: str = Field(min_length=3)
    role: SynthesisClaimRole
    statement: str = Field(min_length=3, max_length=5000)
    hypothesis_refs: list[str] = Field(default_factory=list)
    evidence_position_refs: list[str] = Field(default_factory=list)
    explanation_set_refs: list[str] = Field(default_factory=list)
    qualification_refs: list[str] = Field(default_factory=list)
    original_language_refs: list[str] = Field(default_factory=list)
    statement_is_synthesis_not_source_quote: Literal[True] = True
    claim_is_not_truth_promotion: Literal[True] = True

    @model_validator(mode="after")
    def unique_refs(self):
        for vals, name in [(self.hypothesis_refs,'hypothesis_refs'),(self.evidence_position_refs,'evidence_position_refs'),(self.explanation_set_refs,'explanation_set_refs'),(self.qualification_refs,'qualification_refs'),(self.original_language_refs,'original_language_refs')]:
            if len(vals) != len(set(vals)):
                raise ValueError(f"{name} must be unique")
        return self

    def fingerprint(self) -> str: return canonical_sha256(self)


class ResearchAnswerObject(BaseModel):
    answer_id: str = Field(min_length=3)
    question: str = Field(min_length=3, max_length=5000)
    concise_answer: str = Field(min_length=3, max_length=5000)
    disposition: AnswerDisposition
    synthesis_claim_refs: list[str] = Field(min_length=1)
    explanation_set_refs: list[str] = Field(min_length=1)
    retained_hypothesis_refs: list[str] = Field(default_factory=list)
    rejected_hypothesis_refs: list[str] = Field(default_factory=list)
    counterevidence_position_refs: list[str] = Field(default_factory=list)
    qualification_refs: list[str] = Field(default_factory=list)
    unresolved_questions: list[str] = Field(default_factory=list)
    confidence_label: Literal["qualified","limited","unresolved"]
    confidence_is_not_probability: Literal[True] = True
    answer_is_not_truth_verdict: Literal[True] = True
    answer_is_not_evidence_record: Literal[True] = True

    @model_validator(mode="after")
    def validate_answer(self):
        for vals, name in [(self.synthesis_claim_refs,'synthesis_claim_refs'),(self.explanation_set_refs,'explanation_set_refs'),(self.retained_hypothesis_refs,'retained_hypothesis_refs'),(self.rejected_hypothesis_refs,'rejected_hypothesis_refs'),(self.counterevidence_position_refs,'counterevidence_position_refs'),(self.qualification_refs,'qualification_refs'),(self.unresolved_questions,'unresolved_questions')]:
            if len(vals) != len(set(vals)):
                raise ValueError(f"{name} must be unique")
        if set(self.retained_hypothesis_refs) & set(self.rejected_hypothesis_refs):
            raise ValueError("hypothesis cannot be both retained and rejected")
        if self.disposition == AnswerDisposition.unresolved and not self.unresolved_questions:
            raise ValueError("unresolved answer requires unresolved_questions")
        return self

    def fingerprint(self) -> str: return canonical_sha256(self)


class ResearchAnswerProvenanceRecord(BaseModel):
    provenance_id: str = Field(min_length=3)
    predecessor_hypothesis_fingerprint_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    answer_refs: list[str] = Field(min_length=1)
    synthesis_claim_refs: list[str] = Field(min_length=1)
    method: str = Field(min_length=3, max_length=5000)
    provenance_is_not_truth_certification: Literal[True] = True
    def fingerprint(self) -> str: return canonical_sha256(self)


class ResearchAnswerSnapshot(BaseModel):
    snapshot_id: str = Field(min_length=3)
    predecessor_hypothesis_fingerprint_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    answer_fingerprints: dict[str,str]
    synthesis_claim_fingerprints: dict[str,str]
    deterministic_synthesis_fingerprint_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    supersedable: Literal[True] = True
    snapshot_is_not_truth_or_probability_certification: Literal[True] = True
    def fingerprint(self) -> str: return canonical_sha256(self)


class SemanticSynthesisResearchAnswerBundle(BaseModel):
    release: Literal["4.19.0"] = "4.19.0"
    contract: Literal[CONTRACT_VERSION] = CONTRACT_VERSION
    predecessor_contract: Literal[PREDECESSOR_CONTRACT] = PREDECESSOR_CONTRACT
    policy: ResearchAnswerPolicy
    predecessor_hypothesis_context: ContextualHypothesisCompetingExplanationBundle
    synthesis_claims: list[SynthesisClaim] = Field(min_length=1)
    research_answers: list[ResearchAnswerObject] = Field(min_length=1)
    provenance_records: list[ResearchAnswerProvenanceRecord] = Field(min_length=1)
    snapshots: list[ResearchAnswerSnapshot] = Field(min_length=1)
    database_migration: Literal["none"] = "none"

    @model_validator(mode="after")
    def validate_bundle(self):
        pred=self.predecessor_hypothesis_context
        if pred.release != "4.18.0" or pred.contract != PREDECESSOR_CONTRACT:
            raise ValueError("v4.19 must preserve governed v4.18 hypothesis predecessor")
        def uniq(vals,label):
            if len(vals)!=len(set(vals)): raise ValueError(f"{label} must be unique")
        uniq([x.synthesis_claim_id for x in self.synthesis_claims],"synthesis claim ids")
        uniq([x.answer_id for x in self.research_answers],"answer ids")
        claims={x.synthesis_claim_id:x for x in self.synthesis_claims}
        answers={x.answer_id:x for x in self.research_answers}
        hypotheses={x.hypothesis_id:x for x in pred.hypotheses}
        positions={x.position_id:x for x in pred.evidence_positions}
        sets={x.explanation_set_id:x for x in pred.explanation_sets}
        for c in self.synthesis_claims:
            if c.answer_ref not in answers: raise ValueError("synthesis claim answer must resolve")
            if not set(c.hypothesis_refs).issubset(hypotheses): raise ValueError("synthesis hypothesis refs must resolve")
            if not set(c.evidence_position_refs).issubset(positions): raise ValueError("synthesis evidence position refs must resolve")
            if not set(c.explanation_set_refs).issubset(sets): raise ValueError("synthesis explanation set refs must resolve")
        for a in self.research_answers:
            if not set(a.synthesis_claim_refs).issubset(claims): raise ValueError("answer synthesis claims must resolve")
            if any(claims[c].answer_ref != a.answer_id for c in a.synthesis_claim_refs): raise ValueError("answer may only include its own synthesis claims")
            if not set(a.explanation_set_refs).issubset(sets): raise ValueError("answer explanation sets must resolve")
            if not set(a.retained_hypothesis_refs).issubset(hypotheses): raise ValueError("retained hypotheses must resolve")
            if not set(a.rejected_hypothesis_refs).issubset(hypotheses): raise ValueError("rejected hypotheses must resolve")
            if not set(a.counterevidence_position_refs).issubset(positions): raise ValueError("counterevidence positions must resolve")
            if any(hypotheses[h].state == HypothesisReviewState.rejected for h in a.retained_hypothesis_refs): raise ValueError("rejected hypothesis cannot be retained in answer")
            if any(hypotheses[h].state != HypothesisReviewState.rejected for h in a.rejected_hypothesis_refs): raise ValueError("answer rejected refs must refer to rejected hypotheses")
        subjects=set(answers)|set(claims)
        for p in self.provenance_records:
            if p.predecessor_hypothesis_fingerprint_sha256 != pred.fingerprint(): raise ValueError("provenance predecessor fingerprint mismatch")
            if not set(p.answer_refs).issubset(answers): raise ValueError("provenance answer refs must resolve")
            if not set(p.synthesis_claim_refs).issubset(claims): raise ValueError("provenance synthesis refs must resolve")
        exp_a={x.answer_id:x.fingerprint() for x in self.research_answers}
        exp_c={x.synthesis_claim_id:x.fingerprint() for x in self.synthesis_claims}
        expected=canonical_sha256({"predecessor":pred.fingerprint(),"answers":exp_a,"claims":exp_c})
        for s in self.snapshots:
            if s.predecessor_hypothesis_fingerprint_sha256 != pred.fingerprint(): raise ValueError("snapshot predecessor fingerprint mismatch")
            if s.answer_fingerprints != exp_a: raise ValueError("snapshot answer fingerprints mismatch")
            if s.synthesis_claim_fingerprints != exp_c: raise ValueError("snapshot synthesis fingerprints mismatch")
            if s.deterministic_synthesis_fingerprint_sha256 != expected: raise ValueError("deterministic synthesis fingerprint mismatch")
        return self

    def fingerprint(self) -> str: return canonical_sha256(self)


@lru_cache(maxsize=1)
def reference_semantic_synthesis_research_answer_bundle() -> SemanticSynthesisResearchAnswerBundle:
    pred=reference_contextual_hypothesis_competing_explanation_bundle()
    policy=ResearchAnswerPolicy(policy_id="semantic-synthesis-research-answer-policy:v1")
    answers=[
        ResearchAnswerObject(
            answer_id="answer:emissions-effect",
            question="Did the policy measure reduce emissions?",
            concise_answer="The current source set does not support a single unqualified answer. Sources conflict, and scope, timing, measurement process, and causal identification remain live explanations for the discrepancy.",
            disposition=AnswerDisposition.unresolved,
            synthesis_claim_refs=["synthesis:emissions:conflict","synthesis:emissions:explanations","synthesis:emissions:causal-limit"],
            explanation_set_refs=["explanation-set:emissions-discrepancy"],
            retained_hypothesis_refs=["hypothesis:emissions:scope-difference","hypothesis:emissions:temporal-change","hypothesis:emissions:measurement-process","hypothesis:emissions:real-intervention-effect"],
            counterevidence_position_refs=["position:emissions-causal:challenge"],
            qualification_refs=["strict-claim-conflict-remains-unresolved","causal-identification-not-established"],
            unresolved_questions=["Are evaluation periods identical?","Are emissions boundaries comparable?","Do measurement protocols differ?","Is there sufficient causal identification for a real intervention effect?"],
            confidence_label="unresolved",
        ),
        ResearchAnswerObject(
            answer_id="answer:actor-continuity",
            question="Do 'Ministry' and 'agency' refer to the same institution?",
            concise_answer="The current evidence supports an actor-continuity candidate but does not authorize canonical identity. Same-institution and distinct-related-institution explanations both remain live pending authoritative organizational lineage.",
            disposition=AnswerDisposition.unresolved,
            synthesis_claim_refs=["synthesis:actor:candidate","synthesis:actor:no-merge"],
            explanation_set_refs=["explanation-set:actor-continuity"],
            retained_hypothesis_refs=["hypothesis:actor:same-institution-label-variation","hypothesis:actor:distinct-related-institutions"],
            qualification_refs=["identity-merge-not-authorized"],
            unresolved_questions=["Do authoritative organizational records establish one continuing identity?"],
            confidence_label="unresolved",
        ),
        ResearchAnswerObject(
            answer_id="answer:cost-corroboration",
            question="Does the English cost statement independently corroborate the Chinese original?",
            concise_answer="No. The governed lineage identifies the English statement as a derived translation, so it is not independent corroboration. This resolves source independence, not the truth of the underlying cost claim.",
            disposition=AnswerDisposition.provenance_resolved_claim_unresolved,
            synthesis_claim_refs=["synthesis:cost:derived","synthesis:cost:not-truth"],
            explanation_set_refs=["explanation-set:cost-source-independence"],
            retained_hypothesis_refs=["hypothesis:cost:translation-derivation"],
            rejected_hypothesis_refs=["hypothesis:cost:independent-corroboration"],
            counterevidence_position_refs=["position:cost-independent:challenge"],
            qualification_refs=["derived-translation-not-independent-source","claim-truth-remains-unresolved"],
            unresolved_questions=["Does any genuinely independent cost source corroborate the original-language claim?"],
            confidence_label="qualified",
        ),
    ]
    claims=[
        SynthesisClaim(synthesis_claim_id="synthesis:emissions:conflict",answer_ref="answer:emissions-effect",role=SynthesisClaimRole.answer,statement="The governed source set contains unresolved conflicting emissions findings.",evidence_position_refs=["position:emissions-scope:support","position:emissions-temporal:support"],explanation_set_refs=["explanation-set:emissions-discrepancy"],qualification_refs=["strict-claim-conflict-remains-unresolved"]),
        SynthesisClaim(synthesis_claim_id="synthesis:emissions:explanations",answer_ref="answer:emissions-effect",role=SynthesisClaimRole.qualification,statement="Scope difference, temporal change, measurement process, and a real intervention effect remain candidate explanations; none is automatically selected.",hypothesis_refs=["hypothesis:emissions:scope-difference","hypothesis:emissions:temporal-change","hypothesis:emissions:measurement-process","hypothesis:emissions:real-intervention-effect"],explanation_set_refs=["explanation-set:emissions-discrepancy"]),
        SynthesisClaim(synthesis_claim_id="synthesis:emissions:causal-limit",answer_ref="answer:emissions-effect",role=SynthesisClaimRole.counterevidence,statement="The current context does not establish sufficient causal identification for an intervention-effect conclusion.",hypothesis_refs=["hypothesis:emissions:real-intervention-effect"],evidence_position_refs=["position:emissions-causal:challenge"],qualification_refs=["causal-identification-not-established"]),
        SynthesisClaim(synthesis_claim_id="synthesis:actor:candidate",answer_ref="answer:actor-continuity",role=SynthesisClaimRole.answer,statement="Ministry and agency remain a plausible continuity candidate, but the identity question is unresolved.",hypothesis_refs=["hypothesis:actor:same-institution-label-variation","hypothesis:actor:distinct-related-institutions"],explanation_set_refs=["explanation-set:actor-continuity"]),
        SynthesisClaim(synthesis_claim_id="synthesis:actor:no-merge",answer_ref="answer:actor-continuity",role=SynthesisClaimRole.qualification,statement="Canonical identity merge is not authorized without authoritative organizational lineage.",explanation_set_refs=["explanation-set:actor-continuity"],qualification_refs=["identity-merge-not-authorized"]),
        SynthesisClaim(synthesis_claim_id="synthesis:cost:derived",answer_ref="answer:cost-corroboration",role=SynthesisClaimRole.answer,statement="The English cost statement is a derived translation of the Chinese original and therefore is not independent corroboration.",hypothesis_refs=["hypothesis:cost:translation-derivation","hypothesis:cost:independent-corroboration"],evidence_position_refs=["position:cost-translation:support","position:cost-independent:challenge"],explanation_set_refs=["explanation-set:cost-source-independence"],qualification_refs=["derived-translation-not-independent-source"],original_language_refs=["zh-original:proposal-cost"]),
        SynthesisClaim(synthesis_claim_id="synthesis:cost:not-truth",answer_ref="answer:cost-corroboration",role=SynthesisClaimRole.unresolved,statement="Resolving source independence does not establish whether the proposal actually reduces costs.",explanation_set_refs=["explanation-set:cost-source-independence"],qualification_refs=["claim-truth-remains-unresolved"]),
    ]
    prov=ResearchAnswerProvenanceRecord(
        provenance_id="research-answer-provenance:reference",
        predecessor_hypothesis_fingerprint_sha256=pred.fingerprint(),
        answer_refs=[x.answer_id for x in answers],
        synthesis_claim_refs=[x.synthesis_claim_id for x in claims],
        method="Compose research answers only from governed v4.18 hypothesis sets and evidence positions. Preserve retained and rejected explanations, counterevidence, unresolved questions, source-independence constraints, original-language authority, and causal/identity qualifications. Concise answers are presentation objects, not truth verdicts, evidence records, or probability estimates.",
    )
    af={x.answer_id:x.fingerprint() for x in answers}; cf={x.synthesis_claim_id:x.fingerprint() for x in claims}
    det=canonical_sha256({"predecessor":pred.fingerprint(),"answers":af,"claims":cf})
    snap=ResearchAnswerSnapshot(snapshot_id="research-answer-snapshot:reference",predecessor_hypothesis_fingerprint_sha256=pred.fingerprint(),answer_fingerprints=af,synthesis_claim_fingerprints=cf,deterministic_synthesis_fingerprint_sha256=det)
    return SemanticSynthesisResearchAnswerBundle(policy=policy,predecessor_hypothesis_context=pred,synthesis_claims=claims,research_answers=answers,provenance_records=[prov],snapshots=[snap])


def contract_document() -> dict:
    b=reference_semantic_synthesis_research_answer_bundle()
    return {
        "ok":True,"release":CORE_RELEASE,"contract":CONTRACT_VERSION,"predecessor_contract":PREDECESSOR_CONTRACT,
        "identity":{"product":"Sustainable Catalyst Platform Core","build":"Semantic Synthesis & Research Answer Object","major_api":"v4"},
        "principles":{
            "synthesis_preserves_counterevidence":True,"synthesis_preserves_competing_explanations":True,"original_language_remains_authoritative":True,"translation_lineage_is_preserved":True,"concise_answer_may_not_drop_material_uncertainty":True,
        },
        "boundaries":{
            "answer_disposition_establishes_truth":False,"answer_confidence_establishes_probability":False,"majority_source_count_establishes_truth":False,"rejected_explanation_establishes_opposite_truth":False,"automatic_evidence_promotion_performed":False,"automatic_hypothesis_selection_performed":False,"automatic_context_graph_mutation_performed":False,"automatic_evidence_graph_mutation_performed":False,"automatic_knowledge_graph_mutation_performed":False,"automatic_identity_graph_mutation_performed":False,
        },
        "roadmap_integration":{"extends_v4180_contextual_hypothesis_competing_explanations":True,"prepares_v4200_unified_contextual_reasoning_runtime":True},
        "reference":{
            "predecessor_release":"4.18.0","predecessor_fingerprint_sha256":b.predecessor_hypothesis_context.fingerprint(),"research_answers":len(b.research_answers),"synthesis_claims":len(b.synthesis_claims),"unresolved_answers":sum(x.disposition==AnswerDisposition.unresolved for x in b.research_answers),"provenance_resolved_claim_unresolved_answers":sum(x.disposition==AnswerDisposition.provenance_resolved_claim_unresolved for x in b.research_answers),"answers_preserving_counterevidence":sum(bool(x.counterevidence_position_refs) for x in b.research_answers),"answers_with_live_hypotheses":sum(bool(x.retained_hypothesis_refs) for x in b.research_answers),"snapshots":len(b.snapshots),"bundle_fingerprint_sha256":b.fingerprint(),
        },
        "database_migration":"none",
    }
