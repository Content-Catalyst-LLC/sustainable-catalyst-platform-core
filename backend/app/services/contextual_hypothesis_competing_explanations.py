from __future__ import annotations

from enum import Enum
from functools import lru_cache
from typing import Literal

from pydantic import BaseModel, Field, model_validator

from .computational_runtime_objects import canonical_sha256
from .cross_source_semantic_reconciliation import (
    CrossSourceSemanticReconciliationBundle,
    ReconciliationConflictKind,
    ReconciliationReviewState,
    reference_cross_source_semantic_reconciliation_bundle,
)

CORE_RELEASE = "4.18.0"
CONTRACT_VERSION = "sc.core.contextual-hypothesis-competing-explanation-objects.v1"
PREDECESSOR_CONTRACT = "sc.core.cross-source-semantic-reconciliation-engine.v1"


class HypothesisKind(str, Enum):
    measurement_scope = "measurement-scope"
    temporal_change = "temporal-change"
    source_process = "source-process"
    causal_mechanism = "causal-mechanism"
    actor_identity = "actor-identity"
    terminology_interpretation = "terminology-interpretation"
    source_independence = "source-independence"
    composite = "composite"


class HypothesisReviewState(str, Enum):
    candidate = "candidate"
    reviewed = "reviewed"
    retained = "retained"
    constrained = "constrained"
    rejected = "rejected"
    unresolved = "unresolved"


class EvidencePositionKind(str, Enum):
    supports = "supports"
    challenges = "challenges"
    qualifies = "qualifies"
    contextualizes = "contextualizes"
    unresolved = "unresolved"
    non_independent = "non-independent"


class ExplanationRelation(str, Enum):
    competing = "competing"
    complementary = "complementary"
    nested = "nested"
    incompatible = "incompatible"
    underdetermined = "underdetermined"


class DiscriminatingDimension(str, Enum):
    scope = "scope"
    temporal = "temporal"
    measurement = "measurement"
    causal = "causal"
    identity = "identity"
    terminology = "terminology"
    translation_lineage = "translation-lineage"
    source_independence = "source-independence"


class ContextualHypothesisPolicy(BaseModel):
    policy_id: str = Field(min_length=3, max_length=500)
    predecessor_reconciliation_remains_immutable: Literal[True] = True
    hypotheses_are_explanatory_objects_not_truth_claims: Literal[True] = True
    competing_explanations_may_coexist: Literal[True] = True
    evidence_positions_preserve_support_challenge_and_qualification: Literal[True] = True
    unresolved_assumptions_must_remain_explicit: Literal[True] = True
    source_independence_constraints_must_carry_forward: Literal[True] = True
    original_language_authority_must_carry_forward: Literal[True] = True
    derived_translation_cannot_count_as_independent_support: Literal[True] = True
    causal_identification_status_must_carry_forward: Literal[True] = True
    identity_uncertainty_must_carry_forward: Literal[True] = True
    explanatory_fit_score_establishes_truth: Literal[False] = False
    explanatory_fit_score_is_probability: Literal[False] = False
    support_count_establishes_truth: Literal[False] = False
    challenge_count_establishes_falsity: Literal[False] = False
    retained_hypothesis_is_selected_winner: Literal[False] = False
    automatic_hypothesis_promotion_authorized: Literal[False] = False
    automatic_context_graph_mutation_authorized: Literal[False] = False
    automatic_evidence_graph_mutation_authorized: Literal[False] = False
    automatic_knowledge_graph_mutation_authorized: Literal[False] = False
    automatic_identity_graph_mutation_authorized: Literal[False] = False


