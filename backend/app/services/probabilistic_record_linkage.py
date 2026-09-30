from __future__ import annotations

from enum import Enum
from math import isfinite
from typing import Any, Literal

from pydantic import BaseModel, Field, model_validator

from .computational_runtime_objects import canonical_sha256
from .temporal_identity_intelligence import (
    TemporalIdentityIntelligenceBundle,
    reference_temporal_identity_intelligence_bundle,
)

CORE_RELEASE = "3.79.0"
CONTRACT_VERSION = "sc.core.probabilistic-record-linkage-entity-matching.v1"


def _unique(values: list[str], label: str) -> None:
    if len(values) != len(set(values)):
        raise ValueError(f"{label} must be unique")


class LinkageFeatureKind(str, Enum):
    exact = "exact"
    string_similarity = "string-similarity"
    identifier = "identifier"
    temporal = "temporal"
    geographic = "geographic"
    categorical = "categorical"
    graph = "graph"
    embedding = "embedding"
    other = "other"


class FeatureComparisonState(str, Enum):
    agree = "agree"
    disagree = "disagree"
    partial = "partial"
    missing = "missing"
    unknown = "unknown"


class LinkageMethod(str, Enum):
    fellegi_sunter = "fellegi-sunter"
    logistic = "logistic"
    gradient_boosted = "gradient-boosted"
    neural = "neural"
    hybrid = "hybrid"
    deterministic = "deterministic"
    other = "other"


class MatchDecisionState(str, Enum):
    review_required = "review-required"
    candidate_supported = "candidate-supported"
    candidate_rejected = "candidate-rejected"
    indeterminate = "indeterminate"


class MatchReviewDisposition(str, Enum):
    support_candidate = "support-candidate"
    reject_candidate = "reject-candidate"
    disputed = "disputed"
    insufficient = "insufficient"


