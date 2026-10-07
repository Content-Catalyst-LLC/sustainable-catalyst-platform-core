from __future__ import annotations

from enum import Enum
from functools import lru_cache
from typing import Literal

from pydantic import BaseModel, Field, model_validator

from .computational_runtime_objects import canonical_sha256
from .evidence_context_integration import (
    EvidenceContextIntegrationBundle,
    EvidenceIndependenceState,
    reference_evidence_context_integration_bundle,
)

CORE_RELEASE = "4.15.0"
CONTRACT_VERSION = "sc.core.contextual-causal-language-mechanism-intelligence.v1"
PREDECESSOR_CONTRACT = "sc.core.evidence-context-integration-layer.v1"


class CausalLanguageKind(str, Enum):
    causal_assertion = "causal-assertion"
    causal_possibility = "causal-possibility"
    causal_denial = "causal-denial"
    association = "association"
    temporal_sequence = "temporal-sequence"
    mechanism_proposal = "mechanism-proposal"
    intervention_effect = "intervention-effect"
    counterfactual = "counterfactual"


class CausalRelationKind(str, Enum):
    causes = "causes"
    contributes_to = "contributes-to"
    reduces = "reduces"
    prevents = "prevents"
    enables = "enables"
    associated_with = "associated-with"
    mediated_by = "mediated-by"
    no_direct_effect = "no-direct-effect"
    unresolved = "unresolved"


class CausalEvidenceClass(str, Enum):
    linguistic_only = "linguistic-only"
    evidence_linked = "evidence-linked"
    observational_only = "observational-only"
    intervention_supported = "intervention-supported"
    mechanism_supported = "mechanism-supported"
    unresolved = "unresolved"


class MechanismState(str, Enum):
    proposed = "proposed"
    reported = "reported"
    supported = "supported"
    disputed = "disputed"
    unresolved = "unresolved"


class CausalReviewState(str, Enum):
    generated = "generated"
    reviewed = "reviewed"
    accepted = "accepted"
    disputed = "disputed"
    unresolved = "unresolved"


class CausalPolicy(BaseModel):
    policy_id: str = Field(min_length=3, max_length=500)
    predecessor_evidence_context_objects_remain_immutable: Literal[True] = True
    causal_language_is_distinct_from_causal_identification: Literal[True] = True
    temporal_precedence_is_not_causality: Literal[True] = True
    association_is_not_causality: Literal[True] = True
    mechanism_plausibility_is_not_mechanism_validation: Literal[True] = True
    intervention_language_is_not_experimental_evidence: Literal[True] = True
    counterfactual_language_is_not_counterfactual_estimate: Literal[True] = True
    evidence_link_is_not_causal_identification: Literal[True] = True
    source_attribution_and_modality_must_be_preserved: Literal[True] = True
    translation_lineage_must_be_preserved: Literal[True] = True
    unresolved_contradiction_must_carry_forward: Literal[True] = True
    causal_score_establishes_truth: Literal[False] = False
    causal_wording_establishes_causality: Literal[False] = False
    mechanism_count_establishes_causality: Literal[False] = False
    evidence_count_establishes_causality: Literal[False] = False
    automatic_causal_graph_mutation_authorized: Literal[False] = False
    evidence_graph_mutation_authorized: Literal[False] = False
    knowledge_graph_mutation_authorized: Literal[False] = False
    identity_graph_mutation_authorized: Literal[False] = False


