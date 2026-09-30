from fastapi import APIRouter
from app.services.reproducible_graph_investigation_package import (
    GraphInvestigationManifest,
    InvestigationObjectBinding,
    ReproducibleGraphInvestigationPackageBundle,
    contract_document,
    reference_reproducible_graph_investigation_package_bundle,
)

router=APIRouter(prefix="/v1/graph-investigation-package",tags=["graph-investigation-package"])
public_router=APIRouter(prefix="/public/v1/graph-investigation-package",tags=["graph-investigation-package-public"])

@router.get("/contract")
def private_contract(): return contract_document()

@public_router.get("/contract")
def public_contract(): return contract_document()

@router.get("/reference")
def reference(): return {"ok":True,"bundle":reference_reproducible_graph_investigation_package_bundle().model_dump(mode="json")}

@router.post("/validate-binding")
def validate_binding(payload: InvestigationObjectBinding): return {"ok":True,"fingerprint_sha256":payload.fingerprint()}

@router.post("/validate-manifest")
def validate_manifest(payload: GraphInvestigationManifest): return {"ok":True,"fingerprint_sha256":payload.fingerprint()}

@router.post("/validate-bundle")
def validate_bundle(payload: ReproducibleGraphInvestigationPackageBundle): return {"ok":True,"fingerprint_sha256":payload.fingerprint()}
