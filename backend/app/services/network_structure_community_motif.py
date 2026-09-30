from __future__ import annotations

from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field, model_validator

from .computational_runtime_objects import canonical_sha256
from .relationship_discovery_hypotheses import (
    RelationshipDiscoveryHypothesisBundle,
    reference_relationship_discovery_hypothesis_bundle,
)

CORE_RELEASE = "3.83.0"
CONTRACT_VERSION = "sc.core.network-structure-community-motif-intelligence.v1"


def _unique(values: list[str], label: str) -> None:
    if len(values) != len(set(values)):
        raise ValueError(f"{label} must be unique")


class NetworkEdgeEpistemicState(str, Enum):
    source_observed = "source-observed"
    candidate = "candidate"
    hypothesis = "hypothesis"
    validated_reference = "validated-reference"


class NetworkMetricKind(str, Enum):
    degree = "degree"
    in_degree = "in-degree"
    out_degree = "out-degree"
    betweenness = "betweenness"
    closeness = "closeness"
    eigenvector = "eigenvector"
    pagerank = "pagerank"
    k_core = "k-core"
    constraint = "constraint"
    brokerage = "brokerage"
    local_clustering = "local-clustering"
    component_size = "component-size"
    custom = "custom"


class CommunityAlgorithmKind(str, Enum):
    connected_components = "connected-components"
    louvain = "louvain"
    leiden = "leiden"
    label_propagation = "label-propagation"
    spectral = "spectral"
    modularity = "modularity"
    custom = "custom"


class MotifKind(str, Enum):
    dyad = "dyad"
    reciprocal_dyad = "reciprocal-dyad"
    multiplex_dyad = "multiplex-dyad"
    wedge = "wedge"
    triangle = "triangle"
    directed_triad = "directed-triad"
    cycle = "cycle"
    feed_forward = "feed-forward"
    custom = "custom"


