from __future__ import annotations

from enum import Enum
from functools import lru_cache
from typing import Any, Literal

from pydantic import BaseModel, Field, model_validator

from .computational_runtime_objects import canonical_sha256
from .context_semantic_frame import reference_context_object_semantic_frame_bundle
from .discourse_rhetorical_semantics import reference_discourse_structure_rhetorical_semantics_bundle
from .coreference_referential_identity import reference_coreference_referential_identity_bundle
from .temporal_spatial_language_grounding import reference_temporal_spatial_language_grounding_bundle
from .epistemic_modal_negation_certainty import reference_epistemic_modal_negation_certainty_bundle
from .pragmatic_meaning_speech_act_intent import reference_pragmatic_meaning_speech_act_intent_bundle
from .cross_document_context_graph import reference_cross_document_context_graph_bundle
from .multilingual_context_semantic_alignment import reference_multilingual_context_semantic_alignment_bundle
from .contextual_semantic_evaluation import (
    ContextualSemanticEvaluationBenchmarkBundle,
    reference_contextual_semantic_evaluation_bundle,
)

CORE_RELEASE = "4.10.0"
CONTRACT_VERSION = "sc.core.unified-semantic-contextual-intelligence-runtime.v1"
PREDECESSOR_CONTRACT = "sc.core.contextual-semantic-evaluation-benchmark-framework.v1"


class RuntimeStageKind(str, Enum):
    context_frame = "context-frame"
    discourse = "discourse-rhetorical-semantics"
    reference_identity = "coreference-referential-identity"
    temporal_spatial = "temporal-spatial-language-grounding"
    epistemic = "epistemic-modal-negation-certainty"
    pragmatic = "pragmatic-speech-act-intent"
    context_graph = "cross-document-context-graph"
    multilingual = "multilingual-context-alignment"
    evaluation = "contextual-semantic-evaluation"


class RuntimeExecutionMode(str, Enum):
    reference_replay = "reference-replay"
    delegated = "delegated"
    validation_only = "validation-only"


class RuntimeStageState(str, Enum):
    pending = "pending"
    completed = "completed"
    qualified = "qualified"
    deferred = "deferred"
    blocked = "blocked"
    failed = "failed"


class RuntimeSessionState(str, Enum):
    complete = "complete"
    qualified_complete = "qualified-complete"
    blocked = "blocked"
    failed = "failed"


class RuntimeQualificationCode(str, Enum):
    ambiguity_preserved = "ambiguity-preserved"
    rhetoric_not_truth = "rhetoric-not-truth"
    canonical_identity_deferred = "canonical-identity-deferred"
    geographic_identity_deferred = "geographic-identity-deferred"
    source_uncertainty_preserved = "source-uncertainty-preserved"
    intent_is_interpretive = "intent-is-interpretive"
    continuity_hypothesis_unresolved = "continuity-hypothesis-unresolved"
    cultural_divergence_preserved = "cultural-divergence-preserved"
    benchmark_non_authoritative = "benchmark-non-authoritative"


STAGE_ORDER = [
    RuntimeStageKind.context_frame,
    RuntimeStageKind.discourse,
    RuntimeStageKind.reference_identity,
    RuntimeStageKind.temporal_spatial,
    RuntimeStageKind.epistemic,
    RuntimeStageKind.pragmatic,
    RuntimeStageKind.context_graph,
    RuntimeStageKind.multilingual,
    RuntimeStageKind.evaluation,
]

STAGE_RELEASES = {
    RuntimeStageKind.context_frame: "4.1.0",
    RuntimeStageKind.discourse: "4.2.0",
    RuntimeStageKind.reference_identity: "4.3.0",
    RuntimeStageKind.temporal_spatial: "4.4.0",
    RuntimeStageKind.epistemic: "4.5.0",
    RuntimeStageKind.pragmatic: "4.6.0",
    RuntimeStageKind.context_graph: "4.7.0",
    RuntimeStageKind.multilingual: "4.8.0",
    RuntimeStageKind.evaluation: "4.9.0",
}

