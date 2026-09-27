from __future__ import annotations

from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field, model_validator

from .computational_runtime_objects import canonical_sha256
from .machine_learning_models import MLModelBundle, reference_ml_model_bundle
from .ml_training_lineage import MLTrainingLineageBundle, reference_training_lineage_bundle
from .ml_evaluation_uncertainty import (
    MLEvaluationCalibrationUncertaintyBundle,
    reference_evaluation_calibration_uncertainty_bundle,
)
from .ml_explainability_interpretation import (
    MLExplainabilityInterpretationBundle,
    reference_explainability_interpretation_bundle,
)
from .ml_embedding_representation import (
    MLRepresentationIntelligenceBundle,
    reference_representation_intelligence_bundle,
)
from .ml_inference_prediction_provenance import (
    MLInferencePredictionProvenanceBundle,
    reference_inference_prediction_provenance_bundle,
)

CORE_RELEASE = "3.64.0"
CONTRACT_VERSION = "sc.core.neural-model-registry-reproducible-packages.v1"


class MLRegistryLifecycle(str, Enum):
    draft = "draft"
    registered = "registered"
    deprecated = "deprecated"
    archived = "archived"


class MLArtifactKind(str, Enum):
    architecture = "architecture"
    weights = "weights"
    checkpoint = "checkpoint"
    preprocessor = "preprocessor"
    tokenizer = "tokenizer"
    vocabulary = "vocabulary"
    runtime_manifest = "runtime-manifest"
    environment_lock = "environment-lock"
    model_card = "model-card"
    other = "other"


class MLArtifactFormat(str, Enum):
    safetensors = "safetensors"
    onnx = "onnx"
    torchscript = "torchscript"
    state_dict = "state-dict"
    json = "json"
    yaml = "yaml"
    text = "text"
    binary = "binary"
    other = "other"


class MLDeviceClass(str, Enum):
    cpu = "cpu"
    gpu = "gpu"
    accelerator = "accelerator"
    any = "any"


class MLLimitationCategory(str, Enum):
    data = "data"
    generalization = "generalization"
    calibration = "calibration"
    uncertainty = "uncertainty"
    interpretability = "interpretability"
    fairness = "fairness"
    runtime = "runtime"
    security = "security"
    other = "other"


