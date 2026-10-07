from __future__ import annotations

from enum import Enum
from functools import lru_cache
from typing import Literal

from pydantic import BaseModel, Field, model_validator

from .computational_runtime_objects import canonical_sha256
from .claim_alignment_agreement_contradiction import (
    ClaimAlignmentAgreementContradictionBundle,
    ClaimRelationKind,
    reference_claim_alignment_agreement_contradiction_bundle,
)

CORE_RELEASE = "4.14.0"
CONTRACT_VERSION = "sc.core.evidence-context-integration-layer.v1"
PREDECESSOR_CONTRACT = "sc.core.claim-alignment-agreement-contradiction-intelligence.v1"


class EvidenceContextRelationKind(str, Enum):
    supports = "supports"
    challenges = "challenges"
    qualifies = "qualifies"
    contextualizes = "contextualizes"
    corroborates = "corroborates"
    background = "background"
    derived_representation = "derived-representation"
    unresolved = "unresolved"


class EvidenceIndependenceState(str, Enum):
    independent = "independent"
    same_source_derived = "same-source-derived"
    source_related = "source-related"
    unknown = "unknown"


class EvidenceMaterializationState(str, Enum):
    reference_fixture = "reference-fixture"
    materialized_upstream = "materialized-upstream"


class EvidenceContextReviewState(str, Enum):
    generated = "generated"
    reviewed = "reviewed"
    accepted = "accepted"
    disputed = "disputed"
    unresolved = "unresolved"


class EvidenceIntegrationOutcome(str, Enum):
    supports_comparison_context = "supports-comparison-context"
    qualifies_comparison_context = "qualifies-comparison-context"
    contextualizes_only = "contextualizes-only"
    unresolved_evidence_conflict = "unresolved-evidence-conflict"
    derived_not_independent_corroboration = "derived-not-independent-corroboration"


class EvidenceContextPolicy(BaseModel):
    policy_id: str = Field(min_length=3, max_length=500)
    predecessor_claim_comparison_objects_remain_immutable: Literal[True] = True
    semantic_claim_is_distinct_from_evidence_record: Literal[True] = True
    evidence_link_requires_explicit_claim_scope: Literal[True] = True
    upstream_evidence_review_status_is_authoritative: Literal[True] = True
    evidence_stance_is_preserved_from_upstream: Literal[True] = True
    translation_derivative_is_not_independent_corroboration: Literal[True] = True
    contradiction_requires_context_not_vote_counting: Literal[True] = True
    qualifications_and_unresolved_state_must_carry_forward: Literal[True] = True
    evidence_context_link_is_interpretive_bridge: Literal[True] = True
    read_only_bridge_by_default: Literal[True] = True
    supporting_evidence_count_establishes_truth: Literal[False] = False
    evidence_link_establishes_evidence_validity: Literal[False] = False
    contradiction_link_identifies_false_claim: Literal[False] = False
    semantic_layer_may_override_upstream_review_status: Literal[False] = False
    automatic_evidence_materialization_authorized: Literal[False] = False
    claim_truth_promotion_authorized: Literal[False] = False
    context_graph_mutation_authorized: Literal[False] = False
    identity_graph_mutation_authorized: Literal[False] = False
    evidence_graph_mutation_authorized: Literal[False] = False
    knowledge_graph_mutation_authorized: Literal[False] = False