STAGE_CONTRACTS = {
    RuntimeStageKind.context_frame: "sc.core.context-object-semantic-frame-foundation.v1",
    RuntimeStageKind.discourse: "sc.core.discourse-structure-rhetorical-semantics.v1",
    RuntimeStageKind.reference_identity: "sc.core.coreference-reference-referential-identity-intelligence.v1",
    RuntimeStageKind.temporal_spatial: "sc.core.temporal-spatial-language-grounding.v1",
    RuntimeStageKind.epistemic: "sc.core.epistemic-modal-negation-certainty-semantics.v1",
    RuntimeStageKind.pragmatic: "sc.core.pragmatic-meaning-speech-act-communicative-intent.v1",
    RuntimeStageKind.context_graph: "sc.core.cross-document-context-graph.v1",
    RuntimeStageKind.multilingual: "sc.core.multilingual-context-semantic-alignment.v1",
    RuntimeStageKind.evaluation: "sc.core.contextual-semantic-evaluation-benchmark-framework.v1",
}


class UnifiedSemanticRuntimePolicy(BaseModel):
    policy_id: str = Field(min_length=3, max_length=500)
    original_language_is_preserved_across_runtime: Literal[True] = True
    translations_remain_derived: Literal[True] = True
    every_stage_requires_governed_contract: Literal[True] = True
    every_stage_output_requires_provenance: Literal[True] = True
    every_stage_preserves_unresolved_alternatives: Literal[True] = True
    qualified_outputs_may_continue_with_explicit_qualification: Literal[True] = True
    validation_failure_blocks_promotion: Literal[True] = True
    runtime_output_is_interpretation_not_truth: Literal[True] = True
    benchmark_result_is_measure_not_truth_probability: Literal[True] = True
    core_orchestrates_but_does_not_silently_execute_domain_models: Literal[True] = True
    predecessor_objects_remain_immutable: Literal[True] = True
    context_graph_mutation_authorized: Literal[False] = False
    identity_graph_mutation_authorized: Literal[False] = False
    evidence_graph_mutation_authorized: Literal[False] = False
    knowledge_graph_mutation_authorized: Literal[False] = False


