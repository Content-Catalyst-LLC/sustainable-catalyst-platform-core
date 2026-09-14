from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from ..dependencies import get_session, require_read, require_write
from ..public_api_auth import PublicApiContext, require_public_scope
from ..schemas import PublicEnvelope
from ..services import open_forensics as svc

router = APIRouter(prefix="/v1/open-forensics", tags=["Open Forensics"])
public_router = APIRouter(prefix="/api/v1/open-forensics", tags=["Public Open Forensics"])

class Payload(BaseModel):
    data: dict[str, Any] = Field(default_factory=dict)

def bad(exc):
    return exc if isinstance(exc, HTTPException) else HTTPException(status_code=422, detail=str(exc))

def enabled(request: Request):
    if not request.app.state.settings.open_forensics_enabled:
        raise HTTPException(status_code=404, detail="Open Forensics is disabled.")

def public_enabled(request: Request):
    enabled(request)
    if not request.app.state.settings.open_forensics_public_metadata_enabled:
        raise HTTPException(status_code=404, detail="Public Open Forensics metadata is disabled.")

@router.get("/readiness", dependencies=[Depends(require_read)])
def readiness(request: Request, db: Session = Depends(get_session)):
    enabled(request); data=svc.readiness(db); data.update({"release":request.app.state.settings.version,"enabled":True}); return data

@router.post("/investigations", dependencies=[Depends(require_write)])
def create(request: Request, payload: Payload, db: Session = Depends(get_session)):
    enabled(request)
    try: return svc.create_investigation(db,payload.data)
    except Exception as exc: raise bad(exc)

@router.get("/investigations", dependencies=[Depends(require_read)])
def investigations(request: Request, project_entity_id: str | None=None, limit:int=Query(100,ge=1,le=1000), offset:int=Query(0,ge=0), db:Session=Depends(get_session)):
    enabled(request); items,total=svc.list_investigations(db,project_entity_id=project_entity_id,limit=limit,offset=offset); return {"items":items,"total":total,"limit":limit,"offset":offset}

@router.get("/investigations/{investigation_id}/bundle", dependencies=[Depends(require_read)])
def bundle(request:Request, investigation_id:str, db:Session=Depends(get_session)):
    enabled(request); return svc.bundle(db,investigation_id)

@router.get("/investigations/{investigation_id}/provenance-graph", dependencies=[Depends(require_read)])
def graph(request:Request, investigation_id:str, db:Session=Depends(get_session)):
    enabled(request); return svc.provenance_graph(db,investigation_id)

@router.get("/investigations/{investigation_id}/portable-package", dependencies=[Depends(require_read)])
def portable(request:Request, investigation_id:str, db:Session=Depends(get_session)):
    enabled(request); return svc.portable_package(db,investigation_id)

@router.post("/investigations/{investigation_id}/objects", dependencies=[Depends(require_write)])
def add_object(request:Request, investigation_id:str, payload:Payload, db:Session=Depends(get_session)):
    enabled(request)
    try: return svc.add_object(db,investigation_id,payload.data)
    except Exception as exc: raise bad(exc)

@router.post("/investigations/{investigation_id}/evidence", dependencies=[Depends(require_write)])
def add_evidence(request:Request, investigation_id:str, payload:Payload, db:Session=Depends(get_session)):
    enabled(request)
    try: return svc.add_evidence(db,investigation_id,payload.data)
    except Exception as exc: raise bad(exc)

@router.post("/investigations/{investigation_id}/evidence/{evidence_id}/source-bindings", dependencies=[Depends(require_write)])
def add_binding(request:Request, investigation_id:str, evidence_id:str, payload:Payload, db:Session=Depends(get_session)):
    enabled(request)
    try: return svc.add_source_binding(db,investigation_id,evidence_id,payload.data)
    except Exception as exc: raise bad(exc)

@router.post("/investigations/{investigation_id}/provenance-activities", dependencies=[Depends(require_write)])
def add_activity(request:Request, investigation_id:str, payload:Payload, db:Session=Depends(get_session)):
    enabled(request)
    try: return svc.add_provenance_activity(db,investigation_id,payload.data)
    except Exception as exc: raise bad(exc)

@router.post("/investigations/{investigation_id}/relations", dependencies=[Depends(require_write)])
def add_relation(request:Request, investigation_id:str, payload:Payload, db:Session=Depends(get_session)):
    enabled(request)
    try: return svc.add_relation(db,investigation_id,payload.data)
    except Exception as exc: raise bad(exc)

@router.post("/investigations/{investigation_id}/snapshots", dependencies=[Depends(require_write)])
def snapshot(request:Request, investigation_id:str, payload:Payload, db:Session=Depends(get_session)):
    enabled(request)
    try: return svc.create_snapshot(db,investigation_id,payload.data)
    except Exception as exc: raise bad(exc)



@router.post("/investigations/{investigation_id}/custodians", dependencies=[Depends(require_write)])
def add_custodian(request:Request, investigation_id:str, payload:Payload, db:Session=Depends(get_session)):
    enabled(request)
    try: return svc.add_custodian(db,investigation_id,payload.data)
    except Exception as exc: raise bad(exc)

@router.post("/investigations/{investigation_id}/evidence/{evidence_id}/custody-events", dependencies=[Depends(require_write)])
def custody_event(request:Request, investigation_id:str, evidence_id:str, payload:Payload, db:Session=Depends(get_session)):
    enabled(request)
    try: return svc.record_custody_event(db,investigation_id,evidence_id,payload.data)
    except Exception as exc: raise bad(exc)

@router.get("/investigations/{investigation_id}/evidence/{evidence_id}/custody-chain", dependencies=[Depends(require_read)])
def custody_chain(request:Request, investigation_id:str, evidence_id:str, db:Session=Depends(get_session)):
    enabled(request)
    try: return svc.custody_chain(db,investigation_id,evidence_id)
    except Exception as exc: raise bad(exc)

