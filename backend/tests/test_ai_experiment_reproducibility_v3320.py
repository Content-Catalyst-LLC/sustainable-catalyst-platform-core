from copy import deepcopy
import pytest
from pydantic import ValidationError

from app.services.ai_experiment_reproducibility import (
    CONTRACT_VERSION,
    AIExperimentDefinition,
    AIExperimentPackageBundle,
    AIExperimentReproducibilityPackage,
    ExperimentRunBinding,
    ExperimentalCondition,
    ExperimentalFactor,
    FactorKind,
    ReproductionAttempt,
    ReproductionObservation,
    ReproductionStatus,
    ReproducibilityAssessment,
    ReproducibilityAssessmentKind,
    ReproducibilityPackageArtifact,
    ReproducibilityRequirement,
    contract_document,
    reference_experiment_bundle,
)


def test_contract_declares_experiment_reproducibility_system():
    doc = contract_document()
    assert doc["release"] == "3.32.0"
    assert doc["contract"] == CONTRACT_VERSION
    assert doc["boundaries"]["core_executes_experiments"] is False
    assert doc["boundaries"]["core_selects_winning_condition"] is False


def test_reference_bundle_is_valid():
    bundle = reference_experiment_bundle()
    assert bundle.experiment.conditions
    assert bundle.run_bindings
    assert bundle.reproducibility_package.requirements
    assert bundle.reproduction_attempts
    assert bundle.assessments


def test_experiment_fingerprint_is_stable():
    experiment = reference_experiment_bundle().experiment
    assert experiment.fingerprint() == deepcopy(experiment).fingerprint()
    assert len(experiment.fingerprint()) == 64


def test_experiment_fingerprint_ignores_status():
    experiment = reference_experiment_bundle().experiment
    other = deepcopy(experiment)
    other.status = "running"
    assert experiment.fingerprint() == other.fingerprint()


def test_factor_requires_values():
    with pytest.raises(ValidationError):
        ExperimentalFactor(
            factor_id="factor:test",
            name="Test",
            factor_kind=FactorKind.other,
            values=[],
        )


def test_duplicate_factor_ids_rejected():
    factor = ExperimentalFactor(
        factor_id="factor:test",
        name="Test",
        factor_kind=FactorKind.other,
        values=[1],
    )
    with pytest.raises(ValidationError):
        AIExperimentDefinition(
            experiment_id="experiment:test",
            name="Test",
            objective="test",
            factors=[factor, deepcopy(factor)],
        )


def test_duplicate_condition_ids_rejected():
    factor = ExperimentalFactor(
        factor_id="factor:test",
        name="Test",
        factor_kind=FactorKind.other,
        values=[1],
    )
    condition = ExperimentalCondition(
        condition_id="condition:test",
        name="Test",
        factor_assignments={"factor:test": 1},
        baseline=True,
    )
    with pytest.raises(ValidationError):
        AIExperimentDefinition(
            experiment_id="experiment:test",
            name="Test",
            objective="test",
            factors=[factor],
            conditions=[condition, deepcopy(condition)],
        )


def test_unknown_factor_assignment_rejected():
    with pytest.raises(ValidationError):
        AIExperimentDefinition(
            experiment_id="experiment:test",
            name="Test",
            objective="test",
            factors=[],
            conditions=[
                ExperimentalCondition(
                    condition_id="condition:test",
                    name="Test",
                    factor_assignments={"factor:missing": 1},
                    baseline=True,
                )
            ],
        )


def test_conditions_require_baseline():
    factor = ExperimentalFactor(
        factor_id="factor:test",
        name="Test",
        factor_kind=FactorKind.other,
        values=[1, 2],
    )
    with pytest.raises(ValidationError):
        AIExperimentDefinition(
            experiment_id="experiment:test",
            name="Test",
            objective="test",
            factors=[factor],
            conditions=[
                ExperimentalCondition(
                    condition_id="condition:test",
                    name="Test",
                    factor_assignments={"factor:test": 1},
                    baseline=False,
                )
            ],
        )


def test_run_binding_requires_job():
    with pytest.raises(ValidationError):
        ExperimentRunBinding(
            experiment_run_binding_id="run:test",
            experiment_ref="experiment:test",
            condition_ref="condition:test",
            replicate_index=1,
            runtime_environment_refs=["environment:test"],
        )