class RecordLinkageFeatureDefinition(BaseModel):
    linkage_feature_id: str = Field(min_length=2, max_length=500)
    name: str = Field(min_length=1, max_length=500)
    feature_kind: LinkageFeatureKind
    description: str = Field(min_length=1, max_length=4000)
    source_attribute_refs: list[str] = Field(min_length=1)
    comparison_function_ref: str = Field(min_length=2, max_length=1000)
    missing_value_policy: str = Field(min_length=1, max_length=500)
    model_feature_only: Literal[True] = True
    feature_agreement_is_not_identity_evidence: Literal[True] = True
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_record(self):
        _unique(self.source_attribute_refs, "source_attribute_refs")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class RecordLinkageBlockingRule(BaseModel):
    blocking_rule_id: str = Field(min_length=2, max_length=500)
    name: str = Field(min_length=1, max_length=500)
    key_expression: str = Field(min_length=1, max_length=4000)
    feature_refs: list[str] = Field(default_factory=list)
    deterministic: bool = True
    recall_risk_documented: Literal[True] = True
    blocking_only_reduces_candidate_search_space: Literal[True] = True
    block_membership_is_not_identity_evidence: Literal[True] = True
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_record(self):
        _unique(self.feature_refs, "feature_refs")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class RecordLinkageCandidatePair(BaseModel):
    linkage_pair_id: str = Field(min_length=2, max_length=500)
    left_entity_ref: str = Field(min_length=2, max_length=1000)
    right_entity_ref: str = Field(min_length=2, max_length=1000)
    left_source_identity_assertion_refs: list[str] = Field(min_length=1)
    right_source_identity_assertion_refs: list[str] = Field(min_length=1)
    blocking_rule_refs: list[str] = Field(min_length=1)
    temporal_snapshot_refs: list[str] = Field(default_factory=list)
    candidate_generation_run_ref: str = Field(min_length=2, max_length=1000)
    candidate_pair_is_not_identity_fact: Literal[True] = True
    candidate_generation_is_not_identity_evidence: Literal[True] = True
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_record(self):
        if self.left_entity_ref == self.right_entity_ref:
            raise ValueError("record linkage pair requires two distinct entities")
        for values, label in (
            (self.left_source_identity_assertion_refs, "left_source_identity_assertion_refs"),
            (self.right_source_identity_assertion_refs, "right_source_identity_assertion_refs"),
            (self.blocking_rule_refs, "blocking_rule_refs"),
            (self.temporal_snapshot_refs, "temporal_snapshot_refs"),
        ):
            _unique(values, label)
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class RecordLinkageFeatureObservation(BaseModel):
    feature_observation_id: str = Field(min_length=2, max_length=500)
    linkage_pair_ref: str = Field(min_length=2, max_length=500)
    feature_ref: str = Field(min_length=2, max_length=500)
    comparison_state: FeatureComparisonState
    raw_value: float | str | bool | None = None
    normalized_value: float | None = None
    log_likelihood_ratio: float | None = None
    source_refs: list[str] = Field(min_length=1)
    provenance_refs: list[str] = Field(min_length=1)
    feature_observation_is_model_input_not_identity_fact: Literal[True] = True
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_record(self):
        _unique(self.source_refs, "source_refs")
        _unique(self.provenance_refs, "provenance_refs")
        if self.normalized_value is not None and not isfinite(self.normalized_value):
            raise ValueError("normalized_value must be finite")
        if self.log_likelihood_ratio is not None and not isfinite(self.log_likelihood_ratio):
            raise ValueError("log_likelihood_ratio must be finite")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class RecordLinkageModelSpecification(BaseModel):
    linkage_model_id: str = Field(min_length=2, max_length=500)
    model_name: str = Field(min_length=1, max_length=500)
    method: LinkageMethod
    model_version: str = Field(min_length=1, max_length=200)
    feature_refs: list[str] = Field(min_length=1)
    blocking_rule_refs: list[str] = Field(min_length=1)
    training_dataset_ref: str | None = Field(default=None, max_length=1000)
    training_run_ref: str | None = Field(default=None, max_length=1000)
    calibration_ref: str | None = Field(default=None, max_length=500)
    runtime_ref: str = Field(min_length=2, max_length=1000)
    model_output_is_advisory: Literal[True] = True
    model_cannot_mutate_identity_graph: Literal[True] = True
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_record(self):
        _unique(self.feature_refs, "feature_refs")
        _unique(self.blocking_rule_refs, "blocking_rule_refs")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class MatchProbabilityCalibration(BaseModel):
    calibration_id: str = Field(min_length=2, max_length=500)
    model_ref: str = Field(min_length=2, max_length=500)
    method: str = Field(min_length=1, max_length=500)
    evaluation_dataset_ref: str = Field(min_length=2, max_length=1000)
    brier_score: float | None = Field(default=None, ge=0.0)
    expected_calibration_error: float | None = Field(default=None, ge=0.0)
    calibrated_at: str = Field(min_length=10, max_length=80)
    calibration_does_not_convert_probability_to_fact: Literal[True] = True
    metadata: dict[str, Any] = Field(default_factory=dict)

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class EntityMatchProbabilityRecord(BaseModel):
    entity_match_probability_id: str = Field(min_length=2, max_length=500)
    linkage_pair_ref: str = Field(min_length=2, max_length=500)
    model_ref: str = Field(min_length=2, max_length=500)
    calibration_ref: str | None = Field(default=None, max_length=500)
    feature_observation_refs: list[str] = Field(min_length=1)
    raw_score: float
    match_probability: float = Field(ge=0.0, le=1.0)
    nonmatch_probability: float = Field(ge=0.0, le=1.0)
    scoring_run_ref: str = Field(min_length=2, max_length=1000)
    model_artifact_ref: str = Field(min_length=2, max_length=1000)
    provenance_refs: list[str] = Field(min_length=1)
    is_identity_fact: Literal[False] = False
    is_identity_evidence: Literal[False] = False
    match_probability_is_not_identity_fact: Literal[True] = True
    nonmatch_probability_is_not_proof_of_distinct_identity: Literal[True] = True
    probability_cannot_authorize_merge: Literal[True] = True
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_record(self):
        _unique(self.feature_observation_refs, "feature_observation_refs")
        _unique(self.provenance_refs, "provenance_refs")
        if abs((self.match_probability + self.nonmatch_probability) - 1.0) > 1e-6:
            raise ValueError("match and nonmatch probabilities must sum to 1")
        if not isfinite(self.raw_score):
            raise ValueError("raw_score must be finite")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class EntityMatchThresholdPolicy(BaseModel):
    threshold_policy_id: str = Field(min_length=2, max_length=500)
    reject_below: float = Field(ge=0.0, le=1.0)
    review_at_or_above: float = Field(ge=0.0, le=1.0)
    support_candidate_at_or_above: float = Field(ge=0.0, le=1.0)
    human_review_required_for_supported_candidate: Literal[True] = True
    threshold_crossing_is_not_identity_fact: Literal[True] = True
    threshold_crossing_cannot_authorize_merge: Literal[True] = True
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_record(self):
        if not (self.reject_below <= self.review_at_or_above <= self.support_candidate_at_or_above):
            raise ValueError("thresholds must be monotonic")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class PairwiseEntityMatchDecision(BaseModel):
    pairwise_match_decision_id: str = Field(min_length=2, max_length=500)
    linkage_pair_ref: str = Field(min_length=2, max_length=500)
    probability_record_ref: str = Field(min_length=2, max_length=500)
    threshold_policy_ref: str = Field(min_length=2, max_length=500)
    decision_state: MatchDecisionState
    candidate_entity_match_ref: str | None = Field(default=None, max_length=500)
    review_refs: list[str] = Field(default_factory=list)
    decision_is_not_canonical_identity: Literal[True] = True
    decision_does_not_create_equivalence_edge: Literal[True] = True
    downstream_v377_identity_resolution_required: Literal[True] = True
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_record(self):
        _unique(self.review_refs, "review_refs")
        if self.decision_state == MatchDecisionState.candidate_supported:
            if not self.candidate_entity_match_ref:
                raise ValueError("supported candidate requires candidate_entity_match_ref")
            if not self.review_refs:
                raise ValueError("supported candidate requires review_refs")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class EntityMatchReviewRecord(BaseModel):
    match_review_id: str = Field(min_length=2, max_length=500)
    pairwise_match_decision_ref: str = Field(min_length=2, max_length=500)
    reviewer_ref: str = Field(min_length=2, max_length=1000)
    disposition: MatchReviewDisposition
    identity_evidence_refs: list[str] = Field(default_factory=list)
    considered_probability_record_refs: list[str] = Field(min_length=1)
    rationale: str = Field(min_length=1, max_length=8000)
    reviewed_at: str = Field(min_length=10, max_length=80)
    probability_is_context_not_identity_evidence: Literal[True] = True
    review_does_not_merge_entities: Literal[True] = True
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_record(self):
        _unique(self.identity_evidence_refs, "identity_evidence_refs")
        _unique(self.considered_probability_record_refs, "considered_probability_record_refs")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class RecordLinkageEvaluationSummary(BaseModel):
    evaluation_id: str = Field(min_length=2, max_length=500)
    model_ref: str = Field(min_length=2, max_length=500)
    evaluation_dataset_ref: str = Field(min_length=2, max_length=1000)
    threshold_policy_ref: str = Field(min_length=2, max_length=500)
    precision: float = Field(ge=0.0, le=1.0)
    recall: float = Field(ge=0.0, le=1.0)
    f1: float = Field(ge=0.0, le=1.0)
    roc_auc: float | None = Field(default=None, ge=0.0, le=1.0)
    pr_auc: float | None = Field(default=None, ge=0.0, le=1.0)
    false_merge_risk_documented: Literal[True] = True
    false_split_risk_documented: Literal[True] = True
    evaluation_metric_is_not_identity_truth_measure: Literal[True] = True
    metadata: dict[str, Any] = Field(default_factory=dict)

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class ProbabilisticRecordLinkageBundle(BaseModel):
    temporal_identity_bundle: TemporalIdentityIntelligenceBundle
    feature_definitions: list[RecordLinkageFeatureDefinition]
    blocking_rules: list[RecordLinkageBlockingRule]
    candidate_pairs: list[RecordLinkageCandidatePair]
    feature_observations: list[RecordLinkageFeatureObservation]
    model_specifications: list[RecordLinkageModelSpecification]
    calibrations: list[MatchProbabilityCalibration]
    probability_records: list[EntityMatchProbabilityRecord]
    threshold_policies: list[EntityMatchThresholdPolicy]
    decisions: list[PairwiseEntityMatchDecision]
    reviews: list[EntityMatchReviewRecord]
    evaluations: list[RecordLinkageEvaluationSummary]
    match_probability_is_not_identity_fact: Literal[True] = True
    linkage_output_is_not_identity_evidence: Literal[True] = True
    automatic_merge_allowed: Literal[False] = False
    automatic_split_allowed: Literal[False] = False
    identity_graph_mutation_performed: Literal[False] = False

    @model_validator(mode="after")
    def validate_bundle(self):
        base = self.temporal_identity_bundle.entity_resolution_identity_graph_bundle
        entity_ids = {x.entity_id for x in base.entities}
        source_assertion_ids = {x.source_identity_assertion_id for x in base.source_identity_assertions}
        evidence_ids = {x.identity_evidence_id for x in base.identity_evidence_items}
        candidate_match_ids = {x.candidate_match_id for x in base.candidate_matches}
        temporal_snapshot_ids = {x.temporal_snapshot_id for x in self.temporal_identity_bundle.temporal_snapshots}

        def ids(items, attr, label):
            values=[getattr(x, attr) for x in items]; _unique(values,label); return set(values)

        feature_ids=ids(self.feature_definitions,"linkage_feature_id","linkage_feature_ids")
        blocking_ids=ids(self.blocking_rules,"blocking_rule_id","blocking_rule_ids")
        pair_ids=ids(self.candidate_pairs,"linkage_pair_id","linkage_pair_ids")
        observation_ids=ids(self.feature_observations,"feature_observation_id","feature_observation_ids")
        model_ids=ids(self.model_specifications,"linkage_model_id","linkage_model_ids")
        calibration_ids=ids(self.calibrations,"calibration_id","calibration_ids")
        probability_ids=ids(self.probability_records,"entity_match_probability_id","probability_record_ids")
        threshold_ids=ids(self.threshold_policies,"threshold_policy_id","threshold_policy_ids")
        decision_ids=ids(self.decisions,"pairwise_match_decision_id","decision_ids")
        review_ids=ids(self.reviews,"match_review_id","review_ids")
        ids(self.evaluations,"evaluation_id","evaluation_ids")

        for rule in self.blocking_rules:
            if not set(rule.feature_refs) <= feature_ids: raise ValueError("blocking rule references unknown feature")
        for pair in self.candidate_pairs:
            if pair.left_entity_ref not in entity_ids or pair.right_entity_ref not in entity_ids: raise ValueError("candidate pair references unknown entity")
            if not set(pair.left_source_identity_assertion_refs + pair.right_source_identity_assertion_refs) <= source_assertion_ids: raise ValueError("candidate pair references unknown source identity assertion")
            if not set(pair.blocking_rule_refs) <= blocking_ids: raise ValueError("candidate pair references unknown blocking rule")
            if not set(pair.temporal_snapshot_refs) <= temporal_snapshot_ids: raise ValueError("candidate pair references unknown temporal snapshot")
        for obs in self.feature_observations:
            if obs.linkage_pair_ref not in pair_ids: raise ValueError("feature observation references unknown pair")
            if obs.feature_ref not in feature_ids: raise ValueError("feature observation references unknown feature")
        for model in self.model_specifications:
            if not set(model.feature_refs) <= feature_ids: raise ValueError("model references unknown feature")
            if not set(model.blocking_rule_refs) <= blocking_ids: raise ValueError("model references unknown blocking rule")
            if model.calibration_ref and model.calibration_ref not in calibration_ids: raise ValueError("model references unknown calibration")
        for calibration in self.calibrations:
            if calibration.model_ref not in model_ids: raise ValueError("calibration references unknown model")
        for score in self.probability_records:
            if score.linkage_pair_ref not in pair_ids: raise ValueError("probability references unknown pair")
            if score.model_ref not in model_ids: raise ValueError("probability references unknown model")
            if score.calibration_ref and score.calibration_ref not in calibration_ids: raise ValueError("probability references unknown calibration")
            if not set(score.feature_observation_refs) <= observation_ids: raise ValueError("probability references unknown feature observation")
        for decision in self.decisions:
            if decision.linkage_pair_ref not in pair_ids: raise ValueError("decision references unknown pair")
            if decision.probability_record_ref not in probability_ids: raise ValueError("decision references unknown probability record")
            if decision.threshold_policy_ref not in threshold_ids: raise ValueError("decision references unknown threshold policy")
            if decision.candidate_entity_match_ref and decision.candidate_entity_match_ref not in candidate_match_ids: raise ValueError("decision references unknown v3.77 candidate match")
            if not set(decision.review_refs) <= review_ids: raise ValueError("decision references unknown review")
        for review in self.reviews:
            if review.pairwise_match_decision_ref not in decision_ids: raise ValueError("review references unknown decision")
            if not set(review.identity_evidence_refs) <= evidence_ids: raise ValueError("review references unknown identity evidence")
            if not set(review.considered_probability_record_refs) <= probability_ids: raise ValueError("review references unknown probability record")
        for evaluation in self.evaluations:
            if evaluation.model_ref not in model_ids: raise ValueError("evaluation references unknown model")
            if evaluation.threshold_policy_ref not in threshold_ids: raise ValueError("evaluation references unknown threshold policy")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