class ContextualHypothesis(BaseModel):
    hypothesis_id: str = Field(min_length=3, max_length=500)
    kind: HypothesisKind
    target_cluster_ref: str = Field(min_length=3, max_length=500)
    title: str = Field(min_length=3, max_length=1500)
    proposition: str = Field(min_length=3, max_length=5000)
    source_anchor_refs: list[str] = Field(min_length=1)
    conflict_refs: list[str] = Field(default_factory=list)
    decision_refs: list[str] = Field(default_factory=list)
    mechanism_refs: list[str] = Field(default_factory=list)
    assumption_refs: list[str] = Field(default_factory=list)
    qualification_refs: list[str] = Field(default_factory=list)
    unresolved_refs: list[str] = Field(default_factory=list)
    explanatory_fit_score: float = Field(ge=0.0, le=1.0)
    state: HypothesisReviewState
    reviewer_ref: str | None = Field(default=None, max_length=500)
    hypothesis_is_explanation_candidate_not_truth: Literal[True] = True
    fit_score_is_not_probability_or_truth: Literal[True] = True

    @model_validator(mode="after")
    def validate_hypothesis(self):
        for values, label in [
            (self.source_anchor_refs, "source_anchor_refs"),
            (self.conflict_refs, "conflict_refs"),
            (self.decision_refs, "decision_refs"),
            (self.mechanism_refs, "mechanism_refs"),
            (self.assumption_refs, "assumption_refs"),
            (self.qualification_refs, "qualification_refs"),
            (self.unresolved_refs, "unresolved_refs"),
        ]:
            if len(values) != len(set(values)):
                raise ValueError(f"{label} must be unique")
        if self.state in {HypothesisReviewState.reviewed, HypothesisReviewState.retained, HypothesisReviewState.constrained, HypothesisReviewState.rejected, HypothesisReviewState.unresolved} and not self.reviewer_ref:
            raise ValueError("reviewed hypothesis state requires reviewer_ref")
        if self.kind == HypothesisKind.causal_mechanism and not self.mechanism_refs:
            raise ValueError("causal-mechanism hypothesis requires mechanism_refs")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class HypothesisEvidencePosition(BaseModel):
    position_id: str = Field(min_length=3, max_length=500)
    hypothesis_ref: str = Field(min_length=3, max_length=500)
    position: EvidencePositionKind
    anchor_refs: list[str] = Field(default_factory=list)
    conflict_refs: list[str] = Field(default_factory=list)
    decision_refs: list[str] = Field(default_factory=list)
    rationale: str = Field(min_length=3, max_length=5000)
    qualification_refs: list[str] = Field(default_factory=list)
    unresolved_refs: list[str] = Field(default_factory=list)
    counts_as_independent_support: bool = False
    evidence_position_is_not_truth_update: Literal[True] = True
    evidence_position_does_not_mutate_upstream_evidence: Literal[True] = True

    @model_validator(mode="after")
    def validate_position(self):
        for values, label in [
            (self.anchor_refs, "anchor_refs"),
            (self.conflict_refs, "conflict_refs"),
            (self.decision_refs, "decision_refs"),
            (self.qualification_refs, "qualification_refs"),
            (self.unresolved_refs, "unresolved_refs"),
        ]:
            if len(values) != len(set(values)):
                raise ValueError(f"{label} must be unique")
        if self.position == EvidencePositionKind.supports and not (self.anchor_refs or self.conflict_refs or self.decision_refs):
            raise ValueError("support position requires governed predecessor references")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class CompetingExplanationComparison(BaseModel):
    comparison_id: str = Field(min_length=3, max_length=500)
    left_hypothesis_ref: str = Field(min_length=3, max_length=500)
    right_hypothesis_ref: str = Field(min_length=3, max_length=500)
    relation: ExplanationRelation
    discriminating_dimensions: list[DiscriminatingDimension] = Field(min_length=1)
    discriminating_questions: list[str] = Field(min_length=1)
    evidence_needed: list[str] = Field(min_length=1)
    qualification_refs: list[str] = Field(default_factory=list)
    unresolved_refs: list[str] = Field(default_factory=list)
    comparison_does_not_select_winner: Literal[True] = True
    comparison_does_not_establish_truth: Literal[True] = True

    @model_validator(mode="after")
    def validate_comparison(self):
        if self.left_hypothesis_ref == self.right_hypothesis_ref:
            raise ValueError("comparison requires distinct hypotheses")
        if len(self.discriminating_dimensions) != len(set(self.discriminating_dimensions)):
            raise ValueError("discriminating_dimensions must be unique")
        for values, label in [
            (self.discriminating_questions, "discriminating_questions"),
            (self.evidence_needed, "evidence_needed"),
            (self.qualification_refs, "qualification_refs"),
            (self.unresolved_refs, "unresolved_refs"),
        ]:
            if len(values) != len(set(values)):
                raise ValueError(f"{label} must be unique")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class CompetingExplanationSet(BaseModel):
    explanation_set_id: str = Field(min_length=3, max_length=500)
    target_cluster_ref: str = Field(min_length=3, max_length=500)
    label: str = Field(min_length=3, max_length=1500)
    hypothesis_refs: list[str] = Field(min_length=2)
    evidence_position_refs: list[str] = Field(min_length=2)
    comparison_refs: list[str] = Field(min_length=1)
    retained_hypothesis_refs: list[str] = Field(min_length=1)
    rejected_hypothesis_refs: list[str] = Field(default_factory=list)
    unresolved_questions: list[str] = Field(min_length=1)
    qualification_refs: list[str] = Field(default_factory=list)
    set_establishes_winner: Literal[False] = False
    set_establishes_truth: Literal[False] = False

    @model_validator(mode="after")
    def validate_set(self):
        for values, label in [
            (self.hypothesis_refs, "hypothesis_refs"),
            (self.evidence_position_refs, "evidence_position_refs"),
            (self.comparison_refs, "comparison_refs"),
            (self.retained_hypothesis_refs, "retained_hypothesis_refs"),
            (self.rejected_hypothesis_refs, "rejected_hypothesis_refs"),
            (self.unresolved_questions, "unresolved_questions"),
            (self.qualification_refs, "qualification_refs"),
        ]:
            if len(values) != len(set(values)):
                raise ValueError(f"{label} must be unique")
        if not set(self.retained_hypothesis_refs).issubset(self.hypothesis_refs):
            raise ValueError("retained hypotheses must be members")
        if not set(self.rejected_hypothesis_refs).issubset(self.hypothesis_refs):
            raise ValueError("rejected hypotheses must be members")
        if set(self.retained_hypothesis_refs) & set(self.rejected_hypothesis_refs):
            raise ValueError("hypothesis cannot be both retained and rejected")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class ContextualHypothesisProvenanceRecord(BaseModel):
    provenance_id: str = Field(min_length=3, max_length=500)
    predecessor_reconciliation_fingerprint_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    subject_refs: list[str] = Field(min_length=1)
    method: str = Field(min_length=3, max_length=5000)
    provenance_is_not_hypothesis_truth_or_probability: Literal[True] = True

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class ContextualHypothesisSnapshot(BaseModel):
    snapshot_id: str = Field(min_length=3, max_length=500)
    predecessor_reconciliation_fingerprint_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    hypothesis_fingerprints: dict[str, str]
    evidence_position_fingerprints: dict[str, str]
    comparison_fingerprints: dict[str, str]
    explanation_set_fingerprints: dict[str, str]
    deterministic_hypothesis_context_fingerprint_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    supersedable: Literal[True] = True
    snapshot_is_not_truth_selection_or_probability_certification: Literal[True] = True

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class ContextualHypothesisCompetingExplanationBundle(BaseModel):
    release: Literal["4.18.0"] = "4.18.0"
    contract: Literal[CONTRACT_VERSION] = CONTRACT_VERSION
    predecessor_contract: Literal[PREDECESSOR_CONTRACT] = PREDECESSOR_CONTRACT
    policy: ContextualHypothesisPolicy
    predecessor_reconciliation: CrossSourceSemanticReconciliationBundle
    hypotheses: list[ContextualHypothesis] = Field(min_length=2)
    evidence_positions: list[HypothesisEvidencePosition] = Field(min_length=2)
    comparisons: list[CompetingExplanationComparison] = Field(min_length=1)
    explanation_sets: list[CompetingExplanationSet] = Field(min_length=1)
    provenance_records: list[ContextualHypothesisProvenanceRecord] = Field(min_length=1)
    snapshots: list[ContextualHypothesisSnapshot] = Field(min_length=1)
    database_migration: Literal["none"] = "none"

    @model_validator(mode="after")
    def validate_bundle(self):
        pred = self.predecessor_reconciliation
        if pred.release != "4.17.0" or pred.contract != PREDECESSOR_CONTRACT:
            raise ValueError("v4.18 must preserve governed v4.17 reconciliation predecessor")

        def unique(values: list[str], label: str):
            if len(values) != len(set(values)):
                raise ValueError(f"{label} must be unique")

        unique([x.hypothesis_id for x in self.hypotheses], "hypothesis ids")
        unique([x.position_id for x in self.evidence_positions], "evidence position ids")
        unique([x.comparison_id for x in self.comparisons], "comparison ids")
        unique([x.explanation_set_id for x in self.explanation_sets], "explanation set ids")
        unique([x.provenance_id for x in self.provenance_records], "provenance ids")
        unique([x.snapshot_id for x in self.snapshots], "snapshot ids")

        clusters = {x.cluster_id: x for x in pred.clusters}
        anchors = {x.anchor_id: x for x in pred.anchors}
        conflicts = {x.conflict_id: x for x in pred.conflicts}
        decisions = {x.decision_id: x for x in pred.decisions}
        hypotheses = {x.hypothesis_id: x for x in self.hypotheses}
        positions = {x.position_id: x for x in self.evidence_positions}
        comparisons = {x.comparison_id: x for x in self.comparisons}
        causal = pred.predecessor_framing_context.predecessor_causal_context
        mechanisms = {x.mechanism_id: x for x in causal.mechanisms}

        for h in self.hypotheses:
            if h.target_cluster_ref not in clusters:
                raise ValueError("hypothesis target cluster must resolve")
            if not set(h.source_anchor_refs).issubset(anchors):
                raise ValueError("hypothesis source anchors must resolve")
            if not set(h.conflict_refs).issubset(conflicts):
                raise ValueError("hypothesis conflicts must resolve")
            if not set(h.decision_refs).issubset(decisions):
                raise ValueError("hypothesis decisions must resolve")
            if not set(h.mechanism_refs).issubset(mechanisms):
                raise ValueError("hypothesis mechanism refs must resolve")
            if h.state == HypothesisReviewState.rejected and not h.qualification_refs:
                raise ValueError("rejected hypothesis requires explicit qualification")

        for p in self.evidence_positions:
            if p.hypothesis_ref not in hypotheses:
                raise ValueError("evidence position hypothesis must resolve")
            if not set(p.anchor_refs).issubset(anchors):
                raise ValueError("evidence position anchors must resolve")
            if not set(p.conflict_refs).issubset(conflicts):
                raise ValueError("evidence position conflicts must resolve")
            if not set(p.decision_refs).issubset(decisions):
                raise ValueError("evidence position decisions must resolve")
            if p.counts_as_independent_support:
                if p.position != EvidencePositionKind.supports:
                    raise ValueError("independent support flag requires support position")
                if any(anchors[a].derived_representation for a in p.anchor_refs):
                    raise ValueError("derived representation cannot count as independent support")
            if p.position == EvidencePositionKind.non_independent and p.counts_as_independent_support:
                raise ValueError("non-independent position cannot count as independent support")

        for c in self.comparisons:
            if c.left_hypothesis_ref not in hypotheses or c.right_hypothesis_ref not in hypotheses:
                raise ValueError("comparison hypothesis refs must resolve")
            left = hypotheses[c.left_hypothesis_ref]
            right = hypotheses[c.right_hypothesis_ref]
            if left.target_cluster_ref != right.target_cluster_ref:
                raise ValueError("compared hypotheses must address same target cluster")

        for s in self.explanation_sets:
            if s.target_cluster_ref not in clusters:
                raise ValueError("explanation set target cluster must resolve")
            if not set(s.hypothesis_refs).issubset(hypotheses):
                raise ValueError("explanation set hypotheses must resolve")
            if any(hypotheses[h].target_cluster_ref != s.target_cluster_ref for h in s.hypothesis_refs):
                raise ValueError("explanation set hypotheses must share target cluster")
            if not set(s.evidence_position_refs).issubset(positions):
                raise ValueError("explanation set evidence positions must resolve")
            if any(positions[p].hypothesis_ref not in s.hypothesis_refs for p in s.evidence_position_refs):
                raise ValueError("explanation set evidence positions must belong to member hypotheses")
            if not set(s.comparison_refs).issubset(comparisons):
                raise ValueError("explanation set comparisons must resolve")
            for cref in s.comparison_refs:
                c = comparisons[cref]
                if c.left_hypothesis_ref not in s.hypothesis_refs or c.right_hypothesis_ref not in s.hypothesis_refs:
                    raise ValueError("explanation set comparisons must compare member hypotheses")
            if any(hypotheses[h].state == HypothesisReviewState.rejected for h in s.retained_hypothesis_refs):
                raise ValueError("rejected hypothesis cannot be retained")
            if any(hypotheses[h].state != HypothesisReviewState.rejected for h in s.rejected_hypothesis_refs):
                raise ValueError("rejected_hypothesis_refs must refer to rejected hypotheses")

        all_subjects = set(hypotheses) | set(positions) | set(comparisons) | {x.explanation_set_id for x in self.explanation_sets}
        for p in self.provenance_records:
            if p.predecessor_reconciliation_fingerprint_sha256 != pred.fingerprint():
                raise ValueError("provenance predecessor fingerprint mismatch")
            if not set(p.subject_refs).issubset(all_subjects):
                raise ValueError("provenance subjects must resolve")

        expected_hypotheses = {x.hypothesis_id: x.fingerprint() for x in self.hypotheses}
        expected_positions = {x.position_id: x.fingerprint() for x in self.evidence_positions}
        expected_comparisons = {x.comparison_id: x.fingerprint() for x in self.comparisons}
        expected_sets = {x.explanation_set_id: x.fingerprint() for x in self.explanation_sets}
        expected_material = {
            "predecessor": pred.fingerprint(),
            "hypotheses": expected_hypotheses,
            "evidence_positions": expected_positions,
            "comparisons": expected_comparisons,
            "explanation_sets": expected_sets,
        }
        for s in self.snapshots:
            if s.predecessor_reconciliation_fingerprint_sha256 != pred.fingerprint():
                raise ValueError("snapshot predecessor fingerprint mismatch")
            if s.hypothesis_fingerprints != expected_hypotheses:
                raise ValueError("snapshot hypothesis fingerprints must be exact")
            if s.evidence_position_fingerprints != expected_positions:
                raise ValueError("snapshot evidence position fingerprints must be exact")
            if s.comparison_fingerprints != expected_comparisons:
                raise ValueError("snapshot comparison fingerprints must be exact")
            if s.explanation_set_fingerprints != expected_sets:
                raise ValueError("snapshot explanation-set fingerprints must be exact")
            if s.deterministic_hypothesis_context_fingerprint_sha256 != canonical_sha256(expected_material):
                raise ValueError("snapshot deterministic fingerprint mismatch")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


