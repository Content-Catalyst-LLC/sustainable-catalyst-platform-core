from __future__ import annotations

from enum import Enum
from functools import lru_cache
from typing import Literal

from pydantic import BaseModel, Field, model_validator

from .computational_runtime_objects import canonical_sha256
from .narrative_framing_perspective import (
    NarrativeFramingPerspectiveBundle,
    reference_narrative_framing_perspective_bundle,
)

CORE_RELEASE = "4.17.0"
CONTRACT_VERSION = "sc.core.cross-source-semantic-reconciliation-engine.v1"
PREDECESSOR_CONTRACT = "sc.core.narrative-framing-perspective-intelligence.v1"


class ReconciliationAnchorKind(str, Enum):
    claim = "claim"
    perspective = "perspective"
    frame = "frame"
    actor_reference = "actor-reference"
    terminology = "terminology"
    temporal_scope = "temporal-scope"
    spatial_reference = "spatial-reference"


class ReconciliationDimension(str, Enum):
    subject = "subject"
    predicate = "predicate"
    object_scope = "object-scope"
    polarity = "polarity"
    modality = "modality"
    temporal_scope = "temporal-scope"
    spatial_scope = "spatial-scope"
    actor_identity = "actor-identity"
    terminology = "terminology"
    translation_lineage = "translation-lineage"
    framing = "framing"
    causal_context = "causal-context"
    evidence_context = "evidence-context"
    source_independence = "source-independence"


class ReconciliationRelation(str, Enum):
    exact_correspondence = "exact-correspondence"
    translation_derived_correspondence = "translation-derived-correspondence"
    near_equivalent = "near-equivalent"
    same_semantic_target_conflicting = "same-semantic-target-conflicting"
    scope_overlap = "scope-overlap"
    modality_temporal_related = "modality-temporal-related"
    temporal_alignment_candidate = "temporal-alignment-candidate"
    actor_continuity_candidate = "actor-continuity-candidate"
    culturally_conditioned_correspondence = "culturally-conditioned-correspondence"
    deictic_grounding = "deictic-grounding"
    distinct = "distinct"
    unresolved = "unresolved"


class ReconciliationConflictKind(str, Enum):
    claim_conflict = "claim-conflict"
    scope_divergence = "scope-divergence"
    modality_temporal_divergence = "modality-temporal-divergence"
    identity_uncertainty = "identity-uncertainty"
    cultural_semantic_divergence = "cultural-semantic-divergence"
    source_independence_constraint = "source-independence-constraint"


class ReconciliationReviewState(str, Enum):
    generated = "generated"
    reviewed = "reviewed"
    accepted = "accepted"
    rejected = "rejected"
    unresolved = "unresolved"


class ReconciledClusterKind(str, Enum):
    claim_family = "claim-family"
    actor_family = "actor-family"
    terminology_family = "terminology-family"
    temporal_family = "temporal-family"
    spatial_family = "spatial-family"


class CrossSourceReconciliationPolicy(BaseModel):
    policy_id: str = Field(min_length=3, max_length=500)
    predecessor_framing_context_remains_immutable: Literal[True] = True
    reconciliation_is_alignment_not_canonicalization: Literal[True] = True
    same_surface_form_is_not_same_entity: Literal[True] = True
    same_semantic_key_is_not_truth: Literal[True] = True
    source_agreement_is_not_truth: Literal[True] = True
    contradiction_is_not_false_claim_identification: Literal[True] = True
    temporal_overlap_is_not_same_event: Literal[True] = True
    spatial_grounding_is_not_canonical_geographic_identity: Literal[True] = True
    original_language_remains_authoritative: Literal[True] = True
    translation_remains_derived: Literal[True] = True
    derived_representation_is_not_independent_source: Literal[True] = True
    unresolved_identity_must_carry_forward: Literal[True] = True
    framing_difference_must_not_be_erased: Literal[True] = True
    causal_and_evidence_context_must_remain_distinct: Literal[True] = True
    reconciliation_score_establishes_truth: Literal[False] = False
    reconciliation_score_establishes_identity: Literal[False] = False
    reconciliation_score_establishes_equivalence: Literal[False] = False
    automatic_canonical_entity_merge_authorized: Literal[False] = False
    automatic_context_graph_mutation_authorized: Literal[False] = False
    automatic_evidence_graph_mutation_authorized: Literal[False] = False
    automatic_knowledge_graph_mutation_authorized: Literal[False] = False
    automatic_identity_graph_mutation_authorized: Literal[False] = False


