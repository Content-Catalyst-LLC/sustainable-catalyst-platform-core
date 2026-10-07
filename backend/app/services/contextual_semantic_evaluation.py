from __future__ import annotations

from enum import Enum
from functools import lru_cache
from typing import Any, Literal

from pydantic import BaseModel, Field, model_validator

from .computational_runtime_objects import canonical_sha256
from .context_semantic_frame import InterpretationMethod
from .multilingual_context_semantic_alignment import (
    MultilingualContextSemanticAlignmentBundle,
    reference_multilingual_context_semantic_alignment_bundle,
)

CORE_RELEASE = "4.9.0"
CONTRACT_VERSION = "sc.core.contextual-semantic-evaluation-benchmark-framework.v1"
PREDECESSOR_CONTRACT = "sc.core.multilingual-context-semantic-alignment.v1"

EXTENDS_CONTRACTS = [
    PREDECESSOR_CONTRACT,
    "sc.core.cross-document-context-graph.v1",
    "sc.core.pragmatic-meaning-speech-act-communicative-intent.v1",
    "sc.core.epistemic-modal-negation-certainty-semantics.v1",
    "sc.core.temporal-spatial-language-grounding.v1",
    "sc.core.coreference-reference-referential-identity-intelligence.v1",
    "sc.core.discourse-structure-rhetorical-semantics.v1",
    "sc.core.context-object-semantic-frame-foundation.v1",
    "sc.core.cross-lingual-semantic-linguistic-exchange.v1",
]


def _unique(values: list[str], label: str) -> None:
    if len(values) != len(set(values)):
        raise ValueError(f"{label} must be unique")


class EvaluationTask(str, Enum):
    coreference_resolution = "coreference-resolution"
    discourse_relation = "discourse-relation"
    temporal_grounding = "temporal-grounding"
    spatial_grounding = "spatial-grounding"
    epistemic_classification = "epistemic-classification"
    negation_scope = "negation-scope"
    modality_classification = "modality-classification"
    pragmatic_classification = "pragmatic-classification"
    cross_document_continuity = "cross-document-continuity"
    cross_language_alignment = "cross-language-alignment"
    translation_drift = "translation-drift"
    ambiguity_preservation = "ambiguity-preservation"


class BenchmarkReviewState(str, Enum):
    draft = "draft"
    reviewed = "reviewed"
    deprecated = "deprecated"
    superseded = "superseded"


class EvaluationStatus(str, Enum):
    pass_ = "pass"
    partial = "partial"
    fail = "fail"
    not_scored = "not-scored"


class ErrorCategory(str, Enum):
    wrong_referent = "wrong-referent"
    discourse_misclassification = "discourse-misclassification"
    temporal_normalization_error = "temporal-normalization-error"
    spatial_grounding_error = "spatial-grounding-error"
    epistemic_overstatement = "epistemic-overstatement"
    negation_scope_error = "negation-scope-error"
    modality_collapse = "modality-collapse"
    pragmatic_misclassification = "pragmatic-misclassification"
    identity_overmerge = "identity-overmerge"
    translation_drift = "translation-drift"
    cultural_semantic_flattening = "cultural-semantic-flattening"
    ambiguity_erasure = "ambiguity-erasure"
    unsupported_field = "unsupported-field"


class MetricDirection(str, Enum):
    higher_is_better = "higher-is-better"
    lower_is_better = "lower-is-better"


class ContextualSemanticEvaluationPolicy(BaseModel):
    policy_id: str = Field(min_length=3, max_length=500)
    benchmark_gold_is_reviewed_target_not_world_truth: Literal[True] = True
    benchmark_pass_does_not_establish_claim_truth: Literal[True] = True
    benchmark_pass_does_not_establish_evidence_validity: Literal[True] = True
    benchmark_score_does_not_establish_model_safety: Literal[True] = True
    benchmark_score_does_not_establish_domain_authority: Literal[True] = True
    original_language_remains_authoritative_representation: Literal[True] = True
    translations_remain_derived_representations: Literal[True] = True
    unresolved_ambiguity_may_be_correct_behavior: Literal[True] = True
    competing_interpretations_may_be_benchmark_valid: Literal[True] = True
    benchmark_cases_are_versioned_and_provenanced: Literal[True] = True
    evaluation_runs_are_reproducible_and_supersedable: Literal[True] = True
    predecessor_objects_remain_immutable: Literal[True] = True
    context_graph_mutation_authorized: Literal[False] = False
    identity_graph_mutation_authorized: Literal[False] = False
    evidence_graph_mutation_authorized: Literal[False] = False
    knowledge_graph_mutation_authorized: Literal[False] = False