class EvidenceGraphAnchor(BaseModel):
    anchor_id: str = Field(min_length=3, max_length=500)
    evidence_record_ref: str = Field(min_length=3, max_length=500)
    claim_ref: str = Field(min_length=3, max_length=500)
    source_context_ref: str = Field(min_length=3, max_length=500)
    source_snapshot_ref: str = Field(min_length=3, max_length=500)
    evidence_type: str = Field(min_length=3, max_length=200)
    upstream_stance: str = Field(min_length=3, max_length=100)
    upstream_review_status: str = Field(min_length=3, max_length=100)
    materialization_state: EvidenceMaterializationState = EvidenceMaterializationState.reference_fixture
    independence_state: EvidenceIndependenceState
    derived_from_evidence_record_ref: str | None = Field(default=None, max_length=500)
    qualification_refs: list[str] = Field(default_factory=list)
    unresolved_refs: list[str] = Field(default_factory=list)
    upstream_review_status_remains_authoritative: Literal[True] = True
    anchor_does_not_establish_claim_truth: Literal[True] = True

    @model_validator(mode="after")
    def validate_anchor(self):
        if len(self.qualification_refs) != len(set(self.qualification_refs)):
            raise ValueError("qualification_refs must be unique")
        if len(self.unresolved_refs) != len(set(self.unresolved_refs)):
            raise ValueError("unresolved_refs must be unique")
        if self.independence_state == EvidenceIndependenceState.same_source_derived and not self.derived_from_evidence_record_ref:
            raise ValueError("same-source-derived evidence anchor requires derived_from_evidence_record_ref")
        if self.independence_state != EvidenceIndependenceState.same_source_derived and self.derived_from_evidence_record_ref:
            raise ValueError("derived_from_evidence_record_ref is reserved for same-source-derived anchors")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class EvidenceContextLink(BaseModel):
    link_id: str = Field(min_length=3, max_length=500)
    claim_ref: str = Field(min_length=3, max_length=500)
    evidence_anchor_ref: str = Field(min_length=3, max_length=500)
    relation_assessment_ref: str | None = Field(default=None, max_length=500)
    contextual_relation: EvidenceContextRelationKind
    fit_score: float = Field(ge=0.0, le=1.0)
    scope_match: bool
    independent_corroboration: bool
    qualification_refs: list[str] = Field(default_factory=list)
    unresolved_refs: list[str] = Field(default_factory=list)
    state: EvidenceContextReviewState = EvidenceContextReviewState.reviewed
    reviewer_ref: str | None = Field(default=None, max_length=500)
    link_is_interpretive_bridge_not_evidence_review: Literal[True] = True

    @model_validator(mode="after")
    def validate_link(self):
        if len(self.qualification_refs) != len(set(self.qualification_refs)):
            raise ValueError("qualification_refs must be unique")
        if len(self.unresolved_refs) != len(set(self.unresolved_refs)):
            raise ValueError("unresolved_refs must be unique")
        if self.state in {EvidenceContextReviewState.reviewed, EvidenceContextReviewState.accepted, EvidenceContextReviewState.disputed} and not self.reviewer_ref:
            raise ValueError("reviewed/accepted/disputed link requires reviewer_ref")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class EvidenceContextAssessment(BaseModel):
    assessment_id: str = Field(min_length=3, max_length=500)
    claim_relation_assessment_ref: str = Field(min_length=3, max_length=500)
    evidence_link_refs: list[str] = Field(min_length=1)
    outcome: EvidenceIntegrationOutcome
    rationale: str = Field(min_length=3, max_length=4000)
    qualification_refs: list[str] = Field(default_factory=list)
    unresolved_refs: list[str] = Field(default_factory=list)
    state: EvidenceContextReviewState = EvidenceContextReviewState.reviewed
    reviewer_ref: str | None = Field(default=None, max_length=500)
    assessment_does_not_resolve_claim_truth: Literal[True] = True
    assessment_does_not_override_evidence_review: Literal[True] = True

    @model_validator(mode="after")
    def validate_assessment(self):
        if len(self.evidence_link_refs) != len(set(self.evidence_link_refs)):
            raise ValueError("evidence_link_refs must be unique")
        if len(self.qualification_refs) != len(set(self.qualification_refs)):
            raise ValueError("qualification_refs must be unique")
        if len(self.unresolved_refs) != len(set(self.unresolved_refs)):
            raise ValueError("unresolved_refs must be unique")
        if self.state in {EvidenceContextReviewState.reviewed, EvidenceContextReviewState.accepted, EvidenceContextReviewState.disputed} and not self.reviewer_ref:
            raise ValueError("reviewed/accepted/disputed assessment requires reviewer_ref")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class EvidenceContextProvenanceRecord(BaseModel):
    provenance_id: str = Field(min_length=3, max_length=500)
    predecessor_claim_comparison_fingerprint_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    subject_refs: list[str] = Field(min_length=1)
    method: str = Field(min_length=3, max_length=1000)
    replayable: Literal[True] = True

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class EvidenceContextSnapshot(BaseModel):
    snapshot_id: str = Field(min_length=3, max_length=500)
    predecessor_claim_comparison_fingerprint_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    anchor_fingerprints: dict[str, str]
    link_fingerprints: dict[str, str]
    assessment_fingerprints: dict[str, str]
    deterministic_integration_fingerprint_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    supersedable: Literal[True] = True
    snapshot_is_not_truth_or_evidence_certification: Literal[True] = True

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class EvidenceContextIntegrationBundle(BaseModel):
    release: Literal["4.14.0"] = "4.14.0"
    contract: Literal[CONTRACT_VERSION] = CONTRACT_VERSION
    predecessor_contract: Literal[PREDECESSOR_CONTRACT] = PREDECESSOR_CONTRACT
    policy: EvidenceContextPolicy
    predecessor_claim_comparison: ClaimAlignmentAgreementContradictionBundle
    evidence_anchors: list[EvidenceGraphAnchor] = Field(min_length=1)
    links: list[EvidenceContextLink] = Field(min_length=1)
    assessments: list[EvidenceContextAssessment] = Field(min_length=1)
    provenance_records: list[EvidenceContextProvenanceRecord] = Field(min_length=1)
    snapshots: list[EvidenceContextSnapshot] = Field(min_length=1)
    database_migration: Literal["none"] = "none"

    @model_validator(mode="after")
    def validate_bundle(self):
        predecessor = self.predecessor_claim_comparison
        if predecessor.release != "4.13.0" or predecessor.contract != PREDECESSOR_CONTRACT:
            raise ValueError("v4.14 must preserve governed v4.13 claim-comparison predecessor")

        def unique(values: list[str], label: str):
            if len(values) != len(set(values)):
                raise ValueError(f"{label} must be unique")

        unique([x.anchor_id for x in self.evidence_anchors], "evidence anchor ids")
        unique([x.evidence_record_ref for x in self.evidence_anchors], "evidence record refs")
        unique([x.link_id for x in self.links], "evidence context link ids")
        unique([x.assessment_id for x in self.assessments], "evidence context assessment ids")
        unique([x.provenance_id for x in self.provenance_records], "provenance ids")
        unique([x.snapshot_id for x in self.snapshots], "snapshot ids")

        claims = {x.claim_id: x for x in predecessor.claims}
        source_contexts = {x.source_context_id for x in predecessor.source_contexts}
        relation_assessments = {x.assessment_id: x for x in predecessor.assessments}
        anchors = {x.anchor_id: x for x in self.evidence_anchors}
        evidence_refs = {x.evidence_record_ref for x in self.evidence_anchors}
        links = {x.link_id: x for x in self.links}

        for anchor in self.evidence_anchors:
            if anchor.claim_ref not in claims:
                raise ValueError("evidence anchor claim_ref must resolve to v4.13 claim")
            if anchor.source_context_ref not in source_contexts:
                raise ValueError("evidence anchor source_context_ref must resolve to v4.13 source context")
            if anchor.derived_from_evidence_record_ref and anchor.derived_from_evidence_record_ref not in evidence_refs:
                raise ValueError("derived evidence anchor must reference an anchor in this governed bundle")

        for link in self.links:
            if link.claim_ref not in claims:
                raise ValueError("evidence context link claim_ref must resolve")
            if link.evidence_anchor_ref not in anchors:
                raise ValueError("evidence context link evidence_anchor_ref must resolve")
            anchor = anchors[link.evidence_anchor_ref]
            if anchor.claim_ref != link.claim_ref:
                raise ValueError("evidence context link must connect anchor to its governed claim")
            if link.relation_assessment_ref and link.relation_assessment_ref not in relation_assessments:
                raise ValueError("relation_assessment_ref must resolve to v4.13 assessment")
            if anchor.independence_state == EvidenceIndependenceState.same_source_derived and link.independent_corroboration:
                raise ValueError("same-source-derived evidence cannot count as independent corroboration")
            if link.contextual_relation == EvidenceContextRelationKind.corroborates and not link.independent_corroboration:
                raise ValueError("corroborates relation requires independent_corroboration")

        relation_to_links: dict[str, list[EvidenceContextLink]] = {x: [] for x in relation_assessments}
        for link in self.links:
            if link.relation_assessment_ref:
                relation_to_links[link.relation_assessment_ref].append(link)

        for assessment in self.assessments:
            if assessment.claim_relation_assessment_ref not in relation_assessments:
                raise ValueError("evidence context assessment must resolve v4.13 relation assessment")
            if not set(assessment.evidence_link_refs).issubset(links):
                raise ValueError("evidence context assessment link refs must resolve")
            expected = {x.link_id for x in relation_to_links[assessment.claim_relation_assessment_ref]}
            if set(assessment.evidence_link_refs) != expected:
                raise ValueError("assessment evidence_link_refs must exactly cover linked evidence context for relation")
            predecessor_relation = relation_assessments[assessment.claim_relation_assessment_ref].relation_kind
            if predecessor_relation == ClaimRelationKind.contradiction and assessment.outcome != EvidenceIntegrationOutcome.unresolved_evidence_conflict:
                raise ValueError("strict contradiction remains unresolved at evidence-context integration without upstream adjudication")

        predecessor_fp = predecessor.fingerprint()
        subjects = set(anchors) | set(links) | {x.assessment_id for x in self.assessments}
        for prov in self.provenance_records:
            if prov.predecessor_claim_comparison_fingerprint_sha256 != predecessor_fp:
                raise ValueError("provenance predecessor fingerprint must match v4.13")
            if not set(prov.subject_refs).issubset(subjects):
                raise ValueError("provenance subject_refs must resolve")

        for snap in self.snapshots:
            if snap.predecessor_claim_comparison_fingerprint_sha256 != predecessor_fp:
                raise ValueError("snapshot predecessor fingerprint must match v4.13")
            if snap.anchor_fingerprints != {x.anchor_id: x.fingerprint() for x in self.evidence_anchors}:
                raise ValueError("snapshot anchor fingerprints must be exact")
            if snap.link_fingerprints != {x.link_id: x.fingerprint() for x in self.links}:
                raise ValueError("snapshot link fingerprints must be exact")
            if snap.assessment_fingerprints != {x.assessment_id: x.fingerprint() for x in self.assessments}:
                raise ValueError("snapshot assessment fingerprints must be exact")
            material = {
                "predecessor": predecessor_fp,
                "anchors": snap.anchor_fingerprints,
                "links": snap.link_fingerprints,
                "assessments": snap.assessment_fingerprints,
            }
            if snap.deterministic_integration_fingerprint_sha256 != canonical_sha256(material):
                raise ValueError("snapshot deterministic integration fingerprint mismatch")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


