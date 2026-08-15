from __future__ import annotations
from datetime import datetime, timezone
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from ..hashing import sha256_payload
from ..models import ChangeControlRecord, OperationsIncident, OperationsIncidentEvent, ProductionDeploymentMarker, RollbackCoordinationRecord

SEVERITIES={"sev1","sev2","sev3","sev4"}
INCIDENT_SOURCES={"manual","slo","deployment","reliability","certification","other"}
INCIDENT_STATES={"open","investigating","mitigated","resolved","closed"}
INCIDENT_TRANSITIONS={
    "open":{"investigating","mitigated","resolved"},
    "investigating":{"mitigated","resolved"},
    "mitigated":{"investigating","resolved"},
    "resolved":{"closed","investigating"},
    "closed":{"investigating"},
}
VISIBILITIES={"internal","private","restricted"}
CHANGE_TYPES={"deployment","configuration","schema","connector","rollback","other"}
CHANGE_RISKS={"low","medium","high","critical"}
CHANGE_STATES={"planned","approved","in_progress","completed","failed","cancelled"}
ROLLBACK_STATES={"proposed","acknowledged","executed","dismissed"}

def _now(): return datetime.now(timezone.utc)
def _clean(value):
    if isinstance(value,dict): return {str(k):_clean(v) for k,v in value.items() if str(k).lower() not in {"token","password","secret","api_key","apikey","authorization"}}
    if isinstance(value,list): return [_clean(v) for v in value]
    return value

def _dt_key(value):
    if value is None: return None
    if value.tzinfo is not None: value=value.astimezone(timezone.utc).replace(tzinfo=None)
    return value.isoformat()

def _event_material(event:OperationsIncidentEvent):
    return {"incident_id":event.incident_id,"event_type":event.event_type,"previous_state":event.previous_state,"new_state":event.new_state,"actor":event.actor,"note":event.note,"details":event.details_json,"previous_event_hash":event.previous_event_hash,"created_at":_dt_key(event.created_at)}

def append_event(db:Session, incident:OperationsIncident, *, event_type:str, actor:str="operator", new_state:str|None=None, note:str|None=None, details:dict|None=None):
    prior=db.scalars(select(OperationsIncidentEvent).where(OperationsIncidentEvent.incident_id==incident.id).order_by(OperationsIncidentEvent.created_at.desc(),OperationsIncidentEvent.id.desc()).limit(1)).first()
    previous_state=incident.state
    if new_state is not None:
        if new_state not in INCIDENT_STATES: raise ValueError("Unsupported incident state.")
        if new_state != incident.state and new_state not in INCIDENT_TRANSITIONS.get(incident.state,set()): raise ValueError(f"Invalid incident transition: {incident.state} -> {new_state}.")
        incident.state=new_state
        if new_state=="mitigated": incident.mitigated_at=_now()
        if new_state=="resolved": incident.resolved_at=_now()
        if new_state=="investigating" and previous_state in {"resolved","closed"}: incident.resolved_at=None
        db.add(incident)
    row=OperationsIncidentEvent(incident_id=incident.id,event_type=event_type[:60],previous_state=previous_state,new_state=new_state,actor=(actor or "operator")[:255],note=note,details_json=_clean(details or {}),previous_event_hash=prior.event_hash if prior else None,created_at=_now(),event_hash="pending")
    row.event_hash=sha256_payload(_event_material(row))
    db.add(row); db.commit(); db.refresh(row); db.refresh(incident); return row