class BenchmarkGoldAnnotation(BaseModel):
    annotation_id: str = Field(min_length=3, max_length=500)
    case_ref: str = Field(min_length=3, max_length=500)
    expected_outcome: dict[str, Any] = Field(min_length=1)
    accepted_alternatives: list[dict[str, Any]] = Field(default_factory=list)
    source_refs: list[str] = Field(min_length=1)
    reviewer_ref: str = Field(min_length=3, max_length=500)
    rationale: str = Field(min_length=3, max_length=5000)
    review_state: Literal[BenchmarkReviewState.reviewed] = BenchmarkReviewState.reviewed
    annotation_is_benchmark_target_not_world_truth: Literal[True] = True

    @model_validator(mode="after")
    def validate_annotation(self):
        _unique(self.source_refs, "gold source_refs")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class ContextualSemanticBenchmarkCase(BaseModel):
    case_id: str = Field(min_length=3, max_length=500)
    task: EvaluationTask
    title: str = Field(min_length=3, max_length=500)
    source_refs: list[str] = Field(min_length=1)
    language_refs: list[str] = Field(min_length=1)
    metric_refs: list[str] = Field(min_length=1)
    gold_annotation_ref: str = Field(min_length=3, max_length=500)
    difficulty: Literal["basic", "intermediate", "advanced"]
    context_required: Literal[True] = True
    original_language_required: bool = False
    ambiguity_is_scored: bool = False
    benchmark_case_does_not_assert_source_truth: Literal[True] = True
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_case(self):
        _unique(self.source_refs, "case source_refs")
        _unique(self.language_refs, "case language_refs")
        _unique(self.metric_refs, "case metric_refs")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class EvaluationPrediction(BaseModel):
    prediction_id: str = Field(min_length=3, max_length=500)
    case_ref: str = Field(min_length=3, max_length=500)
    system_ref: str = Field(min_length=3, max_length=500)
    predicted_outcome: dict[str, Any] = Field(min_length=1)
    confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    provenance_ref: str = Field(min_length=3, max_length=500)
    prediction_is_interpretation_not_truth_verdict: Literal[True] = True

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class BenchmarkCaseEvaluation(BaseModel):
    evaluation_id: str = Field(min_length=3, max_length=500)
    case_ref: str = Field(min_length=3, max_length=500)
    prediction_ref: str = Field(min_length=3, max_length=500)
    gold_annotation_ref: str = Field(min_length=3, max_length=500)
    status: EvaluationStatus
    score: float = Field(ge=0.0, le=1.0)
    matched_fields: list[str] = Field(default_factory=list)
    mismatched_fields: list[str] = Field(default_factory=list)
    error_categories: list[ErrorCategory] = Field(default_factory=list)
    qualification_notes: list[str] = Field(default_factory=list)
    evaluation_does_not_establish_claim_truth: Literal[True] = True

    @model_validator(mode="after")
    def validate_evaluation(self):
        _unique(self.matched_fields, "matched_fields")
        _unique(self.mismatched_fields, "mismatched_fields")
        _unique([x.value for x in self.error_categories], "error_categories")
        if self.status == EvaluationStatus.pass_ and self.score != 1.0:
            raise ValueError("pass evaluation requires score 1.0")
        if self.status == EvaluationStatus.fail and self.score == 1.0:
            raise ValueError("fail evaluation cannot have score 1.0")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class MetricDefinition(BaseModel):
    metric_id: str = Field(min_length=3, max_length=500)
    name: str = Field(min_length=3, max_length=500)
    description: str = Field(min_length=3, max_length=3000)
    direction: MetricDirection = MetricDirection.higher_is_better
    minimum: float = 0.0
    maximum: float = 1.0
    benchmark_target_is_not_truth_threshold: Literal[True] = True

    @model_validator(mode="after")
    def validate_range(self):
        if self.maximum <= self.minimum:
            raise ValueError("metric maximum must exceed minimum")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class MetricResult(BaseModel):
    result_id: str = Field(min_length=3, max_length=500)
    metric_ref: str = Field(min_length=3, max_length=500)
    case_refs: list[str] = Field(min_length=1)
    numerator: float = Field(ge=0.0)
    denominator: int = Field(ge=1)
    score: float = Field(ge=0.0, le=1.0)
    qualifications: list[str] = Field(default_factory=list)
    score_is_benchmark_measure_not_truth_probability: Literal[True] = True

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class EvaluationProvenanceRecord(BaseModel):
    provenance_id: str = Field(min_length=3, max_length=500)
    subject_refs: list[str] = Field(min_length=1)
    method: InterpretationMethod
    produced_by_ref: str = Field(min_length=3, max_length=500)
    source_refs: list[str] = Field(min_length=1)
    reviewer_ref: str | None = Field(default=None, max_length=500)
    notes: list[str] = Field(default_factory=list)
    evaluation_output_is_advisory: Literal[True] = True
    provenance_does_not_establish_truth_or_authority: Literal[True] = True

    @model_validator(mode="after")
    def validate_provenance(self):
        _unique(self.subject_refs, "provenance subject_refs")
        _unique(self.source_refs, "provenance source_refs")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class ContextualSemanticEvaluationRun(BaseModel):
    run_id: str = Field(min_length=3, max_length=500)
    benchmark_snapshot_ref: str = Field(min_length=3, max_length=500)
    system_ref: str = Field(min_length=3, max_length=500)
    prediction_refs: list[str] = Field(min_length=1)
    case_evaluation_refs: list[str] = Field(min_length=1)
    metric_result_refs: list[str] = Field(min_length=1)
    overall_score: float = Field(ge=0.0, le=1.0)
    provenance_ref: str = Field(min_length=3, max_length=500)
    reproducible: Literal[True] = True
    run_does_not_establish_system_truthfulness_or_safety: Literal[True] = True

    @model_validator(mode="after")
    def validate_run(self):
        _unique(self.prediction_refs, "prediction_refs")
        _unique(self.case_evaluation_refs, "case_evaluation_refs")
        _unique(self.metric_result_refs, "metric_result_refs")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class BenchmarkSnapshot(BaseModel):
    snapshot_id: str = Field(min_length=3, max_length=500)
    predecessor_fingerprint_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    case_refs: list[str] = Field(min_length=1)
    gold_annotation_refs: list[str] = Field(min_length=1)
    metric_refs: list[str] = Field(min_length=1)
    deterministic_benchmark_fingerprint_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    immutable: Literal[True] = True
    supersedable: Literal[True] = True
    snapshot_does_not_freeze_semantic_truth: Literal[True] = True

    @model_validator(mode="after")
    def validate_snapshot(self):
        _unique(self.case_refs, "snapshot case_refs")
        _unique(self.gold_annotation_refs, "snapshot gold_annotation_refs")
        _unique(self.metric_refs, "snapshot metric_refs")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class ContextualSemanticEvaluationBenchmarkBundle(BaseModel):
    release: Literal["4.9.0"] = "4.9.0"
    contract: Literal[CONTRACT_VERSION] = CONTRACT_VERSION
    predecessor_contract: Literal[PREDECESSOR_CONTRACT] = PREDECESSOR_CONTRACT
    extends_contracts: list[str] = Field(min_length=9)
    policy: ContextualSemanticEvaluationPolicy
    multilingual_context: MultilingualContextSemanticAlignmentBundle
    metric_definitions: list[MetricDefinition] = Field(min_length=5)
    benchmark_cases: list[ContextualSemanticBenchmarkCase] = Field(min_length=10)
    gold_annotations: list[BenchmarkGoldAnnotation] = Field(min_length=10)
    predictions: list[EvaluationPrediction] = Field(min_length=10)
    case_evaluations: list[BenchmarkCaseEvaluation] = Field(min_length=10)
    metric_results: list[MetricResult] = Field(min_length=5)
    provenance_records: list[EvaluationProvenanceRecord] = Field(min_length=1)
    benchmark_snapshots: list[BenchmarkSnapshot] = Field(min_length=1)
    evaluation_runs: list[ContextualSemanticEvaluationRun] = Field(min_length=1)
    database_migration: Literal["none"] = "none"

    @model_validator(mode="after")
    def validate_bundle(self):
        if self.extends_contracts != EXTENDS_CONTRACTS:
            raise ValueError("extends_contracts must preserve v4.9 dependency order")
        if self.multilingual_context.release != "4.8.0" or self.multilingual_context.contract != PREDECESSOR_CONTRACT:
            raise ValueError("v4.9 must embed governed v4.8 multilingual context predecessor")

        for values, label in (
            ([x.metric_id for x in self.metric_definitions], "metric ids"),
            ([x.case_id for x in self.benchmark_cases], "case ids"),
            ([x.annotation_id for x in self.gold_annotations], "annotation ids"),
            ([x.prediction_id for x in self.predictions], "prediction ids"),
            ([x.evaluation_id for x in self.case_evaluations], "evaluation ids"),
            ([x.result_id for x in self.metric_results], "metric result ids"),
            ([x.provenance_id for x in self.provenance_records], "provenance ids"),
            ([x.snapshot_id for x in self.benchmark_snapshots], "snapshot ids"),
            ([x.run_id for x in self.evaluation_runs], "run ids"),
        ):
            _unique(values, label)

        metrics = {x.metric_id: x for x in self.metric_definitions}
        cases = {x.case_id: x for x in self.benchmark_cases}
        gold = {x.annotation_id: x for x in self.gold_annotations}
        preds = {x.prediction_id: x for x in self.predictions}
        evals = {x.evaluation_id: x for x in self.case_evaluations}
        metric_results = {x.result_id: x for x in self.metric_results}
        provenance = {x.provenance_id: x for x in self.provenance_records}
        snapshots = {x.snapshot_id: x for x in self.benchmark_snapshots}

        for case in self.benchmark_cases:
            if case.gold_annotation_ref not in gold:
                raise ValueError("case gold_annotation_ref must resolve")
            if gold[case.gold_annotation_ref].case_ref != case.case_id:
                raise ValueError("gold annotation case_ref must match case")
            for ref in case.metric_refs:
                if ref not in metrics:
                    raise ValueError("case metric_ref must resolve")

        for pred in self.predictions:
            if pred.case_ref not in cases:
                raise ValueError("prediction case_ref must resolve")
            if pred.provenance_ref not in provenance:
                raise ValueError("prediction provenance_ref must resolve")

        for ev in self.case_evaluations:
            if ev.case_ref not in cases or ev.prediction_ref not in preds or ev.gold_annotation_ref not in gold:
                raise ValueError("evaluation references must resolve")
            if preds[ev.prediction_ref].case_ref != ev.case_ref:
                raise ValueError("evaluation prediction must target evaluation case")
            if gold[ev.gold_annotation_ref].case_ref != ev.case_ref:
                raise ValueError("evaluation gold must target evaluation case")

        for result in self.metric_results:
            if result.metric_ref not in metrics:
                raise ValueError("metric result metric_ref must resolve")
            for case_ref in result.case_refs:
                if case_ref not in cases:
                    raise ValueError("metric result case_ref must resolve")

        predecessor_fp = self.multilingual_context.fingerprint()
        for snapshot in self.benchmark_snapshots:
            if snapshot.predecessor_fingerprint_sha256 != predecessor_fp:
                raise ValueError("benchmark snapshot predecessor fingerprint must match v4.8 bundle")
            for ref in snapshot.case_refs:
                if ref not in cases:
                    raise ValueError("snapshot case_ref must resolve")
            for ref in snapshot.gold_annotation_refs:
                if ref not in gold:
                    raise ValueError("snapshot gold_annotation_ref must resolve")
            for ref in snapshot.metric_refs:
                if ref not in metrics:
                    raise ValueError("snapshot metric_ref must resolve")

        for run in self.evaluation_runs:
            if run.benchmark_snapshot_ref not in snapshots:
                raise ValueError("run benchmark_snapshot_ref must resolve")
            if run.provenance_ref not in provenance:
                raise ValueError("run provenance_ref must resolve")
            for ref in run.prediction_refs:
                if ref not in preds:
                    raise ValueError("run prediction_ref must resolve")
            for ref in run.case_evaluation_refs:
                if ref not in evals:
                    raise ValueError("run case_evaluation_ref must resolve")
            for ref in run.metric_result_refs:
                if ref not in metric_results:
                    raise ValueError("run metric_result_ref must resolve")

        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


