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


class ApiPlan(Base):
    __tablename__ = "api_plans"
    __table_args__ = (
        Index("ix_api_plan_public_active", "public", "active"),
        Index("ix_api_plan_sort", "sort_order", "name"),
    )

    id: Mapped[str] = mapped_column(String(100), primary_key=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    requests_per_minute: Mapped[int] = mapped_column(Integer, default=60)
    requests_per_day: Mapped[int] = mapped_column(Integer, default=5000)
    max_page_size: Mapped[int] = mapped_column(Integer, default=100)
    allowed_scopes: Mapped[list] = mapped_column(JSON, default=list)
    public: Mapped[bool] = mapped_column(Boolean, default=True)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=100)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow
    )


class DeveloperApplication(Base):
    __tablename__ = "developer_applications"
    __table_args__ = (
        Index("ix_developer_application_status", "status"),
        Index("ix_developer_application_owner_email", "owner_email"),
    )

    id: Mapped[str] = mapped_column(
        String(255),
        primary_key=True,
        default=lambda: f"sc:developer-app:{uuid.uuid4()}",
    )
    name: Mapped[str] = mapped_column(String(300), nullable=False)
    owner_name: Mapped[str] = mapped_column(String(300), nullable=False)
    owner_email: Mapped[str] = mapped_column(String(500), nullable=False)
    organization: Mapped[str | None] = mapped_column(String(500), nullable=True)
    website_url: Mapped[str | None] = mapped_column(String(2000), nullable=True)
    use_case: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="pending", index=True)
    plan_id: Mapped[str] = mapped_column(
        ForeignKey("api_plans.id", ondelete="RESTRICT"), nullable=False
    )
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow
    )


class ApiCredential(Base):
    __tablename__ = "api_credentials"
    __table_args__ = (
        UniqueConstraint("key_hash", name="uq_api_credential_key_hash"),
        Index("ix_api_credential_application_status", "application_id", "status"),
        Index("ix_api_credential_prefix", "key_prefix"),
    )

    id: Mapped[str] = mapped_column(
        String(255),
        primary_key=True,
        default=lambda: f"sc:api-credential:{uuid.uuid4()}",
    )
    application_id: Mapped[str] = mapped_column(
        ForeignKey("developer_applications.id", ondelete="CASCADE"),
        nullable=False,
    )
    label: Mapped[str] = mapped_column(String(300), nullable=False)
    key_prefix: Mapped[str] = mapped_column(String(32), nullable=False)
    key_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    key_last_four: Mapped[str] = mapped_column(String(4), nullable=False)
    scopes: Mapped[list] = mapped_column(JSON, default=list)
    status: Mapped[str] = mapped_column(String(30), default="active", index=True)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_by: Mapped[str] = mapped_column(String(300), nullable=False)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class ApiRequestLog(Base):
    __tablename__ = "api_request_logs"
    __table_args__ = (
        Index("ix_api_log_credential_created", "credential_id", "created_at"),
        Index("ix_api_log_application_created", "application_id", "created_at"),
        Index("ix_api_log_path_created", "path", "created_at"),
        Index("ix_api_log_request_id", "request_id"),
    )

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    request_id: Mapped[str] = mapped_column(String(64), nullable=False)
    credential_id: Mapped[str | None] = mapped_column(
        ForeignKey("api_credentials.id", ondelete="SET NULL"), nullable=True
    )
    application_id: Mapped[str | None] = mapped_column(
        ForeignKey("developer_applications.id", ondelete="SET NULL"), nullable=True
    )
    method: Mapped[str] = mapped_column(String(20), nullable=False)
    path: Mapped[str] = mapped_column(String(1000), nullable=False)
    query_string: Mapped[str | None] = mapped_column(Text, nullable=True)
    status_code: Mapped[int] = mapped_column(Integer, nullable=False)
    required_scope: Mapped[str | None] = mapped_column(String(150), nullable=True)
    ip_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    user_agent_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    duration_ms: Mapped[float] = mapped_column(Float, nullable=False)
    response_bytes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class WebhookSubscription(Base):
    __tablename__ = "webhook_subscriptions"
    __table_args__ = (
        Index("ix_webhook_subscription_application_status", "application_id", "status"),
    )

    id: Mapped[str] = mapped_column(
        String(255),
        primary_key=True,
        default=lambda: f"sc:webhook-subscription:{uuid.uuid4()}",
    )
    application_id: Mapped[str] = mapped_column(
        ForeignKey("developer_applications.id", ondelete="CASCADE"),
        nullable=False,
    )
    callback_url: Mapped[str] = mapped_column(String(2000), nullable=False)
    event_types: Mapped[list] = mapped_column(JSON, default=list)
    status: Mapped[str] = mapped_column(String(30), default="active", index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_by_credential_id: Mapped[str] = mapped_column(
        ForeignKey("api_credentials.id", ondelete="RESTRICT"),
        nullable=False,
    )
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow
    )


class WebhookEvent(Base):
    __tablename__ = "webhook_events"
    __table_args__ = (
        Index("ix_webhook_event_status_created", "status", "created_at"),
        Index("ix_webhook_event_resource", "resource_type", "resource_id"),
    )

    id: Mapped[str] = mapped_column(
        String(255),
        primary_key=True,
        default=lambda: f"sc:webhook-event:{uuid.uuid4()}",
    )
    event_type: Mapped[str] = mapped_column(String(150), nullable=False, index=True)
    resource_type: Mapped[str] = mapped_column(String(100), nullable=False)
    resource_id: Mapped[str] = mapped_column(String(255), nullable=False)
    payload_json: Mapped[dict] = mapped_column(JSON, default=dict)
    status: Mapped[str] = mapped_column(String(30), default="pending", index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    processed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class WebhookDelivery(Base):
    __tablename__ = "webhook_deliveries"
    __table_args__ = (
        UniqueConstraint(
            "subscription_id", "event_id",
            name="uq_webhook_delivery_subscription_event",
        ),
        Index("ix_webhook_delivery_status_created", "status", "created_at"),
    )

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    subscription_id: Mapped[str] = mapped_column(
        ForeignKey("webhook_subscriptions.id", ondelete="CASCADE"),
        nullable=False,
    )
    event_id: Mapped[str] = mapped_column(
        ForeignKey("webhook_events.id", ondelete="CASCADE"),
        nullable=False,
    )
    status: Mapped[str] = mapped_column(String(30), default="pending", index=True)
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    http_status: Mapped[int | None] = mapped_column(Integer, nullable=True)
    response_excerpt: Mapped[str | None] = mapped_column(Text, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    signature: Mapped[str | None] = mapped_column(String(128), nullable=True)
    attempted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    delivered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class EvaluationDefinition(Base):
    __tablename__ = "evaluation_definitions"
    __table_args__ = (
        Index("ix_evaluation_definition_domain_active", "domain", "active"),
        Index("ix_evaluation_definition_public_sort", "public", "sort_order"),
    )
    id: Mapped[str] = mapped_column(String(150), primary_key=True)
    name: Mapped[str] = mapped_column(String(300), nullable=False)
    domain: Mapped[str] = mapped_column(String(150), nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    methodology: Mapped[str] = mapped_column(Text, nullable=False)
    evaluator_kind: Mapped[str] = mapped_column(String(150), nullable=False)
    target_type: Mapped[str] = mapped_column(String(100), default="platform")
    thresholds: Mapped[dict] = mapped_column(JSON, default=dict)
    cadence: Mapped[str | None] = mapped_column(String(100), nullable=True)
    severity_on_failure: Mapped[str] = mapped_column(String(30), default="medium")
    public: Mapped[bool] = mapped_column(Boolean, default=True)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    version: Mapped[str] = mapped_column(String(50), default="1.0")
    sort_order: Mapped[int] = mapped_column(Integer, default=100)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)


class EvaluationRun(Base):
    __tablename__ = "evaluation_runs"
    __table_args__ = (
        Index("ix_evaluation_run_definition_completed", "definition_id", "completed_at"),
        Index("ix_evaluation_run_target_completed", "target_entity_id", "completed_at"),
        Index("ix_evaluation_run_status_grade", "status", "grade"),
        Index("ix_evaluation_run_public_completed", "public", "completed_at"),
    )
    id: Mapped[str] = mapped_column(String(255), primary_key=True, default=lambda: f"sc:evaluation-run:{uuid.uuid4()}")
    definition_id: Mapped[str] = mapped_column(ForeignKey("evaluation_definitions.id", ondelete="RESTRICT"), nullable=False)
    target_entity_id: Mapped[str | None] = mapped_column(ForeignKey("entities.id", ondelete="SET NULL"), nullable=True)
    status: Mapped[str] = mapped_column(String(30), nullable=False)
    score: Mapped[float | None] = mapped_column(Float, nullable=True)
    grade: Mapped[str] = mapped_column(String(30), nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    triggered_by: Mapped[str] = mapped_column(String(300), nullable=False)
    evaluator_version: Mapped[str] = mapped_column(String(100), nullable=False)
    observations: Mapped[dict] = mapped_column(JSON, default=dict)
    environment: Mapped[dict] = mapped_column(JSON, default=dict)
    evidence_references: Mapped[list] = mapped_column(JSON, default=list)
    content_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    public: Mapped[bool] = mapped_column(Boolean, default=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    completed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class EvaluationCheckResult(Base):
    __tablename__ = "evaluation_check_results"
    __table_args__ = (
        UniqueConstraint("run_id", "check_key", name="uq_evaluation_run_check"),
        Index("ix_evaluation_check_run_status", "run_id", "status"),
        Index("ix_evaluation_check_severity", "severity"),
    )
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    run_id: Mapped[str] = mapped_column(ForeignKey("evaluation_runs.id", ondelete="CASCADE"), nullable=False)
    check_key: Mapped[str] = mapped_column(String(150), nullable=False)
    name: Mapped[str] = mapped_column(String(300), nullable=False)
    status: Mapped[str] = mapped_column(String(30), nullable=False)
    score: Mapped[float | None] = mapped_column(Float, nullable=True)
    severity: Mapped[str] = mapped_column(String(30), default="info")
    observed: Mapped[dict] = mapped_column(JSON, default=dict)
    expected: Mapped[dict] = mapped_column(JSON, default=dict)
    details: Mapped[dict] = mapped_column(JSON, default=dict)
    evidence_references: Mapped[list] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class TrustFinding(Base):
    __tablename__ = "trust_findings"
    __table_args__ = (
        Index("ix_trust_finding_status_severity", "status", "severity"),
        Index("ix_trust_finding_run", "evaluation_run_id"),
        Index("ix_trust_finding_public", "public", "created_at"),
    )
    id: Mapped[str] = mapped_column(String(255), primary_key=True, default=lambda: f"sc:trust-finding:{uuid.uuid4()}")
    evaluation_run_id: Mapped[str | None] = mapped_column(ForeignKey("evaluation_runs.id", ondelete="SET NULL"), nullable=True)
    check_result_id: Mapped[str | None] = mapped_column(ForeignKey("evaluation_check_results.id", ondelete="SET NULL"), nullable=True)
    target_entity_id: Mapped[str | None] = mapped_column(ForeignKey("entities.id", ondelete="SET NULL"), nullable=True)
    finding_type: Mapped[str] = mapped_column(String(100), default="evaluation")
    severity: Mapped[str] = mapped_column(String(30), nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="open")
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    remediation: Mapped[str | None] = mapped_column(Text, nullable=True)
    owner: Mapped[str | None] = mapped_column(String(300), nullable=True)
    due_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    public: Mapped[bool] = mapped_column(Boolean, default=True)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)


class TrustIncident(Base):
    __tablename__ = "trust_incidents"
    __table_args__ = (
        Index("ix_trust_incident_status_severity", "status", "severity"),
        Index("ix_trust_incident_public_started", "public", "started_at"),
    )
    id: Mapped[str] = mapped_column(String(255), primary_key=True, default=lambda: f"sc:trust-incident:{uuid.uuid4()}")
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    severity: Mapped[str] = mapped_column(String(30), nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="investigating")
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    impact: Mapped[str | None] = mapped_column(Text, nullable=True)
    root_cause: Mapped[str | None] = mapped_column(Text, nullable=True)
    remediation: Mapped[str | None] = mapped_column(Text, nullable=True)
    affected_entity_ids: Mapped[list] = mapped_column(JSON, default=list)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    detected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    public: Mapped[bool] = mapped_column(Boolean, default=True)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)


class KnownLimitation(Base):
    __tablename__ = "known_limitations"
    __table_args__ = (
        Index("ix_limitation_domain_status", "domain", "status"),
        Index("ix_limitation_public_review", "public", "review_after"),
    )
    id: Mapped[str] = mapped_column(String(255), primary_key=True, default=lambda: f"sc:limitation:{uuid.uuid4()}")
    domain: Mapped[str] = mapped_column(String(150), nullable=False)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    impact: Mapped[str | None] = mapped_column(Text, nullable=True)
    mitigation: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(30), default="active")
    affected_entity_ids: Mapped[list] = mapped_column(JSON, default=list)
    review_after: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    public: Mapped[bool] = mapped_column(Boolean, default=True)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)


