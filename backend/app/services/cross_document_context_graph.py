from __future__ import annotations

from enum import Enum
from functools import lru_cache
from typing import Any, Literal

from pydantic import BaseModel, Field, model_validator

from .computational_runtime_objects import canonical_sha256
from .context_semantic_frame import InterpretationMethod
from .pragmatic_meaning_speech_act_intent import (
    PragmaticMeaningSpeechActIntentBundle,
    reference_pragmatic_meaning_speech_act_intent_bundle,
)

CORE_RELEASE = "4.7.0"
CONTRACT_VERSION = "sc.core.cross-document-context-graph.v1"
PREDECESSOR_CONTRACT = "sc.core.pragmatic-meaning-speech-act-communicative-intent.v1"

EXTENDS_CONTRACTS = [
    PREDECESSOR_CONTRACT,
    "sc.core.epistemic-modal-negation-certainty-semantics.v1",
    "sc.core.temporal-spatial-language-grounding.v1",
    "sc.core.coreference-reference-referential-identity-intelligence.v1",
    "sc.core.discourse-structure-rhetorical-semantics.v1",
    "sc.core.context-object-semantic-frame-foundation.v1",
]


def _unique(values: list[str], label: str) -> None:
    if len(values) != len(set(values)):
        raise ValueError(f"{label} must be unique")


class GraphReviewState(str, Enum):
    proposed = "proposed"
    accepted = "accepted"
    rejected = "rejected"
    superseded = "superseded"


class ContextNodeType(str, Enum):
    document = "document"
    source_excerpt = "source-excerpt"
    mention = "mention"
    referent = "referent"
    participant = "participant"
    proposition = "proposition"
    event = "event"
    temporal_expression = "temporal-expression"
    temporal_anchor = "temporal-anchor"
    spatial_expression = "spatial-expression"
    spatial_anchor = "spatial-anchor"
    discourse_relation = "discourse-relation"
    epistemic_assessment = "epistemic-assessment"
    speech_act = "speech-act"
    communicative_intent = "communicative-intent"
    evidence_reference = "evidence-reference"
    surface_reference = "surface-reference"


class ContextEdgeType(str, Enum):
    contains = "contains"
    derived_from = "derived-from"
    refers_to = "refers-to"
    attributed_to = "attributed-to"
    temporally_grounded_to = "temporally-grounded-to"
    spatially_grounded_to = "spatially-grounded-to"
    discourse_connected_to = "discourse-connected-to"
    epistemically_qualifies = "epistemically-qualifies"
    pragmatically_realizes = "pragmatically-realizes"
    contextual_continuity = "contextual-continuity"
    candidate_actor_continuity = "candidate-actor-continuity"
    candidate_topic_continuity = "candidate-topic-continuity"


class ContextThreadType(str, Enum):
    actor_continuity = "actor-continuity"
    topic_continuity = "topic-continuity"
    temporal_continuity = "temporal-continuity"
    spatial_continuity = "spatial-continuity"
    event_continuity = "event-continuity"
    discourse_continuity = "discourse-continuity"


class RelationBasis(str, Enum):
    exact_object_reference = "exact-object-reference"
    source_explicit = "source-explicit"
    reviewed_linguistic = "reviewed-linguistic"
    temporal_alignment = "temporal-alignment"
    spatial_alignment = "spatial-alignment"
    surface_similarity = "surface-similarity"
    external_authority = "external-authority"


class ContextGraphPolicy(BaseModel):
    policy_id: str = Field(min_length=3, max_length=500)
    graph_is_contextual_index_not_truth_store: Literal[True] = True
    predecessor_objects_remain_immutable: Literal[True] = True
    cross_document_links_preserve_uncertainty: Literal[True] = True
    accepted_links_require_governed_review: Literal[True] = True
    proposed_links_may_remain_unresolved: Literal[True] = True
    canonical_identity_requires_identity_authority: Literal[True] = True
    evidence_validity_requires_evidence_workflow: Literal[True] = True
    source_authority_is_not_inferred_from_connectivity: Literal[True] = True
    graph_density_is_not_confidence: Literal[True] = True
    conflicting_context_may_coexist: Literal[True] = True
    identity_graph_mutation_authorized: Literal[False] = False
    evidence_graph_mutation_authorized: Literal[False] = False
    knowledge_graph_mutation_authorized: Literal[False] = False
    predecessor_context_rewrite_authorized: Literal[False] = False