class ReconciliationAnchor(BaseModel):
    anchor_id: str = Field(min_length=3, max_length=500)
    kind: ReconciliationAnchorKind
    source_ref: str = Field(min_length=3, max_length=500)
    source_type: Literal["claim", "perspective", "frame", "memory"]
    source_label: str = Field(min_length=1, max_length=1500)
    language_tag: str = Field(min_length=2, max_length=50)
    surface_form: str = Field(min_length=1, max_length=4000)
    semantic_key: str = Field(min_length=3, max_length=1000)
    subject_key: str | None = Field(default=None, max_length=1000)
    predicate_key: str | None = Field(default=None, max_length=1000)
    temporal_scope_ref: str | None = Field(default=None, max_length=1000)
    spatial_scope_ref: str | None = Field(default=None, max_length=1000)
    derived_representation: bool = False
    provenance_refs: list[str] = Field(default_factory=list)
    qualification_refs: list[str] = Field(default_factory=list)
    unresolved_refs: list[str] = Field(default_factory=list)
    anchor_is_normalized_for_reconciliation_only: Literal[True] = True
    anchor_is_not_canonical_identity_or_truth: Literal[True] = True

    @model_validator(mode="after")
    def validate_lists(self):
        for values, label in [
            (self.provenance_refs, "provenance_refs"),
            (self.qualification_refs, "qualification_refs"),
            (self.unresolved_refs, "unresolved_refs"),
        ]:
            if len(values) != len(set(values)):
                raise ValueError(f"{label} must be unique")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class SemanticCorrespondenceCandidate(BaseModel):
    candidate_id: str = Field(min_length=3, max_length=500)
    left_anchor_ref: str = Field(min_length=3, max_length=500)
    right_anchor_ref: str = Field(min_length=3, max_length=500)
    dimensions: list[ReconciliationDimension] = Field(min_length=1)
    proposed_relation: ReconciliationRelation
    advisory_score: float = Field(ge=0.0, le=1.0)
    rationale: str = Field(min_length=3, max_length=4000)
    qualification_refs: list[str] = Field(default_factory=list)
    unresolved_refs: list[str] = Field(default_factory=list)
    requires_review: Literal[True] = True
    candidate_establishes_truth: Literal[False] = False
    candidate_establishes_identity: Literal[False] = False
    candidate_establishes_equivalence: Literal[False] = False

    @model_validator(mode="after")
    def validate_candidate(self):
        if self.left_anchor_ref == self.right_anchor_ref:
            raise ValueError("candidate requires distinct anchors")
        if len(self.dimensions) != len(set(self.dimensions)):
            raise ValueError("candidate dimensions must be unique")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class ReconciliationConflict(BaseModel):
    conflict_id: str = Field(min_length=3, max_length=500)
    kind: ReconciliationConflictKind
    candidate_refs: list[str] = Field(min_length=1)
    affected_anchor_refs: list[str] = Field(min_length=2)
    description: str = Field(min_length=3, max_length=4000)
    qualification_refs: list[str] = Field(default_factory=list)
    unresolved_refs: list[str] = Field(default_factory=list)
    resolved: bool = False
    resolution_note: str | None = Field(default=None, max_length=3000)
    conflict_is_not_truth_adjudication: Literal[True] = True

    @model_validator(mode="after")
    def validate_conflict(self):
        if len(self.candidate_refs) != len(set(self.candidate_refs)):
            raise ValueError("candidate_refs must be unique")
        if len(self.affected_anchor_refs) != len(set(self.affected_anchor_refs)):
            raise ValueError("affected_anchor_refs must be unique")
        if self.resolved and not self.resolution_note:
            raise ValueError("resolved conflict requires resolution_note")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class ReconciliationDecision(BaseModel):
    decision_id: str = Field(min_length=3, max_length=500)
    candidate_ref: str = Field(min_length=3, max_length=500)
    selected_relation: ReconciliationRelation
    state: ReconciliationReviewState
    reviewer_ref: str | None = Field(default=None, max_length=500)
    rationale: str = Field(min_length=3, max_length=4000)
    qualification_refs: list[str] = Field(default_factory=list)
    unresolved_refs: list[str] = Field(default_factory=list)
    canonicalization_authorized: Literal[False] = False
    identity_merge_authorized: Literal[False] = False
    evidence_promotion_authorized: Literal[False] = False
    truth_verdict: Literal[False] = False

    @model_validator(mode="after")
    def validate_decision(self):
        if self.state in {
            ReconciliationReviewState.reviewed,
            ReconciliationReviewState.accepted,
            ReconciliationReviewState.rejected,
            ReconciliationReviewState.unresolved,
        } and not self.reviewer_ref:
            raise ValueError("reviewed decision state requires reviewer_ref")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class ReconciledSemanticCluster(BaseModel):
    cluster_id: str = Field(min_length=3, max_length=500)
    kind: ReconciledClusterKind
    label: str = Field(min_length=3, max_length=1500)
    member_anchor_refs: list[str] = Field(min_length=2)
    decision_refs: list[str] = Field(min_length=1)
    conflict_refs: list[str] = Field(default_factory=list)
    derived_member_refs: list[str] = Field(default_factory=list)
    qualification_refs: list[str] = Field(default_factory=list)
    unresolved_refs: list[str] = Field(default_factory=list)
    cluster_is_navigation_object_not_canonical_entity: Literal[True] = True
    cluster_establishes_equivalence: Literal[False] = False
    cluster_establishes_truth: Literal[False] = False

    @model_validator(mode="after")
    def validate_cluster(self):
        for values, label in [
            (self.member_anchor_refs, "member_anchor_refs"),
            (self.decision_refs, "decision_refs"),
            (self.conflict_refs, "conflict_refs"),
            (self.derived_member_refs, "derived_member_refs"),
        ]:
            if len(values) != len(set(values)):
                raise ValueError(f"{label} must be unique")
        if not set(self.derived_member_refs).issubset(self.member_anchor_refs):
            raise ValueError("derived members must be cluster members")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class CrossSourceReconciliationProvenanceRecord(BaseModel):
    provenance_id: str = Field(min_length=3, max_length=500)
    predecessor_framing_fingerprint_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    subject_refs: list[str] = Field(min_length=1)
    method: str = Field(min_length=3, max_length=4000)
    provenance_is_not_source_credibility_or_truth_assessment: Literal[True] = True

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class CrossSourceReconciliationSnapshot(BaseModel):
    snapshot_id: str = Field(min_length=3, max_length=500)
    predecessor_framing_fingerprint_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    anchor_fingerprints: dict[str, str]
    candidate_fingerprints: dict[str, str]
    conflict_fingerprints: dict[str, str]
    decision_fingerprints: dict[str, str]
    cluster_fingerprints: dict[str, str]
    deterministic_reconciliation_fingerprint_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    supersedable: Literal[True] = True
    snapshot_is_not_truth_identity_or_equivalence_certification: Literal[True] = True

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class CrossSourceSemanticReconciliationBundle(BaseModel):
    release: Literal["4.17.0"] = "4.17.0"
    contract: Literal[CONTRACT_VERSION] = CONTRACT_VERSION
    predecessor_contract: Literal[PREDECESSOR_CONTRACT] = PREDECESSOR_CONTRACT
    policy: CrossSourceReconciliationPolicy
    predecessor_framing_context: NarrativeFramingPerspectiveBundle
    anchors: list[ReconciliationAnchor] = Field(min_length=1)
    candidates: list[SemanticCorrespondenceCandidate] = Field(min_length=1)
    conflicts: list[ReconciliationConflict] = Field(min_length=1)
    decisions: list[ReconciliationDecision] = Field(min_length=1)
    clusters: list[ReconciledSemanticCluster] = Field(min_length=1)
    provenance_records: list[CrossSourceReconciliationProvenanceRecord] = Field(min_length=1)
    snapshots: list[CrossSourceReconciliationSnapshot] = Field(min_length=1)
    database_migration: Literal["none"] = "none"

    @model_validator(mode="after")
    def validate_bundle(self):
        pred = self.predecessor_framing_context
        if pred.release != "4.16.0" or pred.contract != PREDECESSOR_CONTRACT:
            raise ValueError("v4.17 must preserve governed v4.16 framing predecessor")

        def unique(values: list[str], label: str):
            if len(values) != len(set(values)):
                raise ValueError(f"{label} must be unique")

        unique([x.anchor_id for x in self.anchors], "anchor ids")
        unique([x.candidate_id for x in self.candidates], "candidate ids")
        unique([x.conflict_id for x in self.conflicts], "conflict ids")
        unique([x.decision_id for x in self.decisions], "decision ids")
        unique([x.cluster_id for x in self.clusters], "cluster ids")
        unique([x.provenance_id for x in self.provenance_records], "provenance ids")
        unique([x.snapshot_id for x in self.snapshots], "snapshot ids")

        causal = pred.predecessor_causal_context
        claim_bundle = causal.predecessor_evidence_context.predecessor_claim_comparison
        retrieval = claim_bundle.predecessor_retrieval
        memory = retrieval.predecessor_memory
        claims = {x.claim_id: x for x in claim_bundle.claims}
        perspectives = {x.perspective_id: x for x in pred.perspectives}
        frames = {x.frame_id: x for x in pred.frames}
        memories = {x.memory_id: x for x in memory.memories}
        anchors = {x.anchor_id: x for x in self.anchors}
        candidates = {x.candidate_id: x for x in self.candidates}
        conflicts = {x.conflict_id: x for x in self.conflicts}
        decisions = {x.decision_id: x for x in self.decisions}

        source_maps = {
            "claim": claims,
            "perspective": perspectives,
            "frame": frames,
            "memory": memories,
        }
        for anchor in self.anchors:
            if anchor.source_ref not in source_maps[anchor.source_type]:
                raise ValueError("anchor source_ref must resolve in governed predecessor")
            if anchor.source_type == "claim":
                c = claims[anchor.source_ref]
                if anchor.language_tag != c.language_tag:
                    raise ValueError("claim anchor language must match predecessor")
                if c.source_context_ref.endswith("en-derived") and not anchor.derived_representation:
                    raise ValueError("derived claim source must remain derived")
            if anchor.source_type == "perspective":
                p = perspectives[anchor.source_ref]
                if anchor.language_tag != p.language_tag:
                    raise ValueError("perspective anchor language must match predecessor")
                if p.derived_representation and not anchor.derived_representation:
                    raise ValueError("derived perspective must remain derived")

        for c in self.candidates:
            if c.left_anchor_ref not in anchors or c.right_anchor_ref not in anchors:
                raise ValueError("candidate anchor refs must resolve")
            left, right = anchors[c.left_anchor_ref], anchors[c.right_anchor_ref]
            if c.proposed_relation == ReconciliationRelation.translation_derived_correspondence:
                if not (left.derived_representation or right.derived_representation):
                    raise ValueError("translation-derived correspondence requires derived member")
                if ReconciliationDimension.translation_lineage not in c.dimensions:
                    raise ValueError("translation-derived correspondence requires translation-lineage dimension")
            if c.proposed_relation == ReconciliationRelation.actor_continuity_candidate:
                if left.kind != ReconciliationAnchorKind.actor_reference or right.kind != ReconciliationAnchorKind.actor_reference:
                    raise ValueError("actor continuity requires actor anchors")
            if c.proposed_relation == ReconciliationRelation.deictic_grounding:
                if left.kind != ReconciliationAnchorKind.spatial_reference or right.kind != ReconciliationAnchorKind.spatial_reference:
                    raise ValueError("deictic grounding requires spatial anchors")

        for conflict in self.conflicts:
            if not set(conflict.candidate_refs).issubset(candidates):
                raise ValueError("conflict candidate refs must resolve")
            if not set(conflict.affected_anchor_refs).issubset(anchors):
                raise ValueError("conflict anchor refs must resolve")

        for d in self.decisions:
            if d.candidate_ref not in candidates:
                raise ValueError("decision candidate_ref must resolve")
            if d.selected_relation != candidates[d.candidate_ref].proposed_relation:
                raise ValueError("reference decision must preserve reviewed proposed relation")
            if d.state == ReconciliationReviewState.accepted:
                cand = candidates[d.candidate_ref]
                if cand.proposed_relation in {
                    ReconciliationRelation.same_semantic_target_conflicting,
                    ReconciliationRelation.actor_continuity_candidate,
                    ReconciliationRelation.unresolved,
                }:
                    raise ValueError("unresolved/conflicting relation cannot be accepted")

        for cluster in self.clusters:
            if not set(cluster.member_anchor_refs).issubset(anchors):
                raise ValueError("cluster member refs must resolve")
            if not set(cluster.decision_refs).issubset(decisions):
                raise ValueError("cluster decision refs must resolve")
            if not set(cluster.conflict_refs).issubset(conflicts):
                raise ValueError("cluster conflict refs must resolve")
            if any(not anchors[x].derived_representation for x in cluster.derived_member_refs):
                raise ValueError("derived_member_refs must point to derived anchors")

        pred_fp = pred.fingerprint()
        all_subjects = set(anchors) | set(candidates) | set(conflicts) | set(decisions) | {x.cluster_id for x in self.clusters}
        for p in self.provenance_records:
            if p.predecessor_framing_fingerprint_sha256 != pred_fp:
                raise ValueError("provenance predecessor fingerprint must match v4.16")
            if not set(p.subject_refs).issubset(all_subjects):
                raise ValueError("provenance subject refs must resolve")

        expected_a = {x.anchor_id: x.fingerprint() for x in self.anchors}
        expected_c = {x.candidate_id: x.fingerprint() for x in self.candidates}
        expected_f = {x.conflict_id: x.fingerprint() for x in self.conflicts}
        expected_d = {x.decision_id: x.fingerprint() for x in self.decisions}
        expected_cl = {x.cluster_id: x.fingerprint() for x in self.clusters}
        material = {
            "predecessor": pred_fp,
            "anchors": expected_a,
            "candidates": expected_c,
            "conflicts": expected_f,
            "decisions": expected_d,
            "clusters": expected_cl,
        }
        for snap in self.snapshots:
            if snap.predecessor_framing_fingerprint_sha256 != pred_fp:
                raise ValueError("snapshot predecessor fingerprint must match v4.16")
            if snap.anchor_fingerprints != expected_a:
                raise ValueError("snapshot anchor fingerprints must be exact")
            if snap.candidate_fingerprints != expected_c:
                raise ValueError("snapshot candidate fingerprints must be exact")
            if snap.conflict_fingerprints != expected_f:
                raise ValueError("snapshot conflict fingerprints must be exact")
            if snap.decision_fingerprints != expected_d:
                raise ValueError("snapshot decision fingerprints must be exact")
            if snap.cluster_fingerprints != expected_cl:
                raise ValueError("snapshot cluster fingerprints must be exact")
            if snap.deterministic_reconciliation_fingerprint_sha256 != canonical_sha256(material):
                raise ValueError("snapshot deterministic reconciliation fingerprint must match")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


