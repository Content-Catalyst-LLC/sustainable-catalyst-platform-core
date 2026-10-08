from __future__ import annotations

from enum import Enum
from functools import lru_cache
from typing import Literal

from pydantic import BaseModel, Field, model_validator

from .computational_runtime_objects import canonical_sha256
from .contextual_causal_language_mechanism import (
    ContextualCausalLanguageMechanismBundle,
    reference_contextual_causal_language_mechanism_bundle,
)

CORE_RELEASE = "4.16.0"
CONTRACT_VERSION = "sc.core.narrative-framing-perspective-intelligence.v1"
PREDECESSOR_CONTRACT = "sc.core.contextual-causal-language-mechanism-intelligence.v1"


class FramingDimension(str, Enum):
    problem_definition = "problem-definition"
    outcome_emphasis = "outcome-emphasis"
    benefit_emphasis = "benefit-emphasis"
    harm_emphasis = "harm-emphasis"
    uncertainty = "uncertainty"
    responsibility = "responsibility"
    accountability = "accountability"
    urgency = "urgency"
    solution_orientation = "solution-orientation"
    scope_qualification = "scope-qualification"
    mechanism_explanation = "mechanism-explanation"
    distributional_effect = "distributional-effect"


class EmphasisState(str, Enum):
    foregrounded = "foregrounded"
    qualified = "qualified"
    backgrounded = "backgrounded"
    omitted = "omitted"
    contested = "contested"
    unresolved = "unresolved"


class NarrativeFrameKind(str, Enum):
    performance_failure = "performance-failure"
    prospective_benefit = "prospective-benefit"
    observed_efficacy = "observed-efficacy"
    qualified_scope = "qualified-scope"
    economic_possibility = "economic-possibility"
    evidence_conflict = "evidence-conflict"
    mechanism_explanation = "mechanism-explanation"
    accountability = "accountability"
    unresolved = "unresolved"


class PerspectiveRelationship(str, Enum):
    convergent = "convergent"
    divergent = "divergent"
    complementary = "complementary"
    scope_dependent = "scope-dependent"
    modality_dependent = "modality-dependent"
    cross_language_aligned = "cross-language-aligned"
    unresolved = "unresolved"


class FramingReviewState(str, Enum):
    generated = "generated"
    reviewed = "reviewed"
    accepted = "accepted"
    disputed = "disputed"
    unresolved = "unresolved"


class NarrativeFramingPolicy(BaseModel):
    policy_id: str = Field(min_length=3, max_length=500)
    predecessor_causal_context_remains_immutable: Literal[True] = True
    framing_is_descriptive_not_truth_adjudication: Literal[True] = True
    framing_difference_is_not_factual_contradiction: Literal[True] = True
    emphasis_is_not_manipulation: Literal[True] = True
    omission_is_not_deception: Literal[True] = True
    perspective_is_not_private_motive: Literal[True] = True
    source_stance_is_not_source_credibility: Literal[True] = True
    framing_analysis_is_not_ideology_classification: Literal[True] = True
    causal_interpretation_must_remain_distinct: Literal[True] = True
    evidence_review_authority_must_remain_upstream: Literal[True] = True
    original_language_remains_authoritative: Literal[True] = True
    translation_remains_derived: Literal[True] = True
    unresolved_context_must_carry_forward: Literal[True] = True
    framing_score_establishes_truth: Literal[False] = False
    framing_score_establishes_bias: Literal[False] = False
    framing_score_establishes_credibility: Literal[False] = False
    automatic_context_graph_mutation_authorized: Literal[False] = False
    automatic_evidence_graph_mutation_authorized: Literal[False] = False
    automatic_knowledge_graph_mutation_authorized: Literal[False] = False
    automatic_identity_graph_mutation_authorized: Literal[False] = False