@router.post("/investigations/{investigation_id}/evidence/{evidence_id}/seals", dependencies=[Depends(require_write)])
def seal(request:Request, investigation_id:str, evidence_id:str, payload:Payload, db:Session=Depends(get_session)):
    enabled(request)
    try: return svc.record_seal(db,investigation_id,evidence_id,payload.data)
    except Exception as exc: raise bad(exc)

@router.post("/investigations/{investigation_id}/evidence/{evidence_id}/integrity-checks", dependencies=[Depends(require_write)])
def integrity_check(request:Request, investigation_id:str, evidence_id:str, payload:Payload, db:Session=Depends(get_session)):
    enabled(request)
    try: return svc.record_integrity_check(db,investigation_id,evidence_id,payload.data)
    except Exception as exc: raise bad(exc)

@router.post("/investigations/{investigation_id}/evidence/{evidence_id}/continuity-assessments", dependencies=[Depends(require_write)])
def continuity_assessment(request:Request, investigation_id:str, evidence_id:str, payload:Payload, db:Session=Depends(get_session)):
    enabled(request)
    try: return svc.create_continuity_assessment(db,investigation_id,evidence_id,payload.data)
    except Exception as exc: raise bad(exc)

@router.get("/investigations/{investigation_id}/custody-bundle", dependencies=[Depends(require_read)])
def custody_bundle(request:Request, investigation_id:str, db:Session=Depends(get_session)):
    enabled(request); return svc.custody_bundle(db,investigation_id)

@router.post("/investigations/{investigation_id}/custody-snapshots", dependencies=[Depends(require_write)])
def custody_snapshot(request:Request, investigation_id:str, payload:Payload, db:Session=Depends(get_session)):
    enabled(request)
    try: return svc.create_custody_snapshot(db,investigation_id,payload.data)
    except Exception as exc: raise bad(exc)



# v2.44.0 — Claims, Contradictions & Competing Hypotheses
@router.post("/investigations/{investigation_id}/claims", dependencies=[Depends(require_write)])
def add_claim(request:Request, investigation_id:str, payload:Payload, db:Session=Depends(get_session)):
    enabled(request)
    try: return svc.add_claim(db,investigation_id,payload.data)
    except Exception as exc: raise bad(exc)

@router.post("/investigations/{investigation_id}/claims/{claim_id}/evidence-assessments", dependencies=[Depends(require_write)])
def assess_claim_evidence(request:Request, investigation_id:str, claim_id:str, payload:Payload, db:Session=Depends(get_session)):
    enabled(request)
    try: return svc.assess_claim_evidence(db,investigation_id,claim_id,payload.data)
    except Exception as exc: raise bad(exc)

@router.post("/investigations/{investigation_id}/contradictions", dependencies=[Depends(require_write)])
def add_contradiction(request:Request, investigation_id:str, payload:Payload, db:Session=Depends(get_session)):
    enabled(request)
    try: return svc.add_contradiction(db,investigation_id,payload.data)
    except Exception as exc: raise bad(exc)

@router.post("/investigations/{investigation_id}/hypotheses", dependencies=[Depends(require_write)])
def add_hypothesis(request:Request, investigation_id:str, payload:Payload, db:Session=Depends(get_session)):
    enabled(request)
    try: return svc.add_hypothesis(db,investigation_id,payload.data)
    except Exception as exc: raise bad(exc)

@router.post("/investigations/{investigation_id}/hypotheses/{hypothesis_id}/evidence-assessments", dependencies=[Depends(require_write)])
def assess_hypothesis_evidence(request:Request, investigation_id:str, hypothesis_id:str, payload:Payload, db:Session=Depends(get_session)):
    enabled(request)
    try: return svc.assess_hypothesis_evidence(db,investigation_id,hypothesis_id,payload.data)
    except Exception as exc: raise bad(exc)

@router.post("/investigations/{investigation_id}/hypothesis-relations", dependencies=[Depends(require_write)])
def add_hypothesis_relation(request:Request, investigation_id:str, payload:Payload, db:Session=Depends(get_session)):
    enabled(request)
    try: return svc.add_hypothesis_relation(db,investigation_id,payload.data)
    except Exception as exc: raise bad(exc)

@router.get("/investigations/{investigation_id}/claim-map", dependencies=[Depends(require_read)])
def claim_map(request:Request, investigation_id:str, db:Session=Depends(get_session)):
    enabled(request); return svc.claim_map(db,investigation_id)

@router.get("/investigations/{investigation_id}/hypothesis-matrix", dependencies=[Depends(require_read)])
def hypothesis_matrix(request:Request, investigation_id:str, db:Session=Depends(get_session)):
    enabled(request); return svc.hypothesis_matrix(db,investigation_id)

@router.get("/investigations/{investigation_id}/reasoning-bundle", dependencies=[Depends(require_read)])
def reasoning_bundle(request:Request, investigation_id:str, db:Session=Depends(get_session)):
    enabled(request); return svc.reasoning_bundle(db,investigation_id)

@router.post("/investigations/{investigation_id}/reasoning-snapshots", dependencies=[Depends(require_write)])
def reasoning_snapshot(request:Request, investigation_id:str, payload:Payload, db:Session=Depends(get_session)):
    enabled(request)
    try: return svc.create_reasoning_snapshot(db,investigation_id,payload.data)
    except Exception as exc: raise bad(exc)



# v2.45.0 — Forensic Timeline & Event Reconstruction
@router.post("/investigations/{investigation_id}/events", dependencies=[Depends(require_write)])
def add_event(request:Request, investigation_id:str, payload:Payload, db:Session=Depends(get_session)):
    enabled(request)
    try: return svc.add_event(db,investigation_id,payload.data)
    except Exception as exc: raise bad(exc)

