from __future__ import annotations

from datetime import datetime
from fastapi import HTTPException
from sqlalchemy import and_, desc, func, or_, select
from sqlalchemy.orm import Session

from ..models import EconomicDataRecord, LiveDataConnector, LiveDataRawRecord, LiveDataSource

ECONOMIC_RECORD_TYPES = {
    "official_statistic": "Official statistical observation published by a public institution.",
    "macroeconomic_indicator": "National accounts, prices, exchange rates, debt, or macroeconomic observation.",
    "labour_statistic": "Employment, unemployment, wages, productivity, or labour-market observation.",
    "trade_statistic": "Imports, exports, services, commodities, or bilateral trade observation.",
    "energy_statistic": "Energy production, consumption, price, capacity, or emissions observation.",
    "company_filing_fact": "Structured fact extracted from an official company filing.",
    "agriculture_statistic": "Food, agriculture, forestry, fisheries, land, or agricultural-emissions observation.",
    "demographic_statistic": "Population, household, housing, income, poverty, or demographic observation.",
}


def get_record_or_404(db: Session, record_id: str, *, public_only: bool = False) -> EconomicDataRecord:
    record=db.get(EconomicDataRecord,record_id)
    if record is None or (public_only and not record.public):
        raise HTTPException(status_code=404,detail="Economic data record not found.")
    return record


def list_records(db: Session, *, record_type=None, subject=None, source_id=None, connector_id=None, indicator_code=None, dataset_id=None, geography_code=None, frequency=None, query=None, start:datetime|None=None, end:datetime|None=None, public_only=False, limit=100, offset=0):
    filters=[]
    if record_type: filters.append(EconomicDataRecord.record_type==record_type)
    if subject: filters.append(EconomicDataRecord.subject==subject)
    if source_id: filters.append(EconomicDataRecord.source_id==source_id)
    if connector_id: filters.append(EconomicDataRecord.connector_id==connector_id)
    if indicator_code: filters.append(EconomicDataRecord.indicator_code==indicator_code)
    if dataset_id: filters.append(EconomicDataRecord.dataset_id==dataset_id)
    if geography_code: filters.append(EconomicDataRecord.geography_code==geography_code)
    if frequency: filters.append(EconomicDataRecord.frequency==frequency)
    if start: filters.append(EconomicDataRecord.period_start>=start)
    if end: filters.append(EconomicDataRecord.period_start<=end)
    if public_only: filters.append(EconomicDataRecord.public.is_(True))
    if query:
        pattern=f"%{query.strip()}%"
        filters.append(or_(EconomicDataRecord.indicator_name.ilike(pattern),EconomicDataRecord.indicator_code.ilike(pattern),EconomicDataRecord.geography_name.ilike(pattern),EconomicDataRecord.dataset_id.ilike(pattern),EconomicDataRecord.notes.ilike(pattern)))
    stmt=select(EconomicDataRecord); count_stmt=select(func.count()).select_from(EconomicDataRecord)
    if filters: stmt=stmt.where(and_(*filters)); count_stmt=count_stmt.where(and_(*filters))
    total=int(db.scalar(count_stmt) or 0)
    rows=list(db.scalars(stmt.order_by(desc(EconomicDataRecord.period_start),desc(EconomicDataRecord.published_at),EconomicDataRecord.indicator_code).limit(limit).offset(offset)).all())
    return rows,total


def stats(db:Session)->dict:
    def grouped(column): return {str(name):int(count) for name,count in db.execute(select(column,func.count()).group_by(column)).all() if name}
    return {"records":int(db.scalar(select(func.count()).select_from(EconomicDataRecord)) or 0),"public_records":int(db.scalar(select(func.count()).select_from(EconomicDataRecord).where(EconomicDataRecord.public.is_(True))) or 0),"by_record_type":grouped(EconomicDataRecord.record_type),"by_subject":grouped(EconomicDataRecord.subject),"by_source":grouped(EconomicDataRecord.source_id),"by_frequency":grouped(EconomicDataRecord.frequency)}


def provenance(db:Session,record:EconomicDataRecord)->dict:
    return {"record":record,"source":db.get(LiveDataSource,record.source_id),"connector":db.get(LiveDataConnector,record.connector_id),"raw_record":db.get(LiveDataRawRecord,record.raw_record_id) if record.raw_record_id else None,"record_type_explanation":ECONOMIC_RECORD_TYPES.get(record.record_type)}