class MLModelArtifactRecord(BaseModel):
    artifact_id: str = Field(min_length=2, max_length=500)
    artifact_kind: MLArtifactKind
    artifact_format: MLArtifactFormat
    artifact_ref: str = Field(min_length=2, max_length=1000)
    artifact_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    size_bytes: int | None = Field(default=None, ge=0)
    model_spec_ref: str = Field(min_length=2, max_length=500)
    checkpoint_ref: str | None = Field(default=None, max_length=500)
    media_type: str | None = Field(default=None, max_length=200)
    license_ref: str | None = Field(default=None, max_length=1000)
    immutable: Literal[True] = True
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_artifact(self):
        if self.artifact_kind in {MLArtifactKind.weights, MLArtifactKind.checkpoint} and not self.checkpoint_ref:
            raise ValueError("weights/checkpoint artifacts require checkpoint_ref")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class MLRuntimeRequirementRecord(BaseModel):
    runtime_requirement_id: str = Field(min_length=2, max_length=500)
    runtime_binding_ref: str = Field(min_length=2, max_length=500)
    environment_ref: str = Field(min_length=2, max_length=500)
    framework: str = Field(min_length=1, max_length=200)
    framework_version: str | None = Field(default=None, max_length=120)
    python_version: str | None = Field(default=None, max_length=120)
    device_class: MLDeviceClass = MLDeviceClass.any
    capabilities: list[str] = Field(default_factory=list)
    environment_lock_artifact_ref: str | None = Field(default=None, max_length=1000)
    environment_lock_sha256: str | None = Field(default=None, pattern=r"^[0-9a-f]{64}$")
    package_install_performed_by_core: Literal[False] = False
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_requirement(self):
        if len(self.capabilities) != len(set(self.capabilities)):
            raise ValueError("runtime capabilities must be unique")
        if bool(self.environment_lock_artifact_ref) != bool(self.environment_lock_sha256):
            raise ValueError("environment lock ref/hash must be supplied together")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class MLIntendedUseStatement(BaseModel):
    intended_use_id: str = Field(min_length=2, max_length=500)
    registry_entry_ref: str = Field(min_length=2, max_length=500)
    summary: str = Field(min_length=5, max_length=5000)
    supported_tasks: list[str] = Field(min_length=1)
    supported_contexts: list[str] = Field(default_factory=list)
    out_of_scope_uses: list[str] = Field(default_factory=list)
    autonomous_decision_allowed: Literal[False] = False
    evidence_substitution_allowed: Literal[False] = False
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_use(self):
        for values in (self.supported_tasks, self.supported_contexts, self.out_of_scope_uses):
            if len(values) != len(set(values)):
                raise ValueError("intended-use lists must not contain duplicates")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class MLModelLimitationRecord(BaseModel):
    limitation_id: str = Field(min_length=2, max_length=500)
    registry_entry_ref: str = Field(min_length=2, max_length=500)
    category: MLLimitationCategory
    statement: str = Field(min_length=5, max_length=5000)
    affected_scope: list[str] = Field(default_factory=list)
    mitigation_ref: str | None = Field(default=None, max_length=1000)
    metadata: dict[str, Any] = Field(default_factory=dict)

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class MLModelRegistryEntry(BaseModel):
    registry_entry_id: str = Field(min_length=2, max_length=500)
    model_spec_ref: str = Field(min_length=2, max_length=500)
    model_version_ref: str = Field(min_length=2, max_length=500)
    training_run_ref: str = Field(min_length=2, max_length=500)
    checkpoint_ref: str = Field(min_length=2, max_length=500)
    inference_plan_ref: str = Field(min_length=2, max_length=500)
    artifact_refs: list[str] = Field(min_length=1)
    evaluation_refs: list[str] = Field(min_length=1)
    representation_model_refs: list[str] = Field(default_factory=list)
    aliases: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    lifecycle: MLRegistryLifecycle = MLRegistryLifecycle.registered
    intended_use_ref: str | None = Field(default=None, max_length=500)
    limitation_refs: list[str] = Field(default_factory=list)
    registered_at: str | None = Field(default=None, max_length=80)
    registration_implies_certification: Literal[False] = False
    approved_for_autonomous_action: Literal[False] = False
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_registry_entry(self):
        for values in (self.artifact_refs, self.evaluation_refs, self.representation_model_refs, self.aliases, self.tags, self.limitation_refs):
            if len(values) != len(set(values)):
                raise ValueError("registry entry lists must not contain duplicates")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class MLReproducibilityManifest(BaseModel):
    manifest_id: str = Field(min_length=2, max_length=500)
    registry_entry_ref: str = Field(min_length=2, max_length=500)
    model_spec_ref: str = Field(min_length=2, max_length=500)
    model_version_ref: str = Field(min_length=2, max_length=500)
    training_plan_ref: str = Field(min_length=2, max_length=500)
    training_run_ref: str = Field(min_length=2, max_length=500)
    checkpoint_ref: str = Field(min_length=2, max_length=500)
    runtime_requirement_ref: str = Field(min_length=2, max_length=500)
    input_schema_ref: str = Field(min_length=2, max_length=500)
    output_refs: list[str] = Field(min_length=1)
    artifact_refs: list[str] = Field(min_length=1)
    evaluation_refs: list[str] = Field(min_length=1)
    intended_use_ref: str = Field(min_length=2, max_length=500)
    limitation_refs: list[str] = Field(min_length=1)
    model_foundation_fingerprint_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    training_lineage_fingerprint_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    evaluation_fingerprint_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    explainability_fingerprint_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    representation_fingerprint_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    inference_fingerprint_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    reproducibility_guaranteed: Literal[False] = False
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_manifest(self):
        for values in (self.output_refs, self.artifact_refs, self.evaluation_refs, self.limitation_refs):
            if len(values) != len(set(values)):
                raise ValueError("reproducibility manifest lists must not contain duplicates")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class MLReproducibleModelPackage(BaseModel):
    package_id: str = Field(min_length=2, max_length=500)
    registry_entry_ref: str = Field(min_length=2, max_length=500)
    manifest_ref: str = Field(min_length=2, max_length=500)
    artifact_refs: list[str] = Field(min_length=1)
    runtime_requirement_ref: str = Field(min_length=2, max_length=500)
    input_schema_ref: str = Field(min_length=2, max_length=500)
    output_refs: list[str] = Field(min_length=1)
    evaluation_refs: list[str] = Field(min_length=1)
    calibration_refs: list[str] = Field(default_factory=list)
    uncertainty_refs: list[str] = Field(default_factory=list)
    explainability_refs: list[str] = Field(default_factory=list)
    representation_refs: list[str] = Field(default_factory=list)
    inference_plan_ref: str = Field(min_length=2, max_length=500)
    intended_use_ref: str = Field(min_length=2, max_length=500)
    limitation_refs: list[str] = Field(min_length=1)
    portable_research_object: Literal[True] = True
    core_executes_package: Literal[False] = False
    core_downloads_dependencies: Literal[False] = False
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_package(self):
        groups = (
            self.artifact_refs, self.output_refs, self.evaluation_refs, self.calibration_refs,
            self.uncertainty_refs, self.explainability_refs, self.representation_refs, self.limitation_refs,
        )
        for values in groups:
            if len(values) != len(set(values)):
                raise ValueError("model package lists must not contain duplicates")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class MLModelRegistryPackageBundle(BaseModel):
    ml_model_bundle: MLModelBundle
    training_lineage_bundle: MLTrainingLineageBundle
    evaluation_bundle: MLEvaluationCalibrationUncertaintyBundle
    explainability_bundle: MLExplainabilityInterpretationBundle
    representation_bundle: MLRepresentationIntelligenceBundle
    inference_bundle: MLInferencePredictionProvenanceBundle
    artifacts: list[MLModelArtifactRecord] = Field(min_length=1)
    runtime_requirements: list[MLRuntimeRequirementRecord] = Field(min_length=1)
    intended_use_statements: list[MLIntendedUseStatement] = Field(min_length=1)
    limitations: list[MLModelLimitationRecord] = Field(min_length=1)
    registry_entries: list[MLModelRegistryEntry] = Field(min_length=1)
    reproducibility_manifests: list[MLReproducibilityManifest] = Field(min_length=1)
    model_packages: list[MLReproducibleModelPackage] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_bundle(self):
        ml = self.ml_model_bundle
        train = self.training_lineage_bundle
        evaluation = self.evaluation_bundle
        explain = self.explainability_bundle
        rep = self.representation_bundle
        infer = self.inference_bundle

        # Cross-release identity and fingerprint continuity.
        if train.model_spec.model_spec_id != ml.model_spec.model_spec_id:
            raise ValueError("training lineage model spec must match ML model foundation")
        if evaluation.model_spec_ref != ml.model_spec.model_spec_id:
            raise ValueError("evaluation bundle model spec must match ML model foundation")
        if explain.model_spec_ref != ml.model_spec.model_spec_id:
            raise ValueError("explainability model spec must match ML model foundation")
        if rep.model_spec_ref != ml.model_spec.model_spec_id:
            raise ValueError("representation model spec must match ML model foundation")
        if infer.ml_model_bundle.fingerprint() != ml.fingerprint():
            raise ValueError("inference bundle ML foundation must match bundled ML model foundation")
        if infer.representation_bundle.fingerprint() != rep.fingerprint():
            raise ValueError("inference representation bundle must match bundled v3.62 representation bundle")

        def keyed(values, attr, label):
            ids = [getattr(x, attr) for x in values]
            if len(ids) != len(set(ids)):
                raise ValueError(f"{label} ids must be unique")
            return {getattr(x, attr): x for x in values}

        artifacts = keyed(self.artifacts, "artifact_id", "artifact")
        runtime_requirements = keyed(self.runtime_requirements, "runtime_requirement_id", "runtime requirement")
        uses = keyed(self.intended_use_statements, "intended_use_id", "intended-use")
        limitations = keyed(self.limitations, "limitation_id", "limitation")
        entries = keyed(self.registry_entries, "registry_entry_id", "registry entry")
        manifests = keyed(self.reproducibility_manifests, "manifest_id", "reproducibility manifest")
        packages = keyed(self.model_packages, "package_id", "model package")

        runtime_binding_ids = {x.runtime_binding_id for x in ml.model_spec.runtime_bindings}
        training_runs = {x.training_run_id: x for x in train.training_runs}
        checkpoints = {c.checkpoint_id: c for r in train.training_runs for c in r.checkpoints}
        evaluations = {e.evaluation_id: e for r in train.training_runs for e in r.evaluations}
        representation_models = {x.representation_model_id for x in rep.representation_models}
        calibration_ids = {x.calibration_id for x in evaluation.calibration_records}
        uncertainty_ids = {x.uncertainty_estimate_id for x in evaluation.uncertainty_estimates}
        explain_ids = (
            {x.feature_attribution_id for x in explain.feature_attributions}
            | {x.saliency_map_id for x in explain.saliency_maps}
            | {x.attention_explanation_id for x in explain.attention_explanations}
            | {x.counterfactual_id for x in explain.counterfactual_explanations}
            | {x.embedding_explanation_id for x in explain.embedding_explanations}
            | {x.comparison_interpretation_id for x in explain.model_comparisons}
        )
        representation_refs = (
            representation_models
            | {x.embedding_space_id for x in rep.embedding_spaces}
            | {x.similarity_result_id for x in rep.similarity_results}
            | {x.projection_id for x in rep.vector_projections}
            | {x.cluster_id for x in rep.clusters}
        )

        if ml.inference_plan is None:
            raise ValueError("v3.57 ML model bundle requires inference plan")

        for requirement in self.runtime_requirements:
            if requirement.runtime_binding_ref not in runtime_binding_ids:
                raise ValueError("runtime requirement runtime_binding_ref must resolve to v3.57 model runtime binding")
            binding = next(x for x in ml.model_spec.runtime_bindings if x.runtime_binding_id == requirement.runtime_binding_ref)
            if requirement.environment_ref != binding.environment_ref:
                raise ValueError("runtime requirement environment_ref must match governed runtime binding")

        for artifact in self.artifacts:
            if artifact.model_spec_ref != ml.model_spec.model_spec_id:
                raise ValueError("model artifact model_spec_ref must match bundled ML model specification")
            if artifact.checkpoint_ref is not None:
                checkpoint = checkpoints.get(artifact.checkpoint_ref)
                if checkpoint is None:
                    raise ValueError("model artifact checkpoint_ref must resolve to v3.58 training lineage")
                if artifact.artifact_kind in {MLArtifactKind.weights, MLArtifactKind.checkpoint}:
                    if artifact.artifact_sha256 != checkpoint.artifact_sha256:
                        raise ValueError("weights/checkpoint artifact hash must match governed checkpoint hash")

        for use in self.intended_use_statements:
            if use.registry_entry_ref not in entries:
                raise ValueError("intended-use registry_entry_ref must resolve within bundle")

        for limitation in self.limitations:
            if limitation.registry_entry_ref not in entries:
                raise ValueError("limitation registry_entry_ref must resolve within bundle")

        for entry in self.registry_entries:
            if entry.model_spec_ref != ml.model_spec.model_spec_id:
                raise ValueError("registry model_spec_ref must match v3.57 model specification")
            if entry.inference_plan_ref != ml.inference_plan.inference_plan_id:
                raise ValueError("registry inference_plan_ref must match v3.57 inference plan")
            run = training_runs.get(entry.training_run_ref)
            if run is None:
                raise ValueError("registry training_run_ref must resolve to v3.58 training lineage")
            checkpoint = checkpoints.get(entry.checkpoint_ref)
            if checkpoint is None or checkpoint.training_run_ref != entry.training_run_ref:
                raise ValueError("registry checkpoint_ref must resolve within referenced training run")
            expected_model_version = checkpoint.model_version_ref or run.output_model_version_ref
            if expected_model_version and entry.model_version_ref != expected_model_version:
                raise ValueError("registry model_version_ref must match checkpoint/training output model version")
            if set(entry.artifact_refs) - set(artifacts):
                raise ValueError("registry artifact refs must resolve within bundle")
            if set(entry.evaluation_refs) - set(evaluations):
                raise ValueError("registry evaluation refs must resolve to v3.58 evaluation lineage")
            if set(entry.representation_model_refs) - representation_models:
                raise ValueError("registry representation_model_refs must resolve to v3.62 representation models")
            if entry.intended_use_ref and entry.intended_use_ref not in uses:
                raise ValueError("registry intended_use_ref must resolve within bundle")
            if set(entry.limitation_refs) - set(limitations):
                raise ValueError("registry limitation_refs must resolve within bundle")

        for manifest in self.reproducibility_manifests:
            entry = entries.get(manifest.registry_entry_ref)
            if entry is None:
                raise ValueError("manifest registry_entry_ref must resolve within bundle")
            if manifest.model_spec_ref != entry.model_spec_ref or manifest.model_version_ref != entry.model_version_ref:
                raise ValueError("manifest model identity must match registry entry")
            if manifest.training_run_ref != entry.training_run_ref or manifest.checkpoint_ref != entry.checkpoint_ref:
                raise ValueError("manifest training/checkpoint lineage must match registry entry")
            if manifest.training_plan_ref != ml.training_plan.training_plan_id:
                raise ValueError("manifest training_plan_ref must match v3.57 training plan")
            if manifest.runtime_requirement_ref not in runtime_requirements:
                raise ValueError("manifest runtime_requirement_ref must resolve within bundle")
            if manifest.input_schema_ref != ml.inference_plan.input_schema_ref:
                raise ValueError("manifest input_schema_ref must match v3.57 inference plan")
            if set(manifest.artifact_refs) - set(entry.artifact_refs):
                raise ValueError("manifest artifacts must be a subset of registry artifacts")
            if set(manifest.evaluation_refs) - set(entry.evaluation_refs):
                raise ValueError("manifest evaluation refs must be a subset of registry evaluations")
            if manifest.intended_use_ref != entry.intended_use_ref:
                raise ValueError("manifest intended use must match registry entry")
            if set(manifest.limitation_refs) - set(entry.limitation_refs):
                raise ValueError("manifest limitations must be registered limitations")
            expected = {
                "model_foundation_fingerprint_sha256": ml.fingerprint(),
                "training_lineage_fingerprint_sha256": train.fingerprint(),
                "evaluation_fingerprint_sha256": evaluation.fingerprint(),
                "explainability_fingerprint_sha256": explain.fingerprint(),
                "representation_fingerprint_sha256": rep.fingerprint(),
                "inference_fingerprint_sha256": infer.fingerprint(),
            }
            for field, value in expected.items():
                if getattr(manifest, field) != value:
                    raise ValueError(f"manifest {field} must match bundled predecessor object")

        for package in self.model_packages:
            entry = entries.get(package.registry_entry_ref)
            manifest = manifests.get(package.manifest_ref)
            if entry is None or manifest is None:
                raise ValueError("model package registry/manifest refs must resolve within bundle")
            if manifest.registry_entry_ref != entry.registry_entry_id:
                raise ValueError("model package manifest must belong to package registry entry")
            if package.runtime_requirement_ref != manifest.runtime_requirement_ref:
                raise ValueError("model package runtime requirement must match manifest")
            if package.input_schema_ref != manifest.input_schema_ref:
                raise ValueError("model package input schema must match manifest")
            if package.inference_plan_ref != entry.inference_plan_ref:
                raise ValueError("model package inference plan must match registry entry")
            if package.intended_use_ref != manifest.intended_use_ref:
                raise ValueError("model package intended use must match manifest")
            if set(package.artifact_refs) != set(manifest.artifact_refs):
                raise ValueError("model package artifact set must match manifest")
            if set(package.evaluation_refs) - set(evaluations):
                raise ValueError("model package evaluation refs must resolve to v3.58 lineage")
            if set(package.calibration_refs) - calibration_ids:
                raise ValueError("model package calibration refs must resolve to v3.60 objects")
            if set(package.uncertainty_refs) - uncertainty_ids:
                raise ValueError("model package uncertainty refs must resolve to v3.60 objects")
            if set(package.explainability_refs) - explain_ids:
                raise ValueError("model package explainability refs must resolve to v3.61 objects")
            if set(package.representation_refs) - representation_refs:
                raise ValueError("model package representation refs must resolve to v3.62 objects")
            if set(package.limitation_refs) != set(manifest.limitation_refs):
                raise ValueError("model package limitation set must match manifest")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


