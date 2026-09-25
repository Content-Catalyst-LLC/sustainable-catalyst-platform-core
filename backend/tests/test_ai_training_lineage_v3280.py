from copy import deepcopy

import pytest
from pydantic import ValidationError

from app.services.ai_training_lineage import (
    CONTRACT_VERSION,
    DatasetArtifact,
    DatasetIdentity,
    DatasetModality,
    DatasetVersion,
    DatasetVersionBinding,
    FeatureDefinition,
    FeatureSet,
    TrainingLineage,
    TrainingLineageBundle,
    TransformationStep,
    contract_document,
    reference_training_lineage,
)


def test_contract_declares_ai_training_lineage_system():
    doc = contract_document()
    assert doc["release"] == "3.28.0"
    assert doc["contract"] == CONTRACT_VERSION
    assert doc["integration"]["duplicates_generic_dataset_registry"] is False
    assert doc["boundaries"]["core_trains_models"] is False


def test_reference_bundle_is_valid():
    bundle = reference_training_lineage()
    assert bundle.training_lineage.ai_model_version_ref == (
        "ai-model-version:reference-scientific-regressor:1.0.0"
    )
    assert bundle.training_lineage.training_job_ref == "job:reference-model-training"
    assert bundle.dataset_bindings
    assert bundle.feature_sets


def test_dataset_identity_fingerprint_is_stable():
    dataset = reference_training_lineage().dataset_bindings[0].dataset
    assert dataset.fingerprint() == deepcopy(dataset).fingerprint()
    assert len(dataset.fingerprint()) == 64


def test_dataset_version_fingerprint_ignores_created_at():
    version = reference_training_lineage().dataset_bindings[0].dataset_version
    other = deepcopy(version)
    assert version.fingerprint() == other.fingerprint()


def test_dataset_binding_rejects_wrong_dataset_id():
    bundle = reference_training_lineage()
    dataset = bundle.dataset_bindings[0].dataset
    version = deepcopy(bundle.dataset_bindings[0].dataset_version)
    version.dataset_id = "dataset:other"
    with pytest.raises(ValidationError):
        DatasetVersionBinding(dataset=dataset, dataset_version=version)


def test_dataset_version_rejects_self_parent():
    with pytest.raises(ValidationError):
        DatasetVersion(
            dataset_version_id="dataset-version:test:v1",
            dataset_id="dataset:test",
            version="v1",
            parent_dataset_version_ref="dataset-version:test:v1",
        )


def test_duplicate_dataset_artifact_ids_rejected():
    with pytest.raises(ValidationError):
        DatasetVersion(
            dataset_version_id="dataset-version:test:v1",
            dataset_id="dataset:test",
            version="v1",
            artifacts=[
                DatasetArtifact(artifact_id="artifact:x", artifact_kind="data"),
                DatasetArtifact(artifact_id="artifact:x", artifact_kind="schema"),
            ],
        )


def test_feature_set_rejects_duplicate_features():
    with pytest.raises(ValidationError):
        FeatureSet(
            feature_set_id="feature-set:test",
            dataset_version_ref="dataset-version:test:v1",
            version="v1",
            features=[
                FeatureDefinition(feature_id="feature:x", name="x", data_type="float"),
                FeatureDefinition(feature_id="feature:x", name="x2", data_type="float"),
            ],
        )


def test_feature_set_rejects_unknown_target():
    with pytest.raises(ValidationError):
        FeatureSet(
            feature_set_id="feature-set:test",
            dataset_version_ref="dataset-version:test:v1",
            version="v1",
            features=[
                FeatureDefinition(feature_id="feature:x", name="x", data_type="float"),
            ],
            target_feature_refs=["feature:y"],
        )


def test_feature_set_fingerprint_order_insensitive_by_default():
    bundle = reference_training_lineage()
    fs = bundle.feature_sets[0]
    other = deepcopy(fs)
    other.features = list(reversed(other.features))
    assert fs.fingerprint() == other.fingerprint()


def test_training_lineage_rejects_noncontiguous_transform_steps():
    with pytest.raises(ValidationError):
        TrainingLineage(
            training_lineage_id="training-lineage:test",
            ai_model_ref="ai-model:test",
            ai_model_version_ref="ai-model-version:test:1",
            training_job_ref="job:test",
            transformations=[
                TransformationStep(
                    transformation_id="transform:a",
                    ordinal=2,
                    operation="normalize",
                ),
            ],
        )


def test_training_lineage_fingerprint_is_stable():
    lineage = reference_training_lineage().training_lineage
    assert lineage.fingerprint() == deepcopy(lineage).fingerprint()
    assert len(lineage.fingerprint()) == 64


def test_training_lineage_captures_seed_and_hyperparameters():
    lineage = reference_training_lineage().training_lineage
    assert lineage.random_seed == 427
    assert lineage.hyperparameters["learning_rate"] == 0.05


def test_training_bundle_rejects_missing_dataset_version():
    bundle = reference_training_lineage()
    with pytest.raises(ValidationError):
        TrainingLineageBundle(
            dataset_bindings=[],
            feature_sets=bundle.feature_sets,
            training_lineage=bundle.training_lineage,
        )


def test_training_bundle_rejects_missing_feature_set():
    bundle = reference_training_lineage()
    with pytest.raises(ValidationError):
        TrainingLineageBundle(
            dataset_bindings=bundle.dataset_bindings,
            feature_sets=[],
            training_lineage=bundle.training_lineage,
        )


def test_training_bundle_fingerprint_is_stable():
    bundle = reference_training_lineage()
    assert bundle.fingerprint() == deepcopy(bundle).fingerprint()
    assert len(bundle.fingerprint()) == 64


def test_reference_dataset_is_content_addressed():
    version = reference_training_lineage().dataset_bindings[0].dataset_version
    assert version.content_sha256 == "a" * 64
    assert version.schema_sha256 == "b" * 64


def test_reference_lineage_links_environment_and_jobs():
    bundle = reference_training_lineage()
    version = bundle.dataset_bindings[0].dataset_version
    lineage = bundle.training_lineage
    assert version.creation_job_ref is not None
    assert version.runtime_environment_ref is not None
    assert lineage.training_job_ref is not None
    assert lineage.runtime_environment_ref is not None