class ContextDocumentBinding(BaseModel):
    document_id: str = Field(min_length=3, max_length=500)
    source_ref: str = Field(min_length=3, max_length=500)
    source_excerpt_ref: str = Field(min_length=3, max_length=500)
    language_ref: str = Field(min_length=3, max_length=200)
    predecessor_contract: str = Field(min_length=3, max_length=500)
    content_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    title: str = Field(min_length=1, max_length=500)
    immutable: Literal[True] = True
    source_binding_does_not_establish_authority: Literal[True] = True
    metadata: dict[str, Any] = Field(default_factory=dict)

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class ContextGraphNode(BaseModel):
    node_id: str = Field(min_length=3, max_length=500)
    node_type: ContextNodeType
    object_ref: str = Field(min_length=3, max_length=500)
    originating_contract: str = Field(min_length=3, max_length=500)
    document_ref: str | None = Field(default=None, max_length=500)
    source_ref: str | None = Field(default=None, max_length=500)
    label: str | None = Field(default=None, max_length=1000)
    surface_text: str | None = Field(default=None, max_length=2000)
    confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    upstream_object_immutable: Literal[True] = True
    graph_node_does_not_change_upstream_semantics: Literal[True] = True
    metadata: dict[str, Any] = Field(default_factory=dict)

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class ContextGraphEdge(BaseModel):
    edge_id: str = Field(min_length=3, max_length=500)
    edge_type: ContextEdgeType
    source_node_ref: str = Field(min_length=3, max_length=500)
    target_node_ref: str = Field(min_length=3, max_length=500)
    basis: RelationBasis
    cross_document: bool = False
    confidence: float = Field(ge=0.0, le=1.0)
    state: GraphReviewState
    reviewer_ref: str | None = Field(default=None, max_length=500)
    provenance_ref: str = Field(min_length=3, max_length=500)
    relation_is_contextual_not_truth_verdict: Literal[True] = True
    relation_does_not_establish_canonical_identity: Literal[True] = True
    relation_does_not_mutate_upstream_objects: Literal[True] = True
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def accepted_requires_reviewer(self):
        if self.state == GraphReviewState.accepted and not self.reviewer_ref:
            raise ValueError("accepted context graph edge requires reviewer_ref")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class CrossDocumentContextThread(BaseModel):
    thread_id: str = Field(min_length=3, max_length=500)
    thread_type: ContextThreadType
    label: str = Field(min_length=1, max_length=1000)
    document_refs: list[str] = Field(min_length=2)
    node_refs: list[str] = Field(min_length=2)
    edge_refs: list[str] = Field(default_factory=list)
    unresolved_refs: list[str] = Field(default_factory=list)
    confidence: float = Field(ge=0.0, le=1.0)
    state: GraphReviewState
    reviewer_ref: str | None = Field(default=None, max_length=500)
    provenance_ref: str = Field(min_length=3, max_length=500)
    thread_is_contextual_hypothesis_not_identity_fact: Literal[True] = True
    thread_does_not_establish_claim_truth: Literal[True] = True
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def accepted_requires_reviewer(self):
        if self.state == GraphReviewState.accepted and not self.reviewer_ref:
            raise ValueError("accepted context thread requires reviewer_ref")
        if len(set(self.document_refs)) < 2:
            raise ValueError("cross-document thread must span at least two distinct documents")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class ContextGraphProvenanceRecord(BaseModel):
    provenance_id: str = Field(min_length=3, max_length=500)
    subject_refs: list[str] = Field(min_length=1)
    method: InterpretationMethod
    produced_by_ref: str = Field(min_length=3, max_length=500)
    source_refs: list[str] = Field(min_length=1)
    reviewer_ref: str | None = Field(default=None, max_length=500)
    transformation_notes: list[str] = Field(default_factory=list)
    provenance_does_not_establish_truth: Literal[True] = True

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class ContextGraphInterpretation(BaseModel):
    interpretation_id: str = Field(min_length=3, max_length=500)
    predecessor_pragmatic_interpretation_refs: list[str] = Field(min_length=1)
    document_refs: list[str] = Field(min_length=2)
    node_refs: list[str] = Field(min_length=1)
    edge_refs: list[str] = Field(min_length=1)
    thread_refs: list[str] = Field(min_length=1)
    unresolved_refs: list[str] = Field(default_factory=list)
    state: GraphReviewState
    confidence: float = Field(ge=0.0, le=1.0)
    reviewer_ref: str | None = Field(default=None, max_length=500)
    provenance_ref: str = Field(min_length=3, max_length=500)
    accepted_interpretation_does_not_establish_world_truth: Literal[True] = True

    @model_validator(mode="after")
    def accepted_requires_reviewer(self):
        if self.state == GraphReviewState.accepted and not self.reviewer_ref:
            raise ValueError("accepted graph interpretation requires reviewer_ref")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class CrossDocumentContextGraphSnapshot(BaseModel):
    snapshot_id: str = Field(min_length=3, max_length=500)
    predecessor_fingerprint_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    document_refs: list[str] = Field(min_length=2)
    interpretation_refs: list[str] = Field(min_length=1)
    deterministic_graph_fingerprint_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    immutable: Literal[True] = True
    supersedable: Literal[True] = True
    snapshot_does_not_freeze_truth_identity_or_authority: Literal[True] = True

    def fingerprint(self) -> str:
        return canonical_sha256(self)