class CausalLanguageSignal(BaseModel):
    signal_id: str = Field(min_length=3, max_length=500)
    claim_ref: str = Field(min_length=3, max_length=500)
    evidence_anchor_ref: str = Field(min_length=3, max_length=500)
    source_text: str = Field(min_length=1, max_length=4000)
    language_tag: str = Field(min_length=2, max_length=50)
    language_kind: CausalLanguageKind
    relation_kind: CausalRelationKind
    cause_key: str = Field(min_length=3, max_length=500)
    effect_key: str = Field(min_length=3, max_length=500)
    polarity: str = Field(min_length=3, max_length=100)
    modality: str = Field(min_length=3, max_length=100)
    attribution_ref: str = Field(min_length=3, max_length=500)
    temporal_scope_ref: str = Field(min_length=3, max_length=500)
    spatial_scope_ref: str = Field(min_length=3, max_length=500)
    qualification_refs: list[str] = Field(default_factory=list)
    unresolved_refs: list[str] = Field(default_factory=list)
    signal_is_linguistic_interpretation_not_causal_fact: Literal[True] = True

    @model_validator(mode="after")
    def validate_signal(self):
        if len(self.qualification_refs) != len(set(self.qualification_refs)):
            raise ValueError("qualification_refs must be unique")
        if len(self.unresolved_refs) != len(set(self.unresolved_refs)):
            raise ValueError("unresolved_refs must be unique")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class MechanismHypothesis(BaseModel):
    mechanism_id: str = Field(min_length=3, max_length=500)
    label: str = Field(min_length=3, max_length=1000)
    input_key: str = Field(min_length=3, max_length=500)
    mediator_keys: list[str] = Field(min_length=1)
    output_key: str = Field(min_length=3, max_length=500)
    supporting_signal_refs: list[str] = Field(default_factory=list)
    evidence_anchor_refs: list[str] = Field(default_factory=list)
    state: MechanismState
    qualification_refs: list[str] = Field(default_factory=list)
    unresolved_refs: list[str] = Field(default_factory=list)
    mechanism_is_hypothesis_not_validated_pathway: Literal[True] = True

    @model_validator(mode="after")
    def validate_mechanism(self):
        if len(self.mediator_keys) != len(set(self.mediator_keys)):
            raise ValueError("mediator_keys must be unique")
        if len(self.supporting_signal_refs) != len(set(self.supporting_signal_refs)):
            raise ValueError("supporting_signal_refs must be unique")
        if len(self.evidence_anchor_refs) != len(set(self.evidence_anchor_refs)):
            raise ValueError("evidence_anchor_refs must be unique")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class InterventionContext(BaseModel):
    intervention_context_id: str = Field(min_length=3, max_length=500)
    intervention_key: str = Field(min_length=3, max_length=500)
    outcome_key: str = Field(min_length=3, max_length=500)
    source_signal_refs: list[str] = Field(default_factory=list)
    evidence_anchor_refs: list[str] = Field(default_factory=list)
    design_ref: str | None = Field(default=None, max_length=500)
    comparator_ref: str | None = Field(default=None, max_length=500)
    evidence_class: CausalEvidenceClass
    sufficient_for_causal_identification: Literal[False] = False
    qualification_refs: list[str] = Field(default_factory=list)
    unresolved_refs: list[str] = Field(default_factory=list)

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class CounterfactualContext(BaseModel):
    counterfactual_id: str = Field(min_length=3, max_length=500)
    intervention_key: str = Field(min_length=3, max_length=500)
    outcome_key: str = Field(min_length=3, max_length=500)
    observed_world_ref: str = Field(min_length=3, max_length=500)
    counterfactual_question: str = Field(min_length=3, max_length=2000)
    estimate_available: Literal[False] = False
    identification_strategy_ref: str | None = Field(default=None, max_length=500)
    qualification_refs: list[str] = Field(default_factory=list)
    unresolved_refs: list[str] = Field(default_factory=list)
    counterfactual_question_is_not_effect_estimate: Literal[True] = True

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class CausalAssessment(BaseModel):
    assessment_id: str = Field(min_length=3, max_length=500)
    subject_signal_refs: list[str] = Field(min_length=1)
    mechanism_refs: list[str] = Field(default_factory=list)
    intervention_context_refs: list[str] = Field(default_factory=list)
    counterfactual_context_refs: list[str] = Field(default_factory=list)
    evidence_context_assessment_refs: list[str] = Field(default_factory=list)
    relation_kind: CausalRelationKind
    evidence_class: CausalEvidenceClass
    rationale: str = Field(min_length=3, max_length=4000)
    qualification_refs: list[str] = Field(default_factory=list)
    unresolved_refs: list[str] = Field(default_factory=list)
    state: CausalReviewState = CausalReviewState.reviewed
    reviewer_ref: str | None = Field(default=None, max_length=500)
    establishes_causal_truth: Literal[False] = False

    @model_validator(mode="after")
    def validate_assessment(self):
        if self.state in {CausalReviewState.reviewed, CausalReviewState.accepted, CausalReviewState.disputed} and not self.reviewer_ref:
            raise ValueError("reviewed/accepted/disputed assessment requires reviewer_ref")
        for values, label in [
            (self.subject_signal_refs, "subject_signal_refs"),
            (self.mechanism_refs, "mechanism_refs"),
            (self.intervention_context_refs, "intervention_context_refs"),
            (self.counterfactual_context_refs, "counterfactual_context_refs"),
            (self.evidence_context_assessment_refs, "evidence_context_assessment_refs"),
            (self.qualification_refs, "qualification_refs"),
            (self.unresolved_refs, "unresolved_refs"),
        ]:
            if len(values) != len(set(values)):
                raise ValueError(f"{label} must be unique")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class CausalProvenanceRecord(BaseModel):
    provenance_id: str = Field(min_length=3, max_length=500)
    predecessor_evidence_context_fingerprint_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    subject_refs: list[str] = Field(min_length=1)
    method: str = Field(min_length=3, max_length=2000)
    replayable: Literal[True] = True

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class CausalSemanticSnapshot(BaseModel):
    snapshot_id: str = Field(min_length=3, max_length=500)
    predecessor_evidence_context_fingerprint_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    signal_fingerprints: dict[str, str]
    mechanism_fingerprints: dict[str, str]
    intervention_fingerprints: dict[str, str]
    counterfactual_fingerprints: dict[str, str]
    assessment_fingerprints: dict[str, str]
    deterministic_causal_context_fingerprint_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    supersedable: Literal[True] = True
    snapshot_is_not_causal_certification: Literal[True] = True

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class ContextualCausalLanguageMechanismBundle(BaseModel):
    release: Literal["4.15.0"] = "4.15.0"
    contract: Literal[CONTRACT_VERSION] = CONTRACT_VERSION
    predecessor_contract: Literal[PREDECESSOR_CONTRACT] = PREDECESSOR_CONTRACT
    policy: CausalPolicy
    predecessor_evidence_context: EvidenceContextIntegrationBundle
    signals: list[CausalLanguageSignal] = Field(min_length=1)
    mechanisms: list[MechanismHypothesis] = Field(min_length=1)
    intervention_contexts: list[InterventionContext] = Field(min_length=1)
    counterfactual_contexts: list[CounterfactualContext] = Field(min_length=1)
    assessments: list[CausalAssessment] = Field(min_length=1)
    provenance_records: list[CausalProvenanceRecord] = Field(min_length=1)
    snapshots: list[CausalSemanticSnapshot] = Field(min_length=1)
    database_migration: Literal["none"] = "none"

    @model_validator(mode="after")
    def validate_bundle(self):
        predecessor = self.predecessor_evidence_context
        if predecessor.release != "4.14.0" or predecessor.contract != PREDECESSOR_CONTRACT:
            raise ValueError("v4.15 must preserve governed v4.14 evidence-context predecessor")

        def unique(values: list[str], label: str):
            if len(values) != len(set(values)):
                raise ValueError(f"{label} must be unique")

        unique([x.signal_id for x in self.signals], "signal ids")
        unique([x.mechanism_id for x in self.mechanisms], "mechanism ids")
        unique([x.intervention_context_id for x in self.intervention_contexts], "intervention context ids")
        unique([x.counterfactual_id for x in self.counterfactual_contexts], "counterfactual ids")
        unique([x.assessment_id for x in self.assessments], "assessment ids")
        unique([x.provenance_id for x in self.provenance_records], "provenance ids")
        unique([x.snapshot_id for x in self.snapshots], "snapshot ids")

        claims = {x.claim_id: x for x in predecessor.predecessor_claim_comparison.claims}
        anchors = {x.anchor_id: x for x in predecessor.evidence_anchors}
        evidence_assessments = {x.assessment_id: x for x in predecessor.assessments}
        signals = {x.signal_id: x for x in self.signals}
        mechanisms = {x.mechanism_id: x for x in self.mechanisms}
        interventions = {x.intervention_context_id: x for x in self.intervention_contexts}
        counterfactuals = {x.counterfactual_id: x for x in self.counterfactual_contexts}

        for signal in self.signals:
            if signal.claim_ref not in claims:
                raise ValueError("causal signal claim_ref must resolve to v4.14 predecessor claim")
            if signal.evidence_anchor_ref not in anchors:
                raise ValueError("causal signal evidence_anchor_ref must resolve")
            if anchors[signal.evidence_anchor_ref].claim_ref != signal.claim_ref:
                raise ValueError("causal signal must preserve claim/evidence anchor binding")
            if anchors[signal.evidence_anchor_ref].independence_state == EvidenceIndependenceState.same_source_derived:
                if "translation-derived" not in signal.qualification_refs:
                    raise ValueError("derived-language signal must preserve translation-derived qualification")

        for mechanism in self.mechanisms:
            if not set(mechanism.supporting_signal_refs).issubset(signals):
                raise ValueError("mechanism signal refs must resolve")
            if not set(mechanism.evidence_anchor_refs).issubset(anchors):
                raise ValueError("mechanism evidence refs must resolve")
            if mechanism.state == MechanismState.supported and not mechanism.evidence_anchor_refs:
                raise ValueError("supported mechanism requires evidence refs")

        for intervention in self.intervention_contexts:
            if not set(intervention.source_signal_refs).issubset(signals):
                raise ValueError("intervention signal refs must resolve")
            if not set(intervention.evidence_anchor_refs).issubset(anchors):
                raise ValueError("intervention evidence refs must resolve")
            if intervention.evidence_class == CausalEvidenceClass.intervention_supported and not intervention.design_ref:
                raise ValueError("intervention-supported context requires governed design_ref")

        for cf in self.counterfactual_contexts:
            if cf.estimate_available is False and cf.identification_strategy_ref is not None:
                raise ValueError("reference counterfactual without estimate cannot claim identification strategy")

        for assessment in self.assessments:
            if not set(assessment.subject_signal_refs).issubset(signals):
                raise ValueError("assessment signal refs must resolve")
            if not set(assessment.mechanism_refs).issubset(mechanisms):
                raise ValueError("assessment mechanism refs must resolve")
            if not set(assessment.intervention_context_refs).issubset(interventions):
                raise ValueError("assessment intervention refs must resolve")
            if not set(assessment.counterfactual_context_refs).issubset(counterfactuals):
                raise ValueError("assessment counterfactual refs must resolve")
            if not set(assessment.evidence_context_assessment_refs).issubset(evidence_assessments):
                raise ValueError("assessment evidence-context refs must resolve")
            if assessment.evidence_class == CausalEvidenceClass.intervention_supported:
                if not assessment.intervention_context_refs:
                    raise ValueError("intervention-supported assessment requires intervention context")
            if assessment.relation_kind == CausalRelationKind.causes and assessment.evidence_class == CausalEvidenceClass.linguistic_only:
                raise ValueError("linguistic-only assessment cannot promote causal wording to established causes relation")

        pred_fp = predecessor.fingerprint()
        all_subjects = set(signals) | set(mechanisms) | set(interventions) | set(counterfactuals) | {x.assessment_id for x in self.assessments}
        for p in self.provenance_records:
            if p.predecessor_evidence_context_fingerprint_sha256 != pred_fp:
                raise ValueError("provenance predecessor fingerprint must match v4.14")
            if not set(p.subject_refs).issubset(all_subjects):
                raise ValueError("provenance refs must resolve")

        expected_signals = {x.signal_id: x.fingerprint() for x in self.signals}
        expected_mechanisms = {x.mechanism_id: x.fingerprint() for x in self.mechanisms}
        expected_interventions = {x.intervention_context_id: x.fingerprint() for x in self.intervention_contexts}
        expected_counterfactuals = {x.counterfactual_id: x.fingerprint() for x in self.counterfactual_contexts}
        expected_assessments = {x.assessment_id: x.fingerprint() for x in self.assessments}
        for s in self.snapshots:
            if s.predecessor_evidence_context_fingerprint_sha256 != pred_fp:
                raise ValueError("snapshot predecessor fingerprint must match v4.14")
            if s.signal_fingerprints != expected_signals or s.mechanism_fingerprints != expected_mechanisms:
                raise ValueError("snapshot signal/mechanism fingerprints must be exact")
            if s.intervention_fingerprints != expected_interventions or s.counterfactual_fingerprints != expected_counterfactuals:
                raise ValueError("snapshot intervention/counterfactual fingerprints must be exact")
            if s.assessment_fingerprints != expected_assessments:
                raise ValueError("snapshot assessment fingerprints must be exact")
            material = {
                "predecessor": pred_fp,
                "signals": expected_signals,
                "mechanisms": expected_mechanisms,
                "interventions": expected_interventions,
                "counterfactuals": expected_counterfactuals,
                "assessments": expected_assessments,
            }
            if s.deterministic_causal_context_fingerprint_sha256 != canonical_sha256(material):
                raise ValueError("snapshot deterministic causal-context fingerprint mismatch")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