class SemanticRuntimeStageDefinition(BaseModel):
    stage_id: str = Field(min_length=3, max_length=500)
    ordinal: int = Field(ge=1, le=9)
    kind: RuntimeStageKind
    release: str = Field(pattern=r"^4\.[1-9]\.0$")
    contract: str = Field(min_length=3, max_length=500)
    depends_on_stage_refs: list[str] = Field(default_factory=list)
    reference_fingerprint_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    required: Literal[True] = True
    delegated_computation_permitted: Literal[True] = True
    stage_output_is_not_truth_verdict: Literal[True] = True
    authority_boundary: str = Field(min_length=3, max_length=2000)

    @model_validator(mode="after")
    def validate_identity(self):
        if self.release != STAGE_RELEASES[self.kind]:
            raise ValueError("stage release must match governed runtime stage")
        if self.contract != STAGE_CONTRACTS[self.kind]:
            raise ValueError("stage contract must match governed runtime stage")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class RuntimeQualification(BaseModel):
    qualification_id: str = Field(min_length=3, max_length=500)
    stage_ref: str = Field(min_length=3, max_length=500)
    code: RuntimeQualificationCode
    message: str = Field(min_length=3, max_length=3000)
    unresolved_refs: list[str] = Field(default_factory=list)
    qualification_is_not_failure: Literal[True] = True
    qualification_does_not_establish_truth: Literal[True] = True

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class RuntimeProvenanceRecord(BaseModel):
    provenance_id: str = Field(min_length=3, max_length=500)
    subject_refs: list[str] = Field(min_length=1)
    produced_by_ref: str = Field(min_length=3, max_length=500)
    source_refs: list[str] = Field(min_length=1)
    notes: list[str] = Field(default_factory=list)
    replayable: Literal[True] = True
    provenance_does_not_establish_authority: Literal[True] = True

    @model_validator(mode="after")
    def validate_unique_refs(self):
        if len(self.subject_refs) != len(set(self.subject_refs)):
            raise ValueError("provenance subject_refs must be unique")
        if len(self.source_refs) != len(set(self.source_refs)):
            raise ValueError("provenance source_refs must be unique")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class SemanticRuntimeArtifactEnvelope(BaseModel):
    artifact_id: str = Field(min_length=3, max_length=500)
    stage_ref: str = Field(min_length=3, max_length=500)
    object_ref: str = Field(min_length=3, max_length=500)
    contract_ref: str = Field(min_length=3, max_length=500)
    object_fingerprint_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    state: RuntimeStageState
    qualification_refs: list[str] = Field(default_factory=list)
    unresolved_refs: list[str] = Field(default_factory=list)
    provenance_ref: str = Field(min_length=3, max_length=500)
    immutable_reference: Literal[True] = True
    artifact_is_interpretation_not_truth_verdict: Literal[True] = True

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class SemanticRuntimeStageResult(BaseModel):
    result_id: str = Field(min_length=3, max_length=500)
    stage_ref: str = Field(min_length=3, max_length=500)
    state: RuntimeStageState
    input_artifact_refs: list[str] = Field(default_factory=list)
    external_input_refs: list[str] = Field(default_factory=list)
    output_artifact_refs: list[str] = Field(min_length=1)
    qualification_refs: list[str] = Field(default_factory=list)
    provenance_ref: str = Field(min_length=3, max_length=500)
    validation_passed: Literal[True] = True
    stage_completion_does_not_assert_truth: Literal[True] = True

    @model_validator(mode="after")
    def validate_inputs(self):
        if not self.input_artifact_refs and not self.external_input_refs:
            raise ValueError("stage result requires artifact or external input")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class UnifiedSemanticRuntimePlan(BaseModel):
    plan_id: str = Field(min_length=3, max_length=500)
    execution_mode: RuntimeExecutionMode
    stage_refs: list[str] = Field(min_length=9, max_length=9)
    stop_on_validation_failure: Literal[True] = True
    allow_qualified_continuation: Literal[True] = True
    require_original_language_lineage: Literal[True] = True
    require_provenance_at_every_stage: Literal[True] = True
    require_immutable_stage_artifacts: Literal[True] = True
    final_evaluation_required: Literal[True] = True
    runtime_plan_does_not_select_world_truth: Literal[True] = True

    @model_validator(mode="after")
    def validate_stage_refs(self):
        if len(self.stage_refs) != len(set(self.stage_refs)):
            raise ValueError("runtime plan stage_refs must be unique")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class UnifiedSemanticContextSession(BaseModel):
    session_id: str = Field(min_length=3, max_length=500)
    plan_ref: str = Field(min_length=3, max_length=500)
    stage_result_refs: list[str] = Field(min_length=9, max_length=9)
    final_artifact_ref: str = Field(min_length=3, max_length=500)
    evaluation_run_ref: str = Field(min_length=3, max_length=500)
    qualification_refs: list[str] = Field(default_factory=list)
    provenance_ref: str = Field(min_length=3, max_length=500)
    state: RuntimeSessionState
    unresolved_refs: list[str] = Field(default_factory=list)
    reproducible: Literal[True] = True
    session_completion_does_not_establish_truth_or_authority: Literal[True] = True

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class UnifiedSemanticContextSnapshot(BaseModel):
    snapshot_id: str = Field(min_length=3, max_length=500)
    predecessor_fingerprint_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    plan_fingerprint_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    stage_fingerprints: dict[str, str] = Field(min_length=9, max_length=9)
    session_fingerprint_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    deterministic_runtime_fingerprint_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    immutable: Literal[True] = True
    supersedable: Literal[True] = True
    snapshot_does_not_freeze_semantic_truth: Literal[True] = True

    @model_validator(mode="after")
    def validate_stage_fingerprints(self):
        for value in self.stage_fingerprints.values():
            if len(value) != 64 or any(c not in "0123456789abcdef" for c in value):
                raise ValueError("stage fingerprints must be sha256 hex")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class UnifiedSemanticContextRuntimeBundle(BaseModel):
    release: Literal["4.10.0"] = "4.10.0"
    contract: Literal[CONTRACT_VERSION] = CONTRACT_VERSION
    predecessor_contract: Literal[PREDECESSOR_CONTRACT] = PREDECESSOR_CONTRACT
    policy: UnifiedSemanticRuntimePolicy
    predecessor_evaluation: ContextualSemanticEvaluationBenchmarkBundle
    stage_definitions: list[SemanticRuntimeStageDefinition] = Field(min_length=9, max_length=9)
    plans: list[UnifiedSemanticRuntimePlan] = Field(min_length=1)
    qualifications: list[RuntimeQualification] = Field(min_length=1)
    provenance_records: list[RuntimeProvenanceRecord] = Field(min_length=1)
    artifacts: list[SemanticRuntimeArtifactEnvelope] = Field(min_length=9)
    stage_results: list[SemanticRuntimeStageResult] = Field(min_length=9, max_length=9)
    sessions: list[UnifiedSemanticContextSession] = Field(min_length=1)
    snapshots: list[UnifiedSemanticContextSnapshot] = Field(min_length=1)
    database_migration: Literal["none"] = "none"

    @model_validator(mode="after")
    def validate_bundle(self):
        if self.predecessor_evaluation.release != "4.9.0" or self.predecessor_evaluation.contract != PREDECESSOR_CONTRACT:
            raise ValueError("v4.10 must preserve governed v4.9 predecessor")

        def unique(values: list[str], label: str):
            if len(values) != len(set(values)):
                raise ValueError(f"{label} must be unique")

        unique([x.stage_id for x in self.stage_definitions], "stage ids")
        unique([x.plan_id for x in self.plans], "plan ids")
        unique([x.qualification_id for x in self.qualifications], "qualification ids")
        unique([x.provenance_id for x in self.provenance_records], "provenance ids")
        unique([x.artifact_id for x in self.artifacts], "artifact ids")
        unique([x.result_id for x in self.stage_results], "stage result ids")
        unique([x.session_id for x in self.sessions], "session ids")
        unique([x.snapshot_id for x in self.snapshots], "snapshot ids")

        ordered = sorted(self.stage_definitions, key=lambda x: x.ordinal)
        if [x.kind for x in ordered] != STAGE_ORDER:
            raise ValueError("stage definitions must preserve v4.1-v4.9 semantic order")
        if [x.ordinal for x in ordered] != list(range(1, 10)):
            raise ValueError("stage ordinals must be contiguous 1..9")
        for i, stage in enumerate(ordered):
            expected_dep = [] if i == 0 else [ordered[i-1].stage_id]
            if stage.depends_on_stage_refs != expected_dep:
                raise ValueError("each runtime stage must depend on the immediately preceding stage")

        stages = {x.stage_id: x for x in self.stage_definitions}
        plans = {x.plan_id: x for x in self.plans}
        quals = {x.qualification_id: x for x in self.qualifications}
        provenance = {x.provenance_id: x for x in self.provenance_records}
        artifacts = {x.artifact_id: x for x in self.artifacts}
        results = {x.result_id: x for x in self.stage_results}

        for plan in self.plans:
            if plan.stage_refs != [x.stage_id for x in ordered]:
                raise ValueError("runtime plan must include all stages in governed order")

        for q in self.qualifications:
            if q.stage_ref not in stages:
                raise ValueError("qualification stage_ref must resolve")

        for artifact in self.artifacts:
            if artifact.stage_ref not in stages:
                raise ValueError("artifact stage_ref must resolve")
            stage = stages[artifact.stage_ref]
            if artifact.contract_ref != stage.contract:
                raise ValueError("artifact contract must match stage contract")
            if artifact.object_fingerprint_sha256 != stage.reference_fingerprint_sha256:
                raise ValueError("reference artifact fingerprint must match stage reference fingerprint")
            if artifact.provenance_ref not in provenance:
                raise ValueError("artifact provenance_ref must resolve")
            for ref in artifact.qualification_refs:
                if ref not in quals or quals[ref].stage_ref != artifact.stage_ref:
                    raise ValueError("artifact qualification must resolve to same stage")

        for i, result in enumerate(sorted(self.stage_results, key=lambda x: stages[x.stage_ref].ordinal)):
            if result.stage_ref != ordered[i].stage_id:
                raise ValueError("stage result order must match stage definition order")
            if result.provenance_ref not in provenance:
                raise ValueError("stage result provenance_ref must resolve")
            for ref in result.output_artifact_refs:
                if ref not in artifacts or artifacts[ref].stage_ref != result.stage_ref:
                    raise ValueError("stage result output artifact must resolve to same stage")
            for ref in result.input_artifact_refs:
                if ref not in artifacts:
                    raise ValueError("stage result input artifact must resolve")
            for ref in result.qualification_refs:
                if ref not in quals or quals[ref].stage_ref != result.stage_ref:
                    raise ValueError("stage result qualification must resolve to same stage")
            if i == 0:
                if not result.external_input_refs:
                    raise ValueError("first stage requires external source input")
            else:
                prior_output = self.stage_results[i-1].output_artifact_refs[0]
                if result.input_artifact_refs != [prior_output]:
                    raise ValueError("stage result must consume predecessor output artifact")

        for session in self.sessions:
            if session.plan_ref not in plans:
                raise ValueError("session plan_ref must resolve")
            if session.provenance_ref not in provenance:
                raise ValueError("session provenance_ref must resolve")
            if session.stage_result_refs != [x.result_id for x in self.stage_results]:
                raise ValueError("session must preserve complete stage result order")
            if session.final_artifact_ref not in artifacts:
                raise ValueError("session final_artifact_ref must resolve")
            if artifacts[session.final_artifact_ref].stage_ref != ordered[-1].stage_id:
                raise ValueError("session final artifact must come from evaluation stage")
            valid_eval_runs = {x.run_id for x in self.predecessor_evaluation.evaluation_runs}
            if session.evaluation_run_ref not in valid_eval_runs:
                raise ValueError("session evaluation_run_ref must resolve to v4.9 run")
            for ref in session.qualification_refs:
                if ref not in quals:
                    raise ValueError("session qualification_ref must resolve")

        expected_stage_fps = {x.stage_id: x.reference_fingerprint_sha256 for x in ordered}
        for snapshot in self.snapshots:
            if snapshot.predecessor_fingerprint_sha256 != self.predecessor_evaluation.fingerprint():
                raise ValueError("snapshot predecessor fingerprint must match v4.9 bundle")
            if snapshot.stage_fingerprints != expected_stage_fps:
                raise ValueError("snapshot stage fingerprints must match governed stage definitions")
            if snapshot.plan_fingerprint_sha256 != self.plans[0].fingerprint():
                raise ValueError("snapshot plan fingerprint must match reference plan")
            if snapshot.session_fingerprint_sha256 != self.sessions[0].fingerprint():
                raise ValueError("snapshot session fingerprint must match reference session")

        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