def _predecessor_refs(predecessor: PragmaticMeaningSpeechActIntentBundle) -> set[str]:
    refs: set[str] = set()

    for x in predecessor.source_excerpts:
        refs.add(x.source_excerpt_id)
    for x in predecessor.participants:
        refs.add(x.participant_id)
    for x in predecessor.content_units:
        refs.add(x.content_unit_id)
    for x in predecessor.cues:
        refs.add(x.cue_id)
    for x in predecessor.contexts:
        refs.add(x.context_id)
    for x in predecessor.speech_acts:
        refs.add(x.speech_act_id)
    for x in predecessor.intents:
        refs.add(x.intent_id)
    for x in predecessor.interpretations:
        refs.add(x.interpretation_id)

    epi = predecessor.epistemic_semantics
    for attr, id_attr in [
        ("source_excerpts", "source_excerpt_id"),
        ("propositions", "proposition_id"),
        ("attributions", "attribution_id"),
        ("cues", "cue_id"),
        ("negation_scopes", "negation_scope_id"),
        ("modal_scopes", "modal_scope_id"),
        ("conditional_scopes", "conditional_scope_id"),
        ("assessments", "assessment_id"),
        ("interpretations", "interpretation_id"),
    ]:
        for x in getattr(epi, attr):
            refs.add(getattr(x, id_attr))

    grounding = epi.temporal_spatial_grounding
    for attr, id_attr in [
        ("source_excerpts", "source_excerpt_id"),
        ("temporal_expressions", "temporal_expression_id"),
        ("spatial_expressions", "spatial_expression_id"),
        ("temporal_anchors", "temporal_anchor_id"),
        ("spatial_anchors", "spatial_anchor_id"),
        ("temporal_groundings", "temporal_grounding_id"),
        ("spatial_groundings", "spatial_grounding_id"),
        ("temporal_relation_groundings", "temporal_relation_grounding_id"),
        ("interpretations", "interpretation_id"),
    ]:
        for x in getattr(grounding, attr):
            refs.add(getattr(x, id_attr))

    referential = grounding.referential_identity
    for attr, id_attr in [
        ("reference_expressions", "reference_expression_id"),
        ("referents", "referent_id"),
        ("coreference_links", "coreference_link_id"),
        ("coreference_chains", "coreference_chain_id"),
        ("identity_bindings", "identity_binding_id"),
        ("interpretations", "interpretation_id"),
    ]:
        for x in getattr(referential, attr):
            refs.add(getattr(x, id_attr))

    discourse = referential.discourse_semantics
    for attr, id_attr in [
        ("segments", "segment_id"),
        ("signals", "signal_id"),
        ("rhetorical_relations", "relation_id"),
        ("argument_units", "argument_unit_id"),
        ("argument_relations", "argument_relation_id"),
        ("interpretations", "interpretation_id"),
    ]:
        for x in getattr(discourse, attr):
            refs.add(getattr(x, id_attr))

    context = discourse.context_semantics
    for attr, id_attr in [
        ("contexts", "context_id"),
        ("mentions", "mention_id"),
        ("frames", "frame_id"),
        ("participants", "participant_id"),
        ("interpretations", "interpretation_id"),
    ]:
        for x in getattr(context, attr):
            refs.add(getattr(x, id_attr))
    return refs


