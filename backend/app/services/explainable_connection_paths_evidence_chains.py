from __future__ import annotations

from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field, model_validator

from .computational_runtime_objects import canonical_sha256
from .network_structure_community_motif import (
    NetworkEdgeEpistemicState,
    NetworkStructureCommunityMotifBundle,
    reference_network_structure_community_motif_bundle,
)

CORE_RELEASE = "3.84.0"
CONTRACT_VERSION = "sc.core.explainable-connection-paths-evidence-chains.v1"


def _unique(values: list[str], label: str) -> None:
    if len(values) != len(set(values)):
        raise ValueError(f"{label} must be unique")


class EvidenceChainPosition(str, Enum):
    supports = "supports"
    contradicts = "contradicts"
    contextualizes = "contextualizes"
    qualifies = "qualifies"
    unresolved = "unresolved"


class PathBottleneckKind(str, Enum):
    provenance_gap = "provenance-gap"
    source_dependence = "source-dependence"
    epistemic_uncertainty = "epistemic-uncertainty"
    unresolved_contradiction = "unresolved-contradiction"
    unvalidated_hypothesis = "unvalidated-hypothesis"
    documentary_gap = "documentary-gap"
    custom = "custom"


class ConnectionPathPolicy(BaseModel):
    connection_path_policy_id: str = Field(min_length=2, max_length=500)
    require_immutable_network_snapshot: Literal[True] = True
    require_step_epistemic_state: Literal[True] = True
    require_step_provenance: Literal[True] = True
    require_documentary_anchor_when_available: Literal[True] = True
    require_evidence_position_provenance: Literal[True] = True
    preserve_source_independence_groups: Literal[True] = True
    preserve_contradictions: Literal[True] = True
    preserve_alternative_paths: Literal[True] = True
    shortest_path_can_establish_strongest_evidence: Literal[False] = False
    path_length_can_establish_causal_distance: Literal[False] = False
    multiple_paths_can_establish_independent_corroboration: Literal[False] = False
    path_existence_can_establish_relationship_truth: Literal[False] = False
    missing_path_can_establish_no_relationship: Literal[False] = False
    metadata: dict[str, Any] = Field(default_factory=dict)

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class ConnectionPathStep(BaseModel):
    connection_path_step_id: str = Field(min_length=2, max_length=500)
    sequence_index: int = Field(ge=0)
    from_entity_ref: str = Field(min_length=2, max_length=1000)
    to_entity_ref: str = Field(min_length=2, max_length=1000)
    network_edge_projection_ref: str = Field(min_length=2, max_length=500)
    epistemic_state: NetworkEdgeEpistemicState
    documentary_segment_refs: list[str] = Field(default_factory=list)
    documentary_interpretation_refs: list[str] = Field(default_factory=list)
    relationship_evidence_position_refs: list[str] = Field(default_factory=list)
    provenance_refs: list[str] = Field(min_length=1)
    explanation: str = Field(min_length=1, max_length=8000)
    step_is_not_relationship_fact: Literal[True] = True
    step_is_not_causal_claim: Literal[True] = True
    analytical_path_inclusion_does_not_promote_edge: Literal[True] = True
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_step(self):
        if self.from_entity_ref == self.to_entity_ref:
            raise ValueError("connection path step requires distinct entity endpoints")
        for values, label in (
            (self.documentary_segment_refs, "documentary_segment_refs"),
            (self.documentary_interpretation_refs, "documentary_interpretation_refs"),
            (self.relationship_evidence_position_refs, "relationship_evidence_position_refs"),
            (self.provenance_refs, "provenance_refs"),
        ):
            _unique(values, label)
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class ExplainableConnectionPath(BaseModel):
    connection_path_id: str = Field(min_length=2, max_length=500)
    network_structure_snapshot_ref: str = Field(min_length=2, max_length=500)
    connection_path_policy_ref: str = Field(min_length=2, max_length=500)
    start_entity_ref: str = Field(min_length=2, max_length=1000)
    end_entity_ref: str = Field(min_length=2, max_length=1000)
    step_refs: list[str] = Field(min_length=1)
    algorithm_name: str = Field(min_length=1, max_length=500)
    algorithm_version: str | None = Field(default=None, max_length=200)
    parameters: dict[str, Any] = Field(default_factory=dict)
    path_score: float | None = None
    path_score_semantics: str | None = Field(default=None, max_length=2000)
    explanation: str = Field(min_length=1, max_length=12000)
    created_at: str = Field(min_length=10, max_length=80)
    immutable_path: Literal[True] = True
    path_is_explanation_not_truth_verdict: Literal[True] = True
    shortest_path_is_not_strongest_evidence: Literal[True] = True
    path_length_is_not_causal_distance: Literal[True] = True
    path_does_not_mutate_graphs: Literal[True] = True
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_path(self):
        if self.start_entity_ref == self.end_entity_ref:
            raise ValueError("connection path requires distinct start/end entities")
        _unique(self.step_refs, "step_refs")
        if self.path_score is not None and not self.path_score_semantics:
            raise ValueError("scored connection path requires path_score_semantics")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class EvidenceChainItem(BaseModel):
    evidence_chain_item_id: str = Field(min_length=2, max_length=500)
    connection_path_ref: str = Field(min_length=2, max_length=500)
    path_step_ref: str = Field(min_length=2, max_length=500)
    sequence_index: int = Field(ge=0)
    position: EvidenceChainPosition
    documentary_segment_refs: list[str] = Field(default_factory=list)
    documentary_interpretation_refs: list[str] = Field(default_factory=list)
    relationship_evidence_position_refs: list[str] = Field(default_factory=list)
    source_refs: list[str] = Field(default_factory=list)
    independence_group: str = Field(min_length=1, max_length=1000)
    explanation: str = Field(min_length=1, max_length=8000)
    provenance_refs: list[str] = Field(min_length=1)
    item_is_not_truth_verdict: Literal[True] = True
    source_count_is_not_evidence_strength: Literal[True] = True
    source_repetition_is_not_independent_corroboration: Literal[True] = True
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_item(self):
        for values, label in (
            (self.documentary_segment_refs, "documentary_segment_refs"),
            (self.documentary_interpretation_refs, "documentary_interpretation_refs"),
            (self.relationship_evidence_position_refs, "relationship_evidence_position_refs"),
            (self.source_refs, "source_refs"),
            (self.provenance_refs, "provenance_refs"),
        ):
            _unique(values, label)
        if not (
            self.documentary_segment_refs
            or self.documentary_interpretation_refs
            or self.relationship_evidence_position_refs
        ):
            raise ValueError("evidence chain item requires provenance-bearing evidence material")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class PathContradictionMarker(BaseModel):
    path_contradiction_marker_id: str = Field(min_length=2, max_length=500)
    connection_path_ref: str = Field(min_length=2, max_length=500)
    affected_step_refs: list[str] = Field(min_length=1)
    affected_chain_item_refs: list[str] = Field(default_factory=list)
    reconciliation_conflict_refs: list[str] = Field(default_factory=list)
    contradiction_summary: str = Field(min_length=1, max_length=8000)
    provenance_refs: list[str] = Field(min_length=1)
    contradiction_does_not_auto_invalidate_path: Literal[True] = True
    contradiction_must_remain_visible: Literal[True] = True
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_marker(self):
        for values, label in (
            (self.affected_step_refs, "affected_step_refs"),
            (self.affected_chain_item_refs, "affected_chain_item_refs"),
            (self.reconciliation_conflict_refs, "reconciliation_conflict_refs"),
            (self.provenance_refs, "provenance_refs"),
        ):
            _unique(values, label)
        if not (self.affected_chain_item_refs or self.reconciliation_conflict_refs):
            raise ValueError("contradiction marker requires chain-item or reconciliation-conflict context")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class EvidenceChain(BaseModel):
    evidence_chain_id: str = Field(min_length=2, max_length=500)
    connection_path_ref: str = Field(min_length=2, max_length=500)
    item_refs: list[str] = Field(min_length=1)
    independence_groups: list[str] = Field(min_length=1)
    contradiction_marker_refs: list[str] = Field(default_factory=list)
    chain_summary: str = Field(min_length=1, max_length=12000)
    created_at: str = Field(min_length=10, max_length=80)
    immutable_chain: Literal[True] = True
    evidence_chain_is_not_truth_verdict: Literal[True] = True
    evidence_chain_length_is_not_strength: Literal[True] = True
    repeated_sources_do_not_create_independence: Literal[True] = True
    chain_does_not_promote_relationships: Literal[True] = True
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_chain(self):
        _unique(self.item_refs, "item_refs")
        _unique(self.independence_groups, "independence_groups")
        _unique(self.contradiction_marker_refs, "contradiction_marker_refs")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class AlternativeConnectionPathComparison(BaseModel):
    alternative_path_comparison_id: str = Field(min_length=2, max_length=500)
    primary_path_ref: str = Field(min_length=2, max_length=500)
    alternative_path_ref: str = Field(min_length=2, max_length=500)
    divergence_step_refs: list[str] = Field(min_length=1)
    comparison_summary: str = Field(min_length=1, max_length=8000)
    shared_source_ancestry: bool = False
    alternative_path_is_not_independent_evidence: Literal[True] = True
    multiple_paths_do_not_establish_truth: Literal[True] = True
    provenance_refs: list[str] = Field(min_length=1)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_comparison(self):
        if self.primary_path_ref == self.alternative_path_ref:
            raise ValueError("alternative path comparison requires two distinct paths")
        _unique(self.divergence_step_refs, "divergence_step_refs")
        _unique(self.provenance_refs, "provenance_refs")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class PathBottleneckRecord(BaseModel):
    path_bottleneck_record_id: str = Field(min_length=2, max_length=500)
    connection_path_ref: str = Field(min_length=2, max_length=500)
    path_step_ref: str = Field(min_length=2, max_length=500)
    bottleneck_kind: PathBottleneckKind
    explanation: str = Field(min_length=1, max_length=8000)
    provenance_refs: list[str] = Field(min_length=1)
    bottleneck_is_not_proof_path_is_false: Literal[True] = True
    bottleneck_is_not_evidence_strength_score: Literal[True] = True
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_record(self):
        _unique(self.provenance_refs, "provenance_refs")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class ConnectionPathEvidenceSnapshot(BaseModel):
    connection_path_evidence_snapshot_id: str = Field(min_length=2, max_length=500)
    network_intelligence_snapshot_ref: str = Field(min_length=2, max_length=500)
    policy_refs: list[str] = Field(min_length=1)
    path_refs: list[str] = Field(min_length=1)
    evidence_chain_refs: list[str] = Field(min_length=1)
    contradiction_marker_refs: list[str] = Field(default_factory=list)
    alternative_path_comparison_refs: list[str] = Field(default_factory=list)
    bottleneck_record_refs: list[str] = Field(default_factory=list)
    created_at: str = Field(min_length=10, max_length=80)
    immutable_snapshot: Literal[True] = True
    snapshot_is_explanatory_not_evidentiary_promotion: Literal[True] = True
    snapshot_does_not_mutate_graphs: Literal[True] = True
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_snapshot(self):
        for field in (
            "policy_refs",
            "path_refs",
            "evidence_chain_refs",
            "contradiction_marker_refs",
            "alternative_path_comparison_refs",
            "bottleneck_record_refs",
        ):
            _unique(getattr(self, field), field)
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class ExplainableConnectionPathsEvidenceChainsBundle(BaseModel):
    network_structure_community_motif_bundle: NetworkStructureCommunityMotifBundle
    policies: list[ConnectionPathPolicy] = Field(min_length=1)
    path_steps: list[ConnectionPathStep] = Field(min_length=1)
    connection_paths: list[ExplainableConnectionPath] = Field(min_length=1)
    evidence_chain_items: list[EvidenceChainItem] = Field(min_length=1)
    contradiction_markers: list[PathContradictionMarker] = Field(default_factory=list)
    evidence_chains: list[EvidenceChain] = Field(min_length=1)
    alternative_path_comparisons: list[AlternativeConnectionPathComparison] = Field(default_factory=list)
    bottleneck_records: list[PathBottleneckRecord] = Field(default_factory=list)
    snapshots: list[ConnectionPathEvidenceSnapshot] = Field(min_length=1)
    path_existence_is_not_relationship_truth: Literal[True] = True
    shortest_path_is_not_strongest_evidence: Literal[True] = True
    path_length_is_not_causal_distance: Literal[True] = True
    multiple_paths_are_not_independent_corroboration: Literal[True] = True
    evidence_chain_is_not_truth_verdict: Literal[True] = True
    missing_path_is_not_no_relationship: Literal[True] = True
    algorithmic_path_selection_is_not_investigator_conclusion: Literal[True] = True
    relationship_graph_mutation_performed: Literal[False] = False
    evidence_graph_mutation_performed: Literal[False] = False
    identity_graph_mutation_performed: Literal[False] = False

    @model_validator(mode="after")
    def validate_bundle(self):
        upstream = self.network_structure_community_motif_bundle
        rel = upstream.relationship_discovery_hypothesis_bundle
        documentary = rel.public_record_documentary_source_bundle
        reconciliation = documentary.cross_source_entity_reconciliation_bundle
        base = reconciliation.probabilistic_record_linkage_bundle.temporal_identity_bundle.entity_resolution_identity_graph_bundle

        def ids(items, attr, label):
            vals = [getattr(x, attr) for x in items]
            _unique(vals, label)
            return set(vals)

        entity_ids = {x.entity_id for x in base.entities}
        edge_by_id = {x.network_edge_projection_id: x for x in upstream.edge_projections}
        network_snapshot_ids = {x.network_structure_snapshot_id for x in upstream.structure_snapshots}
        intelligence_snapshot_ids = {x.network_intelligence_snapshot_id for x in upstream.intelligence_snapshots}
        segment_ids = {x.document_segment_id for x in documentary.segments}
        interpretation_ids = {x.documentary_interpretation_id for x in documentary.evidence_interpretations}
        source_ids = {x.documentary_source_id for x in documentary.documentary_sources}
        evidence_position_ids = {x.evidence_position_id for x in rel.evidence_positions}
        reconciliation_conflict_ids = {x.reconciliation_conflict_id for x in reconciliation.conflicts}

        policy_ids = ids(self.policies, "connection_path_policy_id", "connection_path_policy_ids")
        step_ids = ids(self.path_steps, "connection_path_step_id", "connection_path_step_ids")
        path_ids = ids(self.connection_paths, "connection_path_id", "connection_path_ids")
        item_ids = ids(self.evidence_chain_items, "evidence_chain_item_id", "evidence_chain_item_ids")
        contradiction_ids = ids(self.contradiction_markers, "path_contradiction_marker_id", "path_contradiction_marker_ids")
        chain_ids = ids(self.evidence_chains, "evidence_chain_id", "evidence_chain_ids")
        comparison_ids = ids(self.alternative_path_comparisons, "alternative_path_comparison_id", "alternative_path_comparison_ids")
        bottleneck_ids = ids(self.bottleneck_records, "path_bottleneck_record_id", "path_bottleneck_record_ids")
        ids(self.snapshots, "connection_path_evidence_snapshot_id", "connection_path_evidence_snapshot_ids")

        step_by_id = {x.connection_path_step_id: x for x in self.path_steps}
        path_by_id = {x.connection_path_id: x for x in self.connection_paths}
        item_by_id = {x.evidence_chain_item_id: x for x in self.evidence_chain_items}

        for step in self.path_steps:
            if step.from_entity_ref not in entity_ids or step.to_entity_ref not in entity_ids:
                raise ValueError("connection path step entity refs must resolve")
            edge = edge_by_id.get(step.network_edge_projection_ref)
            if edge is None:
                raise ValueError("connection path step edge projection ref must resolve")
            if {step.from_entity_ref, step.to_entity_ref} != {edge.subject_entity_ref, edge.object_entity_ref}:
                raise ValueError("connection path step endpoints must match edge projection endpoints")
            if step.epistemic_state != edge.epistemic_state:
                raise ValueError("connection path step must preserve edge epistemic state")
            if not set(step.documentary_segment_refs) <= segment_ids:
                raise ValueError("connection path step documentary segment refs must resolve")
            if not set(step.documentary_interpretation_refs) <= interpretation_ids:
                raise ValueError("connection path step documentary interpretation refs must resolve")
            if not set(step.relationship_evidence_position_refs) <= evidence_position_ids:
                raise ValueError("connection path step relationship evidence position refs must resolve")

        for path in self.connection_paths:
            if path.network_structure_snapshot_ref not in network_snapshot_ids:
                raise ValueError("connection path network snapshot ref must resolve")
            if path.connection_path_policy_ref not in policy_ids:
                raise ValueError("connection path policy ref must resolve")
            if path.start_entity_ref not in entity_ids or path.end_entity_ref not in entity_ids:
                raise ValueError("connection path entity refs must resolve")
            if not set(path.step_refs) <= step_ids:
                raise ValueError("connection path step refs must resolve")
            ordered = sorted((step_by_id[x] for x in path.step_refs), key=lambda x: x.sequence_index)
            if [x.sequence_index for x in ordered] != list(range(len(ordered))):
                raise ValueError("connection path sequence indexes must be contiguous from zero")
            if ordered[0].from_entity_ref != path.start_entity_ref or ordered[-1].to_entity_ref != path.end_entity_ref:
                raise ValueError("connection path endpoints must match ordered path steps")
            for left, right in zip(ordered, ordered[1:]):
                if left.to_entity_ref != right.from_entity_ref:
                    raise ValueError("connection path steps must form a contiguous walk")

        for item in self.evidence_chain_items:
            if item.connection_path_ref not in path_ids or item.path_step_ref not in step_ids:
                raise ValueError("evidence chain item path/step refs must resolve")
            if item.path_step_ref not in path_by_id[item.connection_path_ref].step_refs:
                raise ValueError("evidence chain item step must belong to its connection path")
            if not set(item.documentary_segment_refs) <= segment_ids:
                raise ValueError("evidence chain item documentary segment refs must resolve")
            if not set(item.documentary_interpretation_refs) <= interpretation_ids:
                raise ValueError("evidence chain item documentary interpretation refs must resolve")
            if not set(item.relationship_evidence_position_refs) <= evidence_position_ids:
                raise ValueError("evidence chain item relationship evidence position refs must resolve")
            if not set(item.source_refs) <= source_ids:
                raise ValueError("evidence chain item source refs must resolve")

        for marker in self.contradiction_markers:
            if marker.connection_path_ref not in path_ids:
                raise ValueError("contradiction marker path ref must resolve")
            if not set(marker.affected_step_refs) <= set(path_by_id[marker.connection_path_ref].step_refs):
                raise ValueError("contradiction marker step refs must belong to path")
            if not set(marker.affected_chain_item_refs) <= item_ids:
                raise ValueError("contradiction marker chain item refs must resolve")
            if not set(marker.reconciliation_conflict_refs) <= reconciliation_conflict_ids:
                raise ValueError("contradiction marker reconciliation conflict refs must resolve")

        for chain in self.evidence_chains:
            if chain.connection_path_ref not in path_ids:
                raise ValueError("evidence chain path ref must resolve")
            if not set(chain.item_refs) <= item_ids:
                raise ValueError("evidence chain item refs must resolve")
            if not set(chain.contradiction_marker_refs) <= contradiction_ids:
                raise ValueError("evidence chain contradiction refs must resolve")
            ordered = sorted((item_by_id[x] for x in chain.item_refs), key=lambda x: x.sequence_index)
            if [x.sequence_index for x in ordered] != list(range(len(ordered))):
                raise ValueError("evidence chain item sequence indexes must be contiguous from zero")
            if any(x.connection_path_ref != chain.connection_path_ref for x in ordered):
                raise ValueError("evidence chain items must belong to the chain path")
            groups = {x.independence_group for x in ordered}
            if not groups <= set(chain.independence_groups):
                raise ValueError("evidence chain must enumerate item independence groups")

        for comparison in self.alternative_path_comparisons:
            if comparison.primary_path_ref not in path_ids or comparison.alternative_path_ref not in path_ids:
                raise ValueError("alternative path comparison path refs must resolve")
            allowed_steps = set(path_by_id[comparison.primary_path_ref].step_refs) | set(path_by_id[comparison.alternative_path_ref].step_refs)
            if not set(comparison.divergence_step_refs) <= allowed_steps:
                raise ValueError("alternative path comparison divergence steps must resolve to compared paths")
            primary = path_by_id[comparison.primary_path_ref]
            alt = path_by_id[comparison.alternative_path_ref]
            if primary.start_entity_ref != alt.start_entity_ref or primary.end_entity_ref != alt.end_entity_ref:
                raise ValueError("alternative paths must share start/end entities")

        for bottleneck in self.bottleneck_records:
            if bottleneck.connection_path_ref not in path_ids or bottleneck.path_step_ref not in step_ids:
                raise ValueError("path bottleneck path/step refs must resolve")
            if bottleneck.path_step_ref not in path_by_id[bottleneck.connection_path_ref].step_refs:
                raise ValueError("path bottleneck step must belong to path")

        for snap in self.snapshots:
            if snap.network_intelligence_snapshot_ref not in intelligence_snapshot_ids:
                raise ValueError("connection path snapshot network intelligence ref must resolve")
            if not set(snap.policy_refs) <= policy_ids:
                raise ValueError("connection path snapshot policy refs must resolve")
            if not set(snap.path_refs) <= path_ids:
                raise ValueError("connection path snapshot path refs must resolve")
            if not set(snap.evidence_chain_refs) <= chain_ids:
                raise ValueError("connection path snapshot evidence chain refs must resolve")
            if not set(snap.contradiction_marker_refs) <= contradiction_ids:
                raise ValueError("connection path snapshot contradiction refs must resolve")
            if not set(snap.alternative_path_comparison_refs) <= comparison_ids:
                raise ValueError("connection path snapshot alternative comparison refs must resolve")
            if not set(snap.bottleneck_record_refs) <= bottleneck_ids:
                raise ValueError("connection path snapshot bottleneck refs must resolve")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


