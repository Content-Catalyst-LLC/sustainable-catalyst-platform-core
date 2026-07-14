from __future__ import annotations

from datetime import datetime
from fastapi import HTTPException
from sqlalchemy import and_, desc, func, or_, select
from sqlalchemy.orm import Session

from ..models import InternationalLawRecord, LiveDataConnector, LiveDataRawRecord, LiveDataSource

AUTHORITY_TAXONOMY = {
    "binding_treaty_obligation": "Binding treaty obligation or treaty status record.",
    "official_security_council_resolution": "Official Security Council resolution. Binding effect must be determined from the Charter basis, operative text, and legal context rather than inferred from the document symbol alone.",
    "binding_security_council_decision": "Security Council decision whose binding status has been established through reviewed Charter and textual analysis.",
    "judicial_decision": "Judgment or binding judicial disposition for the parties and matter concerned.",
    "advisory_judicial_opinion": "Advisory judicial opinion; authoritative but not a contentious judgment.",
    "official_interpretation": "Official interpretation by a treaty body or other authorized mechanism.",
    "recommendatory_resolution": "Resolution or decision with recommendatory rather than treaty-level authority.",
    "non_binding_recommendation": "Official recommendation from a human-rights or related monitoring mechanism.",
    "draft_codification_text": "Draft articles, conclusions, principles, or other codification work.",
    "official_report": "Official document or report that is evidentiary but not itself a binding legal rule.",
    "humanitarian_reporting": "Humanitarian report or situation update; informational rather than legal authority.",
    "statistical_observation": "Official statistical observation; evidence rather than legal authority.",
    "commentary": "Secondary commentary or analysis.",
}


def get_record_or_404(db: Session, record_id: str, *, public_only: bool = False) -> InternationalLawRecord:
    record = db.get(InternationalLawRecord, record_id)
    if record is None or (public_only and not record.public):
        raise HTTPException(status_code=404, detail="International-law record not found.")
    return record


def list_records(
    db: Session,
    *,
    record_type: str | None = None,
    authority_level: str | None = None,
    legal_body: str | None = None,
    country: str | None = None,
    subject: str | None = None,
    official_symbol: str | None = None,
    query: str | None = None,
    start: datetime | None = None,
    end: datetime | None = None,
    public_only: bool = False,
    limit: int = 100,
    offset: int = 0,
) -> tuple[list[InternationalLawRecord], int]:
    filters = []
    if record_type:
        filters.append(InternationalLawRecord.record_type == record_type)
    if authority_level:
        filters.append(InternationalLawRecord.authority_level == authority_level)
    if legal_body:
        filters.append(InternationalLawRecord.legal_body == legal_body)
    if official_symbol:
        filters.append(InternationalLawRecord.official_symbol == official_symbol)
    if start:
        filters.append(InternationalLawRecord.publication_date >= start)
    if end:
        filters.append(InternationalLawRecord.publication_date <= end)
    if public_only:
        filters.append(InternationalLawRecord.public.is_(True))
    if country:
        filters.append(InternationalLawRecord.countries_json.contains([country]))
    if subject:
        filters.append(InternationalLawRecord.subjects_json.contains([subject]))
    if query:
        pattern = f"%{query.strip()}%"
        filters.append(or_(InternationalLawRecord.title.ilike(pattern), InternationalLawRecord.summary.ilike(pattern), InternationalLawRecord.official_symbol.ilike(pattern)))
    base = select(InternationalLawRecord)
    count_stmt = select(func.count()).select_from(InternationalLawRecord)
    if filters:
        base = base.where(and_(*filters))
        count_stmt = count_stmt.where(and_(*filters))
    total = int(db.scalar(count_stmt) or 0)
    rows = list(db.scalars(base.order_by(desc(InternationalLawRecord.publication_date), InternationalLawRecord.title).limit(limit).offset(offset)).all())
    return rows, total


def stats(db: Session) -> dict:
    def grouped(column):
        return {str(name): int(count) for name, count in db.execute(select(column, func.count()).group_by(column)).all() if name}
    return {
        "records": int(db.scalar(select(func.count()).select_from(InternationalLawRecord)) or 0),
        "by_record_type": grouped(InternationalLawRecord.record_type),
        "by_authority_level": grouped(InternationalLawRecord.authority_level),
        "by_legal_body": grouped(InternationalLawRecord.legal_body),
        "public_records": int(db.scalar(select(func.count()).select_from(InternationalLawRecord).where(InternationalLawRecord.public.is_(True))) or 0),
    }


def provenance(db: Session, record: InternationalLawRecord) -> dict:
    return {
        "record": record,
        "source": db.get(LiveDataSource, record.source_id),
        "connector": db.get(LiveDataConnector, record.connector_id),
        "raw_record": db.get(LiveDataRawRecord, record.raw_record_id) if record.raw_record_id else None,
        "authority_explanation": AUTHORITY_TAXONOMY.get(record.authority_level),
    }