def test_run_binding_requires_environment():
    with pytest.raises(ValidationError):
        ExperimentRunBinding(
            experiment_run_binding_id="run:test",
            experiment_ref="experiment:test",
            condition_ref="condition:test",
            replicate_index=1,
            computational_job_refs=["job:test"],
        )


def test_run_binding_fingerprint_is_stable():
    run = reference_experiment_bundle().run_bindings[0]
    assert run.fingerprint() == deepcopy(run).fingerprint()


def test_package_artifact_requires_identity():
    with pytest.raises(ValidationError):
        ReproducibilityPackageArtifact(
            package_artifact_id="artifact:test",
            artifact_kind="manifest",
        )


def test_package_requires_run_binding_refs():
    bundle = reference_experiment_bundle()
    p = bundle.reproducibility_package.model_dump(mode="python")
    p["run_binding_refs"] = []
    with pytest.raises(ValidationError):
        AIExperimentReproducibilityPackage.model_validate(p)


def test_package_requires_requirements():
    bundle = reference_experiment_bundle()
    p = bundle.reproducibility_package.model_dump(mode="python")
    p["requirements"] = []
    with pytest.raises(ValidationError):
        AIExperimentReproducibilityPackage.model_validate(p)


def test_duplicate_requirement_ids_rejected():
    bundle = reference_experiment_bundle()
    p = bundle.reproducibility_package.model_dump(mode="python")
    p["requirements"] = [p["requirements"][0], deepcopy(p["requirements"][0])]
    with pytest.raises(ValidationError):
        AIExperimentReproducibilityPackage.model_validate(p)


def test_duplicate_package_artifact_ids_rejected():
    bundle = reference_experiment_bundle()
    p = bundle.reproducibility_package.model_dump(mode="python")
    p["artifacts"] = [p["artifacts"][0], deepcopy(p["artifacts"][0])]
    with pytest.raises(ValidationError):
        AIExperimentReproducibilityPackage.model_validate(p)


def test_package_fingerprint_ignores_created_at():
    package = reference_experiment_bundle().reproducibility_package
    assert package.fingerprint() == deepcopy(package).fingerprint()


def test_completed_reproduction_attempt_requires_observations():
    bundle = reference_experiment_bundle()
    attempt = bundle.reproduction_attempts[0].model_dump(mode="python")
    attempt["observations"] = []
    with pytest.raises(ValidationError):
        ReproductionAttempt.model_validate(attempt)


def test_duplicate_observation_requirement_refs_rejected():
    bundle = reference_experiment_bundle()
    attempt = bundle.reproduction_attempts[0].model_dump(mode="python")
    attempt["observations"] = [
        attempt["observations"][0],
        deepcopy(attempt["observations"][0]),
    ]
    with pytest.raises(ValidationError):
        ReproductionAttempt.model_validate(attempt)


def test_attempt_fingerprint_ignores_lifecycle():
    attempt = reference_experiment_bundle().reproduction_attempts[0]
    other = deepcopy(attempt)
    other.status = ReproductionStatus.running
    other.started_at = None
    other.completed_at = None
    assert attempt.fingerprint() == other.fingerprint()


def test_assessment_count_validation():
    with pytest.raises(ValidationError):
        ReproducibilityAssessment(
            reproducibility_assessment_id="assessment:test",
            reproducibility_package_ref="package:test",
            reproduction_attempt_ref="attempt:test",
            assessment=ReproducibilityAssessmentKind.exact,
            strict_requirements_total=1,
            strict_requirements_matched=2,
            non_strict_requirements_total=0,
            non_strict_requirements_matched=0,
        )


def test_assessment_fingerprint_is_stable():
    assessment = reference_experiment_bundle().assessments[0]
    assert assessment.fingerprint() == deepcopy(assessment).fingerprint()


def test_bundle_rejects_wrong_package_experiment_ref():
    bundle = reference_experiment_bundle()
    package = deepcopy(bundle.reproducibility_package)
    package.experiment_ref = "experiment:other"
    with pytest.raises(ValidationError):
        AIExperimentPackageBundle(
            experiment=bundle.experiment,
            run_bindings=bundle.run_bindings,
            reproducibility_package=package,
            reproduction_attempts=bundle.reproduction_attempts,
            assessments=bundle.assessments,
        )


