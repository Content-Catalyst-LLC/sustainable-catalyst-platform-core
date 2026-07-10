from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models import ImportJob, Relationship
from ..schemas import SiteIntelligenceManifest
from .entities import upsert_entity
from .relationships import create_relationship


def import_site_intelligence_manifest(
    db: Session,
    manifest: SiteIntelligenceManifest,
) -> ImportJob:
    job = ImportJob(
        adapter="site-intelligence-manifest-v1",
        source_name=manifest.source_name,
        entities_received=len(manifest.entities),
        relationships_received=len(manifest.relationships),
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    try:
        for entity_payload in manifest.entities:
            _, created = upsert_entity(db, entity_payload)
            if created:
                job.entities_created += 1
            else:
                job.entities_updated += 1
            db.add(job)
            db.commit()

        for relationship_payload in manifest.relationships:
            existing = db.scalar(
                select(Relationship).where(
                    Relationship.subject_id == relationship_payload.subject_id,
                    Relationship.predicate == relationship_payload.predicate,
                    Relationship.object_id == relationship_payload.object_id,
                )
            )
            if existing is None:
                create_relationship(db, relationship_payload)
                job.relationships_created += 1
            else:
                job.relationships_skipped += 1
            db.add(job)
            db.commit()

        job.status = "completed"
        job.completed_at = datetime.now(timezone.utc)
        job.details = {
            "idempotent_entity_upsert": True,
            "relationship_uniqueness": "subject-predicate-object",
        }
        db.add(job)
        db.commit()
    except Exception as exc:
        db.rollback()
        job = db.get(ImportJob, job.id)
        if job is not None:
            job.status = "failed"
            job.error_message = str(exc)
            job.completed_at = datetime.now(timezone.utc)
            db.add(job)
            db.commit()
        raise

    db.refresh(job)
    return job