def reference_model_registry_package_bundle() -> MLModelRegistryPackageBundle:
    ml = reference_ml_model_bundle()
    train = reference_training_lineage_bundle()
    evaluation = reference_evaluation_calibration_uncertainty_bundle()
    explain = reference_explainability_interpretation_bundle()
    rep = reference_representation_intelligence_bundle()
    infer = reference_inference_prediction_provenance_bundle()

    run = train.training_runs[0]
    checkpoint = next(x for x in run.checkpoints if x.checkpoint_id == "ml-checkpoint:reference-energy:final")
    evaluation_ids = [x.evaluation_id for x in run.evaluations]
    registry_id = "ml-registry-entry:reference-energy-neural-regressor:1.0.1"

    artifacts = [
        MLModelArtifactRecord(
            artifact_id="ml-artifact:reference-energy:architecture:v1",
            artifact_kind=MLArtifactKind.architecture,
            artifact_format=MLArtifactFormat.json,
            artifact_ref="artifact:reference-energy:architecture:v1",
            artifact_sha256="a" * 64,
            size_bytes=4096,
            model_spec_ref=ml.model_spec.model_spec_id,
            media_type="application/json",
        ),
        MLModelArtifactRecord(
            artifact_id="ml-artifact:reference-energy:checkpoint-final",
            artifact_kind=MLArtifactKind.checkpoint,
            artifact_format=MLArtifactFormat.safetensors,
            artifact_ref=checkpoint.artifact_ref,
            artifact_sha256=checkpoint.artifact_sha256,
            size_bytes=8192,
            model_spec_ref=ml.model_spec.model_spec_id,
            checkpoint_ref=checkpoint.checkpoint_id,
            media_type="application/octet-stream",
        ),
        MLModelArtifactRecord(
            artifact_id="ml-artifact:reference-energy:environment-lock",
            artifact_kind=MLArtifactKind.environment_lock,
            artifact_format=MLArtifactFormat.text,
            artifact_ref="artifact:reference-energy:environment-lock",
            artifact_sha256="b" * 64,
            size_bytes=2048,
            model_spec_ref=ml.model_spec.model_spec_id,
            media_type="text/plain",
        ),
        MLModelArtifactRecord(
            artifact_id="ml-artifact:reference-energy:model-card",
            artifact_kind=MLArtifactKind.model_card,
            artifact_format=MLArtifactFormat.text,
            artifact_ref="artifact:reference-energy:model-card",
            artifact_sha256="c" * 64,
            size_bytes=3072,
            model_spec_ref=ml.model_spec.model_spec_id,
            media_type="text/markdown",
        ),
    ]

    runtime = MLRuntimeRequirementRecord(
        runtime_requirement_id="ml-runtime-requirement:reference-energy:v1",
        runtime_binding_ref=ml.model_spec.runtime_bindings[0].runtime_binding_id,
        environment_ref=ml.model_spec.runtime_bindings[0].environment_ref or "environment:reference-ml-python",
        framework=ml.model_spec.runtime_bindings[0].framework or "external-ml-framework",
        framework_version="reference-locked",
        python_version="3.12",
        device_class=MLDeviceClass.cpu,
        capabilities=["infer", "evaluate", "export"],
        environment_lock_artifact_ref="artifact:reference-energy:environment-lock",
        environment_lock_sha256="b" * 64,
    )

    use = MLIntendedUseStatement(
        intended_use_id="ml-intended-use:reference-energy:v1",
        registry_entry_ref=registry_id,
        summary="Research-oriented energy-regression reproduction and governed inference demonstrations.",
        supported_tasks=["regression", "research-reproduction"],
        supported_contexts=["Sustainable Catalyst Workspace", "Sustainable Catalyst Research Lab"],
        out_of_scope_uses=["autonomous high-stakes decisions", "substitution for empirical evidence"],
    )
    limitation_records = [
        MLModelLimitationRecord(
            limitation_id="ml-limitation:reference-energy:generalization",
            registry_entry_ref=registry_id,
            category=MLLimitationCategory.generalization,
            statement="Performance outside the governed reference dataset and operating conditions is not established.",
            affected_scope=["external-data", "distribution-shift"],
        ),
        MLModelLimitationRecord(
            limitation_id="ml-limitation:reference-energy:uncertainty",
            registry_entry_ref=registry_id,
            category=MLLimitationCategory.uncertainty,
            statement="Reported uncertainty objects are analytical estimates and do not guarantee coverage on future data.",
            affected_scope=["prediction-intervals", "ood"],
        ),
    ]

    entry = MLModelRegistryEntry(
        registry_entry_id=registry_id,
        model_spec_ref=ml.model_spec.model_spec_id,
        model_version_ref=checkpoint.model_version_ref or run.output_model_version_ref or ml.inference_plan.model_version_ref,
        training_run_ref=run.training_run_id,
        checkpoint_ref=checkpoint.checkpoint_id,
        inference_plan_ref=ml.inference_plan.inference_plan_id,
        artifact_refs=[x.artifact_id for x in artifacts],
        evaluation_refs=evaluation_ids,
        representation_model_refs=[x.representation_model_id for x in rep.representation_models],
        aliases=["reference-energy-regressor"],
        tags=["neural", "regression", "research-reference"],
        lifecycle=MLRegistryLifecycle.registered,
        intended_use_ref=use.intended_use_id,
        limitation_refs=[x.limitation_id for x in limitation_records],
        registered_at="2026-09-27T16:00:00Z",
    )

    manifest = MLReproducibilityManifest(
        manifest_id="ml-repro-manifest:reference-energy:1.0.1",
        registry_entry_ref=entry.registry_entry_id,
        model_spec_ref=entry.model_spec_ref,
        model_version_ref=entry.model_version_ref,
        training_plan_ref=ml.training_plan.training_plan_id,
        training_run_ref=entry.training_run_ref,
        checkpoint_ref=entry.checkpoint_ref,
        runtime_requirement_ref=runtime.runtime_requirement_id,
        input_schema_ref=ml.inference_plan.input_schema_ref,
        output_refs=list(ml.model_spec.feature_schema.target_names) or ["output:energy_kwh"],
        artifact_refs=entry.artifact_refs,
        evaluation_refs=entry.evaluation_refs,
        intended_use_ref=use.intended_use_id,
        limitation_refs=entry.limitation_refs,
        model_foundation_fingerprint_sha256=ml.fingerprint(),
        training_lineage_fingerprint_sha256=train.fingerprint(),
        evaluation_fingerprint_sha256=evaluation.fingerprint(),
        explainability_fingerprint_sha256=explain.fingerprint(),
        representation_fingerprint_sha256=rep.fingerprint(),
        inference_fingerprint_sha256=infer.fingerprint(),
    )

    explain_refs = (
        [x.feature_attribution_id for x in explain.feature_attributions]
        + [x.saliency_map_id for x in explain.saliency_maps]
        + [x.attention_explanation_id for x in explain.attention_explanations]
        + [x.counterfactual_id for x in explain.counterfactual_explanations]
        + [x.embedding_explanation_id for x in explain.embedding_explanations]
    )
    representation_refs = (
        [x.representation_model_id for x in rep.representation_models]
        + [x.embedding_space_id for x in rep.embedding_spaces]
        + [x.similarity_result_id for x in rep.similarity_results]
        + [x.projection_id for x in rep.vector_projections]
        + [x.cluster_id for x in rep.clusters]
    )

    package = MLReproducibleModelPackage(
        package_id="ml-model-package:reference-energy:1.0.1",
        registry_entry_ref=entry.registry_entry_id,
        manifest_ref=manifest.manifest_id,
        artifact_refs=manifest.artifact_refs,
        runtime_requirement_ref=runtime.runtime_requirement_id,
        input_schema_ref=manifest.input_schema_ref,
        output_refs=manifest.output_refs,
        evaluation_refs=manifest.evaluation_refs,
        calibration_refs=[x.calibration_id for x in evaluation.calibration_records],
        uncertainty_refs=[x.uncertainty_estimate_id for x in evaluation.uncertainty_estimates],
        explainability_refs=explain_refs,
        representation_refs=representation_refs,
        inference_plan_ref=entry.inference_plan_ref,
        intended_use_ref=use.intended_use_id,
        limitation_refs=entry.limitation_refs,
    )

    return MLModelRegistryPackageBundle(
        ml_model_bundle=ml,
        training_lineage_bundle=train,
        evaluation_bundle=evaluation,
        explainability_bundle=explain,
        representation_bundle=rep,
        inference_bundle=infer,
        artifacts=artifacts,
        runtime_requirements=[runtime],
        intended_use_statements=[use],
        limitations=limitation_records,
        registry_entries=[entry],
        reproducibility_manifests=[manifest],
        model_packages=[package],
    )