def _reference_stage_material() -> list[tuple[RuntimeStageKind, Any, str]]:
    return [
        (RuntimeStageKind.context_frame, reference_context_object_semantic_frame_bundle(), "Context and semantic frames remain source-bound; unresolved references are preserved."),
        (RuntimeStageKind.discourse, reference_discourse_structure_rhetorical_semantics_bundle(), "Rhetorical relations describe discourse function and do not establish causal or evidentiary truth."),
        (RuntimeStageKind.reference_identity, reference_coreference_referential_identity_bundle(), "Coreference may be reviewed while canonical actor identity remains separately governed."),
        (RuntimeStageKind.temporal_spatial, reference_temporal_spatial_language_grounding_bundle(), "Linguistic time/place grounding does not establish canonical geography or historical fact."),
        (RuntimeStageKind.epistemic, reference_epistemic_modal_negation_certainty_bundle(), "Source stance, negation, modality, and certainty remain distinct from platform truth or probability."),
        (RuntimeStageKind.pragmatic, reference_pragmatic_meaning_speech_act_intent_bundle(), "Speech act and intent remain contextual interpretations, not private mental-state facts or obligations."),
        (RuntimeStageKind.context_graph, reference_cross_document_context_graph_bundle(), "Cross-document continuity remains a hypothesis unless governed identity/equivalence evidence resolves it."),
        (RuntimeStageKind.multilingual, reference_multilingual_context_semantic_alignment_bundle(), "Original-language meaning remains authoritative and cultural divergence remains first-class."),
        (RuntimeStageKind.evaluation, reference_contextual_semantic_evaluation_bundle(), "Benchmark results measure governed targets and do not establish truth, safety, authority, or evidence validity."),
    ]