def _metric_definitions() -> list[MetricDefinition]:
    rows = [
        ("metric:context-resolution-accuracy", "Context Resolution Accuracy", "Accuracy over reference and ambiguity-sensitive contextual resolution cases."),
        ("metric:entity-reference-accuracy", "Entity Reference Accuracy", "Accuracy of referential identity behavior without unauthorized canonical merges."),
        ("metric:temporal-grounding-accuracy", "Temporal Grounding Accuracy", "Accuracy of explicit and relative temporal language grounding."),
        ("metric:spatial-grounding-accuracy", "Spatial Grounding Accuracy", "Accuracy of named-place and spatial-deictic grounding."),
        ("metric:discourse-relation-accuracy", "Discourse Relation Accuracy", "Accuracy of discourse and rhetorical relation interpretation."),
        ("metric:epistemic-classification-accuracy", "Epistemic Classification Accuracy", "Accuracy of epistemic stance, negation, modality, and certainty classification."),
        ("metric:pragmatic-classification-accuracy", "Pragmatic Classification Accuracy", "Accuracy of speech-act and communicative-intent interpretation."),
        ("metric:cross-language-meaning-preservation", "Cross-Language Meaning Preservation", "Preservation of qualified contextual meaning across language representations."),
        ("metric:translation-drift-detection", "Translation Drift Detection Accuracy", "Accuracy at preserving or detecting semantic, cultural, and historical divergence."),
        ("metric:context-graph-consistency", "Context Graph Consistency", "Consistency of cross-document continuity without identity or claim overmerge."),
        ("metric:ambiguity-preservation", "Ambiguity Preservation Accuracy", "Accuracy at retaining unresolved alternatives when the evidence does not justify collapse."),
    ]
    return [MetricDefinition(metric_id=i, name=n, description=d) for i,n,d in rows]