@lru_cache(maxsize=1)
def reference_evidence_context_integration_bundle() -> EvidenceContextIntegrationBundle:
    predecessor = reference_claim_alignment_agreement_contradiction_bundle()
    claims = {x.claim_id: x for x in predecessor.claims}
    relation_assessments = {x.assessment_id: x for x in predecessor.assessments}

    def anchor(claim_ref: str, suffix: str, evidence_type: str, stance: str, independence: EvidenceIndependenceState,
               review: str = "reviewed", derived_from: str | None = None) -> EvidenceGraphAnchor:
        c = claims[claim_ref]
        return EvidenceGraphAnchor(
            anchor_id=f"evidence-anchor:{suffix}",
            evidence_record_ref=f"sc:evidence:reference:{suffix}",
            claim_ref=claim_ref,
            source_context_ref=c.source_context_ref,
            source_snapshot_ref=f"source-snapshot:reference:{suffix}",
            evidence_type=evidence_type,
            upstream_stance=stance,
            upstream_review_status=review,
            independence_state=independence,
            derived_from_evidence_record_ref=derived_from,
            qualification_refs=c.qualification_refs,
            unresolved_refs=c.unresolved_refs,
        )

    anchors = [
        anchor("claim:v45:measure-no-emissions-reduction", "report-negative-emissions", "documentary-source", "supports", EvidenceIndependenceState.independent),
        anchor("claim:v46:measure-may-reduce-emissions", "agency-possible-emissions", "attributed-statement", "contextualizes", EvidenceIndependenceState.independent),
        anchor("claim:v413:audit-reduced-emissions", "audit-positive-emissions", "audit-record", "supports", EvidenceIndependenceState.independent),
        anchor("claim:v413:review-no-direct-emissions-reduction", "review-direct-negative-emissions", "review-record", "qualifies", EvidenceIndependenceState.independent),
        anchor("claim:v45:proposal-may-lower-costs", "researcher-cost-claim", "attributed-statement", "contextualizes", EvidenceIndependenceState.source_related),
        anchor("claim:v48:zh-proposal-may-lower-costs", "zh-original-cost-claim", "original-language-source", "supports", EvidenceIndependenceState.independent),
        anchor("claim:v48:en-proposal-may-reduce-costs", "en-derived-cost-claim", "derived-translation", "contextualizes", EvidenceIndependenceState.same_source_derived,
               derived_from="sc:evidence:reference:zh-original-cost-claim"),
    ]
    anchor_by_claim = {x.claim_ref: x for x in anchors}

    # Map every v4.13 comparison relation to evidence-context links for both claims.
    links: list[EvidenceContextLink] = []
    for rel in predecessor.assessments:
        pair = next(x for x in predecessor.pairs if x.pair_id == rel.pair_ref)
        for side, claim_ref in (("left", pair.left_claim_ref), ("right", pair.right_claim_ref)):
            a = anchor_by_claim[claim_ref]
            derived = a.independence_state == EvidenceIndependenceState.same_source_derived
            contextual_relation = EvidenceContextRelationKind.derived_representation if derived else (
                EvidenceContextRelationKind.qualifies if a.upstream_stance == "qualifies" else
                EvidenceContextRelationKind.contextualizes if a.upstream_stance == "contextualizes" else
                EvidenceContextRelationKind.supports
            )
            links.append(EvidenceContextLink(
                link_id=f"evidence-context-link:{rel.assessment_id.split(':',1)[1]}:{side}",
                claim_ref=claim_ref,
                evidence_anchor_ref=a.anchor_id,
                relation_assessment_ref=rel.assessment_id,
                contextual_relation=contextual_relation,
                fit_score=0.99 if a.upstream_stance == "supports" else (0.93 if a.upstream_stance == "qualifies" else 0.88),
                scope_match=True if rel.relation_kind in {ClaimRelationKind.contradiction, ClaimRelationKind.agreement, ClaimRelationKind.qualified_agreement} else False,
                independent_corroboration=False,
                qualification_refs=list(dict.fromkeys(rel.qualification_refs + a.qualification_refs)),
                unresolved_refs=list(dict.fromkeys(rel.unresolved_refs + a.unresolved_refs)),
                state=EvidenceContextReviewState.reviewed,
                reviewer_ref="reviewer:evidence-context-reference",
            ))

    assessments: list[EvidenceContextAssessment] = []
    links_by_rel: dict[str, list[EvidenceContextLink]] = {}
    for link in links:
        links_by_rel.setdefault(link.relation_assessment_ref, []).append(link)

    outcome_map = {
        ClaimRelationKind.contradiction: EvidenceIntegrationOutcome.unresolved_evidence_conflict,
        ClaimRelationKind.apparent_contradiction: EvidenceIntegrationOutcome.qualifies_comparison_context,
        ClaimRelationKind.qualified_agreement: EvidenceIntegrationOutcome.qualifies_comparison_context,
        ClaimRelationKind.partial_agreement: EvidenceIntegrationOutcome.qualifies_comparison_context,
        ClaimRelationKind.agreement: EvidenceIntegrationOutcome.supports_comparison_context,
        ClaimRelationKind.scope_mismatch: EvidenceIntegrationOutcome.qualifies_comparison_context,
        ClaimRelationKind.distinct_claim: EvidenceIntegrationOutcome.contextualizes_only,
        ClaimRelationKind.unresolved: EvidenceIntegrationOutcome.contextualizes_only,
    }

    for rel in predecessor.assessments:
        rel_links = links_by_rel[rel.assessment_id]
        derived_present = any(anchor_by_claim[x.claim_ref].independence_state == EvidenceIndependenceState.same_source_derived for x in rel_links)
        outcome = EvidenceIntegrationOutcome.derived_not_independent_corroboration if derived_present else outcome_map[rel.relation_kind]
        rationale = (
            "The relation is connected to governed evidence-context anchors, but the bridge does not adjudicate truth or override upstream evidence review. "
            + ("One side is a same-source translation derivative and therefore cannot count as independent corroboration. " if derived_present else "")
            + ("The predecessor relation is a strict contradiction, so competing evidence context remains unresolved pending governed upstream adjudication." if rel.relation_kind == ClaimRelationKind.contradiction else "The predecessor claim relation and its qualifications remain intact.")
        )
        assessments.append(EvidenceContextAssessment(
            assessment_id=f"evidence-context-assessment:{rel.assessment_id.split(':',1)[1]}",
            claim_relation_assessment_ref=rel.assessment_id,
            evidence_link_refs=[x.link_id for x in rel_links],
            outcome=outcome,
            rationale=rationale,
            qualification_refs=rel.qualification_refs,
            unresolved_refs=rel.unresolved_refs,
            state=EvidenceContextReviewState.unresolved if rel.relation_kind == ClaimRelationKind.contradiction else EvidenceContextReviewState.reviewed,
            reviewer_ref=None if rel.relation_kind == ClaimRelationKind.contradiction else "reviewer:evidence-context-reference",
        ))

    provenance = EvidenceContextProvenanceRecord(
        provenance_id="evidence-context-provenance:reference",
        predecessor_claim_comparison_fingerprint_sha256=predecessor.fingerprint(),
        subject_refs=[x.anchor_id for x in anchors] + [x.link_id for x in links] + [x.assessment_id for x in assessments],
        method="read-only reviewed bridge between governed v4.13 contextual claim relations and Evidence Graph-style evidence anchors; no evidence materialization or review mutation",
    )
    material = {
        "predecessor": predecessor.fingerprint(),
        "anchors": {x.anchor_id: x.fingerprint() for x in anchors},
        "links": {x.link_id: x.fingerprint() for x in links},
        "assessments": {x.assessment_id: x.fingerprint() for x in assessments},
    }
    snapshot = EvidenceContextSnapshot(
        snapshot_id="evidence-context-snapshot:reference:v1",
        predecessor_claim_comparison_fingerprint_sha256=predecessor.fingerprint(),
        anchor_fingerprints=material["anchors"],
        link_fingerprints=material["links"],
        assessment_fingerprints=material["assessments"],
        deterministic_integration_fingerprint_sha256=canonical_sha256(material),
    )
    return EvidenceContextIntegrationBundle(
        policy=EvidenceContextPolicy(policy_id="evidence-context-policy:v1"),
        predecessor_claim_comparison=predecessor,
        evidence_anchors=anchors,
        links=links,
        assessments=assessments,
        provenance_records=[provenance],
        snapshots=[snapshot],
    )