@router.post("/investigations/{investigation_id}/events/{event_id}/evidence-bindings", dependencies=[Depends(require_write)])
def bind_event_evidence(request:Request, investigation_id:str, event_id:str, payload:Payload, db:Session=Depends(get_session)):
    enabled(request)
    try: return svc.bind_event_evidence(db,investigation_id,event_id,payload.data)
    except Exception as exc: raise bad(exc)

@router.post("/investigations/{investigation_id}/events/{event_id}/participants", dependencies=[Depends(require_write)])
def add_event_participant(request:Request, investigation_id:str, event_id:str, payload:Payload, db:Session=Depends(get_session)):
    enabled(request)
    try: return svc.add_event_participant(db,investigation_id,event_id,payload.data)
    except Exception as exc: raise bad(exc)

@router.post("/investigations/{investigation_id}/event-relations", dependencies=[Depends(require_write)])
def add_event_relation(request:Request, investigation_id:str, payload:Payload, db:Session=Depends(get_session)):
    enabled(request)
    try: return svc.add_event_relation(db,investigation_id,payload.data)
    except Exception as exc: raise bad(exc)

@router.post("/investigations/{investigation_id}/event-reconstructions", dependencies=[Depends(require_write)])
def add_event_reconstruction(request:Request, investigation_id:str, payload:Payload, db:Session=Depends(get_session)):
    enabled(request)
    try: return svc.add_event_reconstruction(db,investigation_id,payload.data)
    except Exception as exc: raise bad(exc)

@router.post("/investigations/{investigation_id}/timeline-views", dependencies=[Depends(require_write)])
def add_timeline_view(request:Request, investigation_id:str, payload:Payload, db:Session=Depends(get_session)):
    enabled(request)
    try: return svc.add_timeline_view(db,investigation_id,payload.data)
    except Exception as exc: raise bad(exc)

@router.get("/investigations/{investigation_id}/timeline", dependencies=[Depends(require_read)])
def timeline(request:Request, investigation_id:str, db:Session=Depends(get_session)):
    enabled(request); return svc.timeline_bundle(db,investigation_id)

@router.get("/investigations/{investigation_id}/timeline-specification", dependencies=[Depends(require_read)])
def timeline_specification(request:Request, investigation_id:str, db:Session=Depends(get_session)):
    enabled(request); return svc.timeline_specification(db,investigation_id)

@router.post("/investigations/{investigation_id}/timeline-snapshots", dependencies=[Depends(require_write)])
def timeline_snapshot(request:Request, investigation_id:str, payload:Payload, db:Session=Depends(get_session)):
    enabled(request)
    try: return svc.create_timeline_snapshot(db,investigation_id,payload.data)
    except Exception as exc: raise bad(exc)



# v2.46.0 — Forensic Spatial/Temporal Evidence Integration
@router.post("/investigations/{investigation_id}/places", dependencies=[Depends(require_write)])
def add_place(request:Request, investigation_id:str, payload:Payload, db:Session=Depends(get_session)):
    enabled(request)
    try: return svc.add_place(db,investigation_id,payload.data)
    except Exception as exc: raise bad(exc)

@router.post("/investigations/{investigation_id}/evidence/{evidence_id}/spatial-bindings", dependencies=[Depends(require_write)])
def bind_evidence_spatial(request:Request, investigation_id:str, evidence_id:str, payload:Payload, db:Session=Depends(get_session)):
    enabled(request)
    try: return svc.bind_evidence_spatial(db,investigation_id,evidence_id,payload.data)
    except Exception as exc: raise bad(exc)

@router.post("/investigations/{investigation_id}/events/{event_id}/place-bindings", dependencies=[Depends(require_write)])
def bind_event_place(request:Request, investigation_id:str, event_id:str, payload:Payload, db:Session=Depends(get_session)):
    enabled(request)
    try: return svc.bind_event_place(db,investigation_id,event_id,payload.data)
    except Exception as exc: raise bad(exc)

@router.post("/investigations/{investigation_id}/spatial-uncertainty-envelopes", dependencies=[Depends(require_write)])
def add_spatial_uncertainty(request:Request, investigation_id:str, payload:Payload, db:Session=Depends(get_session)):
    enabled(request)
    try: return svc.add_spatial_uncertainty_envelope(db,investigation_id,payload.data)
    except Exception as exc: raise bad(exc)

@router.post("/investigations/{investigation_id}/trajectory-evidence", dependencies=[Depends(require_write)])
def add_trajectory_evidence(request:Request, investigation_id:str, payload:Payload, db:Session=Depends(get_session)):
    enabled(request)
    try: return svc.add_trajectory_evidence(db,investigation_id,payload.data)
    except Exception as exc: raise bad(exc)

@router.post("/investigations/{investigation_id}/spatial-temporal-intersections", dependencies=[Depends(require_write)])
def add_spatial_temporal_intersection(request:Request, investigation_id:str, payload:Payload, db:Session=Depends(get_session)):
    enabled(request)
    try: return svc.add_spatial_temporal_intersection(db,investigation_id,payload.data)
    except Exception as exc: raise bad(exc)

@router.post("/investigations/{investigation_id}/spatial-temporal-views", dependencies=[Depends(require_write)])
def add_spatial_temporal_view(request:Request, investigation_id:str, payload:Payload, db:Session=Depends(get_session)):
    enabled(request)
    try: return svc.add_spatial_temporal_view(db,investigation_id,payload.data)
    except Exception as exc: raise bad(exc)

