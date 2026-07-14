from __future__ import annotations

from datetime import datetime
from fastapi import HTTPException
from sqlalchemy import and_, desc, func, or_, select
from sqlalchemy.orm import Session

from ..models import LiveDataConnector, LiveDataRawRecord, LiveDataSource, ScientificDataRecord

SCIENTIFIC_RECORD_TYPES = {
    "earth_science_dataset": "Earth science collection or dataset metadata.",
    "astronomy_image": "Astronomy image or public science media record.",
    "environmental_observation": "Climate, weather, oceanographic, or geophysical observation.",
    "forecast_field": "Numerical weather or atmospheric forecast field metadata.",
    "water_observation": "Hydrologic measurement or time-series observation.",
    "biomedical_database_record": "Biomedical literature, gene, protein, sequence, taxonomy, or project identifier.",
    "chemical_compound": "Chemical compound identity, structure, and property record.",
    "biodiversity_occurrence": "Species or taxon occurrence record with dataset provenance.",
    "material": "Computed or experimentally referenced material record.",
    "telescope_observation": "Telescope or mission observation metadata and access links.",
    "astronomy_catalog_record": "Astronomical source or archive catalog record.",
}


def get_record_or_404(db: Session, record_id: str, *, public_only: bool = False) -> ScientificDataRecord:
    record = db.get(ScientificDataRecord, record_id)
    if record is None or (public_only and not record.public):
        raise HTTPException(status_code=404, detail="Scientific data record not found.")
    return record


def list_records(db: Session, *, record_type: str | None = None, discipline: str | None = None, source_id: str | None = None, connector_id: str | None = None, collection: str | None = None, mission: str | None = None, instrument: str | None = None, target: str | None = None, dataset_id: str | None = None, query: str | None = None, start: datetime | None = None, end: datetime | None = None, public_only: bool = False, limit: int = 100, offset: int = 0) -> tuple[list[ScientificDataRecord], int]:
    filters=[]
    if record_type: filters.append(ScientificDataRecord.record_type == record_type)
    if discipline: filters.append(ScientificDataRecord.discipline == discipline)
    if source_id: filters.append(ScientificDataRecord.source_id == source_id)
    if connector_id: filters.append(ScientificDataRecord.connector_id == connector_id)
    if collection: filters.append(ScientificDataRecord.collection == collection)
    if mission: filters.append(ScientificDataRecord.mission == mission)
    if instrument: filters.append(ScientificDataRecord.instrument == instrument)
    if target: filters.append(ScientificDataRecord.target == target)
    if dataset_id: filters.append(ScientificDataRecord.dataset_id == dataset_id)
    if start: filters.append(ScientificDataRecord.observation_start >= start)
    if end: filters.append(ScientificDataRecord.observation_start <= end)
    if public_only: filters.append(ScientificDataRecord.public.is_(True))
    if query:
        pattern=f"%{query.strip()}%"
        filters.append(or_(ScientificDataRecord.title.ilike(pattern), ScientificDataRecord.summary.ilike(pattern), ScientificDataRecord.dataset_id.ilike(pattern), ScientificDataRecord.collection.ilike(pattern), ScientificDataRecord.target.ilike(pattern)))
    stmt=select(ScientificDataRecord); count_stmt=select(func.count()).select_from(ScientificDataRecord)
    if filters:
        stmt=stmt.where(and_(*filters)); count_stmt=count_stmt.where(and_(*filters))
    total=int(db.scalar(count_stmt) or 0)
    rows=list(db.scalars(stmt.order_by(desc(ScientificDataRecord.observation_start), desc(ScientificDataRecord.published_at), ScientificDataRecord.title).limit(limit).offset(offset)).all())
    return rows,total


def stats(db: Session) -> dict:
    def grouped(column):
        return {str(name): int(count) for name,count in db.execute(select(column,func.count()).group_by(column)).all() if name}
    return {
        "records": int(db.scalar(select(func.count()).select_from(ScientificDataRecord)) or 0),
        "public_records": int(db.scalar(select(func.count()).select_from(ScientificDataRecord).where(ScientificDataRecord.public.is_(True))) or 0),
        "by_record_type": grouped(ScientificDataRecord.record_type),
        "by_discipline": grouped(ScientificDataRecord.discipline),
        "by_source": grouped(ScientificDataRecord.source_id),
        "by_mission": grouped(ScientificDataRecord.mission),
    }


def provenance(db: Session, record: ScientificDataRecord) -> dict:
    return {
        "record": record,
        "source": db.get(LiveDataSource, record.source_id),
        "connector": db.get(LiveDataConnector, record.connector_id),
        "raw_record": db.get(LiveDataRawRecord, record.raw_record_id) if record.raw_record_id else None,
        "record_type_explanation": SCIENTIFIC_RECORD_TYPES.get(record.record_type),
    }
