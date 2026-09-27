from fastapi import APIRouter
from app.services.spark_runtime import OPERATIONS, PROVIDER_ENDPOINT, adapter_descriptor, contract_document, reference_bundle, runtime_catalog_entry

router = APIRouter(prefix="/v1/spark-runtime", tags=["spark-runtime"])

@router.get("/contract")
def spark_contract():
    return contract_document()

@router.get("/adapter")
def spark_adapter():
    return adapter_descriptor()

@router.get("/reference")
def spark_reference():
    return reference_bundle()

@router.get("/catalog-entry")
def spark_catalog_entry():
    return runtime_catalog_entry()

@router.get("/operations")
def spark_operations():
    return {"ok": True, "operations": list(OPERATIONS), "provider_endpoint": PROVIDER_ENDPOINT}