class NetworkAnalysisPolicy(BaseModel):
    network_analysis_policy_id: str = Field(min_length=2, max_length=500)
    require_immutable_input_snapshot: Literal[True] = True
    require_edge_epistemic_state: Literal[True] = True
    require_algorithm_and_parameter_provenance: Literal[True] = True
    require_metric_semantics: Literal[True] = True
    require_community_method_provenance: Literal[True] = True
    require_motif_definition_provenance: Literal[True] = True
    centrality_can_establish_importance: Literal[False] = False
    community_membership_can_establish_affiliation: Literal[False] = False
    bridge_score_can_establish_influence: Literal[False] = False
    motif_participation_can_establish_coordination: Literal[False] = False
    structural_equivalence_can_establish_identity: Literal[False] = False
    network_structure_can_establish_causality: Literal[False] = False
    network_analysis_can_establish_wrongdoing: Literal[False] = False
    metadata: dict[str, Any] = Field(default_factory=dict)

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class NetworkEdgeProjection(BaseModel):
    network_edge_projection_id: str = Field(min_length=2, max_length=500)
    subject_entity_ref: str = Field(min_length=2, max_length=1000)
    object_entity_ref: str = Field(min_length=2, max_length=1000)
    relationship_type: str = Field(min_length=1, max_length=500)
    epistemic_state: NetworkEdgeEpistemicState
    source_observed_relationship_ref: str | None = Field(default=None, max_length=500)
    connection_candidate_ref: str | None = Field(default=None, max_length=500)
    connection_hypothesis_ref: str | None = Field(default=None, max_length=500)
    promotion_gate_ref: str | None = Field(default=None, max_length=500)
    weight: float | None = Field(default=None, ge=0.0)
    weight_semantics: str | None = Field(default=None, max_length=1000)
    provenance_refs: list[str] = Field(min_length=1)
    edge_projection_is_not_graph_fact: Literal[True] = True
    analytical_inclusion_does_not_promote_relationship: Literal[True] = True
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_projection(self):
        if self.subject_entity_ref == self.object_entity_ref:
            raise ValueError("network edge projection requires distinct entity endpoints")
        _unique(self.provenance_refs, "provenance_refs")
        refs = [
            self.source_observed_relationship_ref,
            self.connection_candidate_ref,
            self.connection_hypothesis_ref,
        ]
        if sum(x is not None for x in refs) != 1:
            raise ValueError("network edge projection must bind exactly one upstream relationship object")
        expected = {
            NetworkEdgeEpistemicState.source_observed: self.source_observed_relationship_ref,
            NetworkEdgeEpistemicState.candidate: self.connection_candidate_ref,
            NetworkEdgeEpistemicState.hypothesis: self.connection_hypothesis_ref,
        }
        if self.epistemic_state in expected and expected[self.epistemic_state] is None:
            raise ValueError("epistemic_state must match the bound upstream relationship object")
        if self.weight is not None and not self.weight_semantics:
            raise ValueError("weighted network edge projection requires weight_semantics")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class NetworkStructureSnapshot(BaseModel):
    network_structure_snapshot_id: str = Field(min_length=2, max_length=500)
    entity_refs: list[str] = Field(min_length=2)
    edge_projection_refs: list[str] = Field(min_length=1)
    relationship_discovery_snapshot_ref: str = Field(min_length=2, max_length=500)
    directed: bool = False
    multigraph: bool = True
    valid_at: str | None = Field(default=None, max_length=80)
    created_at: str = Field(min_length=10, max_length=80)
    immutable_snapshot: Literal[True] = True
    preserves_epistemic_edge_state: Literal[True] = True
    snapshot_is_analytical_view_not_evidence_graph: Literal[True] = True
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_snapshot(self):
        _unique(self.entity_refs, "entity_refs")
        _unique(self.edge_projection_refs, "edge_projection_refs")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class NetworkAnalysisRun(BaseModel):
    network_analysis_run_id: str = Field(min_length=2, max_length=500)
    network_structure_snapshot_ref: str = Field(min_length=2, max_length=500)
    network_analysis_policy_ref: str = Field(min_length=2, max_length=500)
    runtime_ref: str = Field(min_length=2, max_length=1000)
    algorithm_name: str = Field(min_length=1, max_length=500)
    algorithm_version: str | None = Field(default=None, max_length=200)
    parameters: dict[str, Any] = Field(default_factory=dict)
    random_seed: int | None = None
    started_at: str = Field(min_length=10, max_length=80)
    completed_at: str = Field(min_length=10, max_length=80)
    provenance_refs: list[str] = Field(min_length=1)
    runtime_may_mutate_evidence_graph: Literal[False] = False
    runtime_may_promote_relationships: Literal[False] = False
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_run(self):
        _unique(self.provenance_refs, "provenance_refs")
        if self.started_at > self.completed_at:
            raise ValueError("network analysis run started_at must not be after completed_at")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class NetworkMetricRecord(BaseModel):
    network_metric_record_id: str = Field(min_length=2, max_length=500)
    network_analysis_run_ref: str = Field(min_length=2, max_length=500)
    network_structure_snapshot_ref: str = Field(min_length=2, max_length=500)
    target_entity_ref: str = Field(min_length=2, max_length=1000)
    metric_kind: NetworkMetricKind
    metric_name: str = Field(min_length=1, max_length=500)
    value: float
    normalized: bool = False
    metric_semantics: str = Field(min_length=1, max_length=2000)
    provenance_refs: list[str] = Field(min_length=1)
    metric_is_not_importance: Literal[True] = True
    metric_is_not_influence: Literal[True] = True
    metric_is_not_evidence_strength: Literal[True] = True
    metric_is_not_wrongdoing_indicator: Literal[True] = True
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_metric(self):
        _unique(self.provenance_refs, "provenance_refs")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class CommunityDetectionRun(BaseModel):
    community_detection_run_id: str = Field(min_length=2, max_length=500)
    network_structure_snapshot_ref: str = Field(min_length=2, max_length=500)
    network_analysis_policy_ref: str = Field(min_length=2, max_length=500)
    algorithm_kind: CommunityAlgorithmKind
    algorithm_name: str = Field(min_length=1, max_length=500)
    algorithm_version: str | None = Field(default=None, max_length=200)
    parameters: dict[str, Any] = Field(default_factory=dict)
    random_seed: int | None = None
    run_at: str = Field(min_length=10, max_length=80)
    provenance_refs: list[str] = Field(min_length=1)
    community_detection_is_descriptive_partitioning: Literal[True] = True
    detected_community_is_not_affiliation: Literal[True] = True
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_run(self):
        _unique(self.provenance_refs, "provenance_refs")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class CommunityAssignment(BaseModel):
    community_assignment_id: str = Field(min_length=2, max_length=500)
    community_detection_run_ref: str = Field(min_length=2, max_length=500)
    network_structure_snapshot_ref: str = Field(min_length=2, max_length=500)
    entity_ref: str = Field(min_length=2, max_length=1000)
    community_id: str = Field(min_length=1, max_length=500)
    membership_score: float | None = Field(default=None, ge=0.0, le=1.0)
    membership_score_semantics: str | None = Field(default=None, max_length=1000)
    provenance_refs: list[str] = Field(min_length=1)
    community_membership_is_not_affiliation: Literal[True] = True
    community_membership_is_not_identity: Literal[True] = True
    community_membership_is_not_coordination: Literal[True] = True
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_assignment(self):
        _unique(self.provenance_refs, "provenance_refs")
        if self.membership_score is not None and not self.membership_score_semantics:
            raise ValueError("community membership score requires membership_score_semantics")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class CommunityProfile(BaseModel):
    community_profile_id: str = Field(min_length=2, max_length=500)
    community_detection_run_ref: str = Field(min_length=2, max_length=500)
    community_id: str = Field(min_length=1, max_length=500)
    member_entity_refs: list[str] = Field(min_length=1)
    descriptive_label: str | None = Field(default=None, max_length=1000)
    label_generated_from: str | None = Field(default=None, max_length=1000)
    provenance_refs: list[str] = Field(min_length=1)
    descriptive_label_is_not_official_group_name: Literal[True] = True
    community_profile_is_not_affiliation_record: Literal[True] = True
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_profile(self):
        _unique(self.member_entity_refs, "member_entity_refs")
        _unique(self.provenance_refs, "provenance_refs")
        if self.descriptive_label and not self.label_generated_from:
            raise ValueError("descriptive community label requires label_generated_from")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class MotifDefinition(BaseModel):
    motif_definition_id: str = Field(min_length=2, max_length=500)
    motif_kind: MotifKind
    motif_name: str = Field(min_length=1, max_length=500)
    required_node_count: int = Field(ge=2, le=100)
    required_edge_count: int = Field(ge=1, le=1000)
    definition_semantics: str = Field(min_length=1, max_length=4000)
    provenance_refs: list[str] = Field(min_length=1)
    motif_definition_is_analytical_pattern: Literal[True] = True
    motif_does_not_encode_intent_or_causality: Literal[True] = True
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_definition(self):
        _unique(self.provenance_refs, "provenance_refs")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class MotifInstance(BaseModel):
    motif_instance_id: str = Field(min_length=2, max_length=500)
    motif_definition_ref: str = Field(min_length=2, max_length=500)
    network_structure_snapshot_ref: str = Field(min_length=2, max_length=500)
    participating_entity_refs: list[str] = Field(min_length=2)
    participating_edge_projection_refs: list[str] = Field(min_length=1)
    detected_by_run_ref: str = Field(min_length=2, max_length=500)
    observed_count: int = Field(default=1, ge=1)
    motif_score: float | None = None
    motif_score_semantics: str | None = Field(default=None, max_length=1000)
    provenance_refs: list[str] = Field(min_length=1)
    motif_participation_is_not_coordination: Literal[True] = True
    motif_participation_is_not_causality: Literal[True] = True
    motif_participation_is_not_wrongdoing: Literal[True] = True
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_instance(self):
        _unique(self.participating_entity_refs, "participating_entity_refs")
        _unique(self.participating_edge_projection_refs, "participating_edge_projection_refs")
        _unique(self.provenance_refs, "provenance_refs")
        if self.motif_score is not None and not self.motif_score_semantics:
            raise ValueError("scored motif instance requires motif_score_semantics")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class BridgeBrokerRecord(BaseModel):
    bridge_broker_record_id: str = Field(min_length=2, max_length=500)
    network_analysis_run_ref: str = Field(min_length=2, max_length=500)
    network_structure_snapshot_ref: str = Field(min_length=2, max_length=500)
    entity_ref: str = Field(min_length=2, max_length=1000)
    community_ids: list[str] = Field(min_length=1)
    bridge_score: float = Field(ge=0.0)
    score_semantics: str = Field(min_length=1, max_length=2000)
    provenance_refs: list[str] = Field(min_length=1)
    bridge_score_is_not_influence: Literal[True] = True
    bridge_score_is_not_intermediary_fact: Literal[True] = True
    bridge_score_is_not_wrongdoing: Literal[True] = True
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_record(self):
        _unique(self.community_ids, "community_ids")
        _unique(self.provenance_refs, "provenance_refs")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class StructuralEquivalenceRecord(BaseModel):
    structural_equivalence_record_id: str = Field(min_length=2, max_length=500)
    network_analysis_run_ref: str = Field(min_length=2, max_length=500)
    network_structure_snapshot_ref: str = Field(min_length=2, max_length=500)
    entity_a_ref: str = Field(min_length=2, max_length=1000)
    entity_b_ref: str = Field(min_length=2, max_length=1000)
    similarity_score: float = Field(ge=0.0, le=1.0)
    comparison_basis: str = Field(min_length=1, max_length=2000)
    provenance_refs: list[str] = Field(min_length=1)
    structural_equivalence_is_not_identity: Literal[True] = True
    structural_equivalence_is_not_relationship: Literal[True] = True
    structural_equivalence_is_not_shared_intent: Literal[True] = True
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_record(self):
        if self.entity_a_ref == self.entity_b_ref:
            raise ValueError("structural equivalence requires two distinct entities")
        _unique(self.provenance_refs, "provenance_refs")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class NetworkIntelligenceSnapshot(BaseModel):
    network_intelligence_snapshot_id: str = Field(min_length=2, max_length=500)
    network_structure_snapshot_ref: str = Field(min_length=2, max_length=500)
    network_analysis_policy_refs: list[str] = Field(min_length=1)
    network_analysis_run_refs: list[str] = Field(min_length=1)
    network_metric_record_refs: list[str] = Field(default_factory=list)
    community_detection_run_refs: list[str] = Field(default_factory=list)
    community_assignment_refs: list[str] = Field(default_factory=list)
    community_profile_refs: list[str] = Field(default_factory=list)
    motif_definition_refs: list[str] = Field(default_factory=list)
    motif_instance_refs: list[str] = Field(default_factory=list)
    bridge_broker_record_refs: list[str] = Field(default_factory=list)
    structural_equivalence_record_refs: list[str] = Field(default_factory=list)
    created_at: str = Field(min_length=10, max_length=80)
    immutable_snapshot: Literal[True] = True
    snapshot_is_descriptive_not_evidentiary: Literal[True] = True
    snapshot_does_not_mutate_graphs: Literal[True] = True
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_snapshot(self):
        for field in (
            "network_analysis_policy_refs", "network_analysis_run_refs", "network_metric_record_refs",
            "community_detection_run_refs", "community_assignment_refs", "community_profile_refs",
            "motif_definition_refs", "motif_instance_refs", "bridge_broker_record_refs",
            "structural_equivalence_record_refs",
        ):
            _unique(getattr(self, field), field)
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class NetworkStructureCommunityMotifBundle(BaseModel):
    relationship_discovery_hypothesis_bundle: RelationshipDiscoveryHypothesisBundle
    policies: list[NetworkAnalysisPolicy] = Field(min_length=1)
    edge_projections: list[NetworkEdgeProjection] = Field(min_length=1)
    structure_snapshots: list[NetworkStructureSnapshot] = Field(min_length=1)
    analysis_runs: list[NetworkAnalysisRun] = Field(min_length=1)
    metric_records: list[NetworkMetricRecord] = Field(default_factory=list)
    community_runs: list[CommunityDetectionRun] = Field(min_length=1)
    community_assignments: list[CommunityAssignment] = Field(min_length=1)
    community_profiles: list[CommunityProfile] = Field(min_length=1)
    motif_definitions: list[MotifDefinition] = Field(min_length=1)
    motif_instances: list[MotifInstance] = Field(min_length=1)
    bridge_broker_records: list[BridgeBrokerRecord] = Field(default_factory=list)
    structural_equivalence_records: list[StructuralEquivalenceRecord] = Field(default_factory=list)
    intelligence_snapshots: list[NetworkIntelligenceSnapshot] = Field(min_length=1)
    centrality_is_not_importance: Literal[True] = True
    community_membership_is_not_affiliation: Literal[True] = True
    motif_participation_is_not_coordination: Literal[True] = True
    bridge_score_is_not_influence: Literal[True] = True
    structural_equivalence_is_not_identity: Literal[True] = True
    network_structure_is_not_causality: Literal[True] = True
    network_analysis_is_not_wrongdoing: Literal[True] = True
    relationship_graph_mutation_performed: Literal[False] = False
    evidence_graph_mutation_performed: Literal[False] = False
    identity_graph_mutation_performed: Literal[False] = False

    @model_validator(mode="after")
    def validate_bundle(self):
        upstream = self.relationship_discovery_hypothesis_bundle
        documentary = upstream.public_record_documentary_source_bundle
        reconciliation = documentary.cross_source_entity_reconciliation_bundle
        base = reconciliation.probabilistic_record_linkage_bundle.temporal_identity_bundle.entity_resolution_identity_graph_bundle

        def ids(items, attr, label):
            vals = [getattr(x, attr) for x in items]
            _unique(vals, label)
            return set(vals)

        entity_ids = {x.entity_id for x in base.entities}
        observed_ids = {x.source_observed_relationship_id for x in upstream.source_observed_relationships}
        candidate_ids = {x.connection_candidate_id for x in upstream.connection_candidates}
        hypothesis_ids = {x.connection_hypothesis_id for x in upstream.connection_hypotheses}
        gate_ids = {x.relationship_promotion_gate_id for x in upstream.promotion_gates}
        relationship_snapshot_ids = {x.relationship_discovery_snapshot_id for x in upstream.snapshots}

        policy_ids = ids(self.policies, "network_analysis_policy_id", "network_analysis_policy_ids")
        edge_ids = ids(self.edge_projections, "network_edge_projection_id", "network_edge_projection_ids")
        snapshot_ids = ids(self.structure_snapshots, "network_structure_snapshot_id", "network_structure_snapshot_ids")
        run_ids = ids(self.analysis_runs, "network_analysis_run_id", "network_analysis_run_ids")
        metric_ids = ids(self.metric_records, "network_metric_record_id", "network_metric_record_ids")
        community_run_ids = ids(self.community_runs, "community_detection_run_id", "community_detection_run_ids")
        assignment_ids = ids(self.community_assignments, "community_assignment_id", "community_assignment_ids")
        profile_ids = ids(self.community_profiles, "community_profile_id", "community_profile_ids")
        motif_definition_ids = ids(self.motif_definitions, "motif_definition_id", "motif_definition_ids")
        motif_instance_ids = ids(self.motif_instances, "motif_instance_id", "motif_instance_ids")
        bridge_ids = ids(self.bridge_broker_records, "bridge_broker_record_id", "bridge_broker_record_ids")
        structural_ids = ids(self.structural_equivalence_records, "structural_equivalence_record_id", "structural_equivalence_record_ids")
        ids(self.intelligence_snapshots, "network_intelligence_snapshot_id", "network_intelligence_snapshot_ids")

        for edge in self.edge_projections:
            if edge.subject_entity_ref not in entity_ids or edge.object_entity_ref not in entity_ids:
                raise ValueError("network edge projection entity refs must resolve")
            if edge.source_observed_relationship_ref and edge.source_observed_relationship_ref not in observed_ids:
                raise ValueError("network edge projection observed relationship ref must resolve")
            if edge.connection_candidate_ref and edge.connection_candidate_ref not in candidate_ids:
                raise ValueError("network edge projection candidate ref must resolve")
            if edge.connection_hypothesis_ref and edge.connection_hypothesis_ref not in hypothesis_ids:
                raise ValueError("network edge projection hypothesis ref must resolve")
            if edge.promotion_gate_ref and edge.promotion_gate_ref not in gate_ids:
                raise ValueError("network edge projection promotion gate ref must resolve")

        for snap in self.structure_snapshots:
            if not set(snap.entity_refs) <= entity_ids:
                raise ValueError("network structure snapshot entity refs must resolve")
            if not set(snap.edge_projection_refs) <= edge_ids:
                raise ValueError("network structure snapshot edge refs must resolve")
            if snap.relationship_discovery_snapshot_ref not in relationship_snapshot_ids:
                raise ValueError("network structure snapshot relationship discovery snapshot ref must resolve")
            for edge_ref in snap.edge_projection_refs:
                edge = next(x for x in self.edge_projections if x.network_edge_projection_id == edge_ref)
                if edge.subject_entity_ref not in snap.entity_refs or edge.object_entity_ref not in snap.entity_refs:
                    raise ValueError("network structure snapshot must contain all edge endpoint entities")

        for run in self.analysis_runs:
            if run.network_structure_snapshot_ref not in snapshot_ids:
                raise ValueError("network analysis run snapshot ref must resolve")
            if run.network_analysis_policy_ref not in policy_ids:
                raise ValueError("network analysis run policy ref must resolve")

        for metric in self.metric_records:
            if metric.network_analysis_run_ref not in run_ids or metric.network_structure_snapshot_ref not in snapshot_ids:
                raise ValueError("network metric run/snapshot refs must resolve")
            if metric.target_entity_ref not in entity_ids:
                raise ValueError("network metric target entity ref must resolve")

        for run in self.community_runs:
            if run.network_structure_snapshot_ref not in snapshot_ids or run.network_analysis_policy_ref not in policy_ids:
                raise ValueError("community run snapshot/policy refs must resolve")

        community_ids_by_run: dict[str, set[str]] = {}
        for assignment in self.community_assignments:
            if assignment.community_detection_run_ref not in community_run_ids or assignment.network_structure_snapshot_ref not in snapshot_ids:
                raise ValueError("community assignment run/snapshot refs must resolve")
            if assignment.entity_ref not in entity_ids:
                raise ValueError("community assignment entity ref must resolve")
            community_ids_by_run.setdefault(assignment.community_detection_run_ref, set()).add(assignment.community_id)

        for profile in self.community_profiles:
            if profile.community_detection_run_ref not in community_run_ids:
                raise ValueError("community profile run ref must resolve")
            if not set(profile.member_entity_refs) <= entity_ids:
                raise ValueError("community profile member entity refs must resolve")
            if profile.community_id not in community_ids_by_run.get(profile.community_detection_run_ref, set()):
                raise ValueError("community profile community id must be represented by assignments")
            assigned = {x.entity_ref for x in self.community_assignments if x.community_detection_run_ref == profile.community_detection_run_ref and x.community_id == profile.community_id}
            if set(profile.member_entity_refs) != assigned:
                raise ValueError("community profile members must equal assignment members")

        for motif in self.motif_instances:
            if motif.motif_definition_ref not in motif_definition_ids or motif.network_structure_snapshot_ref not in snapshot_ids or motif.detected_by_run_ref not in run_ids:
                raise ValueError("motif instance definition/snapshot/run refs must resolve")
            if not set(motif.participating_entity_refs) <= entity_ids or not set(motif.participating_edge_projection_refs) <= edge_ids:
                raise ValueError("motif instance entity/edge refs must resolve")
            definition = next(x for x in self.motif_definitions if x.motif_definition_id == motif.motif_definition_ref)
            if len(motif.participating_entity_refs) != definition.required_node_count:
                raise ValueError("motif instance node count must match definition")
            if len(motif.participating_edge_projection_refs) != definition.required_edge_count:
                raise ValueError("motif instance edge count must match definition")

        all_community_ids = {x.community_id for x in self.community_assignments}
        for bridge in self.bridge_broker_records:
            if bridge.network_analysis_run_ref not in run_ids or bridge.network_structure_snapshot_ref not in snapshot_ids or bridge.entity_ref not in entity_ids:
                raise ValueError("bridge/broker refs must resolve")
            if not set(bridge.community_ids) <= all_community_ids:
                raise ValueError("bridge/broker community ids must resolve")

        for record in self.structural_equivalence_records:
            if record.network_analysis_run_ref not in run_ids or record.network_structure_snapshot_ref not in snapshot_ids:
                raise ValueError("structural equivalence run/snapshot refs must resolve")
            if record.entity_a_ref not in entity_ids or record.entity_b_ref not in entity_ids:
                raise ValueError("structural equivalence entity refs must resolve")

        for snap in self.intelligence_snapshots:
            if snap.network_structure_snapshot_ref not in snapshot_ids:
                raise ValueError("network intelligence structure snapshot ref must resolve")
            checks = [
                (snap.network_analysis_policy_refs, policy_ids),
                (snap.network_analysis_run_refs, run_ids),
                (snap.network_metric_record_refs, metric_ids),
                (snap.community_detection_run_refs, community_run_ids),
                (snap.community_assignment_refs, assignment_ids),
                (snap.community_profile_refs, profile_ids),
                (snap.motif_definition_refs, motif_definition_ids),
                (snap.motif_instance_refs, motif_instance_ids),
                (snap.bridge_broker_record_refs, bridge_ids),
                (snap.structural_equivalence_record_refs, structural_ids),
            ]
            if any(not set(refs) <= valid for refs, valid in checks):
                raise ValueError("network intelligence snapshot contains unresolved refs")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