@lru_cache(maxsize=1)
def reference_contextual_hypothesis_competing_explanation_bundle() -> ContextualHypothesisCompetingExplanationBundle:
    pred = reference_cross_source_semantic_reconciliation_bundle()
    reviewer = "reviewer:contextual-hypothesis-reference"

    hypotheses = [
        ContextualHypothesis(
            hypothesis_id="hypothesis:emissions:scope-difference",
            kind=HypothesisKind.measurement_scope,
            target_cluster_ref="cluster:emissions-policy-measure",
            title="Different emissions scopes explain part of the disagreement",
            proposition="The audit and review can differ because one addresses total or unspecified emissions while the other is limited to direct emissions.",
            source_anchor_refs=["anchor:claim:audit-emissions-positive", "anchor:claim:review-direct-emissions-negative"],
            conflict_refs=["conflict:emissions-scope"],
            decision_refs=["decision:emissions-audit-review"],
            assumption_refs=["assumption:measurement-boundaries-materially-differ"],
            qualification_refs=["scope-explanation-does-not-resolve-report-audit-claim-conflict"],
            unresolved_refs=["direct-vs-total-emissions-scope"],
            explanatory_fit_score=0.86,
            state=HypothesisReviewState.retained,
            reviewer_ref=reviewer,
        ),
        ContextualHypothesis(
            hypothesis_id="hypothesis:emissions:temporal-change",
            kind=HypothesisKind.temporal_change,
            target_cluster_ref="cluster:emissions-policy-measure",
            title="Performance changed between reporting periods",
            proposition="The negative report and positive audit could both be contextually accurate if they describe different evaluation periods or a real change in performance over time.",
            source_anchor_refs=["anchor:claim:report-emissions-negative", "anchor:claim:audit-emissions-positive", "anchor:temporal:report-evaluation-period", "anchor:temporal:audit-evaluation-period"],
            conflict_refs=["conflict:emissions-claim"],
            decision_refs=["decision:emissions-report-audit", "decision:temporal-report-audit"],
            assumption_refs=["assumption:evaluation-periods-are-not-identical"],
            qualification_refs=["temporal-alignment-remains-unresolved"],
            unresolved_refs=["same-period:reference-corpus"],
            explanatory_fit_score=0.70,
            state=HypothesisReviewState.unresolved,
            reviewer_ref=reviewer,
        ),
        ContextualHypothesis(
            hypothesis_id="hypothesis:emissions:measurement-process",
            kind=HypothesisKind.source_process,
            target_cluster_ref="cluster:emissions-policy-measure",
            title="Different measurement or accounting processes produced different findings",
            proposition="The report and audit could differ because their measurement protocols, baselines, accounting boundaries, or data-quality procedures differ.",
            source_anchor_refs=["anchor:claim:report-emissions-negative", "anchor:claim:audit-emissions-positive"],
            conflict_refs=["conflict:emissions-claim"],
            decision_refs=["decision:emissions-report-audit"],
            assumption_refs=["assumption:measurement-protocols-differ"],
            qualification_refs=["no-measurement-protocol-evidence-in-reference-corpus"],
            unresolved_refs=["measurement-protocol:report", "measurement-protocol:audit"],
            explanatory_fit_score=0.45,
            state=HypothesisReviewState.candidate,
        ),
        ContextualHypothesis(
            hypothesis_id="hypothesis:emissions:real-intervention-effect",
            kind=HypothesisKind.causal_mechanism,
            target_cluster_ref="cluster:emissions-policy-measure",
            title="The intervention genuinely reduced emissions after implementation",
            proposition="A real intervention effect could explain a later positive audit after an earlier negative report, but the governed causal layer has no sufficient identification design or counterfactual estimate.",
            source_anchor_refs=["anchor:claim:report-emissions-negative", "anchor:claim:audit-emissions-positive"],
            conflict_refs=["conflict:emissions-claim", "conflict:report-agency-modality-time"],
            decision_refs=["decision:emissions-report-audit", "decision:emissions-report-agency"],
            mechanism_refs=["mechanism:measure-to-emissions:reference"],
            assumption_refs=["assumption:intervention-precedes-positive-outcome"],
            qualification_refs=["causal-identification-not-established"],
            unresolved_refs=["causal-effect:measure-to-emissions", "same-period:reference-corpus"],
            explanatory_fit_score=0.38,
            state=HypothesisReviewState.constrained,
            reviewer_ref=reviewer,
        ),
        ContextualHypothesis(
            hypothesis_id="hypothesis:actor:same-institution-label-variation",
            kind=HypothesisKind.actor_identity,
            target_cluster_ref="cluster:actor-ministry-agency",
            title="Ministry and agency refer to the same continuing institutional actor",
            proposition="The ministry and agency labels may describe the same institution under source-specific or temporal naming variation.",
            source_anchor_refs=["anchor:actor:ministry", "anchor:actor:agency"],
            conflict_refs=["conflict:actor-identity"],
            decision_refs=["decision:actor-ministry-agency"],
            assumption_refs=["assumption:institutional-continuity"],
            qualification_refs=["identity-merge-not-authorized"],
            unresolved_refs=["thread:actor-continuity:candidate"],
            explanatory_fit_score=0.62,
            state=HypothesisReviewState.unresolved,
            reviewer_ref=reviewer,
        ),
        ContextualHypothesis(
            hypothesis_id="hypothesis:actor:distinct-related-institutions",
            kind=HypothesisKind.actor_identity,
            target_cluster_ref="cluster:actor-ministry-agency",
            title="Ministry and agency are distinct but related institutions",
            proposition="The labels may describe different institutions that participate in the same policy process rather than one continuing canonical actor.",
            source_anchor_refs=["anchor:actor:ministry", "anchor:actor:agency"],
            conflict_refs=["conflict:actor-identity"],
            decision_refs=["decision:actor-ministry-agency"],
            assumption_refs=["assumption:institutional-distinctness"],
            qualification_refs=["relationship-between-institutions-not-established"],
            unresolved_refs=["thread:actor-continuity:candidate"],
            explanatory_fit_score=0.62,
            state=HypothesisReviewState.unresolved,
            reviewer_ref=reviewer,
        ),
        ContextualHypothesis(
            hypothesis_id="hypothesis:governance:contextual-equivalence",
            kind=HypothesisKind.terminology_interpretation,
            target_cluster_ref="cluster:governance-terminology",
            title="治理, governance, and gobernanza are contextually aligned enough for this passage",
            proposition="The three terms can be treated as contextually corresponding for the governed passage while retaining original-language lineage and qualification.",
            source_anchor_refs=["anchor:term:zh-governance", "anchor:term:en-governance", "anchor:term:es-gobernanza"],
            conflict_refs=["conflict:governance-cultural-semantics"],
            decision_refs=["decision:term-zh-en", "decision:term-zh-es"],
            assumption_refs=["assumption:local-discourse-function-overlaps"],
            qualification_refs=["contextual-correspondence-not-universal-equivalence"],
            unresolved_refs=["universal-equivalence:治理-governance-gobernanza"],
            explanatory_fit_score=0.74,
            state=HypothesisReviewState.retained,
            reviewer_ref=reviewer,
        ),
        ContextualHypothesis(
            hypothesis_id="hypothesis:governance:culturally-conditioned-divergence",
            kind=HypothesisKind.terminology_interpretation,
            target_cluster_ref="cluster:governance-terminology",
            title="Cultural and institutional context materially changes the governance terms",
            proposition="The cross-language terms overlap but carry context-specific institutional or historical meaning that should remain semantically distinct during synthesis.",
            source_anchor_refs=["anchor:term:zh-governance", "anchor:term:en-governance", "anchor:term:es-gobernanza"],
            conflict_refs=["conflict:governance-cultural-semantics"],
            decision_refs=["decision:term-zh-en", "decision:term-zh-es"],
            assumption_refs=["assumption:cultural-semantic-context-is-material"],
            qualification_refs=["qualification:08:cultural-divergence-preserved"],
            unresolved_refs=["universal-equivalence:治理-governance-gobernanza"],
            explanatory_fit_score=0.81,
            state=HypothesisReviewState.retained,
            reviewer_ref=reviewer,
        ),
        ContextualHypothesis(
            hypothesis_id="hypothesis:cost:translation-derivation",
            kind=HypothesisKind.source_independence,
            target_cluster_ref="cluster:proposal-cost",
            title="English cost agreement is explained by translation derivation",
            proposition="The English cost statement agrees with the Chinese statement because it is a derived translation of that source, not an independent corroborating observation.",
            source_anchor_refs=["anchor:claim:zh-cost-possible", "anchor:claim:en-derived-cost-possible"],
            conflict_refs=["conflict:translation-source-independence"],
            decision_refs=["decision:cost-zh-en-derived"],
            assumption_refs=["assumption:translation-lineage-is-complete"],
            qualification_refs=["translation-derived-not-independent"],
            unresolved_refs=[],
            explanatory_fit_score=0.99,
            state=HypothesisReviewState.retained,
            reviewer_ref=reviewer,
        ),
        ContextualHypothesis(
            hypothesis_id="hypothesis:cost:independent-corroboration",
            kind=HypothesisKind.source_independence,
            target_cluster_ref="cluster:proposal-cost",
            title="English cost agreement represents independent corroboration",
            proposition="The English cost statement is an independent source that separately corroborates the Chinese cost claim.",
            source_anchor_refs=["anchor:claim:zh-cost-possible", "anchor:claim:en-derived-cost-possible"],
            conflict_refs=["conflict:translation-source-independence"],
            decision_refs=["decision:cost-zh-en-derived"],
            assumption_refs=["assumption:english-representation-independent"],
            qualification_refs=["rejected-by-governed-translation-lineage"],
            unresolved_refs=[],
            explanatory_fit_score=0.02,
            state=HypothesisReviewState.rejected,
            reviewer_ref=reviewer,
        ),
    ]

    evidence_positions = [
        HypothesisEvidencePosition(position_id="position:emissions-scope:support", hypothesis_ref="hypothesis:emissions:scope-difference", position=EvidencePositionKind.supports, anchor_refs=["anchor:claim:audit-emissions-positive", "anchor:claim:review-direct-emissions-negative"], conflict_refs=["conflict:emissions-scope"], decision_refs=["decision:emissions-audit-review"], rationale="The predecessor explicitly preserves total/unspecified versus direct-only emissions scope divergence.", counts_as_independent_support=True),
        HypothesisEvidencePosition(position_id="position:emissions-scope:qualification", hypothesis_ref="hypothesis:emissions:scope-difference", position=EvidencePositionKind.qualifies, conflict_refs=["conflict:emissions-claim"], rationale="Scope divergence does not resolve the separate strict report-versus-audit claim conflict.", unresolved_refs=["same-measure:reference-corpus"]),
        HypothesisEvidencePosition(position_id="position:emissions-temporal:support", hypothesis_ref="hypothesis:emissions:temporal-change", position=EvidencePositionKind.supports, anchor_refs=["anchor:temporal:report-evaluation-period", "anchor:temporal:audit-evaluation-period"], decision_refs=["decision:temporal-report-audit"], rationale="The predecessor keeps evaluation-period alignment as a candidate rather than established same-period identity.", counts_as_independent_support=True, unresolved_refs=["same-period:reference-corpus"]),
        HypothesisEvidencePosition(position_id="position:emissions-temporal:qualification", hypothesis_ref="hypothesis:emissions:temporal-change", position=EvidencePositionKind.qualifies, conflict_refs=["conflict:emissions-claim"], rationale="A temporal explanation remains possible but does not itself demonstrate that the observations occurred in distinct periods."),
        HypothesisEvidencePosition(position_id="position:emissions-measurement:context", hypothesis_ref="hypothesis:emissions:measurement-process", position=EvidencePositionKind.contextualizes, anchor_refs=["anchor:claim:report-emissions-negative", "anchor:claim:audit-emissions-positive"], conflict_refs=["conflict:emissions-claim"], rationale="Conflicting findings motivate a measurement-process hypothesis, but the predecessor contains no protocol-level evidence.", unresolved_refs=["measurement-protocol:report", "measurement-protocol:audit"]),
        HypothesisEvidencePosition(position_id="position:emissions-causal:challenge", hypothesis_ref="hypothesis:emissions:real-intervention-effect", position=EvidencePositionKind.challenges, anchor_refs=["anchor:claim:report-emissions-negative", "anchor:claim:audit-emissions-positive"], rationale="The governed causal layer has no sufficient identification design or counterfactual estimate, so causal-effect explanation remains constrained.", qualification_refs=["causal-identification-not-established"], unresolved_refs=["causal-effect:measure-to-emissions"]),
        HypothesisEvidencePosition(position_id="position:actor-same:unresolved", hypothesis_ref="hypothesis:actor:same-institution-label-variation", position=EvidencePositionKind.unresolved, anchor_refs=["anchor:actor:ministry", "anchor:actor:agency"], conflict_refs=["conflict:actor-identity"], decision_refs=["decision:actor-ministry-agency"], rationale="Continuity is a reviewed candidate, but canonical identity remains unresolved.", unresolved_refs=["thread:actor-continuity:candidate"]),
        HypothesisEvidencePosition(position_id="position:actor-distinct:unresolved", hypothesis_ref="hypothesis:actor:distinct-related-institutions", position=EvidencePositionKind.unresolved, anchor_refs=["anchor:actor:ministry", "anchor:actor:agency"], conflict_refs=["conflict:actor-identity"], decision_refs=["decision:actor-ministry-agency"], rationale="The same identity uncertainty also leaves the distinct-related-institutions explanation live.", unresolved_refs=["thread:actor-continuity:candidate"]),
        HypothesisEvidencePosition(position_id="position:governance-equivalence:qualification", hypothesis_ref="hypothesis:governance:contextual-equivalence", position=EvidencePositionKind.qualifies, anchor_refs=["anchor:term:zh-governance", "anchor:term:en-governance", "anchor:term:es-gobernanza"], conflict_refs=["conflict:governance-cultural-semantics"], decision_refs=["decision:term-zh-en", "decision:term-zh-es"], rationale="Reviewed contextual correspondence supports local alignment, but universal equivalence is explicitly rejected.", qualification_refs=["contextual-correspondence-not-universal-equivalence"]),
        HypothesisEvidencePosition(position_id="position:governance-divergence:support", hypothesis_ref="hypothesis:governance:culturally-conditioned-divergence", position=EvidencePositionKind.supports, anchor_refs=["anchor:term:zh-governance", "anchor:term:en-governance", "anchor:term:es-gobernanza"], conflict_refs=["conflict:governance-cultural-semantics"], rationale="The predecessor explicitly preserves cultural-semantic divergence across the terminology family.", counts_as_independent_support=True, qualification_refs=["qualification:08:cultural-divergence-preserved"]),
        HypothesisEvidencePosition(position_id="position:cost-translation:support", hypothesis_ref="hypothesis:cost:translation-derivation", position=EvidencePositionKind.non_independent, anchor_refs=["anchor:claim:zh-cost-possible", "anchor:claim:en-derived-cost-possible"], conflict_refs=["conflict:translation-source-independence"], decision_refs=["decision:cost-zh-en-derived"], rationale="Translation lineage directly explains agreement between the Chinese original and English derived representation without adding an independent source.", qualification_refs=["translation-derived-not-independent"], counts_as_independent_support=False),
        HypothesisEvidencePosition(position_id="position:cost-independent:challenge", hypothesis_ref="hypothesis:cost:independent-corroboration", position=EvidencePositionKind.challenges, anchor_refs=["anchor:claim:zh-cost-possible", "anchor:claim:en-derived-cost-possible"], conflict_refs=["conflict:translation-source-independence"], decision_refs=["decision:cost-zh-en-derived"], rationale="The source-independence conflict is resolved: the English representation is derived and cannot count as independent corroboration.", qualification_refs=["rejected-by-governed-translation-lineage"], counts_as_independent_support=False),
    ]

    comparisons = [
        CompetingExplanationComparison(comparison_id="comparison:emissions:scope-vs-temporal", left_hypothesis_ref="hypothesis:emissions:scope-difference", right_hypothesis_ref="hypothesis:emissions:temporal-change", relation=ExplanationRelation.underdetermined, discriminating_dimensions=[DiscriminatingDimension.scope, DiscriminatingDimension.temporal], discriminating_questions=["Were the compared observations measured over the same emissions boundary?", "Do the report and audit cover the same evaluation period?"], evidence_needed=["Comparable emissions-boundary definitions", "Date-bounded observation windows"]),
        CompetingExplanationComparison(comparison_id="comparison:emissions:scope-vs-measurement", left_hypothesis_ref="hypothesis:emissions:scope-difference", right_hypothesis_ref="hypothesis:emissions:measurement-process", relation=ExplanationRelation.underdetermined, discriminating_dimensions=[DiscriminatingDimension.scope, DiscriminatingDimension.measurement], discriminating_questions=["Is the disagreement fully explained by scope or also by measurement method?"], evidence_needed=["Measurement protocols", "Accounting boundaries", "Baseline definitions"]),
        CompetingExplanationComparison(comparison_id="comparison:emissions:temporal-vs-causal", left_hypothesis_ref="hypothesis:emissions:temporal-change", right_hypothesis_ref="hypothesis:emissions:real-intervention-effect", relation=ExplanationRelation.underdetermined, discriminating_dimensions=[DiscriminatingDimension.temporal, DiscriminatingDimension.causal], discriminating_questions=["Did outcomes change after the intervention?", "Can the change be causally attributed to the intervention rather than time-varying confounding?"], evidence_needed=["Intervention timing", "Counterfactual comparison", "Identification design"], qualification_refs=["causal-identification-not-established"]),
        CompetingExplanationComparison(comparison_id="comparison:emissions:measurement-vs-causal", left_hypothesis_ref="hypothesis:emissions:measurement-process", right_hypothesis_ref="hypothesis:emissions:real-intervention-effect", relation=ExplanationRelation.underdetermined, discriminating_dimensions=[DiscriminatingDimension.measurement, DiscriminatingDimension.causal], discriminating_questions=["Would harmonized measurement eliminate the apparent change?"], evidence_needed=["Protocol harmonization study", "Causal identification evidence"]),
        CompetingExplanationComparison(comparison_id="comparison:actor:same-vs-distinct", left_hypothesis_ref="hypothesis:actor:same-institution-label-variation", right_hypothesis_ref="hypothesis:actor:distinct-related-institutions", relation=ExplanationRelation.incompatible, discriminating_dimensions=[DiscriminatingDimension.identity], discriminating_questions=["Do both labels resolve to one governed institutional identity across time?"], evidence_needed=["Authoritative organizational records", "Temporal alias lineage", "Institutional succession records"], unresolved_refs=["thread:actor-continuity:candidate"]),
        CompetingExplanationComparison(comparison_id="comparison:governance:equivalence-vs-divergence", left_hypothesis_ref="hypothesis:governance:contextual-equivalence", right_hypothesis_ref="hypothesis:governance:culturally-conditioned-divergence", relation=ExplanationRelation.complementary, discriminating_dimensions=[DiscriminatingDimension.terminology, DiscriminatingDimension.translation_lineage], discriminating_questions=["Which semantic dimensions are preserved across languages and which are culturally conditioned?"], evidence_needed=["Original-language usage context", "Institutional terminology notes", "Parallel-text evidence"], qualification_refs=["local-correspondence-can-coexist-with-cultural-divergence"]),
        CompetingExplanationComparison(comparison_id="comparison:cost:translation-vs-independent", left_hypothesis_ref="hypothesis:cost:translation-derivation", right_hypothesis_ref="hypothesis:cost:independent-corroboration", relation=ExplanationRelation.incompatible, discriminating_dimensions=[DiscriminatingDimension.source_independence, DiscriminatingDimension.translation_lineage], discriminating_questions=["Is the English representation independently sourced or derived from the Chinese original?"], evidence_needed=["Source lineage record"], qualification_refs=["translation-lineage-governs-source-independence"]),
    ]

    explanation_sets = [
        CompetingExplanationSet(explanation_set_id="explanation-set:emissions-discrepancy", target_cluster_ref="cluster:emissions-policy-measure", label="Competing explanations for the emissions discrepancy", hypothesis_refs=["hypothesis:emissions:scope-difference", "hypothesis:emissions:temporal-change", "hypothesis:emissions:measurement-process", "hypothesis:emissions:real-intervention-effect"], evidence_position_refs=["position:emissions-scope:support", "position:emissions-scope:qualification", "position:emissions-temporal:support", "position:emissions-temporal:qualification", "position:emissions-measurement:context", "position:emissions-causal:challenge"], comparison_refs=["comparison:emissions:scope-vs-temporal", "comparison:emissions:scope-vs-measurement", "comparison:emissions:temporal-vs-causal", "comparison:emissions:measurement-vs-causal"], retained_hypothesis_refs=["hypothesis:emissions:scope-difference", "hypothesis:emissions:temporal-change", "hypothesis:emissions:measurement-process", "hypothesis:emissions:real-intervention-effect"], unresolved_questions=["Are evaluation periods identical?", "Are emissions boundaries comparable?", "Do measurement protocols differ?", "Is there sufficient causal identification for a real intervention effect?"], qualification_refs=["strict-claim-conflict-remains-unresolved"]),
        CompetingExplanationSet(explanation_set_id="explanation-set:actor-continuity", target_cluster_ref="cluster:actor-ministry-agency", label="Competing explanations for ministry / agency continuity", hypothesis_refs=["hypothesis:actor:same-institution-label-variation", "hypothesis:actor:distinct-related-institutions"], evidence_position_refs=["position:actor-same:unresolved", "position:actor-distinct:unresolved"], comparison_refs=["comparison:actor:same-vs-distinct"], retained_hypothesis_refs=["hypothesis:actor:same-institution-label-variation", "hypothesis:actor:distinct-related-institutions"], unresolved_questions=["Do authoritative organizational records establish one continuing identity?"], qualification_refs=["identity-merge-not-authorized"]),
        CompetingExplanationSet(explanation_set_id="explanation-set:governance-semantics", target_cluster_ref="cluster:governance-terminology", label="Alternative interpretations of cross-language governance terminology", hypothesis_refs=["hypothesis:governance:contextual-equivalence", "hypothesis:governance:culturally-conditioned-divergence"], evidence_position_refs=["position:governance-equivalence:qualification", "position:governance-divergence:support"], comparison_refs=["comparison:governance:equivalence-vs-divergence"], retained_hypothesis_refs=["hypothesis:governance:contextual-equivalence", "hypothesis:governance:culturally-conditioned-divergence"], unresolved_questions=["Which semantic dimensions are sufficiently aligned for the intended research task?"], qualification_refs=["original-language-authority-preserved"]),
        CompetingExplanationSet(explanation_set_id="explanation-set:cost-source-independence", target_cluster_ref="cluster:proposal-cost", label="Competing explanations for Chinese / English cost-claim agreement", hypothesis_refs=["hypothesis:cost:translation-derivation", "hypothesis:cost:independent-corroboration"], evidence_position_refs=["position:cost-translation:support", "position:cost-independent:challenge"], comparison_refs=["comparison:cost:translation-vs-independent"], retained_hypothesis_refs=["hypothesis:cost:translation-derivation"], rejected_hypothesis_refs=["hypothesis:cost:independent-corroboration"], unresolved_questions=["Does any genuinely independent cost source corroborate the original-language claim?"], qualification_refs=["derived-translation-not-independent-source"]),
    ]

    subjects = [x.hypothesis_id for x in hypotheses] + [x.position_id for x in evidence_positions] + [x.comparison_id for x in comparisons] + [x.explanation_set_id for x in explanation_sets]
    provenance = ContextualHypothesisProvenanceRecord(
        provenance_id="contextual-hypothesis-provenance:reference",
        predecessor_reconciliation_fingerprint_sha256=pred.fingerprint(),
        subject_refs=subjects,
        method="Construct competing explanatory objects only from governed v4.17 reconciliation clusters, conflicts, decisions, anchors, and preserved v4.15 causal context. Retain supporting, challenging, qualifying, unresolved, and non-independent evidence positions separately. Scores are advisory explanatory-fit metadata, not probabilities, truth values, or evidence weights. No winning explanation is inferred automatically.",
    )
    material = {
        "predecessor": pred.fingerprint(),
        "hypotheses": {x.hypothesis_id: x.fingerprint() for x in hypotheses},
        "evidence_positions": {x.position_id: x.fingerprint() for x in evidence_positions},
        "comparisons": {x.comparison_id: x.fingerprint() for x in comparisons},
        "explanation_sets": {x.explanation_set_id: x.fingerprint() for x in explanation_sets},
    }
    snapshot = ContextualHypothesisSnapshot(
        snapshot_id="contextual-hypothesis-snapshot:reference:v1",
        predecessor_reconciliation_fingerprint_sha256=pred.fingerprint(),
        hypothesis_fingerprints=material["hypotheses"],
        evidence_position_fingerprints=material["evidence_positions"],
        comparison_fingerprints=material["comparisons"],
        explanation_set_fingerprints=material["explanation_sets"],
        deterministic_hypothesis_context_fingerprint_sha256=canonical_sha256(material),
    )
    return ContextualHypothesisCompetingExplanationBundle(
        policy=ContextualHypothesisPolicy(policy_id="contextual-hypothesis-competing-explanation-policy:v1"),
        predecessor_reconciliation=pred,
        hypotheses=hypotheses,
        evidence_positions=evidence_positions,
        comparisons=comparisons,
        explanation_sets=explanation_sets,
        provenance_records=[provenance],
        snapshots=[snapshot],
    )