def create_incident(db:Session, *, title:str, service:str="platform-core", environment:str="production", severity:str="sev3", source:str="manual", source_ref:str|None=None, summary:str|None=None, owner:str="unassigned", visibility:str="internal", idempotency_key:str|None=None, metadata:dict|None=None):
    if severity not in SEVERITIES: raise ValueError("Unsupported incident severity.")
    if source not in INCIDENT_SOURCES: raise ValueError("Unsupported incident source.")
    if visibility not in VISIBILITIES: raise ValueError("Operational incidents cannot be public records.")
    if idempotency_key:
        existing=db.scalar(select(OperationsIncident).where(OperationsIncident.idempotency_key==idempotency_key))
        if existing: return existing
    row=OperationsIncident(idempotency_key=idempotency_key,title=title[:300],service=(service or "platform-core")[:100],environment=(environment or "production")[:40],severity=severity,source=source,source_ref=(source_ref or "")[:255] or None,summary=summary,owner=(owner or "unassigned")[:255],visibility=visibility,metadata_json=_clean(metadata or {}))
    db.add(row)
    try: db.commit()
    except IntegrityError:
        db.rollback()
        if idempotency_key:
            existing=db.scalar(select(OperationsIncident).where(OperationsIncident.idempotency_key==idempotency_key))
            if existing: return existing
        raise
    db.refresh(row); append_event(db,row,event_type="incident.created",actor=owner,note=summary,details={"source":source,"source_ref":source_ref,"severity":severity}); return row

def list_incidents(db:Session, *, state:str|None=None, service:str|None=None, limit:int=100):
    q=select(OperationsIncident).order_by(OperationsIncident.created_at.desc()).limit(limit)
    if state: q=q.where(OperationsIncident.state==state)
    if service: q=q.where(OperationsIncident.service==service)
    return db.scalars(q).all()

def events(db:Session, incident_id:str): return db.scalars(select(OperationsIncidentEvent).where(OperationsIncidentEvent.incident_id==incident_id).order_by(OperationsIncidentEvent.created_at.asc(),OperationsIncidentEvent.id.asc())).all()

def verify_event_chain(db:Session, incident_id:str):
    previous=None; checked=0
    for row in events(db,incident_id):
        checked+=1
        if row.previous_event_hash!=previous: return {"valid":False,"checked":checked,"reason":"previous-event-hash-mismatch","event_id":row.id}
        expected=sha256_payload(_event_material(row))
        if row.event_hash!=expected: return {"valid":False,"checked":checked,"reason":"event-hash-mismatch","event_id":row.id}
        previous=row.event_hash
    return {"valid":True,"checked":checked,"reason":None,"event_id":None}

def create_change(db:Session, settings, *, change_key:str, service:str="platform-core", release:str|None=None, environment:str="production", change_type:str="deployment", risk:str="medium", actor:str="operator", incident_id:str|None=None, deployment_marker_id:str|None=None, details:dict|None=None, planned_start_at:datetime|None=None):
    if change_type not in CHANGE_TYPES: raise ValueError("Unsupported change type.")
    if risk not in CHANGE_RISKS: raise ValueError("Unsupported change risk.")
    existing=db.scalar(select(ChangeControlRecord).where(ChangeControlRecord.change_key==change_key))
    if existing: return existing
    approval_required=bool(settings.change_high_risk_approval_required and risk in {"high","critical"})
    row=ChangeControlRecord(change_key=change_key[:255],service=service[:100],release=(release or "")[:40] or None,environment=environment[:40],change_type=change_type,risk=risk,state="planned",actor=actor[:255],approval_required=approval_required,incident_id=incident_id,deployment_marker_id=deployment_marker_id,details_json=_clean(details or {}),planned_start_at=planned_start_at)
    db.add(row); db.commit(); db.refresh(row); return row

def approve_change(db:Session, row:ChangeControlRecord, *, actor:str):
    if row.state not in {"planned","approved"}: raise ValueError("Only planned changes can be approved.")
    row.state="approved"; row.approved_by=actor[:255]; db.add(row); db.commit(); db.refresh(row); return row

def start_change(db:Session, row:ChangeControlRecord, *, actor:str):
    if row.state not in {"planned","approved"}: raise ValueError("Change is not startable.")
    if row.approval_required and not row.approved_by: raise ValueError("High-risk changes require approval before start.")
    row.state="in_progress"; row.actor=actor[:255]; row.started_at=_now(); db.add(row); db.commit(); db.refresh(row); return row