class TrustAttestation(Base):
    __tablename__ = "trust_attestations"
    __table_args__ = (
        Index("ix_attestation_subject_status", "subject_entity_id", "status"),
        Index("ix_attestation_public_valid", "public", "valid_until"),
    )
    id: Mapped[str] = mapped_column(String(255), primary_key=True, default=lambda: f"sc:attestation:{uuid.uuid4()}")
    subject_entity_id: Mapped[str | None] = mapped_column(ForeignKey("entities.id", ondelete="SET NULL"), nullable=True)
    statement: Mapped[str] = mapped_column(Text, nullable=False)
    scope: Mapped[str] = mapped_column(String(300), nullable=False)
    issuer: Mapped[str] = mapped_column(String(300), nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="active")
    evidence_references: Mapped[list] = mapped_column(JSON, default=list)
    valid_from: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    valid_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    revocation_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    content_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    public: Mapped[bool] = mapped_column(Boolean, default=True)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


@event.listens_for(EvaluationRun, "before_update")
def _prevent_evaluation_run_update(mapper, connection, target):
    raise RuntimeError("Evaluation runs are immutable and cannot be updated.")


@event.listens_for(EvaluationRun, "before_delete")
def _prevent_evaluation_run_delete(mapper, connection, target):
    raise RuntimeError("Evaluation runs are immutable and cannot be deleted.")


@event.listens_for(EvaluationCheckResult, "before_update")
def _prevent_evaluation_check_update(mapper, connection, target):
    raise RuntimeError("Evaluation check results are immutable and cannot be updated.")


@event.listens_for(EvaluationCheckResult, "before_delete")
def _prevent_evaluation_check_delete(mapper, connection, target):
    raise RuntimeError("Evaluation check results are immutable and cannot be deleted.")

class WorkflowDefinition(Base):
    __tablename__ = "workflow_definitions"
    __table_args__ = (
        Index("ix_workflow_definition_active_public", "active", "public"),
        Index("ix_workflow_definition_sort", "sort_order", "name"),
    )
    id: Mapped[str] = mapped_column(String(150), primary_key=True)
    name: Mapped[str] = mapped_column(String(300), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    version: Mapped[str] = mapped_column(String(50), default="1.0")
    stages: Mapped[list] = mapped_column(JSON, default=list)
    public: Mapped[bool] = mapped_column(Boolean, default=True)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=100)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)


class WorkflowRun(Base):
    __tablename__ = "workflow_runs"
    __table_args__ = (
        Index("ix_workflow_run_definition_status", "definition_id", "status"),
        Index("ix_workflow_run_subject_status", "subject_entity_id", "status"),
        Index("ix_workflow_run_public_created", "public", "created_at"),
    )
    id: Mapped[str] = mapped_column(String(255), primary_key=True, default=lambda: f"sc:workflow-run:{uuid.uuid4()}")
    definition_id: Mapped[str] = mapped_column(ForeignKey("workflow_definitions.id", ondelete="RESTRICT"), nullable=False)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    subject_entity_id: Mapped[str | None] = mapped_column(ForeignKey("entities.id", ondelete="SET NULL"), nullable=True)
    status: Mapped[str] = mapped_column(String(30), default="draft", index=True)
    current_step_key: Mapped[str | None] = mapped_column(String(150), nullable=True)
    requested_by: Mapped[str] = mapped_column(String(300), nullable=False)
    owner: Mapped[str | None] = mapped_column(String(300), nullable=True)
    context_json: Mapped[dict] = mapped_column(JSON, default=dict)
    content_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    public: Mapped[bool] = mapped_column(Boolean, default=False)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)


class WorkflowStep(Base):
    __tablename__ = "workflow_steps"
    __table_args__ = (
        UniqueConstraint("run_id", "step_key", name="uq_workflow_run_step"),
        Index("ix_workflow_step_run_sequence", "run_id", "sequence"),
        Index("ix_workflow_step_status_product", "status", "product"),
    )
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    run_id: Mapped[str] = mapped_column(ForeignKey("workflow_runs.id", ondelete="CASCADE"), nullable=False)
    step_key: Mapped[str] = mapped_column(String(150), nullable=False)
    name: Mapped[str] = mapped_column(String(300), nullable=False)
    sequence: Mapped[int] = mapped_column(Integer, nullable=False)
    product: Mapped[str] = mapped_column(String(150), nullable=False)
    action: Mapped[str] = mapped_column(String(150), nullable=False)
    required: Mapped[bool] = mapped_column(Boolean, default=True)
    status: Mapped[str] = mapped_column(String(30), default="pending", index=True)
    assigned_to: Mapped[str | None] = mapped_column(String(300), nullable=True)
    input_references: Mapped[list] = mapped_column(JSON, default=list)
    output_references: Mapped[list] = mapped_column(JSON, default=list)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    due_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)


class WorkflowTransition(Base):
    __tablename__ = "workflow_transitions"
    __table_args__ = (
        Index("ix_workflow_transition_run_created", "run_id", "created_at"),
        Index("ix_workflow_transition_step_created", "step_id", "created_at"),
    )
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    run_id: Mapped[str] = mapped_column(ForeignKey("workflow_runs.id", ondelete="CASCADE"), nullable=False)
    step_id: Mapped[str | None] = mapped_column(ForeignKey("workflow_steps.id", ondelete="SET NULL"), nullable=True)
    from_status: Mapped[str | None] = mapped_column(String(30), nullable=True)
    to_status: Mapped[str] = mapped_column(String(30), nullable=False)
    actor: Mapped[str] = mapped_column(String(300), nullable=False)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    payload_json: Mapped[dict] = mapped_column(JSON, default=dict)
    content_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class SignatureDossier(Base):
    __tablename__ = "signature_dossiers"
    __table_args__ = (
        Index("ix_dossier_status_visibility", "status", "visibility"),
        Index("ix_dossier_workflow", "workflow_run_id"),
        Index("ix_dossier_subject", "subject_entity_id"),
        UniqueConstraint("dossier_hash", name="uq_signature_dossier_hash"),
    )
    id: Mapped[str] = mapped_column(String(255), primary_key=True, default=lambda: f"sc:dossier:{uuid.uuid4()}")
    workflow_run_id: Mapped[str | None] = mapped_column(ForeignKey("workflow_runs.id", ondelete="SET NULL"), nullable=True)
    subject_entity_id: Mapped[str | None] = mapped_column(ForeignKey("entities.id", ondelete="SET NULL"), nullable=True)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    purpose: Mapped[str] = mapped_column(Text, nullable=False)
    version: Mapped[str] = mapped_column(String(50), default="1.0")
    status: Mapped[str] = mapped_column(String(30), default="draft", index=True)
    visibility: Mapped[str] = mapped_column(String(30), default="private", index=True)
    dossier_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    signature_algorithm: Mapped[str | None] = mapped_column(String(100), nullable=True)
    platform_signature: Mapped[str | None] = mapped_column(String(128), nullable=True)
    signing_key_id: Mapped[str | None] = mapped_column(String(200), nullable=True)
    signed_by: Mapped[str | None] = mapped_column(String(300), nullable=True)
    signed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    snapshot_json: Mapped[dict] = mapped_column(JSON, default=dict)
    supersedes_dossier_id: Mapped[str | None] = mapped_column(ForeignKey("signature_dossiers.id", ondelete="SET NULL"), nullable=True)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)


class DossierRecord(Base):
    __tablename__ = "dossier_records"
    __table_args__ = (
        UniqueConstraint("dossier_id", "record_type", "record_id", name="uq_dossier_record"),
        Index("ix_dossier_record_section_order", "dossier_id", "section", "sort_order"),
    )
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    dossier_id: Mapped[str] = mapped_column(ForeignKey("signature_dossiers.id", ondelete="CASCADE"), nullable=False)
    section: Mapped[str] = mapped_column(String(150), nullable=False)
    record_type: Mapped[str] = mapped_column(String(100), nullable=False)
    record_id: Mapped[str] = mapped_column(String(255), nullable=False)
    label: Mapped[str | None] = mapped_column(String(500), nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=100)
    snapshot_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    snapshot_json: Mapped[dict] = mapped_column(JSON, default=dict)
    public: Mapped[bool] = mapped_column(Boolean, default=True)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class DossierApproval(Base):
    __tablename__ = "dossier_approvals"
    __table_args__ = (
        Index("ix_dossier_approval_dossier_created", "dossier_id", "created_at"),
        Index("ix_dossier_approval_decision", "decision"),
    )
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    dossier_id: Mapped[str] = mapped_column(ForeignKey("signature_dossiers.id", ondelete="CASCADE"), nullable=False)
    decision: Mapped[str] = mapped_column(String(30), nullable=False)
    signer: Mapped[str] = mapped_column(String(300), nullable=False)
    role: Mapped[str] = mapped_column(String(200), nullable=False)
    statement: Mapped[str | None] = mapped_column(Text, nullable=True)
    evidence_references: Mapped[list] = mapped_column(JSON, default=list)
    content_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