def reference_probabilistic_record_linkage_bundle() -> ProbabilisticRecordLinkageBundle:
    temporal = reference_temporal_identity_intelligence_bundle()
    base = temporal.entity_resolution_identity_graph_bundle
    left, right = base.entities[0].entity_id, base.entities[1].entity_id
    left_src = [base.source_identity_assertions[0].source_identity_assertion_id]
    right_src = [base.source_identity_assertions[1].source_identity_assertion_id]

    features = [
        RecordLinkageFeatureDefinition(linkage_feature_id="linkage-feature:normalized-name:v1",name="Normalized name similarity",feature_kind=LinkageFeatureKind.string_similarity,description="Synthetic normalized organization-name similarity.",source_attribute_refs=["attribute:canonical-label","attribute:alias"],comparison_function_ref="comparison:jaro-winkler-normalized:v1",missing_value_policy="mark-missing",metadata={"synthetic_reference":True}),
        RecordLinkageFeatureDefinition(linkage_feature_id="linkage-feature:registry-identifier:v1",name="Registry identifier agreement",feature_kind=LinkageFeatureKind.identifier,description="Synthetic governed comparison of registry identifiers.",source_attribute_refs=["attribute:registry-identifier"],comparison_function_ref="comparison:exact-normalized:v1",missing_value_policy="mark-missing",metadata={"synthetic_reference":True}),
        RecordLinkageFeatureDefinition(linkage_feature_id="linkage-feature:temporal-compatibility:v1",name="Temporal compatibility",feature_kind=LinkageFeatureKind.temporal,description="Synthetic temporal compatibility signal; not identity evidence.",source_attribute_refs=["attribute:validity-window"],comparison_function_ref="comparison:temporal-overlap:v1",missing_value_policy="unknown",metadata={"synthetic_reference":True}),
    ]
    blocking = RecordLinkageBlockingRule(blocking_rule_id="blocking-rule:synthetic:name-prefix:v1",name="Normalized-name prefix blocking",key_expression="normalized_name_prefix(8)",feature_refs=[features[0].linkage_feature_id],metadata={"synthetic_reference":True})
    pair = RecordLinkageCandidatePair(linkage_pair_id="linkage-pair:synthetic:northstar-a-b:v1",left_entity_ref=left,right_entity_ref=right,left_source_identity_assertion_refs=left_src,right_source_identity_assertion_refs=right_src,blocking_rule_refs=[blocking.blocking_rule_id],temporal_snapshot_refs=[],candidate_generation_run_ref="linkage-run:synthetic:blocking:v1",metadata={"synthetic_reference":True})
    observations = [
        RecordLinkageFeatureObservation(feature_observation_id="feature-observation:synthetic:name:v1",linkage_pair_ref=pair.linkage_pair_id,feature_ref=features[0].linkage_feature_id,comparison_state=FeatureComparisonState.agree,raw_value=0.93,normalized_value=0.93,log_likelihood_ratio=1.8,source_refs=["source:synthetic:registry-a","source:synthetic:annual-report-b"],provenance_refs=["provenance:synthetic:linkage:name:v1"],metadata={"synthetic_reference":True}),
        RecordLinkageFeatureObservation(feature_observation_id="feature-observation:synthetic:identifier:v1",linkage_pair_ref=pair.linkage_pair_id,feature_ref=features[1].linkage_feature_id,comparison_state=FeatureComparisonState.agree,raw_value=True,normalized_value=1.0,log_likelihood_ratio=4.2,source_refs=["source:synthetic:registry-a","source:synthetic:registry-crosscheck-b"],provenance_refs=["provenance:synthetic:linkage:identifier:v1"],metadata={"synthetic_reference":True}),
        RecordLinkageFeatureObservation(feature_observation_id="feature-observation:synthetic:temporal:v1",linkage_pair_ref=pair.linkage_pair_id,feature_ref=features[2].linkage_feature_id,comparison_state=FeatureComparisonState.unknown,raw_value=None,normalized_value=0.5,log_likelihood_ratio=0.0,source_refs=["source:synthetic:registry-a","source:synthetic:annual-report-b"],provenance_refs=["provenance:synthetic:linkage:temporal:v1"],metadata={"synthetic_reference":True,"note":"temporal signal intentionally neutral"}),
    ]
    model = RecordLinkageModelSpecification(linkage_model_id="linkage-model:synthetic:fellegi-sunter:v1",model_name="Synthetic Fellegi-Sunter linkage model",method=LinkageMethod.fellegi_sunter,model_version="1.0.0",feature_refs=[x.linkage_feature_id for x in features],blocking_rule_refs=[blocking.blocking_rule_id],training_dataset_ref="dataset:synthetic:record-linkage-training:v1",training_run_ref="training-run:synthetic:record-linkage:v1",calibration_ref="calibration:synthetic:linkage:v1",runtime_ref="runtime:workspace:record-linkage:v1",metadata={"synthetic_reference":True})
    calibration = MatchProbabilityCalibration(calibration_id="calibration:synthetic:linkage:v1",model_ref=model.linkage_model_id,method="isotonic",evaluation_dataset_ref="dataset:synthetic:record-linkage-evaluation:v1",brier_score=0.061,expected_calibration_error=0.027,calibrated_at="2026-09-29T18:00:00Z",metadata={"synthetic_reference":True})
    probability = EntityMatchProbabilityRecord(entity_match_probability_id="match-probability:synthetic:northstar-a-b:v1",linkage_pair_ref=pair.linkage_pair_id,model_ref=model.linkage_model_id,calibration_ref=calibration.calibration_id,feature_observation_refs=[x.feature_observation_id for x in observations],raw_score=6.0,match_probability=0.97,nonmatch_probability=0.03,scoring_run_ref="linkage-run:synthetic:score:v1",model_artifact_ref="model-artifact:synthetic:record-linkage:v1",provenance_refs=["provenance:synthetic:record-linkage-score:v1"],metadata={"synthetic_reference":True})
    threshold = EntityMatchThresholdPolicy(threshold_policy_id="linkage-threshold-policy:reference:v1",reject_below=0.20,review_at_or_above=0.60,support_candidate_at_or_above=0.90,metadata={"synthetic_reference":True})
    review_ids=["linkage-review:synthetic:a:v1","linkage-review:synthetic:b:v1"]
    decision = PairwiseEntityMatchDecision(pairwise_match_decision_id="pairwise-match-decision:synthetic:northstar-a-b:v1",linkage_pair_ref=pair.linkage_pair_id,probability_record_ref=probability.entity_match_probability_id,threshold_policy_ref=threshold.threshold_policy_id,decision_state=MatchDecisionState.candidate_supported,candidate_entity_match_ref=base.candidate_matches[0].candidate_match_id,review_refs=review_ids,metadata={"synthetic_reference":True})
    reviews = [
        EntityMatchReviewRecord(match_review_id=review_ids[0],pairwise_match_decision_ref=decision.pairwise_match_decision_id,reviewer_ref="reviewer:synthetic:linkage-a:v1",disposition=MatchReviewDisposition.support_candidate,identity_evidence_refs=[base.identity_evidence_items[0].identity_evidence_id],considered_probability_record_refs=[probability.entity_match_probability_id],rationale="Synthetic reviewer A treats probability as context and uses provenance-bearing identity evidence for candidate support.",reviewed_at="2026-09-29T18:05:00Z",metadata={"synthetic_reference":True}),
        EntityMatchReviewRecord(match_review_id=review_ids[1],pairwise_match_decision_ref=decision.pairwise_match_decision_id,reviewer_ref="reviewer:synthetic:linkage-b:v1",disposition=MatchReviewDisposition.support_candidate,identity_evidence_refs=[base.identity_evidence_items[1].identity_evidence_id],considered_probability_record_refs=[probability.entity_match_probability_id],rationale="Synthetic reviewer B independently reviews source evidence; the model score does not establish identity.",reviewed_at="2026-09-29T18:07:00Z",metadata={"synthetic_reference":True}),
    ]
    evaluation = RecordLinkageEvaluationSummary(evaluation_id="linkage-evaluation:synthetic:v1",model_ref=model.linkage_model_id,evaluation_dataset_ref="dataset:synthetic:record-linkage-evaluation:v1",threshold_policy_ref=threshold.threshold_policy_id,precision=0.94,recall=0.91,f1=0.925,roc_auc=0.97,pr_auc=0.95,metadata={"synthetic_reference":True})
    return ProbabilisticRecordLinkageBundle(temporal_identity_bundle=temporal,feature_definitions=features,blocking_rules=[blocking],candidate_pairs=[pair],feature_observations=observations,model_specifications=[model],calibrations=[calibration],probability_records=[probability],threshold_policies=[threshold],decisions=[decision],reviews=reviews,evaluations=[evaluation])