def _case_specs() -> list[tuple[str, EvaluationTask, str, list[str], list[str], list[str], dict[str, Any], str, bool, bool]]:
    return [
        ("benchmark:coreference-it-proposal", EvaluationTask.coreference_resolution, "Resolve pronoun while preserving ranked alternatives", ["reference-expression:it", "coreference-link:it-to-proposal", "candidate-set:it"], ["language:en"], ["metric:context-resolution-accuracy", "metric:entity-reference-accuracy", "metric:ambiguity-preservation"], {"referent_ref":"referent:proposal","review_state":"reviewed","alternatives_preserved":True,"canonical_identity_asserted":False}, "advanced", False, True),
        ("benchmark:discourse-nevertheless-concession", EvaluationTask.discourse_relation, "Classify concessive rhetorical relation", ["discourse-signal:nevertheless", "rhetorical-relation:concession-viability"], ["language:en"], ["metric:context-resolution-accuracy", "metric:discourse-relation-accuracy"], {"relation":"concession","signal":"nevertheless","truth_verdict":False}, "intermediate", False, False),
        ("benchmark:temporal-following-year", EvaluationTask.temporal_grounding, "Ground relative year by explicit derivation", ["temporal-expression:2025", "temporal-expression:following-year", "temporal-grounding:following-year"], ["language:en"], ["metric:context-resolution-accuracy", "metric:temporal-grounding-accuracy"], {"normalized_year":2026,"derivation":"+P1Y","event_occurrence_asserted":False}, "intermediate", False, False),
        ("benchmark:spatial-there-brussels", EvaluationTask.spatial_grounding, "Resolve spatial deixis without canonical geocoding", ["spatial-expression:there", "spatial-expression:brussels", "spatial-grounding:there-to-brussels"], ["language:en"], ["metric:context-resolution-accuracy", "metric:spatial-grounding-accuracy"], {"anchor_ref":"spatial-anchor:brussels-source-place","canonical_geographic_identity":False}, "intermediate", False, False),
        ("benchmark:negation-did-not-reduce", EvaluationTask.negation_scope, "Preserve explicit negation scope", ["proposition:measure-no-emissions-reduction", "negation-scope:measure-no-emissions-reduction"], ["language:en"], ["metric:epistemic-classification-accuracy"], {"negated":True,"scope_ref":"proposition:measure-no-emissions-reduction","claim_truth_asserted":False}, "intermediate", False, False),
        ("benchmark:modality-may-lower-costs", EvaluationTask.modality_classification, "Preserve possibility without converting to probability", ["proposition:may-lower-costs", "modal-scope:may-lower-costs"], ["language:en"], ["metric:epistemic-classification-accuracy"], {"modality":"possibility","numeric_probability":False,"claim_truth_asserted":False}, "intermediate", False, False),
        ("benchmark:epistemic-explicit-uncertainty", EvaluationTask.epistemic_classification, "Classify source-level explicit uncertainty", ["proposition:estimate-uncertain", "assessment:ministry-explicit-uncertainty"], ["language:en"], ["metric:epistemic-classification-accuracy"], {"epistemic_status":"explicit-uncertainty","source_level":True,"evidence_validity_asserted":False}, "intermediate", False, False),
        ("benchmark:pragmatic-warning-alert", EvaluationTask.pragmatic_classification, "Separate warning speech act from alert intent", ["speech-act:warn-disruption", "intent:alert-disruption"], ["language:en"], ["metric:pragmatic-classification-accuracy", "metric:context-resolution-accuracy"], {"speech_act":"warning","communicative_intent":"alert","risk_fact_asserted":False}, "intermediate", False, False),
        ("benchmark:cross-document-actor-continuity", EvaluationTask.cross_document_continuity, "Preserve candidate actor continuity without identity merge", ["edge:ministry:agency:candidate", "thread:institutional-actor-continuity:candidate"], ["language:en"], ["metric:context-graph-consistency", "metric:entity-reference-accuracy", "metric:ambiguity-preservation"], {"state":"proposed","confidence":0.42,"canonical_actor_merge":False,"unresolved_identity_preserved":True}, "advanced", False, True),
        ("benchmark:cross-language-proposal-modality", EvaluationTask.cross_language_alignment, "Preserve possibility modality across Chinese and English", ["context-unit:zh:proposal-cost:v1", "context-unit:en:proposal-cost:v1", "context-alignment:zh-en:proposal-cost:v1"], ["language:zh", "language:en"], ["metric:cross-language-meaning-preservation", "metric:context-resolution-accuracy"], {"relation":"translation-correspondence","modality_preserved":"possibility","original_language_authoritative":True}, "advanced", True, False),
        ("benchmark:governance-cultural-divergence", EvaluationTask.translation_drift, "Preserve cultural semantic divergence for 治理/governance", ["context-unit:zh:governance:v1", "context-unit:en:governance:v1", "divergence:zh-en:governance:v1"], ["language:zh", "language:en"], ["metric:translation-drift-detection", "metric:cross-language-meaning-preservation", "metric:ambiguity-preservation"], {"relation":"culturally-conditioned","exact_equivalence":False,"divergence_preserved":True}, "advanced", True, True),
        ("benchmark:governance-unresolved-spanish", EvaluationTask.ambiguity_preservation, "Keep candidate Spanish governance correspondence unresolved", ["context-alignment:zh-es:governance:v1", "divergence:zh-es:governance:v1"], ["language:zh", "language:es"], ["metric:ambiguity-preservation", "metric:translation-drift-detection", "metric:cross-language-meaning-preservation"], {"review_state":"candidate","universal_equivalence_asserted":False,"unresolved_divergence_preserved":True}, "advanced", True, True),
    ]