@event.listens_for(WorkflowTransition, "before_update")
def _prevent_workflow_transition_update(mapper, connection, target):
    raise RuntimeError("Workflow transitions are append-only and cannot be updated.")


@event.listens_for(WorkflowTransition, "before_delete")
def _prevent_workflow_transition_delete(mapper, connection, target):
    raise RuntimeError("Workflow transitions are append-only and cannot be deleted.")


@event.listens_for(DossierRecord, "before_update")
def _prevent_dossier_record_update(mapper, connection, target):
    raise RuntimeError("Dossier record snapshots are immutable and cannot be updated.")


@event.listens_for(DossierApproval, "before_update")
def _prevent_dossier_approval_update(mapper, connection, target):
    raise RuntimeError("Dossier approvals are append-only and cannot be updated.")


@event.listens_for(DossierApproval, "before_delete")
def _prevent_dossier_approval_delete(mapper, connection, target):
    raise RuntimeError("Dossier approvals are append-only and cannot be deleted.")


class LiveDataSource(Base):
    __tablename__ = "live_data_sources"
    __table_args__ = (
        Index("ix_live_source_review_active", "review_status", "active"),
        Index("ix_live_source_public_name", "public", "name"),
    )

    id: Mapped[str] = mapped_column(String(150), primary_key=True)
    name: Mapped[str] = mapped_column(String(300), nullable=False)
    organization: Mapped[str] = mapped_column(String(300), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    homepage_url: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    documentation_url: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    license_name: Mapped[str | None] = mapped_column(String(300), nullable=True)
    license_url: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    attribution: Mapped[str | None] = mapped_column(Text, nullable=True)
    access_cost: Mapped[str] = mapped_column(String(50), default="free", index=True)
    credit_card_required: Mapped[bool] = mapped_column(Boolean, default=False)
    api_key_requirement: Mapped[str] = mapped_column(String(50), default="none")
    commercial_use_status: Mapped[str] = mapped_column(String(100), default="review_required")
    redistribution_status: Mapped[str] = mapped_column(String(100), default="review_required")
    automated_access_status: Mapped[str] = mapped_column(String(100), default="allowed")
    rate_limit_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    review_status: Mapped[str] = mapped_column(String(80), default="LICENSE_REVIEW_REQUIRED", index=True)
    last_reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    public: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)


