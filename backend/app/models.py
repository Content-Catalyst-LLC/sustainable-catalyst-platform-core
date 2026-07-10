from __future__ import annotations
from datetime import datetime, timezone
import uuid
from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Index, Integer, JSON, String, Text, UniqueConstraint, event
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .database import Base

def utcnow() -> datetime:
    return datetime.now(timezone.utc)

class Entity(Base):
    __tablename__ = "entities"
    __table_args__ = (
        UniqueConstraint("entity_type", "slug", name="uq_entities_type_slug"),
        Index("ix_entities_type_status", "entity_type", "status"),
        Index("ix_entities_name", "name"),
    )
    id: Mapped[str] = mapped_column(String(255), primary_key=True)
    entity_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    slug: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(300), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    canonical_url: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="active", index=True)
    visibility: Mapped[str] = mapped_column(String(30), default="public", index=True)
    schema_version: Mapped[str] = mapped_column(String(20), default="1.0")
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)
    aliases: Mapped[list["EntityAlias"]] = relationship(back_populates="entity", cascade="all, delete-orphan")

class EntityAlias(Base):
    __tablename__ = "entity_aliases"
    __table_args__ = (UniqueConstraint("namespace", "value", name="uq_alias_namespace_value"), Index("ix_alias_entity", "entity_id"))
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    entity_id: Mapped[str] = mapped_column(ForeignKey("entities.id", ondelete="CASCADE"), nullable=False)
    namespace: Mapped[str] = mapped_column(String(100), nullable=False)
    value: Mapped[str] = mapped_column(String(1000), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    entity: Mapped[Entity] = relationship(back_populates="aliases")

class PredicateDefinition(Base):
    __tablename__ = "predicate_definitions"
    __table_args__ = (Index("ix_predicate_status_visibility", "status", "visibility"), Index("ix_predicate_sort", "sort_order", "label"))
    id: Mapped[str] = mapped_column(String(100), primary_key=True)
    label: Mapped[str] = mapped_column(String(150), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    inverse_predicate: Mapped[str | None] = mapped_column(String(100), nullable=True)
    symmetric: Mapped[bool] = mapped_column(Boolean, default=False)
    transitive: Mapped[bool] = mapped_column(Boolean, default=False)
    allowed_subject_types: Mapped[list] = mapped_column(JSON, default=list)
    allowed_object_types: Mapped[list] = mapped_column(JSON, default=list)
    status: Mapped[str] = mapped_column(String(30), default="active", index=True)
    visibility: Mapped[str] = mapped_column(String(30), default="public", index=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=100)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

class Relationship(Base):
    __tablename__ = "relationships"
    __table_args__ = (
        UniqueConstraint("subject_id", "predicate", "object_id", name="uq_relationship_spo"),
        Index("ix_relationship_subject_predicate", "subject_id", "predicate"),
        Index("ix_relationship_object_predicate", "object_id", "predicate"),
        Index("ix_relationship_status_confidence", "status", "confidence"),
    )
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    subject_id: Mapped[str] = mapped_column(ForeignKey("entities.id", ondelete="CASCADE"), nullable=False)
    predicate: Mapped[str] = mapped_column(ForeignKey("predicate_definitions.id", ondelete="RESTRICT"), nullable=False, index=True)
    object_id: Mapped[str] = mapped_column(ForeignKey("entities.id", ondelete="CASCADE"), nullable=False)
    confidence: Mapped[float] = mapped_column(Float, default=1.0)
    status: Mapped[str] = mapped_column(String(50), default="proposed", index=True)
    provenance: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

class RelationshipReview(Base):
    __tablename__ = "relationship_reviews"
    __table_args__ = (Index("ix_review_relationship_created", "relationship_id", "created_at"), Index("ix_review_decision", "decision"))
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    relationship_id: Mapped[str] = mapped_column(ForeignKey("relationships.id", ondelete="CASCADE"), nullable=False)
    decision: Mapped[str] = mapped_column(String(30), nullable=False)
    reviewer: Mapped[str] = mapped_column(String(200), nullable=False)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    previous_status: Mapped[str] = mapped_column(String(50), nullable=False)
    resulting_status: Mapped[str] = mapped_column(String(50), nullable=False)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

class EvidenceFoundation(Base):
    __tablename__ = "evidence_foundations"
    __table_args__ = (Index("ix_evidence_subject", "subject_entity_id"), Index("ix_evidence_source", "source_entity_id"), Index("ix_evidence_review_status", "review_status"))
    id: Mapped[str] = mapped_column(String(255), primary_key=True, default=lambda: f"sc:evidence:{uuid.uuid4()}")
    evidence_type: Mapped[str] = mapped_column(String(100), nullable=False)
    subject_entity_id: Mapped[str | None] = mapped_column(ForeignKey("entities.id", ondelete="SET NULL"), nullable=True)
    source_entity_id: Mapped[str | None] = mapped_column(ForeignKey("entities.id", ondelete="SET NULL"), nullable=True)
    methodology: Mapped[str | None] = mapped_column(Text, nullable=True)
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    review_status: Mapped[str] = mapped_column(String(50), default="unreviewed")
    provenance: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

class ValidationEvent(Base):
    __tablename__ = "validation_events"
    __table_args__ = (Index("ix_validation_component_status", "component", "status"), Index("ix_validation_entity", "entity_id"), Index("ix_validation_observed", "observed_at"))
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    entity_id: Mapped[str | None] = mapped_column(ForeignKey("entities.id", ondelete="SET NULL"), nullable=True)
    component: Mapped[str] = mapped_column(String(150), nullable=False)
    check_name: Mapped[str] = mapped_column(String(200), nullable=False)
    status: Mapped[str] = mapped_column(String(30), nullable=False)
    severity: Mapped[str] = mapped_column(String(30), default="info")
    details: Mapped[dict] = mapped_column(JSON, default=dict)
    observed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

class ImportJob(Base):
    __tablename__ = "import_jobs"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    adapter: Mapped[str] = mapped_column(String(100), nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="running")
    source_name: Mapped[str | None] = mapped_column(String(300), nullable=True)
    entities_received: Mapped[int] = mapped_column(Integer, default=0)
    entities_created: Mapped[int] = mapped_column(Integer, default=0)
    entities_updated: Mapped[int] = mapped_column(Integer, default=0)
    relationships_received: Mapped[int] = mapped_column(Integer, default=0)
    relationships_created: Mapped[int] = mapped_column(Integer, default=0)
    relationships_skipped: Mapped[int] = mapped_column(Integer, default=0)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    details: Mapped[dict] = mapped_column(JSON, default=dict)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

class SchemaMigration(Base):
    __tablename__ = "schema_migrations"
    version: Mapped[str] = mapped_column(String(50), primary_key=True)
    description: Mapped[str] = mapped_column(String(300), nullable=False)
    applied_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class ClaimRecord(Base):
    __tablename__ = "claim_records"
    __table_args__ = (
        Index("ix_claim_subject_status", "subject_entity_id", "status"),
        Index("ix_claim_visibility_created", "visibility", "created_at"),
    )
    id: Mapped[str] = mapped_column(
        String(255), primary_key=True,
        default=lambda: f"sc:claim:{uuid.uuid4()}"
    )
    claim_text: Mapped[str] = mapped_column(Text, nullable=False)
    claim_type: Mapped[str] = mapped_column(String(100), default="factual")
    subject_entity_id: Mapped[str | None] = mapped_column(
        ForeignKey("entities.id", ondelete="SET NULL"), nullable=True
    )
    status: Mapped[str] = mapped_column(String(50), default="draft", index=True)
    visibility: Mapped[str] = mapped_column(String(30), default="public", index=True)
    language: Mapped[str] = mapped_column(String(20), default="en")
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow
    )


class SourceSnapshot(Base):
    __tablename__ = "source_snapshots"
    __table_args__ = (
        Index("ix_snapshot_source_retrieved", "source_entity_id", "retrieved_at"),
        Index("ix_snapshot_hash", "content_hash"),
    )
    id: Mapped[str] = mapped_column(
        String(255), primary_key=True,
        default=lambda: f"sc:snapshot:{uuid.uuid4()}"
    )
    source_entity_id: Mapped[str | None] = mapped_column(
        ForeignKey("entities.id", ondelete="SET NULL"), nullable=True
    )
    canonical_url: Mapped[str | None] = mapped_column(String(2000), nullable=True)
    title: Mapped[str | None] = mapped_column(String(500), nullable=True)
    publisher: Mapped[str | None] = mapped_column(String(300), nullable=True)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    retrieved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    media_type: Mapped[str] = mapped_column(String(150), default="text/html")
    content_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    content_length: Mapped[int | None] = mapped_column(Integer, nullable=True)
    content_excerpt: Mapped[str | None] = mapped_column(Text, nullable=True)
    storage_uri: Mapped[str | None] = mapped_column(String(2000), nullable=True)
    archived_url: Mapped[str | None] = mapped_column(String(2000), nullable=True)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class ProvenanceActivity(Base):
    __tablename__ = "provenance_activities"
    __table_args__ = (
        Index("ix_activity_type_status", "activity_type", "status"),
        Index("ix_activity_started", "started_at"),
    )
    id: Mapped[str] = mapped_column(
        String(255), primary_key=True,
        default=lambda: f"sc:activity:{uuid.uuid4()}"
    )
    activity_type: Mapped[str] = mapped_column(String(100), nullable=False)
    name: Mapped[str] = mapped_column(String(300), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    agent: Mapped[str] = mapped_column(String(300), nullable=False)
    software_entity_id: Mapped[str | None] = mapped_column(
        ForeignKey("entities.id", ondelete="SET NULL"), nullable=True
    )
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    parameters: Mapped[dict] = mapped_column(JSON, default=dict)
    environment: Mapped[dict] = mapped_column(JSON, default=dict)
    status: Mapped[str] = mapped_column(String(50), default="completed")
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class CalculationTrace(Base):
    __tablename__ = "calculation_traces"
    __table_args__ = (
        Index("ix_trace_tool_created", "tool_entity_id", "created_at"),
        Index("ix_trace_activity", "activity_id"),
        Index("ix_trace_hash", "content_hash"),
    )
    id: Mapped[str] = mapped_column(
        String(255), primary_key=True,
        default=lambda: f"sc:trace:{uuid.uuid4()}"
    )
    tool_entity_id: Mapped[str] = mapped_column(
        ForeignKey("entities.id", ondelete="RESTRICT"), nullable=False
    )
    subject_entity_id: Mapped[str | None] = mapped_column(
        ForeignKey("entities.id", ondelete="SET NULL"), nullable=True
    )
    activity_id: Mapped[str | None] = mapped_column(
        ForeignKey("provenance_activities.id", ondelete="SET NULL"), nullable=True
    )
    run_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    inputs: Mapped[dict] = mapped_column(JSON, default=dict)
    outputs: Mapped[dict] = mapped_column(JSON, default=dict)
    formula_version: Mapped[str | None] = mapped_column(String(100), nullable=True)
    code_version: Mapped[str | None] = mapped_column(String(100), nullable=True)
    runtime: Mapped[dict] = mapped_column(JSON, default=dict)
    status: Mapped[str] = mapped_column(String(50), default="completed")
    content_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class EvidenceRecord(Base):
    __tablename__ = "evidence_records"
    __table_args__ = (
        Index("ix_evidence_record_claim_review", "claim_id", "review_status"),
        Index("ix_evidence_record_subject", "subject_entity_id"),
        Index("ix_evidence_record_snapshot", "source_snapshot_id"),
        Index("ix_evidence_record_trace", "calculation_trace_id"),
    )
    id: Mapped[str] = mapped_column(
        String(255), primary_key=True,
        default=lambda: f"sc:evidence:{uuid.uuid4()}"
    )
    evidence_type: Mapped[str] = mapped_column(String(100), nullable=False)
    stance: Mapped[str] = mapped_column(String(50), default="contextualizes")
    claim_id: Mapped[str | None] = mapped_column(
        ForeignKey("claim_records.id", ondelete="SET NULL"), nullable=True
    )
    subject_entity_id: Mapped[str | None] = mapped_column(
        ForeignKey("entities.id", ondelete="SET NULL"), nullable=True
    )
    source_entity_id: Mapped[str | None] = mapped_column(
        ForeignKey("entities.id", ondelete="SET NULL"), nullable=True
    )
    source_snapshot_id: Mapped[str | None] = mapped_column(
        ForeignKey("source_snapshots.id", ondelete="SET NULL"), nullable=True
    )
    relationship_id: Mapped[str | None] = mapped_column(
        ForeignKey("relationships.id", ondelete="SET NULL"), nullable=True
    )
    calculation_trace_id: Mapped[str | None] = mapped_column(
        ForeignKey("calculation_traces.id", ondelete="SET NULL"), nullable=True
    )
    statement: Mapped[str | None] = mapped_column(Text, nullable=True)
    methodology: Mapped[str | None] = mapped_column(Text, nullable=True)
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    review_status: Mapped[str] = mapped_column(String(50), default="unreviewed", index=True)
    provenance: Mapped[dict] = mapped_column(JSON, default=dict)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow
    )


class EvidenceReview(Base):
    __tablename__ = "evidence_reviews"
    __table_args__ = (
        Index("ix_evidence_review_record_created", "evidence_id", "created_at"),
        Index("ix_evidence_review_decision", "decision"),
    )
    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    evidence_id: Mapped[str] = mapped_column(
        ForeignKey("evidence_records.id", ondelete="CASCADE"), nullable=False
    )
    decision: Mapped[str] = mapped_column(String(30), nullable=False)
    reviewer: Mapped[str] = mapped_column(String(200), nullable=False)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    previous_status: Mapped[str] = mapped_column(String(50), nullable=False)
    resulting_status: Mapped[str] = mapped_column(String(50), nullable=False)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class EvidenceReviewAssignment(Base):
    __tablename__ = "evidence_review_assignments"
    __table_args__ = (
        Index("ix_assignment_evidence_status", "evidence_id", "status"),
        Index("ix_assignment_assignee_status", "assignee", "status"),
    )
    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    evidence_id: Mapped[str] = mapped_column(
        ForeignKey("evidence_records.id", ondelete="CASCADE"), nullable=False
    )
    assignee: Mapped[str] = mapped_column(String(200), nullable=False)
    assigned_by: Mapped[str] = mapped_column(String(200), nullable=False)
    instructions: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(30), default="open")
    due_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class ProvenanceLink(Base):
    __tablename__ = "provenance_links"
    __table_args__ = (
        UniqueConstraint(
            "activity_id", "role", "object_type", "object_id",
            name="uq_provenance_activity_role_object"
        ),
        Index("ix_provenance_object", "object_type", "object_id"),
    )
    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    activity_id: Mapped[str] = mapped_column(
        ForeignKey("provenance_activities.id", ondelete="CASCADE"), nullable=False
    )
    role: Mapped[str] = mapped_column(String(50), nullable=False)
    object_type: Mapped[str] = mapped_column(String(100), nullable=False)
    object_id: Mapped[str] = mapped_column(String(255), nullable=False)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class LedgerEntry(Base):
    __tablename__ = "ledger_entries"
    __table_args__ = (
        UniqueConstraint("id", name="uq_ledger_entry_id"),
        UniqueConstraint("entry_hash", name="uq_ledger_entry_hash"),
        Index("ix_ledger_record", "record_type", "record_id"),
        Index("ix_ledger_created", "created_at"),
    )
    sequence: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    id: Mapped[str] = mapped_column(
        String(36), nullable=False, default=lambda: str(uuid.uuid4())
    )
    record_type: Mapped[str] = mapped_column(String(100), nullable=False)
    record_id: Mapped[str] = mapped_column(String(255), nullable=False)
    action: Mapped[str] = mapped_column(String(100), nullable=False)
    actor: Mapped[str] = mapped_column(String(300), nullable=False)
    payload_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    previous_entry_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    entry_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    payload_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


@event.listens_for(LedgerEntry, "before_update")
def _prevent_ledger_update(mapper, connection, target):
    raise RuntimeError("Ledger entries are append-only and cannot be updated.")


@event.listens_for(LedgerEntry, "before_delete")
def _prevent_ledger_delete(mapper, connection, target):
    raise RuntimeError("Ledger entries are append-only and cannot be deleted.")
