from __future__ import annotations

from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field, model_validator

from .computational_runtime_objects import canonical_sha256
from .knowledge_graph_representation_learning import (
    KnowledgeGraphRepresentationLearningBundle,
    reference_knowledge_graph_representation_learning_bundle,
)

CORE_RELEASE = "3.76.0"
CONTRACT_VERSION = "sc.core.evidence-graph-neural-analysis-validation.v1"


def _unique(values: list[str], label: str) -> None:
    if len(values) != len(set(values)):
        raise ValueError(f"{label} must be unique")


class NeuralSignalKind(str, Enum):
    link_prediction = "link-prediction"
    node_classification = "node-classification"
    edge_classification = "edge-classification"
    graph_anomaly = "graph-anomaly"
    graph_embedding = "graph-embedding"
    kg_triple_score = "kg-triple-score"


class EvidenceRole(str, Enum):
    supporting = "supporting"
    contradicting = "contradicting"
    contextual = "contextual"


class EvidenceValidationState(str, Enum):
    pending = "pending"
    under_review = "under-review"
    supported = "supported"
    contradicted = "contradicted"
    disputed = "disputed"
    insufficient = "insufficient"
    rejected = "rejected"


class ReviewDisposition(str, Enum):
    support = "support"
    contradict = "contradict"
    disputed = "disputed"
    insufficient = "insufficient"


class PromotionDecision(str, Enum):
    authorized = "authorized"
    denied = "denied"
    deferred = "deferred"