@router.get("/investigations/{investigation_id}/spatial-temporal-evidence", dependencies=[Depends(require_read)])
def spatial_temporal_evidence(request:Request, investigation_id:str, db:Session=Depends(get_session)):
    enabled(request); return svc.spatial_temporal_evidence_bundle(db,investigation_id)

@router.get("/investigations/{investigation_id}/forensic-scene-specification", dependencies=[Depends(require_read)])
def forensic_scene_specification(request:Request, investigation_id:str, db:Session=Depends(get_session)):
    enabled(request); return svc.forensic_scene_specification(db,investigation_id)

@router.get("/investigations/{investigation_id}/site-intelligence-handoff", dependencies=[Depends(require_read)])
def site_intelligence_handoff(request:Request, investigation_id:str, db:Session=Depends(get_session)):
    enabled(request); return svc.site_intelligence_handoff(db,investigation_id)

@router.post("/investigations/{investigation_id}/spatial-temporal-snapshots", dependencies=[Depends(require_write)])
def spatial_temporal_snapshot(request:Request, investigation_id:str, payload:Payload, db:Session=Depends(get_session)):
    enabled(request)
    try: return svc.create_spatial_temporal_snapshot(db,investigation_id,payload.data)
    except Exception as exc: raise bad(exc)


# v2.47.0 — Media Artifact & Derivative Provenance
@router.post("/investigations/{investigation_id}/media-artifacts", dependencies=[Depends(require_write)])
def add_media_artifact(request:Request, investigation_id:str, payload:Payload, db:Session=Depends(get_session)):
    enabled(request)
    try: return svc.add_media_artifact(db,investigation_id,payload.data)
    except Exception as exc: raise bad(exc)

@router.post("/investigations/{investigation_id}/media-derivations", dependencies=[Depends(require_write)])
def add_media_derivation(request:Request, investigation_id:str, payload:Payload, db:Session=Depends(get_session)):
    enabled(request)
    try: return svc.add_media_derivation(db,investigation_id,payload.data)
    except Exception as exc: raise bad(exc)

@router.post("/investigations/{investigation_id}/media-artifacts/{artifact_id}/metadata", dependencies=[Depends(require_write)])
def add_media_metadata(request:Request, investigation_id:str, artifact_id:str, payload:Payload, db:Session=Depends(get_session)):
    enabled(request)
    try: return svc.add_media_metadata(db,investigation_id,artifact_id,payload.data)
    except Exception as exc: raise bad(exc)

@router.post("/investigations/{investigation_id}/media-artifacts/{artifact_id}/fingerprints", dependencies=[Depends(require_write)])
def add_media_fingerprint(request:Request, investigation_id:str, artifact_id:str, payload:Payload, db:Session=Depends(get_session)):
    enabled(request)
    try: return svc.add_media_fingerprint(db,investigation_id,artifact_id,payload.data)
    except Exception as exc: raise bad(exc)

@router.post("/investigations/{investigation_id}/media-artifacts/{artifact_id}/segments", dependencies=[Depends(require_write)])
def add_media_segment(request:Request, investigation_id:str, artifact_id:str, payload:Payload, db:Session=Depends(get_session)):
    enabled(request)
    try: return svc.add_media_segment(db,investigation_id,artifact_id,payload.data)
    except Exception as exc: raise bad(exc)

@router.post("/investigations/{investigation_id}/media-comparisons", dependencies=[Depends(require_write)])
def add_media_comparison(request:Request, investigation_id:str, payload:Payload, db:Session=Depends(get_session)):
    enabled(request)
    try: return svc.add_media_comparison(db,investigation_id,payload.data)
    except Exception as exc: raise bad(exc)

@router.get("/investigations/{investigation_id}/media-provenance", dependencies=[Depends(require_read)])
def media_provenance(request:Request, investigation_id:str, db:Session=Depends(get_session)):
    enabled(request)
    try: return svc.media_provenance_bundle(db,investigation_id)
    except Exception as exc: raise bad(exc)

@router.get("/investigations/{investigation_id}/media-lineage-graph", dependencies=[Depends(require_read)])
def media_lineage_graph(request:Request, investigation_id:str, db:Session=Depends(get_session)):
    enabled(request)
    try: return svc.media_lineage_graph(db,investigation_id)
    except Exception as exc: raise bad(exc)

@router.get("/investigations/{investigation_id}/media-comparison-bundle", dependencies=[Depends(require_read)])
def media_comparison_bundle(request:Request, investigation_id:str, db:Session=Depends(get_session)):
    enabled(request)
    try: return svc.media_comparison_bundle(db,investigation_id)
    except Exception as exc: raise bad(exc)

@router.post("/investigations/{investigation_id}/media-provenance-snapshots", dependencies=[Depends(require_write)])
def media_provenance_snapshot(request:Request, investigation_id:str, payload:Payload, db:Session=Depends(get_session)):
    enabled(request)
    try: return svc.create_media_provenance_snapshot(db,investigation_id,payload.data)
    except Exception as exc: raise bad(exc)


# v2.48.0 — Quantitative Reconstruction & Reproduction Handoffs
@router.post("/investigations/{investigation_id}/quantitative-reconstructions", dependencies=[Depends(require_write)])
def add_quantitative_reconstruction(request:Request, investigation_id:str, payload:Payload, db:Session=Depends(get_session)):
    enabled(request)
    try: return svc.add_quantitative_reconstruction(db,investigation_id,payload.data)
    except Exception as exc: raise bad(exc)

@router.post("/investigations/{investigation_id}/quantitative-reconstructions/{reconstruction_id}/measurements", dependencies=[Depends(require_write)])
def add_quantitative_measurement(request:Request, investigation_id:str, reconstruction_id:str, payload:Payload, db:Session=Depends(get_session)):
    enabled(request)
    try: return svc.add_quantitative_measurement(db,investigation_id,reconstruction_id,payload.data)
    except Exception as exc: raise bad(exc)