class LiveDataConnector(Base):
    __tablename__ = "live_data_connectors"
    __table_args__ = (
        Index("ix_live_connector_domain_status", "domain", "status"),
        Index("ix_live_connector_source_enabled", "source_id", "enabled"),
        Index("ix_live_connector_health", "last_health_status", "last_health_checked_at"),
    )

    id: Mapped[str] = mapped_column(String(180), primary_key=True)
    source_id: Mapped[str] = mapped_column(
        ForeignKey("live_data_sources.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(300), nullable=False)
    domain: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    adapter: Mapped[str] = mapped_column(String(180), nullable=False)
    base_url: Mapped[str] = mapped_column(String(1000), nullable=False)
    refresh_policy: Mapped[str] = mapped_column(String(100), default="manual")
    freshness_window_seconds: Mapped[int] = mapped_column(Integer, default=86400)
    timeout_seconds: Mapped[int] = mapped_column(Integer, default=20)
    max_response_bytes: Mapped[int] = mapped_column(Integer, default=5242880)
    schema_version: Mapped[str] = mapped_column(String(30), default="1.0")
    capabilities: Mapped[list] = mapped_column(JSON, default=list)
    configuration_json: Mapped[dict] = mapped_column(JSON, default=dict)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    public: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    status: Mapped[str] = mapped_column(String(50), default="active", index=True)
    last_health_status: Mapped[str] = mapped_column(String(50), default="unknown", index=True)
    last_health_checked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_success_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_failure_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)


class LiveDataIngestionRun(Base):
    __tablename__ = "live_data_ingestion_runs"
    __table_args__ = (
        Index("ix_live_run_connector_started", "connector_id", "started_at"),
        Index("ix_live_run_status_started", "status", "started_at"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    connector_id: Mapped[str] = mapped_column(
        ForeignKey("live_data_connectors.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    run_type: Mapped[str] = mapped_column(String(50), default="manual")
    status: Mapped[str] = mapped_column(String(50), default="running", index=True)
    requested_by: Mapped[str] = mapped_column(String(300), default="platform-core")
    parameters_json: Mapped[dict] = mapped_column(JSON, default=dict)
    http_status: Mapped[int | None] = mapped_column(Integer, nullable=True)
    records_received: Mapped[int] = mapped_column(Integer, default=0)
    records_created: Mapped[int] = mapped_column(Integer, default=0)
    records_updated: Mapped[int] = mapped_column(Integer, default=0)
    records_rejected: Mapped[int] = mapped_column(Integer, default=0)
    raw_content_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    details_json: Mapped[dict] = mapped_column(JSON, default=dict)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class LiveDataRawRecord(Base):
    __tablename__ = "live_data_raw_records"
    __table_args__ = (
        Index("ix_live_raw_connector_retrieved", "connector_id", "retrieved_at"),
        Index("ix_live_raw_hash", "content_hash"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    connector_id: Mapped[str] = mapped_column(
        ForeignKey("live_data_connectors.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    ingestion_run_id: Mapped[str] = mapped_column(
        ForeignKey("live_data_ingestion_runs.id", ondelete="CASCADE"), nullable=False, index=True
    )
    source_record_id: Mapped[str | None] = mapped_column(String(500), nullable=True)
    media_type: Mapped[str] = mapped_column(String(150), default="application/json")
    payload_json: Mapped[dict] = mapped_column(JSON, default=dict)
    content_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    size_bytes: Mapped[int] = mapped_column(Integer, default=0)
    truncated: Mapped[bool] = mapped_column(Boolean, default=False)
    retrieved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class LiveDataObservation(Base):
    __tablename__ = "live_data_observations"
    __table_args__ = (
        UniqueConstraint(
            "connector_id", "source_record_id", "metric", "observed_at",
            name="uq_live_observation_source_metric_time",
        ),
        Index("ix_live_observation_domain_metric_time", "domain", "metric", "observed_at"),
        Index("ix_live_observation_connector_time", "connector_id", "observed_at"),
        Index("ix_live_observation_source_time", "source_id", "observed_at"),
        Index("ix_live_observation_freshness", "freshness_status", "retrieved_at"),
        Index("ix_live_observation_public", "public", "observed_at"),
    )

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    connector_id: Mapped[str] = mapped_column(
        ForeignKey("live_data_connectors.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    source_id: Mapped[str] = mapped_column(
        ForeignKey("live_data_sources.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    raw_record_id: Mapped[str | None] = mapped_column(
        ForeignKey("live_data_raw_records.id", ondelete="SET NULL"), nullable=True, index=True
    )
    source_record_id: Mapped[str] = mapped_column(String(500), nullable=False)
    domain: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    metric: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    value_number: Mapped[float | None] = mapped_column(Float, nullable=True)
    value_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    unit: Mapped[str | None] = mapped_column(String(100), nullable=True)
    geometry_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    dimensions_json: Mapped[dict] = mapped_column(JSON, default=dict)
    observed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    retrieved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, index=True)
    freshness_status: Mapped[str] = mapped_column(String(50), default="unknown", index=True)
    quality_status: Mapped[str] = mapped_column(String(50), default="source_reported", index=True)
    license_name: Mapped[str | None] = mapped_column(String(300), nullable=True)
    attribution: Mapped[str | None] = mapped_column(Text, nullable=True)
    methodology_url: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    raw_record_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)
    public: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)


class ScientificDataRecord(Base):
    __tablename__ = "scientific_data_records"
    __table_args__ = (
        UniqueConstraint("connector_id", "source_record_id", "record_type", name="uq_scientific_data_source_type"),
        Index("ix_scientific_data_discipline_type", "discipline", "record_type"),
        Index("ix_scientific_data_collection_time", "collection", "observation_start"),
        Index("ix_scientific_data_mission_instrument", "mission", "instrument"),
        Index("ix_scientific_data_dataset", "dataset_id"),
        Index("ix_scientific_data_public", "public", "published_at"),
    )

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    connector_id: Mapped[str] = mapped_column(ForeignKey("live_data_connectors.id", ondelete="RESTRICT"), nullable=False, index=True)
    source_id: Mapped[str] = mapped_column(ForeignKey("live_data_sources.id", ondelete="RESTRICT"), nullable=False, index=True)
    raw_record_id: Mapped[str | None] = mapped_column(ForeignKey("live_data_raw_records.id", ondelete="SET NULL"), nullable=True, index=True)
    source_record_id: Mapped[str] = mapped_column(String(500), nullable=False)
    record_type: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    discipline: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    dataset_id: Mapped[str | None] = mapped_column(String(500), nullable=True, index=True)
    collection: Mapped[str | None] = mapped_column(String(500), nullable=True, index=True)
    mission: Mapped[str | None] = mapped_column(String(300), nullable=True, index=True)
    instrument: Mapped[str | None] = mapped_column(String(300), nullable=True, index=True)
    target: Mapped[str | None] = mapped_column(String(500), nullable=True, index=True)
    doi: Mapped[str | None] = mapped_column(String(500), nullable=True, index=True)
    access_url: Mapped[str | None] = mapped_column(String(2000), nullable=True)
    landing_page_url: Mapped[str | None] = mapped_column(String(2000), nullable=True)
    geometry_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    observation_start: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    observation_end: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    identifiers_json: Mapped[dict] = mapped_column(JSON, default=dict)
    keywords_json: Mapped[list] = mapped_column(JSON, default=list)
    variables_json: Mapped[list] = mapped_column(JSON, default=list)
    file_formats_json: Mapped[list] = mapped_column(JSON, default=list)
    quality_status: Mapped[str] = mapped_column(String(100), default="source_reported", index=True)
    license_name: Mapped[str | None] = mapped_column(String(300), nullable=True)
    attribution: Mapped[str | None] = mapped_column(Text, nullable=True)
    content_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)
    public: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

class EconomicDataRecord(Base):
    __tablename__ = "economic_data_records"
    __table_args__ = (
        UniqueConstraint("connector_id", "source_record_id", "record_type", name="uq_economic_data_source_type"),
        Index("ix_economic_data_subject_indicator", "subject", "indicator_code"),
        Index("ix_economic_data_geography_period", "geography_code", "period_start"),
        Index("ix_economic_data_dataset_period", "dataset_id", "period_start"),
        Index("ix_economic_data_frequency", "frequency", "period_start"),
        Index("ix_economic_data_public", "public", "published_at"),
    )

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    connector_id: Mapped[str] = mapped_column(ForeignKey("live_data_connectors.id", ondelete="RESTRICT"), nullable=False, index=True)
    source_id: Mapped[str] = mapped_column(ForeignKey("live_data_sources.id", ondelete="RESTRICT"), nullable=False, index=True)
    raw_record_id: Mapped[str | None] = mapped_column(ForeignKey("live_data_raw_records.id", ondelete="SET NULL"), nullable=True, index=True)
    source_record_id: Mapped[str] = mapped_column(String(700), nullable=False)
    record_type: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    subject: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    indicator_code: Mapped[str | None] = mapped_column(String(500), nullable=True, index=True)
    indicator_name: Mapped[str | None] = mapped_column(Text, nullable=True)
    dataset_id: Mapped[str | None] = mapped_column(String(500), nullable=True, index=True)
    geography_code: Mapped[str | None] = mapped_column(String(200), nullable=True, index=True)
    geography_name: Mapped[str | None] = mapped_column(String(500), nullable=True)
    counterpart_code: Mapped[str | None] = mapped_column(String(200), nullable=True, index=True)
    period: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    period_start: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    period_end: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    frequency: Mapped[str | None] = mapped_column(String(80), nullable=True, index=True)
    value_number: Mapped[float | None] = mapped_column(Float, nullable=True)
    value_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    unit: Mapped[str | None] = mapped_column(String(300), nullable=True)
    multiplier: Mapped[str | None] = mapped_column(String(100), nullable=True)
    seasonal_adjustment: Mapped[str | None] = mapped_column(String(200), nullable=True)
    price_basis: Mapped[str | None] = mapped_column(String(200), nullable=True)
    status: Mapped[str] = mapped_column(String(100), default="official_release", index=True)
    release_name: Mapped[str | None] = mapped_column(String(500), nullable=True)
    vintage_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    dimensions_json: Mapped[dict] = mapped_column(JSON, default=dict)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    source_url: Mapped[str | None] = mapped_column(String(2000), nullable=True)
    license_name: Mapped[str | None] = mapped_column(String(300), nullable=True)
    attribution: Mapped[str | None] = mapped_column(Text, nullable=True)
    content_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)
    public: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)


class InternationalLawRecord(Base):
    __tablename__ = "international_law_records"
    __table_args__ = (
        UniqueConstraint("connector_id", "source_record_id", "record_type", name="uq_international_law_source_type"),
        Index("ix_international_law_type_date", "record_type", "publication_date"),
        Index("ix_international_law_authority_date", "authority_level", "publication_date"),
        Index("ix_international_law_symbol", "official_symbol"),
        Index("ix_international_law_body", "legal_body", "publication_date"),
        Index("ix_international_law_public", "public", "publication_date"),
    )

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    connector_id: Mapped[str] = mapped_column(ForeignKey("live_data_connectors.id", ondelete="RESTRICT"), nullable=False, index=True)
    source_id: Mapped[str] = mapped_column(ForeignKey("live_data_sources.id", ondelete="RESTRICT"), nullable=False, index=True)
    raw_record_id: Mapped[str | None] = mapped_column(ForeignKey("live_data_raw_records.id", ondelete="SET NULL"), nullable=True, index=True)
    source_record_id: Mapped[str] = mapped_column(String(500), nullable=False)
    record_type: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    authority_level: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    official_symbol: Mapped[str | None] = mapped_column(String(500), nullable=True, index=True)
    issuing_body: Mapped[str | None] = mapped_column(String(500), nullable=True)
    legal_body: Mapped[str | None] = mapped_column(String(500), nullable=True, index=True)
    jurisdiction: Mapped[str] = mapped_column(String(120), default="international", index=True)
    legal_status: Mapped[str] = mapped_column(String(120), default="official_record", index=True)
    adoption_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    publication_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    entry_into_force_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    languages_json: Mapped[list] = mapped_column(JSON, default=list)
    countries_json: Mapped[list] = mapped_column(JSON, default=list)
    subjects_json: Mapped[list] = mapped_column(JSON, default=list)
    related_instruments_json: Mapped[list] = mapped_column(JSON, default=list)
    related_cases_json: Mapped[list] = mapped_column(JSON, default=list)
    related_resolutions_json: Mapped[list] = mapped_column(JSON, default=list)
    related_sdg_targets_json: Mapped[list] = mapped_column(JSON, default=list)
    canonical_source_url: Mapped[str | None] = mapped_column(String(2000), nullable=True)
    citation: Mapped[str | None] = mapped_column(Text, nullable=True)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    license_name: Mapped[str | None] = mapped_column(String(300), nullable=True)
    attribution: Mapped[str | None] = mapped_column(Text, nullable=True)
    content_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)
    public: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)



class GeospatialFeature(Base):
    __tablename__ = "geospatial_features"
    __table_args__ = (
        UniqueConstraint("source_id", "source_record_id", "feature_type", name="uq_geospatial_source_feature"),
        Index("ix_geospatial_feature_dataset_type", "dataset_id", "feature_type"),
        Index("ix_geospatial_feature_geometry_type", "geometry_type", "observed_at"),
        Index("ix_geospatial_feature_bbox", "min_x", "min_y", "max_x", "max_y"),
        Index("ix_geospatial_feature_public", "public", "observed_at"),
    )

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    source_id: Mapped[str] = mapped_column(ForeignKey("live_data_sources.id", ondelete="RESTRICT"), nullable=False, index=True)
    connector_id: Mapped[str | None] = mapped_column(ForeignKey("live_data_connectors.id", ondelete="SET NULL"), nullable=True, index=True)
    raw_record_id: Mapped[str | None] = mapped_column(ForeignKey("live_data_raw_records.id", ondelete="SET NULL"), nullable=True, index=True)
    observation_id: Mapped[str | None] = mapped_column(ForeignKey("live_data_observations.id", ondelete="SET NULL"), nullable=True, index=True)
    scientific_record_id: Mapped[str | None] = mapped_column(ForeignKey("scientific_data_records.id", ondelete="SET NULL"), nullable=True, index=True)
    source_record_id: Mapped[str] = mapped_column(String(700), nullable=False)
    dataset_id: Mapped[str | None] = mapped_column(String(500), nullable=True, index=True)
    collection_id: Mapped[str | None] = mapped_column(String(500), nullable=True, index=True)
    feature_type: Mapped[str] = mapped_column(String(150), default="observation", index=True)
    geometry_type: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    geometry_json: Mapped[dict] = mapped_column(JSON, nullable=False)
    bbox_json: Mapped[list] = mapped_column(JSON, default=list)
    min_x: Mapped[float | None] = mapped_column(Float, nullable=True)
    min_y: Mapped[float | None] = mapped_column(Float, nullable=True)
    max_x: Mapped[float | None] = mapped_column(Float, nullable=True)
    max_y: Mapped[float | None] = mapped_column(Float, nullable=True)
    srid: Mapped[int] = mapped_column(Integer, default=4326)
    properties_json: Mapped[dict] = mapped_column(JSON, default=dict)
    observed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    valid_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    license_name: Mapped[str | None] = mapped_column(String(300), nullable=True)
    attribution: Mapped[str | None] = mapped_column(Text, nullable=True)
    content_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    public: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)


class TimeSeriesDefinition(Base):
    __tablename__ = "time_series_definitions"
    __table_args__ = (
        UniqueConstraint("connector_id", "metric", "dimension_hash", name="uq_timeseries_connector_metric_dimensions"),
        Index("ix_timeseries_source_metric", "source_id", "metric"),
        Index("ix_timeseries_dataset_metric", "dataset_id", "metric"),
        Index("ix_timeseries_public", "public", "updated_at"),
    )

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    source_id: Mapped[str] = mapped_column(ForeignKey("live_data_sources.id", ondelete="RESTRICT"), nullable=False, index=True)
    connector_id: Mapped[str] = mapped_column(ForeignKey("live_data_connectors.id", ondelete="RESTRICT"), nullable=False, index=True)
    metric: Mapped[str] = mapped_column(String(300), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(700), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    dataset_id: Mapped[str | None] = mapped_column(String(500), nullable=True, index=True)
    domain: Mapped[str] = mapped_column(String(150), nullable=False, index=True)
    unit: Mapped[str | None] = mapped_column(String(200), nullable=True)
    frequency: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    geography_code: Mapped[str | None] = mapped_column(String(200), nullable=True, index=True)
    dimensions_json: Mapped[dict] = mapped_column(JSON, default=dict)
    dimension_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    license_name: Mapped[str | None] = mapped_column(String(300), nullable=True)
    attribution: Mapped[str | None] = mapped_column(Text, nullable=True)
    public: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)


class TimeSeriesPoint(Base):
    __tablename__ = "time_series_points"
    __table_args__ = (
        UniqueConstraint("series_id", "observed_at", "point_hash", name="uq_timeseries_point_time_hash"),
        Index("ix_timeseries_point_series_time", "series_id", "observed_at"),
        Index("ix_timeseries_point_partition", "partition_key", "series_id"),
        Index("ix_timeseries_point_observation", "observation_id"),
        Index("ix_timeseries_point_public", "public", "observed_at"),
    )

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    series_id: Mapped[str] = mapped_column(ForeignKey("time_series_definitions.id", ondelete="CASCADE"), nullable=False, index=True)
    observation_id: Mapped[str | None] = mapped_column(ForeignKey("live_data_observations.id", ondelete="SET NULL"), nullable=True, index=True)
    raw_record_id: Mapped[str | None] = mapped_column(ForeignKey("live_data_raw_records.id", ondelete="SET NULL"), nullable=True, index=True)
    observed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    partition_key: Mapped[str] = mapped_column(String(7), nullable=False, index=True)
    value_number: Mapped[float | None] = mapped_column(Float, nullable=True)
    value_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    quality_status: Mapped[str] = mapped_column(String(100), default="source_reported", index=True)
    freshness_status: Mapped[str] = mapped_column(String(100), default="unknown", index=True)
    dimensions_json: Mapped[dict] = mapped_column(JSON, default=dict)
    point_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    public: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class ScientificDataAsset(Base):
    __tablename__ = "scientific_data_assets"
    __table_args__ = (
        UniqueConstraint("scientific_record_id", "href", "asset_role", name="uq_scientific_asset_record_href_role"),
        Index("ix_scientific_asset_format_role", "format", "asset_role"),
        Index("ix_scientific_asset_dataset", "dataset_id"),
        Index("ix_scientific_asset_public", "public", "created_at"),
    )

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    scientific_record_id: Mapped[str | None] = mapped_column(ForeignKey("scientific_data_records.id", ondelete="CASCADE"), nullable=True, index=True)
    source_id: Mapped[str] = mapped_column(ForeignKey("live_data_sources.id", ondelete="RESTRICT"), nullable=False, index=True)
    connector_id: Mapped[str | None] = mapped_column(ForeignKey("live_data_connectors.id", ondelete="SET NULL"), nullable=True, index=True)
    raw_record_id: Mapped[str | None] = mapped_column(ForeignKey("live_data_raw_records.id", ondelete="SET NULL"), nullable=True, index=True)
    dataset_id: Mapped[str | None] = mapped_column(String(500), nullable=True, index=True)
    title: Mapped[str] = mapped_column(String(1000), nullable=False)
    asset_role: Mapped[str] = mapped_column(String(100), default="data", index=True)
    media_type: Mapped[str | None] = mapped_column(String(300), nullable=True)
    format: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    href: Mapped[str] = mapped_column(String(3000), nullable=False)
    storage_mode: Mapped[str] = mapped_column(String(80), default="remote", index=True)
    size_bytes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    checksum: Mapped[str | None] = mapped_column(String(300), nullable=True)
    stac_roles_json: Mapped[list] = mapped_column(JSON, default=list)
    variables_json: Mapped[list] = mapped_column(JSON, default=list)
    spatial_extent_json: Mapped[list] = mapped_column(JSON, default=list)
    temporal_extent_json: Mapped[list] = mapped_column(JSON, default=list)
    license_name: Mapped[str | None] = mapped_column(String(300), nullable=True)
    attribution: Mapped[str | None] = mapped_column(Text, nullable=True)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)
    public: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)