class NeuralAnalysisSignalRef(BaseModel):
    neural_signal_ref_id: str = Field(min_length=2, max_length=500)
    signal_kind: NeuralSignalKind
    source_object_ref: str = Field(min_length=2, max_length=1000)
    source_release: str = Field(min_length=1, max_length=50)
    candidate_relationship_ref: str | None = Field(default=None, max_length=1000)
    score: float | None = None
    probability: float | None = Field(default=None, ge=0.0, le=1.0)
    explanation_refs: list[str] = Field(default_factory=list)
    is_graph_fact: Literal[False] = False
    is_evidence: Literal[False] = False
    may_satisfy_evidence_gate: Literal[False] = False
    neural_signal_is_context_for_validation_only: Literal[True] = True
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_signal(self):
        _unique(self.explanation_refs, "explanation_refs")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class EvidenceValidationItem(BaseModel):
    validation_evidence_item_id: str = Field(min_length=2, max_length=500)
    evidence_ref: str = Field(min_length=2, max_length=1000)
    provenance_refs: list[str] = Field(min_length=1)
    role: EvidenceRole
    source_ref: str | None = Field(default=None, max_length=1000)
    source_fingerprint_sha256: str | None = Field(default=None, pattern=r"^[0-9a-f]{64}$")
    independent_of_model_output: Literal[True] = True
    admissibility_review_required: Literal[True] = True
    model_generated_score_is_not_evidence: Literal[True] = True
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_item(self):
        _unique(self.provenance_refs, "provenance_refs")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class EvidenceValidationPolicy(BaseModel):
    evidence_validation_policy_id: str = Field(min_length=2, max_length=500)
    minimum_supporting_evidence_items: int = Field(ge=1, le=100)
    minimum_independent_reviewers: int = Field(ge=1, le=20)
    require_evidence_provenance: Literal[True] = True
    require_contradictory_evidence_review: Literal[True] = True
    require_candidate_human_review: Literal[True] = True
    require_independent_validation: Literal[True] = True
    model_probability_can_satisfy_gate: Literal[False] = False
    anomaly_score_can_satisfy_gate: Literal[False] = False
    embedding_similarity_can_satisfy_gate: Literal[False] = False
    classification_output_can_satisfy_gate: Literal[False] = False
    kg_triple_score_can_satisfy_gate: Literal[False] = False
    metadata: dict[str, Any] = Field(default_factory=dict)

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class EvidenceGraphNeuralValidationCase(BaseModel):
    validation_case_id: str = Field(min_length=2, max_length=500)
    candidate_relationship_ref: str = Field(min_length=2, max_length=1000)
    snapshot_ref: str = Field(min_length=2, max_length=1000)
    source_node_ref: str = Field(min_length=2, max_length=1000)
    target_node_ref: str = Field(min_length=2, max_length=1000)
    relationship_type_candidate: str = Field(min_length=1, max_length=300)
    policy_ref: str = Field(min_length=2, max_length=500)
    neural_signal_refs: list[str] = Field(min_length=1)
    evidence_item_refs: list[str] = Field(min_length=1)
    review_assessment_refs: list[str] = Field(default_factory=list)
    validation_state: EvidenceValidationState = EvidenceValidationState.pending
    candidate_still_not_graph_fact: Literal[True] = True
    neural_signals_do_not_count_as_evidence: Literal[True] = True
    evidence_validation_is_separate_from_model_inference: Literal[True] = True
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_case(self):
        if self.source_node_ref == self.target_node_ref:
            raise ValueError("validation case cannot be self-referential")
        for xs, label in ((self.neural_signal_refs,"neural_signal_refs"),(self.evidence_item_refs,"evidence_item_refs"),(self.review_assessment_refs,"review_assessment_refs")):
            _unique(xs,label)
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class IndependentEvidenceAssessmentRecord(BaseModel):
    evidence_assessment_id: str = Field(min_length=2, max_length=500)
    validation_case_ref: str = Field(min_length=2, max_length=500)
    reviewer_ref: str = Field(min_length=2, max_length=1000)
    disposition: ReviewDisposition
    supporting_evidence_item_refs: list[str] = Field(default_factory=list)
    contradicting_evidence_item_refs: list[str] = Field(default_factory=list)
    considered_neural_signal_refs: list[str] = Field(default_factory=list)
    rationale: str = Field(min_length=1, max_length=8000)
    reviewed_at: str | None = Field(default=None, max_length=80)
    reviewer_independent_of_model_run: Literal[True] = True
    neural_signals_are_context_not_evidence: Literal[True] = True
    assessment_does_not_itself_create_edge: Literal[True] = True
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_assessment(self):
        for xs,label in ((self.supporting_evidence_item_refs,"supporting_evidence_item_refs"),(self.contradicting_evidence_item_refs,"contradicting_evidence_item_refs"),(self.considered_neural_signal_refs,"considered_neural_signal_refs")):
            _unique(xs,label)
        if self.disposition == ReviewDisposition.support and not self.supporting_evidence_item_refs:
            raise ValueError("support assessment requires supporting evidence items")
        if self.disposition == ReviewDisposition.contradict and not self.contradicting_evidence_item_refs:
            raise ValueError("contradict assessment requires contradicting evidence items")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class EvidenceEdgePromotionAuthorization(BaseModel):
    promotion_authorization_id: str = Field(min_length=2, max_length=500)
    validation_case_ref: str = Field(min_length=2, max_length=500)
    decision: PromotionDecision
    validated_source_node_ref: str = Field(min_length=2, max_length=1000)
    validated_target_node_ref: str = Field(min_length=2, max_length=1000)
    validated_relationship_type: str = Field(min_length=1, max_length=300)
    supporting_evidence_item_refs: list[str] = Field(default_factory=list)
    contradicting_evidence_item_refs: list[str] = Field(default_factory=list)
    reviewer_assessment_refs: list[str] = Field(min_length=1)
    evidence_provenance_verified: bool
    contradictory_evidence_review_completed: bool
    independent_validation_completed: bool
    proposed_evidence_edge_ref: str | None = Field(default=None, max_length=1000)
    model_outputs_counted_as_evidence: Literal[False] = False
    model_outputs_can_authorize_promotion: Literal[False] = False
    actual_evidence_graph_mutation_performed: Literal[False] = False
    authorization_requires_downstream_edge_creation: Literal[True] = True
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_authorization(self):
        for xs,label in ((self.supporting_evidence_item_refs,"supporting_evidence_item_refs"),(self.contradicting_evidence_item_refs,"contradicting_evidence_item_refs"),(self.reviewer_assessment_refs,"reviewer_assessment_refs")):
            _unique(xs,label)
        if self.decision == PromotionDecision.authorized:
            if not self.proposed_evidence_edge_ref:
                raise ValueError("authorized promotion requires proposed_evidence_edge_ref")
            if not self.supporting_evidence_item_refs:
                raise ValueError("authorized promotion requires supporting evidence")
            if not (self.evidence_provenance_verified and self.contradictory_evidence_review_completed and self.independent_validation_completed):
                raise ValueError("authorized promotion requires all governance gates")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class EvidenceGraphValidationAuditRecord(BaseModel):
    validation_audit_id: str = Field(min_length=2, max_length=500)
    validation_case_ref: str = Field(min_length=2, max_length=500)
    event_type: str = Field(min_length=1, max_length=200)
    actor_ref: str = Field(min_length=2, max_length=1000)
    occurred_at: str = Field(min_length=10, max_length=80)
    input_fingerprint_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    output_fingerprint_sha256: str | None = Field(default=None, pattern=r"^[0-9a-f]{64}$")
    append_only_audit_event: Literal[True] = True
    metadata: dict[str, Any] = Field(default_factory=dict)

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class EvidenceGraphNeuralValidationBundle(BaseModel):
    knowledge_graph_representation_bundle: KnowledgeGraphRepresentationLearningBundle
    policies: list[EvidenceValidationPolicy] = Field(min_length=1)
    neural_signals: list[NeuralAnalysisSignalRef] = Field(min_length=1)
    evidence_items: list[EvidenceValidationItem] = Field(min_length=1)
    validation_cases: list[EvidenceGraphNeuralValidationCase] = Field(min_length=1)
    assessments: list[IndependentEvidenceAssessmentRecord] = Field(min_length=1)
    promotion_authorizations: list[EvidenceEdgePromotionAuthorization] = Field(min_length=1)
    audit_records: list[EvidenceGraphValidationAuditRecord] = Field(min_length=1)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_bundle(self):
        groups=((self.policies,"policies","evidence_validation_policy_id"),(self.neural_signals,"neural_signals","neural_signal_ref_id"),(self.evidence_items,"evidence_items","validation_evidence_item_id"),(self.validation_cases,"validation_cases","validation_case_id"),(self.assessments,"assessments","evidence_assessment_id"),(self.promotion_authorizations,"promotion_authorizations","promotion_authorization_id"),(self.audit_records,"audit_records","validation_audit_id"))
        for xs,label,attr in groups: _unique([getattr(x,attr) for x in xs],label)

        kg=self.knowledge_graph_representation_bundle
        an=kg.graph_anomaly_detection_bundle
        lp=an.graph_link_prediction_bundle
        gc=lp.graph_classification_bundle
        ge=gc.graph_embedding_bundle
        graph=ge.graph_ml_foundation_bundle
        signal_sources={
            NeuralSignalKind.link_prediction:{x.link_prediction_id for x in lp.predictions},
            NeuralSignalKind.node_classification:{x.classification_prediction_id for x in gc.predictions if x.target_kind.value=='node'},
            NeuralSignalKind.edge_classification:{x.classification_prediction_id for x in gc.predictions if x.target_kind.value=='edge'},
            NeuralSignalKind.graph_anomaly:{x.anomaly_score_id for x in an.scores},
            NeuralSignalKind.graph_embedding:{x.embedding_id for x in ge.embeddings},
            NeuralSignalKind.kg_triple_score:{x.triple_score_id for x in kg.triple_scores},
        }
        candidate_map={x.candidate_relationship_id:x for x in lp.candidate_relationships}
        snapshot_ids={x.snapshot_id for x in graph.snapshots}
        policy_map={x.evidence_validation_policy_id:x for x in self.policies}
        signal_map={x.neural_signal_ref_id:x for x in self.neural_signals}
        item_map={x.validation_evidence_item_id:x for x in self.evidence_items}
        case_map={x.validation_case_id:x for x in self.validation_cases}
        assessment_map={x.evidence_assessment_id:x for x in self.assessments}

        for s in self.neural_signals:
            if s.source_object_ref not in signal_sources[s.signal_kind]:
                raise ValueError(f"neural signal source does not resolve for {s.signal_kind.value}")
            if s.candidate_relationship_ref and s.candidate_relationship_ref not in candidate_map:
                raise ValueError("neural signal candidate relationship must resolve")

        for case in self.validation_cases:
            if case.candidate_relationship_ref not in candidate_map or case.snapshot_ref not in snapshot_ids or case.policy_ref not in policy_map:
                raise ValueError("validation case graph/policy references must resolve")
            candidate=candidate_map[case.candidate_relationship_ref]
            if (case.source_node_ref,case.target_node_ref,case.relationship_type_candidate)!=(candidate.source_node_ref,candidate.target_node_ref,candidate.relationship_type_candidate):
                raise ValueError("validation case must preserve candidate relationship identity")
            if any(x not in signal_map for x in case.neural_signal_refs) or any(x not in item_map for x in case.evidence_item_refs):
                raise ValueError("validation case signal/evidence refs must resolve")
            if any(x not in assessment_map for x in case.review_assessment_refs):
                raise ValueError("validation case assessment refs must resolve")

        for a in self.assessments:
            if a.validation_case_ref not in case_map:
                raise ValueError("assessment case must resolve")
            case=case_map[a.validation_case_ref]
            if any(x not in case.evidence_item_refs for x in a.supporting_evidence_item_refs+a.contradicting_evidence_item_refs):
                raise ValueError("assessment evidence refs must belong to case")
            if any(x not in case.neural_signal_refs for x in a.considered_neural_signal_refs):
                raise ValueError("assessment neural refs must belong to case")

        for auth in self.promotion_authorizations:
            if auth.validation_case_ref not in case_map:
                raise ValueError("promotion authorization case must resolve")
            case=case_map[auth.validation_case_ref]; policy=policy_map[case.policy_ref]
            if any(x not in case.evidence_item_refs for x in auth.supporting_evidence_item_refs+auth.contradicting_evidence_item_refs):
                raise ValueError("promotion evidence refs must belong to case")
            if any(x not in assessment_map for x in auth.reviewer_assessment_refs):
                raise ValueError("promotion reviewer assessments must resolve")
            if auth.decision == PromotionDecision.authorized:
                if case.validation_state != EvidenceValidationState.supported:
                    raise ValueError("authorized promotion requires supported validation case")
                if len(auth.supporting_evidence_item_refs) < policy.minimum_supporting_evidence_items:
                    raise ValueError("authorized promotion does not satisfy minimum supporting evidence")
                reviewers={assessment_map[x].reviewer_ref for x in auth.reviewer_assessment_refs}
                if len(reviewers) < policy.minimum_independent_reviewers:
                    raise ValueError("authorized promotion does not satisfy independent reviewer minimum")
                if any(item_map[x].role != EvidenceRole.supporting for x in auth.supporting_evidence_item_refs):
                    raise ValueError("promotion supporting refs must be supporting evidence items")
                if auth.validated_source_node_ref!=case.source_node_ref or auth.validated_target_node_ref!=case.target_node_ref or auth.validated_relationship_type!=case.relationship_type_candidate:
                    raise ValueError("promotion authorization must preserve validated relationship identity")

        for audit in self.audit_records:
            if audit.validation_case_ref not in case_map:
                raise ValueError("audit validation case must resolve")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