@lru_cache(maxsize=1)
def reference_contextual_causal_language_mechanism_bundle() -> ContextualCausalLanguageMechanismBundle:
    predecessor = reference_evidence_context_integration_bundle()
    claims = {x.claim_id: x for x in predecessor.predecessor_claim_comparison.claims}
    anchors = {x.claim_ref: x for x in predecessor.evidence_anchors}

    specs = [
        ("claim:v45:measure-no-emissions-reduction", CausalLanguageKind.causal_denial, CausalRelationKind.no_direct_effect, "policy-measure:reference", "emissions:total-unspecified"),
        ("claim:v46:measure-may-reduce-emissions", CausalLanguageKind.causal_possibility, CausalRelationKind.reduces, "policy-measure:reference", "emissions:total-unspecified"),
        ("claim:v413:audit-reduced-emissions", CausalLanguageKind.causal_assertion, CausalRelationKind.reduces, "policy-measure:reference", "emissions:total-unspecified"),
        ("claim:v413:review-no-direct-emissions-reduction", CausalLanguageKind.causal_denial, CausalRelationKind.no_direct_effect, "policy-measure:reference", "emissions:direct-only"),
        ("claim:v45:proposal-may-lower-costs", CausalLanguageKind.causal_possibility, CausalRelationKind.reduces, "policy-proposal:reference", "costs:unspecified"),
        ("claim:v48:zh-proposal-may-lower-costs", CausalLanguageKind.causal_possibility, CausalRelationKind.reduces, "policy-proposal:reference", "costs:unspecified"),
        ("claim:v48:en-proposal-may-reduce-costs", CausalLanguageKind.causal_possibility, CausalRelationKind.reduces, "policy-proposal:reference", "costs:unspecified"),
    ]
    signals: list[CausalLanguageSignal] = []
    for idx, (claim_ref, kind, relation, cause, effect) in enumerate(specs, 1):
        c = claims[claim_ref]
        a = anchors[claim_ref]
        quals = list(c.qualification_refs)
        if a.independence_state == EvidenceIndependenceState.same_source_derived:
            quals = list(dict.fromkeys(quals + ["translation-derived"]))
        signals.append(CausalLanguageSignal(
            signal_id=f"causal-signal:reference:{idx}",
            claim_ref=claim_ref,
            evidence_anchor_ref=a.anchor_id,
            source_text=c.surface_text,
            language_tag=c.language_tag,
            language_kind=kind,
            relation_kind=relation,
            cause_key=cause,
            effect_key=effect,
            polarity=c.polarity.value,
            modality=c.modality.value,
            attribution_ref=c.attribution_ref,
            temporal_scope_ref=c.temporal_scope_ref,
            spatial_scope_ref=c.spatial_scope_ref,
            qualification_refs=quals,
            unresolved_refs=c.unresolved_refs,
        ))
    by_claim={s.claim_ref:s for s in signals}

    mechanisms = [
        MechanismHypothesis(
            mechanism_id="mechanism:measure-to-emissions:reference",
            label="Policy measure may alter operational activity and thereby change emissions.",
            input_key="policy-measure:reference",
            mediator_keys=["operational-activity:unspecified"],
            output_key="emissions:total-unspecified",
            supporting_signal_refs=[by_claim["claim:v46:measure-may-reduce-emissions"].signal_id, by_claim["claim:v413:audit-reduced-emissions"].signal_id],
            evidence_anchor_refs=[anchors["claim:v46:measure-may-reduce-emissions"].anchor_id, anchors["claim:v413:audit-reduced-emissions"].anchor_id],
            state=MechanismState.proposed,
            qualification_refs=["mechanism-mediator-not-observed-in-reference-fixture"],
            unresolved_refs=["causal-identification:not-established"],
        ),
        MechanismHypothesis(
            mechanism_id="mechanism:proposal-to-costs:reference",
            label="Policy proposal may alter resource use and thereby change costs.",
            input_key="policy-proposal:reference",
            mediator_keys=["resource-use:unspecified"],
            output_key="costs:unspecified",
            supporting_signal_refs=[by_claim["claim:v45:proposal-may-lower-costs"].signal_id, by_claim["claim:v48:zh-proposal-may-lower-costs"].signal_id, by_claim["claim:v48:en-proposal-may-reduce-costs"].signal_id],
            evidence_anchor_refs=[anchors["claim:v45:proposal-may-lower-costs"].anchor_id, anchors["claim:v48:zh-proposal-may-lower-costs"].anchor_id, anchors["claim:v48:en-proposal-may-reduce-costs"].anchor_id],
            state=MechanismState.proposed,
            qualification_refs=["mechanism-mediator-not-observed-in-reference-fixture", "translation-lineage-preserved"],
            unresolved_refs=["causal-identification:not-established"],
        ),
    ]

    interventions = [
        InterventionContext(
            intervention_context_id="intervention-context:measure-emissions:reference",
            intervention_key="policy-measure:reference",
            outcome_key="emissions:total-unspecified",
            source_signal_refs=[by_claim["claim:v413:audit-reduced-emissions"].signal_id, by_claim["claim:v45:measure-no-emissions-reduction"].signal_id],
            evidence_anchor_refs=[anchors["claim:v413:audit-reduced-emissions"].anchor_id, anchors["claim:v45:measure-no-emissions-reduction"].anchor_id],
            evidence_class=CausalEvidenceClass.evidence_linked,
            qualification_refs=["no-randomization-or-quasi-experimental-design-bound-in-reference-fixture"],
            unresolved_refs=["causal-identification:not-established", "strict-evidence-conflict:emissions-effect"],
        )
    ]

    counterfactuals = [
        CounterfactualContext(
            counterfactual_id="counterfactual:measure-emissions:reference",
            intervention_key="policy-measure:reference",
            outcome_key="emissions:total-unspecified",
            observed_world_ref=interventions[0].intervention_context_id,
            counterfactual_question="What would emissions have been during the same evaluation period if the reference policy measure had not been implemented?",
            qualification_refs=["counterfactual-not-observed", "no-identification-strategy-bound"],
            unresolved_refs=["counterfactual-effect:not-estimated"],
        ),
        CounterfactualContext(
            counterfactual_id="counterfactual:proposal-costs:reference",
            intervention_key="policy-proposal:reference",
            outcome_key="costs:unspecified",
            observed_world_ref="claim:v48:zh-proposal-may-lower-costs",
            counterfactual_question="What would costs have been under an otherwise comparable condition without the reference proposal?",
            qualification_refs=["counterfactual-not-observed", "translation-lineage-preserved"],
            unresolved_refs=["counterfactual-effect:not-estimated"],
        ),
    ]

    evidence_by_relation={x.claim_relation_assessment_ref:x.assessment_id for x in predecessor.assessments}
    relation_assessments=predecessor.predecessor_claim_comparison.assessments
    strict_rel=next(x for x in relation_assessments if x.relation_kind.value=="contradiction")
    apparent_rel=next(x for x in relation_assessments if x.relation_kind.value=="apparent-contradiction")

    assessments = [
        CausalAssessment(
            assessment_id="causal-assessment:emissions-effect-conflict",
            subject_signal_refs=[by_claim["claim:v45:measure-no-emissions-reduction"].signal_id, by_claim["claim:v413:audit-reduced-emissions"].signal_id],
            mechanism_refs=["mechanism:measure-to-emissions:reference"],
            intervention_context_refs=[interventions[0].intervention_context_id],
            counterfactual_context_refs=[counterfactuals[0].counterfactual_id],
            evidence_context_assessment_refs=[evidence_by_relation[strict_rel.assessment_id]],
            relation_kind=CausalRelationKind.unresolved,
            evidence_class=CausalEvidenceClass.unresolved,
            rationale="The evidence-context layer preserves a strict contradiction about the emissions effect. Causal wording exists on both sides, but no governed identification design or counterfactual estimate resolves the causal effect.",
            qualification_refs=["strict-contradiction-preserved", "no-identification-design"],
            unresolved_refs=["causal-effect:measure-to-emissions"],
            state=CausalReviewState.unresolved,
        ),
        CausalAssessment(
            assessment_id="causal-assessment:agency-possible-emissions-effect",
            subject_signal_refs=[by_claim["claim:v46:measure-may-reduce-emissions"].signal_id],
            mechanism_refs=["mechanism:measure-to-emissions:reference"],
            evidence_context_assessment_refs=[evidence_by_relation[apparent_rel.assessment_id]],
            relation_kind=CausalRelationKind.reduces,
            evidence_class=CausalEvidenceClass.linguistic_only,
            rationale="The agency statement expresses a possible causal effect. Modality and attribution are preserved, and the interpretation does not establish that the measure actually reduced emissions.",
            qualification_refs=["modal-possibility", "attributed-claim"],
            unresolved_refs=["causal-effect:measure-to-emissions"],
            reviewer_ref="reviewer:causal-context-reference",
        ),
        CausalAssessment(
            assessment_id="causal-assessment:direct-emissions-effect",
            subject_signal_refs=[by_claim["claim:v413:review-no-direct-emissions-reduction"].signal_id],
            relation_kind=CausalRelationKind.no_direct_effect,
            evidence_class=CausalEvidenceClass.evidence_linked,
            rationale="The review states no direct emissions reduction for the reference period. The narrower direct-emissions scope is preserved and does not settle total or indirect effects.",
            qualification_refs=["direct-emissions-only"],
            unresolved_refs=["indirect-emissions:not-assessed"],
            reviewer_ref="reviewer:causal-context-reference",
        ),
        CausalAssessment(
            assessment_id="causal-assessment:proposal-cost-effect",
            subject_signal_refs=[by_claim["claim:v45:proposal-may-lower-costs"].signal_id, by_claim["claim:v48:zh-proposal-may-lower-costs"].signal_id, by_claim["claim:v48:en-proposal-may-reduce-costs"].signal_id],
            mechanism_refs=["mechanism:proposal-to-costs:reference"],
            counterfactual_context_refs=[counterfactuals[1].counterfactual_id],
            relation_kind=CausalRelationKind.reduces,
            evidence_class=CausalEvidenceClass.linguistic_only,
            rationale="Multiple language representations express a possible cost-reduction relation, but the English representation is derived from the Chinese source and does not add independent causal evidence. The proposed mechanism and counterfactual remain unvalidated.",
            qualification_refs=["modal-possibility", "translation-derived-not-independent"],
            unresolved_refs=["causal-effect:proposal-to-costs", "mechanism:resource-use:not-observed"],
            reviewer_ref="reviewer:causal-context-reference",
        ),
    ]

    subjects=[x.signal_id for x in signals]+[x.mechanism_id for x in mechanisms]+[x.intervention_context_id for x in interventions]+[x.counterfactual_id for x in counterfactuals]+[x.assessment_id for x in assessments]
    provenance=CausalProvenanceRecord(
        provenance_id="causal-provenance:reference",
        predecessor_evidence_context_fingerprint_sha256=predecessor.fingerprint(),
        subject_refs=subjects,
        method="governed contextual causal-language interpretation over v4.14 evidence-context objects; preserves modality, attribution, scope, translation lineage, contradiction, and non-identification boundaries",
    )
    material={
        "predecessor": predecessor.fingerprint(),
        "signals": {x.signal_id:x.fingerprint() for x in signals},
        "mechanisms": {x.mechanism_id:x.fingerprint() for x in mechanisms},
        "interventions": {x.intervention_context_id:x.fingerprint() for x in interventions},
        "counterfactuals": {x.counterfactual_id:x.fingerprint() for x in counterfactuals},
        "assessments": {x.assessment_id:x.fingerprint() for x in assessments},
    }
    snapshot=CausalSemanticSnapshot(
        snapshot_id="causal-semantic-snapshot:reference:v1",
        predecessor_evidence_context_fingerprint_sha256=predecessor.fingerprint(),
        signal_fingerprints=material["signals"],
        mechanism_fingerprints=material["mechanisms"],
        intervention_fingerprints=material["interventions"],
        counterfactual_fingerprints=material["counterfactuals"],
        assessment_fingerprints=material["assessments"],
        deterministic_causal_context_fingerprint_sha256=canonical_sha256(material),
    )
    return ContextualCausalLanguageMechanismBundle(
        policy=CausalPolicy(policy_id="causal-context-policy:v1"),
        predecessor_evidence_context=predecessor,
        signals=signals,
        mechanisms=mechanisms,
        intervention_contexts=interventions,
        counterfactual_contexts=counterfactuals,
        assessments=assessments,
        provenance_records=[provenance],
        snapshots=[snapshot],
    )