@router.post("/investigations/{investigation_id}/quantitative-reconstructions/{reconstruction_id}/assumptions", dependencies=[Depends(require_write)])
def add_quantitative_assumption(request:Request, investigation_id:str, reconstruction_id:str, payload:Payload, db:Session=Depends(get_session)):
    enabled(request)
    try: return svc.add_quantitative_assumption(db,investigation_id,reconstruction_id,payload.data)
    except Exception as exc: raise bad(exc)

@router.post("/investigations/{investigation_id}/quantitative-reconstructions/{reconstruction_id}/parameters", dependencies=[Depends(require_write)])
def add_quantitative_parameter(request:Request, investigation_id:str, reconstruction_id:str, payload:Payload, db:Session=Depends(get_session)):
    enabled(request)
    try: return svc.add_quantitative_parameter(db,investigation_id,reconstruction_id,payload.data)
    except Exception as exc: raise bad(exc)

@router.post("/investigations/{investigation_id}/quantitative-reconstructions/{reconstruction_id}/scenarios", dependencies=[Depends(require_write)])
def add_quantitative_scenario(request:Request, investigation_id:str, reconstruction_id:str, payload:Payload, db:Session=Depends(get_session)):
    enabled(request)
    try: return svc.add_quantitative_scenario(db,investigation_id,reconstruction_id,payload.data)
    except Exception as exc: raise bad(exc)

@router.get("/investigations/{investigation_id}/quantitative-reconstructions", dependencies=[Depends(require_read)])
def quantitative_reconstructions(request:Request, investigation_id:str, db:Session=Depends(get_session)):
    enabled(request); return svc.quantitative_reconstruction_bundle(db,investigation_id)

@router.post("/investigations/{investigation_id}/quantitative-reconstructions/{reconstruction_id}/handoffs", dependencies=[Depends(require_write)])
def quantitative_handoff(request:Request, investigation_id:str, reconstruction_id:str, payload:Payload, db:Session=Depends(get_session)):
    enabled(request)
    try: return svc.create_quantitative_handoff(db,investigation_id,reconstruction_id,payload.data)
    except Exception as exc: raise bad(exc)

@router.get("/investigations/{investigation_id}/quantitative-reconstructions/{reconstruction_id}/handoff/{target_product}", dependencies=[Depends(require_read)])
def quantitative_handoff_contract(request:Request, investigation_id:str, reconstruction_id:str, target_product:str, db:Session=Depends(get_session)):
    enabled(request)
    try: return svc.quantitative_handoff_contract(db,investigation_id,reconstruction_id,target_product)
    except Exception as exc: raise bad(exc)

@router.post("/investigations/{investigation_id}/quantitative-handoffs/{handoff_id}/results", dependencies=[Depends(require_write)])
def quantitative_result_binding(request:Request, investigation_id:str, handoff_id:str, payload:Payload, db:Session=Depends(get_session)):
    enabled(request)
    try: return svc.add_quantitative_result_binding(db,investigation_id,handoff_id,payload.data)
    except Exception as exc: raise bad(exc)

@router.post("/investigations/{investigation_id}/quantitative-reconstructions/{reconstruction_id}/reproduction-packages", dependencies=[Depends(require_write)])
def quantitative_reproduction_package(request:Request, investigation_id:str, reconstruction_id:str, payload:Payload, db:Session=Depends(get_session)):
    enabled(request)
    try: return svc.create_quantitative_reproduction_package(db,investigation_id,reconstruction_id,payload.data)
    except Exception as exc: raise bad(exc)



# v2.49.0 — Testimony, Statements & Documentary Evidence
@router.post("/investigations/{investigation_id}/statements", dependencies=[Depends(require_write)])
def add_statement(request:Request, investigation_id:str, payload:Payload, db:Session=Depends(get_session)):
    enabled(request)
    try: return svc.add_statement(db,investigation_id,payload.data)
    except Exception as exc: raise bad(exc)

@router.post("/investigations/{investigation_id}/statements/{statement_id}/source-contexts", dependencies=[Depends(require_write)])
def add_statement_source_context(request:Request, investigation_id:str, statement_id:str, payload:Payload, db:Session=Depends(get_session)):
    enabled(request)
    try: return svc.add_statement_source_context(db,investigation_id,statement_id,payload.data)
    except Exception as exc: raise bad(exc)

@router.post("/investigations/{investigation_id}/documents", dependencies=[Depends(require_write)])
def add_document(request:Request, investigation_id:str, payload:Payload, db:Session=Depends(get_session)):
    enabled(request)
    try: return svc.add_document(db,investigation_id,payload.data)
    except Exception as exc: raise bad(exc)

@router.post("/investigations/{investigation_id}/documents/{document_id}/assertions", dependencies=[Depends(require_write)])
def add_document_assertion(request:Request, investigation_id:str, document_id:str, payload:Payload, db:Session=Depends(get_session)):
    enabled(request)
    try: return svc.add_document_assertion(db,investigation_id,document_id,payload.data)
    except Exception as exc: raise bad(exc)

@router.post("/investigations/{investigation_id}/statements/{statement_id}/claim-bindings", dependencies=[Depends(require_write)])
def bind_statement_claim(request:Request, investigation_id:str, statement_id:str, payload:Payload, db:Session=Depends(get_session)):
    enabled(request)
    try: return svc.bind_statement_claim(db,investigation_id,statement_id,payload.data)
    except Exception as exc: raise bad(exc)

@router.post("/investigations/{investigation_id}/statement-relations", dependencies=[Depends(require_write)])
def add_statement_relation(request:Request, investigation_id:str, payload:Payload, db:Session=Depends(get_session)):
    enabled(request)
    try: return svc.add_statement_relation(db,investigation_id,payload.data)
    except Exception as exc: raise bad(exc)