def contract_document() -> dict[str, Any]:
    ref = reference_model_registry_package_bundle()
    entry = ref.registry_entries[0]
    package = ref.model_packages[0]
    manifest = ref.reproducibility_manifests[0]
    return {
        "ok": True,
        "release": CORE_RELEASE,
        "contract": CONTRACT_VERSION,
        "object_types": [
            "MLModelArtifactRecord",
            "MLRuntimeRequirementRecord",
            "MLIntendedUseStatement",
            "MLModelLimitationRecord",
            "MLModelRegistryEntry",
            "MLReproducibilityManifest",
            "MLReproducibleModelPackage",
            "MLModelRegistryPackageBundle",
        ],
        "integration": {
            "extends_machine_learning_neural_model_foundation_v3570": True,
            "extends_training_run_checkpoint_experiment_lineage_v3580": True,
            "extends_neural_evaluation_calibration_uncertainty_v3600": True,
            "extends_explainability_model_interpretation_v3610": True,
            "extends_neural_embedding_representation_intelligence_v3620": True,
            "extends_neural_inference_prediction_provenance_v3630": True,
            "registry_resolves_model_training_checkpoint_and_inference_lineage": True,
            "packages_resolve_evaluation_uncertainty_explainability_and_representation_objects": True,
        },
        "registry_capabilities": {
            "framework_neutral_registry_entries": True,
            "immutable_artifact_hashes": True,
            "model_version_and_checkpoint_lineage": True,
            "aliases_and_tags": True,
            "lifecycle_states_without_quality_certification": True,
            "intended_use_and_limitations": True,
        },
        "package_capabilities": {
            "portable_research_model_packages": True,
            "runtime_and_environment_requirements": True,
            "input_output_schema_bindings": True,
            "training_and_checkpoint_provenance": True,
            "evaluation_and_uncertainty_bindings": True,
            "explainability_and_representation_bindings": True,
            "deterministic_reproducibility_manifest": True,
            "deterministic_package_fingerprint": True,
        },
        "governance": {
            "registration_does_not_certify_quality": True,
            "portable_package_does_not_guarantee_reproducibility": True,
            "intended_use_does_not_authorize_autonomous_action": True,
            "model_package_is_not_evidence": True,
            "prediction_remains_analytical_output_not_evidence": True,
            "limitations_are_first_class_governed_objects": True,
            "artifact_integrity_uses_immutable_sha256": True,
        },
        "boundaries": {
            "core_trains_models": False,
            "core_runs_inference": False,
            "core_executes_model_packages": False,
            "core_installs_dependencies": False,
            "core_downloads_model_artifacts": False,
            "core_selects_best_model": False,
            "core_promotes_registry_entries": False,
            "core_certifies_model_quality": False,
            "core_certifies_reproducibility": False,
            "core_authorizes_autonomous_action": False,
            "core_promotes_predictions_to_evidence": False,
        },
        "reference": {
            "registry_entry_id": entry.registry_entry_id,
            "package_id": package.package_id,
            "manifest_id": manifest.manifest_id,
            "checkpoint_ref": entry.checkpoint_ref,
            "bundle_fingerprint_sha256": ref.fingerprint(),
            "package_fingerprint_sha256": package.fingerprint(),
            "manifest_fingerprint_sha256": manifest.fingerprint(),
        },
    }