def _error_category_for(task: EvaluationTask) -> ErrorCategory:
    return {
        EvaluationTask.coreference_resolution: ErrorCategory.wrong_referent,
        EvaluationTask.discourse_relation: ErrorCategory.discourse_misclassification,
        EvaluationTask.temporal_grounding: ErrorCategory.temporal_normalization_error,
        EvaluationTask.spatial_grounding: ErrorCategory.spatial_grounding_error,
        EvaluationTask.epistemic_classification: ErrorCategory.epistemic_overstatement,
        EvaluationTask.negation_scope: ErrorCategory.negation_scope_error,
        EvaluationTask.modality_classification: ErrorCategory.modality_collapse,
        EvaluationTask.pragmatic_classification: ErrorCategory.pragmatic_misclassification,
        EvaluationTask.cross_document_continuity: ErrorCategory.identity_overmerge,
        EvaluationTask.cross_language_alignment: ErrorCategory.translation_drift,
        EvaluationTask.translation_drift: ErrorCategory.cultural_semantic_flattening,
        EvaluationTask.ambiguity_preservation: ErrorCategory.ambiguity_erasure,
    }[task]


def evaluate_prediction(case: ContextualSemanticBenchmarkCase, gold: BenchmarkGoldAnnotation, prediction: EvaluationPrediction) -> BenchmarkCaseEvaluation:
    if prediction.case_ref != case.case_id or gold.case_ref != case.case_id:
        raise ValueError("case, gold, and prediction must target the same benchmark case")
    expected = gold.expected_outcome
    predicted = prediction.predicted_outcome
    matched = [k for k,v in expected.items() if k in predicted and predicted[k] == v]
    mismatched = [k for k,v in expected.items() if k not in predicted or predicted[k] != v]
    score = len(matched) / len(expected)
    if any(predicted == alt for alt in gold.accepted_alternatives):
        matched = list(expected.keys())
        mismatched = []
        score = 1.0
    if score == 1.0:
        status = EvaluationStatus.pass_
        errors: list[ErrorCategory] = []
    elif score == 0.0:
        status = EvaluationStatus.fail
        errors = [_error_category_for(case.task)]
    else:
        status = EvaluationStatus.partial
        errors = [_error_category_for(case.task)]
    return BenchmarkCaseEvaluation(
        evaluation_id=f"evaluation:{case.case_id.split(':',1)[1]}:reference-baseline",
        case_ref=case.case_id,
        prediction_ref=prediction.prediction_id,
        gold_annotation_ref=gold.annotation_id,
        status=status,
        score=score,
        matched_fields=matched,
        mismatched_fields=mismatched,
        error_categories=errors,
        qualification_notes=["Exact-field reference scoring is deterministic; benchmark success is not a truth or safety claim."],
    )