class CrossDocumentContextGraphBundle(BaseModel):
    release: Literal["4.7.0"] = "4.7.0"
    contract: Literal[CONTRACT_VERSION] = CONTRACT_VERSION
    predecessor_contract: Literal[PREDECESSOR_CONTRACT] = PREDECESSOR_CONTRACT
    extends_contracts: list[str] = Field(min_length=6)
    policy: ContextGraphPolicy
    pragmatic_semantics: PragmaticMeaningSpeechActIntentBundle
    documents: list[ContextDocumentBinding] = Field(min_length=2)
    nodes: list[ContextGraphNode] = Field(min_length=2)
    edges: list[ContextGraphEdge] = Field(min_length=1)
    threads: list[CrossDocumentContextThread] = Field(min_length=1)
    provenance_records: list[ContextGraphProvenanceRecord] = Field(min_length=1)
    interpretations: list[ContextGraphInterpretation] = Field(min_length=1)
    snapshots: list[CrossDocumentContextGraphSnapshot] = Field(min_length=1)
    database_migration: Literal["none"] = "none"

    @model_validator(mode="after")
    def validate_bundle(self):
        if self.extends_contracts != EXTENDS_CONTRACTS:
            raise ValueError("extends_contracts must preserve declared v4.7 dependency order")
        if self.pragmatic_semantics.release != "4.6.0" or self.pragmatic_semantics.contract != PREDECESSOR_CONTRACT:
            raise ValueError("v4.7 must embed governed v4.6 pragmatic predecessor")

        for values, label in (
            ([x.document_id for x in self.documents], "document ids"),
            ([x.node_id for x in self.nodes], "node ids"),
            ([x.edge_id for x in self.edges], "edge ids"),
            ([x.thread_id for x in self.threads], "thread ids"),
            ([x.provenance_id for x in self.provenance_records], "provenance ids"),
            ([x.interpretation_id for x in self.interpretations], "interpretation ids"),
            ([x.snapshot_id for x in self.snapshots], "snapshot ids"),
        ):
            _unique(values, label)

        docs = {x.document_id: x for x in self.documents}
        nodes = {x.node_id: x for x in self.nodes}
        edges = {x.edge_id: x for x in self.edges}
        threads = {x.thread_id: x for x in self.threads}
        provenances = {x.provenance_id: x for x in self.provenance_records}
        interpretations = {x.interpretation_id: x for x in self.interpretations}
        upstream = _predecessor_refs(self.pragmatic_semantics)

        grounding = self.pragmatic_semantics.epistemic_semantics.temporal_spatial_grounding
        grounding_excerpt = grounding.source_excerpts[0]
        pragmatic_excerpt = self.pragmatic_semantics.source_excerpts[0]
        context_excerpt = grounding.referential_identity.discourse_semantics.context_semantics.source_bindings[0]
        expected_docs = {
            "document:context-reference:v1": (context_excerpt.source_object_ref, context_excerpt.content_sha256),
            "document:grounding-reference:v1": (grounding_excerpt.source_ref, grounding_excerpt.content_sha256),
            "document:pragmatic-hearing:v1": (pragmatic_excerpt.source_ref, pragmatic_excerpt.content_sha256),
        }
        for doc in self.documents:
            if doc.document_id in expected_docs:
                expected_source, expected_hash = expected_docs[doc.document_id]
                if doc.source_ref != expected_source or doc.content_sha256 != expected_hash:
                    raise ValueError("document binding must preserve predecessor source identity and content hash")

        for node in self.nodes:
            if node.document_ref and node.document_ref not in docs:
                raise ValueError("node document_ref must resolve")
            if node.node_type != ContextNodeType.document and node.object_ref not in upstream:
                raise ValueError(f"node object_ref must resolve to governed predecessor object: {node.object_ref}")
            if node.node_type == ContextNodeType.document and node.object_ref not in docs:
                raise ValueError("document node object_ref must resolve to document binding")

        for edge in self.edges:
            if edge.source_node_ref not in nodes or edge.target_node_ref not in nodes:
                raise ValueError("edge endpoints must resolve")
            if edge.provenance_ref not in provenances:
                raise ValueError("edge provenance_ref must resolve")
            if edge.cross_document:
                sdoc = nodes[edge.source_node_ref].document_ref
                tdoc = nodes[edge.target_node_ref].document_ref
                if not sdoc or not tdoc or sdoc == tdoc:
                    raise ValueError("cross_document edge must connect nodes from distinct documents")

        for thread in self.threads:
            if any(ref not in docs for ref in thread.document_refs):
                raise ValueError("thread document refs must resolve")
            if any(ref not in nodes for ref in thread.node_refs):
                raise ValueError("thread node refs must resolve")
            if any(ref not in edges for ref in thread.edge_refs):
                raise ValueError("thread edge refs must resolve")
            if thread.provenance_ref not in provenances:
                raise ValueError("thread provenance_ref must resolve")

        predecessor_interpretations = {x.interpretation_id for x in self.pragmatic_semantics.interpretations}
        for interpretation in self.interpretations:
            if any(ref not in predecessor_interpretations for ref in interpretation.predecessor_pragmatic_interpretation_refs):
                raise ValueError("context graph predecessor pragmatic interpretation ref must resolve")
            if any(ref not in docs for ref in interpretation.document_refs):
                raise ValueError("interpretation document refs must resolve")
            if any(ref not in nodes for ref in interpretation.node_refs):
                raise ValueError("interpretation node refs must resolve")
            if any(ref not in edges for ref in interpretation.edge_refs):
                raise ValueError("interpretation edge refs must resolve")
            if any(ref not in threads for ref in interpretation.thread_refs):
                raise ValueError("interpretation thread refs must resolve")
            if interpretation.provenance_ref not in provenances:
                raise ValueError("interpretation provenance_ref must resolve")

        local_subjects = set(nodes) | set(edges) | set(threads) | set(interpretations) | {x.snapshot_id for x in self.snapshots}
        for provenance in self.provenance_records:
            if any(ref not in local_subjects for ref in provenance.subject_refs):
                raise ValueError("provenance subject ref must resolve to v4.7 object")

        pred_fp = self.pragmatic_semantics.fingerprint()
        for snapshot in self.snapshots:
            if snapshot.predecessor_fingerprint_sha256 != pred_fp:
                raise ValueError("snapshot predecessor fingerprint must match embedded v4.6 bundle")
            if any(ref not in docs for ref in snapshot.document_refs):
                raise ValueError("snapshot document ref must resolve")
            if any(ref not in interpretations for ref in snapshot.interpretation_refs):
                raise ValueError("snapshot interpretation ref must resolve")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


