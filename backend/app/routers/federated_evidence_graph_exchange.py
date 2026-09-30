from fastapi import APIRouter

from app.services.federated_evidence_graph_exchange import (
    FederatedEvidenceGraphExchangeBundle, FederatedObjectDescriptor, ExchangeManifest,
    contract_document, reference_federated_evidence_graph_exchange_bundle,
)

router=APIRouter(prefix="/v1/federated-evidence-graph-exchange",tags=["federated-evidence-graph-exchange"])
public_router=APIRouter(prefix="/public/v1/federated-evidence-graph-exchange",tags=["federated-evidence-graph-exchange-public"])

@router.get("/contract")
def private_contract(): return contract_document()

@public_router.get("/contract")
def public_contract(): return contract_document()

@router.get("/reference")
def reference(): return {"ok":True,"bundle":reference_federated_evidence_graph_exchange_bundle().model_dump(mode="json")}

@router.post("/validate-object-descriptor")
def validate_object_descriptor(payload: FederatedObjectDescriptor): return {"ok":True,"fingerprint_sha256":payload.fingerprint()}

@router.post("/validate-manifest")
def validate_manifest(payload: ExchangeManifest): return {"ok":True,"fingerprint_sha256":payload.fingerprint()}

@router.post("/validate-bundle")
def validate_bundle(payload: FederatedEvidenceGraphExchangeBundle): return {"ok":True,"fingerprint_sha256":payload.fingerprint()}