def contract_document() -> dict[str, Any]:
    b=reference_probabilistic_record_linkage_bundle()
    return {
        "ok": True,
        "release": CORE_RELEASE,
        "contract": CONTRACT_VERSION,
        "extends_contracts": ["sc.core.entity-resolution-identity-graph-foundation.v1","sc.core.temporal-identity-alias-name-variant-intelligence.v1"],
        "object_types": ["RecordLinkageFeatureDefinition","RecordLinkageBlockingRule","RecordLinkageCandidatePair","RecordLinkageFeatureObservation","RecordLinkageModelSpecification","MatchProbabilityCalibration","EntityMatchProbabilityRecord","EntityMatchThresholdPolicy","PairwiseEntityMatchDecision","EntityMatchReviewRecord","RecordLinkageEvaluationSummary","ProbabilisticRecordLinkageBundle"],
        "principles": {
            "match_probability_is_not_identity_fact": True,
            "nonmatch_probability_is_not_proof_of_distinct_identity": True,
            "feature_agreement_is_not_identity_evidence": True,
            "blocking_membership_is_not_identity_evidence": True,
            "calibration_does_not_convert_probability_to_fact": True,
            "threshold_crossing_is_not_identity_fact": True,
            "v377_identity_resolution_remains_authoritative_for_merge_authorization": True,
        },
        "capabilities": {
            "governed_linkage_features": True,
            "blocking_and_candidate_generation_provenance": True,
            "pairwise_feature_comparisons": True,
            "probabilistic_match_scoring": True,
            "probability_calibration": True,
            "review_threshold_policies": True,
            "human_review_records": True,
            "linkage_evaluation_metrics": True,
            "temporal_identity_compatibility": True,
        },
        "boundaries": {
            "core_executes_record_linkage_model": False,
            "core_trains_record_linkage_model": False,
            "core_treats_probability_as_identity_evidence": False,
            "core_auto_merges_entities_from_probability": False,
            "core_auto_splits_entities_from_nonmatch_probability": False,
            "core_creates_canonical_equivalence_edge_from_linkage_output": False,
            "core_bypasses_v377_identity_review_policy": False,
            "identity_graph_mutation_performed": False,
        },
        "roadmap_integration": {
            "extends_v3770_entity_resolution_foundation": True,
            "extends_v3780_temporal_identity_intelligence": True,
            "prepares_v3800_cross_source_entity_reconciliation": True,
            "preserves_v3760_evidence_validation_boundary": True,
        },
        "reference": {
            "feature_definitions": len(b.feature_definitions),
            "blocking_rules": len(b.blocking_rules),
            "candidate_pairs": len(b.candidate_pairs),
            "feature_observations": len(b.feature_observations),
            "probability_records": len(b.probability_records),
            "reviews": len(b.reviews),
            "match_probability": b.probability_records[0].match_probability,
            "decision_state": b.decisions[0].decision_state.value,
            "identity_graph_mutation_performed": b.identity_graph_mutation_performed,
            "bundle_fingerprint_sha256": b.fingerprint(),
        },
        "database_migration": "none",
    }