@lru_cache(maxsize=1)
def reference_cross_document_context_graph_bundle() -> CrossDocumentContextGraphBundle:
    predecessor = reference_pragmatic_meaning_speech_act_intent_bundle()
    grounding = predecessor.epistemic_semantics.temporal_spatial_grounding
    referential = grounding.referential_identity
    context_semantics = referential.discourse_semantics.context_semantics

    context_source = context_semantics.source_bindings[0]
    grounding_source = grounding.source_excerpts[0]
    pragmatic_source = predecessor.source_excerpts[0]

    documents = [
        ContextDocumentBinding(
            document_id="document:context-reference:v1",
            source_ref=context_source.source_object_ref,
            source_excerpt_ref=context_source.source_binding_id,
            language_ref=context_source.language_ref,
            predecessor_contract=context_semantics.contract,
            content_sha256=context_source.content_sha256,
            title="Context and semantic-frame reference document",
            metadata={"layer": "v4.1", "contains": "commission/ministry/proposal reference case"},
        ),
        ContextDocumentBinding(
            document_id="document:grounding-reference:v1",
            source_ref=grounding_source.source_ref,
            source_excerpt_ref=grounding_source.source_excerpt_id,
            language_ref=grounding_source.language_ref,
            predecessor_contract=grounding.contract,
            content_sha256=grounding_source.content_sha256,
            title="Temporal and spatial grounding reference document",
            metadata={"layer": "v4.4", "contains": "2025/Brussels/following-year reference case"},
        ),
        ContextDocumentBinding(
            document_id="document:pragmatic-hearing:v1",
            source_ref=pragmatic_source.source_ref,
            source_excerpt_ref=pragmatic_source.source_excerpt_id,
            language_ref=pragmatic_source.language_ref,
            predecessor_contract=predecessor.contract,
            content_sha256=pragmatic_source.content_sha256,
            title="Pragmatic public-hearing reference document",
            metadata={"layer": "v4.6", "contains": "agency speech acts and communicative intents"},
        ),
    ]

    nodes = [
        ContextGraphNode(node_id="node:doc:context", node_type=ContextNodeType.document, object_ref="document:context-reference:v1", originating_contract=context_semantics.contract, document_ref="document:context-reference:v1", label="context reference document"),
        ContextGraphNode(node_id="node:doc:grounding", node_type=ContextNodeType.document, object_ref="document:grounding-reference:v1", originating_contract=grounding.contract, document_ref="document:grounding-reference:v1", label="grounding reference document"),
        ContextGraphNode(node_id="node:doc:hearing", node_type=ContextNodeType.document, object_ref="document:pragmatic-hearing:v1", originating_contract=predecessor.contract, document_ref="document:pragmatic-hearing:v1", label="public hearing reference document"),
        ContextGraphNode(node_id="node:mention:ministry", node_type=ContextNodeType.mention, object_ref="mention:ministry", originating_contract=context_semantics.contract, document_ref="document:context-reference:v1", label="ministry mention", surface_text="the ministry", confidence=1.0),
        ContextGraphNode(node_id="node:mention:proposal", node_type=ContextNodeType.mention, object_ref="mention:proposal", originating_contract=context_semantics.contract, document_ref="document:context-reference:v1", label="proposal mention", surface_text="the proposal", confidence=1.0),
        ContextGraphNode(node_id="node:place:brussels", node_type=ContextNodeType.spatial_anchor, object_ref="spatial-anchor:brussels-source-place", originating_contract=grounding.contract, document_ref="document:grounding-reference:v1", label="Brussels source-place anchor", surface_text="Brussels", confidence=1.0),
        ContextGraphNode(node_id="node:time:2025", node_type=ContextNodeType.temporal_anchor, object_ref="temporal-anchor:calendar-year:2025", originating_contract=grounding.contract, document_ref="document:grounding-reference:v1", label="calendar year 2025", confidence=1.0),
        ContextGraphNode(node_id="node:time:2026", node_type=ContextNodeType.temporal_anchor, object_ref="temporal-anchor:calendar-year:2026", originating_contract=grounding.contract, document_ref="document:grounding-reference:v1", label="derived calendar year 2026", confidence=1.0),
        ContextGraphNode(node_id="node:participant:agency", node_type=ContextNodeType.participant, object_ref="participant:agency-speaker", originating_contract=predecessor.contract, document_ref="document:pragmatic-hearing:v1", label="agency speaker surface participant", surface_text="the agency", confidence=1.0),
        ContextGraphNode(node_id="node:content:measure", node_type=ContextNodeType.proposition, object_ref="content:measure-may-reduce-emissions", originating_contract=predecessor.contract, document_ref="document:pragmatic-hearing:v1", label="measure emissions content unit", surface_text="the measure may reduce emissions", confidence=1.0),
        ContextGraphNode(node_id="node:speech-act:warning", node_type=ContextNodeType.speech_act, object_ref="speech-act:warn-disruption", originating_contract=predecessor.contract, document_ref="document:pragmatic-hearing:v1", label="warning speech act", confidence=0.99),
        ContextGraphNode(node_id="node:intent:alert", node_type=ContextNodeType.communicative_intent, object_ref="intent:alert-disruption", originating_contract=predecessor.contract, document_ref="document:pragmatic-hearing:v1", label="alert communicative intent", confidence=0.98),
    ]

    prov_edges = "prov:context-graph:edges:reference"
    prov_threads = "prov:context-graph:threads:reference"
    prov_interpretation = "prov:context-graph:interpretation:reference"

    edges = [
        ContextGraphEdge(edge_id="edge:context-doc:ministry", edge_type=ContextEdgeType.contains, source_node_ref="node:doc:context", target_node_ref="node:mention:ministry", basis=RelationBasis.exact_object_reference, confidence=1.0, state=GraphReviewState.accepted, reviewer_ref="reviewer:context-graph:v1", provenance_ref=prov_edges),
        ContextGraphEdge(edge_id="edge:context-doc:proposal", edge_type=ContextEdgeType.contains, source_node_ref="node:doc:context", target_node_ref="node:mention:proposal", basis=RelationBasis.exact_object_reference, confidence=1.0, state=GraphReviewState.accepted, reviewer_ref="reviewer:context-graph:v1", provenance_ref=prov_edges),
        ContextGraphEdge(edge_id="edge:grounding-doc:brussels", edge_type=ContextEdgeType.contains, source_node_ref="node:doc:grounding", target_node_ref="node:place:brussels", basis=RelationBasis.exact_object_reference, confidence=1.0, state=GraphReviewState.accepted, reviewer_ref="reviewer:context-graph:v1", provenance_ref=prov_edges),
        ContextGraphEdge(edge_id="edge:grounding-doc:2025", edge_type=ContextEdgeType.contains, source_node_ref="node:doc:grounding", target_node_ref="node:time:2025", basis=RelationBasis.exact_object_reference, confidence=1.0, state=GraphReviewState.accepted, reviewer_ref="reviewer:context-graph:v1", provenance_ref=prov_edges),
        ContextGraphEdge(edge_id="edge:2025:2026", edge_type=ContextEdgeType.contextual_continuity, source_node_ref="node:time:2025", target_node_ref="node:time:2026", basis=RelationBasis.temporal_alignment, confidence=1.0, state=GraphReviewState.accepted, reviewer_ref="reviewer:context-graph:v1", provenance_ref=prov_edges, metadata={"derivation": "+P1Y", "semantic_boundary": "derived time does not establish event occurrence"}),
        ContextGraphEdge(edge_id="edge:hearing:agency", edge_type=ContextEdgeType.contains, source_node_ref="node:doc:hearing", target_node_ref="node:participant:agency", basis=RelationBasis.exact_object_reference, confidence=1.0, state=GraphReviewState.accepted, reviewer_ref="reviewer:context-graph:v1", provenance_ref=prov_edges),
        ContextGraphEdge(edge_id="edge:hearing:measure", edge_type=ContextEdgeType.contains, source_node_ref="node:doc:hearing", target_node_ref="node:content:measure", basis=RelationBasis.exact_object_reference, confidence=1.0, state=GraphReviewState.accepted, reviewer_ref="reviewer:context-graph:v1", provenance_ref=prov_edges),
        ContextGraphEdge(edge_id="edge:hearing:warning", edge_type=ContextEdgeType.contains, source_node_ref="node:doc:hearing", target_node_ref="node:speech-act:warning", basis=RelationBasis.exact_object_reference, confidence=1.0, state=GraphReviewState.accepted, reviewer_ref="reviewer:context-graph:v1", provenance_ref=prov_edges),
        ContextGraphEdge(edge_id="edge:warning:alert", edge_type=ContextEdgeType.pragmatically_realizes, source_node_ref="node:speech-act:warning", target_node_ref="node:intent:alert", basis=RelationBasis.exact_object_reference, confidence=0.98, state=GraphReviewState.accepted, reviewer_ref="reviewer:context-graph:v1", provenance_ref=prov_edges),
        ContextGraphEdge(edge_id="edge:ministry:agency:candidate", edge_type=ContextEdgeType.candidate_actor_continuity, source_node_ref="node:mention:ministry", target_node_ref="node:participant:agency", basis=RelationBasis.surface_similarity, cross_document=True, confidence=0.42, state=GraphReviewState.proposed, provenance_ref=prov_edges, metadata={"reason": "institutional surface-form continuity candidate only; no canonical actor identity asserted"}),
        ContextGraphEdge(edge_id="edge:proposal:measure:candidate", edge_type=ContextEdgeType.candidate_topic_continuity, source_node_ref="node:mention:proposal", target_node_ref="node:content:measure", basis=RelationBasis.reviewed_linguistic, cross_document=True, confidence=0.36, state=GraphReviewState.proposed, provenance_ref=prov_edges, metadata={"reason": "policy-topic continuity candidate only; proposal and measure are not asserted to be the same object"}),
    ]

    actor_thread = CrossDocumentContextThread(
        thread_id="thread:institutional-actor-continuity:candidate",
        thread_type=ContextThreadType.actor_continuity,
        label="candidate institutional actor continuity across context and hearing documents",
        document_refs=["document:context-reference:v1", "document:pragmatic-hearing:v1"],
        node_refs=["node:mention:ministry", "node:participant:agency"],
        edge_refs=["edge:ministry:agency:candidate"],
        unresolved_refs=["canonical-actor:ministry", "canonical-actor:agency", "same-actor:ministry-agency"],
        confidence=0.42,
        state=GraphReviewState.proposed,
        provenance_ref=prov_threads,
        metadata={"review_note": "cross-document context preserves the hypothesis without merging actors"},
    )

    topic_thread = CrossDocumentContextThread(
        thread_id="thread:policy-topic-continuity:candidate",
        thread_type=ContextThreadType.topic_continuity,
        label="candidate policy-topic continuity across context and hearing documents",
        document_refs=["document:context-reference:v1", "document:pragmatic-hearing:v1"],
        node_refs=["node:mention:proposal", "node:content:measure"],
        edge_refs=["edge:proposal:measure:candidate"],
        unresolved_refs=["same-topic:proposal-measure", "same-object:proposal-measure"],
        confidence=0.36,
        state=GraphReviewState.proposed,
        provenance_ref=prov_threads,
        metadata={"review_note": "topic continuity is indexed without asserting referential identity or claim equivalence"},
    )

    interpretation = ContextGraphInterpretation(
        interpretation_id="context-graph-interpretation:reference:v1",
        predecessor_pragmatic_interpretation_refs=[predecessor.interpretations[0].interpretation_id],
        document_refs=[x.document_id for x in documents],
        node_refs=[x.node_id for x in nodes],
        edge_refs=[x.edge_id for x in edges],
        thread_refs=[actor_thread.thread_id, topic_thread.thread_id],
        unresolved_refs=["same-actor:ministry-agency", "canonical-actor:ministry", "canonical-actor:agency"],
        state=GraphReviewState.accepted,
        confidence=0.95,
        reviewer_ref="reviewer:context-graph:v1",
        provenance_ref=prov_interpretation,
    )

    snapshot_material = {
        "predecessor": predecessor.fingerprint(),
        "documents": [x.fingerprint() for x in documents],
        "nodes": [x.fingerprint() for x in nodes],
        "edges": [x.fingerprint() for x in edges],
        "threads": [actor_thread.fingerprint(), topic_thread.fingerprint()],
        "interpretation": interpretation.fingerprint(),
    }
    snapshot = CrossDocumentContextGraphSnapshot(
        snapshot_id="snapshot:cross-document-context-graph:reference:v1",
        predecessor_fingerprint_sha256=predecessor.fingerprint(),
        document_refs=[x.document_id for x in documents],
        interpretation_refs=[interpretation.interpretation_id],
        deterministic_graph_fingerprint_sha256=canonical_sha256(snapshot_material),
    )

    provenances = [
        ContextGraphProvenanceRecord(
            provenance_id=prov_edges,
            subject_refs=[x.edge_id for x in edges],
            method=InterpretationMethod.manual,
            produced_by_ref="reviewer:context-graph:v1",
            source_refs=[x.source_ref for x in documents],
            reviewer_ref="reviewer:context-graph:v1",
            transformation_notes=["Edges index contextual relationships and preserve predecessor semantics; they do not establish world truth or canonical identity."],
        ),
        ContextGraphProvenanceRecord(
            provenance_id=prov_threads,
            subject_refs=[actor_thread.thread_id, topic_thread.thread_id],
            method=InterpretationMethod.manual,
            produced_by_ref="reviewer:context-graph:v1",
            source_refs=[context_source.source_object_ref, pragmatic_source.source_ref],
            transformation_notes=["Actor and topic continuity remain proposed cross-document hypotheses with explicit unresolved identity/equivalence state."],
        ),
        ContextGraphProvenanceRecord(
            provenance_id=prov_interpretation,
            subject_refs=[interpretation.interpretation_id, snapshot.snapshot_id],
            method=InterpretationMethod.manual,
            produced_by_ref="reviewer:context-graph:v1",
            source_refs=[x.source_ref for x in documents],
            reviewer_ref="reviewer:context-graph:v1",
            transformation_notes=["Accepted graph packaging certifies reviewed contextual structure, not source authority, evidence validity, or claim truth."],
        ),
    ]

    return CrossDocumentContextGraphBundle(
        extends_contracts=list(EXTENDS_CONTRACTS),
        policy=ContextGraphPolicy(policy_id="cross-document-context-graph-policy:v4.7"),
        pragmatic_semantics=predecessor,
        documents=documents,
        nodes=nodes,
        edges=edges,
        threads=[actor_thread, topic_thread],
        provenance_records=provenances,
        interpretations=[interpretation],
        snapshots=[snapshot],
    )