def _claim_anchor(claim, *, anchor_id: str, label: str | None = None) -> ReconciliationAnchor:
    derived = claim.source_context_ref.endswith("en-derived")
    return ReconciliationAnchor(
        anchor_id=anchor_id,
        kind=ReconciliationAnchorKind.claim,
        source_ref=claim.claim_id,
        source_type="claim",
        source_label=label or claim.source_context_ref,
        language_tag=claim.language_tag,
        surface_form=claim.surface_text,
        semantic_key=f"{claim.subject_key}|{claim.predicate_key}|{claim.object_scope_key}",
        subject_key=claim.subject_key,
        predicate_key=claim.predicate_key,
        temporal_scope_ref=claim.temporal_scope_ref,
        spatial_scope_ref=claim.spatial_scope_ref,
        derived_representation=derived,
        provenance_refs=[claim.source_object_ref, claim.attribution_ref],
        qualification_refs=list(claim.qualification_refs) + (["translation-derived"] if derived else []),
        unresolved_refs=list(claim.unresolved_refs),
    )


@lru_cache(maxsize=1)
def reference_cross_source_semantic_reconciliation_bundle() -> CrossSourceSemanticReconciliationBundle:
    pred = reference_narrative_framing_perspective_bundle()
    claim_bundle = pred.predecessor_causal_context.predecessor_evidence_context.predecessor_claim_comparison
    memory = claim_bundle.predecessor_retrieval.predecessor_memory
    claims = {x.claim_id: x for x in claim_bundle.claims}

    anchors = [
        _claim_anchor(claims["claim:v45:measure-no-emissions-reduction"], anchor_id="anchor:claim:report-emissions-negative", label="v4.5 report"),
        _claim_anchor(claims["claim:v46:measure-may-reduce-emissions"], anchor_id="anchor:claim:agency-emissions-possible", label="v4.6 agency statement"),
        _claim_anchor(claims["claim:v413:audit-reduced-emissions"], anchor_id="anchor:claim:audit-emissions-positive", label="v4.13 audit"),
        _claim_anchor(claims["claim:v413:review-no-direct-emissions-reduction"], anchor_id="anchor:claim:review-direct-emissions-negative", label="v4.13 review"),
        _claim_anchor(claims["claim:v45:proposal-may-lower-costs"], anchor_id="anchor:claim:report-cost-possible", label="v4.5 report"),
        _claim_anchor(claims["claim:v48:zh-proposal-may-lower-costs"], anchor_id="anchor:claim:zh-cost-possible", label="v4.8 Chinese original"),
        _claim_anchor(claims["claim:v48:en-proposal-may-reduce-costs"], anchor_id="anchor:claim:en-derived-cost-possible", label="v4.8 English derived"),
        ReconciliationAnchor(anchor_id="anchor:actor:ministry", kind=ReconciliationAnchorKind.actor_reference, source_ref="memory:continuity:actor-ministry-agency", source_type="memory", source_label="Cross-document actor continuity memory", language_tag="en", surface_form="Ministry", semantic_key="actor:ministry", provenance_refs=["runtime-artifact:stage:07:reference"], qualification_refs=["qualification:07:continuity-hypothesis-unresolved"], unresolved_refs=["thread:actor-continuity:candidate"]),
        ReconciliationAnchor(anchor_id="anchor:actor:agency", kind=ReconciliationAnchorKind.actor_reference, source_ref="memory:continuity:actor-ministry-agency", source_type="memory", source_label="Cross-document actor continuity memory", language_tag="en", surface_form="agency", semantic_key="actor:agency", provenance_refs=["runtime-artifact:stage:07:reference"], qualification_refs=["qualification:07:continuity-hypothesis-unresolved"], unresolved_refs=["thread:actor-continuity:candidate"]),
        ReconciliationAnchor(anchor_id="anchor:term:zh-governance", kind=ReconciliationAnchorKind.terminology, source_ref="memory:multilingual-divergence:governance", source_type="memory", source_label="Governance multilingual divergence memory", language_tag="zh", surface_form="治理", semantic_key="governance-concept:zh", provenance_refs=["runtime-artifact:stage:08:reference"], qualification_refs=["qualification:08:cultural-divergence-preserved"], unresolved_refs=["universal-equivalence:治理-governance-gobernanza"]),
        ReconciliationAnchor(anchor_id="anchor:term:en-governance", kind=ReconciliationAnchorKind.terminology, source_ref="memory:multilingual-divergence:governance", source_type="memory", source_label="Governance multilingual divergence memory", language_tag="en", surface_form="governance", semantic_key="governance-concept:en", provenance_refs=["runtime-artifact:stage:08:reference"], qualification_refs=["qualification:08:cultural-divergence-preserved"], unresolved_refs=["universal-equivalence:治理-governance-gobernanza"]),
        ReconciliationAnchor(anchor_id="anchor:term:es-gobernanza", kind=ReconciliationAnchorKind.terminology, source_ref="memory:multilingual-divergence:governance", source_type="memory", source_label="Governance multilingual divergence memory", language_tag="es", surface_form="gobernanza", semantic_key="governance-concept:es", provenance_refs=["runtime-artifact:stage:08:reference"], qualification_refs=["qualification:08:cultural-divergence-preserved"], unresolved_refs=["universal-equivalence:治理-governance-gobernanza"]),
        ReconciliationAnchor(anchor_id="anchor:spatial:brussels", kind=ReconciliationAnchorKind.spatial_reference, source_ref="memory:geographic-grounding:brussels", source_type="memory", source_label="Brussels source-place memory", language_tag="en", surface_form="Brussels", semantic_key="spatial-anchor:brussels-source-place", spatial_scope_ref="spatial-anchor:brussels-source-place", provenance_refs=["runtime-artifact:stage:04:reference"], qualification_refs=["qualification:04:geographic-identity-deferred"], unresolved_refs=["spatial-anchor:brussels-source-place"]),
        ReconciliationAnchor(anchor_id="anchor:spatial:there", kind=ReconciliationAnchorKind.spatial_reference, source_ref="memory:geographic-grounding:brussels", source_type="memory", source_label="Spatial-deictic grounding memory", language_tag="en", surface_form="there", semantic_key="spatial-anchor:brussels-source-place", spatial_scope_ref="spatial-anchor:brussels-source-place", provenance_refs=["runtime-artifact:stage:04:reference"], qualification_refs=["qualification:04:geographic-identity-deferred"], unresolved_refs=["spatial-anchor:brussels-source-place"]),
        ReconciliationAnchor(anchor_id="anchor:temporal:report-evaluation-period", kind=ReconciliationAnchorKind.temporal_scope, source_ref="claim:v45:measure-no-emissions-reduction", source_type="claim", source_label="Report evaluation-period scope", language_tag="en", surface_form="reference evaluation period", semantic_key="temporal-scope:reference-evaluation-period", temporal_scope_ref="temporal-scope:reference-evaluation-period", provenance_refs=["proposition:measure-no-emissions-reduction"], qualification_refs=["qualification:05:source-uncertainty-preserved"], unresolved_refs=["same-period:reference-corpus"]),
        ReconciliationAnchor(anchor_id="anchor:temporal:audit-evaluation-period", kind=ReconciliationAnchorKind.temporal_scope, source_ref="claim:v413:audit-reduced-emissions", source_type="claim", source_label="Audit evaluation-period scope", language_tag="en", surface_form="reference evaluation period", semantic_key="temporal-scope:reference-evaluation-period", temporal_scope_ref="temporal-scope:reference-evaluation-period", provenance_refs=["fixture-claim:audit-reduced-emissions"], qualification_refs=["qualification:05:source-uncertainty-preserved"], unresolved_refs=["same-period:reference-corpus"]),
    ]

    candidates = [
        SemanticCorrespondenceCandidate(candidate_id="candidate:emissions-report-audit", left_anchor_ref="anchor:claim:report-emissions-negative", right_anchor_ref="anchor:claim:audit-emissions-positive", dimensions=[ReconciliationDimension.subject, ReconciliationDimension.predicate, ReconciliationDimension.object_scope, ReconciliationDimension.polarity, ReconciliationDimension.temporal_scope], proposed_relation=ReconciliationRelation.same_semantic_target_conflicting, advisory_score=0.96, rationale="The claims target the same normalized policy-measure/emissions proposition and reference period but assert opposite polarity. Reconciliation preserves the conflict rather than selecting a winner.", qualification_refs=["same-target-not-truth-adjudication"], unresolved_refs=["same-measure:reference-corpus", "same-period:reference-corpus"]),
        SemanticCorrespondenceCandidate(candidate_id="candidate:emissions-audit-review", left_anchor_ref="anchor:claim:audit-emissions-positive", right_anchor_ref="anchor:claim:review-direct-emissions-negative", dimensions=[ReconciliationDimension.subject, ReconciliationDimension.predicate, ReconciliationDimension.object_scope, ReconciliationDimension.temporal_scope], proposed_relation=ReconciliationRelation.scope_overlap, advisory_score=0.84, rationale="Both claims concern emissions in the reference period, but one addresses total/unspecified emissions while the review is limited to direct emissions.", qualification_refs=["scope-preserved"], unresolved_refs=["direct-vs-total-emissions-scope"]),
        SemanticCorrespondenceCandidate(candidate_id="candidate:emissions-report-agency", left_anchor_ref="anchor:claim:report-emissions-negative", right_anchor_ref="anchor:claim:agency-emissions-possible", dimensions=[ReconciliationDimension.subject, ReconciliationDimension.predicate, ReconciliationDimension.modality, ReconciliationDimension.temporal_scope, ReconciliationDimension.framing], proposed_relation=ReconciliationRelation.modality_temporal_related, advisory_score=0.73, rationale="The report is retrospective/asserted while the agency statement is prospective/possible. They are related but should not be reconciled as equivalent or strictly contradictory.", qualification_refs=["modality-and-temporal-scope-preserved"], unresolved_refs=["same-measure:reference-corpus"]),
        SemanticCorrespondenceCandidate(candidate_id="candidate:cost-zh-en-derived", left_anchor_ref="anchor:claim:zh-cost-possible", right_anchor_ref="anchor:claim:en-derived-cost-possible", dimensions=[ReconciliationDimension.subject, ReconciliationDimension.predicate, ReconciliationDimension.modality, ReconciliationDimension.translation_lineage, ReconciliationDimension.source_independence], proposed_relation=ReconciliationRelation.translation_derived_correspondence, advisory_score=0.98, rationale="The English representation is a derived translation counterpart of the Chinese original and preserves possibility semantics, but it is not an independent source.", qualification_refs=["translation-derived-not-independent"], unresolved_refs=["same-policy-object:v48-v47"]),
        SemanticCorrespondenceCandidate(candidate_id="candidate:cost-report-zh", left_anchor_ref="anchor:claim:report-cost-possible", right_anchor_ref="anchor:claim:zh-cost-possible", dimensions=[ReconciliationDimension.subject, ReconciliationDimension.predicate, ReconciliationDimension.modality, ReconciliationDimension.translation_lineage], proposed_relation=ReconciliationRelation.near_equivalent, advisory_score=0.88, rationale="Both claims express possible cost reduction for a policy proposal, but cross-source policy-object identity remains unresolved and wording provenance differs.", qualification_refs=["cross-source-near-equivalence-only"], unresolved_refs=["thread:policy-topic-continuity:candidate", "same-policy-object:v48-v47"]),
        SemanticCorrespondenceCandidate(candidate_id="candidate:actor-ministry-agency", left_anchor_ref="anchor:actor:ministry", right_anchor_ref="anchor:actor:agency", dimensions=[ReconciliationDimension.actor_identity, ReconciliationDimension.source_independence], proposed_relation=ReconciliationRelation.actor_continuity_candidate, advisory_score=0.42, rationale="The predecessor context graph carries a reviewed but unresolved ministry-agency continuity hypothesis. Reconciliation may retain the candidate relationship but cannot canonicalize the actors.", qualification_refs=["qualification:07:continuity-hypothesis-unresolved"], unresolved_refs=["thread:actor-continuity:candidate"]),
        SemanticCorrespondenceCandidate(candidate_id="candidate:term-zh-en-governance", left_anchor_ref="anchor:term:zh-governance", right_anchor_ref="anchor:term:en-governance", dimensions=[ReconciliationDimension.terminology, ReconciliationDimension.translation_lineage], proposed_relation=ReconciliationRelation.culturally_conditioned_correspondence, advisory_score=0.72, rationale="治理 and governance are contextually aligned but culturally conditioned; exact universal equivalence is explicitly not established.", qualification_refs=["qualification:08:cultural-divergence-preserved"], unresolved_refs=["universal-equivalence:治理-governance-gobernanza"]),
        SemanticCorrespondenceCandidate(candidate_id="candidate:term-zh-es-governance", left_anchor_ref="anchor:term:zh-governance", right_anchor_ref="anchor:term:es-gobernanza", dimensions=[ReconciliationDimension.terminology, ReconciliationDimension.translation_lineage], proposed_relation=ReconciliationRelation.culturally_conditioned_correspondence, advisory_score=0.68, rationale="治理 and gobernanza are candidate contextual correspondences with cultural-semantic divergence preserved.", qualification_refs=["qualification:08:cultural-divergence-preserved"], unresolved_refs=["universal-equivalence:治理-governance-gobernanza"]),
        SemanticCorrespondenceCandidate(candidate_id="candidate:spatial-brussels-there", left_anchor_ref="anchor:spatial:brussels", right_anchor_ref="anchor:spatial:there", dimensions=[ReconciliationDimension.spatial_scope], proposed_relation=ReconciliationRelation.deictic_grounding, advisory_score=0.93, rationale="The deictic expression 'there' is grounded to the same source-place anchor as Brussels, while canonical geographic identity remains deferred.", qualification_refs=["qualification:04:geographic-identity-deferred"], unresolved_refs=["spatial-anchor:brussels-source-place"]),
        SemanticCorrespondenceCandidate(candidate_id="candidate:temporal-report-audit-period", left_anchor_ref="anchor:temporal:report-evaluation-period", right_anchor_ref="anchor:temporal:audit-evaluation-period", dimensions=[ReconciliationDimension.temporal_scope], proposed_relation=ReconciliationRelation.temporal_alignment_candidate, advisory_score=0.86, rationale="Both sources use the reference evaluation-period scope, but predecessor claim objects preserve same-period identity as unresolved rather than canonical.", qualification_refs=["temporal-scope-label-aligned"], unresolved_refs=["same-period:reference-corpus"]),
    ]

    conflicts = [
        ReconciliationConflict(conflict_id="conflict:emissions-claim", kind=ReconciliationConflictKind.claim_conflict, candidate_refs=["candidate:emissions-report-audit"], affected_anchor_refs=["anchor:claim:report-emissions-negative", "anchor:claim:audit-emissions-positive"], description="Opposite-polarity claims over the same normalized target remain unresolved; reconciliation does not select a true claim.", unresolved_refs=["same-period:reference-corpus"]),
        ReconciliationConflict(conflict_id="conflict:emissions-scope", kind=ReconciliationConflictKind.scope_divergence, candidate_refs=["candidate:emissions-audit-review"], affected_anchor_refs=["anchor:claim:audit-emissions-positive", "anchor:claim:review-direct-emissions-negative"], description="Total/unspecified emissions and direct-only emissions cannot be collapsed into one scope.", unresolved_refs=["direct-vs-total-emissions-scope"]),
        ReconciliationConflict(conflict_id="conflict:report-agency-modality-time", kind=ReconciliationConflictKind.modality_temporal_divergence, candidate_refs=["candidate:emissions-report-agency"], affected_anchor_refs=["anchor:claim:report-emissions-negative", "anchor:claim:agency-emissions-possible"], description="Retrospective asserted performance and prospective possibility are not equivalent propositions."),
        ReconciliationConflict(conflict_id="conflict:actor-identity", kind=ReconciliationConflictKind.identity_uncertainty, candidate_refs=["candidate:actor-ministry-agency"], affected_anchor_refs=["anchor:actor:ministry", "anchor:actor:agency"], description="Ministry-agency continuity remains a reviewed hypothesis and cannot authorize canonical identity merge.", unresolved_refs=["thread:actor-continuity:candidate"]),
        ReconciliationConflict(conflict_id="conflict:governance-cultural-semantics", kind=ReconciliationConflictKind.cultural_semantic_divergence, candidate_refs=["candidate:term-zh-en-governance", "candidate:term-zh-es-governance"], affected_anchor_refs=["anchor:term:zh-governance", "anchor:term:en-governance", "anchor:term:es-gobernanza"], description="Cross-language governance terms remain culturally conditioned and non-universally equivalent.", qualification_refs=["qualification:08:cultural-divergence-preserved"], unresolved_refs=["universal-equivalence:治理-governance-gobernanza"]),
        ReconciliationConflict(conflict_id="conflict:translation-source-independence", kind=ReconciliationConflictKind.source_independence_constraint, candidate_refs=["candidate:cost-zh-en-derived"], affected_anchor_refs=["anchor:claim:zh-cost-possible", "anchor:claim:en-derived-cost-possible"], description="The English translation is derived from the Chinese source and must not be counted as independent corroboration.", resolved=True, resolution_note="Preserve one source-independence lineage group and mark the English member derived."),
    ]

    reviewer = "reviewer:cross-source-reconciliation-reference"
    decisions = [
        ReconciliationDecision(decision_id="decision:emissions-report-audit", candidate_ref="candidate:emissions-report-audit", selected_relation=ReconciliationRelation.same_semantic_target_conflicting, state=ReconciliationReviewState.unresolved, reviewer_ref=reviewer, rationale="Preserve both claims and the explicit conflict without truth adjudication.", unresolved_refs=["conflict:emissions-claim"]),
        ReconciliationDecision(decision_id="decision:emissions-audit-review", candidate_ref="candidate:emissions-audit-review", selected_relation=ReconciliationRelation.scope_overlap, state=ReconciliationReviewState.reviewed, reviewer_ref=reviewer, rationale="Retain shared topic and time scope while preserving direct-vs-total emissions distinction.", qualification_refs=["scope-preserved"]),
        ReconciliationDecision(decision_id="decision:emissions-report-agency", candidate_ref="candidate:emissions-report-agency", selected_relation=ReconciliationRelation.modality_temporal_related, state=ReconciliationReviewState.reviewed, reviewer_ref=reviewer, rationale="Retain relation as modality/temporal dependent rather than strict contradiction."),
        ReconciliationDecision(decision_id="decision:cost-zh-en-derived", candidate_ref="candidate:cost-zh-en-derived", selected_relation=ReconciliationRelation.translation_derived_correspondence, state=ReconciliationReviewState.reviewed, reviewer_ref=reviewer, rationale="Align derived English representation to Chinese original while preserving source dependence.", qualification_refs=["translation-derived-not-independent"]),
        ReconciliationDecision(decision_id="decision:cost-report-zh", candidate_ref="candidate:cost-report-zh", selected_relation=ReconciliationRelation.near_equivalent, state=ReconciliationReviewState.reviewed, reviewer_ref=reviewer, rationale="Retain near-equivalence with policy-object identity unresolved.", unresolved_refs=["same-policy-object:v48-v47"]),
        ReconciliationDecision(decision_id="decision:actor-ministry-agency", candidate_ref="candidate:actor-ministry-agency", selected_relation=ReconciliationRelation.actor_continuity_candidate, state=ReconciliationReviewState.unresolved, reviewer_ref=reviewer, rationale="Carry forward the continuity candidate; no identity merge is authorized.", unresolved_refs=["thread:actor-continuity:candidate"]),
        ReconciliationDecision(decision_id="decision:term-zh-en", candidate_ref="candidate:term-zh-en-governance", selected_relation=ReconciliationRelation.culturally_conditioned_correspondence, state=ReconciliationReviewState.reviewed, reviewer_ref=reviewer, rationale="Preserve contextual correspondence and cultural divergence; reject universal equivalence."),
        ReconciliationDecision(decision_id="decision:term-zh-es", candidate_ref="candidate:term-zh-es-governance", selected_relation=ReconciliationRelation.culturally_conditioned_correspondence, state=ReconciliationReviewState.reviewed, reviewer_ref=reviewer, rationale="Preserve candidate correspondence and cultural divergence; reject universal equivalence."),
        ReconciliationDecision(decision_id="decision:spatial-brussels-there", candidate_ref="candidate:spatial-brussels-there", selected_relation=ReconciliationRelation.deictic_grounding, state=ReconciliationReviewState.reviewed, reviewer_ref=reviewer, rationale="Retain deictic grounding to the source-place anchor while canonical geography remains deferred."),
        ReconciliationDecision(decision_id="decision:temporal-report-audit", candidate_ref="candidate:temporal-report-audit-period", selected_relation=ReconciliationRelation.temporal_alignment_candidate, state=ReconciliationReviewState.unresolved, reviewer_ref=reviewer, rationale="The scope labels align, but same-period identity remains unresolved by predecessor semantics.", unresolved_refs=["same-period:reference-corpus"]),
    ]

    clusters = [
        ReconciledSemanticCluster(cluster_id="cluster:emissions-policy-measure", kind=ReconciledClusterKind.claim_family, label="Policy-measure emissions claim family", member_anchor_refs=["anchor:claim:report-emissions-negative", "anchor:claim:agency-emissions-possible", "anchor:claim:audit-emissions-positive", "anchor:claim:review-direct-emissions-negative"], decision_refs=["decision:emissions-report-audit", "decision:emissions-audit-review", "decision:emissions-report-agency"], conflict_refs=["conflict:emissions-claim", "conflict:emissions-scope", "conflict:report-agency-modality-time"], qualification_refs=["claim-family-does-not-collapse-propositions"], unresolved_refs=["same-measure:reference-corpus", "same-period:reference-corpus", "direct-vs-total-emissions-scope"]),
        ReconciledSemanticCluster(cluster_id="cluster:proposal-cost", kind=ReconciledClusterKind.claim_family, label="Policy-proposal cost claim family", member_anchor_refs=["anchor:claim:report-cost-possible", "anchor:claim:zh-cost-possible", "anchor:claim:en-derived-cost-possible"], decision_refs=["decision:cost-zh-en-derived", "decision:cost-report-zh"], conflict_refs=["conflict:translation-source-independence"], derived_member_refs=["anchor:claim:en-derived-cost-possible"], qualification_refs=["original-language-authority-preserved"], unresolved_refs=["same-policy-object:v48-v47"]),
        ReconciledSemanticCluster(cluster_id="cluster:actor-ministry-agency", kind=ReconciledClusterKind.actor_family, label="Ministry / agency actor continuity family", member_anchor_refs=["anchor:actor:ministry", "anchor:actor:agency"], decision_refs=["decision:actor-ministry-agency"], conflict_refs=["conflict:actor-identity"], qualification_refs=["qualification:07:continuity-hypothesis-unresolved"], unresolved_refs=["thread:actor-continuity:candidate"]),
        ReconciledSemanticCluster(cluster_id="cluster:governance-terminology", kind=ReconciledClusterKind.terminology_family, label="治理 / governance / gobernanza contextual terminology family", member_anchor_refs=["anchor:term:zh-governance", "anchor:term:en-governance", "anchor:term:es-gobernanza"], decision_refs=["decision:term-zh-en", "decision:term-zh-es"], conflict_refs=["conflict:governance-cultural-semantics"], qualification_refs=["qualification:08:cultural-divergence-preserved"], unresolved_refs=["universal-equivalence:治理-governance-gobernanza"]),
        ReconciledSemanticCluster(cluster_id="cluster:brussels-deictic", kind=ReconciledClusterKind.spatial_family, label="Brussels / there source-place grounding family", member_anchor_refs=["anchor:spatial:brussels", "anchor:spatial:there"], decision_refs=["decision:spatial-brussels-there"], qualification_refs=["qualification:04:geographic-identity-deferred"], unresolved_refs=["spatial-anchor:brussels-source-place"]),
        ReconciledSemanticCluster(cluster_id="cluster:reference-evaluation-period", kind=ReconciledClusterKind.temporal_family, label="Reference evaluation-period scope family", member_anchor_refs=["anchor:temporal:report-evaluation-period", "anchor:temporal:audit-evaluation-period"], decision_refs=["decision:temporal-report-audit"], unresolved_refs=["same-period:reference-corpus"]),
    ]

    subjects = [x.anchor_id for x in anchors] + [x.candidate_id for x in candidates] + [x.conflict_id for x in conflicts] + [x.decision_id for x in decisions] + [x.cluster_id for x in clusters]
    provenance = CrossSourceReconciliationProvenanceRecord(
        provenance_id="cross-source-reconciliation-provenance:reference",
        predecessor_framing_fingerprint_sha256=pred.fingerprint(),
        subject_refs=subjects,
        method="Governed cross-source semantic reconciliation over v4.16 framing plus preserved v4.13-v4.11 claim, retrieval, memory, multilingual, temporal, spatial, causal, and evidence context. Candidate generation is advisory; review preserves conflicts, scope/modality differences, source independence, original-language authority, identity uncertainty, and non-mutating graph boundaries.",
    )
    material = {
        "predecessor": pred.fingerprint(),
        "anchors": {x.anchor_id: x.fingerprint() for x in anchors},
        "candidates": {x.candidate_id: x.fingerprint() for x in candidates},
        "conflicts": {x.conflict_id: x.fingerprint() for x in conflicts},
        "decisions": {x.decision_id: x.fingerprint() for x in decisions},
        "clusters": {x.cluster_id: x.fingerprint() for x in clusters},
    }
    snapshot = CrossSourceReconciliationSnapshot(
        snapshot_id="cross-source-reconciliation-snapshot:reference:v1",
        predecessor_framing_fingerprint_sha256=pred.fingerprint(),
        anchor_fingerprints=material["anchors"],
        candidate_fingerprints=material["candidates"],
        conflict_fingerprints=material["conflicts"],
        decision_fingerprints=material["decisions"],
        cluster_fingerprints=material["clusters"],
        deterministic_reconciliation_fingerprint_sha256=canonical_sha256(material),
    )
    return CrossSourceSemanticReconciliationBundle(
        policy=CrossSourceReconciliationPolicy(policy_id="cross-source-semantic-reconciliation-policy:v1"),
        predecessor_framing_context=pred,
        anchors=anchors,
        candidates=candidates,
        conflicts=conflicts,
        decisions=decisions,
        clusters=clusters,
        provenance_records=[provenance],
        snapshots=[snapshot],
    )