class SourcePerspective(BaseModel):
    perspective_id: str = Field(min_length=3, max_length=500)
    source_context_ref: str = Field(min_length=3, max_length=500)
    source_label: str = Field(min_length=3, max_length=1000)
    language_tag: str = Field(min_length=2, max_length=50)
    claim_refs: list[str] = Field(min_length=1)
    causal_assessment_refs: list[str] = Field(default_factory=list)
    attributed_role: str = Field(min_length=3, max_length=500)
    stance_summary: str = Field(min_length=3, max_length=2000)
    qualification_refs: list[str] = Field(default_factory=list)
    unresolved_refs: list[str] = Field(default_factory=list)
    derived_representation: bool = False
    perspective_is_observed_source_position_not_private_motive: Literal[True] = True

    @model_validator(mode="after")
    def validate_refs(self):
        for values, label in [
            (self.claim_refs, "claim_refs"),
            (self.causal_assessment_refs, "causal_assessment_refs"),
            (self.qualification_refs, "qualification_refs"),
            (self.unresolved_refs, "unresolved_refs"),
        ]:
            if len(values) != len(set(values)):
                raise ValueError(f"{label} must be unique")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class FramingSignal(BaseModel):
    signal_id: str = Field(min_length=3, max_length=500)
    perspective_ref: str = Field(min_length=3, max_length=500)
    claim_refs: list[str] = Field(min_length=1)
    dimension: FramingDimension
    emphasis: EmphasisState
    surface_basis: str = Field(min_length=1, max_length=4000)
    interpretation: str = Field(min_length=3, max_length=3000)
    qualification_refs: list[str] = Field(default_factory=list)
    unresolved_refs: list[str] = Field(default_factory=list)
    signal_is_descriptive_not_motive_inference: Literal[True] = True
    signal_is_not_bias_verdict: Literal[True] = True

    @model_validator(mode="after")
    def validate_refs(self):
        if len(self.claim_refs) != len(set(self.claim_refs)):
            raise ValueError("claim_refs must be unique")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class NarrativeFrame(BaseModel):
    frame_id: str = Field(min_length=3, max_length=500)
    label: str = Field(min_length=3, max_length=1000)
    frame_kind: NarrativeFrameKind
    perspective_refs: list[str] = Field(min_length=1)
    claim_refs: list[str] = Field(min_length=1)
    signal_refs: list[str] = Field(min_length=1)
    frame_summary: str = Field(min_length=3, max_length=3000)
    foregrounded_dimensions: list[FramingDimension] = Field(min_length=1)
    backgrounded_or_unaddressed_dimensions: list[FramingDimension] = Field(default_factory=list)
    qualification_refs: list[str] = Field(default_factory=list)
    unresolved_refs: list[str] = Field(default_factory=list)
    frame_is_interpretive_description_not_truth_verdict: Literal[True] = True

    @model_validator(mode="after")
    def validate_refs(self):
        for values, label in [
            (self.perspective_refs, "perspective_refs"),
            (self.claim_refs, "claim_refs"),
            (self.signal_refs, "signal_refs"),
            (self.foregrounded_dimensions, "foregrounded_dimensions"),
            (self.backgrounded_or_unaddressed_dimensions, "backgrounded_or_unaddressed_dimensions"),
        ]:
            if len(values) != len(set(values)):
                raise ValueError(f"{label} must be unique")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class PerspectiveComparison(BaseModel):
    comparison_id: str = Field(min_length=3, max_length=500)
    left_frame_ref: str = Field(min_length=3, max_length=500)
    right_frame_ref: str = Field(min_length=3, max_length=500)
    relationship: PerspectiveRelationship
    shared_dimensions: list[FramingDimension] = Field(default_factory=list)
    differing_dimensions: list[FramingDimension] = Field(default_factory=list)
    rationale: str = Field(min_length=3, max_length=3000)
    qualification_refs: list[str] = Field(default_factory=list)
    unresolved_refs: list[str] = Field(default_factory=list)
    comparison_establishes_truth: Literal[False] = False
    comparison_establishes_bias: Literal[False] = False

    @model_validator(mode="after")
    def validate_comparison(self):
        if self.left_frame_ref == self.right_frame_ref:
            raise ValueError("comparison requires distinct frames")
        if len(self.shared_dimensions) != len(set(self.shared_dimensions)):
            raise ValueError("shared_dimensions must be unique")
        if len(self.differing_dimensions) != len(set(self.differing_dimensions)):
            raise ValueError("differing_dimensions must be unique")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class NarrativeFramingAssessment(BaseModel):
    assessment_id: str = Field(min_length=3, max_length=500)
    frame_refs: list[str] = Field(min_length=1)
    comparison_refs: list[str] = Field(default_factory=list)
    causal_assessment_refs: list[str] = Field(default_factory=list)
    conclusion: str = Field(min_length=3, max_length=4000)
    qualification_refs: list[str] = Field(default_factory=list)
    unresolved_refs: list[str] = Field(default_factory=list)
    state: FramingReviewState = FramingReviewState.reviewed
    reviewer_ref: str | None = Field(default=None, max_length=500)
    establishes_truth: Literal[False] = False
    establishes_bias: Literal[False] = False
    establishes_motive: Literal[False] = False

    @model_validator(mode="after")
    def validate_assessment(self):
        if self.state in {FramingReviewState.reviewed, FramingReviewState.accepted, FramingReviewState.disputed} and not self.reviewer_ref:
            raise ValueError("reviewed/accepted/disputed assessment requires reviewer_ref")
        for values, label in [
            (self.frame_refs, "frame_refs"),
            (self.comparison_refs, "comparison_refs"),
            (self.causal_assessment_refs, "causal_assessment_refs"),
        ]:
            if len(values) != len(set(values)):
                raise ValueError(f"{label} must be unique")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class NarrativeFramingProvenanceRecord(BaseModel):
    provenance_id: str = Field(min_length=3, max_length=500)
    predecessor_causal_context_fingerprint_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    subject_refs: list[str] = Field(min_length=1)
    method: str = Field(min_length=3, max_length=4000)
    provenance_is_not_source_credibility_assessment: Literal[True] = True

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class NarrativeFramingSnapshot(BaseModel):
    snapshot_id: str = Field(min_length=3, max_length=500)
    predecessor_causal_context_fingerprint_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    perspective_fingerprints: dict[str, str]
    signal_fingerprints: dict[str, str]
    frame_fingerprints: dict[str, str]
    comparison_fingerprints: dict[str, str]
    assessment_fingerprints: dict[str, str]
    deterministic_framing_context_fingerprint_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    supersedable: Literal[True] = True
    snapshot_is_not_truth_or_bias_certification: Literal[True] = True

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class NarrativeFramingPerspectiveBundle(BaseModel):
    release: Literal["4.16.0"] = "4.16.0"
    contract: Literal[CONTRACT_VERSION] = CONTRACT_VERSION
    predecessor_contract: Literal[PREDECESSOR_CONTRACT] = PREDECESSOR_CONTRACT
    policy: NarrativeFramingPolicy
    predecessor_causal_context: ContextualCausalLanguageMechanismBundle
    perspectives: list[SourcePerspective] = Field(min_length=1)
    signals: list[FramingSignal] = Field(min_length=1)
    frames: list[NarrativeFrame] = Field(min_length=1)
    comparisons: list[PerspectiveComparison] = Field(min_length=1)
    assessments: list[NarrativeFramingAssessment] = Field(min_length=1)
    provenance_records: list[NarrativeFramingProvenanceRecord] = Field(min_length=1)
    snapshots: list[NarrativeFramingSnapshot] = Field(min_length=1)
    database_migration: Literal["none"] = "none"

    @model_validator(mode="after")
    def validate_bundle(self):
        pred = self.predecessor_causal_context
        if pred.release != "4.15.0" or pred.contract != PREDECESSOR_CONTRACT:
            raise ValueError("v4.16 must preserve governed v4.15 causal-context predecessor")

        def unique(values: list[str], label: str):
            if len(values) != len(set(values)):
                raise ValueError(f"{label} must be unique")

        unique([x.perspective_id for x in self.perspectives], "perspective ids")
        unique([x.signal_id for x in self.signals], "signal ids")
        unique([x.frame_id for x in self.frames], "frame ids")
        unique([x.comparison_id for x in self.comparisons], "comparison ids")
        unique([x.assessment_id for x in self.assessments], "assessment ids")
        unique([x.provenance_id for x in self.provenance_records], "provenance ids")
        unique([x.snapshot_id for x in self.snapshots], "snapshot ids")

        claim_bundle = pred.predecessor_evidence_context.predecessor_claim_comparison
        claims = {x.claim_id: x for x in claim_bundle.claims}
        source_contexts = {x.source_context_id: x for x in claim_bundle.source_contexts}
        causal_assessments = {x.assessment_id: x for x in pred.assessments}
        perspectives = {x.perspective_id: x for x in self.perspectives}
        signals = {x.signal_id: x for x in self.signals}
        frames = {x.frame_id: x for x in self.frames}
        comparisons = {x.comparison_id: x for x in self.comparisons}

        for p in self.perspectives:
            if p.source_context_ref not in source_contexts:
                raise ValueError("perspective source_context_ref must resolve")
            if not set(p.claim_refs).issubset(claims):
                raise ValueError("perspective claim refs must resolve")
            if any(claims[c].source_context_ref != p.source_context_ref for c in p.claim_refs):
                raise ValueError("perspective claims must belong to source context")
            if not set(p.causal_assessment_refs).issubset(causal_assessments):
                raise ValueError("perspective causal assessment refs must resolve")
            if source_contexts[p.source_context_ref].derived_representation and not p.derived_representation:
                raise ValueError("derived source context must remain derived in perspective")

        for s in self.signals:
            if s.perspective_ref not in perspectives:
                raise ValueError("framing signal perspective_ref must resolve")
            if not set(s.claim_refs).issubset(claims):
                raise ValueError("framing signal claim refs must resolve")
            if not set(s.claim_refs).issubset(set(perspectives[s.perspective_ref].claim_refs)):
                raise ValueError("framing signal claims must belong to perspective")

        for f in self.frames:
            if not set(f.perspective_refs).issubset(perspectives):
                raise ValueError("frame perspective refs must resolve")
            if not set(f.claim_refs).issubset(claims):
                raise ValueError("frame claim refs must resolve")
            if not set(f.signal_refs).issubset(signals):
                raise ValueError("frame signal refs must resolve")
            if any(signals[s].perspective_ref not in f.perspective_refs for s in f.signal_refs):
                raise ValueError("frame signal must belong to one of its perspectives")

        for c in self.comparisons:
            if c.left_frame_ref not in frames or c.right_frame_ref not in frames:
                raise ValueError("comparison frame refs must resolve")
            left=frames[c.left_frame_ref]; right=frames[c.right_frame_ref]
            if c.relationship == PerspectiveRelationship.cross_language_aligned:
                languages={perspectives[p].language_tag for p in left.perspective_refs + right.perspective_refs}
                if len(languages) < 2:
                    raise ValueError("cross-language-aligned comparison requires at least two languages")

        for a in self.assessments:
            if not set(a.frame_refs).issubset(frames):
                raise ValueError("assessment frame refs must resolve")
            if not set(a.comparison_refs).issubset(comparisons):
                raise ValueError("assessment comparison refs must resolve")
            if not set(a.causal_assessment_refs).issubset(causal_assessments):
                raise ValueError("assessment causal refs must resolve")

        pred_fp = pred.fingerprint()
        all_subjects = set(perspectives) | set(signals) | set(frames) | set(comparisons) | {x.assessment_id for x in self.assessments}
        for p in self.provenance_records:
            if p.predecessor_causal_context_fingerprint_sha256 != pred_fp:
                raise ValueError("provenance predecessor fingerprint must match v4.15")
            if not set(p.subject_refs).issubset(all_subjects):
                raise ValueError("provenance refs must resolve")

        expected_p={x.perspective_id:x.fingerprint() for x in self.perspectives}
        expected_s={x.signal_id:x.fingerprint() for x in self.signals}
        expected_f={x.frame_id:x.fingerprint() for x in self.frames}
        expected_c={x.comparison_id:x.fingerprint() for x in self.comparisons}
        expected_a={x.assessment_id:x.fingerprint() for x in self.assessments}
        material={"predecessor":pred_fp,"perspectives":expected_p,"signals":expected_s,"frames":expected_f,"comparisons":expected_c,"assessments":expected_a}
        for snap in self.snapshots:
            if snap.predecessor_causal_context_fingerprint_sha256 != pred_fp:
                raise ValueError("snapshot predecessor fingerprint must match v4.15")
            if snap.perspective_fingerprints != expected_p or snap.signal_fingerprints != expected_s:
                raise ValueError("snapshot perspective/signal fingerprints must be exact")
            if snap.frame_fingerprints != expected_f or snap.comparison_fingerprints != expected_c:
                raise ValueError("snapshot frame/comparison fingerprints must be exact")
            if snap.assessment_fingerprints != expected_a:
                raise ValueError("snapshot assessment fingerprints must be exact")
            if snap.deterministic_framing_context_fingerprint_sha256 != canonical_sha256(material):
                raise ValueError("snapshot deterministic framing fingerprint mismatch")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