def contract_document() -> dict:
    b=reference_contextual_causal_language_mechanism_bundle()
    return {
        "ok": True,
        "release": CORE_RELEASE,
        "contract": CONTRACT_VERSION,
        "predecessor_contract": PREDECESSOR_CONTRACT,
        "identity": {"product":"Sustainable Catalyst Platform Core","build":"Contextual Causal Language & Mechanism Intelligence","major_api":"v4"},
        "principles": {
            "causal_language_is_distinct_from_causal_identification": True,
            "temporal_precedence_is_not_causality": True,
            "association_is_not_causality": True,
            "mechanism_plausibility_is_not_mechanism_validation": True,
            "intervention_language_is_not_experimental_evidence": True,
            "counterfactual_language_is_not_counterfactual_estimate": True,
            "source_attribution_and_modality_must_be_preserved": True,
            "translation_lineage_must_be_preserved": True,
        },
        "boundaries": {
            "causal_score_establishes_truth": False,
            "causal_wording_establishes_causality": False,
            "mechanism_count_establishes_causality": False,
            "evidence_count_establishes_causality": False,
            "automatic_causal_graph_mutation_performed": False,
            "evidence_graph_mutation_performed": False,
            "knowledge_graph_mutation_performed": False,
            "identity_graph_mutation_performed": False,
        },
        "roadmap_integration": {
            "extends_v4140_evidence_context_integration": True,
            "prepares_v4160_narrative_framing_perspective_intelligence": True,
            "prepares_v4170_cross_source_semantic_reconciliation": True,
            "prepares_v4180_contextual_hypothesis_competing_explanations": True,
            "prepares_v4190_semantic_synthesis_research_answer": True,
            "prepares_v4200_unified_contextual_reasoning_runtime": True,
        },
        "reference": {
            "predecessor_release": b.predecessor_evidence_context.release,
            "predecessor_fingerprint_sha256": b.predecessor_evidence_context.fingerprint(),
            "causal_language_signals": len(b.signals),
            "mechanism_hypotheses": len(b.mechanisms),
            "intervention_contexts": len(b.intervention_contexts),
            "counterfactual_contexts": len(b.counterfactual_contexts),
            "causal_assessments": len(b.assessments),
            "unresolved_causal_assessments": sum(x.state == CausalReviewState.unresolved for x in b.assessments),
            "intervention_supported_assessments": sum(x.evidence_class == CausalEvidenceClass.intervention_supported for x in b.assessments),
            "snapshots": len(b.snapshots),
            "bundle_fingerprint_sha256": b.fingerprint(),
        },
        "database_migration": "none",
    }