@lru_cache(maxsize=1)
def reference_unified_semantic_context_runtime_bundle() -> UnifiedSemanticContextRuntimeBundle:
    predecessor = reference_contextual_semantic_evaluation_bundle()
    material = _reference_stage_material()

    stage_defs: list[SemanticRuntimeStageDefinition] = []
    for idx, (kind, bundle, boundary) in enumerate(material, start=1):
        stage_id = f"runtime-stage:{idx:02d}:{kind.value}"
        deps = [] if idx == 1 else [f"runtime-stage:{idx-1:02d}:{STAGE_ORDER[idx-2].value}"]
        stage_defs.append(SemanticRuntimeStageDefinition(
            stage_id=stage_id,
            ordinal=idx,
            kind=kind,
            release=STAGE_RELEASES[kind],
            contract=STAGE_CONTRACTS[kind],
            depends_on_stage_refs=deps,
            reference_fingerprint_sha256=bundle.fingerprint(),
            authority_boundary=boundary,
        ))

    qual_specs = [
        (RuntimeQualificationCode.ambiguity_preserved, ["mention:it-unresolved"], "v4.1 unresolved reference state is retained rather than fabricated away."),
        (RuntimeQualificationCode.rhetoric_not_truth, ["rhetorical-relation:concession-viability"], "Discourse function is preserved without causal or evidentiary promotion."),
        (RuntimeQualificationCode.canonical_identity_deferred, ["surface-actor:commission", "surface-actor:ministry"], "Referential resolution does not silently create canonical actor identities."),
        (RuntimeQualificationCode.geographic_identity_deferred, ["spatial-anchor:brussels-source-place"], "Source-place grounding is retained without inventing gazetteer identity or coordinates."),
        (RuntimeQualificationCode.source_uncertainty_preserved, ["assessment:ministry-explicit-uncertainty"], "Explicit source uncertainty remains visible in downstream context."),
        (RuntimeQualificationCode.intent_is_interpretive, ["intent:alert-disruption"], "Communicative intent remains a reviewed contextual interpretation."),
        (RuntimeQualificationCode.continuity_hypothesis_unresolved, ["thread:actor-continuity:candidate", "thread:policy-topic-continuity:candidate"], "Cross-document actor/topic continuity remains hypothesis-level."),
        (RuntimeQualificationCode.cultural_divergence_preserved, ["universal-equivalence:治理-governance-gobernanza"], "Cultural semantic divergence remains explicit rather than flattened."),
        (RuntimeQualificationCode.benchmark_non_authoritative, ["evaluation-run:reference-baseline:v1"], "Reference benchmark score validates mechanics and is not a truth, safety, or authority claim."),
    ]
    qualifications = [RuntimeQualification(
        qualification_id=f"qualification:{idx:02d}:{code.value}",
        stage_ref=stage_defs[idx-1].stage_id,
        code=code,
        message=message,
        unresolved_refs=refs,
    ) for idx, (code, refs, message) in enumerate(qual_specs, start=1)]

    provenance_records: list[RuntimeProvenanceRecord] = []
    artifacts: list[SemanticRuntimeArtifactEnvelope] = []
    results: list[SemanticRuntimeStageResult] = []
    for idx, ((kind, bundle, _), stage, qual) in enumerate(zip(material, stage_defs, qualifications), start=1):
        prov_id = f"runtime-provenance:stage:{idx:02d}:reference-replay"
        artifact_id = f"runtime-artifact:stage:{idx:02d}:reference"
        result_id = f"runtime-result:stage:{idx:02d}:reference"
        provenance_records.append(RuntimeProvenanceRecord(
            provenance_id=prov_id,
            subject_refs=[artifact_id, result_id],
            produced_by_ref="runtime-provider:governed-reference-replay:v4.10",
            source_refs=[stage.contract, stage.reference_fingerprint_sha256],
            notes=["Reference replay packages a pre-existing governed predecessor artifact; it does not rerun or reinterpret the specialist semantic model."],
        ))
        artifacts.append(SemanticRuntimeArtifactEnvelope(
            artifact_id=artifact_id,
            stage_ref=stage.stage_id,
            object_ref=f"reference-bundle:{kind.value}:v{stage.release}",
            contract_ref=stage.contract,
            object_fingerprint_sha256=bundle.fingerprint(),
            state=RuntimeStageState.qualified,
            qualification_refs=[qual.qualification_id],
            unresolved_refs=list(qual.unresolved_refs),
            provenance_ref=prov_id,
        ))
        results.append(SemanticRuntimeStageResult(
            result_id=result_id,
            stage_ref=stage.stage_id,
            state=RuntimeStageState.qualified,
            input_artifact_refs=[] if idx == 1 else [f"runtime-artifact:stage:{idx-1:02d}:reference"],
            external_input_refs=["source:governed-reference-corpus:v4.10"] if idx == 1 else [],
            output_artifact_refs=[artifact_id],
            qualification_refs=[qual.qualification_id],
            provenance_ref=prov_id,
        ))

    plan = UnifiedSemanticRuntimePlan(
        plan_id="runtime-plan:unified-semantic-context:reference:v1",
        execution_mode=RuntimeExecutionMode.reference_replay,
        stage_refs=[x.stage_id for x in stage_defs],
    )
    session_prov = RuntimeProvenanceRecord(
        provenance_id="runtime-provenance:session:reference:v1",
        subject_refs=["runtime-session:unified-semantic-context:reference:v1"],
        produced_by_ref="runtime-provider:governed-reference-replay:v4.10",
        source_refs=[x.artifact_id for x in artifacts],
        notes=["Session composes immutable governed predecessor artifacts and their qualifications in stage order."],
    )
    provenance_records.append(session_prov)
    session = UnifiedSemanticContextSession(
        session_id="runtime-session:unified-semantic-context:reference:v1",
        plan_ref=plan.plan_id,
        stage_result_refs=[x.result_id for x in results],
        final_artifact_ref=artifacts[-1].artifact_id,
        evaluation_run_ref=predecessor.evaluation_runs[0].run_id,
        qualification_refs=[x.qualification_id for x in qualifications],
        provenance_ref=session_prov.provenance_id,
        state=RuntimeSessionState.qualified_complete,
        unresolved_refs=[ref for q in qualifications for ref in q.unresolved_refs],
    )
    stage_fps = {x.stage_id: x.reference_fingerprint_sha256 for x in stage_defs}
    snapshot_material = {
        "predecessor": predecessor.fingerprint(),
        "plan": plan.fingerprint(),
        "stages": stage_fps,
        "session": session.fingerprint(),
        "artifacts": [x.fingerprint() for x in artifacts],
        "results": [x.fingerprint() for x in results],
        "qualifications": [x.fingerprint() for x in qualifications],
    }
    snapshot = UnifiedSemanticContextSnapshot(
        snapshot_id="runtime-snapshot:unified-semantic-context:reference:v1",
        predecessor_fingerprint_sha256=predecessor.fingerprint(),
        plan_fingerprint_sha256=plan.fingerprint(),
        stage_fingerprints=stage_fps,
        session_fingerprint_sha256=session.fingerprint(),
        deterministic_runtime_fingerprint_sha256=canonical_sha256(snapshot_material),
    )
    return UnifiedSemanticContextRuntimeBundle(
        policy=UnifiedSemanticRuntimePolicy(policy_id="unified-semantic-context-runtime-policy:v4.10"),
        predecessor_evaluation=predecessor,
        stage_definitions=stage_defs,
        plans=[plan],
        qualifications=qualifications,
        provenance_records=provenance_records,
        artifacts=artifacts,
        stage_results=results,
        sessions=[session],
        snapshots=[snapshot],
    )