def contract_document() -> dict[str, Any]:
    bundle = reference_cross_document_context_graph_bundle()
    cross_edges = [x for x in bundle.edges if x.cross_document]
    proposed_edges = [x for x in bundle.edges if x.state == GraphReviewState.proposed]
    accepted_edges = [x for x in bundle.edges if x.state == GraphReviewState.accepted]
    return {
        "ok": True,
        "release": CORE_RELEASE,
        "contract": CONTRACT_VERSION,
        "predecessor_contract": PREDECESSOR_CONTRACT,
        "extends_contracts": list(EXTENDS_CONTRACTS),
        "identity": {
            "product": "Sustainable Catalyst Platform Core",
            "build": "Cross-Document Context Graph",
            "major_api": "v4",
        },
        "principles": {
            "context_graph_is_persistent_and_queryable": True,
            "cross_document_links_preserve_uncertainty": True,
            "predecessor_semantic_objects_remain_immutable": True,
            "accepted_links_require_governed_review": True,
            "proposed_links_may_remain_unresolved": True,
            "conflicting_context_may_coexist": True,
            "source_language_and_provenance_are_preserved": True,
            "graph_snapshot_is_supersedable": True,
        },
        "boundaries": {
            "context_graph_establishes_world_truth": False,
            "graph_connectivity_establishes_source_authority": False,
            "cross_document_link_establishes_canonical_identity": False,
            "candidate_actor_continuity_merges_entities": False,
            "graph_density_is_confidence": False,
            "accepted_context_edge_establishes_evidence_validity": False,
            "accepted_graph_interpretation_rewrites_v460_predecessor": False,
            "identity_graph_mutation_performed": False,
            "evidence_graph_mutation_performed": False,
            "knowledge_graph_mutation_performed": False,
        },
        "roadmap_integration": {
            "extends_v460_pragmatic_meaning_speech_act_intent": True,
            "integrates_v410_through_v460_contextual_semantics": True,
            "prepares_v480_multilingual_context_alignment": True,
            "prepares_v490_contextual_semantic_evaluation": True,
            "prepares_v4100_unified_contextual_intelligence_runtime": True,
        },
        "reference": {
            "predecessor_release": bundle.pragmatic_semantics.release,
            "predecessor_fingerprint_sha256": bundle.pragmatic_semantics.fingerprint(),
            "documents": len(bundle.documents),
            "nodes": len(bundle.nodes),
            "edges": len(bundle.edges),
            "cross_document_edges": len(cross_edges),
            "accepted_edges": len(accepted_edges),
            "proposed_edges": len(proposed_edges),
            "threads": len(bundle.threads),
            "proposed_actor_continuity_threads": sum(x.thread_type == ContextThreadType.actor_continuity and x.state == GraphReviewState.proposed for x in bundle.threads),
            "canonical_actor_bindings_created": 0,
            "interpretations": len(bundle.interpretations),
            "snapshots": len(bundle.snapshots),
            "bundle_fingerprint_sha256": bundle.fingerprint(),
        },
        "database_migration": "none",
    }
