import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.routers import ml_dataset_provenance
from app.services.ml_dataset_provenance import (
    CONTRACT_VERSION,
    CORE_RELEASE,
    MLDatasetFeatureTransformationLineageBundle,
    contract_document,
    reference_dataset_feature_transformation_bundle,
)


def test_contract_identity():
    d = contract_document()
    assert CORE_RELEASE == "3.59.0"
    assert CONTRACT_VERSION == "sc.core.neural-dataset-feature-transformation-provenance.v1"
    assert d["release"] == "3.59.0"
    assert d["integration"]["extends_training_run_checkpoint_experiment_lineage_v3580"] is True


def test_lineage_chain_is_first_class():
    assert contract_document()["lineage_chain"] == [
        "MLRawSourceReference", "MLDatasetSnapshotRecord", "MLDatasetPartitionRecord",
        "MLTransformationPipelineRecord", "MLFeatureRepresentationRecord", "MLTensorInputRecord",
    ]


def test_core_does_not_execute_data_pipeline():
    b = contract_document()["boundaries"]
    for key in (
        "core_ingests_raw_data", "core_materializes_datasets", "core_executes_splits",
        "core_applies_transformations", "core_fits_transform_state", "core_creates_tensors",
        "core_installs_ml_packages", "core_accepts_arbitrary_executable_transform_payloads",
        "core_treats_model_inputs_as_evidence",
    ):
        assert b[key] is False


def test_reference_bundle_is_valid_and_fingerprinted():
    b = reference_dataset_feature_transformation_bundle()
    assert len(b.fingerprint()) == 64
    assert len(b.raw_sources) == 2
    assert len(b.partitions) == 3
    assert len(b.transformation_pipelines) == 3
    assert len(b.feature_representations) == 3
    assert len(b.tensor_inputs) == 3


def test_fingerprint_is_stable_for_same_payload():
    a = reference_dataset_feature_transformation_bundle()
    b = MLDatasetFeatureTransformationLineageBundle.model_validate(a.model_dump(mode="json"))
    assert a.fingerprint() == b.fingerprint()


def invalid(mutator):
    payload = reference_dataset_feature_transformation_bundle().model_dump(mode="json")
    mutator(payload)
    with pytest.raises(ValidationError):
        MLDatasetFeatureTransformationLineageBundle.model_validate(payload)


def test_snapshot_raw_source_must_resolve():
    invalid(lambda p: p["dataset_snapshots"][0].__setitem__("raw_source_refs", ["ml-source:missing"]))


def test_training_plan_dataset_must_have_snapshot():
    invalid(lambda p: p.__setitem__("dataset_snapshots", []))


def test_partition_snapshot_must_resolve():
    invalid(lambda p: p["partitions"][0].__setitem__("snapshot_ref", "ml-dataset-snapshot:missing"))


def test_partition_dataset_must_match_snapshot():
    invalid(lambda p: p["partitions"][0].__setitem__("dataset_version_ref", "dataset-version:wrong"))


def test_pipeline_partition_must_resolve():
    invalid(lambda p: p["transformation_pipelines"][0].__setitem__("source_partition_ref", "ml-partition:missing"))


def test_pipeline_dataset_must_match_partition():
    invalid(lambda p: p["transformation_pipelines"][0].__setitem__("dataset_version_ref", "dataset-version:wrong"))


def test_pipeline_step_ordinals_must_be_contiguous():
    invalid(lambda p: p["transformation_pipelines"][0]["steps"][1].__setitem__("ordinal", 3))


def test_fitted_transform_state_must_use_training_partition():
    invalid(lambda p: p["transformation_pipelines"][1]["steps"][0].__setitem__("fitted_on_partition_ref", "ml-partition:reference-energy:validation"))


def test_pipeline_output_representation_must_resolve():
    invalid(lambda p: p["transformation_pipelines"][0].__setitem__("output_representation_ref", "ml-feature-representation:missing"))


def test_representation_feature_names_must_match_schema():
    invalid(lambda p: p["feature_representations"][0].__setitem__("feature_names", ["temperature_c", "energy_kwh"]))


def test_representation_pipeline_link_must_be_consistent():
    invalid(lambda p: p["feature_representations"][0].__setitem__("transformation_pipeline_ref", p["transformation_pipelines"][1]["pipeline_id"]))


def test_tensor_feature_names_must_match_ordered_model_inputs():
    invalid(lambda p: p["tensor_inputs"][0].__setitem__("feature_names", ["humidity_pct", "temperature_c"]))


def test_tabular_tensor_last_dimension_must_match_features():
    invalid(lambda p: p["tensor_inputs"][0].__setitem__("shape", [800, 3]))


def test_arbitrary_executable_transform_payload_is_rejected():
    invalid(lambda p: p["transformation_pipelines"][0]["steps"][0].__setitem__("arbitrary_executable_payload_embedded", True))


def test_training_lineage_refs_are_carried_forward():
    b = reference_dataset_feature_transformation_bundle()
    assert b.training_experiment_refs == ["ml-experiment:reference-energy:v1"]
    assert b.training_run_refs == ["ml-training-run:reference-energy:run-001"]


def test_public_contract_route():
    app = FastAPI(); app.include_router(ml_dataset_provenance.public_router)
    r = TestClient(app).get("/public/v1/ml-dataset-provenance/contract")
    assert r.status_code == 200
    assert r.json()["release"] == "3.59.0"


def test_private_reference_route():
    app = FastAPI(); app.include_router(ml_dataset_provenance.router)
    r = TestClient(app).get("/api/v1/ml-dataset-provenance/reference")
    assert r.status_code == 200
    assert len(r.json()["bundle_fingerprint_sha256"]) == 64