def reference_explainable_connection_paths_evidence_chains_bundle() -> ExplainableConnectionPathsEvidenceChainsBundle:
    upstream = reference_network_structure_community_motif_bundle()
    rel = upstream.relationship_discovery_hypothesis_bundle
    documentary = rel.public_record_documentary_source_bundle
    reconciliation = documentary.cross_source_entity_reconciliation_bundle
    base = reconciliation.probabilistic_record_linkage_bundle.temporal_identity_bundle.entity_resolution_identity_graph_bundle

    entity_a = base.entities[0].entity_id
    entity_b = base.entities[1].entity_id
    edge_observed = next(x for x in upstream.edge_projections if x.epistemic_state == NetworkEdgeEpistemicState.source_observed)
    edge_hypothesis = next(x for x in upstream.edge_projections if x.epistemic_state == NetworkEdgeEpistemicState.hypothesis)
    network_snapshot = upstream.structure_snapshots[0]
    intelligence_snapshot = upstream.intelligence_snapshots[0]
    seg_a = documentary.segments[0].document_segment_id
    seg_b = documentary.segments[-1].document_segment_id
    interp_a = documentary.evidence_interpretations[0].documentary_interpretation_id
    interp_b = documentary.evidence_interpretations[-1].documentary_interpretation_id
    pos_a = rel.evidence_positions[0].evidence_position_id
    pos_b = rel.evidence_positions[-1].evidence_position_id
    source_a = documentary.documentary_sources[0].documentary_source_id
    source_b = documentary.documentary_sources[-1].documentary_source_id
    conflict = reconciliation.conflicts[0].reconciliation_conflict_id

    policy = ConnectionPathPolicy(
        connection_path_policy_id="connection-path-policy:synthetic:default:v1",
        metadata={"synthetic_reference": True},
    )

    primary_step = ConnectionPathStep(
        connection_path_step_id="connection-path-step:synthetic:observed:v1",
        sequence_index=0,
        from_entity_ref=entity_a,
        to_entity_ref=entity_b,
        network_edge_projection_ref=edge_observed.network_edge_projection_id,
        epistemic_state=edge_observed.epistemic_state,
        documentary_segment_refs=[seg_a],
        documentary_interpretation_refs=[interp_a],
        relationship_evidence_position_refs=[pos_a],
        provenance_refs=["provenance:synthetic:path-step:observed:v1"],
        explanation="The primary one-hop path uses a source-observed relationship projection and preserves its source-bound epistemic state.",
        metadata={"synthetic_reference": True},
    )
    alternative_step = ConnectionPathStep(
        connection_path_step_id="connection-path-step:synthetic:hypothesis:v1",
        sequence_index=0,
        from_entity_ref=entity_a,
        to_entity_ref=entity_b,
        network_edge_projection_ref=edge_hypothesis.network_edge_projection_id,
        epistemic_state=edge_hypothesis.epistemic_state,
        documentary_segment_refs=[seg_b],
        documentary_interpretation_refs=[interp_b],
        relationship_evidence_position_refs=[pos_b],
        provenance_refs=["provenance:synthetic:path-step:hypothesis:v1"],
        explanation="The alternative one-hop path uses a still-hypothetical relationship projection and does not promote it to a graph fact.",
        metadata={"synthetic_reference": True},
    )

    primary_path = ExplainableConnectionPath(
        connection_path_id="connection-path:synthetic:primary:v1",
        network_structure_snapshot_ref=network_snapshot.network_structure_snapshot_id,
        connection_path_policy_ref=policy.connection_path_policy_id,
        start_entity_ref=entity_a,
        end_entity_ref=entity_b,
        step_refs=[primary_step.connection_path_step_id],
        algorithm_name="bounded-provenance-preserving-path-selection",
        algorithm_version="1.0",
        parameters={"max_hops": 4, "epistemic_state_preserved": True},
        path_score=1.0,
        path_score_semantics="synthetic traversal cost only; not evidence strength or relationship probability",
        explanation="Primary explainable path through the source-observed projection. Its existence explains a traversable analytical connection, not relationship truth.",
        created_at="2026-09-30T19:00:00Z",
        metadata={"synthetic_reference": True},
    )
    alternative_path = ExplainableConnectionPath(
        connection_path_id="connection-path:synthetic:alternative:v1",
        network_structure_snapshot_ref=network_snapshot.network_structure_snapshot_id,
        connection_path_policy_ref=policy.connection_path_policy_id,
        start_entity_ref=entity_a,
        end_entity_ref=entity_b,
        step_refs=[alternative_step.connection_path_step_id],
        algorithm_name="bounded-provenance-preserving-path-selection",
        algorithm_version="1.0",
        parameters={"max_hops": 4, "include_hypotheses": True},
        path_score=1.1,
        path_score_semantics="synthetic traversal cost only; not evidence strength or relationship probability",
        explanation="Alternative explainable path through the hypothesis projection. It remains explicitly non-factual and requires separate validation.",
        created_at="2026-09-30T19:01:00Z",
        metadata={"synthetic_reference": True},
    )

    items = [
        EvidenceChainItem(
            evidence_chain_item_id="evidence-chain-item:synthetic:filing:v1",
            connection_path_ref=primary_path.connection_path_id,
            path_step_ref=primary_step.connection_path_step_id,
            sequence_index=0,
            position=EvidenceChainPosition.supports,
            documentary_segment_refs=[seg_a],
            documentary_interpretation_refs=[interp_a],
            relationship_evidence_position_refs=[pos_a],
            source_refs=[source_a],
            independence_group="independence-group:synthetic:filing",
            explanation="Synthetic filing material supports continued validation of the source-observed path while remaining source-bound.",
            provenance_refs=["provenance:synthetic:evidence-chain:filing:v1"],
            metadata={"synthetic_reference": True},
        ),
        EvidenceChainItem(
            evidence_chain_item_id="evidence-chain-item:synthetic:disclosure:v1",
            connection_path_ref=primary_path.connection_path_id,
            path_step_ref=primary_step.connection_path_step_id,
            sequence_index=1,
            position=EvidenceChainPosition.qualifies,
            documentary_segment_refs=[seg_b],
            documentary_interpretation_refs=[interp_b],
            relationship_evidence_position_refs=[pos_b],
            source_refs=[source_b],
            independence_group="independence-group:synthetic:disclosure",
            explanation="Synthetic disclosure material adds independent context but also preserves a temporal/source qualification relevant to the path explanation.",
            provenance_refs=["provenance:synthetic:evidence-chain:disclosure:v1"],
            metadata={"synthetic_reference": True},
        ),
    ]

    contradiction = PathContradictionMarker(
        path_contradiction_marker_id="path-contradiction:synthetic:temporal-source:v1",
        connection_path_ref=primary_path.connection_path_id,
        affected_step_refs=[primary_step.connection_path_step_id],
        affected_chain_item_refs=[x.evidence_chain_item_id for x in items],
        reconciliation_conflict_refs=[conflict],
        contradiction_summary="The upstream cross-source reconciliation layer preserves a temporal/source identity conflict; v3.84 keeps that qualification visible in the path explanation instead of erasing it.",
        provenance_refs=["provenance:synthetic:path-contradiction:v1"],
        metadata={"synthetic_reference": True},
    )

    chain = EvidenceChain(
        evidence_chain_id="evidence-chain:synthetic:primary:v1",
        connection_path_ref=primary_path.connection_path_id,
        item_refs=[x.evidence_chain_item_id for x in items],
        independence_groups=[x.independence_group for x in items],
        contradiction_marker_refs=[contradiction.path_contradiction_marker_id],
        chain_summary="Two provenance-bearing source groups explain why the primary connection is reviewable while preserving a source/temporal qualification. The chain is not a truth verdict.",
        created_at="2026-09-30T19:02:00Z",
        metadata={"synthetic_reference": True},
    )

    comparison = AlternativeConnectionPathComparison(
        alternative_path_comparison_id="alternative-path-comparison:synthetic:observed-vs-hypothesis:v1",
        primary_path_ref=primary_path.connection_path_id,
        alternative_path_ref=alternative_path.connection_path_id,
        divergence_step_refs=[primary_step.connection_path_step_id, alternative_step.connection_path_step_id],
        comparison_summary="The two one-hop paths share endpoints but differ in epistemic status: one projects a source-observed relationship and one projects a hypothesis. Their coexistence is not independent corroboration.",
        shared_source_ancestry=True,
        provenance_refs=["provenance:synthetic:alternative-path-comparison:v1"],
        metadata={"synthetic_reference": True},
    )

    bottleneck = PathBottleneckRecord(
        path_bottleneck_record_id="path-bottleneck:synthetic:hypothesis-validation:v1",
        connection_path_ref=alternative_path.connection_path_id,
        path_step_ref=alternative_step.connection_path_step_id,
        bottleneck_kind=PathBottleneckKind.unvalidated_hypothesis,
        explanation="The alternative path depends on an upstream hypothesis that is eligible for separate evidence validation but has not been promoted to a factual relationship edge.",
        provenance_refs=["provenance:synthetic:path-bottleneck:hypothesis:v1"],
        metadata={"synthetic_reference": True},
    )

    snapshot = ConnectionPathEvidenceSnapshot(
        connection_path_evidence_snapshot_id="connection-path-evidence-snapshot:synthetic:2026-09-30:v1",
        network_intelligence_snapshot_ref=intelligence_snapshot.network_intelligence_snapshot_id,
        policy_refs=[policy.connection_path_policy_id],
        path_refs=[primary_path.connection_path_id, alternative_path.connection_path_id],
        evidence_chain_refs=[chain.evidence_chain_id],
        contradiction_marker_refs=[contradiction.path_contradiction_marker_id],
        alternative_path_comparison_refs=[comparison.alternative_path_comparison_id],
        bottleneck_record_refs=[bottleneck.path_bottleneck_record_id],
        created_at="2026-09-30T19:03:00Z",
        metadata={"synthetic_reference": True},
    )

    return ExplainableConnectionPathsEvidenceChainsBundle(
        network_structure_community_motif_bundle=upstream,
        policies=[policy],
        path_steps=[primary_step, alternative_step],
        connection_paths=[primary_path, alternative_path],
        evidence_chain_items=items,
        contradiction_markers=[contradiction],
        evidence_chains=[chain],
        alternative_path_comparisons=[comparison],
        bottleneck_records=[bottleneck],
        snapshots=[snapshot],
    )