def reference_evidence_graph_neural_validation_bundle() -> EvidenceGraphNeuralValidationBundle:
    kg=reference_knowledge_graph_representation_learning_bundle()
    an=kg.graph_anomaly_detection_bundle; lp=an.graph_link_prediction_bundle; gc=lp.graph_classification_bundle; ge=gc.graph_embedding_bundle
    candidate=lp.candidate_relationships[0]
    policy=EvidenceValidationPolicy(evidence_validation_policy_id="evidence-validation-policy:reference:v1",minimum_supporting_evidence_items=2,minimum_independent_reviewers=2,metadata={"synthetic_reference":True})
    signals=[
        NeuralAnalysisSignalRef(neural_signal_ref_id="neural-signal:link-prediction:reference:v1",signal_kind=NeuralSignalKind.link_prediction,source_object_ref=lp.predictions[0].link_prediction_id,source_release="3.73.0",candidate_relationship_ref=candidate.candidate_relationship_id,probability=lp.predictions[0].confidence,metadata={"synthetic_reference":True}),
        NeuralAnalysisSignalRef(neural_signal_ref_id="neural-signal:anomaly:reference:v1",signal_kind=NeuralSignalKind.graph_anomaly,source_object_ref=an.scores[0].anomaly_score_id,source_release="3.74.0",candidate_relationship_ref=candidate.candidate_relationship_id,score=an.scores[0].normalized_score,metadata={"synthetic_reference":True}),
        NeuralAnalysisSignalRef(neural_signal_ref_id="neural-signal:embedding:reference:v1",signal_kind=NeuralSignalKind.graph_embedding,source_object_ref=ge.embeddings[2].embedding_id,source_release="3.71.0",candidate_relationship_ref=candidate.candidate_relationship_id,metadata={"synthetic_reference":True}),
        NeuralAnalysisSignalRef(neural_signal_ref_id="neural-signal:kg-score:reference:v1",signal_kind=NeuralSignalKind.kg_triple_score,source_object_ref=kg.triple_scores[1].triple_score_id,source_release="3.75.0",candidate_relationship_ref=candidate.candidate_relationship_id,score=kg.triple_scores[1].raw_score,metadata={"synthetic_reference":True}),
    ]
    items=[
        EvidenceValidationItem(validation_evidence_item_id="validation-evidence:alignment:reference:v1",evidence_ref="alignment:es-a:water",provenance_refs=["provenance:alignment:es-a:water"],role=EvidenceRole.supporting,source_ref="cross-lingual-exchange:reference",metadata={"synthetic_reference":True}),
        EvidenceValidationItem(validation_evidence_item_id="validation-evidence:source:reference:v1",evidence_ref="source:reference:multilingual-note",provenance_refs=["provenance:source:reference:multilingual-note"],role=EvidenceRole.supporting,source_ref="text-source:multilingual-reference-note:v1",metadata={"synthetic_reference":True}),
        EvidenceValidationItem(validation_evidence_item_id="validation-evidence:context:reference:v1",evidence_ref="context:reference:no-known-contradiction",provenance_refs=["provenance:context:reference:v1"],role=EvidenceRole.contextual,metadata={"synthetic_reference":True,"not_negative_evidence":True}),
    ]
    case=EvidenceGraphNeuralValidationCase(validation_case_id="evidence-neural-validation-case:reference:v1",candidate_relationship_ref=candidate.candidate_relationship_id,snapshot_ref=candidate.snapshot_ref,source_node_ref=candidate.source_node_ref,target_node_ref=candidate.target_node_ref,relationship_type_candidate=candidate.relationship_type_candidate,policy_ref=policy.evidence_validation_policy_id,neural_signal_refs=[x.neural_signal_ref_id for x in signals],evidence_item_refs=[x.validation_evidence_item_id for x in items],review_assessment_refs=["evidence-assessment:reference:reviewer-a:v1","evidence-assessment:reference:reviewer-b:v1"],validation_state=EvidenceValidationState.supported,metadata={"synthetic_reference":True,"neural_outputs_not_counted_as_evidence":True})
    assessments=[
        IndependentEvidenceAssessmentRecord(evidence_assessment_id="evidence-assessment:reference:reviewer-a:v1",validation_case_ref=case.validation_case_id,reviewer_ref="reviewer:reference:human-a:v1",disposition=ReviewDisposition.support,supporting_evidence_item_refs=[items[0].validation_evidence_item_id,items[1].validation_evidence_item_id],considered_neural_signal_refs=[signals[0].neural_signal_ref_id,signals[3].neural_signal_ref_id],rationale="Synthetic independent review supports validation based on source-bound evidence; model outputs were contextual only.",reviewed_at="2026-09-29T00:00:00Z"),
        IndependentEvidenceAssessmentRecord(evidence_assessment_id="evidence-assessment:reference:reviewer-b:v1",validation_case_ref=case.validation_case_id,reviewer_ref="reviewer:reference:human-b:v1",disposition=ReviewDisposition.support,supporting_evidence_item_refs=[items[0].validation_evidence_item_id,items[1].validation_evidence_item_id],considered_neural_signal_refs=[signals[1].neural_signal_ref_id,signals[2].neural_signal_ref_id],rationale="Synthetic second review independently supports validation from evidence provenance and does not treat neural scores as evidence.",reviewed_at="2026-09-29T00:05:00Z"),
    ]
    auth=EvidenceEdgePromotionAuthorization(promotion_authorization_id="evidence-edge-authorization:reference:v1",validation_case_ref=case.validation_case_id,decision=PromotionDecision.authorized,validated_source_node_ref=case.source_node_ref,validated_target_node_ref=case.target_node_ref,validated_relationship_type=case.relationship_type_candidate,supporting_evidence_item_refs=[items[0].validation_evidence_item_id,items[1].validation_evidence_item_id],contradicting_evidence_item_refs=[],reviewer_assessment_refs=[x.evidence_assessment_id for x in assessments],evidence_provenance_verified=True,contradictory_evidence_review_completed=True,independent_validation_completed=True,proposed_evidence_edge_ref="proposed-evidence-edge:reference:en-es:semantic-related:v1",metadata={"synthetic_reference":True,"authorization_not_graph_mutation":True})
    audit=[EvidenceGraphValidationAuditRecord(validation_audit_id="evidence-validation-audit:reference:authorized:v1",validation_case_ref=case.validation_case_id,event_type="promotion-authorized",actor_ref="governance:reference:evidence-validation:v1",occurred_at="2026-09-29T00:06:00Z",input_fingerprint_sha256=case.fingerprint(),output_fingerprint_sha256=auth.fingerprint(),metadata={"synthetic_reference":True})]
    return EvidenceGraphNeuralValidationBundle(knowledge_graph_representation_bundle=kg,policies=[policy],neural_signals=signals,evidence_items=items,validation_cases=[case],assessments=assessments,promotion_authorizations=[auth],audit_records=audit,metadata={"reference_fixture":"synthetic-contract-fixture","gnn_prediction_is_not_graph_fact":True,"promotion_requires_independent_evidence":True})


