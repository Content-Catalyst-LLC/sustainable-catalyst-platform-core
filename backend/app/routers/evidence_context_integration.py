from fastapi import APIRouter

from app.services.evidence_context_integration import (
    EvidenceContextAssessment,
    EvidenceContextIntegrationBundle,
    EvidenceContextLink,
    EvidenceGraphAnchor,
    contract_document,
    reference_evidence_context_integration_bundle,
)

router = APIRouter(prefix="/v1/evidence-context", tags=["evidence-context-integration"])
public_router = APIRouter(prefix="/public/v1/evidence-context", tags=["evidence-context-integration-public"])

@public_router.get("/contract")
def public_contract():
    return contract_document()

@router.get("/contract")
def contract():
    return contract_document()

@router.get("/reference")
def reference():
    bundle = reference_evidence_context_integration_bundle()
    return {"ok": True, "bundle_fingerprint_sha256": bundle.fingerprint(), "bundle": bundle.model_dump(mode="json")}

@router.get("/reference/anchors")
def reference_anchors():
    items = reference_evidence_context_integration_bundle().evidence_anchors
    return {"ok": True, "count": len(items), "items": [x.model_dump(mode="json") for x in items]}

@router.get("/reference/links")
def reference_links():
    items = reference_evidence_context_integration_bundle().links
    return {"ok": True, "count": len(items), "items": [x.model_dump(mode="json") for x in items]}

@router.get("/reference/assessments")
def reference_assessments():
    items = reference_evidence_context_integration_bundle().assessments
    return {"ok": True, "count": len(items), "items": [x.model_dump(mode="json") for x in items]}

@router.post("/validate-anchor")
def validate_anchor(payload: EvidenceGraphAnchor):
    return {"ok": True, "fingerprint_sha256": payload.fingerprint()}

@router.post("/validate-link")
def validate_link(payload: EvidenceContextLink):
    return {"ok": True, "fingerprint_sha256": payload.fingerprint()}

@router.post("/validate-assessment")
def validate_assessment(payload: EvidenceContextAssessment):
    return {"ok": True, "fingerprint_sha256": payload.fingerprint()}

@router.post("/validate-bundle")
def validate_bundle(payload: EvidenceContextIntegrationBundle):
    return {"ok": True, "fingerprint_sha256": payload.fingerprint()}
