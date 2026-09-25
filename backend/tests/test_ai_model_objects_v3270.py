from copy import deepcopy

import pytest
from pydantic import ValidationError

from app.services.ai_model_objects import (
    CONTRACT_VERSION,
    AIModel,
    AIModelArtifact,
    AIModelCapability,
    AIModelKind,
    AIModelProvider,
    AIModelProvider,
    AIModelStatus,
    AIModelVersion,
    AIModelVersionBinding,
    AIProviderKind,
    compare_model_versions,
    contract_document,
    reference_ai_model,
)


def test_contract_declares_ai_model_object_system():
    doc = contract_document()
    assert doc["release"] == "3.27.0"
    assert doc["contract"] == CONTRACT_VERSION
    assert doc["integration"]["duplicates_generic_model_registry"] is False
    assert doc["boundaries"]["core_trains_models"] is False
    assert doc["boundaries"]["core_runs_inference"] is False


def test_reference_binding_is_valid():
    binding = reference_ai_model()
    assert binding.model.model_id == binding.model_version.model_id
    assert binding.model.predictive_model_ref is not None
    assert binding.model.research_model_ref is not None


def test_model_fingerprint_is_stable_across_created_at():
    a = reference_ai_model().model
    b = deepcopy(a)
    assert a.fingerprint() == b.fingerprint()
    assert len(a.fingerprint()) == 64


def test_model_version_fingerprint_is_stable():
    version = reference_ai_model().model_version
    assert version.fingerprint() == deepcopy(version).fingerprint()
    assert len(version.fingerprint()) == 64


def test_binding_fingerprint_is_stable():
    binding = reference_ai_model()
    assert binding.fingerprint() == deepcopy(binding).fingerprint()
    assert len(binding.fingerprint()) == 64


def test_duplicate_capability_keys_rejected():
    provider = AIModelProvider(
        provider_id="provider:test",
        name="Test",
        provider_kind=AIProviderKind.local,
    )
    with pytest.raises(ValidationError):
        AIModel(
            model_id="ai-model:test",
            name="Test",
            model_kind=AIModelKind.classical_ml,
            provider=provider,
            capabilities=[
                AIModelCapability(capability_key="x", task="regression"),
                AIModelCapability(capability_key="x", task="classification"),
            ],
        )


def test_self_parent_model_rejected():
    provider = AIModelProvider(
        provider_id="provider:test",
        name="Test",
        provider_kind=AIProviderKind.local,
    )
    with pytest.raises(ValidationError):
        AIModel(
            model_id="ai-model:test",
            name="Test",
            model_kind=AIModelKind.classical_ml,
            provider=provider,
            parent_model_ref="ai-model:test",
        )


def test_duplicate_artifact_ids_rejected():
    with pytest.raises(ValidationError):
        AIModelVersion(
            model_version_id="ai-model-version:test:1",
            model_id="ai-model:test",
            version="1",
            artifacts=[
                AIModelArtifact(artifact_id="artifact:x", artifact_kind="weights"),
                AIModelArtifact(artifact_id="artifact:x", artifact_kind="config"),
            ],
        )


def test_model_version_binding_rejects_wrong_model_id():
    binding = reference_ai_model()
    data = binding.model_version.model_dump(mode="python")
    data["model_id"] = "ai-model:other"
    with pytest.raises(ValidationError):
        AIModelVersionBinding(
            model=binding.model,
            model_version=AIModelVersion.model_validate(data),
        )


def test_version_comparison_detects_weights_change():
    left = reference_ai_model().model_version
    right = deepcopy(left)
    right.weights_sha256 = "c" * 64
    comparison = compare_model_versions(left, right)
    assert comparison.exact_match is False
    assert any(item.field == "weights_sha256" for item in comparison.differences)


def test_version_comparison_identical_is_exact():
    left = reference_ai_model().model_version
    comparison = compare_model_versions(left, deepcopy(left))
    assert comparison.exact_match is True
    assert comparison.differences == []


def test_hash_validation_rejects_short_weights_hash():
    with pytest.raises(ValidationError):
        AIModelVersion(
            model_version_id="ai-model-version:test:1",
            model_id="ai-model:test",
            version="1",
            weights_sha256="abc",
        )


def test_provider_identity_is_explicit():
    binding = reference_ai_model()
    assert binding.model.provider.provider_id == "provider:sustainable-catalyst-local"
    assert binding.model.provider.provider_kind == AIProviderKind.local


def test_reference_artifacts_are_content_addressed():
    version = reference_ai_model().model_version
    assert len(version.artifacts) == 2
    assert all(item.content_sha256 for item in version.artifacts)


def test_version_links_dataset_and_runtime_lineage():
    version = reference_ai_model().model_version
    assert version.training_dataset_refs
    assert version.evaluation_dataset_refs
    assert version.runtime_environment_ref is not None