def test_bundle_rejects_wrong_experiment_fingerprint():
    bundle = reference_experiment_bundle()
    package = deepcopy(bundle.reproducibility_package)
    package.experiment_fingerprint_sha256 = "f" * 64
    with pytest.raises(ValidationError):
        AIExperimentPackageBundle(
            experiment=bundle.experiment,
            run_bindings=bundle.run_bindings,
            reproducibility_package=package,
            reproduction_attempts=bundle.reproduction_attempts,
            assessments=bundle.assessments,
        )


def test_bundle_rejects_missing_run_binding():
    bundle = reference_experiment_bundle()
    with pytest.raises(ValidationError):
        AIExperimentPackageBundle(
            experiment=bundle.experiment,
            run_bindings=[bundle.run_bindings[0]],
            reproducibility_package=bundle.reproducibility_package,
            reproduction_attempts=bundle.reproduction_attempts,
            assessments=bundle.assessments,
        )


def test_bundle_rejects_attempt_for_other_package():
    bundle = reference_experiment_bundle()
    attempt = deepcopy(bundle.reproduction_attempts[0])
    attempt.reproducibility_package_ref = "package:other"
    with pytest.raises(ValidationError):
        AIExperimentPackageBundle(
            experiment=bundle.experiment,
            run_bindings=bundle.run_bindings,
            reproducibility_package=bundle.reproducibility_package,
            reproduction_attempts=[attempt],
            assessments=[],
        )


def test_bundle_rejects_assessment_for_missing_attempt():
    bundle = reference_experiment_bundle()
    assessment = deepcopy(bundle.assessments[0])
    assessment.reproduction_attempt_ref = "attempt:missing"
    with pytest.raises(ValidationError):
        AIExperimentPackageBundle(
            experiment=bundle.experiment,
            run_bindings=bundle.run_bindings,
            reproducibility_package=bundle.reproducibility_package,
            reproduction_attempts=bundle.reproduction_attempts,
            assessments=[assessment],
        )


def test_bundle_fingerprint_is_stable():
    bundle = reference_experiment_bundle()
    assert bundle.fingerprint() == deepcopy(bundle).fingerprint()
    assert len(bundle.fingerprint()) == 64


def test_reference_has_exact_reproducibility_assessment():
    assessment = reference_experiment_bundle().assessments[0]
    assert assessment.assessment == ReproducibilityAssessmentKind.exact
    assert assessment.strict_requirements_total == 4
    assert assessment.strict_requirements_matched == 4


def test_reference_observations_match_all_requirements():
    bundle = reference_experiment_bundle()
    package = bundle.reproducibility_package
    attempt = bundle.reproduction_attempts[0]
    assert len(attempt.observations) == len(package.requirements)
    assert all(item.matched is True for item in attempt.observations)


def test_reference_binds_baseline_and_candidate():
    bundle = reference_experiment_bundle()
    conditions = {item.condition_id: item for item in bundle.experiment.conditions}
    assert conditions["condition:baseline"].baseline is True
    assert conditions["condition:candidate"].baseline is False


def test_reference_binds_jobs_and_environments():
    bundle = reference_experiment_bundle()
    assert all(item.computational_job_refs for item in bundle.run_bindings)
    assert all(item.runtime_environment_refs for item in bundle.run_bindings)


def test_reference_package_is_content_addressed():
    package = reference_experiment_bundle().reproducibility_package
    assert all(
        artifact.content_sha256 is not None
        for artifact in package.artifacts
    )


def test_core_does_not_execute_or_select_winner():
    doc = contract_document()
    assert doc["boundaries"]["core_executes_experiments"] is False
    assert doc["boundaries"]["core_selects_winning_condition"] is False
    assert doc["boundaries"]["core_certifies_scientific_validity"] is False


def test_core_does_not_duplicate_storage():
    doc = contract_document()
    assert doc["integration"]["core_duplicates_dataset_storage"] is False
    assert doc["integration"]["core_duplicates_model_artifacts"] is False
    assert doc["integration"]["core_duplicates_evaluation_storage"] is False