def contract_document() -> dict:
    b = reference_cross_source_semantic_reconciliation_bundle()
    return {
        "ok": True,
        "release": CORE_RELEASE,
        "contract": CONTRACT_VERSION,
        "predecessor_contract": PREDECESSOR_CONTRACT,
        "identity": {"product": "Sustainable Catalyst Platform Core", "build": "Cross-Source Semantic Reconciliation Engine", "major_api": "v4"},
        "principles": {
            "reconciliation_is_alignment_not_canonicalization": True,
            "same_surface_form_is_not_same_entity": True,
            "source_agreement_is_not_truth": True,
            "temporal_overlap_is_not_same_event": True,
            "spatial_grounding_is_not_canonical_geographic_identity": True,
            "original_language_remains_authoritative": True,
            "translation_remains_derived": True,
            "derived_representation_is_not_independent_source": True,
            "unresolved_identity_and_conflict_are_preserved": True,
        },
        "boundaries": {
            "reconciliation_score_establishes_truth": False,
            "reconciliation_score_establishes_identity": False,
            "reconciliation_score_establishes_equivalence": False,
            "automatic_canonical_entity_merge_performed": False,
            "automatic_context_graph_mutation_performed": False,
            "automatic_evidence_graph_mutation_performed": False,
            "automatic_knowledge_graph_mutation_performed": False,
            "automatic_identity_graph_mutation_performed": False,
        },
        "roadmap_integration": {
            "extends_v4160_narrative_framing_perspective": True,
            "prepares_v4180_contextual_hypothesis_competing_explanations": True,
            "prepares_v4190_semantic_synthesis_research_answer": True,
            "prepares_v4200_unified_contextual_reasoning_runtime": True,
        },
        "reference": {
            "predecessor_release": b.predecessor_framing_context.release,
            "predecessor_fingerprint_sha256": b.predecessor_framing_context.fingerprint(),
            "anchors": len(b.anchors),
            "correspondence_candidates": len(b.candidates),
            "conflicts": len(b.conflicts),
            "review_decisions": len(b.decisions),
            "semantic_clusters": len(b.clusters),
            "unresolved_decisions": sum(x.state == ReconciliationReviewState.unresolved for x in b.decisions),
            "derived_anchors": sum(x.derived_representation for x in b.anchors),
            "resolved_source_independence_conflicts": sum(x.kind == ReconciliationConflictKind.source_independence_constraint and x.resolved for x in b.conflicts),
            "snapshots": len(b.snapshots),
            "bundle_fingerprint_sha256": b.fingerprint(),
        },
        "database_migration": "none",
    }