def contract_document() -> dict:
    b = reference_contextual_hypothesis_competing_explanation_bundle()
    return {
        "ok": True,
        "release": CORE_RELEASE,
        "contract": CONTRACT_VERSION,
        "predecessor_contract": PREDECESSOR_CONTRACT,
        "identity": {"product": "Sustainable Catalyst Platform Core", "build": "Contextual Hypothesis & Competing Explanation Objects", "major_api": "v4"},
        "principles": {
            "hypotheses_are_explanatory_objects_not_truth_claims": True,
            "competing_explanations_may_coexist": True,
            "support_challenge_qualification_and_unresolved_positions_are_separate": True,
            "source_independence_constraints_carry_forward": True,
            "derived_translation_cannot_count_as_independent_support": True,
            "causal_identification_status_carries_forward": True,
            "identity_uncertainty_carries_forward": True,
            "original_language_authority_carries_forward": True,
        },
        "boundaries": {
            "explanatory_fit_score_establishes_truth": False,
            "explanatory_fit_score_is_probability": False,
            "support_count_establishes_truth": False,
            "challenge_count_establishes_falsity": False,
            "retained_hypothesis_is_selected_winner": False,
            "automatic_hypothesis_promotion_performed": False,
            "automatic_context_graph_mutation_performed": False,
            "automatic_evidence_graph_mutation_performed": False,
            "automatic_knowledge_graph_mutation_performed": False,
            "automatic_identity_graph_mutation_performed": False,
        },
        "roadmap_integration": {
            "extends_v4170_cross_source_semantic_reconciliation": True,
            "prepares_v4190_semantic_synthesis_research_answer": True,
            "prepares_v4200_unified_contextual_reasoning_runtime": True,
        },
        "reference": {
            "predecessor_release": b.predecessor_reconciliation.release,
            "predecessor_fingerprint_sha256": b.predecessor_reconciliation.fingerprint(),
            "hypotheses": len(b.hypotheses),
            "evidence_positions": len(b.evidence_positions),
            "comparisons": len(b.comparisons),
            "explanation_sets": len(b.explanation_sets),
            "retained_hypotheses": sum(x.state == HypothesisReviewState.retained for x in b.hypotheses),
            "unresolved_hypotheses": sum(x.state == HypothesisReviewState.unresolved for x in b.hypotheses),
            "constrained_hypotheses": sum(x.state == HypothesisReviewState.constrained for x in b.hypotheses),
            "rejected_hypotheses": sum(x.state == HypothesisReviewState.rejected for x in b.hypotheses),
            "non_independent_positions": sum(x.position == EvidencePositionKind.non_independent for x in b.evidence_positions),
            "sets_with_no_winner": sum(not x.set_establishes_winner for x in b.explanation_sets),
            "snapshots": len(b.snapshots),
            "bundle_fingerprint_sha256": b.fingerprint(),
        },
        "database_migration": "none",
    }