class MapLayer(Base):
    __tablename__ = "map_layers"
    __table_args__ = (
        UniqueConstraint("source_id", "external_layer_id", name="uq_map_layer_source_external"),
        Index("ix_map_layer_type_status", "layer_type", "status"),
        Index("ix_map_layer_public", "public", "title"),
    )

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    source_id: Mapped[str] = mapped_column(ForeignKey("live_data_sources.id", ondelete="RESTRICT"), nullable=False, index=True)
    connector_id: Mapped[str | None] = mapped_column(ForeignKey("live_data_connectors.id", ondelete="SET NULL"), nullable=True, index=True)
    external_layer_id: Mapped[str] = mapped_column(String(700), nullable=False)
    title: Mapped[str] = mapped_column(String(1000), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    layer_type: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    endpoint_url: Mapped[str] = mapped_column(String(3000), nullable=False)
    tile_template: Mapped[str | None] = mapped_column(String(3000), nullable=True)
    style_json: Mapped[dict] = mapped_column(JSON, default=dict)
    bounds_json: Mapped[list] = mapped_column(JSON, default=list)
    min_zoom: Mapped[int | None] = mapped_column(Integer, nullable=True)
    max_zoom: Mapped[int | None] = mapped_column(Integer, nullable=True)
    time_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    license_name: Mapped[str | None] = mapped_column(String(300), nullable=True)
    attribution: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(80), default="active", index=True)
    public: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)


class StacCollection(Base):
    __tablename__ = "stac_collections"
    __table_args__ = (
        Index("ix_stac_collection_source", "source_id", "public"),
        Index("ix_stac_collection_updated", "updated_at"),
    )

    id: Mapped[str] = mapped_column(String(500), primary_key=True)
    source_id: Mapped[str] = mapped_column(ForeignKey("live_data_sources.id", ondelete="RESTRICT"), nullable=False, index=True)
    connector_id: Mapped[str | None] = mapped_column(ForeignKey("live_data_connectors.id", ondelete="SET NULL"), nullable=True, index=True)
    title: Mapped[str] = mapped_column(String(1000), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    license_name: Mapped[str | None] = mapped_column(String(300), nullable=True)
    spatial_extent_json: Mapped[list] = mapped_column(JSON, default=list)
    temporal_extent_json: Mapped[list] = mapped_column(JSON, default=list)
    keywords_json: Mapped[list] = mapped_column(JSON, default=list)
    providers_json: Mapped[list] = mapped_column(JSON, default=list)
    links_json: Mapped[list] = mapped_column(JSON, default=list)
    summaries_json: Mapped[dict] = mapped_column(JSON, default=dict)
    public: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)


class StacItem(Base):
    __tablename__ = "stac_items"
    __table_args__ = (
        UniqueConstraint("collection_id", "source_record_id", name="uq_stac_item_collection_source"),
        Index("ix_stac_item_collection_datetime", "collection_id", "datetime"),
        Index("ix_stac_item_bbox", "min_x", "min_y", "max_x", "max_y"),
        Index("ix_stac_item_public", "public", "datetime"),
    )

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    collection_id: Mapped[str] = mapped_column(ForeignKey("stac_collections.id", ondelete="CASCADE"), nullable=False, index=True)
    source_id: Mapped[str] = mapped_column(ForeignKey("live_data_sources.id", ondelete="RESTRICT"), nullable=False, index=True)
    connector_id: Mapped[str | None] = mapped_column(ForeignKey("live_data_connectors.id", ondelete="SET NULL"), nullable=True, index=True)
    scientific_record_id: Mapped[str | None] = mapped_column(ForeignKey("scientific_data_records.id", ondelete="SET NULL"), nullable=True, index=True)
    source_record_id: Mapped[str] = mapped_column(String(700), nullable=False)
    geometry_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    bbox_json: Mapped[list] = mapped_column(JSON, default=list)
    min_x: Mapped[float | None] = mapped_column(Float, nullable=True)
    min_y: Mapped[float | None] = mapped_column(Float, nullable=True)
    max_x: Mapped[float | None] = mapped_column(Float, nullable=True)
    max_y: Mapped[float | None] = mapped_column(Float, nullable=True)
    datetime: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    start_datetime: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    end_datetime: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    properties_json: Mapped[dict] = mapped_column(JSON, default=dict)
    assets_json: Mapped[dict] = mapped_column(JSON, default=dict)
    links_json: Mapped[list] = mapped_column(JSON, default=list)
    content_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    public: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)