@router.post("/investigations/{investigation_id}/temporal-consistency", dependencies=[Depends(require_write)])
def add_temporal_consistency(request:Request, investigation_id:str, payload:Payload, db:Session=Depends(get_session)):
    enabled(request)
    try: return svc.add_temporal_consistency_assessment(db,investigation_id,payload.data)
    except Exception as exc: raise bad(exc)

@router.get("/investigations/{investigation_id}/documentary-evidence", dependencies=[Depends(require_read)])
def documentary_evidence(request:Request, investigation_id:str, db:Session=Depends(get_session)):
    enabled(request); return svc.documentary_evidence_bundle(db,investigation_id)

@router.post("/investigations/{investigation_id}/documentary-snapshots", dependencies=[Depends(require_write)])
def documentary_snapshot(request:Request, investigation_id:str, payload:Payload, db:Session=Depends(get_session)):
    enabled(request)
    try: return svc.create_documentary_snapshot(db,investigation_id,payload.data)
    except Exception as exc: raise bad(exc)



# v2.50.0 — Forensic Research Graph
@router.post("/investigations/{investigation_id}/research-graphs", dependencies=[Depends(require_write)])
def create_research_graph(request:Request, investigation_id:str, payload:Payload, db:Session=Depends(get_session)):
    enabled(request)
    try: return svc.create_research_graph(db,investigation_id,payload.data)
    except Exception as exc: raise bad(exc)

@router.get("/investigations/{investigation_id}/research-graph-inventory", dependencies=[Depends(require_read)])
def research_graph_inventory(request:Request, investigation_id:str, db:Session=Depends(get_session)):
    enabled(request); return svc.research_graph_source_inventory(db,investigation_id)

@router.post("/investigations/{investigation_id}/research-graphs/{graph_id}/nodes", dependencies=[Depends(require_write)])
def add_research_graph_node(request:Request, investigation_id:str, graph_id:str, payload:Payload, db:Session=Depends(get_session)):
    enabled(request)
    try: return svc.add_research_graph_node(db,investigation_id,graph_id,payload.data)
    except Exception as exc: raise bad(exc)

@router.post("/investigations/{investigation_id}/research-graphs/{graph_id}/edges", dependencies=[Depends(require_write)])
def add_research_graph_edge(request:Request, investigation_id:str, graph_id:str, payload:Payload, db:Session=Depends(get_session)):
    enabled(request)
    try: return svc.add_research_graph_edge(db,investigation_id,graph_id,payload.data)
    except Exception as exc: raise bad(exc)

@router.post("/investigations/{investigation_id}/research-graphs/{graph_id}/views", dependencies=[Depends(require_write)])
def add_research_graph_view(request:Request, investigation_id:str, graph_id:str, payload:Payload, db:Session=Depends(get_session)):
    enabled(request)
    try: return svc.add_research_graph_view(db,investigation_id,graph_id,payload.data)
    except Exception as exc: raise bad(exc)

@router.get("/investigations/{investigation_id}/research-graphs/{graph_id}", dependencies=[Depends(require_read)])
def research_graph_bundle(request:Request, investigation_id:str, graph_id:str, db:Session=Depends(get_session)):
    enabled(request); return svc.forensic_research_graph_bundle(db,investigation_id,graph_id)

@router.get("/investigations/{investigation_id}/research-graphs/{graph_id}/visual-spec", dependencies=[Depends(require_read)])
def research_graph_visual_spec(request:Request, investigation_id:str, graph_id:str, db:Session=Depends(get_session)):
    enabled(request); return svc.forensic_research_graph_visual_spec(db,investigation_id,graph_id)

@router.post("/investigations/{investigation_id}/research-graphs/{graph_id}/handoffs", dependencies=[Depends(require_write)])
def research_graph_handoff(request:Request, investigation_id:str, graph_id:str, payload:Payload, db:Session=Depends(get_session)):
    enabled(request)
    try: return svc.create_research_graph_handoff(db,investigation_id,graph_id,payload.data)
    except Exception as exc: raise bad(exc)

@router.post("/investigations/{investigation_id}/research-graphs/{graph_id}/snapshots", dependencies=[Depends(require_write)])
def research_graph_snapshot(request:Request, investigation_id:str, graph_id:str, payload:Payload, db:Session=Depends(get_session)):
    enabled(request)
    try: return svc.create_research_graph_snapshot(db,investigation_id,graph_id,payload.data)
    except Exception as exc: raise bad(exc)

@router.post("/investigations/{investigation_id}/research-graphs/{graph_id}/packages", dependencies=[Depends(require_write)])
def research_graph_package(request:Request, investigation_id:str, graph_id:str, payload:Payload, db:Session=Depends(get_session)):
    enabled(request)
    try: return svc.create_research_graph_package(db,investigation_id,graph_id,payload.data)
    except Exception as exc: raise bad(exc)




# v2.51.0 — Reproducible Investigation Packages
@router.post("/investigations/{investigation_id}/reproducible-packages", dependencies=[Depends(require_write)])
def create_reproducible_package(request:Request, investigation_id:str, payload:Payload, db:Session=Depends(get_session)):
    enabled(request)
    try: return svc.create_reproducible_investigation_package(db,investigation_id,payload.data)
    except Exception as exc: raise bad(exc)

@router.get("/investigations/{investigation_id}/reproducible-packages", dependencies=[Depends(require_read)])
def list_reproducible_packages(request:Request, investigation_id:str, db:Session=Depends(get_session)):
    enabled(request); return svc.list_reproducible_investigation_packages(db,investigation_id)