def finish_change(db:Session, row:ChangeControlRecord, *, state:str, actor:str, details:dict|None=None):
    if state not in {"completed","failed","cancelled"}: raise ValueError("Unsupported terminal change state.")
    if row.state not in {"planned","approved","in_progress"}: raise ValueError("Change is already terminal.")
    row.state=state; row.actor=actor[:255]; row.completed_at=_now(); row.details_json={**(row.details_json or {}),**_clean(details or {})}; db.add(row); db.commit(); db.refresh(row); return row

def assess_rollback(db:Session, *, incident:OperationsIncident, deployment_marker_id:str|None=None, slo_evaluations:list[dict]|None=None):
    deployment=db.get(ProductionDeploymentMarker,deployment_marker_id) if deployment_marker_id else None
    evaluations=slo_evaluations or []
    breached=[x for x in evaluations if x.get("state")=="breached"]
    recommended=bool(deployment and breached and incident.severity in {"sev1","sev2"} and incident.state not in {"resolved","closed"})
    rationale=("Rollback review recommended because a severe active incident is temporally associated with a deployment and one or more SLOs are breached." if recommended else "Rollback is not automatically recommended; operator review remains required.")
    row=RollbackCoordinationRecord(incident_id=incident.id,deployment_marker_id=deployment.id if deployment else None,recommendation="recommended" if recommended else "review",state="proposed",rationale=rationale,evidence_json=_clean({"slo_evaluations":evaluations,"deployment_release":deployment.release if deployment else None,"correlation_only":True}),automatic_execution=False,causal_attribution=False)
    db.add(row); db.commit(); db.refresh(row); return row

def decide_rollback(db:Session, row:RollbackCoordinationRecord, *, state:str, actor:str, note:str|None=None):
    if state not in {"acknowledged","executed","dismissed"}: raise ValueError("Unsupported rollback decision state.")
    if state=="executed" and row.state!="acknowledged": raise ValueError("Rollback execution requires prior operator acknowledgement.")
    row.state=state; row.operator_actor=actor[:255]; row.operator_note=note; row.automatic_execution=False; row.causal_attribution=False; db.add(row); db.commit(); db.refresh(row); return row

def readiness(db:Session, settings):
    open_states={"open","investigating","mitigated"}
    open_count=db.scalar(select(func.count()).select_from(OperationsIncident).where(OperationsIncident.state.in_(open_states))) or 0
    active_changes=db.scalar(select(func.count()).select_from(ChangeControlRecord).where(ChangeControlRecord.state.in_({"planned","approved","in_progress"}))) or 0
    return {"enabled":settings.incident_change_control_enabled,"public_status_enabled":settings.incident_public_status_enabled,"incident_retention_hours":settings.incident_retention_hours,"high_risk_approval_required":settings.change_high_risk_approval_required,"open_incidents":int(open_count),"active_changes":int(active_changes),"automatic_rollback_enabled":False,"rollback_execution_mode":"operator-confirmed","causal_attribution_from_correlation":False,"evidence_semantics_unchanged":True}

def public_status(db:Session, settings):
    active={"open","investigating","mitigated"}; rows=db.scalars(select(OperationsIncident).where(OperationsIncident.state.in_(active))).all()
    by={k:0 for k in sorted(SEVERITIES)}
    for row in rows: by[row.severity]=by.get(row.severity,0)+1
    r=readiness(db,settings)
    return {"release":settings.version,"status":"ready" if r["enabled"] else "disabled","open_incidents":len(rows),"incidents_by_severity":by,"active_changes":r["active_changes"],"automatic_rollback_enabled":False,"rollback_execution_mode":"operator-confirmed","causal_attribution_from_correlation":False,"incident_details_publicly_exposed":False,"operator_metadata_publicly_exposed":False}