# v2.9.0 — Streaming, Alerts, and Source Reliability
class ConnectorWorkItem(Base):
    __tablename__ = "connector_work_items"
    __table_args__ = (
        Index("ix_connector_work_status_available", "status", "available_at"),
        Index("ix_connector_work_connector_created", "connector_id", "created_at"),
        Index("ix_connector_work_lease", "lease_expires_at"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    connector_id: Mapped[str] = mapped_column(ForeignKey("live_data_connectors.id", ondelete="RESTRICT"), nullable=False, index=True)
    parameters_json: Mapped[dict] = mapped_column(JSON, default=dict)
    requested_by: Mapped[str] = mapped_column(String(300), default="platform-core")
    priority: Mapped[int] = mapped_column(Integer, default=100, index=True)
    status: Mapped[str] = mapped_column(String(40), default="pending", index=True)
    attempt_count: Mapped[int] = mapped_column(Integer, default=0)
    max_attempts: Mapped[int] = mapped_column(Integer, default=3)
    available_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, index=True)
    lease_owner: Mapped[str | None] = mapped_column(String(200), nullable=True)
    lease_expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    last_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    ingestion_run_id: Mapped[str | None] = mapped_column(ForeignKey("live_data_ingestion_runs.id", ondelete="SET NULL"), nullable=True)
    execution_connector_id: Mapped[str | None] = mapped_column(String(180), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class DeadLetterRecord(Base):
    __tablename__ = "dead_letter_records"
    __table_args__ = (
        Index("ix_dead_letter_connector_created", "connector_id", "created_at"),
        Index("ix_dead_letter_status_created", "status", "created_at"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    work_item_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    connector_id: Mapped[str] = mapped_column(ForeignKey("live_data_connectors.id", ondelete="RESTRICT"), nullable=False, index=True)
    parameters_json: Mapped[dict] = mapped_column(JSON, default=dict)
    error_message: Mapped[str] = mapped_column(Text, nullable=False)
    attempt_count: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String(30), default="open", index=True)
    replay_count: Mapped[int] = mapped_column(Integer, default=0)
    last_replayed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class StreamEvent(Base):
    __tablename__ = "stream_events"
    __table_args__ = (
        Index("ix_stream_event_type_created", "event_type", "created_at"),
        Index("ix_stream_event_public_id", "public", "id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    event_type: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    subject_type: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    subject_id: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    payload_json: Mapped[dict] = mapped_column(JSON, default=dict)
    public: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, index=True)


class AlertRule(Base):
    __tablename__ = "alert_rules"
    __table_args__ = (
        Index("ix_alert_rule_enabled_domain", "enabled", "domain"),
        Index("ix_alert_rule_metric", "metric"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(300), nullable=False)
    domain: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    metric: Mapped[str | None] = mapped_column(String(200), nullable=True, index=True)
    connector_id: Mapped[str | None] = mapped_column(String(180), nullable=True, index=True)
    source_id: Mapped[str | None] = mapped_column(String(150), nullable=True, index=True)
    operator: Mapped[str] = mapped_column(String(20), default="exists")
    threshold_number: Mapped[float | None] = mapped_column(Float, nullable=True)
    geography_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    severity: Mapped[str] = mapped_column(String(30), default="info")
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    public: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)


class GeographicSubscription(Base):
    __tablename__ = "geographic_subscriptions"
    __table_args__ = (
        Index("ix_geo_subscription_active", "active"),
        Index("ix_geo_subscription_public", "public"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(300), nullable=False)
    geometry_json: Mapped[dict] = mapped_column(JSON, default=dict)
    domains_json: Mapped[list] = mapped_column(JSON, default=list)
    connector_ids_json: Mapped[list] = mapped_column(JSON, default=list)
    event_types_json: Mapped[list] = mapped_column(JSON, default=list)
    active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    public: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)


# v2.10.0 — Operational Evidence & Facility Registry
class OperationalFacility(Base):
    __tablename__ = "operational_facilities"
    __table_args__ = (
        Index("ix_operational_facility_country_type", "country_code", "facility_type"),
        Index("ix_operational_facility_status_public", "registry_status", "public"),
        Index("ix_operational_facility_coordinates", "latitude", "longitude"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    canonical_entity_id: Mapped[str | None] = mapped_column(ForeignKey("entities.id", ondelete="SET NULL"), nullable=True, index=True)
    name: Mapped[str] = mapped_column(String(500), nullable=False, index=True)
    facility_type: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    country_code: Mapped[str] = mapped_column(String(3), nullable=False, index=True)
    admin_area: Mapped[str | None] = mapped_column(String(300), nullable=True, index=True)
    locality: Mapped[str | None] = mapped_column(String(300), nullable=True)
    latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    longitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    geometry_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    registry_status: Mapped[str] = mapped_column(String(40), default="active", index=True)
    public: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)


class FacilitySourceIdentifier(Base):
    __tablename__ = "facility_source_identifiers"
    __table_args__ = (
        UniqueConstraint("namespace", "value", name="uq_facility_source_identifier"),
        Index("ix_facility_source_identifier_facility", "facility_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    facility_id: Mapped[str] = mapped_column(ForeignKey("operational_facilities.id", ondelete="CASCADE"), nullable=False, index=True)
    namespace: Mapped[str] = mapped_column(String(160), nullable=False)
    value: Mapped[str] = mapped_column(String(700), nullable=False)
    source_id: Mapped[str | None] = mapped_column(ForeignKey("live_data_sources.id", ondelete="SET NULL"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class FacilityObservation(Base):
    __tablename__ = "facility_observations"
    __table_args__ = (
        Index("ix_facility_observation_facility_time", "facility_id", "observed_at"),
        Index("ix_facility_observation_kind_status", "observation_kind", "status_value"),
        Index("ix_facility_observation_source_record", "source_id", "source_record_id"),
        Index("ix_facility_observation_public_time", "public", "observed_at"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    facility_id: Mapped[str] = mapped_column(ForeignKey("operational_facilities.id", ondelete="CASCADE"), nullable=False, index=True)
    observation_kind: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    status_value: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    observed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    valid_from: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    valid_to: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    publisher: Mapped[str] = mapped_column(String(400), nullable=False)
    source_id: Mapped[str | None] = mapped_column(ForeignKey("live_data_sources.id", ondelete="SET NULL"), nullable=True, index=True)
    connector_id: Mapped[str | None] = mapped_column(ForeignKey("live_data_connectors.id", ondelete="SET NULL"), nullable=True, index=True)
    source_record_id: Mapped[str | None] = mapped_column(String(700), nullable=True)
    source_url: Mapped[str | None] = mapped_column(String(1800), nullable=True)
    evidence_class: Mapped[str] = mapped_column(String(80), default="published-evidence", index=True)
    geographic_scope: Mapped[str | None] = mapped_column(String(200), nullable=True)
    methodology: Mapped[str | None] = mapped_column(Text, nullable=True)
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    services_json: Mapped[list] = mapped_column(JSON, default=list)
    constraints_json: Mapped[list] = mapped_column(JSON, default=list)
    details_json: Mapped[dict] = mapped_column(JSON, default=dict)
    provenance_json: Mapped[dict] = mapped_column(JSON, default=dict)
    public: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

# v2.11.0 — Humanitarian Access & Essential Services Fabric
class HumanitarianCondition(Base):
    __tablename__ = "humanitarian_conditions"
    __table_args__ = (
        UniqueConstraint(
            "source_id", "source_record_id", "service_domain", "condition_kind", "observed_at",
            name="uq_humanitarian_condition_source_kind_time",
        ),
        Index("ix_humanitarian_condition_country_domain_time", "country_code", "service_domain", "observed_at"),
        Index("ix_humanitarian_condition_facility_time", "facility_id", "observed_at"),
        Index("ix_humanitarian_condition_kind_status", "condition_kind", "status_value"),
        Index("ix_humanitarian_condition_semantic_public", "semantic_role", "public"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    country_code: Mapped[str] = mapped_column(String(3), nullable=False, index=True)
    admin_area: Mapped[str | None] = mapped_column(String(300), nullable=True, index=True)
    locality: Mapped[str | None] = mapped_column(String(300), nullable=True)
    facility_id: Mapped[str | None] = mapped_column(ForeignKey("operational_facilities.id", ondelete="SET NULL"), nullable=True, index=True)
    service_domain: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    condition_kind: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    semantic_role: Mapped[str] = mapped_column(String(80), default="humanitarian-indicator", index=True)
    status_value: Mapped[str | None] = mapped_column(String(160), nullable=True, index=True)
    value_number: Mapped[float | None] = mapped_column(Float, nullable=True)
    value_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    unit: Mapped[str | None] = mapped_column(String(120), nullable=True)
    observed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    publisher: Mapped[str] = mapped_column(String(400), nullable=False)
    source_id: Mapped[str | None] = mapped_column(ForeignKey("live_data_sources.id", ondelete="SET NULL"), nullable=True, index=True)
    connector_id: Mapped[str | None] = mapped_column(ForeignKey("live_data_connectors.id", ondelete="SET NULL"), nullable=True, index=True)
    source_record_id: Mapped[str | None] = mapped_column(String(700), nullable=True)
    source_url: Mapped[str | None] = mapped_column(String(1800), nullable=True)
    evidence_class: Mapped[str] = mapped_column(String(100), default="published-evidence", index=True)
    geographic_scope: Mapped[str | None] = mapped_column(String(250), nullable=True)
    methodology: Mapped[str | None] = mapped_column(Text, nullable=True)
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    dimensions_json: Mapped[dict] = mapped_column(JSON, default=dict)
    details_json: Mapped[dict] = mapped_column(JSON, default=dict)
    provenance_json: Mapped[dict] = mapped_column(JSON, default=dict)
    public: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)



# v2.12.0 — Country Evidence Federation & Reconciliation
class CountryEvidenceReconciliation(Base):
    __tablename__ = "country_evidence_reconciliations"
    __table_args__ = (
        UniqueConstraint("request_fingerprint", name="uq_country_evidence_reconciliation_fingerprint"),
        Index("ix_country_evidence_reconciliation_country_concept", "country_code", "concept"),
        Index("ix_country_evidence_reconciliation_state_time", "decision_state", "created_at"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    country_code: Mapped[str] = mapped_column(String(3), nullable=False, index=True)
    concept: Mapped[str] = mapped_column(String(500), nullable=False, index=True)
    decision_state: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    selected_record_family: Mapped[str | None] = mapped_column(String(100), nullable=True)
    selected_record_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    selected_source: Mapped[str | None] = mapped_column(String(500), nullable=True)
    selected_authority_role: Mapped[str | None] = mapped_column(String(100), nullable=True)
    request_fingerprint: Mapped[str] = mapped_column(String(64), nullable=False)
    candidates_json: Mapped[list] = mapped_column(JSON, default=list)
    rationale_json: Mapped[dict] = mapped_column(JSON, default=dict)
    public: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

# v2.13.0 — Earth, Ocean, Space & Scientific Service Fabric
class ScientificDomainBinding(Base):
    __tablename__ = "scientific_domain_bindings"
    __table_args__ = (
        UniqueConstraint("subject_type", "subject_id", "domain", name="uq_scientific_domain_subject_domain"),
        Index("ix_scientific_domain_domain_subdomain", "domain", "subdomain"),
        Index("ix_scientific_domain_subject", "subject_type", "subject_id"),
        Index("ix_scientific_domain_public", "public", "domain"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    subject_type: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    subject_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    domain: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    subdomain: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    classification_basis: Mapped[str] = mapped_column(String(80), nullable=False)
    classification_evidence_json: Mapped[list] = mapped_column(JSON, default=list)
    confidence: Mapped[float] = mapped_column(Float, default=0.0)
    is_primary: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    routing_only: Mapped[bool] = mapped_column(Boolean, default=True)
    truth_precedence: Mapped[str] = mapped_column(String(32), default="none")
    public: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)


# v2.14.0 — Cross-Product Evidence Exchange
class CrossProductExchangePackage(Base):
    __tablename__ = "cross_product_exchange_packages"
    __table_args__ = (
        UniqueConstraint("origin_product", "target_product", "idempotency_key", name="uq_cross_product_exchange_idempotency"),
        Index("ix_cross_product_exchange_route", "origin_product", "target_product", "created_at"),
        Index("ix_cross_product_exchange_visibility_state", "visibility", "state"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    origin_product: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    target_product: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    idempotency_key: Mapped[str] = mapped_column(String(128), nullable=False)
    title: Mapped[str] = mapped_column(String(400), nullable=False)
    purpose: Mapped[str | None] = mapped_column(Text, nullable=True)
    visibility: Mapped[str] = mapped_column(String(30), default="internal", index=True)
    state: Mapped[str] = mapped_column(String(40), default="ready", index=True)
    delivery_mode: Mapped[str] = mapped_column(String(30), default="pull")
    governance_json: Mapped[dict] = mapped_column(JSON, default=dict)
    provenance_json: Mapped[dict] = mapped_column(JSON, default=dict)
    package_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)


class CrossProductExchangeItem(Base):
    __tablename__ = "cross_product_exchange_items"
    __table_args__ = (
        UniqueConstraint("package_id", "ordinal", name="uq_cross_product_exchange_package_ordinal"),
        Index("ix_cross_product_exchange_item_subject", "subject_type", "subject_id"),
        Index("ix_cross_product_exchange_item_package", "package_id", "ordinal"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    package_id: Mapped[str] = mapped_column(ForeignKey("cross_product_exchange_packages.id", ondelete="CASCADE"), nullable=False, index=True)
    ordinal: Mapped[int] = mapped_column(Integer, nullable=False)
    artifact_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    subject_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    subject_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    canonical_uri: Mapped[str] = mapped_column(String(1800), nullable=False)
    snapshot_mode: Mapped[str] = mapped_column(String(40), default="reference")
    snapshot_json: Mapped[dict] = mapped_column(JSON, default=dict)
    provenance_json: Mapped[dict] = mapped_column(JSON, default=dict)
    evidence_role: Mapped[str] = mapped_column(String(100), default="inherited")
    truth_precedence: Mapped[str] = mapped_column(String(80), default="inherit-from-subject")
    transformation_state: Mapped[str] = mapped_column(String(80), default="unaltered-reference")
    item_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class CrossProductExchangeReceipt(Base):
    __tablename__ = "cross_product_exchange_receipts"
    __table_args__ = (
        Index("ix_cross_product_exchange_receipt_package_time", "package_id", "created_at"),
        Index("ix_cross_product_exchange_receipt_target_state", "target_product", "state"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    package_id: Mapped[str] = mapped_column(ForeignKey("cross_product_exchange_packages.id", ondelete="CASCADE"), nullable=False, index=True)
    target_product: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    state: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    derived_object_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


# v2.15.0 — Distributed Processing, Storage & Scale
class ScaleProcessingJob(Base):
    __tablename__ = "scale_processing_jobs"
    __table_args__ = (
        UniqueConstraint("job_type", "idempotency_key", name="uq_scale_job_type_idempotency"),
        Index("ix_scale_jobs_state_priority", "state", "priority", "created_at"),
        Index("ix_scale_jobs_product_state", "origin_product", "state"),
    )
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    job_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    origin_product: Mapped[str] = mapped_column(String(80), default="platform-core", index=True)
    idempotency_key: Mapped[str] = mapped_column(String(128), nullable=False)
    state: Mapped[str] = mapped_column(String(40), default="queued", index=True)
    priority: Mapped[int] = mapped_column(Integer, default=100, index=True)
    partition_count: Mapped[int] = mapped_column(Integer, default=1)
    completed_partitions: Mapped[int] = mapped_column(Integer, default=0)
    failed_partitions: Mapped[int] = mapped_column(Integer, default=0)
    parameters_json: Mapped[dict] = mapped_column(JSON, default=dict)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

class ScaleProcessingPartition(Base):
    __tablename__ = "scale_processing_partitions"
    __table_args__ = (
        UniqueConstraint("job_id", "partition_key", name="uq_scale_job_partition_key"),
        Index("ix_scale_partition_claim", "state", "available_at", "created_at"),
        Index("ix_scale_partition_job_state", "job_id", "state"),
    )
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    job_id: Mapped[str] = mapped_column(ForeignKey("scale_processing_jobs.id", ondelete="CASCADE"), nullable=False, index=True)
    partition_key: Mapped[str] = mapped_column(String(255), nullable=False)
    state: Mapped[str] = mapped_column(String(40), default="queued", index=True)
    payload_json: Mapped[dict] = mapped_column(JSON, default=dict)
    attempt_count: Mapped[int] = mapped_column(Integer, default=0)
    max_attempts: Mapped[int] = mapped_column(Integer, default=3)
    lease_owner: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    lease_expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    available_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, index=True)
    storage_object_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    last_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

class ScaleStorageObject(Base):
    __tablename__ = "scale_storage_objects"
    __table_args__ = (
        UniqueConstraint("content_hash", "storage_class", name="uq_scale_storage_hash_class"),
        Index("ix_scale_storage_retention", "retention_state", "expires_at"),
        Index("ix_scale_storage_subject", "subject_type", "subject_id"),
    )
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    storage_class: Mapped[str] = mapped_column(String(40), default="inline", index=True)
    content_type: Mapped[str] = mapped_column(String(160), default="application/json")
    byte_size: Mapped[int] = mapped_column(Integer, default=0)
    content_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    inline_json: Mapped[dict] = mapped_column(JSON, default=dict)
    external_uri: Mapped[str | None] = mapped_column(String(1800), nullable=True)
    subject_type: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    subject_id: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    provenance_json: Mapped[dict] = mapped_column(JSON, default=dict)
    retention_state: Mapped[str] = mapped_column(String(40), default="active", index=True)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


# v2.16.0 — Governance, Access & Audit Control Plane
class GovernancePolicy(Base):
    __tablename__ = "governance_policies"
    __table_args__ = (
        Index("ix_governance_policy_match", "enabled", "resource_type", "action", "priority"),
        Index("ix_governance_policy_principal", "principal_type", "principal_id"),
        Index("ix_governance_policy_product", "product_scope"),
    )
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(240), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    effect: Mapped[str] = mapped_column(String(20), nullable=False, default="deny", index=True)
    principal_type: Mapped[str] = mapped_column(String(60), nullable=False, default="any", index=True)
    principal_id: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    product_scope: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    resource_type: Mapped[str] = mapped_column(String(120), nullable=False, default="*", index=True)
    action: Mapped[str] = mapped_column(String(80), nullable=False, default="*", index=True)
    visibility_ceiling: Mapped[str] = mapped_column(String(30), nullable=False, default="internal")
    priority: Mapped[int] = mapped_column(Integer, default=100, index=True)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    conditions_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_by: Mapped[str] = mapped_column(String(255), default="operator")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

class GovernanceRoleBinding(Base):
    __tablename__ = "governance_role_bindings"
    __table_args__ = (
        UniqueConstraint("principal_type", "principal_id", "role", "product_scope", name="uq_governance_principal_role_scope"),
        Index("ix_governance_role_principal", "principal_type", "principal_id", "active"),
    )
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    principal_type: Mapped[str] = mapped_column(String(60), nullable=False, index=True)
    principal_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    role: Mapped[str] = mapped_column(String(60), nullable=False, index=True)
    product_scope: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

class GovernanceDecision(Base):
    __tablename__ = "governance_decisions"
    __table_args__ = (
        Index("ix_governance_decision_created", "created_at"),
        Index("ix_governance_decision_principal", "principal_type", "principal_id", "created_at"),
        Index("ix_governance_decision_resource", "resource_type", "resource_id", "created_at"),
        Index("ix_governance_decision_outcome", "decision", "created_at"),
    )
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    request_id: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    principal_type: Mapped[str] = mapped_column(String(60), nullable=False)
    principal_id: Mapped[str] = mapped_column(String(255), nullable=False)
    product: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    resource_type: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    resource_id: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    action: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    requested_visibility: Mapped[str] = mapped_column(String(30), default="internal")
    decision: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    matched_policy_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    reason: Mapped[str] = mapped_column(String(500), nullable=False)
    enforcement_mode: Mapped[str] = mapped_column(String(20), default="audit")
    context_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

class GovernanceAuditEvent(Base):
    __tablename__ = "governance_audit_events"
    __table_args__ = (
        Index("ix_governance_audit_created", "created_at"),
        Index("ix_governance_audit_actor", "actor_type", "actor_id", "created_at"),
        Index("ix_governance_audit_resource", "resource_type", "resource_id", "created_at"),
    )
    sequence: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    event_id: Mapped[str] = mapped_column(String(36), nullable=False, unique=True, default=lambda: str(uuid.uuid4()))
    event_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    actor_type: Mapped[str] = mapped_column(String(60), nullable=False)
    actor_id: Mapped[str] = mapped_column(String(255), nullable=False)
    action: Mapped[str] = mapped_column(String(80), nullable=False)
    resource_type: Mapped[str] = mapped_column(String(120), nullable=False)
    resource_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    decision_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    details_json: Mapped[dict] = mapped_column(JSON, default=dict)
    details_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    previous_event_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    event_hash: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

class GovernanceRetentionPolicy(Base):
    __tablename__ = "governance_retention_policies"
    __table_args__ = (Index("ix_governance_retention_resource", "resource_type", "enabled"),)
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    resource_type: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    retention_hours: Mapped[int] = mapped_column(Integer, nullable=False)
    disposition: Mapped[str] = mapped_column(String(30), default="compact")
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


# v2.17.0 — Production Certification, Migration Assurance & Recovery Readiness
class ProductionCertificationRun(Base):
    __tablename__ = "production_certification_runs"
    __table_args__ = (
        Index("ix_production_certification_release_state", "release", "state", "created_at"),
        Index("ix_production_certification_created", "created_at"),
    )
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    release: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    state: Mapped[str] = mapped_column(String(40), nullable=False, default="blocked", index=True)
    migration_head: Mapped[str] = mapped_column(String(20), nullable=False)
    pending_migrations_json: Mapped[list] = mapped_column(JSON, default=list)
    checks_json: Mapped[dict] = mapped_column(JSON, default=dict)
    blockers_json: Mapped[list] = mapped_column(JSON, default=list)
    gateway_json: Mapped[dict] = mapped_column(JSON, default=dict)
    recovery_json: Mapped[dict] = mapped_column(JSON, default=dict)
    certification_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    completed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

class RecoveryReadinessCheckpoint(Base):
    __tablename__ = "recovery_readiness_checkpoints"
    __table_args__ = (
        Index("ix_recovery_checkpoint_release_created", "release", "created_at"),
        Index("ix_recovery_checkpoint_expires", "expires_at"),
    )
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    release: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    schema_head: Mapped[str] = mapped_column(String(20), nullable=False)
    migration_inventory_json: Mapped[list] = mapped_column(JSON, default=list)
    table_inventory_json: Mapped[list] = mapped_column(JSON, default=list)
    row_counts_json: Mapped[dict] = mapped_column(JSON, default=dict)
    recovery_contract_json: Mapped[dict] = mapped_column(JSON, default=dict)
    checkpoint_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)


# v2.18.0 — Observability, SLOs & Production Operations
class ObservabilityMetricSample(Base):
    __tablename__ = "observability_metric_samples"
    __table_args__ = (
        Index("ix_observability_metric_time", "metric_name", "observed_at"),
        Index("ix_observability_service_time", "service", "observed_at"),
        Index("ix_observability_status_time", "status_class", "observed_at"),
    )
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    service: Mapped[str] = mapped_column(String(100), nullable=False, default="platform-core", index=True)
    metric_name: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    value: Mapped[float] = mapped_column(Float, nullable=False)
    unit: Mapped[str] = mapped_column(String(40), nullable=False, default="count")
    method: Mapped[str | None] = mapped_column(String(16), nullable=True)
    route: Mapped[str | None] = mapped_column(String(600), nullable=True)
    status_code: Mapped[int | None] = mapped_column(Integer, nullable=True)
    status_class: Mapped[str | None] = mapped_column(String(20), nullable=True, index=True)
    request_id: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    labels_json: Mapped[dict] = mapped_column(JSON, default=dict)
    observed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, index=True)

class ServiceLevelObjective(Base):
    __tablename__ = "service_level_objectives"
    __table_args__ = (
        UniqueConstraint("service", "name", name="uq_slo_service_name"),
        Index("ix_slo_service_enabled", "service", "enabled"),
    )
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    service: Mapped[str] = mapped_column(String(100), nullable=False, default="platform-core", index=True)
    name: Mapped[str] = mapped_column(String(240), nullable=False)
    indicator: Mapped[str] = mapped_column(String(60), nullable=False, index=True)
    target: Mapped[float] = mapped_column(Float, nullable=False)
    comparison: Mapped[str] = mapped_column(String(8), nullable=False, default=">=")
    window_minutes: Mapped[int] = mapped_column(Integer, nullable=False, default=60)
    minimum_samples: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, index=True)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

class ProductionDeploymentMarker(Base):
    __tablename__ = "production_deployment_markers"
    __table_args__ = (
        Index("ix_deployment_release_time", "release", "created_at"),
        Index("ix_deployment_environment_time", "environment", "created_at"),
    )
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    release: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    environment: Mapped[str] = mapped_column(String(40), nullable=False, default="production", index=True)
    state: Mapped[str] = mapped_column(String(40), nullable=False, default="deployed", index=True)
    commit_sha: Mapped[str | None] = mapped_column(String(128), nullable=True)
    actor: Mapped[str] = mapped_column(String(255), nullable=False, default="operator")
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, index=True)

# v2.19.0 — Incident Response, Change Control & Rollback Coordination
class OperationsIncident(Base):
    __tablename__ = "operations_incidents"
    __table_args__ = (
        UniqueConstraint("idempotency_key", name="uq_operations_incident_idempotency"),
        Index("ix_operations_incident_service_state", "service", "state", "created_at"),
        Index("ix_operations_incident_severity_state", "severity", "state", "created_at"),
    )
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    idempotency_key: Mapped[str | None] = mapped_column(String(255), nullable=True)
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    service: Mapped[str] = mapped_column(String(100), nullable=False, default="platform-core", index=True)
    environment: Mapped[str] = mapped_column(String(40), nullable=False, default="production", index=True)
    severity: Mapped[str] = mapped_column(String(20), nullable=False, default="sev3", index=True)
    state: Mapped[str] = mapped_column(String(40), nullable=False, default="open", index=True)
    source: Mapped[str] = mapped_column(String(40), nullable=False, default="manual", index=True)
    source_ref: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    owner: Mapped[str] = mapped_column(String(255), nullable=False, default="unassigned")
    visibility: Mapped[str] = mapped_column(String(30), nullable=False, default="internal", index=True)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)
    detected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, index=True)
    mitigated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

class OperationsIncidentEvent(Base):
    __tablename__ = "operations_incident_events"
    __table_args__ = (Index("ix_operations_incident_event_order", "incident_id", "created_at", "id"),)
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    incident_id: Mapped[str] = mapped_column(ForeignKey("operations_incidents.id", ondelete="CASCADE"), nullable=False, index=True)
    event_type: Mapped[str] = mapped_column(String(60), nullable=False, index=True)
    previous_state: Mapped[str | None] = mapped_column(String(40), nullable=True)
    new_state: Mapped[str | None] = mapped_column(String(40), nullable=True)
    actor: Mapped[str] = mapped_column(String(255), nullable=False, default="operator")
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    details_json: Mapped[dict] = mapped_column(JSON, default=dict)
    previous_event_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    event_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, index=True)

class ChangeControlRecord(Base):
    __tablename__ = "change_control_records"
    __table_args__ = (
        UniqueConstraint("change_key", name="uq_change_control_key"),
        Index("ix_change_control_environment_state", "environment", "state", "created_at"),
        Index("ix_change_control_release", "release", "created_at"),
    )
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    change_key: Mapped[str] = mapped_column(String(255), nullable=False)
    service: Mapped[str] = mapped_column(String(100), nullable=False, default="platform-core", index=True)
    release: Mapped[str | None] = mapped_column(String(40), nullable=True, index=True)
    environment: Mapped[str] = mapped_column(String(40), nullable=False, default="production", index=True)
    change_type: Mapped[str] = mapped_column(String(40), nullable=False, default="deployment", index=True)
    risk: Mapped[str] = mapped_column(String(20), nullable=False, default="medium", index=True)
    state: Mapped[str] = mapped_column(String(40), nullable=False, default="planned", index=True)
    actor: Mapped[str] = mapped_column(String(255), nullable=False, default="operator")
    approval_required: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    approved_by: Mapped[str | None] = mapped_column(String(255), nullable=True)
    incident_id: Mapped[str | None] = mapped_column(ForeignKey("operations_incidents.id", ondelete="SET NULL"), nullable=True, index=True)
    deployment_marker_id: Mapped[str | None] = mapped_column(ForeignKey("production_deployment_markers.id", ondelete="SET NULL"), nullable=True, index=True)
    details_json: Mapped[dict] = mapped_column(JSON, default=dict)
    planned_start_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

class RollbackCoordinationRecord(Base):
    __tablename__ = "rollback_coordination_records"
    __table_args__ = (Index("ix_rollback_incident_state", "incident_id", "state", "created_at"),)
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    incident_id: Mapped[str] = mapped_column(ForeignKey("operations_incidents.id", ondelete="CASCADE"), nullable=False, index=True)
    deployment_marker_id: Mapped[str | None] = mapped_column(ForeignKey("production_deployment_markers.id", ondelete="SET NULL"), nullable=True, index=True)
    recommendation: Mapped[str] = mapped_column(String(40), nullable=False, default="review", index=True)
    state: Mapped[str] = mapped_column(String(40), nullable=False, default="proposed", index=True)
    rationale: Mapped[str] = mapped_column(Text, nullable=False)
    evidence_json: Mapped[dict] = mapped_column(JSON, default=dict)
    operator_actor: Mapped[str | None] = mapped_column(String(255), nullable=True)
    operator_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    automatic_execution: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    causal_attribution: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)



# v2.20.0 — Continuity, Backup Verification & Disaster Recovery
class BackupArtifactRecord(Base):
    __tablename__ = "backup_artifact_records"
    __table_args__ = (
        UniqueConstraint("backup_key", name="uq_backup_artifact_key"),
        Index("ix_backup_environment_completed", "environment", "backup_completed_at"),
        Index("ix_backup_verification_state", "verification_state", "verified_at"),
    )
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    backup_key: Mapped[str] = mapped_column(String(255), nullable=False)
    environment: Mapped[str] = mapped_column(String(40), nullable=False, default="production", index=True)
    database_engine: Mapped[str] = mapped_column(String(40), nullable=False, default="postgresql", index=True)
    storage_kind: Mapped[str] = mapped_column(String(40), nullable=False, default="operator-managed", index=True)
    storage_uri: Mapped[str] = mapped_column(String(2000), nullable=False)
    checksum_sha256: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    size_bytes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    verification_state: Mapped[str] = mapped_column(String(40), nullable=False, default="pending", index=True)
    verification_details_json: Mapped[dict] = mapped_column(JSON, default=dict)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)
    backup_started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    backup_completed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utcnow, index=True)
    verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

class DisasterRecoveryObjective(Base):
    __tablename__ = "disaster_recovery_objectives"
    __table_args__ = (UniqueConstraint("environment", name="uq_dr_objective_environment"),)
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    environment: Mapped[str] = mapped_column(String(40), nullable=False, default="production", index=True)
    rpo_minutes: Mapped[int] = mapped_column(Integer, nullable=False, default=1440)
    rto_minutes: Mapped[int] = mapped_column(Integer, nullable=False, default=240)
    max_backup_age_minutes: Mapped[int] = mapped_column(Integer, nullable=False, default=1440)
    restore_rehearsal_max_age_hours: Mapped[int] = mapped_column(Integer, nullable=False, default=720)
    require_verified_backup: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    require_restore_rehearsal: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

class RestoreRehearsalRecord(Base):
    __tablename__ = "restore_rehearsal_records"
    __table_args__ = (
        Index("ix_restore_rehearsal_environment_completed", "environment", "completed_at"),
        Index("ix_restore_rehearsal_backup_state", "backup_id", "state"),
    )
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    backup_id: Mapped[str] = mapped_column(ForeignKey("backup_artifact_records.id", ondelete="CASCADE"), nullable=False, index=True)
    environment: Mapped[str] = mapped_column(String(40), nullable=False, default="production", index=True)
    state: Mapped[str] = mapped_column(String(40), nullable=False, default="planned", index=True)
    execution_mode: Mapped[str] = mapped_column(String(60), nullable=False, default="external-operator")
    operator_actor: Mapped[str] = mapped_column(String(255), nullable=False, default="operator")
    schema_head: Mapped[str | None] = mapped_column(String(20), nullable=True)
    duration_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    integrity_checks_json: Mapped[dict] = mapped_column(JSON, default=dict)
    evidence_json: Mapped[dict] = mapped_column(JSON, default=dict)
    isolated_target: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    source_database_mutated: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    automatic_restore: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


# v2.21.0 — Multi-Region Resilience & Failover Coordination
class RegionServiceStatusRecord(Base):
    __tablename__ = "region_service_status_records"
    __table_args__ = (
        UniqueConstraint("service", "environment", "region_key", name="uq_region_service_status"),
        Index("ix_region_service_health", "service", "environment", "health_state", "observed_at"),
    )
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    service: Mapped[str] = mapped_column(String(100), nullable=False, default="platform-core", index=True)
    environment: Mapped[str] = mapped_column(String(40), nullable=False, default="production", index=True)
    region_key: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    role: Mapped[str] = mapped_column(String(30), nullable=False, default="standby", index=True)
    health_state: Mapped[str] = mapped_column(String(30), nullable=False, default="unknown", index=True)
    readiness_state: Mapped[str] = mapped_column(String(30), nullable=False, default="unknown", index=True)
    replication_state: Mapped[str] = mapped_column(String(30), nullable=False, default="unknown", index=True)
    replication_lag_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)
    read_eligible: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    write_eligible: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    recovery_priority: Mapped[int] = mapped_column(Integer, nullable=False, default=100)
    endpoint_ref: Mapped[str | None] = mapped_column(String(500), nullable=True)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)
    observed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

class FailoverGroupRecord(Base):
    __tablename__ = "failover_group_records"
    __table_args__ = (UniqueConstraint("group_key", name="uq_failover_group_key"), Index("ix_failover_group_service", "service", "environment"),)
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    group_key: Mapped[str] = mapped_column(String(255), nullable=False)
    service: Mapped[str] = mapped_column(String(100), nullable=False, default="platform-core", index=True)
    environment: Mapped[str] = mapped_column(String(40), nullable=False, default="production", index=True)
    active_region: Mapped[str] = mapped_column(String(100), nullable=False)
    candidate_regions_json: Mapped[list] = mapped_column(JSON, default=list)
    strategy: Mapped[str] = mapped_column(String(40), nullable=False, default="operator-coordinated")
    degraded_read_only_allowed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    max_replication_lag_seconds: Mapped[int] = mapped_column(Integer, nullable=False, default=300)
    automatic_failover: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

class FailoverAssessmentRecord(Base):
    __tablename__ = "failover_assessment_records"
    __table_args__ = (Index("ix_failover_assessment_group_state", "group_id", "state", "created_at"),)
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    group_id: Mapped[str] = mapped_column(ForeignKey("failover_group_records.id", ondelete="CASCADE"), nullable=False, index=True)
    source_region: Mapped[str] = mapped_column(String(100), nullable=False)
    target_region: Mapped[str | None] = mapped_column(String(100), nullable=True)
    recommendation: Mapped[str] = mapped_column(String(40), nullable=False, default="stay", index=True)
    state: Mapped[str] = mapped_column(String(40), nullable=False, default="proposed", index=True)
    reason: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    read_only: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    automatic_execution: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    infrastructure_actuation_by_core: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    replication_safe_for_write: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    acknowledged_by: Mapped[str | None] = mapped_column(String(255), nullable=True)
    approved_by: Mapped[str | None] = mapped_column(String(255), nullable=True)
    executed_by: Mapped[str | None] = mapped_column(String(255), nullable=True)
    evidence_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)