def reference_network_structure_community_motif_bundle() -> NetworkStructureCommunityMotifBundle:
    upstream = reference_relationship_discovery_hypothesis_bundle()
    base = upstream.public_record_documentary_source_bundle.cross_source_entity_reconciliation_bundle.probabilistic_record_linkage_bundle.temporal_identity_bundle.entity_resolution_identity_graph_bundle
    entity_a, entity_b = [x.entity_id for x in base.entities[:2]]
    observed = upstream.source_observed_relationships[0]
    hypothesis = upstream.connection_hypotheses[0]
    candidate = upstream.connection_candidates[0]
    gate = upstream.promotion_gates[0]
    upstream_snapshot = upstream.snapshots[0]

    policy = NetworkAnalysisPolicy(
        network_analysis_policy_id="network-analysis-policy:synthetic:v1",
        metadata={"synthetic_reference": True},
    )

    edges = [
        NetworkEdgeProjection(
            network_edge_projection_id="network-edge:synthetic:observed:v1",
            subject_entity_ref=observed.subject_entity_ref,
            object_entity_ref=observed.object_entity_ref,
            relationship_type=observed.relationship_type,
            epistemic_state=NetworkEdgeEpistemicState.source_observed,
            source_observed_relationship_ref=observed.source_observed_relationship_id,
            weight=1.0,
            weight_semantics="synthetic analytical inclusion weight; not evidence strength",
            provenance_refs=["provenance:synthetic:network-edge:observed:v1"],
            metadata={"synthetic_reference": True},
        ),
        NetworkEdgeProjection(
            network_edge_projection_id="network-edge:synthetic:hypothesis:v1",
            subject_entity_ref=hypothesis.subject_entity_ref,
            object_entity_ref=hypothesis.object_entity_ref,
            relationship_type=hypothesis.relationship_type_hypothesis,
            epistemic_state=NetworkEdgeEpistemicState.hypothesis,
            connection_hypothesis_ref=hypothesis.connection_hypothesis_id,
            promotion_gate_ref=gate.relationship_promotion_gate_id,
            weight=0.5,
            weight_semantics="synthetic analytical hypothesis weight; not relationship probability",
            provenance_refs=["provenance:synthetic:network-edge:hypothesis:v1"],
            metadata={"synthetic_reference": True},
        ),
    ]

    structure = NetworkStructureSnapshot(
        network_structure_snapshot_id="network-structure-snapshot:synthetic:2026-09-30:v1",
        entity_refs=[entity_a, entity_b],
        edge_projection_refs=[x.network_edge_projection_id for x in edges],
        relationship_discovery_snapshot_ref=upstream_snapshot.relationship_discovery_snapshot_id,
        directed=False,
        multigraph=True,
        valid_at="2026-09-30T18:00:00Z",
        created_at="2026-09-30T18:00:00Z",
        metadata={"synthetic_reference": True},
    )

    analysis_run = NetworkAnalysisRun(
        network_analysis_run_id="network-analysis-run:synthetic:v1",
        network_structure_snapshot_ref=structure.network_structure_snapshot_id,
        network_analysis_policy_ref=policy.network_analysis_policy_id,
        runtime_ref="workspace-network-runtime:synthetic:v1",
        algorithm_name="synthetic-network-summary",
        algorithm_version="1.0",
        parameters={"epistemic_states_preserved": True},
        random_seed=7,
        started_at="2026-09-30T18:01:00Z",
        completed_at="2026-09-30T18:01:01Z",
        provenance_refs=["provenance:synthetic:network-analysis-run:v1"],
        metadata={"synthetic_reference": True},
    )

    metrics = [
        NetworkMetricRecord(
            network_metric_record_id="network-metric:synthetic:a:degree:v1",
            network_analysis_run_ref=analysis_run.network_analysis_run_id,
            network_structure_snapshot_ref=structure.network_structure_snapshot_id,
            target_entity_ref=entity_a,
            metric_kind=NetworkMetricKind.degree,
            metric_name="analytical multiplex degree",
            value=2.0,
            normalized=False,
            metric_semantics="number of projected analytical edges incident to the entity in this immutable synthetic multigraph snapshot",
            provenance_refs=["provenance:synthetic:metric:a:v1"],
            metadata={"synthetic_reference": True},
        ),
        NetworkMetricRecord(
            network_metric_record_id="network-metric:synthetic:b:degree:v1",
            network_analysis_run_ref=analysis_run.network_analysis_run_id,
            network_structure_snapshot_ref=structure.network_structure_snapshot_id,
            target_entity_ref=entity_b,
            metric_kind=NetworkMetricKind.degree,
            metric_name="analytical multiplex degree",
            value=2.0,
            normalized=False,
            metric_semantics="number of projected analytical edges incident to the entity in this immutable synthetic multigraph snapshot",
            provenance_refs=["provenance:synthetic:metric:b:v1"],
            metadata={"synthetic_reference": True},
        ),
    ]

    community_run = CommunityDetectionRun(
        community_detection_run_id="community-run:synthetic:v1",
        network_structure_snapshot_ref=structure.network_structure_snapshot_id,
        network_analysis_policy_ref=policy.network_analysis_policy_id,
        algorithm_kind=CommunityAlgorithmKind.connected_components,
        algorithm_name="connected-components-reference",
        algorithm_version="1.0",
        parameters={"treat_multiedges_as_connected": True},
        run_at="2026-09-30T18:02:00Z",
        provenance_refs=["provenance:synthetic:community-run:v1"],
        metadata={"synthetic_reference": True},
    )
    assignments = [
        CommunityAssignment(
            community_assignment_id="community-assignment:synthetic:a:v1",
            community_detection_run_ref=community_run.community_detection_run_id,
            network_structure_snapshot_ref=structure.network_structure_snapshot_id,
            entity_ref=entity_a,
            community_id="community:synthetic:component-1",
            membership_score=1.0,
            membership_score_semantics="deterministic membership in the connected component of this analytical snapshot",
            provenance_refs=["provenance:synthetic:community-assignment:a:v1"],
            metadata={"synthetic_reference": True},
        ),
        CommunityAssignment(
            community_assignment_id="community-assignment:synthetic:b:v1",
            community_detection_run_ref=community_run.community_detection_run_id,
            network_structure_snapshot_ref=structure.network_structure_snapshot_id,
            entity_ref=entity_b,
            community_id="community:synthetic:component-1",
            membership_score=1.0,
            membership_score_semantics="deterministic membership in the connected component of this analytical snapshot",
            provenance_refs=["provenance:synthetic:community-assignment:b:v1"],
            metadata={"synthetic_reference": True},
        ),
    ]
    profile = CommunityProfile(
        community_profile_id="community-profile:synthetic:component-1:v1",
        community_detection_run_ref=community_run.community_detection_run_id,
        community_id="community:synthetic:component-1",
        member_entity_refs=[entity_a, entity_b],
        descriptive_label="Synthetic connected component",
        label_generated_from="connected-components-reference output; descriptive only",
        provenance_refs=["provenance:synthetic:community-profile:v1"],
        metadata={"synthetic_reference": True},
    )

    motif_definition = MotifDefinition(
        motif_definition_id="motif-definition:synthetic:multiplex-dyad:v1",
        motif_kind=MotifKind.multiplex_dyad,
        motif_name="multiplex epistemic dyad",
        required_node_count=2,
        required_edge_count=2,
        definition_semantics="two analytical edge projections between the same entity pair that preserve different epistemic states",
        provenance_refs=["provenance:synthetic:motif-definition:v1"],
        metadata={"synthetic_reference": True},
    )
    motif_instance = MotifInstance(
        motif_instance_id="motif-instance:synthetic:multiplex-dyad:v1",
        motif_definition_ref=motif_definition.motif_definition_id,
        network_structure_snapshot_ref=structure.network_structure_snapshot_id,
        participating_entity_refs=[entity_a, entity_b],
        participating_edge_projection_refs=[x.network_edge_projection_id for x in edges],
        detected_by_run_ref=analysis_run.network_analysis_run_id,
        observed_count=1,
        motif_score=1.0,
        motif_score_semantics="exact structural match to the synthetic multiplex-dyad definition; not evidence strength",
        provenance_refs=["provenance:synthetic:motif-instance:v1"],
        metadata={"synthetic_reference": True},
    )

    bridge = BridgeBrokerRecord(
        bridge_broker_record_id="bridge-broker:synthetic:a:v1",
        network_analysis_run_ref=analysis_run.network_analysis_run_id,
        network_structure_snapshot_ref=structure.network_structure_snapshot_id,
        entity_ref=entity_a,
        community_ids=["community:synthetic:component-1"],
        bridge_score=0.0,
        score_semantics="synthetic bridge score in a single-component two-node analytical graph",
        provenance_refs=["provenance:synthetic:bridge:a:v1"],
        metadata={"synthetic_reference": True},
    )
    structural = StructuralEquivalenceRecord(
        structural_equivalence_record_id="structural-equivalence:synthetic:a-b:v1",
        network_analysis_run_ref=analysis_run.network_analysis_run_id,
        network_structure_snapshot_ref=structure.network_structure_snapshot_id,
        entity_a_ref=entity_a,
        entity_b_ref=entity_b,
        similarity_score=1.0,
        comparison_basis="symmetric projected degree profile in this synthetic two-node multigraph snapshot",
        provenance_refs=["provenance:synthetic:structural-equivalence:v1"],
        metadata={"synthetic_reference": True},
    )

    intelligence_snapshot = NetworkIntelligenceSnapshot(
        network_intelligence_snapshot_id="network-intelligence-snapshot:synthetic:2026-09-30:v1",
        network_structure_snapshot_ref=structure.network_structure_snapshot_id,
        network_analysis_policy_refs=[policy.network_analysis_policy_id],
        network_analysis_run_refs=[analysis_run.network_analysis_run_id],
        network_metric_record_refs=[x.network_metric_record_id for x in metrics],
        community_detection_run_refs=[community_run.community_detection_run_id],
        community_assignment_refs=[x.community_assignment_id for x in assignments],
        community_profile_refs=[profile.community_profile_id],
        motif_definition_refs=[motif_definition.motif_definition_id],
        motif_instance_refs=[motif_instance.motif_instance_id],
        bridge_broker_record_refs=[bridge.bridge_broker_record_id],
        structural_equivalence_record_refs=[structural.structural_equivalence_record_id],
        created_at="2026-09-30T18:03:00Z",
        metadata={"synthetic_reference": True},
    )

    return NetworkStructureCommunityMotifBundle(
        relationship_discovery_hypothesis_bundle=upstream,
        policies=[policy],
        edge_projections=edges,
        structure_snapshots=[structure],
        analysis_runs=[analysis_run],
        metric_records=metrics,
        community_runs=[community_run],
        community_assignments=assignments,
        community_profiles=[profile],
        motif_definitions=[motif_definition],
        motif_instances=[motif_instance],
        bridge_broker_records=[bridge],
        structural_equivalence_records=[structural],
        intelligence_snapshots=[intelligence_snapshot],
    )