def contract_document() -> dict[str, Any]:
    b = reference_explainable_connection_paths_evidence_chains_bundle()
    return {
        "ok": True,
        "release": CORE_RELEASE,
        "contract": CONTRACT_VERSION,
        "extends_contracts": [
            "sc.core.network-structure-community-motif-intelligence.v1",
            "sc.core.relationship-discovery-connection-hypothesis.v1",
            "sc.core.public-record-documentary-source-object-model.v1",
            "sc.core.cross-source-entity-reconciliation-identity-provenance.v1",
            "sc.core.evidence-graph-neural-analysis-validation.v1",
        ],
        "object_types": [
            "ConnectionPathPolicy",
            "ConnectionPathStep",
            "ExplainableConnectionPath",
            "EvidenceChainItem",
            "PathContradictionMarker",
            "EvidenceChain",
            "AlternativeConnectionPathComparison",
            "PathBottleneckRecord",
            "ConnectionPathEvidenceSnapshot",
            "ExplainableConnectionPathsEvidenceChainsBundle",
        ],
        "principles": {
            "path_existence_is_not_relationship_truth": True,
            "shortest_path_is_not_strongest_evidence": True,
            "path_length_is_not_causal_distance": True,
            "multiple_paths_are_not_independent_corroboration": True,
            "evidence_chain_is_not_truth_verdict": True,
            "missing_path_is_not_no_relationship": True,
            "algorithmic_path_selection_is_not_investigator_conclusion": True,
            "contradictions_remain_visible": True,
            "epistemic_edge_state_is_preserved": True,
        },
        "boundaries": {
            "runtime_may_mutate_evidence_graph": False,
            "runtime_may_mutate_identity_graph": False,
            "runtime_may_promote_relationships": False,
            "v384_creates_evidence_edge": False,
            "v384_creates_canonical_relationship_fact": False,
        },
        "reference": {
            "path_steps": len(b.path_steps),
            "connection_paths": len(b.connection_paths),
            "evidence_chain_items": len(b.evidence_chain_items),
            "evidence_chains": len(b.evidence_chains),
            "contradiction_markers": len(b.contradiction_markers),
            "alternative_path_comparisons": len(b.alternative_path_comparisons),
            "bottleneck_records": len(b.bottleneck_records),
            "primary_path_epistemic_state": b.path_steps[0].epistemic_state.value,
            "alternative_path_epistemic_state": b.path_steps[1].epistemic_state.value,
            "relationship_graph_mutation_performed": b.relationship_graph_mutation_performed,
            "evidence_graph_mutation_performed": b.evidence_graph_mutation_performed,
            "identity_graph_mutation_performed": b.identity_graph_mutation_performed,
            "bundle_fingerprint_sha256": b.fingerprint(),
        },
        "database_migration": "none",
    }
