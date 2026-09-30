from fastapi import APIRouter
from app.services.entity_centric_timeline_event_association import (
    CrossEventAssociation, EntityCentricTimelineEventAssociationBundle, EventRecord,
    contract_document, reference_entity_centric_timeline_event_association_bundle,
)
router=APIRouter(prefix="/v1/entity-timeline",tags=["entity-timeline"])
public_router=APIRouter(prefix="/public/v1/entity-timeline",tags=["entity-timeline-public"])
@router.get("/contract")
def private_contract(): return contract_document()
@public_router.get("/contract")
def public_contract(): return contract_document()
@router.get("/reference")
def reference(): return {"ok":True,"bundle":reference_entity_centric_timeline_event_association_bundle().model_dump(mode="json")}
@router.post("/validate-event")
def validate_event(payload: EventRecord): return {"ok":True,"fingerprint_sha256":payload.fingerprint()}
@router.post("/validate-association")
def validate_association(payload: CrossEventAssociation): return {"ok":True,"fingerprint_sha256":payload.fingerprint()}
@router.post("/validate-bundle")
def validate_bundle(payload: EntityCentricTimelineEventAssociationBundle): return {"ok":True,"fingerprint_sha256":payload.fingerprint()}