@router.get("/investigations/{investigation_id}/reproducible-packages/{package_id}", dependencies=[Depends(require_read)])
def reproducible_package(request:Request, investigation_id:str, package_id:str, db:Session=Depends(get_session)):
    enabled(request); return svc.reproducible_investigation_package_bundle(db,investigation_id,package_id)

@router.get("/investigations/{investigation_id}/reproducible-packages/{package_id}/portable", dependencies=[Depends(require_read)])
def portable_reproducible_package(request:Request, investigation_id:str, package_id:str, db:Session=Depends(get_session)):
    enabled(request); return svc.portable_reproducible_investigation_package(db,investigation_id,package_id)

@router.post("/investigations/{investigation_id}/reproducible-packages/{package_id}/artifacts", dependencies=[Depends(require_write)])
def reproducible_package_artifact(request:Request, investigation_id:str, package_id:str, payload:Payload, db:Session=Depends(get_session)):
    enabled(request)
    try: return svc.add_investigation_package_artifact(db,investigation_id,package_id,payload.data)
    except Exception as exc: raise bad(exc)

@router.post("/investigations/{investigation_id}/reproducible-packages/{package_id}/environments", dependencies=[Depends(require_write)])
def reproducible_package_environment(request:Request, investigation_id:str, package_id:str, payload:Payload, db:Session=Depends(get_session)):
    enabled(request)
    try: return svc.add_investigation_package_environment(db,investigation_id,package_id,payload.data)
    except Exception as exc: raise bad(exc)

@router.post("/investigations/{investigation_id}/reproducible-packages/{package_id}/verify", dependencies=[Depends(require_write)])
def verify_reproducible_package(request:Request, investigation_id:str, package_id:str, payload:Payload, db:Session=Depends(get_session)):
    enabled(request)
    try: return svc.verify_reproducible_investigation_package(db,investigation_id,package_id,payload.data)
    except Exception as exc: raise bad(exc)

@router.post("/investigations/{investigation_id}/reproducible-packages/{package_id}/reviews", dependencies=[Depends(require_write)])
def review_reproducible_package(request:Request, investigation_id:str, package_id:str, payload:Payload, db:Session=Depends(get_session)):
    enabled(request)
    try: return svc.add_investigation_package_review(db,investigation_id,package_id,payload.data)
    except Exception as exc: raise bad(exc)

@router.post("/investigations/{investigation_id}/reproducible-packages/{package_id}/snapshots", dependencies=[Depends(require_write)])
def snapshot_reproducible_package(request:Request, investigation_id:str, package_id:str, payload:Payload, db:Session=Depends(get_session)):
    enabled(request)
    try: return svc.create_investigation_package_snapshot(db,investigation_id,package_id,payload.data)
    except Exception as exc: raise bad(exc)

@public_router.get("/readiness", response_model=PublicEnvelope)
def public_readiness(request:Request, db:Session=Depends(get_session), _ctx:PublicApiContext=Depends(require_public_scope("data:read"))):
    public_enabled(request); data=svc.readiness(db); data.update({"release":request.app.state.settings.version,"enabled":True}); return PublicEnvelope(data=data,meta={"api_version":"v1","request_id":request.state.request_id})

@public_router.get("/investigations", response_model=PublicEnvelope)
def public_investigations(request:Request, project_entity_id:str|None=None, limit:int=Query(100,ge=1), offset:int=Query(0,ge=0), ctx:PublicApiContext=Depends(require_public_scope("data:read")), db:Session=Depends(get_session)):
    public_enabled(request); limit=min(limit,ctx.plan.max_page_size,request.app.state.settings.page_size_max); items,total=svc.list_investigations(db,project_entity_id=project_entity_id,public_only=True,limit=limit,offset=offset); return PublicEnvelope(data=items,meta={"api_version":"v1","request_id":request.state.request_id,"pagination":{"total":total,"limit":limit,"offset":offset}})

@public_router.get("/investigations/{investigation_id}/bundle", response_model=PublicEnvelope)
def public_bundle(investigation_id:str, request:Request, db:Session=Depends(get_session), _ctx:PublicApiContext=Depends(require_public_scope("data:read"))):
    public_enabled(request); return PublicEnvelope(data=svc.bundle(db,investigation_id,public_only=True),meta={"api_version":"v1","request_id":request.state.request_id})


@public_router.get("/investigations/{investigation_id}/timeline", response_model=PublicEnvelope)
def public_timeline(investigation_id:str, request:Request, db:Session=Depends(get_session), _ctx:PublicApiContext=Depends(require_public_scope("data:read"))):
    public_enabled(request); inv=svc._investigation(db,investigation_id)
    if inv.visibility != "public": raise HTTPException(status_code=404,detail="Forensic investigation not found.")
    return PublicEnvelope(data=svc.timeline_bundle(db,investigation_id),meta={"api_version":"v1","request_id":request.state.request_id})


@public_router.get("/investigations/{investigation_id}/spatial-temporal-evidence", response_model=PublicEnvelope)
def public_spatial_temporal_evidence(investigation_id:str, request:Request, db:Session=Depends(get_session), _ctx:PublicApiContext=Depends(require_public_scope("data:read"))):
    public_enabled(request); inv=svc._investigation(db,investigation_id)
    if inv.visibility != "public": raise HTTPException(status_code=404,detail="Forensic investigation not found.")
    return PublicEnvelope(data=svc.spatial_temporal_evidence_bundle(db,investigation_id),meta={"api_version":"v1","request_id":request.state.request_id})

@public_router.get("/investigations/{investigation_id}/media-provenance", response_model=PublicEnvelope)
def public_media_provenance(investigation_id:str, request:Request, db:Session=Depends(get_session), _ctx:PublicApiContext=Depends(require_public_scope("data:read"))):
    public_enabled(request); inv=svc._investigation(db,investigation_id)
    if inv.visibility != "public": raise HTTPException(status_code=404,detail="Forensic investigation not found.")
    return PublicEnvelope(data=svc.media_provenance_bundle(db,investigation_id),meta={"api_version":"v1","request_id":request.state.request_id})