@lru_cache(maxsize=1)
def reference_narrative_framing_perspective_bundle() -> NarrativeFramingPerspectiveBundle:
    pred=reference_contextual_causal_language_mechanism_bundle()
    claim_bundle=pred.predecessor_evidence_context.predecessor_claim_comparison
    claims={x.claim_id:x for x in claim_bundle.claims}
    sources={x.source_context_id:x for x in claim_bundle.source_contexts}

    by_source: dict[str,list[str]]={}
    for c in claim_bundle.claims:
        by_source.setdefault(c.source_context_ref,[]).append(c.claim_id)

    causal_by_claim: dict[str,list[str]]={}
    for a in pred.assessments:
        signal_claims=[]
        sigs={s.signal_id:s for s in pred.signals}
        for sr in a.subject_signal_refs:
            signal_claims.append(sigs[sr].claim_ref)
        for claim in signal_claims:
            causal_by_claim.setdefault(claim,[]).append(a.assessment_id)

    perspective_specs=[
        ("perspective:v45-report","claim-source:v45:epistemic-report","research report","Reports a negative emissions outcome while also presenting a possible cost benefit.",["source-level-attribution-preserved"], ["same-measure:reference-corpus"]),
        ("perspective:v46-agency","claim-source:v46:public-hearing","agency speaker","Presents a prospective possibility that the measure may reduce emissions.",["modal-possibility-preserved"], ["same-measure:reference-corpus"]),
        ("perspective:v413-audit","claim-source:v413:audit","audit source","Presents a positive emissions outcome for the reference evaluation period.",["reference-period-preserved"], ["strict-evidence-conflict:emissions-effect"]),
        ("perspective:v413-review","claim-source:v413:review","review source","Qualifies the emissions question to direct emissions and explicitly leaves indirect emissions unassessed.",["direct-emissions-scope"], ["indirect-emissions:not-assessed"]),
        ("perspective:v48-zh","claim-source:v48:zh-original","Chinese original-language source","Presents possible cost reduction in the authoritative original-language representation.",["original-language-authority"], ["causal-effect:proposal-to-costs"]),
        ("perspective:v48-en","claim-source:v48:en-derived","English derived representation","Preserves the possible cost-reduction framing in a derived English representation.",["translation-derived"], ["causal-effect:proposal-to-costs"]),
    ]
    perspectives=[]
    for pid,sref,role,summary,quals,unresolved in perspective_specs:
        cref=by_source[sref]
        ca=[]
        for c in cref: ca.extend(causal_by_claim.get(c,[]))
        src=sources[sref]
        perspectives.append(SourcePerspective(
            perspective_id=pid, source_context_ref=sref, source_label=src.label, language_tag=src.language_tag,
            claim_refs=cref, causal_assessment_refs=list(dict.fromkeys(ca)), attributed_role=role,
            stance_summary=summary, qualification_refs=quals, unresolved_refs=unresolved,
            derived_representation=src.derived_representation,
        ))
    pmap={x.perspective_id:x for x in perspectives}

    signal_specs=[
        ("signal:v45:emissions-outcome","perspective:v45-report",["claim:v45:measure-no-emissions-reduction"],FramingDimension.outcome_emphasis,EmphasisState.foregrounded,"the measure did not reduce emissions","Foregrounds a negative reported emissions outcome."),
        ("signal:v45:cost-possibility","perspective:v45-report",["claim:v45:proposal-may-lower-costs"],FramingDimension.benefit_emphasis,EmphasisState.qualified,"it may lower costs","Presents a possible economic benefit while preserving modal uncertainty."),
        ("signal:v46:possible-emissions-benefit","perspective:v46-agency",["claim:v46:measure-may-reduce-emissions"],FramingDimension.benefit_emphasis,EmphasisState.foregrounded,"the measure may reduce emissions","Foregrounds a prospective environmental benefit."),
        ("signal:v46:uncertainty","perspective:v46-agency",["claim:v46:measure-may-reduce-emissions"],FramingDimension.uncertainty,EmphasisState.qualified,"may reduce","Explicit modality qualifies the prospective benefit."),
        ("signal:v413-audit:efficacy","perspective:v413-audit",["claim:v413:audit-reduced-emissions"],FramingDimension.outcome_emphasis,EmphasisState.foregrounded,"reduced emissions during the reference evaluation period","Foregrounds an affirmative evaluated outcome."),
        ("signal:v413-audit:scope","perspective:v413-audit",["claim:v413:audit-reduced-emissions"],FramingDimension.scope_qualification,EmphasisState.qualified,"during the reference evaluation period","Bounds the outcome to the reference evaluation period."),
        ("signal:v413-review:direct-scope","perspective:v413-review",["claim:v413:review-no-direct-emissions-reduction"],FramingDimension.scope_qualification,EmphasisState.foregrounded,"did not reduce direct emissions","Foregrounds the narrower direct-emissions scope."),
        ("signal:v413-review:unassessed-indirect","perspective:v413-review",["claim:v413:review-no-direct-emissions-reduction"],FramingDimension.uncertainty,EmphasisState.qualified,"indirect emissions were not assessed","Explicitly preserves an unassessed outcome domain."),
        ("signal:v48-zh:economic-benefit","perspective:v48-zh",["claim:v48:zh-proposal-may-lower-costs"],FramingDimension.benefit_emphasis,EmphasisState.foregrounded,"该提案可能降低成本。","Foregrounds possible cost reduction in the original-language source."),
        ("signal:v48-zh:uncertainty","perspective:v48-zh",["claim:v48:zh-proposal-may-lower-costs"],FramingDimension.uncertainty,EmphasisState.qualified,"可能","Preserves possibility rather than certainty."),
        ("signal:v48-en:economic-benefit","perspective:v48-en",["claim:v48:en-proposal-may-reduce-costs"],FramingDimension.benefit_emphasis,EmphasisState.foregrounded,"The proposal may reduce costs.","Preserves the cost-reduction framing in translation."),
        ("signal:v48-en:translation-qualification","perspective:v48-en",["claim:v48:en-proposal-may-reduce-costs"],FramingDimension.scope_qualification,EmphasisState.qualified,"derived English representation","Marks this perspective as derived rather than independent source framing."),
    ]
    signals=[FramingSignal(signal_id=i,perspective_ref=p,claim_refs=c,dimension=d,emphasis=e,surface_basis=b,interpretation=t,
                           qualification_refs=(['translation-derived'] if p=='perspective:v48-en' else []),
                           unresolved_refs=pmap[p].unresolved_refs) for i,p,c,d,e,b,t in signal_specs]
    smap={x.signal_id:x for x in signals}

    frame_specs=[
        ("frame:v45:performance-and-cost","Negative performance with possible economic benefit",NarrativeFrameKind.performance_failure,["perspective:v45-report"],by_source["claim-source:v45:epistemic-report"],["signal:v45:emissions-outcome","signal:v45:cost-possibility"],"Frames the policy through a negative emissions outcome while retaining a separate possible cost benefit.",[FramingDimension.outcome_emphasis,FramingDimension.benefit_emphasis],[FramingDimension.mechanism_explanation]),
        ("frame:v46:prospective-benefit","Prospective emissions benefit",NarrativeFrameKind.prospective_benefit,["perspective:v46-agency"],by_source["claim-source:v46:public-hearing"],["signal:v46:possible-emissions-benefit","signal:v46:uncertainty"],"Frames the measure as potentially beneficial while explicitly preserving uncertainty.",[FramingDimension.benefit_emphasis,FramingDimension.uncertainty],[FramingDimension.outcome_emphasis]),
        ("frame:v413:audit-efficacy","Audit efficacy",NarrativeFrameKind.observed_efficacy,["perspective:v413-audit"],by_source["claim-source:v413:audit"],["signal:v413-audit:efficacy","signal:v413-audit:scope"],"Frames the reference-period result as an affirmative observed emissions outcome.",[FramingDimension.outcome_emphasis,FramingDimension.scope_qualification],[FramingDimension.mechanism_explanation]),
        ("frame:v413:review-qualified-scope","Qualified direct-emissions review",NarrativeFrameKind.qualified_scope,["perspective:v413-review"],by_source["claim-source:v413:review"],["signal:v413-review:direct-scope","signal:v413-review:unassessed-indirect"],"Frames the result narrowly around direct emissions and leaves indirect emissions unresolved.",[FramingDimension.scope_qualification,FramingDimension.uncertainty],[FramingDimension.benefit_emphasis]),
        ("frame:v48:zh-economic-possibility","Original-language economic possibility",NarrativeFrameKind.economic_possibility,["perspective:v48-zh"],by_source["claim-source:v48:zh-original"],["signal:v48-zh:economic-benefit","signal:v48-zh:uncertainty"],"Frames the proposal as possibly reducing costs in the authoritative Chinese representation.",[FramingDimension.benefit_emphasis,FramingDimension.uncertainty],[FramingDimension.outcome_emphasis]),
        ("frame:v48:en-derived-economic-possibility","Derived English economic possibility",NarrativeFrameKind.economic_possibility,["perspective:v48-en"],by_source["claim-source:v48:en-derived"],["signal:v48-en:economic-benefit","signal:v48-en:translation-qualification"],"Preserves the same possible cost-benefit frame in a derived English representation; it is not an independent source perspective.",[FramingDimension.benefit_emphasis,FramingDimension.scope_qualification],[FramingDimension.outcome_emphasis]),
    ]
    frames=[NarrativeFrame(frame_id=i,label=l,frame_kind=k,perspective_refs=p,claim_refs=c,signal_refs=s,frame_summary=summary,
                           foregrounded_dimensions=fg,backgrounded_or_unaddressed_dimensions=bg,
                           qualification_refs=sum([pmap[x].qualification_refs for x in p],[]),
                           unresolved_refs=sum([pmap[x].unresolved_refs for x in p],[]))
            for i,l,k,p,c,s,summary,fg,bg in frame_specs]

    comparisons=[
        PerspectiveComparison(comparison_id="comparison:report-vs-agency",left_frame_ref="frame:v45:performance-and-cost",right_frame_ref="frame:v46:prospective-benefit",relationship=PerspectiveRelationship.modality_dependent,shared_dimensions=[FramingDimension.benefit_emphasis],differing_dimensions=[FramingDimension.outcome_emphasis,FramingDimension.uncertainty],rationale="The report foregrounds a negative asserted outcome while the agency statement foregrounds a possible future benefit. The framing difference is modality-dependent and is not itself a factual verdict.",qualification_refs=["claim-comparison:apparent-contradiction-preserved"],unresolved_refs=["causal-effect:measure-to-emissions"]),
        PerspectiveComparison(comparison_id="comparison:report-vs-audit",left_frame_ref="frame:v45:performance-and-cost",right_frame_ref="frame:v413:audit-efficacy",relationship=PerspectiveRelationship.divergent,shared_dimensions=[FramingDimension.outcome_emphasis],differing_dimensions=[FramingDimension.benefit_emphasis],rationale="Both foreground emissions performance for the same reference problem but report opposing outcomes. v4.16 preserves this as divergent framing around an unresolved evidence conflict rather than deciding which source is true.",qualification_refs=["strict-contradiction-preserved"],unresolved_refs=["causal-effect:measure-to-emissions"]),
        PerspectiveComparison(comparison_id="comparison:audit-vs-review",left_frame_ref="frame:v413:audit-efficacy",right_frame_ref="frame:v413:review-qualified-scope",relationship=PerspectiveRelationship.scope_dependent,shared_dimensions=[FramingDimension.outcome_emphasis,FramingDimension.scope_qualification],differing_dimensions=[FramingDimension.uncertainty],rationale="The audit speaks to total emissions while the review narrows the frame to direct emissions and leaves indirect emissions unassessed. The difference is scope-dependent rather than a simple binary disagreement.",qualification_refs=["direct-vs-total-emissions-scope"],unresolved_refs=["indirect-emissions:not-assessed"]),
        PerspectiveComparison(comparison_id="comparison:zh-vs-en-cost",left_frame_ref="frame:v48:zh-economic-possibility",right_frame_ref="frame:v48:en-derived-economic-possibility",relationship=PerspectiveRelationship.cross_language_aligned,shared_dimensions=[FramingDimension.benefit_emphasis,FramingDimension.uncertainty],differing_dimensions=[FramingDimension.scope_qualification],rationale="The English representation preserves the Chinese source's possible cost-reduction framing, but translation lineage means the two frames are not independent source perspectives.",qualification_refs=["original-language-authority","translation-derived-not-independent"],unresolved_refs=["causal-effect:proposal-to-costs"]),
    ]

    assessments=[
        NarrativeFramingAssessment(assessment_id="framing-assessment:emissions-perspective-plurality",frame_refs=["frame:v45:performance-and-cost","frame:v46:prospective-benefit","frame:v413:audit-efficacy","frame:v413:review-qualified-scope"],comparison_refs=["comparison:report-vs-agency","comparison:report-vs-audit","comparison:audit-vs-review"],causal_assessment_refs=["causal-assessment:emissions-effect-conflict","causal-assessment:agency-possible-emissions-effect","causal-assessment:direct-emissions-effect"],conclusion="The reference corpus contains multiple legitimate descriptive perspectives on emissions performance: negative reported outcome, possible future benefit, positive audit outcome, and a narrower direct-emissions qualification. Their coexistence does not establish which account is true or biased.",qualification_refs=["plural-framing-preserved"],unresolved_refs=["causal-effect:measure-to-emissions"],state=FramingReviewState.unresolved),
        NarrativeFramingAssessment(assessment_id="framing-assessment:modality-dependent-agency",frame_refs=["frame:v45:performance-and-cost","frame:v46:prospective-benefit"],comparison_refs=["comparison:report-vs-agency"],causal_assessment_refs=["causal-assessment:agency-possible-emissions-effect"],conclusion="The agency framing is prospective and modal, while the report is retrospective/asserted. The difference should not be flattened into either agreement or strict contradiction.",qualification_refs=["modality-preserved"],unresolved_refs=["same-period:reference-corpus"],reviewer_ref="reviewer:narrative-framing-reference"),
        NarrativeFramingAssessment(assessment_id="framing-assessment:scope-dependent-review",frame_refs=["frame:v413:audit-efficacy","frame:v413:review-qualified-scope"],comparison_refs=["comparison:audit-vs-review"],causal_assessment_refs=["causal-assessment:direct-emissions-effect"],conclusion="The review's direct-emissions frame and the audit's broader emissions frame are materially different scopes; the framing layer preserves that distinction rather than treating wording alone as contradiction.",qualification_refs=["scope-preserved"],unresolved_refs=["indirect-emissions:not-assessed"],reviewer_ref="reviewer:narrative-framing-reference"),
        NarrativeFramingAssessment(assessment_id="framing-assessment:cross-language-cost",frame_refs=["frame:v48:zh-economic-possibility","frame:v48:en-derived-economic-possibility"],comparison_refs=["comparison:zh-vs-en-cost"],causal_assessment_refs=["causal-assessment:proposal-cost-effect"],conclusion="The English translation preserves the source framing of possible cost reduction, but it remains derived from the Chinese source and cannot count as an independent perspective or corroborating narrative.",qualification_refs=["translation-lineage-preserved"],unresolved_refs=["causal-effect:proposal-to-costs"],reviewer_ref="reviewer:narrative-framing-reference"),
    ]

    subjects=[x.perspective_id for x in perspectives]+[x.signal_id for x in signals]+[x.frame_id for x in frames]+[x.comparison_id for x in comparisons]+[x.assessment_id for x in assessments]
    provenance=NarrativeFramingProvenanceRecord(provenance_id="framing-provenance:reference",predecessor_causal_context_fingerprint_sha256=pred.fingerprint(),subject_refs=subjects,method="governed descriptive narrative/framing analysis over v4.15 causal-context and predecessor claim objects; preserves source wording, modality, scope, evidence conflict, original-language authority, translation derivation, qualifications, and unresolved state")
    material={"predecessor":pred.fingerprint(),"perspectives":{x.perspective_id:x.fingerprint() for x in perspectives},"signals":{x.signal_id:x.fingerprint() for x in signals},"frames":{x.frame_id:x.fingerprint() for x in frames},"comparisons":{x.comparison_id:x.fingerprint() for x in comparisons},"assessments":{x.assessment_id:x.fingerprint() for x in assessments}}
    snapshot=NarrativeFramingSnapshot(snapshot_id="narrative-framing-snapshot:reference:v1",predecessor_causal_context_fingerprint_sha256=pred.fingerprint(),perspective_fingerprints=material["perspectives"],signal_fingerprints=material["signals"],frame_fingerprints=material["frames"],comparison_fingerprints=material["comparisons"],assessment_fingerprints=material["assessments"],deterministic_framing_context_fingerprint_sha256=canonical_sha256(material))
    return NarrativeFramingPerspectiveBundle(policy=NarrativeFramingPolicy(policy_id="narrative-framing-policy:v1"),predecessor_causal_context=pred,perspectives=perspectives,signals=signals,frames=frames,comparisons=comparisons,assessments=assessments,provenance_records=[provenance],snapshots=[snapshot])


