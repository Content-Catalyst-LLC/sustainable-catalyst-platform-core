from copy import deepcopy

import pytest
from pydantic import ValidationError

from app.services.ai_inference_provenance import (
    CONTRACT_VERSION,
    AIArtifactKind,
    AIArtifactProvenance,
    AIInferenceInput,
    AIInferenceParameterSet,
    AIInferenceRun,
    AIInferenceRunBundle,
    AIInferenceStatus,
    AIInputKind,
    compare_inference_runs,
    contract_document,
    reference_inference_run,
)


def test_contract_declares_inference_provenance_system():
    doc = contract_document()
    assert doc["release"] == "3.29.0"
    assert doc["contract"] == CONTRACT_VERSION
    assert doc["integration"]["duplicates_runtime_artifact_model"] is False
    assert doc["boundaries"]["core_executes_inference"] is False


def test_reference_bundle_is_valid():
    bundle = reference_inference_run()
    run = bundle.inference_run
    assert run.status == AIInferenceStatus.completed
    assert run.ai_model_version_ref == (
        "ai-model-version:reference-scientific-regressor:1.0.0"
    )
    assert run.computational_job_ref == "job:reference-inference-001"
    assert run.artifacts


def test_input_requires_payload_or_reference():
    with pytest.raises(ValidationError):
        AIInferenceInput(
            input_id="input:test",
            input_kind=AIInputKind.text,
        )


def test_input_fingerprint_is_stable():
    item = reference_inference_run().inference_run.inputs[0]
    assert item.fingerprint() == deepcopy(item).fingerprint()
    assert len(item.fingerprint()) == 64


def test_parameter_set_fingerprint_is_stable():
    params = reference_inference_run().inference_run.parameter_set
    assert params is not None
    assert params.fingerprint() == deepcopy(params).fingerprint()


def test_artifact_requires_payload_or_reference():
    with pytest.raises(ValidationError):
        AIArtifactProvenance(
            ai_artifact_id="artifact:test",
            artifact_kind=AIArtifactKind.prediction,
            inference_run_ref="inference-run:test",
            ai_model_ref="ai-model:test",
            ai_model_version_ref="ai-model-version:test:1",
        )


def test_artifact_requires_ai_model_version_identity():
    with pytest.raises(ValidationError):
        AIArtifactProvenance(
            ai_artifact_id="artifact:test",
            artifact_kind=AIArtifactKind.prediction,
            inference_run_ref="inference-run:test",
            ai_model_ref="ai-model:test",
            ai_model_version_ref="model-version:test:1",
            scalar_value=1.0,
        )


def test_artifact_fingerprint_ignores_created_at():
    artifact = reference_inference_run().inference_run.artifacts[0]
    assert artifact.fingerprint() == deepcopy(artifact).fingerprint()
    assert len(artifact.fingerprint()) == 64


def test_completed_run_requires_artifact():
    bundle = reference_inference_run()
    run = bundle.inference_run
    data = run.model_dump(mode="python")
    data["artifacts"] = []
    with pytest.raises(ValidationError):
        AIInferenceRun.model_validate(data)


def test_duplicate_input_ids_rejected():
    run = reference_inference_run().inference_run
    data = run.model_dump(mode="python")
    data["status"] = "running"
    data["artifacts"] = []
    data["inputs"] = [data["inputs"][0], deepcopy(data["inputs"][0])]
    with pytest.raises(ValidationError):
        AIInferenceRun.model_validate(data)


def test_duplicate_artifact_ids_rejected():
    run = reference_inference_run().inference_run
    data = run.model_dump(mode="python")
    data["artifacts"] = [data["artifacts"][0], deepcopy(data["artifacts"][0])]
    with pytest.raises(ValidationError):
        AIInferenceRun.model_validate(data)


def test_artifact_must_match_run_identity():
    run = reference_inference_run().inference_run
    data = run.model_dump(mode="python")
    data["artifacts"][0]["inference_run_ref"] = "inference-run:other"
    with pytest.raises(ValidationError):
        AIInferenceRun.model_validate(data)


def test_artifact_source_input_refs_must_exist():
    run = reference_inference_run().inference_run
    data = run.model_dump(mode="python")
    data["artifacts"][0]["source_input_refs"] = ["input:missing"]
    with pytest.raises(ValidationError):
        AIInferenceRun.model_validate(data)


def test_run_fingerprint_ignores_status_and_usage():
    run = reference_inference_run().inference_run
    other = deepcopy(run)
    other.status = AIInferenceStatus.running
    other.usage.latency_ms = 999.0
    assert run.fingerprint() == other.fingerprint()


def test_run_fingerprint_is_stable():
    run = reference_inference_run().inference_run
    assert run.fingerprint() == deepcopy(run).fingerprint()
    assert len(run.fingerprint()) == 64


def test_bundle_fingerprint_is_stable():
    bundle = reference_inference_run()
    assert bundle.fingerprint() == deepcopy(bundle).fingerprint()
    assert len(bundle.fingerprint()) == 64


def test_compare_identical_runs_is_exact():
    run = reference_inference_run().inference_run
    comparison = compare_inference_runs(run, deepcopy(run))
    assert comparison.exact_match is True
    assert comparison.differences == []


def test_compare_detects_model_version_change():
    left = reference_inference_run().inference_run
    right = deepcopy(left)
    right.ai_model_version_ref = "ai-model-version:reference-scientific-regressor:2.0.0"
    right.artifacts[0].ai_model_version_ref = right.ai_model_version_ref
    comparison = compare_inference_runs(left, right)
    assert comparison.exact_match is False
    assert any(
        item.field == "ai_model_version_ref"
        for item in comparison.differences
    )


def test_reference_artifact_links_exact_input():
    run = reference_inference_run().inference_run
    artifact = run.artifacts[0]
    assert artifact.source_input_refs == [run.inputs[0].input_id]


def test_reference_usage_is_observational_not_identity():
    run = reference_inference_run().inference_run
    assert run.usage is not None
    assert run.usage.latency_ms == 12.5
    assert run.usage.unit_kind == "rows"


def test_prompt_and_retrieval_refs_are_reserved_not_required():
    run = reference_inference_run().inference_run
    assert run.prompt_version_ref is None
    assert run.retrieval_context_ref is None


def test_runtime_artifact_model_is_linked_not_duplicated():
    artifact = reference_inference_run().inference_run.artifacts[0]
    assert hasattr(artifact, "runtime_artifact_ref")
    assert hasattr(artifact, "execution_result_ref")
