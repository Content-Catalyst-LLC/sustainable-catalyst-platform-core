from fastapi import APIRouter

from app.services.investigation_session_research_context_runtime import (
    InvestigationSession,
    InvestigationSessionResearchContextBundle,
    contract_document,
    reference_investigation_session_research_context_bundle,
)

router = APIRouter(prefix="/v1/investigation-session", tags=["investigation-session"])
public_router = APIRouter(prefix="/public/v1/investigation-session", tags=["investigation-session-public"])

@router.get("/contract")
def private_contract(): return contract_document()

@public_router.get("/contract")
def public_contract(): return contract_document()

@router.get("/reference")
def reference(): return {"ok":True,"bundle":reference_investigation_session_research_context_bundle().model_dump(mode="json")}

@router.post("/validate-session")
def validate_session(payload: InvestigationSession): return {"ok":True,"fingerprint_sha256":payload.fingerprint()}

@router.post("/validate-bundle")
def validate_bundle(payload: InvestigationSessionResearchContextBundle): return {"ok":True,"fingerprint_sha256":payload.fingerprint()}