def contract_document() -> dict[str, Any]:
    b=reference_evidence_graph_neural_validation_bundle()
    return {
        "ok":True,"release":CORE_RELEASE,"contract":CONTRACT_VERSION,
        "extends_contracts":["sc.core.graph-machine-learning-foundation.v1","sc.core.graph-embedding-runtime.v1","sc.core.graph-node-edge-classification.v1","sc.core.graph-link-prediction-candidate-relationship.v1","sc.core.graph-anomaly-detection.v1","sc.core.knowledge-graph-representation-learning.v1"],
        "object_types":["NeuralAnalysisSignalRef","EvidenceValidationItem","EvidenceValidationPolicy","EvidenceGraphNeuralValidationCase","IndependentEvidenceAssessmentRecord","EvidenceEdgePromotionAuthorization","EvidenceGraphValidationAuditRecord","EvidenceGraphNeuralValidationBundle"],
        "principles":{"gnn_prediction_is_not_graph_fact":True,"neural_signal_is_not_evidence":True,"anomaly_is_not_evidence":True,"embedding_similarity_is_not_evidence":True,"classification_output_is_not_evidence":True,"kg_triple_score_is_not_evidence":True,"model_output_cannot_satisfy_evidence_gate":True,"promotion_requires_independent_evidence":True,"promotion_requires_evidence_provenance":True,"contradictory_evidence_must_be_reviewable":True,"authorization_is_not_graph_mutation":True},
        "capabilities":{"neural_signal_aggregation":True,"candidate_evidence_validation_cases":True,"supporting_and_contradicting_evidence_channels":True,"independent_reviewer_assessments":True,"policy_gated_promotion_authorization":True,"append_only_validation_audit":True,"proposed_evidence_edge_handoff":True},
        "boundaries":{"core_treats_model_output_as_evidence":False,"core_allows_model_score_to_satisfy_promotion_gate":False,"core_auto_promotes_candidate_relationship":False,"core_mutates_evidence_graph_during_neural_validation":False,"runtime_may_promote_candidate_to_evidence_edge":False,"authorization_itself_creates_evidence_edge":False},
        "roadmap_integration":{"completes_graph_neural_wave_v3700_through_v3760":True,"reconnects_graph_ml_to_evidence_validation_architecture":True,"preserves_candidate_relationship_boundary_from_v3730":True,"preserves_non_evidentiary_anomaly_boundary_from_v3740":True,"preserves_non_evidentiary_kg_score_boundary_from_v3750":True},
        "reference":{"validation_case_id":b.validation_cases[0].validation_case_id,"neural_signal_count":len(b.neural_signals),"evidence_item_count":len(b.evidence_items),"independent_reviewers":len({x.reviewer_ref for x in b.assessments}),"promotion_decision":b.promotion_authorizations[0].decision.value,"proposed_evidence_edge_ref":b.promotion_authorizations[0].proposed_evidence_edge_ref,"actual_graph_mutation_performed":b.promotion_authorizations[0].actual_evidence_graph_mutation_performed,"bundle_fingerprint_sha256":b.fingerprint()},
    }
