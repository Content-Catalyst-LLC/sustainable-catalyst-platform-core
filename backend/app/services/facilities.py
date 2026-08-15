from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from ..models import FacilityObservation, FacilitySourceIdentifier, OperationalFacility, StreamEvent

FACILITY_TYPES = {
    "hospital", "clinic", "health-center", "school", "university", "shelter",
    "water-facility", "power-facility", "crossing", "port", "airport",
    "communications-facility", "food-distribution", "warehouse", "other",
}
OBSERVATION_KINDS = {"operational-status", "damage-status", "access-status", "service-status", "capacity-status", "supply-status", "other"}

def normalize_country(value: str) -> str:
    code=(value or "").strip().upper()
    if len(code)!=3 or not code.isalpha():
        raise ValueError("country_code must be an ISO3-like three-letter code")
    return code

def validate_coordinates(lat: float | None, lon: float | None) -> None:
    if (lat is None) != (lon is None):
        raise ValueError("latitude and longitude must be supplied together")
    if lat is not None and not (-90 <= lat <= 90 and -180 <= lon <= 180):
        raise ValueError("facility coordinates are outside valid geographic bounds")

def create_facility(db: Session, *, name: str, facility_type: str, country_code: str, admin_area: str|None=None, locality: str|None=None, latitude: float|None=None, longitude: float|None=None, geometry: dict|None=None, canonical_entity_id: str|None=None, source_identifiers: list[dict]|None=None, public: bool=True, metadata: dict|None=None) -> OperationalFacility:
    ftype=facility_type.strip().lower()
    if ftype not in FACILITY_TYPES:
        raise ValueError(f"unsupported facility_type: {facility_type}")
    code=normalize_country(country_code); validate_coordinates(latitude, longitude)
    identifiers=source_identifiers or []
    for item in identifiers:
        namespace=str(item.get("namespace","")).strip(); value=str(item.get("value","")).strip()
        if not namespace or not value: raise ValueError("source identifiers require namespace and value")
        existing=db.scalar(select(FacilitySourceIdentifier).where(FacilitySourceIdentifier.namespace==namespace, FacilitySourceIdentifier.value==value))
        if existing:
            row=db.get(OperationalFacility, existing.facility_id)
            if row: return row
    row=OperationalFacility(canonical_entity_id=canonical_entity_id, name=name.strip(), facility_type=ftype, country_code=code, admin_area=admin_area, locality=locality, latitude=latitude, longitude=longitude, geometry_json=geometry, public=public, metadata_json=metadata or {})
    db.add(row); db.flush()
    for item in identifiers:
        db.add(FacilitySourceIdentifier(facility_id=row.id, namespace=str(item["namespace"]).strip(), value=str(item["value"]).strip(), source_id=item.get("source_id")))
    db.commit(); db.refresh(row); return row

def create_observation(db: Session, facility_id: str, *, observation_kind: str, status_value: str, observed_at: datetime, publisher: str, source_id: str|None=None, connector_id: str|None=None, source_record_id: str|None=None, source_url: str|None=None, evidence_class: str="published-evidence", geographic_scope: str|None=None, methodology: str|None=None, confidence: float|None=None, services: list|None=None, constraints: list|None=None, details: dict|None=None, provenance: dict|None=None, public: bool=True) -> FacilityObservation:
    facility=db.get(OperationalFacility, facility_id)
    if not facility: raise ValueError("facility not found")
    kind=observation_kind.strip().lower()
    if kind not in OBSERVATION_KINDS: raise ValueError(f"unsupported observation_kind: {observation_kind}")
    if confidence is not None and not 0 <= confidence <= 1: raise ValueError("confidence must be between 0 and 1")
    if observed_at.tzinfo is None: observed_at=observed_at.replace(tzinfo=timezone.utc)
    row=FacilityObservation(facility_id=facility_id, observation_kind=kind, status_value=status_value.strip().lower(), observed_at=observed_at, publisher=publisher.strip(), source_id=source_id, connector_id=connector_id, source_record_id=source_record_id, source_url=source_url, evidence_class=evidence_class, geographic_scope=geographic_scope, methodology=methodology, confidence=confidence, services_json=services or [], constraints_json=constraints or [], details_json=details or {}, provenance_json=provenance or {}, public=public)
    db.add(row); db.flush()
    db.add(StreamEvent(event_type="facility.observation.created", subject_type="facility", subject_id=facility_id, public=bool(public and facility.public), payload_json={"facility_id": facility_id, "country_code": facility.country_code, "facility_type": facility.facility_type, "observation_kind": kind, "status_value": row.status_value, "observed_at": observed_at.isoformat(), "publisher": publisher, "evidence_class": evidence_class}))
    db.commit(); db.refresh(row); return row

def current_observations(db: Session, facility_id: str, *, public_only: bool=False) -> list[FacilityObservation]:
    q=select(FacilityObservation).where(FacilityObservation.facility_id==facility_id)
    if public_only: q=q.where(FacilityObservation.public.is_(True))
    rows=db.scalars(q.order_by(desc(FacilityObservation.observed_at), desc(FacilityObservation.created_at))).all()
    current=[]; seen=set()
    for row in rows:
        if row.observation_kind not in seen:
            current.append(row); seen.add(row.observation_kind)
    return current

def query_facilities(db: Session, *, country_code: str|None=None, facility_type: str|None=None, admin_area: str|None=None, bbox: tuple[float,float,float,float]|None=None, public_only: bool=False, limit: int=200) -> list[OperationalFacility]:
    q=select(OperationalFacility)
    if country_code: q=q.where(OperationalFacility.country_code==normalize_country(country_code))
    if facility_type: q=q.where(OperationalFacility.facility_type==facility_type.strip().lower())
    if admin_area: q=q.where(OperationalFacility.admin_area==admin_area)
    if public_only: q=q.where(OperationalFacility.public.is_(True))
    if bbox:
        min_lon,min_lat,max_lon,max_lat=bbox
        if min_lon>max_lon or min_lat>max_lat: raise ValueError("bbox must be min_lon,min_lat,max_lon,max_lat")
        q=q.where(OperationalFacility.latitude.is_not(None), OperationalFacility.longitude.is_not(None), OperationalFacility.longitude>=min_lon, OperationalFacility.longitude<=max_lon, OperationalFacility.latitude>=min_lat, OperationalFacility.latitude<=max_lat)
    return list(db.scalars(q.order_by(OperationalFacility.country_code, OperationalFacility.facility_type, OperationalFacility.name).limit(limit)).all())
