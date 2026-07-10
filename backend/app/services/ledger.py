from __future__ import annotations

from datetime import datetime, timezone
import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..hashing import json_safe, sha256_payload
from ..models import LedgerEntry
from ..schemas import LedgerVerificationResult


def _stable_datetime(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def append_ledger_entry(
    db: Session,
    *,
    record_type: str,
    record_id: str,
    action: str,
    actor: str,
    payload: dict,
) -> LedgerEntry:
    previous = db.scalar(
        select(LedgerEntry).order_by(LedgerEntry.sequence.desc()).limit(1)
    )
    previous_hash = previous.entry_hash if previous else None
    created_at = datetime.now(timezone.utc)
    entry_id = str(uuid.uuid4())
    safe_payload = json_safe(payload)
    payload_hash = sha256_payload(safe_payload)
    entry_material = {
        "id": entry_id,
        "record_type": record_type,
        "record_id": record_id,
        "action": action,
        "actor": actor,
        "payload_hash": payload_hash,
        "previous_entry_hash": previous_hash,
        "created_at": _stable_datetime(created_at),
    }
    entry = LedgerEntry(
        id=entry_id,
        record_type=record_type,
        record_id=record_id,
        action=action,
        actor=actor,
        payload_hash=payload_hash,
        previous_entry_hash=previous_hash,
        entry_hash=sha256_payload(entry_material),
        payload_json=safe_payload,
        created_at=created_at,
    )
    db.add(entry)
    db.flush()
    return entry


def list_ledger_entries(
    db: Session,
    *,
    record_type: str | None = None,
    record_id: str | None = None,
    limit: int = 100,
    offset: int = 0,
) -> list[LedgerEntry]:
    filters = []
    if record_type:
        filters.append(LedgerEntry.record_type == record_type)
    if record_id:
        filters.append(LedgerEntry.record_id == record_id)
    return list(
        db.scalars(
            select(LedgerEntry)
            .where(*filters)
            .order_by(LedgerEntry.sequence)
            .limit(limit)
            .offset(offset)
        ).all()
    )


def verify_ledger(db: Session) -> LedgerVerificationResult:
    entries = list(
        db.scalars(
            select(LedgerEntry).order_by(LedgerEntry.sequence)
        ).all()
    )
    errors: list[str] = []
    previous_hash: str | None = None

    for entry in entries:
        observed_payload_hash = sha256_payload(entry.payload_json)
        if observed_payload_hash != entry.payload_hash:
            errors.append(
                f"Sequence {entry.sequence}: payload hash mismatch."
            )

        expected_entry_hash = sha256_payload(
            {
                "id": entry.id,
                "record_type": entry.record_type,
                "record_id": entry.record_id,
                "action": entry.action,
                "actor": entry.actor,
                "payload_hash": entry.payload_hash,
                "previous_entry_hash": entry.previous_entry_hash,
                "created_at": _stable_datetime(entry.created_at),
            }
        )
        if expected_entry_hash != entry.entry_hash:
            errors.append(
                f"Sequence {entry.sequence}: entry hash mismatch."
            )

        if entry.previous_entry_hash != previous_hash:
            errors.append(
                f"Sequence {entry.sequence}: previous hash does not match chain head."
            )
        previous_hash = entry.entry_hash

    return LedgerVerificationResult(
        valid=not errors,
        entries_checked=len(entries),
        first_sequence=entries[0].sequence if entries else None,
        last_sequence=entries[-1].sequence if entries else None,
        head_hash=entries[-1].entry_hash if entries else None,
        errors=errors,
    )