def contract_document() -> dict:
    b = reference_evidence_context_integration_bundle()
    outcomes = {x.value: 0 for x in EvidenceIntegrationOutcome}
    for a in b.assessments:
        outcomes[a.outcome.value] += 1
    return {
        "ok": True,
        "release": CORE_RELEASE,
        "contract": CONTRACT_VERSION,
        "predecessor_contract": PREDECESSOR_CONTRACT,
        "identity": {"product": "Sustainable Catalyst Platform Core", "build": "Evidence-Context Integration Layer", "major_api": "v4"},
        "principles": {
            "semantic_claim_is_distinct_from_evidence_record": True,
            "upstream_evidence_review_status_is_authoritative": True,
            "translation_derivative_is_not_independent_corroboration": True,
            "contradiction_requires_context_not_vote_counting": True,
            "qualifications_and_unresolved_state_must_carry_forward": True,
            "read_only_bridge_by_default": True,
        },
        "boundaries": {
            "supporting_evidence_count_establishes_truth": False,
            "evidence_link_establishes_evidence_validity": False,
            "contradiction_link_identifies_false_claim": False,
            "semantic_layer_may_override_upstream_review_status": False,
            "automatic_evidence_materialization_authorized": False,
            "claim_truth_promotion_authorized": False,
            "context_graph_mutation_performed": False,
            "identity_graph_mutation_performed": False,
            "evidence_graph_mutation_performed": False,
            "knowledge_graph_mutation_performed": False,
        },
        "roadmap_integration": {
            "extends_v4130_claim_alignment_agreement_contradiction": True,
            "prepares_v4150_contextual_causal_language_mechanism_intelligence": True,
            "prepares_v4160_narrative_framing_perspective_intelligence": True,
            "prepares_v4170_cross_source_semantic_reconciliation": True,
            "prepares_v4180_contextual_hypothesis_competing_explanations": True,
            "prepares_v4190_semantic_synthesis_research_answer": True,
            "prepares_v4200_unified_contextual_reasoning_runtime": True,
        },
        "reference": {
            "predecessor_release": b.predecessor_claim_comparison.release,
            "predecessor_fingerprint_sha256": b.predecessor_claim_comparison.fingerprint(),
            "evidence_anchors": len(b.evidence_anchors),
            "evidence_context_links": len(b.links),
            "evidence_context_assessments": len(b.assessments),
            "independent_anchors": sum(x.independence_state == EvidenceIndependenceState.independent for x in b.evidence_anchors),
            "derived_same_source_anchors": sum(x.independence_state == EvidenceIndependenceState.same_source_derived for x in b.evidence_anchors),
            "strict_contradictions_left_unresolved": sum(a.outcome == EvidenceIntegrationOutcome.unresolved_evidence_conflict for a in b.assessments),
            "outcome_counts": outcomes,
            "snapshots": len(b.snapshots),
            "bundle_fingerprint_sha256": b.fingerprint(),
        },
        "database_migration": "none",
    }