def contract_document() -> dict[str, Any]:
    bundle = reference_unified_semantic_context_runtime_bundle()
    qualified = [x for x in bundle.stage_results if x.state == RuntimeStageState.qualified]
    return {
        "ok": True,
        "release": CORE_RELEASE,
        "contract": CONTRACT_VERSION,
        "predecessor_contract": PREDECESSOR_CONTRACT,
        "identity": {"product": "Sustainable Catalyst Platform Core", "build": "Unified Semantic & Contextual Intelligence Runtime", "major_api": "v4"},
        "principles": {
            "v410_through_v490_are_orchestrated_in_governed_order": True,
            "stage_contract_identity_is_preserved": True,
            "stage_provenance_is_required": True,
            "unresolved_ambiguity_is_preserved": True,
            "original_language_lineage_is_required": True,
            "qualified_outputs_may_continue_with_explicit_qualification": True,
            "validation_failure_blocks_promotion": True,
            "reference_replay_is_reproducible": True,
            "specialist_models_remain_separate_from_core_contract_authority": True,
        },
        "boundaries": {
            "runtime_completion_establishes_claim_truth": False,
            "runtime_completion_establishes_evidence_validity": False,
            "runtime_completion_establishes_canonical_identity": False,
            "runtime_completion_establishes_source_authority": False,
            "benchmark_score_is_probability_of_truth": False,
            "runtime_silently_discards_ambiguity": False,
            "runtime_silently_rewrites_predecessor_objects": False,
            "core_silently_executes_domain_models": False,
            "context_graph_mutation_performed": False,
            "identity_graph_mutation_performed": False,
            "evidence_graph_mutation_performed": False,
            "knowledge_graph_mutation_performed": False,
        },
        "runtime_pipeline": [
            {"ordinal": x.ordinal, "stage_id": x.stage_id, "kind": x.kind.value, "release": x.release, "contract": x.contract}
            for x in sorted(bundle.stage_definitions, key=lambda x: x.ordinal)
        ],
        "reference": {
            "predecessor_release": bundle.predecessor_evaluation.release,
            "predecessor_fingerprint_sha256": bundle.predecessor_evaluation.fingerprint(),
            "stages": len(bundle.stage_definitions),
            "stage_results": len(bundle.stage_results),
            "qualified_stage_results": len(qualified),
            "artifacts": len(bundle.artifacts),
            "qualifications": len(bundle.qualifications),
            "plans": len(bundle.plans),
            "sessions": len(bundle.sessions),
            "snapshots": len(bundle.snapshots),
            "session_state": bundle.sessions[0].state.value,
            "evaluation_run_ref": bundle.sessions[0].evaluation_run_ref,
            "context_graph_mutations_created": 0,
            "identity_graph_mutations_created": 0,
            "evidence_graph_mutations_created": 0,
            "knowledge_graph_mutations_created": 0,
            "bundle_fingerprint_sha256": bundle.fingerprint(),
        },
        "database_migration": "none",
    }