@lru_cache(maxsize=1)
def reference_contextual_semantic_evaluation_bundle() -> ContextualSemanticEvaluationBenchmarkBundle:
    predecessor = reference_multilingual_context_semantic_alignment_bundle()
    metrics = _metric_definitions()
    cases: list[ContextualSemanticBenchmarkCase] = []
    golds: list[BenchmarkGoldAnnotation] = []
    predictions: list[EvaluationPrediction] = []
    evaluations: list[BenchmarkCaseEvaluation] = []
    prov_pred = "prov:context-evaluation:reference-predictions:v1"
    for case_id, task, title, source_refs, langs, metric_refs, expected, difficulty, original_required, ambiguity in _case_specs():
        ann_id = f"gold:{case_id.split(':',1)[1]}:v1"
        case = ContextualSemanticBenchmarkCase(
            case_id=case_id,
            task=task,
            title=title,
            source_refs=source_refs,
            language_refs=langs,
            metric_refs=metric_refs,
            gold_annotation_ref=ann_id,
            difficulty=difficulty,
            original_language_required=original_required,
            ambiguity_is_scored=ambiguity,
            metadata={"benchmark_family":"contextual-semantics-v4.9"},
        )
        gold = BenchmarkGoldAnnotation(
            annotation_id=ann_id,
            case_ref=case_id,
            expected_outcome=expected,
            accepted_alternatives=[],
            source_refs=source_refs,
            reviewer_ref="reviewer:context-evaluation:v1",
            rationale=f"Reviewed benchmark target anchored to governed Core source objects for {title.lower()}.",
        )
        pred = EvaluationPrediction(
            prediction_id=f"prediction:{case_id.split(':',1)[1]}:reference-baseline",
            case_ref=case_id,
            system_ref="system:context-evaluation-reference-baseline:v1",
            predicted_outcome=dict(expected),
            confidence=1.0,
            provenance_ref=prov_pred,
        )
        ev = evaluate_prediction(case, gold, pred)
        cases.append(case); golds.append(gold); predictions.append(pred); evaluations.append(ev)

    metric_results: list[MetricResult] = []
    eval_by_case = {x.case_ref: x for x in evaluations}
    for metric in metrics:
        related = [c for c in cases if metric.metric_id in c.metric_refs]
        numerator = sum(eval_by_case[c.case_id].score for c in related)
        denominator = len(related)
        metric_results.append(MetricResult(
            result_id=f"result:{metric.metric_id.split(':',1)[1]}:reference-baseline",
            metric_ref=metric.metric_id,
            case_refs=[c.case_id for c in related],
            numerator=numerator,
            denominator=denominator,
            score=numerator/denominator,
            qualifications=["Reference baseline mirrors reviewed fixture labels and demonstrates the evaluation contract; it is not a model-performance claim."],
        ))

    snapshot_material = {
        "predecessor": predecessor.fingerprint(),
        "cases": [x.fingerprint() for x in cases],
        "gold": [x.fingerprint() for x in golds],
        "metrics": [x.fingerprint() for x in metrics],
    }
    snapshot = BenchmarkSnapshot(
        snapshot_id="snapshot:contextual-semantic-benchmark:v4.9:reference:v1",
        predecessor_fingerprint_sha256=predecessor.fingerprint(),
        case_refs=[x.case_id for x in cases],
        gold_annotation_refs=[x.annotation_id for x in golds],
        metric_refs=[x.metric_id for x in metrics],
        deterministic_benchmark_fingerprint_sha256=canonical_sha256(snapshot_material),
    )
    prov_benchmark = "prov:context-evaluation:benchmark:v1"
    prov_run = "prov:context-evaluation:reference-run:v1"
    provenances = [
        EvaluationProvenanceRecord(
            provenance_id=prov_benchmark,
            subject_refs=[snapshot.snapshot_id] + [x.case_id for x in cases] + [x.annotation_id for x in golds],
            method=InterpretationMethod.manual,
            produced_by_ref="curator:context-evaluation:v1",
            source_refs=[predecessor.fingerprint()],
            reviewer_ref="reviewer:context-evaluation:v1",
            notes=["Benchmark cases are derived from governed v4.1-v4.8 reference objects; gold labels are reviewed evaluation targets, not world-truth assertions."],
        ),
        EvaluationProvenanceRecord(
            provenance_id=prov_pred,
            subject_refs=[x.prediction_id for x in predictions],
            method=InterpretationMethod.manual,
            produced_by_ref="system:context-evaluation-reference-baseline:v1",
            source_refs=[snapshot.snapshot_id],
            notes=["Reference predictions intentionally mirror fixture gold labels to demonstrate deterministic scoring behavior."],
        ),
        EvaluationProvenanceRecord(
            provenance_id=prov_run,
            subject_refs=["run:contextual-semantic-evaluation:reference-baseline:v1"] + [x.evaluation_id for x in evaluations] + [x.result_id for x in metric_results],
            method=InterpretationMethod.manual,
            produced_by_ref="evaluator:contextual-semantic:v1",
            source_refs=[snapshot.snapshot_id],
            reviewer_ref="reviewer:context-evaluation:v1",
            notes=["Run packages benchmark evidence reproducibly; score 1.0 for the fixture baseline does not establish model safety, truthfulness, or domain authority."],
        ),
    ]
    run = ContextualSemanticEvaluationRun(
        run_id="run:contextual-semantic-evaluation:reference-baseline:v1",
        benchmark_snapshot_ref=snapshot.snapshot_id,
        system_ref="system:context-evaluation-reference-baseline:v1",
        prediction_refs=[x.prediction_id for x in predictions],
        case_evaluation_refs=[x.evaluation_id for x in evaluations],
        metric_result_refs=[x.result_id for x in metric_results],
        overall_score=sum(x.score for x in evaluations)/len(evaluations),
        provenance_ref=prov_run,
    )
    return ContextualSemanticEvaluationBenchmarkBundle(
        extends_contracts=list(EXTENDS_CONTRACTS),
        policy=ContextualSemanticEvaluationPolicy(policy_id="contextual-semantic-evaluation-policy:v4.9"),
        multilingual_context=predecessor,
        metric_definitions=metrics,
        benchmark_cases=cases,
        gold_annotations=golds,
        predictions=predictions,
        case_evaluations=evaluations,
        metric_results=metric_results,
        provenance_records=provenances,
        benchmark_snapshots=[snapshot],
        evaluation_runs=[run],
    )