def contract_document() -> dict:
    b=reference_narrative_framing_perspective_bundle()
    return {
        "ok":True,
        "release":CORE_RELEASE,
        "contract":CONTRACT_VERSION,
        "predecessor_contract":PREDECESSOR_CONTRACT,
        "identity":{"product":"Sustainable Catalyst Platform Core","build":"Narrative, Framing & Perspective Intelligence","major_api":"v4"},
        "principles":{
            "framing_is_descriptive_not_truth_adjudication":True,
            "framing_difference_is_not_factual_contradiction":True,
            "emphasis_is_not_manipulation":True,
            "omission_is_not_deception":True,
            "perspective_is_not_private_motive":True,
            "framing_analysis_is_not_ideology_classification":True,
            "original_language_remains_authoritative":True,
            "translation_remains_derived":True,
        },
        "boundaries":{
            "framing_score_establishes_truth":False,
            "framing_score_establishes_bias":False,
            "framing_score_establishes_credibility":False,
            "automatic_context_graph_mutation_performed":False,
            "automatic_evidence_graph_mutation_performed":False,
            "automatic_knowledge_graph_mutation_performed":False,
            "automatic_identity_graph_mutation_performed":False,
        },
        "roadmap_integration":{
            "extends_v4150_contextual_causal_language_mechanism":True,
            "prepares_v4170_cross_source_semantic_reconciliation":True,
            "prepares_v4180_contextual_hypothesis_competing_explanations":True,
            "prepares_v4190_semantic_synthesis_research_answer":True,
            "prepares_v4200_unified_contextual_reasoning_runtime":True,
        },
        "reference":{
            "predecessor_release":b.predecessor_causal_context.release,
            "predecessor_fingerprint_sha256":b.predecessor_causal_context.fingerprint(),
            "source_perspectives":len(b.perspectives),
            "framing_signals":len(b.signals),
            "narrative_frames":len(b.frames),
            "perspective_comparisons":len(b.comparisons),
            "framing_assessments":len(b.assessments),
            "unresolved_assessments":sum(x.state==FramingReviewState.unresolved for x in b.assessments),
            "derived_perspectives":sum(x.derived_representation for x in b.perspectives),
            "snapshots":len(b.snapshots),
            "bundle_fingerprint_sha256":b.fingerprint(),
        },
        "database_migration":"none",
    }
