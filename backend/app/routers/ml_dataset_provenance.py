from fastapi import APIRouter

from ..services.ml_dataset_provenance import (
    CONTRACT_VERSION,
    CORE_RELEASE,
    MLDatasetFeatureTransformationLineageBundle,
    MLDatasetPartitionRecord,
    MLDatasetSnapshotRecord,
    MLFeatureRepresentationRecord,
    MLRawSourceReference,
    MLTensorInputRecord,
    MLTransformationPipelineRecord,
    contract_document,
    reference_dataset_feature_transformation_bundle,
)

router = APIRouter(prefix="/api/v1/ml-dataset-provenance", tags=["ml-dataset-provenance"])
public_router = APIRouter(prefix="/public/v1/ml-dataset-provenance", tags=["public-ml-dataset-provenance"])

@router.get("/contract")
def get_contract(): return contract_document()

@public_router.get("/contract")
def get_public_contract(): return contract_document()

@router.get("/reference")
def get_reference():
    b = reference_dataset_feature_transformation_bundle()
    return {"ok": True, "release": CORE_RELEASE, "contract": CONTRACT_VERSION, "bundle": b.model_dump(mode="json", exclude_none=True), "bundle_fingerprint_sha256": b.fingerprint()}

@router.post("/validate-source")
def validate_source(body: MLRawSourceReference): return {"ok": True, "release": CORE_RELEASE, "contract": CONTRACT_VERSION, "fingerprint_sha256": body.fingerprint()}

@router.post("/validate-snapshot")
def validate_snapshot(body: MLDatasetSnapshotRecord): return {"ok": True, "release": CORE_RELEASE, "contract": CONTRACT_VERSION, "fingerprint_sha256": body.fingerprint()}

@router.post("/validate-partition")
def validate_partition(body: MLDatasetPartitionRecord): return {"ok": True, "release": CORE_RELEASE, "contract": CONTRACT_VERSION, "fingerprint_sha256": body.fingerprint()}

@router.post("/validate-pipeline")
def validate_pipeline(body: MLTransformationPipelineRecord): return {"ok": True, "release": CORE_RELEASE, "contract": CONTRACT_VERSION, "fingerprint_sha256": body.fingerprint()}

@router.post("/validate-representation")
def validate_representation(body: MLFeatureRepresentationRecord): return {"ok": True, "release": CORE_RELEASE, "contract": CONTRACT_VERSION, "fingerprint_sha256": body.fingerprint()}

@router.post("/validate-tensor-input")
def validate_tensor_input(body: MLTensorInputRecord): return {"ok": True, "release": CORE_RELEASE, "contract": CONTRACT_VERSION, "fingerprint_sha256": body.fingerprint()}

@router.post("/validate-bundle")
def validate_bundle(body: MLDatasetFeatureTransformationLineageBundle): return {"ok": True, "release": CORE_RELEASE, "contract": CONTRACT_VERSION, "bundle_fingerprint_sha256": body.fingerprint()}