def contract_document() -> dict[str, Any]:
    bundle = reference_contextual_semantic_evaluation_bundle()
    run = bundle.evaluation_runs[0]
    task_counts: dict[str,int] = {}
    for case in bundle.benchmark_cases:
        task_counts[case.task.value] = task_counts.get(case.task.value, 0) + 1
    return {
        "ok": True,
        "release": CORE_RELEASE,
        "contract": CONTRACT_VERSION,
        "predecessor_contract": PREDECESSOR_CONTRACT,
        "extends_contracts": list(EXTENDS_CONTRACTS),
        "identity": {"product":"Sustainable Catalyst Platform Core","build":"Contextual Semantic Evaluation & Benchmark Framework","major_api":"v4"},
        "principles": {
            "semantic_capability_must_be_measurable": True,
            "benchmark_cases_are_governed_objects": True,
            "gold_annotations_are_reviewed_targets_not_world_truth": True,
            "ambiguity_preservation_is_evaluable_behavior": True,
            "original_language_evaluation_is_first_class": True,
            "cross_language_drift_and_divergence_are_first_class": True,
            "evaluation_runs_are_reproducible_and_supersedable": True,
            "predecessor_semantic_objects_remain_immutable": True,
        },
        "boundaries": {
            "benchmark_pass_establishes_claim_truth": False,
            "benchmark_pass_establishes_evidence_validity": False,
            "benchmark_score_is_probability_of_truth": False,
            "benchmark_score_establishes_model_safety": False,
            "benchmark_score_establishes_domain_authority": False,
            "gold_annotation_rewrites_source_meaning": False,
            "evaluation_run_mutates_v480_predecessor": False,
            "context_graph_mutation_performed": False,
            "identity_graph_mutation_performed": False,
            "evidence_graph_mutation_performed": False,
            "knowledge_graph_mutation_performed": False,
        },
        "roadmap_integration": {
            "evaluates_v410_through_v480_contextual_semantics": True,
            "evaluates_v3650_through_v3690_multilingual_linguistics": True,
            "prepares_v4100_unified_contextual_intelligence_runtime": True,
        },
        "reference": {
            "predecessor_release": bundle.multilingual_context.release,
            "predecessor_fingerprint_sha256": bundle.multilingual_context.fingerprint(),
            "benchmark_cases": len(bundle.benchmark_cases),
            "gold_annotations": len(bundle.gold_annotations),
            "metric_definitions": len(bundle.metric_definitions),
            "task_counts": task_counts,
            "predictions": len(bundle.predictions),
            "case_evaluations": len(bundle.case_evaluations),
            "metric_results": len(bundle.metric_results),
            "benchmark_snapshots": len(bundle.benchmark_snapshots),
            "evaluation_runs": len(bundle.evaluation_runs),
            "reference_baseline_overall_score": run.overall_score,
            "failed_reference_cases": sum(1 for x in bundle.case_evaluations if x.status == EvaluationStatus.fail),
            "partial_reference_cases": sum(1 for x in bundle.case_evaluations if x.status == EvaluationStatus.partial),
            "context_graph_mutations_created": 0,
            "bundle_fingerprint_sha256": bundle.fingerprint(),
        },
        "database_migration": "none",
    }