@public_router.get("/investigations/{investigation_id}/media-provenance", response_model=PublicEnvelope)
def public_media_provenance(investigation_id:str, request:Request, db:Session=Depends(get_session), _ctx:PublicApiContext=Depends(require_public_scope("data:read"))):
    public_enabled(request); inv=svc._investigation(db,investigation_id)
    if inv.visibility != "public": raise HTTPException(status_code=404,detail="Forensic investigation not found.")
    return PublicEnvelope(data=svc.media_provenance_bundle(db,investigation_id),meta={"api_version":"v1","request_id":request.state.request_id})

@public_router.get("/investigations/{investigation_id}/media-lineage-graph", response_model=PublicEnvelope)
def public_media_lineage_graph(investigation_id:str, request:Request, db:Session=Depends(get_session), _ctx:PublicApiContext=Depends(require_public_scope("data:read"))):
    public_enabled(request); inv=svc._investigation(db,investigation_id)
    if inv.visibility != "public": raise HTTPException(status_code=404,detail="Forensic investigation not found.")
    return PublicEnvelope(data=svc.media_lineage_graph(db,investigation_id),meta={"api_version":"v1","request_id":request.state.request_id})

@public_router.get("/investigations/{investigation_id}/media-comparison-bundle", response_model=PublicEnvelope)
def public_media_comparison_bundle(investigation_id:str, request:Request, db:Session=Depends(get_session), _ctx:PublicApiContext=Depends(require_public_scope("data:read"))):
    public_enabled(request); inv=svc._investigation(db,investigation_id)
    if inv.visibility != "public": raise HTTPException(status_code=404,detail="Forensic investigation not found.")
    return PublicEnvelope(data=svc.media_comparison_bundle(db,investigation_id),meta={"api_version":"v1","request_id":request.state.request_id})


@public_router.get("/investigations/{investigation_id}/quantitative-reconstructions", response_model=PublicEnvelope)
def public_quantitative_reconstructions(investigation_id:str, request:Request, db:Session=Depends(get_session), _ctx:PublicApiContext=Depends(require_public_scope("data:read"))):
    public_enabled(request); inv=svc._investigation(db,investigation_id)
    if inv.visibility != "public": raise HTTPException(status_code=404,detail="Forensic investigation not found.")
    return PublicEnvelope(data=svc.quantitative_reconstruction_bundle(db,investigation_id),meta={"api_version":"v1","request_id":request.state.request_id})


@public_router.get("/investigations/{investigation_id}/documentary-evidence", response_model=PublicEnvelope)
def public_documentary_evidence(investigation_id:str, request:Request, db:Session=Depends(get_session), _ctx:PublicApiContext=Depends(require_public_scope("data:read"))):
    public_enabled(request); inv=svc._investigation(db,investigation_id)
    if inv.visibility != "public": raise HTTPException(status_code=404,detail="Forensic investigation not found.")
    return PublicEnvelope(data=svc.documentary_evidence_bundle(db,investigation_id),meta={"api_version":"v1","request_id":request.state.request_id})


@public_router.get("/investigations/{investigation_id}/research-graphs/{graph_id}", response_model=PublicEnvelope)
def public_research_graph(investigation_id:str, graph_id:str, request:Request, db:Session=Depends(get_session), _ctx:PublicApiContext=Depends(require_public_scope("data:read"))):
    public_enabled(request); inv=svc._investigation(db,investigation_id)
    if inv.visibility != "public": raise HTTPException(status_code=404,detail="Forensic investigation not found.")
    graph=svc._research_graph(db,investigation_id,graph_id)
    if graph.visibility != "public": raise HTTPException(status_code=404,detail="Forensic research graph not found.")
    return PublicEnvelope(data=svc.forensic_research_graph_bundle(db,investigation_id,graph_id),meta={"api_version":"v1","request_id":request.state.request_id})

@public_router.get("/investigations/{investigation_id}/research-graphs/{graph_id}/visual-spec", response_model=PublicEnvelope)
def public_research_graph_visual_spec(investigation_id:str, graph_id:str, request:Request, db:Session=Depends(get_session), _ctx:PublicApiContext=Depends(require_public_scope("data:read"))):
    public_enabled(request); inv=svc._investigation(db,investigation_id)
    if inv.visibility != "public": raise HTTPException(status_code=404,detail="Forensic investigation not found.")
    graph=svc._research_graph(db,investigation_id,graph_id)
    if graph.visibility != "public": raise HTTPException(status_code=404,detail="Forensic research graph not found.")
    return PublicEnvelope(data=svc.forensic_research_graph_visual_spec(db,investigation_id,graph_id),meta={"api_version":"v1","request_id":request.state.request_id})


@public_router.get("/investigations/{investigation_id}/reproducible-packages/{package_id}", response_model=PublicEnvelope)
def public_reproducible_package(investigation_id:str, package_id:str, request:Request, db:Session=Depends(get_session), _ctx:PublicApiContext=Depends(require_public_scope("data:read"))):
    public_enabled(request); inv=svc._investigation(db,investigation_id)
    if inv.visibility != "public": raise HTTPException(status_code=404,detail="Forensic investigation not found.")
    pkg=svc._investigation_package(db,investigation_id,package_id)
    if pkg.visibility != "public": raise HTTPException(status_code=404,detail="Reproducible investigation package not found.")
    return PublicEnvelope(data=svc.portable_reproducible_investigation_package(db,investigation_id,package_id),meta={"api_version":"v1","request_id":request.state.request_id})