def contract_document() -> dict[str, Any]:
    b = reference_network_structure_community_motif_bundle()
    return {
        "ok": True,
        "release": CORE_RELEASE,
        "contract": CONTRACT_VERSION,
        "extends_contracts": [
            "sc.core.relationship-discovery-connection-hypothesis.v1",
            "sc.core.public-record-documentary-source-object-model.v1",
            "sc.core.cross-source-entity-reconciliation-identity-provenance.v1",
            "sc.core.entity-resolution-identity-graph-foundation.v1",
        ],
        "object_types": [
            "NetworkAnalysisPolicy", "NetworkEdgeProjection", "NetworkStructureSnapshot",
            "NetworkAnalysisRun", "NetworkMetricRecord", "CommunityDetectionRun",
            "CommunityAssignment", "CommunityProfile", "MotifDefinition", "MotifInstance",
            "BridgeBrokerRecord", "StructuralEquivalenceRecord", "NetworkIntelligenceSnapshot",
            "NetworkStructureCommunityMotifBundle",
        ],
        "principles": {
            "centrality_is_not_importance": True,
            "community_membership_is_not_affiliation": True,
            "motif_participation_is_not_coordination": True,
            "bridge_score_is_not_influence": True,
            "structural_equivalence_is_not_identity": True,
            "network_structure_is_not_causality": True,
            "network_analysis_is_not_wrongdoing": True,
            "analytical_edge_projection_is_not_graph_fact": True,
        },
        "boundaries": {
            "core_executes_large_scale_network_analysis": False,
            "runtime_may_mutate_evidence_graph": False,
            "runtime_may_promote_relationships": False,
            "community_assignment_may_create_affiliation_edge": False,
            "motif_instance_may_create_coordination_edge": False,
            "centrality_may_be_used_as_evidence_strength": False,
            "v383_creates_evidence_edge": False,
        },
        "roadmap_integration": {
            "extends_v3820_relationship_discovery": True,
            "prepares_v3840_explainable_connection_paths_evidence_chains": True,
            "prepares_v3850_multihop_research_investigation_graph_reasoning": True,
            "preserves_v3760_evidence_validation_boundary": True,
        },
        "reference": {
            "edge_projections": len(b.edge_projections),
            "structure_snapshots": len(b.structure_snapshots),
            "metric_records": len(b.metric_records),
            "community_assignments": len(b.community_assignments),
            "communities": len(b.community_profiles),
            "motif_instances": len(b.motif_instances),
            "bridge_broker_records": len(b.bridge_broker_records),
            "structural_equivalence_records": len(b.structural_equivalence_records),
            "centrality_is_not_importance": b.centrality_is_not_importance,
            "community_membership_is_not_affiliation": b.community_membership_is_not_affiliation,
            "motif_participation_is_not_coordination": b.motif_participation_is_not_coordination,
            "relationship_graph_mutation_performed": b.relationship_graph_mutation_performed,
            "evidence_graph_mutation_performed": b.evidence_graph_mutation_performed,
            "identity_graph_mutation_performed": b.identity_graph_mutation_performed,
            "bundle_fingerprint_sha256": b.fingerprint(),
        },
        "database_migration": "none",
    }
