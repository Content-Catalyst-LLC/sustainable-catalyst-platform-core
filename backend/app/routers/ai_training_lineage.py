from __future__ import annotations

from fastapi import APIRouter

from ..services.ai_training_lineage import (
    CONTRACT_VERSION,
    CORE_RELEASE,
    DatasetIdentity,
    DatasetVersion,
    DatasetVersionBinding,
    FeatureSet,
    TrainingLineage,
    TrainingLineageBundle,
    contract_document,
    reference_training_lineage,
)

router = APIRouter(prefix="/api/v1/ai-training-lineage", tags=["ai-training-lineage"])
public_router = APIRouter(prefix="/public/v1/ai-training-lineage", tags=["public-ai-training-lineage"])


@router.get("/contract")
def get_contract():
    return contract_document()


@public_router.get("/contract")
def get_public_contract():
    return contract_document()


@router.get("/reference")
def get_reference():
    bundle = reference_training_lineage()
    return {
        "ok": True,
        "release": CORE_RELEASE,
        "contract": CONTRACT_VERSION,
        "bundle": bundle.model_dump(mode="json", exclude_none=True),
        "bundle_fingerprint_sha256": bundle.fingerprint(),
        "training_lineage_fingerprint_sha256": bundle.training_lineage.fingerprint(),
        "dataset_version_fingerprints": {
            item.dataset_version.dataset_version_id: item.dataset_version.fingerprint()
            for item in bundle.dataset_bindings
        },
        "feature_set_fingerprints": {
            item.feature_set_id: item.fingerprint()
            for item in bundle.feature_sets
        },
    }


@router.post("/validate-dataset")
def validate_dataset(body: DatasetIdentity):
    return {
        "ok": True,
        "release": CORE_RELEASE,
        "contract": CONTRACT_VERSION,
        "dataset_fingerprint_sha256": body.fingerprint(),
        "dataset": body.model_dump(mode="json", exclude_none=True),
    }


@router.post("/validate-dataset-version")
def validate_dataset_version(body: DatasetVersion):
    return {
        "ok": True,
        "release": CORE_RELEASE,
        "contract": CONTRACT_VERSION,
        "dataset_version_fingerprint_sha256": body.fingerprint(),
        "dataset_version": body.model_dump(mode="json", exclude_none=True),
    }


@router.post("/validate-dataset-binding")
def validate_dataset_binding(body: DatasetVersionBinding):
    return {
        "ok": True,
        "release": CORE_RELEASE,
        "contract": CONTRACT_VERSION,
        "dataset_binding_fingerprint_sha256": body.fingerprint(),
        "binding": body.model_dump(mode="json", exclude_none=True),
    }


@router.post("/validate-feature-set")
def validate_feature_set(body: FeatureSet):
    return {
        "ok": True,
        "release": CORE_RELEASE,
        "contract": CONTRACT_VERSION,
        "feature_set_fingerprint_sha256": body.fingerprint(),
        "feature_set": body.model_dump(mode="json", exclude_none=True),
    }


@router.post("/validate-training-lineage")
def validate_training_lineage(body: TrainingLineage):
    return {
        "ok": True,
        "release": CORE_RELEASE,
        "contract": CONTRACT_VERSION,
        "training_lineage_fingerprint_sha256": body.fingerprint(),
        "training_lineage": body.model_dump(mode="json", exclude_none=True),
    }


@router.post("/validate-bundle")
def validate_bundle(body: TrainingLineageBundle):
    return {
        "ok": True,
        "release": CORE_RELEASE,
        "contract": CONTRACT_VERSION,
        "bundle_fingerprint_sha256": body.fingerprint(),
        "bundle": body.model_dump(mode="json", exclude_none=True),
    }
