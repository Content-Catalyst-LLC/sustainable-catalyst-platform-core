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

# v2.22.0 — Data Lifecycle, Archival Integrity & Preservation
class DataLifecyclePolicyRecord(Base):
    __tablename__ = "data_lifecycle_policy_records"
    __table_args__ = (
        UniqueConstraint("policy_key", name="uq_data_lifecycle_policy_key"),
        Index("ix_data_lifecycle_policy_subject", "subject_type", "enabled"),
    )
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    policy_key: Mapped[str] = mapped_column(String(255), nullable=False)
    subject_type: Mapped[str] = mapped_column(String(120), nullable=False, default="evidence-record", index=True)
    retention_class: Mapped[str] = mapped_column(String(40), nullable=False, default="institutional", index=True)
    minimum_retention_days: Mapped[int] = mapped_column(Integer, nullable=False, default=365)
    archive_after_days: Mapped[int] = mapped_column(Integer, nullable=False, default=90)
    tombstone_after_days: Mapped[int | None] = mapped_column(Integer, nullable=True)
    preserve_provenance: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    hold_overrides_lifecycle: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    hard_delete_allowed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, index=True)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

class PreservationArchiveRecord(Base):
    __tablename__ = "preservation_archive_records"
    __table_args__ = (
        UniqueConstraint("archive_key", name="uq_preservation_archive_key"),
        Index("ix_preservation_archive_subject", "subject_type", "subject_id", "archived_at"),
        Index("ix_preservation_archive_state", "state", "verified_at"),
    )
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    archive_key: Mapped[str] = mapped_column(String(255), nullable=False)
    subject_type: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    subject_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    state: Mapped[str] = mapped_column(String(40), nullable=False, default="archived", index=True)
    storage_kind: Mapped[str] = mapped_column(String(40), nullable=False, default="core-manifest")
    storage_uri: Mapped[str | None] = mapped_column(String(2000), nullable=True)
    snapshot_json: Mapped[dict] = mapped_column(JSON, default=dict)
    content_sha256: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    manifest_sha256: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    verification_state: Mapped[str] = mapped_column(String(40), nullable=False, default="verified", index=True)
    provenance_preserved: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)
    archived_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, index=True)
    verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    restored_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

class LifecycleHoldRecord(Base):
    __tablename__ = "lifecycle_hold_records"
    __table_args__ = (
        UniqueConstraint("hold_key", name="uq_lifecycle_hold_key"),
        Index("ix_lifecycle_hold_subject_state", "subject_type", "subject_id", "state"),
    )
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    hold_key: Mapped[str] = mapped_column(String(255), nullable=False)
    subject_type: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    subject_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    hold_type: Mapped[str] = mapped_column(String(40), nullable=False, default="policy", index=True)
    state: Mapped[str] = mapped_column(String(30), nullable=False, default="active", index=True)
    reason: Mapped[str] = mapped_column(Text, nullable=False, default="")
    actor: Mapped[str] = mapped_column(String(255), nullable=False, default="operator")
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)
    placed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    released_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

class LifecycleActionRecord(Base):
    __tablename__ = "lifecycle_action_records"
    __table_args__ = (Index("ix_lifecycle_action_subject_time", "subject_type", "subject_id", "created_at"),)
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    subject_type: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    subject_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    action_type: Mapped[str] = mapped_column(String(60), nullable=False, index=True)
    state: Mapped[str] = mapped_column(String(40), nullable=False, default="recorded", index=True)
    archive_id: Mapped[str | None] = mapped_column(ForeignKey("preservation_archive_records.id", ondelete="SET NULL"), nullable=True, index=True)
    actor: Mapped[str] = mapped_column(String(255), nullable=False, default="operator")
    automatic_execution: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    source_record_deleted: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    provenance_preserved: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    evidence_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, index=True)

# v2.23.0 — Federated Core & Trusted Node Exchange
class FederationNodeRecord(Base):
    __tablename__ = "federation_node_records"
    __table_args__ = (
        UniqueConstraint("node_key", name="uq_federation_node_key"),
        Index("ix_federation_node_trust_state", "trust_state", "state"),
    )
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    node_key: Mapped[str] = mapped_column(String(255), nullable=False)
    name: Mapped[str] = mapped_column(String(300), nullable=False)
    environment: Mapped[str] = mapped_column(String(40), nullable=False, default="production", index=True)
    base_url: Mapped[str | None] = mapped_column(String(2000), nullable=True)
    state: Mapped[str] = mapped_column(String(40), nullable=False, default="active", index=True)
    trust_state: Mapped[str] = mapped_column(String(40), nullable=False, default="pending", index=True)
    exchange_mode: Mapped[str] = mapped_column(String(30), nullable=False, default="pull")
    signing_key_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    signing_key_fingerprint: Mapped[str | None] = mapped_column(String(255), nullable=True)
    capabilities_json: Mapped[list] = mapped_column(JSON, default=list)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)
    last_seen_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

class FederationTrustRelationship(Base):
    __tablename__ = "federation_trust_relationships"
    __table_args__ = (
        UniqueConstraint("relationship_key", name="uq_federation_trust_relationship_key"),
        UniqueConstraint("remote_node_id", name="uq_federation_trust_remote_node"),
    )
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    relationship_key: Mapped[str] = mapped_column(String(255), nullable=False)
    remote_node_id: Mapped[str] = mapped_column(ForeignKey("federation_node_records.id", ondelete="CASCADE"), nullable=False, index=True)
    state: Mapped[str] = mapped_column(String(40), nullable=False, default="active", index=True)
    trust_level: Mapped[str] = mapped_column(String(40), nullable=False, default="trusted", index=True)
    allowed_subject_types_json: Mapped[list] = mapped_column(JSON, default=list)
    allow_snapshots: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    allow_private_records: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    signature_required: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    automatic_truth_promotion: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    automatic_ownership_transfer: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

class FederationExchangeManifest(Base):
    __tablename__ = "federation_exchange_manifests"
    __table_args__ = (
        UniqueConstraint("manifest_key", name="uq_federation_manifest_key"),
        Index("ix_federation_manifest_direction_state", "direction", "state", "created_at"),
        Index("ix_federation_manifest_nodes", "origin_node_key", "target_node_key", "created_at"),
    )
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    manifest_key: Mapped[str] = mapped_column(String(255), nullable=False)
    direction: Mapped[str] = mapped_column(String(20), nullable=False, default="outbound", index=True)
    origin_node_key: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    target_node_key: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    state: Mapped[str] = mapped_column(String(40), nullable=False, default="created", index=True)
    item_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    manifest_json: Mapped[dict] = mapped_column(JSON, default=dict)
    manifest_sha256: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    signature_algorithm: Mapped[str] = mapped_column(String(40), nullable=False, default="hmac-sha256")
    signature_key_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    signature_value: Mapped[str | None] = mapped_column(String(128), nullable=True)
    verification_state: Mapped[str] = mapped_column(String(40), nullable=False, default="unverified", index=True)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, index=True)
    verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    accepted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

class FederationRemoteReference(Base):
    __tablename__ = "federation_remote_references"
    __table_args__ = (
        UniqueConstraint("origin_node_key", "subject_type", "subject_id", "content_sha256", name="uq_federation_remote_reference"),
        Index("ix_federation_reference_subject", "subject_type", "subject_id", "created_at"),
        Index("ix_federation_reference_origin", "origin_node_key", "state", "created_at"),
    )
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    manifest_id: Mapped[str] = mapped_column(ForeignKey("federation_exchange_manifests.id", ondelete="CASCADE"), nullable=False, index=True)
    origin_node_key: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    subject_type: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    subject_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    canonical_uri: Mapped[str] = mapped_column(String(2000), nullable=False)
    content_sha256: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    visibility: Mapped[str] = mapped_column(String(30), nullable=False, default="internal", index=True)
    state: Mapped[str] = mapped_column(String(40), nullable=False, default="reference-only", index=True)
    provenance_json: Mapped[dict] = mapped_column(JSON, default=dict)
    automatic_truth_promotion: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    automatic_ownership_transfer: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    local_subject_overwritten: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, index=True)

# v2.24.0 — Capacity Forecasting & Resource Governance
class CapacityResourceProfile(Base):
    __tablename__ = "capacity_resource_profiles"
    __table_args__ = (
        UniqueConstraint("resource_type", "resource_key", "product_scope", name="uq_capacity_resource_scope"),
        Index("ix_capacity_profile_scope_state", "product_scope", "enabled", "resource_type"),
    )
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    resource_type: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    resource_key: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    product_scope: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    unit: Mapped[str] = mapped_column(String(80), nullable=False, default="count")
    capacity_limit: Mapped[float] = mapped_column(Float, nullable=False)
    warning_utilization: Mapped[float] = mapped_column(Float, nullable=False, default=0.80)
    critical_utilization: Mapped[float] = mapped_column(Float, nullable=False, default=0.95)
    forecast_horizon_hours: Mapped[int] = mapped_column(Integer, nullable=False, default=24)
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, index=True)
    public_summary: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)


class CapacityObservation(Base):
    __tablename__ = "capacity_observations"
    __table_args__ = (
        Index("ix_capacity_observation_profile_time", "profile_id", "observed_at"),
        Index("ix_capacity_observation_source_time", "source", "observed_at"),
    )
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    profile_id: Mapped[str] = mapped_column(ForeignKey("capacity_resource_profiles.id", ondelete="CASCADE"), nullable=False, index=True)
    used_value: Mapped[float] = mapped_column(Float, nullable=False)
    demand_value: Mapped[float | None] = mapped_column(Float, nullable=True)
    source: Mapped[str] = mapped_column(String(120), nullable=False, default="operator", index=True)
    observed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, index=True)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class CapacityBudget(Base):
    __tablename__ = "capacity_budgets"
    __table_args__ = (
        UniqueConstraint("budget_key", name="uq_capacity_budget_key"),
        Index("ix_capacity_budget_scope_resource", "product_scope", "resource_type", "enabled"),
    )
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    budget_key: Mapped[str] = mapped_column(String(255), nullable=False)
    name: Mapped[str] = mapped_column(String(300), nullable=False)
    product_scope: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    resource_type: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    resource_key: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    unit: Mapped[str] = mapped_column(String(80), nullable=False, default="count")
    budget_limit: Mapped[float] = mapped_column(Float, nullable=False)
    warning_fraction: Mapped[float] = mapped_column(Float, nullable=False, default=0.80)
    enforcement_mode: Mapped[str] = mapped_column(String(40), nullable=False, default="advisory", index=True)
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, index=True)
    public_summary: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)


class CapacityForecastRecord(Base):
    __tablename__ = "capacity_forecast_records"
    __table_args__ = (
        Index("ix_capacity_forecast_profile_time", "profile_id", "generated_at"),
        Index("ix_capacity_forecast_state_time", "state", "generated_at"),
    )
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    profile_id: Mapped[str] = mapped_column(ForeignKey("capacity_resource_profiles.id", ondelete="CASCADE"), nullable=False, index=True)
    method: Mapped[str] = mapped_column(String(60), nullable=False, default="bounded-linear")
    window_hours: Mapped[int] = mapped_column(Integer, nullable=False)
    horizon_hours: Mapped[int] = mapped_column(Integer, nullable=False)
    observed_points: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    current_value: Mapped[float | None] = mapped_column(Float, nullable=True)
    slope_per_hour: Mapped[float | None] = mapped_column(Float, nullable=True)
    predicted_value: Mapped[float | None] = mapped_column(Float, nullable=True)
    predicted_utilization: Mapped[float | None] = mapped_column(Float, nullable=True)
    confidence: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    state: Mapped[str] = mapped_column(String(40), nullable=False, default="insufficient-data", index=True)
    hours_to_capacity: Mapped[float | None] = mapped_column(Float, nullable=True)
    evidence_json: Mapped[dict] = mapped_column(JSON, default=dict)
    generated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, index=True)


class CapacityGovernanceDecision(Base):
    __tablename__ = "capacity_governance_decisions"
    __table_args__ = (
        Index("ix_capacity_decision_profile_time", "profile_id", "created_at"),
        Index("ix_capacity_decision_action_time", "action", "created_at"),
    )
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    profile_id: Mapped[str | None] = mapped_column(ForeignKey("capacity_resource_profiles.id", ondelete="SET NULL"), nullable=True, index=True)
    budget_id: Mapped[str | None] = mapped_column(ForeignKey("capacity_budgets.id", ondelete="SET NULL"), nullable=True, index=True)
    product_scope: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    action: Mapped[str] = mapped_column(String(40), nullable=False, default="allow", index=True)
    reason: Mapped[str] = mapped_column(String(500), nullable=False, default="within-governed-capacity")
    current_value: Mapped[float | None] = mapped_column(Float, nullable=True)
    forecast_value: Mapped[float | None] = mapped_column(Float, nullable=True)
    limit_value: Mapped[float | None] = mapped_column(Float, nullable=True)
    automatic_actuation: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    evidence_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, index=True)

# v2.25.0 — Identity, Credential & Cryptographic Key Lifecycle
class CredentialRegistryRecord(Base):
    __tablename__ = "credential_registry_records"
    __table_args__ = (
        UniqueConstraint("credential_key", name="uq_credential_registry_key"),
        Index("ix_credential_registry_owner_status", "owner_scope", "status", "enabled"),
        Index("ix_credential_registry_type_status", "credential_type", "status", "enabled"),
    )
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    credential_key: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(300), nullable=False)
    credential_type: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    purpose: Mapped[str] = mapped_column(String(300), nullable=False)
    owner_scope: Mapped[str] = mapped_column(String(120), nullable=False, default="platform-core", index=True)
    provider: Mapped[str] = mapped_column(String(120), nullable=False, default="environment")
    secret_reference: Mapped[str] = mapped_column(String(1000), nullable=False)
    allowed_consumers_json: Mapped[list] = mapped_column(JSON, default=list)
    allowed_operations_json: Mapped[list] = mapped_column(JSON, default=list)
    rotation_interval_days: Mapped[int] = mapped_column(Integer, nullable=False, default=90)
    overlap_minutes: Mapped[int] = mapped_column(Integer, nullable=False, default=60)
    status: Mapped[str] = mapped_column(String(40), nullable=False, default="active", index=True)
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, index=True)
    public_summary: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)


class CredentialKeyVersion(Base):
    __tablename__ = "credential_key_versions"
    __table_args__ = (
        UniqueConstraint("credential_id", "version", name="uq_credential_key_version"),
        UniqueConstraint("key_id", name="uq_credential_key_id"),
        Index("ix_credential_key_version_state", "credential_id", "state", "issued_at"),
        Index("ix_credential_key_expiry", "state", "expires_at"),
    )
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    credential_id: Mapped[str] = mapped_column(ForeignKey("credential_registry_records.id", ondelete="CASCADE"), nullable=False, index=True)
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    key_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    algorithm: Mapped[str] = mapped_column(String(80), nullable=False, default="opaque")
    fingerprint_sha256: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    state: Mapped[str] = mapped_column(String(40), nullable=False, default="staged", index=True)
    issued_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, index=True)
    activates_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    retire_after: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    revocation_reason: Mapped[str | None] = mapped_column(String(500), nullable=True)
    compromise_reported_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    secret_value_persisted: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)


class CredentialRotationRecord(Base):
    __tablename__ = "credential_rotation_records"
    __table_args__ = (
        Index("ix_credential_rotation_state", "credential_id", "state", "requested_at"),
    )
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    credential_id: Mapped[str] = mapped_column(ForeignKey("credential_registry_records.id", ondelete="CASCADE"), nullable=False, index=True)
    from_key_version_id: Mapped[str | None] = mapped_column(ForeignKey("credential_key_versions.id", ondelete="SET NULL"), nullable=True)
    to_key_version_id: Mapped[str] = mapped_column(ForeignKey("credential_key_versions.id", ondelete="RESTRICT"), nullable=False)
    state: Mapped[str] = mapped_column(String(40), nullable=False, default="planned", index=True)
    reason: Mapped[str] = mapped_column(String(500), nullable=False, default="scheduled-rotation")
    requested_by: Mapped[str] = mapped_column(String(255), nullable=False, default="operator")
    requested_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, index=True)
    overlap_starts_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    overlap_ends_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    automatic_secret_generation: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    automatic_secret_distribution: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    automatic_activation: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)


class CredentialLifecycleEvent(Base):
    __tablename__ = "credential_lifecycle_events"
    __table_args__ = (
        Index("ix_credential_lifecycle_event", "credential_id", "event_type", "created_at"),
    )
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    credential_id: Mapped[str] = mapped_column(ForeignKey("credential_registry_records.id", ondelete="CASCADE"), nullable=False, index=True)
    key_version_id: Mapped[str | None] = mapped_column(ForeignKey("credential_key_versions.id", ondelete="SET NULL"), nullable=True, index=True)
    event_type: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    actor: Mapped[str] = mapped_column(String(255), nullable=False, default="operator")
    detail: Mapped[str] = mapped_column(String(1000), nullable=False, default="")
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, index=True)


class CredentialUseEvent(Base):
    __tablename__ = "credential_use_events"
    __table_args__ = (
        Index("ix_credential_use_event", "credential_id", "occurred_at"),
        Index("ix_credential_use_service", "service_id", "occurred_at"),
    )
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    credential_id: Mapped[str] = mapped_column(ForeignKey("credential_registry_records.id", ondelete="CASCADE"), nullable=False, index=True)
    key_version_id: Mapped[str | None] = mapped_column(ForeignKey("credential_key_versions.id", ondelete="SET NULL"), nullable=True, index=True)
    service_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    operation: Mapped[str] = mapped_column(String(120), nullable=False)
    success: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    context_json: Mapped[dict] = mapped_column(JSON, default=dict)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, index=True)


# v2.26.0 — Distributed Quotas, Admission Control & Workload Governance
class WorkloadClassRecord(Base):
    __tablename__ = "workload_class_records"
    __table_args__ = (
        UniqueConstraint("class_key", name="uq_workload_class_key"),
        Index("ix_workload_class_priority_enabled", "priority", "enabled"),
    )
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    class_key: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    priority: Mapped[int] = mapped_column(Integer, nullable=False, default=100, index=True)
    queue_weight: Mapped[float] = mapped_column(Float, nullable=False, default=1.0)
    max_concurrent_leases: Mapped[int] = mapped_column(Integer, nullable=False, default=64)
    max_request_units: Mapped[float] = mapped_column(Float, nullable=False, default=1000.0)
    allow_when_slo_breached: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    allow_when_capacity_critical: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, index=True)
    public_summary: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)


class DistributedQuotaPolicy(Base):
    __tablename__ = "distributed_quota_policies"
    __table_args__ = (
        UniqueConstraint("policy_key", name="uq_distributed_quota_policy_key"),
        Index("ix_quota_policy_subject_resource", "subject_scope", "subject_key", "resource_type", "enabled"),
    )
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    policy_key: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(300), nullable=False)
    subject_scope: Mapped[str] = mapped_column(String(80), nullable=False, default="product", index=True)
    subject_key: Mapped[str] = mapped_column(String(255), nullable=False, default="*", index=True)
    resource_type: Mapped[str] = mapped_column(String(120), nullable=False, default="requests", index=True)
    workload_class_key: Mapped[str | None] = mapped_column(String(120), nullable=True, index=True)
    window_seconds: Mapped[int] = mapped_column(Integer, nullable=False, default=60)
    limit_units: Mapped[float] = mapped_column(Float, nullable=False, default=1000.0)
    burst_units: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    enforcement_mode: Mapped[str] = mapped_column(String(40), nullable=False, default="enforce", index=True)
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, index=True)
    public_summary: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)


class DistributedQuotaUsageBucket(Base):
    __tablename__ = "distributed_quota_usage_buckets"
    __table_args__ = (
        UniqueConstraint("policy_id", "bucket_start", name="uq_quota_usage_policy_bucket"),
        Index("ix_quota_usage_policy_time", "policy_id", "bucket_start"),
    )
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    policy_id: Mapped[str] = mapped_column(ForeignKey("distributed_quota_policies.id", ondelete="CASCADE"), nullable=False, index=True)
    bucket_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    used_units: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    admitted_requests: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    rejected_requests: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    throttled_requests: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)


class WorkloadAdmissionDecision(Base):
    __tablename__ = "workload_admission_decisions"
    __table_args__ = (
        UniqueConstraint("request_key", name="uq_workload_admission_request_key"),
        Index("ix_admission_decision_subject_time", "subject_scope", "subject_key", "created_at"),
        Index("ix_admission_decision_state_time", "decision", "created_at"),
    )
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    request_key: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    subject_scope: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    subject_key: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    resource_type: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    workload_class_key: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    requested_units: Mapped[float] = mapped_column(Float, nullable=False)
    decision: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    reason: Mapped[str] = mapped_column(String(500), nullable=False)
    policy_id: Mapped[str | None] = mapped_column(ForeignKey("distributed_quota_policies.id", ondelete="SET NULL"), nullable=True, index=True)
    quota_limit: Mapped[float | None] = mapped_column(Float, nullable=True)
    quota_used_before: Mapped[float | None] = mapped_column(Float, nullable=True)
    quota_remaining_after: Mapped[float | None] = mapped_column(Float, nullable=True)
    retry_after_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)
    capacity_state: Mapped[str] = mapped_column(String(60), nullable=False, default="unknown")
    slo_state: Mapped[str] = mapped_column(String(60), nullable=False, default="unknown")
    hard_enforcement: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    evidence_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, index=True)


class WorkloadAdmissionLease(Base):
    __tablename__ = "workload_admission_leases"
    __table_args__ = (
        UniqueConstraint("lease_key", name="uq_workload_admission_lease_key"),
        Index("ix_admission_lease_class_state_expiry", "workload_class_key", "state", "expires_at"),
        Index("ix_admission_lease_subject_state", "subject_scope", "subject_key", "state"),
    )
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    lease_key: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    decision_id: Mapped[str] = mapped_column(ForeignKey("workload_admission_decisions.id", ondelete="CASCADE"), nullable=False, index=True)
    subject_scope: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    subject_key: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    workload_class_key: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    units: Mapped[float] = mapped_column(Float, nullable=False, default=1.0)
    state: Mapped[str] = mapped_column(String(40), nullable=False, default="active", index=True)
    acquired_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    released_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)


# v2.27.0 — Scientific Object Storage & Processing Adapter Fabric
class ScientificStorageBackend(Base):
    __tablename__ = "scientific_storage_backends"
    __table_args__ = (
        UniqueConstraint("backend_key", name="uq_scientific_storage_backend_key"),
        Index("ix_scientific_storage_backend_type_enabled", "backend_type", "enabled"),
    )
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    backend_key: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    backend_type: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    uri_scheme: Mapped[str] = mapped_column(String(40), nullable=False)
    readable: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    writable: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, index=True)
    public_summary: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    capabilities_json: Mapped[dict] = mapped_column(JSON, default=dict)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)


class ScientificStoredObject(Base):
    __tablename__ = "scientific_stored_objects"
    __table_args__ = (
        Index("ix_scientific_object_asset", "scientific_asset_id"),
        Index("ix_scientific_object_backend_state", "backend_key", "lifecycle_state"),
        Index("ix_scientific_object_hash", "content_hash"),
        Index("ix_scientific_object_public_created", "public", "created_at"),
        Index("ix_scientific_object_parent", "parent_object_id"),
    )
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    scientific_asset_id: Mapped[str | None] = mapped_column(ForeignKey("scientific_data_assets.id", ondelete="SET NULL"), nullable=True, index=True)
    parent_object_id: Mapped[str | None] = mapped_column(ForeignKey("scientific_stored_objects.id", ondelete="SET NULL"), nullable=True, index=True)
    backend_key: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    object_key: Mapped[str] = mapped_column(String(700), nullable=False, index=True)
    canonical_uri: Mapped[str] = mapped_column(String(3000), nullable=False)
    title: Mapped[str] = mapped_column(String(1000), nullable=False)
    format: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    media_type: Mapped[str | None] = mapped_column(String(300), nullable=True)
    size_bytes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    content_hash: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    checksum_algorithm: Mapped[str | None] = mapped_column(String(40), nullable=True)
    integrity_status: Mapped[str] = mapped_column(String(60), nullable=False, default="unverified", index=True)
    lifecycle_state: Mapped[str] = mapped_column(String(60), nullable=False, default="active", index=True)
    retention_class: Mapped[str] = mapped_column(String(80), nullable=False, default="standard", index=True)
    derived: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, index=True)
    public: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, index=True)
    license_name: Mapped[str | None] = mapped_column(String(300), nullable=True)
    attribution: Mapped[str | None] = mapped_column(Text, nullable=True)
    provenance_json: Mapped[dict] = mapped_column(JSON, default=dict)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_by: Mapped[str] = mapped_column(String(255), nullable=False, default="operator")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)


class ScientificProcessingAdapter(Base):
    __tablename__ = "scientific_processing_adapters"
    __table_args__ = (
        UniqueConstraint("adapter_key", name="uq_scientific_processing_adapter_key"),
        Index("ix_scientific_processing_adapter_enabled", "enabled", "execution_mode"),
    )
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    adapter_key: Mapped[str] = mapped_column(String(160), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(300), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    execution_mode: Mapped[str] = mapped_column(String(80), nullable=False, default="external-contract", index=True)
    runtime: Mapped[str] = mapped_column(String(80), nullable=False, default="python")
    supported_input_formats_json: Mapped[list] = mapped_column(JSON, default=list)
    supported_output_formats_json: Mapped[list] = mapped_column(JSON, default=list)
    operations_json: Mapped[list] = mapped_column(JSON, default=list)
    configuration_schema_json: Mapped[dict] = mapped_column(JSON, default=dict)
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, index=True)
    executable: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    public_summary: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)


class ScientificProcessingRun(Base):
    __tablename__ = "scientific_processing_runs"
    __table_args__ = (
        UniqueConstraint("adapter_id", "input_object_id", "operation", "idempotency_key", name="uq_scientific_processing_run_idempotency"),
        Index("ix_scientific_processing_run_state", "state", "created_at"),
        Index("ix_scientific_processing_run_input", "input_object_id", "created_at"),
    )
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    adapter_id: Mapped[str] = mapped_column(ForeignKey("scientific_processing_adapters.id", ondelete="RESTRICT"), nullable=False, index=True)
    input_object_id: Mapped[str] = mapped_column(ForeignKey("scientific_stored_objects.id", ondelete="RESTRICT"), nullable=False, index=True)
    output_object_id: Mapped[str | None] = mapped_column(ForeignKey("scientific_stored_objects.id", ondelete="SET NULL"), nullable=True, index=True)
    operation: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    idempotency_key: Mapped[str] = mapped_column(String(255), nullable=False)
    state: Mapped[str] = mapped_column(String(60), nullable=False, default="queued", index=True)
    parameters_json: Mapped[dict] = mapped_column(JSON, default=dict)
    provenance_json: Mapped[dict] = mapped_column(JSON, default=dict)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    requested_by: Mapped[str] = mapped_column(String(255), nullable=False, default="operator")
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

# v2.28.0 — Research Object & Model Foundation

class ResearchProjectRecord(Base):
    __tablename__ = "research_projects"
    __table_args__ = (
        Index("ix_research_project_state", "lifecycle_state"),
        Index("ix_research_project_owner", "owner_product"),
    )
    entity_id: Mapped[str] = mapped_column(ForeignKey("entities.id", ondelete="CASCADE"), primary_key=True)
    research_question: Mapped[str | None] = mapped_column(Text, nullable=True)
    objective: Mapped[str | None] = mapped_column(Text, nullable=True)
    methodology: Mapped[str | None] = mapped_column(Text, nullable=True)
    owner_product: Mapped[str] = mapped_column(String(80), default="workspace", index=True)
    lifecycle_state: Mapped[str] = mapped_column(String(50), default="draft", index=True)
    reproducibility_target: Mapped[str] = mapped_column(String(50), default="reproducible")
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)


class ResearchModelRecord(Base):
    __tablename__ = "research_models"
    __table_args__ = (
        Index("ix_research_model_project", "project_entity_id"),
        Index("ix_research_model_kind", "model_kind"),
    )
    entity_id: Mapped[str] = mapped_column(ForeignKey("entities.id", ondelete="CASCADE"), primary_key=True)
    project_entity_id: Mapped[str | None] = mapped_column(ForeignKey("entities.id", ondelete="SET NULL"), nullable=True)
    model_kind: Mapped[str] = mapped_column(String(80), default="conceptual", index=True)
    execution_target: Mapped[str] = mapped_column(String(80), default="not-executable")
    specification_json: Mapped[dict] = mapped_column(JSON, default=dict)
    assumptions_json: Mapped[list] = mapped_column(JSON, default=list)
    equations_json: Mapped[list] = mapped_column(JSON, default=list)
    reproducibility_status: Mapped[str] = mapped_column(String(50), default="declared")
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)


class ResearchModelVersionRecord(Base):
    __tablename__ = "research_model_versions"
    __table_args__ = (
        UniqueConstraint("model_entity_id", "version_label", name="uq_research_model_version_label"),
        Index("ix_research_model_version_model", "model_entity_id"),
        Index("ix_research_model_version_hash", "specification_hash"),
    )
    entity_id: Mapped[str] = mapped_column(ForeignKey("entities.id", ondelete="CASCADE"), primary_key=True)
    model_entity_id: Mapped[str] = mapped_column(ForeignKey("entities.id", ondelete="CASCADE"), nullable=False)
    version_label: Mapped[str] = mapped_column(String(100), nullable=False)
    code_version: Mapped[str | None] = mapped_column(String(200), nullable=True)
    specification_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    specification_json: Mapped[dict] = mapped_column(JSON, default=dict)
    immutable: Mapped[bool] = mapped_column(Boolean, default=True)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class ResearchVariableRecord(Base):
    __tablename__ = "research_variables"
    __table_args__ = (
        UniqueConstraint("model_entity_id", "symbol", name="uq_research_variable_symbol"),
        Index("ix_research_variable_model", "model_entity_id"),
        Index("ix_research_variable_role", "role"),
    )
    entity_id: Mapped[str] = mapped_column(ForeignKey("entities.id", ondelete="CASCADE"), primary_key=True)
    model_entity_id: Mapped[str] = mapped_column(ForeignKey("entities.id", ondelete="CASCADE"), nullable=False)
    symbol: Mapped[str] = mapped_column(String(160), nullable=False)
    role: Mapped[str] = mapped_column(String(50), default="input", index=True)
    data_type: Mapped[str] = mapped_column(String(50), default="number")
    unit: Mapped[str | None] = mapped_column(String(120), nullable=True)
    definition: Mapped[str | None] = mapped_column(Text, nullable=True)
    domain_json: Mapped[dict] = mapped_column(JSON, default=dict)
    uncertainty_json: Mapped[dict] = mapped_column(JSON, default=dict)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)


class ResearchParameterRecord(Base):
    __tablename__ = "research_parameters"
    __table_args__ = (
        UniqueConstraint("model_entity_id", "name", name="uq_research_parameter_name"),
        Index("ix_research_parameter_model", "model_entity_id"),
    )
    entity_id: Mapped[str] = mapped_column(ForeignKey("entities.id", ondelete="CASCADE"), primary_key=True)
    model_entity_id: Mapped[str] = mapped_column(ForeignKey("entities.id", ondelete="CASCADE"), nullable=False)
    variable_entity_id: Mapped[str | None] = mapped_column(ForeignKey("entities.id", ondelete="SET NULL"), nullable=True)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    data_type: Mapped[str] = mapped_column(String(50), default="number")
    unit: Mapped[str | None] = mapped_column(String(120), nullable=True)
    default_value_json: Mapped[dict] = mapped_column(JSON, default=dict)
    bounds_json: Mapped[dict] = mapped_column(JSON, default=dict)
    prior_json: Mapped[dict] = mapped_column(JSON, default=dict)
    sensitivity_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)


class ResearchScenarioRecord(Base):
    __tablename__ = "research_scenarios"
    __table_args__ = (
        Index("ix_research_scenario_project", "project_entity_id"),
        Index("ix_research_scenario_base", "base_scenario_entity_id"),
        Index("ix_research_scenario_state", "scenario_state"),
    )
    entity_id: Mapped[str] = mapped_column(ForeignKey("entities.id", ondelete="CASCADE"), primary_key=True)
    project_entity_id: Mapped[str] = mapped_column(ForeignKey("entities.id", ondelete="CASCADE"), nullable=False)
    base_scenario_entity_id: Mapped[str | None] = mapped_column(ForeignKey("entities.id", ondelete="SET NULL"), nullable=True)
    scenario_state: Mapped[str] = mapped_column(String(50), default="draft", index=True)
    parameter_values_json: Mapped[dict] = mapped_column(JSON, default=dict)
    assumptions_json: Mapped[list] = mapped_column(JSON, default=list)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)


class ResearchModelRunRecord(Base):
    __tablename__ = "research_model_runs"
    __table_args__ = (
        Index("ix_research_model_run_version", "model_version_entity_id"),
        Index("ix_research_model_run_scenario", "scenario_entity_id"),
        Index("ix_research_model_run_status", "run_status"),
    )
    entity_id: Mapped[str] = mapped_column(ForeignKey("entities.id", ondelete="CASCADE"), primary_key=True)
    model_version_entity_id: Mapped[str] = mapped_column(ForeignKey("entities.id", ondelete="RESTRICT"), nullable=False)
    scenario_entity_id: Mapped[str | None] = mapped_column(ForeignKey("entities.id", ondelete="SET NULL"), nullable=True)
    executor_product: Mapped[str] = mapped_column(String(80), default="lab")
    external_run_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    run_status: Mapped[str] = mapped_column(String(50), default="requested", index=True)
    parameter_values_json: Mapped[dict] = mapped_column(JSON, default=dict)
    runtime_json: Mapped[dict] = mapped_column(JSON, default=dict)
    provenance_activity_id: Mapped[str | None] = mapped_column(ForeignKey("provenance_activities.id", ondelete="SET NULL"), nullable=True)
    calculation_trace_id: Mapped[str | None] = mapped_column(ForeignKey("calculation_traces.id", ondelete="SET NULL"), nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)


class ResearchResultRecord(Base):
    __tablename__ = "research_results"
    __table_args__ = (
        Index("ix_research_result_run", "model_run_entity_id"),
        Index("ix_research_result_kind", "result_kind"),
        Index("ix_research_result_quality", "quality_status"),
    )
    entity_id: Mapped[str] = mapped_column(ForeignKey("entities.id", ondelete="CASCADE"), primary_key=True)
    model_run_entity_id: Mapped[str] = mapped_column(ForeignKey("entities.id", ondelete="CASCADE"), nullable=False)
    result_kind: Mapped[str] = mapped_column(String(80), default="summary", index=True)
    value_json: Mapped[dict] = mapped_column(JSON, default=dict)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    scientific_object_id: Mapped[str | None] = mapped_column(ForeignKey("scientific_stored_objects.id", ondelete="SET NULL"), nullable=True)
    quality_status: Mapped[str] = mapped_column(String(50), default="unreviewed", index=True)
    uncertainty_json: Mapped[dict] = mapped_column(JSON, default=dict)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)


# v2.29.0 — Visual Reasoning Object Model

class VisualReasoningObjectRecord(Base):
    __tablename__ = "visual_reasoning_objects"
    __table_args__ = (
        Index("ix_visual_reasoning_project", "project_entity_id"),
        Index("ix_visual_reasoning_subject", "primary_subject_entity_id"),
        Index("ix_visual_reasoning_kind_state", "visual_kind", "semantic_state"),
    )
    entity_id: Mapped[str] = mapped_column(ForeignKey("entities.id", ondelete="CASCADE"), primary_key=True)
    project_entity_id: Mapped[str | None] = mapped_column(ForeignKey("entities.id", ondelete="SET NULL"), nullable=True)
    primary_subject_entity_id: Mapped[str | None] = mapped_column(ForeignKey("entities.id", ondelete="SET NULL"), nullable=True)
    visual_kind: Mapped[str] = mapped_column(String(80), nullable=False, default="generic", index=True)
    reasoning_purpose: Mapped[str] = mapped_column(String(80), nullable=False, default="explore")
    semantic_state: Mapped[str] = mapped_column(String(50), nullable=False, default="draft", index=True)
    coordinate_space: Mapped[str] = mapped_column(String(50), nullable=False, default="abstract")
    lens_json: Mapped[dict] = mapped_column(JSON, default=dict)
    filters_json: Mapped[dict] = mapped_column(JSON, default=dict)
    assumptions_json: Mapped[list] = mapped_column(JSON, default=list)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)


class VisualReasoningElementRecord(Base):
    __tablename__ = "visual_reasoning_elements"
    __table_args__ = (
        UniqueConstraint("visual_entity_id", "element_key", name="uq_visual_reasoning_element_key"),
        Index("ix_visual_reasoning_element_visual", "visual_entity_id"),
        Index("ix_visual_reasoning_element_source", "source_entity_id"),
        Index("ix_visual_reasoning_element_role", "semantic_role"),
    )
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    visual_entity_id: Mapped[str] = mapped_column(ForeignKey("entities.id", ondelete="CASCADE"), nullable=False)
    element_key: Mapped[str] = mapped_column(String(180), nullable=False)
    element_kind: Mapped[str] = mapped_column(String(60), nullable=False, default="node")
    semantic_role: Mapped[str] = mapped_column(String(80), nullable=False, default="context", index=True)
    label: Mapped[str] = mapped_column(String(300), nullable=False)
    source_entity_id: Mapped[str | None] = mapped_column(ForeignKey("entities.id", ondelete="SET NULL"), nullable=True)
    source_scientific_object_id: Mapped[str | None] = mapped_column(ForeignKey("scientific_stored_objects.id", ondelete="SET NULL"), nullable=True)
    value_json: Mapped[object] = mapped_column(JSON, nullable=True)
    uncertainty_json: Mapped[dict] = mapped_column(JSON, default=dict)
    provenance_json: Mapped[dict] = mapped_column(JSON, default=dict)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)


class VisualReasoningRelationRecord(Base):
    __tablename__ = "visual_reasoning_relations"
    __table_args__ = (
        UniqueConstraint("visual_entity_id", "source_element_id", "relation_kind", "target_element_id", name="uq_visual_reasoning_relation"),
        Index("ix_visual_reasoning_relation_visual", "visual_entity_id"),
        Index("ix_visual_reasoning_relation_kind", "relation_kind"),
    )
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    visual_entity_id: Mapped[str] = mapped_column(ForeignKey("entities.id", ondelete="CASCADE"), nullable=False)
    source_element_id: Mapped[str] = mapped_column(ForeignKey("visual_reasoning_elements.id", ondelete="CASCADE"), nullable=False)
    target_element_id: Mapped[str] = mapped_column(ForeignKey("visual_reasoning_elements.id", ondelete="CASCADE"), nullable=False)
    relation_kind: Mapped[str] = mapped_column(String(80), nullable=False, default="association", index=True)
    direction: Mapped[str] = mapped_column(String(30), nullable=False, default="directed")
    magnitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    uncertainty_json: Mapped[dict] = mapped_column(JSON, default=dict)
    provenance_json: Mapped[dict] = mapped_column(JSON, default=dict)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class VisualReasoningLayerRecord(Base):
    __tablename__ = "visual_reasoning_layers"
    __table_args__ = (
        UniqueConstraint("visual_entity_id", "layer_key", name="uq_visual_reasoning_layer_key"),
        Index("ix_visual_reasoning_layer_visual", "visual_entity_id"),
    )
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    visual_entity_id: Mapped[str] = mapped_column(ForeignKey("entities.id", ondelete="CASCADE"), nullable=False)
    layer_key: Mapped[str] = mapped_column(String(180), nullable=False)
    name: Mapped[str] = mapped_column(String(300), nullable=False)
    layer_kind: Mapped[str] = mapped_column(String(80), nullable=False, default="context")
    order_index: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    visible_by_default: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    filter_json: Mapped[dict] = mapped_column(JSON, default=dict)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class VisualReasoningAnnotationRecord(Base):
    __tablename__ = "visual_reasoning_annotations"
    __table_args__ = (
        Index("ix_visual_reasoning_annotation_visual", "visual_entity_id"),
        Index("ix_visual_reasoning_annotation_kind", "annotation_kind"),
    )
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    visual_entity_id: Mapped[str] = mapped_column(ForeignKey("entities.id", ondelete="CASCADE"), nullable=False)
    element_id: Mapped[str | None] = mapped_column(ForeignKey("visual_reasoning_elements.id", ondelete="CASCADE"), nullable=True)
    relation_id: Mapped[str | None] = mapped_column(ForeignKey("visual_reasoning_relations.id", ondelete="CASCADE"), nullable=True)
    annotation_kind: Mapped[str] = mapped_column(String(80), nullable=False, default="note")
    text: Mapped[str] = mapped_column(Text, nullable=False)
    evidence_entity_id: Mapped[str | None] = mapped_column(ForeignKey("entities.id", ondelete="SET NULL"), nullable=True)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class VisualReasoningSnapshotRecord(Base):
    __tablename__ = "visual_reasoning_snapshots"
    __table_args__ = (
        UniqueConstraint("visual_entity_id", "snapshot_key", name="uq_visual_reasoning_snapshot_key"),
        Index("ix_visual_reasoning_snapshot_visual", "visual_entity_id", "created_at"),
        Index("ix_visual_reasoning_snapshot_hash", "state_hash"),
    )
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    visual_entity_id: Mapped[str] = mapped_column(ForeignKey("entities.id", ondelete="CASCADE"), nullable=False)
    snapshot_key: Mapped[str] = mapped_column(String(180), nullable=False)
    state_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    semantic_state_json: Mapped[dict] = mapped_column(JSON, default=dict)
    provenance_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_by: Mapped[str] = mapped_column(String(255), nullable=False, default="operator")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

# v2.30.0 — Visualization Specification & Renderer Registry

class VisualizationSpecificationRecord(Base):
    __tablename__ = "visualization_specifications"
    __table_args__ = (
        UniqueConstraint("visual_entity_id", "spec_key", "revision", name="uq_visualization_spec_revision"),
        Index("ix_visualization_spec_visual", "visual_entity_id"),
        Index("ix_visualization_spec_kind", "spec_kind"),
        Index("ix_visualization_spec_hash", "state_hash"),
    )
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    visual_entity_id: Mapped[str] = mapped_column(ForeignKey("entities.id", ondelete="CASCADE"), nullable=False)
    spec_key: Mapped[str] = mapped_column(String(180), nullable=False)
    revision: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    spec_version: Mapped[str] = mapped_column(String(30), nullable=False, default="1.0")
    spec_kind: Mapped[str] = mapped_column(String(80), nullable=False, default="generic")
    title: Mapped[str | None] = mapped_column(String(300), nullable=True)
    preferred_renderer_key: Mapped[str | None] = mapped_column(String(180), nullable=True)
    renderer_policy: Mapped[str] = mapped_column(String(50), nullable=False, default="compatible")
    encoding_json: Mapped[dict] = mapped_column(JSON, default=dict)
    interaction_json: Mapped[dict] = mapped_column(JSON, default=dict)
    accessibility_json: Mapped[dict] = mapped_column(JSON, default=dict)
    layout_constraints_json: Mapped[dict] = mapped_column(JSON, default=dict)
    export_json: Mapped[dict] = mapped_column(JSON, default=dict)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)
    state_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    created_by: Mapped[str] = mapped_column(String(255), nullable=False, default="operator")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class RendererDefinitionRecord(Base):
    __tablename__ = "renderer_definitions"
    renderer_key: Mapped[str] = mapped_column(String(180), primary_key=True)
    name: Mapped[str] = mapped_column(String(300), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    renderer_family: Mapped[str] = mapped_column(String(100), nullable=False)
    runtime: Mapped[str] = mapped_column(String(80), nullable=False, default="external-runtime")
    execution_mode: Mapped[str] = mapped_column(String(80), nullable=False, default="contract-only")
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, index=True)
    executable_by_core: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    public_summary: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    supported_spec_versions_json: Mapped[list] = mapped_column(JSON, default=list)
    capabilities_json: Mapped[dict] = mapped_column(JSON, default=dict)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)


class RendererVersionRecord(Base):
    __tablename__ = "renderer_versions"
    __table_args__ = (
        UniqueConstraint("renderer_key", "version", name="uq_renderer_version"),
        Index("ix_renderer_version_renderer", "renderer_key"),
        Index("ix_renderer_version_status", "status"),
    )
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    renderer_key: Mapped[str] = mapped_column(ForeignKey("renderer_definitions.renderer_key", ondelete="CASCADE"), nullable=False)
    version: Mapped[str] = mapped_column(String(80), nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="active")
    contract_version: Mapped[str] = mapped_column(String(30), nullable=False, default="1.0")
    capabilities_json: Mapped[dict] = mapped_column(JSON, default=dict)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class RendererCompatibilityRuleRecord(Base):
    __tablename__ = "renderer_compatibility_rules"
    __table_args__ = (
        UniqueConstraint("renderer_key", "visual_kind", "spec_kind", name="uq_renderer_compat_rule"),
        Index("ix_renderer_compat_visual_kind", "visual_kind"),
        Index("ix_renderer_compat_spec_kind", "spec_kind"),
    )
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    renderer_key: Mapped[str] = mapped_column(ForeignKey("renderer_definitions.renderer_key", ondelete="CASCADE"), nullable=False)
    visual_kind: Mapped[str] = mapped_column(String(80), nullable=False)
    spec_kind: Mapped[str] = mapped_column(String(80), nullable=False)
    priority: Mapped[int] = mapped_column(Integer, nullable=False, default=100)
    required_capabilities_json: Mapped[list] = mapped_column(JSON, default=list)
    constraints_json: Mapped[dict] = mapped_column(JSON, default=dict)
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class RendererResolutionRecord(Base):
    __tablename__ = "renderer_resolution_records"
    __table_args__ = (
        Index("ix_renderer_resolution_spec", "specification_id", "created_at"),
        Index("ix_renderer_resolution_renderer", "resolved_renderer_key"),
    )
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    specification_id: Mapped[str] = mapped_column(ForeignKey("visualization_specifications.id", ondelete="CASCADE"), nullable=False)
    requested_renderer_key: Mapped[str | None] = mapped_column(String(180), nullable=True)
    resolved_renderer_key: Mapped[str | None] = mapped_column(ForeignKey("renderer_definitions.renderer_key", ondelete="SET NULL"), nullable=True)
    resolved_renderer_version: Mapped[str | None] = mapped_column(String(80), nullable=True)
    resolution_state: Mapped[str] = mapped_column(String(50), nullable=False, default="resolved")
    selection_mode: Mapped[str] = mapped_column(String(80), nullable=False, default="registry-priority")
    rationale_json: Mapped[dict] = mapped_column(JSON, default=dict)
    execution_performed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_by: Mapped[str] = mapped_column(String(255), nullable=False, default="operator")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


# v2.33.0 — System Maps

class SystemMapRecord(Base):
    __tablename__ = "system_maps"
    visual_entity_id: Mapped[str] = mapped_column(ForeignKey("visual_reasoning_objects.entity_id", ondelete="CASCADE"), primary_key=True)
    system_purpose: Mapped[str] = mapped_column(String(120), nullable=False, default="explore")
    perspective: Mapped[str | None] = mapped_column(String(300), nullable=True)
    map_state: Mapped[str] = mapped_column(String(50), nullable=False, default="draft", index=True)
    boundary_statement: Mapped[str | None] = mapped_column(Text, nullable=True)
    assumptions_json: Mapped[list] = mapped_column(JSON, default=list)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_by: Mapped[str] = mapped_column(String(255), nullable=False, default="operator")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)


class SystemMapBoundaryRecord(Base):
    __tablename__ = "system_map_boundaries"
    __table_args__ = (
        UniqueConstraint("visual_entity_id", "boundary_key", name="uq_system_map_boundary_key"),
        Index("ix_system_map_boundary_visual", "visual_entity_id"),
        Index("ix_system_map_boundary_kind", "boundary_kind"),
    )
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    visual_entity_id: Mapped[str] = mapped_column(ForeignKey("system_maps.visual_entity_id", ondelete="CASCADE"), nullable=False)
    boundary_key: Mapped[str] = mapped_column(String(180), nullable=False)
    boundary_kind: Mapped[str] = mapped_column(String(50), nullable=False, default="included")
    name: Mapped[str] = mapped_column(String(300), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    criteria_json: Mapped[dict] = mapped_column(JSON, default=dict)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class SystemMapDomainRecord(Base):
    __tablename__ = "system_map_domains"
    __table_args__ = (
        UniqueConstraint("visual_entity_id", "domain_key", name="uq_system_map_domain_key"),
        Index("ix_system_map_domain_visual", "visual_entity_id"),
        Index("ix_system_map_domain_parent", "parent_domain_id"),
    )
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    visual_entity_id: Mapped[str] = mapped_column(ForeignKey("system_maps.visual_entity_id", ondelete="CASCADE"), nullable=False)
    domain_key: Mapped[str] = mapped_column(String(180), nullable=False)
    name: Mapped[str] = mapped_column(String(300), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    parent_domain_id: Mapped[str | None] = mapped_column(ForeignKey("system_map_domains.id", ondelete="SET NULL"), nullable=True)
    order_index: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class SystemMapMembershipRecord(Base):
    __tablename__ = "system_map_memberships"
    __table_args__ = (
        UniqueConstraint("domain_id", "element_id", name="uq_system_map_domain_element"),
        Index("ix_system_map_membership_visual", "visual_entity_id"),
        Index("ix_system_map_membership_element", "element_id"),
    )
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    visual_entity_id: Mapped[str] = mapped_column(ForeignKey("system_maps.visual_entity_id", ondelete="CASCADE"), nullable=False)
    domain_id: Mapped[str] = mapped_column(ForeignKey("system_map_domains.id", ondelete="CASCADE"), nullable=False)
    element_id: Mapped[str] = mapped_column(ForeignKey("visual_reasoning_elements.id", ondelete="CASCADE"), nullable=False)
    membership_role: Mapped[str] = mapped_column(String(80), nullable=False, default="member")
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class SystemMapViewRecord(Base):
    __tablename__ = "system_map_views"
    __table_args__ = (
        UniqueConstraint("visual_entity_id", "view_key", name="uq_system_map_view_key"),
        Index("ix_system_map_view_visual", "visual_entity_id"),
    )
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    visual_entity_id: Mapped[str] = mapped_column(ForeignKey("system_maps.visual_entity_id", ondelete="CASCADE"), nullable=False)
    view_key: Mapped[str] = mapped_column(String(180), nullable=False)
    name: Mapped[str] = mapped_column(String(300), nullable=False)
    lens_json: Mapped[dict] = mapped_column(JSON, default=dict)
    filters_json: Mapped[dict] = mapped_column(JSON, default=dict)
    highlights_json: Mapped[list] = mapped_column(JSON, default=list)
    layout_intent_json: Mapped[dict] = mapped_column(JSON, default=dict)
    specification_id: Mapped[str | None] = mapped_column(ForeignKey("visualization_specifications.id", ondelete="SET NULL"), nullable=True)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


# v2.33.0 — Flow Maps

class FlowMapRecord(Base):
    __tablename__ = "flow_maps"
    visual_entity_id: Mapped[str] = mapped_column(ForeignKey("visual_reasoning_objects.entity_id", ondelete="CASCADE"), primary_key=True)
    flow_purpose: Mapped[str] = mapped_column(String(120), nullable=False, default="trace")
    flow_domain: Mapped[str] = mapped_column(String(120), nullable=False, default="generic")
    map_state: Mapped[str] = mapped_column(String(50), nullable=False, default="draft", index=True)
    quantity_mode: Mapped[str] = mapped_column(String(50), nullable=False, default="mixed")
    default_unit: Mapped[str | None] = mapped_column(String(100), nullable=True)
    time_basis: Mapped[str] = mapped_column(String(50), nullable=False, default="unspecified")
    conservation_policy: Mapped[str] = mapped_column(String(50), nullable=False, default="advisory")
    assumptions_json: Mapped[list] = mapped_column(JSON, default=list)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_by: Mapped[str] = mapped_column(String(255), nullable=False, default="operator")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)


class FlowMapChannelRecord(Base):
    __tablename__ = "flow_map_channels"
    __table_args__ = (
        UniqueConstraint("visual_entity_id", "channel_key", name="uq_flow_map_channel_key"),
        Index("ix_flow_map_channel_visual", "visual_entity_id"),
        Index("ix_flow_map_channel_kind", "flow_kind"),
    )
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    visual_entity_id: Mapped[str] = mapped_column(ForeignKey("flow_maps.visual_entity_id", ondelete="CASCADE"), nullable=False)
    channel_key: Mapped[str] = mapped_column(String(180), nullable=False)
    name: Mapped[str] = mapped_column(String(300), nullable=False)
    flow_kind: Mapped[str] = mapped_column(String(80), nullable=False, default="generic", index=True)
    unit: Mapped[str | None] = mapped_column(String(100), nullable=True)
    order_index: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class FlowMapFlowRecord(Base):
    __tablename__ = "flow_map_flows"
    __table_args__ = (
        UniqueConstraint("visual_entity_id", "flow_key", name="uq_flow_map_flow_key"),
        Index("ix_flow_map_flow_visual", "visual_entity_id"),
        Index("ix_flow_map_flow_relation", "relation_id"),
        Index("ix_flow_map_flow_channel", "channel_id"),
        Index("ix_flow_map_flow_status", "flow_status"),
    )
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    visual_entity_id: Mapped[str] = mapped_column(ForeignKey("flow_maps.visual_entity_id", ondelete="CASCADE"), nullable=False)
    flow_key: Mapped[str] = mapped_column(String(180), nullable=False)
    relation_id: Mapped[str] = mapped_column(ForeignKey("visual_reasoning_relations.id", ondelete="CASCADE"), nullable=False)
    channel_id: Mapped[str | None] = mapped_column(ForeignKey("flow_map_channels.id", ondelete="SET NULL"), nullable=True)
    quantity_kind: Mapped[str] = mapped_column(String(50), nullable=False, default="qualitative")
    quantity_value: Mapped[float | None] = mapped_column(Float, nullable=True)
    unit: Mapped[str | None] = mapped_column(String(100), nullable=True)
    lower_bound: Mapped[float | None] = mapped_column(Float, nullable=True)
    upper_bound: Mapped[float | None] = mapped_column(Float, nullable=True)
    period_start: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    period_end: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    flow_status: Mapped[str] = mapped_column(String(50), nullable=False, default="observed", index=True)
    uncertainty_json: Mapped[dict] = mapped_column(JSON, default=dict)
    provenance_json: Mapped[dict] = mapped_column(JSON, default=dict)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)


class FlowMapNodeStateRecord(Base):
    __tablename__ = "flow_map_node_states"
    __table_args__ = (
        Index("ix_flow_map_node_state_visual", "visual_entity_id"),
        Index("ix_flow_map_node_state_element", "element_id"),
        Index("ix_flow_map_node_state_kind", "state_kind"),
    )
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    visual_entity_id: Mapped[str] = mapped_column(ForeignKey("flow_maps.visual_entity_id", ondelete="CASCADE"), nullable=False)
    element_id: Mapped[str] = mapped_column(ForeignKey("visual_reasoning_elements.id", ondelete="CASCADE"), nullable=False)
    state_key: Mapped[str] = mapped_column(String(180), nullable=False, default="state")
    state_kind: Mapped[str] = mapped_column(String(80), nullable=False, default="stock")
    quantity_value: Mapped[float | None] = mapped_column(Float, nullable=True)
    unit: Mapped[str | None] = mapped_column(String(100), nullable=True)
    observed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    uncertainty_json: Mapped[dict] = mapped_column(JSON, default=dict)
    provenance_json: Mapped[dict] = mapped_column(JSON, default=dict)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class FlowMapViewRecord(Base):
    __tablename__ = "flow_map_views"
    __table_args__ = (
        UniqueConstraint("visual_entity_id", "view_key", name="uq_flow_map_view_key"),
        Index("ix_flow_map_view_visual", "visual_entity_id"),
    )
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    visual_entity_id: Mapped[str] = mapped_column(ForeignKey("flow_maps.visual_entity_id", ondelete="CASCADE"), nullable=False)
    view_key: Mapped[str] = mapped_column(String(180), nullable=False)
    name: Mapped[str] = mapped_column(String(300), nullable=False)
    channel_ids_json: Mapped[list] = mapped_column(JSON, default=list)
    filters_json: Mapped[dict] = mapped_column(JSON, default=dict)
    time_window_json: Mapped[dict] = mapped_column(JSON, default=dict)
    layout_intent_json: Mapped[dict] = mapped_column(JSON, default=dict)
    specification_id: Mapped[str | None] = mapped_column(ForeignKey("visualization_specifications.id", ondelete="SET NULL"), nullable=True)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


# v2.33.0 — Scenario Landscapes

class ScenarioLandscapeRecord(Base):
    __tablename__ = "scenario_landscapes"
    visual_entity_id: Mapped[str] = mapped_column(ForeignKey("visual_reasoning_objects.entity_id", ondelete="CASCADE"), primary_key=True)
    project_entity_id: Mapped[str] = mapped_column(ForeignKey("entities.id", ondelete="CASCADE"), nullable=False, index=True)
    baseline_scenario_entity_id: Mapped[str | None] = mapped_column(ForeignKey("entities.id", ondelete="SET NULL"), nullable=True, index=True)
    comparison_mode: Mapped[str] = mapped_column(String(60), nullable=False, default="baseline-relative")
    landscape_state: Mapped[str] = mapped_column(String(50), nullable=False, default="draft", index=True)
    objective: Mapped[str | None] = mapped_column(Text, nullable=True)
    dimension_policy: Mapped[str] = mapped_column(String(60), nullable=False, default="explicit")
    assumptions_json: Mapped[list] = mapped_column(JSON, default=list)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_by: Mapped[str] = mapped_column(String(255), nullable=False, default="operator")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)


class ScenarioLandscapeScenarioRecord(Base):
    __tablename__ = "scenario_landscape_scenarios"
    __table_args__ = (
        UniqueConstraint("visual_entity_id", "scenario_entity_id", name="uq_scenario_landscape_scenario"),
        Index("ix_scenario_landscape_scenario_visual", "visual_entity_id"),
        Index("ix_scenario_landscape_scenario_role", "scenario_role"),
    )
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    visual_entity_id: Mapped[str] = mapped_column(ForeignKey("scenario_landscapes.visual_entity_id", ondelete="CASCADE"), nullable=False)
    scenario_entity_id: Mapped[str] = mapped_column(ForeignKey("entities.id", ondelete="CASCADE"), nullable=False)
    scenario_role: Mapped[str] = mapped_column(String(50), nullable=False, default="alternative")
    display_label: Mapped[str | None] = mapped_column(String(300), nullable=True)
    order_index: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class ScenarioLandscapeDimensionRecord(Base):
    __tablename__ = "scenario_landscape_dimensions"
    __table_args__ = (
        UniqueConstraint("visual_entity_id", "dimension_key", name="uq_scenario_landscape_dimension_key"),
        Index("ix_scenario_landscape_dimension_visual", "visual_entity_id"),
        Index("ix_scenario_landscape_dimension_kind", "dimension_kind"),
        Index("ix_scenario_landscape_dimension_source", "source_entity_id"),
    )
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    visual_entity_id: Mapped[str] = mapped_column(ForeignKey("scenario_landscapes.visual_entity_id", ondelete="CASCADE"), nullable=False)
    dimension_key: Mapped[str] = mapped_column(String(180), nullable=False)
    dimension_kind: Mapped[str] = mapped_column(String(60), nullable=False, default="metric")
    source_entity_id: Mapped[str | None] = mapped_column(ForeignKey("entities.id", ondelete="SET NULL"), nullable=True)
    label: Mapped[str] = mapped_column(String(300), nullable=False)
    unit: Mapped[str | None] = mapped_column(String(120), nullable=True)
    preference_direction: Mapped[str] = mapped_column(String(40), nullable=False, default="neutral")
    order_index: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class ScenarioLandscapeValueRecord(Base):
    __tablename__ = "scenario_landscape_values"
    __table_args__ = (
        UniqueConstraint("visual_entity_id", "scenario_entity_id", "dimension_id", name="uq_scenario_landscape_value"),
        Index("ix_scenario_landscape_value_visual", "visual_entity_id"),
        Index("ix_scenario_landscape_value_scenario", "scenario_entity_id"),
        Index("ix_scenario_landscape_value_dimension", "dimension_id"),
    )
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    visual_entity_id: Mapped[str] = mapped_column(ForeignKey("scenario_landscapes.visual_entity_id", ondelete="CASCADE"), nullable=False)
    scenario_entity_id: Mapped[str] = mapped_column(ForeignKey("entities.id", ondelete="CASCADE"), nullable=False)
    dimension_id: Mapped[str] = mapped_column(ForeignKey("scenario_landscape_dimensions.id", ondelete="CASCADE"), nullable=False)
    numeric_value: Mapped[float | None] = mapped_column(Float, nullable=True)
    value_json: Mapped[object] = mapped_column(JSON, nullable=True)
    unit: Mapped[str | None] = mapped_column(String(120), nullable=True)
    lower_bound: Mapped[float | None] = mapped_column(Float, nullable=True)
    upper_bound: Mapped[float | None] = mapped_column(Float, nullable=True)
    uncertainty_json: Mapped[dict] = mapped_column(JSON, default=dict)
    provenance_json: Mapped[dict] = mapped_column(JSON, default=dict)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)


class ScenarioLandscapeViewRecord(Base):
    __tablename__ = "scenario_landscape_views"
    __table_args__ = (
        UniqueConstraint("visual_entity_id", "view_key", name="uq_scenario_landscape_view_key"),
        Index("ix_scenario_landscape_view_visual", "visual_entity_id"),
    )
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    visual_entity_id: Mapped[str] = mapped_column(ForeignKey("scenario_landscapes.visual_entity_id", ondelete="CASCADE"), nullable=False)
    view_key: Mapped[str] = mapped_column(String(180), nullable=False)
    name: Mapped[str] = mapped_column(String(300), nullable=False)
    scenario_ids_json: Mapped[list] = mapped_column(JSON, default=list)
    dimension_ids_json: Mapped[list] = mapped_column(JSON, default=list)
    filters_json: Mapped[dict] = mapped_column(JSON, default=dict)
    layout_intent_json: Mapped[dict] = mapped_column(JSON, default=dict)
    specification_id: Mapped[str | None] = mapped_column(ForeignKey("visualization_specifications.id", ondelete="SET NULL"), nullable=True)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


# v2.34.0 — Interactive Model Canvas

class ModelCanvasRecord(Base):
    __tablename__ = "model_canvases"
    visual_entity_id: Mapped[str] = mapped_column(ForeignKey("visual_reasoning_objects.entity_id", ondelete="CASCADE"), primary_key=True)
    project_entity_id: Mapped[str] = mapped_column(ForeignKey("entities.id", ondelete="CASCADE"), nullable=False, index=True)
    model_entity_id: Mapped[str] = mapped_column(ForeignKey("entities.id", ondelete="CASCADE"), nullable=False, index=True)
    model_version_entity_id: Mapped[str | None] = mapped_column(ForeignKey("entities.id", ondelete="SET NULL"), nullable=True, index=True)
    canvas_state: Mapped[str] = mapped_column(String(50), nullable=False, default="draft", index=True)
    interaction_mode: Mapped[str] = mapped_column(String(60), nullable=False, default="inspect-configure")
    execution_target: Mapped[str] = mapped_column(String(80), nullable=False, default="external")
    assumptions_json: Mapped[list] = mapped_column(JSON, default=list)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_by: Mapped[str] = mapped_column(String(255), nullable=False, default="operator")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)


class ModelCanvasNodeRecord(Base):
    __tablename__ = "model_canvas_nodes"
    __table_args__ = (
        UniqueConstraint("visual_entity_id", "node_key", name="uq_model_canvas_node_key"),
        Index("ix_model_canvas_node_visual", "visual_entity_id"),
        Index("ix_model_canvas_node_kind", "node_kind"),
        Index("ix_model_canvas_node_bound", "bound_entity_id"),
    )
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    visual_entity_id: Mapped[str] = mapped_column(ForeignKey("model_canvases.visual_entity_id", ondelete="CASCADE"), nullable=False)
    node_key: Mapped[str] = mapped_column(String(180), nullable=False)
    node_kind: Mapped[str] = mapped_column(String(60), nullable=False, default="component")
    semantic_role: Mapped[str] = mapped_column(String(60), nullable=False, default="context")
    bound_entity_id: Mapped[str | None] = mapped_column(ForeignKey("entities.id", ondelete="SET NULL"), nullable=True)
    label: Mapped[str] = mapped_column(String(300), nullable=False)
    unit: Mapped[str | None] = mapped_column(String(120), nullable=True)
    position_hint_json: Mapped[dict] = mapped_column(JSON, default=dict)
    interaction_json: Mapped[dict] = mapped_column(JSON, default=dict)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class ModelCanvasEdgeRecord(Base):
    __tablename__ = "model_canvas_edges"
    __table_args__ = (
        Index("ix_model_canvas_edge_visual", "visual_entity_id"),
        Index("ix_model_canvas_edge_source", "source_node_id"),
        Index("ix_model_canvas_edge_target", "target_node_id"),
    )
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    visual_entity_id: Mapped[str] = mapped_column(ForeignKey("model_canvases.visual_entity_id", ondelete="CASCADE"), nullable=False)
    source_node_id: Mapped[str] = mapped_column(ForeignKey("model_canvas_nodes.id", ondelete="CASCADE"), nullable=False)
    target_node_id: Mapped[str] = mapped_column(ForeignKey("model_canvas_nodes.id", ondelete="CASCADE"), nullable=False)
    edge_kind: Mapped[str] = mapped_column(String(60), nullable=False, default="dependency")
    directed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    label: Mapped[str | None] = mapped_column(String(300), nullable=True)
    bound_relation_id: Mapped[str | None] = mapped_column(ForeignKey("visual_reasoning_relations.id", ondelete="SET NULL"), nullable=True)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class ModelCanvasControlRecord(Base):
    __tablename__ = "model_canvas_controls"
    __table_args__ = (
        UniqueConstraint("visual_entity_id", "control_key", name="uq_model_canvas_control_key"),
        Index("ix_model_canvas_control_visual", "visual_entity_id"),
        Index("ix_model_canvas_control_bound", "bound_entity_id"),
    )
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    visual_entity_id: Mapped[str] = mapped_column(ForeignKey("model_canvases.visual_entity_id", ondelete="CASCADE"), nullable=False)
    control_key: Mapped[str] = mapped_column(String(180), nullable=False)
    control_kind: Mapped[str] = mapped_column(String(60), nullable=False, default="input")
    node_id: Mapped[str | None] = mapped_column(ForeignKey("model_canvas_nodes.id", ondelete="SET NULL"), nullable=True)
    bound_entity_id: Mapped[str | None] = mapped_column(ForeignKey("entities.id", ondelete="SET NULL"), nullable=True)
    label: Mapped[str] = mapped_column(String(300), nullable=False)
    data_type: Mapped[str] = mapped_column(String(50), nullable=False, default="number")
    unit: Mapped[str | None] = mapped_column(String(120), nullable=True)
    default_value_json: Mapped[object] = mapped_column(JSON, nullable=True)
    bounds_json: Mapped[dict] = mapped_column(JSON, default=dict)
    allowed_values_json: Mapped[list] = mapped_column(JSON, default=list)
    handoff_json: Mapped[dict] = mapped_column(JSON, default=dict)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class ModelCanvasStateRecord(Base):
    __tablename__ = "model_canvas_states"
    __table_args__ = (
        UniqueConstraint("visual_entity_id", "state_key", name="uq_model_canvas_state_key"),
        Index("ix_model_canvas_state_visual", "visual_entity_id"),
        Index("ix_model_canvas_state_scenario", "scenario_entity_id"),
    )
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    visual_entity_id: Mapped[str] = mapped_column(ForeignKey("model_canvases.visual_entity_id", ondelete="CASCADE"), nullable=False)
    state_key: Mapped[str] = mapped_column(String(180), nullable=False)
    name: Mapped[str] = mapped_column(String(300), nullable=False)
    scenario_entity_id: Mapped[str | None] = mapped_column(ForeignKey("entities.id", ondelete="SET NULL"), nullable=True)
    model_run_entity_id: Mapped[str | None] = mapped_column(ForeignKey("entities.id", ondelete="SET NULL"), nullable=True)
    values_json: Mapped[dict] = mapped_column(JSON, default=dict)
    provenance_json: Mapped[dict] = mapped_column(JSON, default=dict)
    state_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    immutable: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_by: Mapped[str] = mapped_column(String(255), nullable=False, default="operator")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class ModelCanvasViewRecord(Base):
    __tablename__ = "model_canvas_views"
    __table_args__ = (
        UniqueConstraint("visual_entity_id", "view_key", name="uq_model_canvas_view_key"),
        Index("ix_model_canvas_view_visual", "visual_entity_id"),
    )
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    visual_entity_id: Mapped[str] = mapped_column(ForeignKey("model_canvases.visual_entity_id", ondelete="CASCADE"), nullable=False)
    view_key: Mapped[str] = mapped_column(String(180), nullable=False)
    name: Mapped[str] = mapped_column(String(300), nullable=False)
    node_ids_json: Mapped[list] = mapped_column(JSON, default=list)
    edge_ids_json: Mapped[list] = mapped_column(JSON, default=list)
    control_ids_json: Mapped[list] = mapped_column(JSON, default=list)
    filters_json: Mapped[dict] = mapped_column(JSON, default=dict)
    layout_intent_json: Mapped[dict] = mapped_column(JSON, default=dict)
    specification_id: Mapped[str | None] = mapped_column(ForeignKey("visualization_specifications.id", ondelete="SET NULL"), nullable=True)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

# v2.35.0 — Scenario Compute Engine

class ScenarioComputePlanRecord(Base):
    __tablename__ = "scenario_compute_plans"
    __table_args__ = (
        UniqueConstraint("project_entity_id", "plan_key", name="uq_scenario_compute_plan_project_key"),
        Index("ix_scenario_compute_plan_project", "project_entity_id"),
        Index("ix_scenario_compute_plan_model", "model_entity_id"),
        Index("ix_scenario_compute_plan_state", "plan_state"),
    )
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    plan_key: Mapped[str] = mapped_column(String(180), nullable=False)
    name: Mapped[str] = mapped_column(String(300), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    visibility: Mapped[str] = mapped_column(String(30), nullable=False, default="private", index=True)
    project_entity_id: Mapped[str] = mapped_column(ForeignKey("entities.id", ondelete="CASCADE"), nullable=False)
    model_entity_id: Mapped[str] = mapped_column(ForeignKey("entities.id", ondelete="CASCADE"), nullable=False)
    model_version_entity_id: Mapped[str] = mapped_column(ForeignKey("entities.id", ondelete="RESTRICT"), nullable=False)
    scenario_landscape_visual_entity_id: Mapped[str | None] = mapped_column(ForeignKey("scenario_landscapes.visual_entity_id", ondelete="SET NULL"), nullable=True)
    model_canvas_visual_entity_id: Mapped[str | None] = mapped_column(ForeignKey("model_canvases.visual_entity_id", ondelete="SET NULL"), nullable=True)
    plan_state: Mapped[str] = mapped_column(String(50), nullable=False, default="draft", index=True)
    execution_product: Mapped[str] = mapped_column(String(80), nullable=False, default="lab")
    execution_contract_json: Mapped[dict] = mapped_column(JSON, default=dict)
    output_contract_json: Mapped[dict] = mapped_column(JSON, default=dict)
    concurrency_policy_json: Mapped[dict] = mapped_column(JSON, default=dict)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_by: Mapped[str] = mapped_column(String(255), nullable=False, default="operator")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)


class ScenarioComputeCaseRecord(Base):
    __tablename__ = "scenario_compute_cases"
    __table_args__ = (
        UniqueConstraint("plan_id", "case_key", name="uq_scenario_compute_case_plan_key"),
        Index("ix_scenario_compute_case_plan", "plan_id"),
        Index("ix_scenario_compute_case_scenario", "scenario_entity_id"),
    )
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    plan_id: Mapped[str] = mapped_column(ForeignKey("scenario_compute_plans.id", ondelete="CASCADE"), nullable=False)
    case_key: Mapped[str] = mapped_column(String(180), nullable=False)
    label: Mapped[str] = mapped_column(String(300), nullable=False)
    scenario_entity_id: Mapped[str] = mapped_column(ForeignKey("entities.id", ondelete="RESTRICT"), nullable=False)
    comparison_role: Mapped[str] = mapped_column(String(50), nullable=False, default="alternative")
    parameter_overrides_json: Mapped[dict] = mapped_column(JSON, default=dict)
    expected_outputs_json: Mapped[list] = mapped_column(JSON, default=list)
    case_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, index=True)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class ScenarioComputeRequestRecord(Base):
    __tablename__ = "scenario_compute_requests"
    __table_args__ = (
        UniqueConstraint("plan_id", "idempotency_key", name="uq_scenario_compute_request_idempotency"),
        Index("ix_scenario_compute_request_plan", "plan_id"),
        Index("ix_scenario_compute_request_case", "case_id"),
        Index("ix_scenario_compute_request_state", "request_state"),
    )
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    plan_id: Mapped[str] = mapped_column(ForeignKey("scenario_compute_plans.id", ondelete="CASCADE"), nullable=False)
    case_id: Mapped[str] = mapped_column(ForeignKey("scenario_compute_cases.id", ondelete="CASCADE"), nullable=False)
    idempotency_key: Mapped[str] = mapped_column(String(255), nullable=False)
    request_state: Mapped[str] = mapped_column(String(50), nullable=False, default="requested", index=True)
    requested_product: Mapped[str] = mapped_column(String(80), nullable=False, default="lab")
    input_manifest_json: Mapped[dict] = mapped_column(JSON, default=dict)
    request_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    external_request_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    model_run_entity_id: Mapped[str | None] = mapped_column(ForeignKey("entities.id", ondelete="SET NULL"), nullable=True)
    submitted_by: Mapped[str] = mapped_column(String(255), nullable=False, default="operator")
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)


class ScenarioComputeAttemptRecord(Base):
    __tablename__ = "scenario_compute_attempts"
    __table_args__ = (
        UniqueConstraint("request_id", "attempt_number", name="uq_scenario_compute_attempt_number"),
        Index("ix_scenario_compute_attempt_request", "request_id"),
        Index("ix_scenario_compute_attempt_state", "attempt_state"),
    )
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    request_id: Mapped[str] = mapped_column(ForeignKey("scenario_compute_requests.id", ondelete="CASCADE"), nullable=False)
    attempt_number: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    attempt_state: Mapped[str] = mapped_column(String(50), nullable=False, default="accepted", index=True)
    executor_product: Mapped[str] = mapped_column(String(80), nullable=False, default="lab")
    external_execution_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    runtime_metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)
    error_json: Mapped[dict] = mapped_column(JSON, default=dict)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)


class ScenarioComputeResultBindingRecord(Base):
    __tablename__ = "scenario_compute_result_bindings"
    __table_args__ = (
        UniqueConstraint("request_id", "output_key", name="uq_scenario_compute_result_output"),
        Index("ix_scenario_compute_result_request", "request_id"),
        Index("ix_scenario_compute_result_entity", "result_entity_id"),
    )
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    request_id: Mapped[str] = mapped_column(ForeignKey("scenario_compute_requests.id", ondelete="CASCADE"), nullable=False)
    result_entity_id: Mapped[str] = mapped_column(ForeignKey("entities.id", ondelete="RESTRICT"), nullable=False)
    output_key: Mapped[str] = mapped_column(String(180), nullable=False)
    binding_role: Mapped[str] = mapped_column(String(50), nullable=False, default="primary")
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


# v2.36.0 — Uncertainty, Sensitivity & Ensemble Reasoning

class UncertaintyDefinitionRecord(Base):
    __tablename__ = "uncertainty_definitions"
    __table_args__ = (
        UniqueConstraint("project_entity_id", "uncertainty_key", name="uq_uncertainty_definition_project_key"),
        Index("ix_uncertainty_definition_project", "project_entity_id"),
        Index("ix_uncertainty_definition_subject", "subject_entity_id"),
        Index("ix_uncertainty_definition_kind", "uncertainty_kind"),
    )
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    uncertainty_key: Mapped[str] = mapped_column(String(180), nullable=False)
    name: Mapped[str] = mapped_column(String(300), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    visibility: Mapped[str] = mapped_column(String(30), nullable=False, default="private", index=True)
    project_entity_id: Mapped[str] = mapped_column(ForeignKey("entities.id", ondelete="CASCADE"), nullable=False)
    subject_entity_id: Mapped[str] = mapped_column(ForeignKey("entities.id", ondelete="CASCADE"), nullable=False)
    uncertainty_kind: Mapped[str] = mapped_column(String(50), nullable=False, default="epistemic", index=True)
    distribution_family: Mapped[str] = mapped_column(String(80), nullable=False, default="interval")
    parameters_json: Mapped[dict] = mapped_column(JSON, default=dict)
    lower_bound: Mapped[float | None] = mapped_column(Float, nullable=True)
    upper_bound: Mapped[float | None] = mapped_column(Float, nullable=True)
    unit: Mapped[str | None] = mapped_column(String(120), nullable=True)
    confidence_level: Mapped[float | None] = mapped_column(Float, nullable=True)
    source_json: Mapped[dict] = mapped_column(JSON, default=dict)
    provenance_json: Mapped[dict] = mapped_column(JSON, default=dict)
    assumptions_json: Mapped[list] = mapped_column(JSON, default=list)
    state: Mapped[str] = mapped_column(String(50), nullable=False, default="declared", index=True)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_by: Mapped[str] = mapped_column(String(255), nullable=False, default="operator")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)


class SensitivityStudyRecord(Base):
    __tablename__ = "sensitivity_studies"
    __table_args__ = (
        UniqueConstraint("project_entity_id", "study_key", name="uq_sensitivity_study_project_key"),
        Index("ix_sensitivity_study_project", "project_entity_id"),
        Index("ix_sensitivity_study_model", "model_entity_id"),
        Index("ix_sensitivity_study_state", "study_state"),
    )
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    study_key: Mapped[str] = mapped_column(String(180), nullable=False)
    name: Mapped[str] = mapped_column(String(300), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    visibility: Mapped[str] = mapped_column(String(30), nullable=False, default="private", index=True)
    project_entity_id: Mapped[str] = mapped_column(ForeignKey("entities.id", ondelete="CASCADE"), nullable=False)
    model_entity_id: Mapped[str] = mapped_column(ForeignKey("entities.id", ondelete="CASCADE"), nullable=False)
    model_version_entity_id: Mapped[str] = mapped_column(ForeignKey("entities.id", ondelete="RESTRICT"), nullable=False)
    compute_plan_id: Mapped[str | None] = mapped_column(ForeignKey("scenario_compute_plans.id", ondelete="SET NULL"), nullable=True)
    method: Mapped[str] = mapped_column(String(80), nullable=False, default="local", index=True)
    output_metric: Mapped[str | None] = mapped_column(String(180), nullable=True)
    study_state: Mapped[str] = mapped_column(String(50), nullable=False, default="draft", index=True)
    execution_product: Mapped[str] = mapped_column(String(80), nullable=False, default="lab")
    configuration_json: Mapped[dict] = mapped_column(JSON, default=dict)
    assumptions_json: Mapped[list] = mapped_column(JSON, default=list)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_by: Mapped[str] = mapped_column(String(255), nullable=False, default="operator")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)


class SensitivityFactorRecord(Base):
    __tablename__ = "sensitivity_factors"
    __table_args__ = (
        UniqueConstraint("study_id", "factor_key", name="uq_sensitivity_factor_study_key"),
        UniqueConstraint("study_id", "parameter_entity_id", name="uq_sensitivity_factor_study_parameter"),
        Index("ix_sensitivity_factor_study", "study_id"),
        Index("ix_sensitivity_factor_parameter", "parameter_entity_id"),
    )
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    study_id: Mapped[str] = mapped_column(ForeignKey("sensitivity_studies.id", ondelete="CASCADE"), nullable=False)
    factor_key: Mapped[str] = mapped_column(String(180), nullable=False)
    parameter_entity_id: Mapped[str] = mapped_column(ForeignKey("entities.id", ondelete="RESTRICT"), nullable=False)
    lower_bound: Mapped[float | None] = mapped_column(Float, nullable=True)
    upper_bound: Mapped[float | None] = mapped_column(Float, nullable=True)
    unit: Mapped[str | None] = mapped_column(String(120), nullable=True)
    uncertainty_definition_id: Mapped[str | None] = mapped_column(ForeignKey("uncertainty_definitions.id", ondelete="SET NULL"), nullable=True)
    order_index: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class SensitivityMeasureRecord(Base):
    __tablename__ = "sensitivity_measures"
    __table_args__ = (
        UniqueConstraint("study_id", "factor_id", "output_key", "measure_kind", name="uq_sensitivity_measure_identity"),
        Index("ix_sensitivity_measure_study", "study_id"),
        Index("ix_sensitivity_measure_factor", "factor_id"),
        Index("ix_sensitivity_measure_output", "output_key"),
    )
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    study_id: Mapped[str] = mapped_column(ForeignKey("sensitivity_studies.id", ondelete="CASCADE"), nullable=False)
    factor_id: Mapped[str] = mapped_column(ForeignKey("sensitivity_factors.id", ondelete="CASCADE"), nullable=False)
    output_key: Mapped[str] = mapped_column(String(180), nullable=False, default="output")
    result_entity_id: Mapped[str | None] = mapped_column(ForeignKey("entities.id", ondelete="SET NULL"), nullable=True)
    measure_kind: Mapped[str] = mapped_column(String(80), nullable=False, default="effect")
    measure_value: Mapped[float] = mapped_column(Float, nullable=False)
    lower_bound: Mapped[float | None] = mapped_column(Float, nullable=True)
    upper_bound: Mapped[float | None] = mapped_column(Float, nullable=True)
    confidence_level: Mapped[float | None] = mapped_column(Float, nullable=True)
    unit: Mapped[str | None] = mapped_column(String(120), nullable=True)
    provenance_json: Mapped[dict] = mapped_column(JSON, default=dict)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class EnsembleRecord(Base):
    __tablename__ = "ensembles"
    __table_args__ = (
        UniqueConstraint("project_entity_id", "ensemble_key", name="uq_ensemble_project_key"),
        Index("ix_ensemble_project", "project_entity_id"),
        Index("ix_ensemble_model_version", "model_version_entity_id"),
        Index("ix_ensemble_state", "ensemble_state"),
    )
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    ensemble_key: Mapped[str] = mapped_column(String(180), nullable=False)
    name: Mapped[str] = mapped_column(String(300), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    visibility: Mapped[str] = mapped_column(String(30), nullable=False, default="private", index=True)
    project_entity_id: Mapped[str] = mapped_column(ForeignKey("entities.id", ondelete="CASCADE"), nullable=False)
    model_entity_id: Mapped[str] = mapped_column(ForeignKey("entities.id", ondelete="CASCADE"), nullable=False)
    model_version_entity_id: Mapped[str] = mapped_column(ForeignKey("entities.id", ondelete="RESTRICT"), nullable=False)
    compute_plan_id: Mapped[str | None] = mapped_column(ForeignKey("scenario_compute_plans.id", ondelete="SET NULL"), nullable=True)
    ensemble_state: Mapped[str] = mapped_column(String(50), nullable=False, default="draft", index=True)
    combination_policy_json: Mapped[dict] = mapped_column(JSON, default=dict)
    assumptions_json: Mapped[list] = mapped_column(JSON, default=list)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_by: Mapped[str] = mapped_column(String(255), nullable=False, default="operator")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)


class EnsembleMemberRecord(Base):
    __tablename__ = "ensemble_members"
    __table_args__ = (
        UniqueConstraint("ensemble_id", "member_key", name="uq_ensemble_member_key"),
        Index("ix_ensemble_member_ensemble", "ensemble_id"),
        Index("ix_ensemble_member_scenario", "scenario_entity_id"),
        Index("ix_ensemble_member_run", "model_run_entity_id"),
    )
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    ensemble_id: Mapped[str] = mapped_column(ForeignKey("ensembles.id", ondelete="CASCADE"), nullable=False)
    member_key: Mapped[str] = mapped_column(String(180), nullable=False)
    scenario_entity_id: Mapped[str | None] = mapped_column(ForeignKey("entities.id", ondelete="SET NULL"), nullable=True)
    compute_request_id: Mapped[str | None] = mapped_column(ForeignKey("scenario_compute_requests.id", ondelete="SET NULL"), nullable=True)
    model_run_entity_id: Mapped[str | None] = mapped_column(ForeignKey("entities.id", ondelete="SET NULL"), nullable=True)
    member_state: Mapped[str] = mapped_column(String(50), nullable=False, default="declared", index=True)
    weight: Mapped[float | None] = mapped_column(Float, nullable=True)
    provenance_json: Mapped[dict] = mapped_column(JSON, default=dict)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class EnsembleStatisticRecord(Base):
    __tablename__ = "ensemble_statistics"
    __table_args__ = (
        UniqueConstraint("ensemble_id", "output_key", "statistic_kind", "quantile", name="uq_ensemble_statistic_identity"),
        Index("ix_ensemble_statistic_ensemble", "ensemble_id"),
        Index("ix_ensemble_statistic_output", "output_key"),
    )
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    ensemble_id: Mapped[str] = mapped_column(ForeignKey("ensembles.id", ondelete="CASCADE"), nullable=False)
    output_key: Mapped[str] = mapped_column(String(180), nullable=False)
    statistic_kind: Mapped[str] = mapped_column(String(80), nullable=False)
    statistic_value: Mapped[float] = mapped_column(Float, nullable=False)
    unit: Mapped[str | None] = mapped_column(String(120), nullable=True)
    quantile: Mapped[float | None] = mapped_column(Float, nullable=True)
    lower_bound: Mapped[float | None] = mapped_column(Float, nullable=True)
    upper_bound: Mapped[float | None] = mapped_column(Float, nullable=True)
    confidence_level: Mapped[float | None] = mapped_column(Float, nullable=True)
    provenance_json: Mapped[dict] = mapped_column(JSON, default=dict)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


# v2.36.1.1 — Uncertainty Compute Runtime Integration production-schema compatibility repair

class UncertaintyComputeRunRecord(Base):
    __tablename__ = "uncertainty_compute_runs"
    __table_args__ = (
        UniqueConstraint("run_key", name="uq_uncertainty_compute_run_key"),
        Index("ix_uncertainty_compute_method", "method"),
        Index("ix_uncertainty_compute_state", "run_state"),
        Index("ix_uncertainty_compute_project", "project_entity_id"),
        Index("ix_uncertainty_compute_sensitivity", "sensitivity_study_id"),
        Index("ix_uncertainty_compute_ensemble", "ensemble_id"),
    )
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    run_key: Mapped[str] = mapped_column(String(180), nullable=False)
    name: Mapped[str] = mapped_column(String(300), nullable=False)
    method: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    run_state: Mapped[str] = mapped_column(String(50), nullable=False, default="completed", index=True)
    project_entity_id: Mapped[str | None] = mapped_column(ForeignKey("entities.id", ondelete="SET NULL"), nullable=True)
    model_entity_id: Mapped[str | None] = mapped_column(ForeignKey("entities.id", ondelete="SET NULL"), nullable=True)
    model_version_entity_id: Mapped[str | None] = mapped_column(ForeignKey("entities.id", ondelete="SET NULL"), nullable=True)
    sensitivity_study_id: Mapped[str | None] = mapped_column(ForeignKey("sensitivity_studies.id", ondelete="SET NULL"), nullable=True)
    ensemble_id: Mapped[str | None] = mapped_column(ForeignKey("ensembles.id", ondelete="SET NULL"), nullable=True)
    runtime_product: Mapped[str] = mapped_column(String(80), nullable=False, default="core-statistics")
    seed: Mapped[int | None] = mapped_column(Integer, nullable=True)
    sample_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    input_manifest_json: Mapped[dict] = mapped_column(JSON, default=dict)
    output_summary_json: Mapped[dict] = mapped_column(JSON, default=dict)
    provenance_json: Mapped[dict] = mapped_column(JSON, default=dict)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_by: Mapped[str] = mapped_column(String(255), nullable=False, default="operator")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)


# v2.37.0 — Causal Systems Explorer

class CausalGraphRecord(Base):
    __tablename__ = "causal_graphs"
    __table_args__ = (
        UniqueConstraint("project_entity_id", "graph_key", name="uq_causal_graph_project_key"),
        Index("ix_causal_graph_project", "project_entity_id"),
        Index("ix_causal_graph_model", "model_entity_id"),
        Index("ix_causal_graph_state", "graph_state"),
    )
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    graph_key: Mapped[str] = mapped_column(String(180), nullable=False)
    name: Mapped[str] = mapped_column(String(300), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    visibility: Mapped[str] = mapped_column(String(30), nullable=False, default="private", index=True)
    project_entity_id: Mapped[str] = mapped_column(ForeignKey("entities.id", ondelete="CASCADE"), nullable=False)
    model_entity_id: Mapped[str | None] = mapped_column(ForeignKey("entities.id", ondelete="SET NULL"), nullable=True)
    model_version_entity_id: Mapped[str | None] = mapped_column(ForeignKey("entities.id", ondelete="SET NULL"), nullable=True)
    visual_entity_id: Mapped[str | None] = mapped_column(ForeignKey("visual_reasoning_objects.entity_id", ondelete="SET NULL"), nullable=True)
    graph_state: Mapped[str] = mapped_column(String(50), nullable=False, default="draft", index=True)
    causal_semantics: Mapped[str] = mapped_column(String(50), nullable=False, default="directed-acyclic")
    assumptions_json: Mapped[list] = mapped_column(JSON, default=list)
    provenance_json: Mapped[dict] = mapped_column(JSON, default=dict)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_by: Mapped[str] = mapped_column(String(255), nullable=False, default="operator")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

class CausalVariableRecord(Base):
    __tablename__ = "causal_variables"
    __table_args__ = (
        UniqueConstraint("graph_id", "variable_key", name="uq_causal_variable_graph_key"),
        Index("ix_causal_variable_graph", "graph_id"),
        Index("ix_causal_variable_role", "causal_role"),
        Index("ix_causal_variable_entity", "bound_entity_id"),
    )
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    graph_id: Mapped[str] = mapped_column(ForeignKey("causal_graphs.id", ondelete="CASCADE"), nullable=False)
    variable_key: Mapped[str] = mapped_column(String(180), nullable=False)
    label: Mapped[str] = mapped_column(String(300), nullable=False)
    causal_role: Mapped[str] = mapped_column(String(80), nullable=False, default="variable", index=True)
    bound_entity_id: Mapped[str | None] = mapped_column(ForeignKey("entities.id", ondelete="SET NULL"), nullable=True)
    observed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    unit: Mapped[str | None] = mapped_column(String(120), nullable=True)
    temporal_index_json: Mapped[dict] = mapped_column(JSON, default=dict)
    uncertainty_json: Mapped[dict] = mapped_column(JSON, default=dict)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

class CausalEdgeRecord(Base):
    __tablename__ = "causal_edges"
    __table_args__ = (
        UniqueConstraint("graph_id", "source_variable_id", "target_variable_id", "edge_kind", name="uq_causal_edge_identity"),
        Index("ix_causal_edge_graph", "graph_id"),
        Index("ix_causal_edge_source", "source_variable_id"),
        Index("ix_causal_edge_target", "target_variable_id"),
    )
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    graph_id: Mapped[str] = mapped_column(ForeignKey("causal_graphs.id", ondelete="CASCADE"), nullable=False)
    source_variable_id: Mapped[str] = mapped_column(ForeignKey("causal_variables.id", ondelete="CASCADE"), nullable=False)
    target_variable_id: Mapped[str] = mapped_column(ForeignKey("causal_variables.id", ondelete="CASCADE"), nullable=False)
    edge_kind: Mapped[str] = mapped_column(String(80), nullable=False, default="causal")
    sign: Mapped[str] = mapped_column(String(30), nullable=False, default="unknown")
    lag_json: Mapped[dict] = mapped_column(JSON, default=dict)
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    assumptions_json: Mapped[list] = mapped_column(JSON, default=list)
    provenance_json: Mapped[dict] = mapped_column(JSON, default=dict)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

class CausalInterventionRecord(Base):
    __tablename__ = "causal_interventions"
    __table_args__ = (Index("ix_causal_intervention_graph", "graph_id"), Index("ix_causal_intervention_variable", "variable_id"),)
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    graph_id: Mapped[str] = mapped_column(ForeignKey("causal_graphs.id", ondelete="CASCADE"), nullable=False)
    variable_id: Mapped[str] = mapped_column(ForeignKey("causal_variables.id", ondelete="CASCADE"), nullable=False)
    intervention_kind: Mapped[str] = mapped_column(String(80), nullable=False, default="set")
    value_json: Mapped[object] = mapped_column(JSON, nullable=True)
    comparison_value_json: Mapped[object] = mapped_column(JSON, nullable=True)
    unit: Mapped[str | None] = mapped_column(String(120), nullable=True)
    assumptions_json: Mapped[list] = mapped_column(JSON, default=list)
    provenance_json: Mapped[dict] = mapped_column(JSON, default=dict)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_by: Mapped[str] = mapped_column(String(255), nullable=False, default="operator")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

class CausalIdentificationRecord(Base):
    __tablename__ = "causal_identifications"
    __table_args__ = (Index("ix_causal_identification_graph", "graph_id"), Index("ix_causal_identification_status", "identification_status"),)
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    graph_id: Mapped[str] = mapped_column(ForeignKey("causal_graphs.id", ondelete="CASCADE"), nullable=False)
    treatment_variable_id: Mapped[str] = mapped_column(ForeignKey("causal_variables.id", ondelete="CASCADE"), nullable=False)
    outcome_variable_id: Mapped[str] = mapped_column(ForeignKey("causal_variables.id", ondelete="CASCADE"), nullable=False)
    estimand: Mapped[str] = mapped_column(String(80), nullable=False, default="ATE")
    identification_method: Mapped[str] = mapped_column(String(100), nullable=False, default="unassessed")
    identification_status: Mapped[str] = mapped_column(String(50), nullable=False, default="unassessed", index=True)
    adjustment_set_json: Mapped[list] = mapped_column(JSON, default=list)
    assumptions_json: Mapped[list] = mapped_column(JSON, default=list)
    rationale_json: Mapped[dict] = mapped_column(JSON, default=dict)
    provenance_json: Mapped[dict] = mapped_column(JSON, default=dict)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_by: Mapped[str] = mapped_column(String(255), nullable=False, default="operator")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

class CausalEstimateRecord(Base):
    __tablename__ = "causal_estimates"
    __table_args__ = (Index("ix_causal_estimate_graph", "graph_id"), Index("ix_causal_estimate_identification", "identification_id"),)
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    graph_id: Mapped[str] = mapped_column(ForeignKey("causal_graphs.id", ondelete="CASCADE"), nullable=False)
    identification_id: Mapped[str | None] = mapped_column(ForeignKey("causal_identifications.id", ondelete="SET NULL"), nullable=True)
    estimate_kind: Mapped[str] = mapped_column(String(100), nullable=False, default="effect")
    estimate_value: Mapped[float] = mapped_column(Float, nullable=False)
    lower_bound: Mapped[float | None] = mapped_column(Float, nullable=True)
    upper_bound: Mapped[float | None] = mapped_column(Float, nullable=True)
    confidence_level: Mapped[float | None] = mapped_column(Float, nullable=True)
    unit: Mapped[str | None] = mapped_column(String(120), nullable=True)
    method: Mapped[str] = mapped_column(String(120), nullable=False, default="external")
    source_execution_json: Mapped[dict] = mapped_column(JSON, default=dict)
    provenance_json: Mapped[dict] = mapped_column(JSON, default=dict)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

class CausalDiagnosticRecord(Base):
    __tablename__ = "causal_diagnostics"
    __table_args__ = (Index("ix_causal_diagnostic_graph", "graph_id"), Index("ix_causal_diagnostic_kind", "diagnostic_kind"),)
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    graph_id: Mapped[str] = mapped_column(ForeignKey("causal_graphs.id", ondelete="CASCADE"), nullable=False)
    identification_id: Mapped[str | None] = mapped_column(ForeignKey("causal_identifications.id", ondelete="SET NULL"), nullable=True)
    diagnostic_kind: Mapped[str] = mapped_column(String(100), nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="reported")
    value_json: Mapped[object] = mapped_column(JSON, nullable=True)
    threshold_json: Mapped[object] = mapped_column(JSON, nullable=True)
    interpretation: Mapped[str | None] = mapped_column(Text, nullable=True)
    provenance_json: Mapped[dict] = mapped_column(JSON, default=dict)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


# v2.38.0 — Spatial & Temporal Visual Reasoning

class SpatialTemporalSceneRecord(Base):
    __tablename__ = "spatial_temporal_scenes"
    __table_args__ = (
        UniqueConstraint("project_entity_id", "scene_key", name="uq_spatiotemporal_scene_project_key"),
        Index("ix_spatiotemporal_scene_project", "project_entity_id"),
        Index("ix_spatiotemporal_scene_model", "model_entity_id"),
        Index("ix_spatiotemporal_scene_state", "scene_state"),
        Index("ix_spatiotemporal_scene_visibility", "visibility"),
    )
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    scene_key: Mapped[str] = mapped_column(String(180), nullable=False)
    name: Mapped[str] = mapped_column(String(300), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    visibility: Mapped[str] = mapped_column(String(30), nullable=False, default="private", index=True)
    project_entity_id: Mapped[str] = mapped_column(ForeignKey("entities.id", ondelete="CASCADE"), nullable=False)
    model_entity_id: Mapped[str | None] = mapped_column(ForeignKey("entities.id", ondelete="SET NULL"), nullable=True)
    model_version_entity_id: Mapped[str | None] = mapped_column(ForeignKey("entities.id", ondelete="SET NULL"), nullable=True)
    causal_graph_id: Mapped[str | None] = mapped_column(ForeignKey("causal_graphs.id", ondelete="SET NULL"), nullable=True)
    visual_entity_id: Mapped[str | None] = mapped_column(ForeignKey("visual_reasoning_objects.entity_id", ondelete="SET NULL"), nullable=True)
    scene_state: Mapped[str] = mapped_column(String(50), nullable=False, default="draft", index=True)
    spatial_reference_json: Mapped[dict] = mapped_column(JSON, default=dict)
    temporal_reference_json: Mapped[dict] = mapped_column(JSON, default=dict)
    spatial_extent_json: Mapped[dict] = mapped_column(JSON, default=dict)
    temporal_start: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    temporal_end: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    provenance_json: Mapped[dict] = mapped_column(JSON, default=dict)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_by: Mapped[str] = mapped_column(String(255), nullable=False, default="operator")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

class SpatialFeatureRecord(Base):
    __tablename__ = "spatial_temporal_features"
    __table_args__ = (
        UniqueConstraint("scene_id", "feature_key", name="uq_spatiotemporal_feature_scene_key"),
        Index("ix_spatiotemporal_feature_scene", "scene_id"),
        Index("ix_spatiotemporal_feature_entity", "bound_entity_id"),
        Index("ix_spatiotemporal_feature_kind", "feature_kind"),
    )
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    scene_id: Mapped[str] = mapped_column(ForeignKey("spatial_temporal_scenes.id", ondelete="CASCADE"), nullable=False)
    feature_key: Mapped[str] = mapped_column(String(180), nullable=False)
    label: Mapped[str] = mapped_column(String(300), nullable=False)
    feature_kind: Mapped[str] = mapped_column(String(100), nullable=False, default="feature")
    geometry_type: Mapped[str] = mapped_column(String(50), nullable=False)
    geometry_json: Mapped[dict] = mapped_column(JSON, nullable=False)
    srid: Mapped[int] = mapped_column(Integer, nullable=False, default=4326)
    crs: Mapped[str] = mapped_column(String(120), nullable=False, default="EPSG:4326")
    spatial_role: Mapped[str] = mapped_column(String(80), nullable=False, default="context")
    bound_entity_id: Mapped[str | None] = mapped_column(ForeignKey("entities.id", ondelete="SET NULL"), nullable=True)
    visual_element_id: Mapped[str | None] = mapped_column(ForeignKey("visual_reasoning_elements.id", ondelete="SET NULL"), nullable=True)
    temporal_start: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    temporal_end: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    properties_json: Mapped[dict] = mapped_column(JSON, default=dict)
    uncertainty_json: Mapped[dict] = mapped_column(JSON, default=dict)
    provenance_json: Mapped[dict] = mapped_column(JSON, default=dict)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

class TemporalEventRecord(Base):
    __tablename__ = "spatial_temporal_events"
    __table_args__ = (
        UniqueConstraint("scene_id", "event_key", name="uq_spatiotemporal_event_scene_key"),
        Index("ix_spatiotemporal_event_scene_time", "scene_id", "starts_at"),
        Index("ix_spatiotemporal_event_kind", "event_kind"),
    )
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    scene_id: Mapped[str] = mapped_column(ForeignKey("spatial_temporal_scenes.id", ondelete="CASCADE"), nullable=False)
    event_key: Mapped[str] = mapped_column(String(180), nullable=False)
    label: Mapped[str] = mapped_column(String(300), nullable=False)
    event_kind: Mapped[str] = mapped_column(String(100), nullable=False, default="event")
    starts_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    ends_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    temporal_precision: Mapped[str] = mapped_column(String(50), nullable=False, default="instant")
    timezone_name: Mapped[str] = mapped_column(String(100), nullable=False, default="UTC")
    bound_entity_id: Mapped[str | None] = mapped_column(ForeignKey("entities.id", ondelete="SET NULL"), nullable=True)
    feature_id: Mapped[str | None] = mapped_column(ForeignKey("spatial_temporal_features.id", ondelete="SET NULL"), nullable=True)
    uncertainty_json: Mapped[dict] = mapped_column(JSON, default=dict)
    provenance_json: Mapped[dict] = mapped_column(JSON, default=dict)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

class TrajectoryRecord(Base):
    __tablename__ = "spatial_temporal_trajectories"
    __table_args__ = (
        UniqueConstraint("scene_id", "trajectory_key", name="uq_spatiotemporal_trajectory_scene_key"),
        Index("ix_spatiotemporal_trajectory_scene", "scene_id"),
        Index("ix_spatiotemporal_trajectory_subject", "subject_entity_id"),
    )
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    scene_id: Mapped[str] = mapped_column(ForeignKey("spatial_temporal_scenes.id", ondelete="CASCADE"), nullable=False)
    trajectory_key: Mapped[str] = mapped_column(String(180), nullable=False)
    label: Mapped[str] = mapped_column(String(300), nullable=False)
    subject_entity_id: Mapped[str | None] = mapped_column(ForeignKey("entities.id", ondelete="SET NULL"), nullable=True)
    feature_id: Mapped[str | None] = mapped_column(ForeignKey("spatial_temporal_features.id", ondelete="SET NULL"), nullable=True)
    interpolation: Mapped[str] = mapped_column(String(80), nullable=False, default="linear")
    unit: Mapped[str | None] = mapped_column(String(120), nullable=True)
    provenance_json: Mapped[dict] = mapped_column(JSON, default=dict)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

class TrajectoryPointRecord(Base):
    __tablename__ = "spatial_temporal_trajectory_points"
    __table_args__ = (
        UniqueConstraint("trajectory_id", "sequence_position", name="uq_spatiotemporal_trajectory_point_position"),
        Index("ix_spatiotemporal_trajectory_point_time", "trajectory_id", "observed_at"),
    )
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    trajectory_id: Mapped[str] = mapped_column(ForeignKey("spatial_temporal_trajectories.id", ondelete="CASCADE"), nullable=False)
    sequence_position: Mapped[int] = mapped_column(Integer, nullable=False)
    observed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    geometry_json: Mapped[dict] = mapped_column(JSON, nullable=False)
    srid: Mapped[int] = mapped_column(Integer, nullable=False, default=4326)
    value_json: Mapped[object] = mapped_column(JSON, nullable=True)
    uncertainty_json: Mapped[dict] = mapped_column(JSON, default=dict)
    provenance_json: Mapped[dict] = mapped_column(JSON, default=dict)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

class SpatialTemporalChangeRecord(Base):
    __tablename__ = "spatial_temporal_changes"
    __table_args__ = (
        UniqueConstraint("scene_id", "change_key", name="uq_spatiotemporal_change_scene_key"),
        Index("ix_spatiotemporal_change_scene", "scene_id"),
        Index("ix_spatiotemporal_change_kind", "change_kind"),
    )
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    scene_id: Mapped[str] = mapped_column(ForeignKey("spatial_temporal_scenes.id", ondelete="CASCADE"), nullable=False)
    change_key: Mapped[str] = mapped_column(String(180), nullable=False)
    label: Mapped[str] = mapped_column(String(300), nullable=False)
    change_kind: Mapped[str] = mapped_column(String(100), nullable=False, default="change")
    feature_id: Mapped[str | None] = mapped_column(ForeignKey("spatial_temporal_features.id", ondelete="SET NULL"), nullable=True)
    before_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    after_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    before_json: Mapped[object] = mapped_column(JSON, nullable=True)
    after_json: Mapped[object] = mapped_column(JSON, nullable=True)
    delta_json: Mapped[object] = mapped_column(JSON, nullable=True)
    method: Mapped[str] = mapped_column(String(120), nullable=False, default="reported")
    source_execution_json: Mapped[dict] = mapped_column(JSON, default=dict)
    provenance_json: Mapped[dict] = mapped_column(JSON, default=dict)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

class SpatialTemporalViewRecord(Base):
    __tablename__ = "spatial_temporal_views"
    __table_args__ = (
        UniqueConstraint("scene_id", "view_key", name="uq_spatiotemporal_view_scene_key"),
        Index("ix_spatiotemporal_view_scene", "scene_id"),
        Index("ix_spatiotemporal_view_kind", "view_kind"),
    )
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    scene_id: Mapped[str] = mapped_column(ForeignKey("spatial_temporal_scenes.id", ondelete="CASCADE"), nullable=False)
    view_key: Mapped[str] = mapped_column(String(180), nullable=False)
    name: Mapped[str] = mapped_column(String(300), nullable=False)
    view_kind: Mapped[str] = mapped_column(String(80), nullable=False, default="linked-map-timeline")
    spatial_window_json: Mapped[dict] = mapped_column(JSON, default=dict)
    temporal_start: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    temporal_end: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    layer_config_json: Mapped[list] = mapped_column(JSON, default=list)
    renderer_contract: Mapped[str] = mapped_column(String(120), nullable=False, default="contract.d3")
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


# v2.39.0 — Research Librarian Visual Explanation

class ResearchVisualExplanationRecord(Base):
    __tablename__ = "research_visual_explanations"
    __table_args__ = (
        UniqueConstraint("project_entity_id", "explanation_key", name="uq_research_visual_explanation_project_key"),
        Index("ix_research_visual_explanation_project", "project_entity_id"),
        Index("ix_research_visual_explanation_kind", "explanation_kind"),
        Index("ix_research_visual_explanation_state", "explanation_state"),
        Index("ix_research_visual_explanation_visibility", "visibility"),
    )
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    explanation_key: Mapped[str] = mapped_column(String(180), nullable=False)
    name: Mapped[str] = mapped_column(String(300), nullable=False)
    question: Mapped[str | None] = mapped_column(Text, nullable=True)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    explanation_kind: Mapped[str] = mapped_column(String(100), nullable=False, default="evidence-map")
    explanation_state: Mapped[str] = mapped_column(String(50), nullable=False, default="draft", index=True)
    visibility: Mapped[str] = mapped_column(String(30), nullable=False, default="private", index=True)
    audience: Mapped[str] = mapped_column(String(100), nullable=False, default="general")
    project_entity_id: Mapped[str] = mapped_column(ForeignKey("entities.id", ondelete="CASCADE"), nullable=False)
    research_subject_entity_id: Mapped[str | None] = mapped_column(ForeignKey("entities.id", ondelete="SET NULL"), nullable=True)
    visual_entity_id: Mapped[str | None] = mapped_column(ForeignKey("visual_reasoning_objects.entity_id", ondelete="SET NULL"), nullable=True)
    source_scope_json: Mapped[dict] = mapped_column(JSON, default=dict)
    provenance_json: Mapped[dict] = mapped_column(JSON, default=dict)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_by: Mapped[str] = mapped_column(String(255), nullable=False, default="operator")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

class ResearchExplanationNodeRecord(Base):
    __tablename__ = "research_explanation_nodes"
    __table_args__ = (
        UniqueConstraint("explanation_id", "node_key", name="uq_research_explanation_node_key"),
        Index("ix_research_explanation_node_explanation", "explanation_id"),
        Index("ix_research_explanation_node_kind", "node_kind"),
        Index("ix_research_explanation_node_entity", "bound_entity_id"),
    )
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    explanation_id: Mapped[str] = mapped_column(ForeignKey("research_visual_explanations.id", ondelete="CASCADE"), nullable=False)
    node_key: Mapped[str] = mapped_column(String(180), nullable=False)
    node_kind: Mapped[str] = mapped_column(String(80), nullable=False, default="concept")
    label: Mapped[str] = mapped_column(String(300), nullable=False)
    body: Mapped[str | None] = mapped_column(Text, nullable=True)
    bound_entity_id: Mapped[str | None] = mapped_column(ForeignKey("entities.id", ondelete="SET NULL"), nullable=True)
    visual_element_id: Mapped[str | None] = mapped_column(ForeignKey("visual_reasoning_elements.id", ondelete="SET NULL"), nullable=True)
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    sequence_position: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    citation_required: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    visual_role: Mapped[str] = mapped_column(String(80), nullable=False, default="content")
    provenance_json: Mapped[dict] = mapped_column(JSON, default=dict)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

class ResearchExplanationRelationRecord(Base):
    __tablename__ = "research_explanation_relations"
    __table_args__ = (
        UniqueConstraint("explanation_id", "relation_key", name="uq_research_explanation_relation_key"),
        Index("ix_research_explanation_relation_explanation", "explanation_id"),
        Index("ix_research_explanation_relation_kind", "relation_kind"),
    )
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    explanation_id: Mapped[str] = mapped_column(ForeignKey("research_visual_explanations.id", ondelete="CASCADE"), nullable=False)
    relation_key: Mapped[str] = mapped_column(String(180), nullable=False)
    source_node_id: Mapped[str] = mapped_column(ForeignKey("research_explanation_nodes.id", ondelete="CASCADE"), nullable=False)
    target_node_id: Mapped[str] = mapped_column(ForeignKey("research_explanation_nodes.id", ondelete="CASCADE"), nullable=False)
    relation_kind: Mapped[str] = mapped_column(String(80), nullable=False, default="relates-to")
    label: Mapped[str | None] = mapped_column(String(300), nullable=True)
    strength: Mapped[float | None] = mapped_column(Float, nullable=True)
    rationale: Mapped[str | None] = mapped_column(Text, nullable=True)
    provenance_json: Mapped[dict] = mapped_column(JSON, default=dict)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

class ResearchExplanationCitationRecord(Base):
    __tablename__ = "research_explanation_citations"
    __table_args__ = (
        UniqueConstraint("explanation_id", "citation_key", name="uq_research_explanation_citation_key"),
        Index("ix_research_explanation_citation_explanation", "explanation_id"),
        Index("ix_research_explanation_citation_node", "node_id"),
        Index("ix_research_explanation_citation_evidence", "evidence_id"),
        Index("ix_research_explanation_citation_snapshot", "source_snapshot_id"),
    )
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    explanation_id: Mapped[str] = mapped_column(ForeignKey("research_visual_explanations.id", ondelete="CASCADE"), nullable=False)
    citation_key: Mapped[str] = mapped_column(String(180), nullable=False)
    node_id: Mapped[str | None] = mapped_column(ForeignKey("research_explanation_nodes.id", ondelete="CASCADE"), nullable=True)
    evidence_id: Mapped[str | None] = mapped_column(ForeignKey("evidence_records.id", ondelete="SET NULL"), nullable=True)
    source_snapshot_id: Mapped[str | None] = mapped_column(ForeignKey("source_snapshots.id", ondelete="SET NULL"), nullable=True)
    source_entity_id: Mapped[str | None] = mapped_column(ForeignKey("entities.id", ondelete="SET NULL"), nullable=True)
    external_uri: Mapped[str | None] = mapped_column(String(1500), nullable=True)
    citation_label: Mapped[str | None] = mapped_column(String(500), nullable=True)
    locator_json: Mapped[dict] = mapped_column(JSON, default=dict)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    provenance_json: Mapped[dict] = mapped_column(JSON, default=dict)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

class ResearchExplanationViewRecord(Base):
    __tablename__ = "research_explanation_views"
    __table_args__ = (
        UniqueConstraint("explanation_id", "view_key", name="uq_research_explanation_view_key"),
        Index("ix_research_explanation_view_explanation", "explanation_id"),
        Index("ix_research_explanation_view_kind", "view_kind"),
    )
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    explanation_id: Mapped[str] = mapped_column(ForeignKey("research_visual_explanations.id", ondelete="CASCADE"), nullable=False)
    view_key: Mapped[str] = mapped_column(String(180), nullable=False)
    name: Mapped[str] = mapped_column(String(300), nullable=False)
    view_kind: Mapped[str] = mapped_column(String(80), nullable=False, default="evidence-map")
    renderer_contract: Mapped[str] = mapped_column(String(120), nullable=False, default="contract.d3")
    focus_node_ids_json: Mapped[list] = mapped_column(JSON, default=list)
    layer_config_json: Mapped[list] = mapped_column(JSON, default=list)
    layout_hints_json: Mapped[dict] = mapped_column(JSON, default=dict)
    legend_json: Mapped[dict] = mapped_column(JSON, default=dict)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

class ResearchExplanationSnapshotRecord(Base):
    __tablename__ = "research_explanation_snapshots"
    __table_args__ = (
        UniqueConstraint("explanation_id", "revision", name="uq_research_explanation_snapshot_revision"),
        Index("ix_research_explanation_snapshot_explanation", "explanation_id"),
        Index("ix_research_explanation_snapshot_hash", "content_hash"),
    )
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    explanation_id: Mapped[str] = mapped_column(ForeignKey("research_visual_explanations.id", ondelete="CASCADE"), nullable=False)
    revision: Mapped[int] = mapped_column(Integer, nullable=False)
    content_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    state_json: Mapped[dict] = mapped_column(JSON, nullable=False)
    provenance_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_by: Mapped[str] = mapped_column(String(255), nullable=False, default="operator")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

# v2.40.0 — Cross-Product Visual Research Objects

class CrossProductVisualResearchObjectRecord(Base):
    __tablename__ = "cross_product_visual_research_objects"
    __table_args__ = (
        UniqueConstraint("project_entity_id", "object_key", name="uq_cross_product_visual_research_project_key"),
        Index("ix_cross_product_visual_research_project", "project_entity_id"),
        Index("ix_cross_product_visual_research_kind", "object_kind"),
        Index("ix_cross_product_visual_research_state", "lifecycle_state"),
        Index("ix_cross_product_visual_research_visibility", "visibility"),
    )
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    object_key: Mapped[str] = mapped_column(String(180), nullable=False)
    name: Mapped[str] = mapped_column(String(300), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    object_kind: Mapped[str] = mapped_column(String(100), nullable=False, default="research-composite")
    lifecycle_state: Mapped[str] = mapped_column(String(50), nullable=False, default="draft")
    visibility: Mapped[str] = mapped_column(String(30), nullable=False, default="private")
    project_entity_id: Mapped[str] = mapped_column(ForeignKey("entities.id", ondelete="CASCADE"), nullable=False)
    root_visual_entity_id: Mapped[str | None] = mapped_column(ForeignKey("visual_reasoning_objects.entity_id", ondelete="SET NULL"), nullable=True)
    root_explanation_id: Mapped[str | None] = mapped_column(ForeignKey("research_visual_explanations.id", ondelete="SET NULL"), nullable=True)
    source_products_json: Mapped[list] = mapped_column(JSON, default=list)
    provenance_json: Mapped[dict] = mapped_column(JSON, default=dict)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_by: Mapped[str] = mapped_column(String(255), nullable=False, default="operator")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)


class CrossProductVisualResearchMemberRecord(Base):
    __tablename__ = "cross_product_visual_research_members"
    __table_args__ = (
        UniqueConstraint("object_id", "member_key", name="uq_cross_product_visual_research_member_key"),
        Index("ix_cross_product_visual_research_member_object", "object_id"),
        Index("ix_cross_product_visual_research_member_product", "source_product"),
        Index("ix_cross_product_visual_research_member_kind", "member_kind"),
        Index("ix_cross_product_visual_research_member_entity", "local_entity_id"),
    )
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    object_id: Mapped[str] = mapped_column(ForeignKey("cross_product_visual_research_objects.id", ondelete="CASCADE"), nullable=False)
    member_key: Mapped[str] = mapped_column(String(180), nullable=False)
    member_kind: Mapped[str] = mapped_column(String(100), nullable=False, default="research-object")
    source_product: Mapped[str] = mapped_column(String(80), nullable=False)
    semantic_role: Mapped[str] = mapped_column(String(100), nullable=False, default="context")
    label: Mapped[str] = mapped_column(String(300), nullable=False)
    local_entity_id: Mapped[str | None] = mapped_column(ForeignKey("entities.id", ondelete="SET NULL"), nullable=True)
    visual_entity_id: Mapped[str | None] = mapped_column(ForeignKey("visual_reasoning_objects.entity_id", ondelete="SET NULL"), nullable=True)
    explanation_id: Mapped[str | None] = mapped_column(ForeignKey("research_visual_explanations.id", ondelete="SET NULL"), nullable=True)
    external_ref: Mapped[str | None] = mapped_column(String(1500), nullable=True)
    source_ref_json: Mapped[dict] = mapped_column(JSON, default=dict)
    display_json: Mapped[dict] = mapped_column(JSON, default=dict)
    provenance_json: Mapped[dict] = mapped_column(JSON, default=dict)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class CrossProductVisualResearchRelationRecord(Base):
    __tablename__ = "cross_product_visual_research_relations"
    __table_args__ = (
        UniqueConstraint("object_id", "relation_key", name="uq_cross_product_visual_research_relation_key"),
        Index("ix_cross_product_visual_research_relation_object", "object_id"),
        Index("ix_cross_product_visual_research_relation_kind", "relation_kind"),
    )
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    object_id: Mapped[str] = mapped_column(ForeignKey("cross_product_visual_research_objects.id", ondelete="CASCADE"), nullable=False)
    relation_key: Mapped[str] = mapped_column(String(180), nullable=False)
    source_member_id: Mapped[str] = mapped_column(ForeignKey("cross_product_visual_research_members.id", ondelete="CASCADE"), nullable=False)
    target_member_id: Mapped[str] = mapped_column(ForeignKey("cross_product_visual_research_members.id", ondelete="CASCADE"), nullable=False)
    relation_kind: Mapped[str] = mapped_column(String(80), nullable=False, default="relates-to")
    directed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    label: Mapped[str | None] = mapped_column(String(300), nullable=True)
    rationale: Mapped[str | None] = mapped_column(Text, nullable=True)
    provenance_json: Mapped[dict] = mapped_column(JSON, default=dict)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class CrossProductVisualResearchViewRecord(Base):
    __tablename__ = "cross_product_visual_research_views"
    __table_args__ = (
        UniqueConstraint("object_id", "view_key", name="uq_cross_product_visual_research_view_key"),
        Index("ix_cross_product_visual_research_view_object", "object_id"),
        Index("ix_cross_product_visual_research_view_kind", "view_kind"),
    )
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    object_id: Mapped[str] = mapped_column(ForeignKey("cross_product_visual_research_objects.id", ondelete="CASCADE"), nullable=False)
    view_key: Mapped[str] = mapped_column(String(180), nullable=False)
    name: Mapped[str] = mapped_column(String(300), nullable=False)
    view_kind: Mapped[str] = mapped_column(String(80), nullable=False, default="composite")
    renderer_contract: Mapped[str] = mapped_column(String(120), nullable=False, default="contract.d3")
    member_order_json: Mapped[list] = mapped_column(JSON, default=list)
    layer_config_json: Mapped[list] = mapped_column(JSON, default=list)
    layout_hints_json: Mapped[dict] = mapped_column(JSON, default=dict)
    interaction_json: Mapped[dict] = mapped_column(JSON, default=dict)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class CrossProductVisualResearchSnapshotRecord(Base):
    __tablename__ = "cross_product_visual_research_snapshots"
    __table_args__ = (
        UniqueConstraint("object_id", "revision", name="uq_cross_product_visual_research_snapshot_revision"),
        Index("ix_cross_product_visual_research_snapshot_object", "object_id"),
        Index("ix_cross_product_visual_research_snapshot_hash", "content_hash"),
    )
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    object_id: Mapped[str] = mapped_column(ForeignKey("cross_product_visual_research_objects.id", ondelete="CASCADE"), nullable=False)
    revision: Mapped[int] = mapped_column(Integer, nullable=False)
    content_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    state_json: Mapped[dict] = mapped_column(JSON, nullable=False)
    provenance_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_by: Mapped[str] = mapped_column(String(255), nullable=False, default="operator")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


# v2.41.0 — Reproducible Visual Knowledge Layer

class ReproducibleVisualKnowledgePackageRecord(Base):
    __tablename__ = "reproducible_visual_knowledge_packages"
    __table_args__ = (
        UniqueConstraint("project_entity_id", "package_key", name="uq_repro_visual_knowledge_project_key"),
        Index("ix_repro_visual_knowledge_project", "project_entity_id"),
        Index("ix_repro_visual_knowledge_source_object", "source_object_id"),
        Index("ix_repro_visual_knowledge_state", "lifecycle_state"),
        Index("ix_repro_visual_knowledge_visibility", "visibility"),
    )
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    package_key: Mapped[str] = mapped_column(String(180), nullable=False)
    name: Mapped[str] = mapped_column(String(300), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    project_entity_id: Mapped[str] = mapped_column(ForeignKey("entities.id", ondelete="CASCADE"), nullable=False)
    source_object_id: Mapped[str] = mapped_column(ForeignKey("cross_product_visual_research_objects.id", ondelete="CASCADE"), nullable=False)
    source_snapshot_id: Mapped[str | None] = mapped_column(ForeignKey("cross_product_visual_research_snapshots.id", ondelete="SET NULL"), nullable=True)
    lifecycle_state: Mapped[str] = mapped_column(String(50), nullable=False, default="draft")
    visibility: Mapped[str] = mapped_column(String(30), nullable=False, default="private")
    reproducibility_level: Mapped[str] = mapped_column(String(50), nullable=False, default="documented")
    knowledge_contract: Mapped[str] = mapped_column(String(120), nullable=False, default="sc.reproducible-visual-knowledge.v1")
    provenance_json: Mapped[dict] = mapped_column(JSON, default=dict)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_by: Mapped[str] = mapped_column(String(255), nullable=False, default="operator")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)


class ReproducibleVisualKnowledgeInputRecord(Base):
    __tablename__ = "reproducible_visual_knowledge_inputs"
    __table_args__ = (
        UniqueConstraint("package_id", "input_key", name="uq_repro_visual_knowledge_input_key"),
        Index("ix_repro_visual_knowledge_input_package", "package_id"),
        Index("ix_repro_visual_knowledge_input_product", "source_product"),
        Index("ix_repro_visual_knowledge_input_role", "input_role"),
    )
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    package_id: Mapped[str] = mapped_column(ForeignKey("reproducible_visual_knowledge_packages.id", ondelete="CASCADE"), nullable=False)
    input_key: Mapped[str] = mapped_column(String(180), nullable=False)
    label: Mapped[str] = mapped_column(String(300), nullable=False)
    input_role: Mapped[str] = mapped_column(String(80), nullable=False, default="source")
    source_product: Mapped[str] = mapped_column(String(80), nullable=False)
    source_ref: Mapped[str] = mapped_column(String(1500), nullable=False)
    source_version: Mapped[str | None] = mapped_column(String(180), nullable=True)
    content_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    hash_algorithm: Mapped[str] = mapped_column(String(30), nullable=False, default="sha256")
    immutable: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    provenance_json: Mapped[dict] = mapped_column(JSON, default=dict)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class ReproducibleVisualKnowledgeEnvironmentRecord(Base):
    __tablename__ = "reproducible_visual_knowledge_environments"
    __table_args__ = (
        UniqueConstraint("package_id", "environment_key", name="uq_repro_visual_knowledge_environment_key"),
        Index("ix_repro_visual_knowledge_environment_package", "package_id"),
    )
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    package_id: Mapped[str] = mapped_column(ForeignKey("reproducible_visual_knowledge_packages.id", ondelete="CASCADE"), nullable=False)
    environment_key: Mapped[str] = mapped_column(String(180), nullable=False)
    name: Mapped[str] = mapped_column(String(300), nullable=False)
    runtime_versions_json: Mapped[dict] = mapped_column(JSON, default=dict)
    dependencies_json: Mapped[list] = mapped_column(JSON, default=list)
    container_ref: Mapped[str | None] = mapped_column(String(1500), nullable=True)
    container_digest: Mapped[str | None] = mapped_column(String(180), nullable=True)
    code_ref: Mapped[str | None] = mapped_column(String(1500), nullable=True)
    random_seed: Mapped[str | None] = mapped_column(String(180), nullable=True)
    locale: Mapped[str | None] = mapped_column(String(80), nullable=True)
    timezone: Mapped[str | None] = mapped_column(String(80), nullable=True)
    deterministic_claim: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class ReproducibleVisualKnowledgeReplayPlanRecord(Base):
    __tablename__ = "reproducible_visual_knowledge_replay_plans"
    __table_args__ = (
        UniqueConstraint("package_id", "plan_key", name="uq_repro_visual_knowledge_replay_plan_key"),
        Index("ix_repro_visual_knowledge_replay_package", "package_id"),
    )
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    package_id: Mapped[str] = mapped_column(ForeignKey("reproducible_visual_knowledge_packages.id", ondelete="CASCADE"), nullable=False)
    plan_key: Mapped[str] = mapped_column(String(180), nullable=False)
    name: Mapped[str] = mapped_column(String(300), nullable=False)
    steps_json: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    expected_outputs_json: Mapped[list] = mapped_column(JSON, default=list)
    environment_id: Mapped[str | None] = mapped_column(ForeignKey("reproducible_visual_knowledge_environments.id", ondelete="SET NULL"), nullable=True)
    execution_policy: Mapped[str] = mapped_column(String(80), nullable=False, default="external-only")
    provenance_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class ReproducibleVisualKnowledgeVerificationRecord(Base):
    __tablename__ = "reproducible_visual_knowledge_verifications"
    __table_args__ = (
        Index("ix_repro_visual_knowledge_verification_package", "package_id"),
        Index("ix_repro_visual_knowledge_verification_status", "status"),
    )
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    package_id: Mapped[str] = mapped_column(ForeignKey("reproducible_visual_knowledge_packages.id", ondelete="CASCADE"), nullable=False)
    verification_kind: Mapped[str] = mapped_column(String(80), nullable=False, default="integrity")
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="recorded")
    expected_fingerprint: Mapped[str | None] = mapped_column(String(64), nullable=True)
    observed_fingerprint: Mapped[str | None] = mapped_column(String(64), nullable=True)
    verifier_product: Mapped[str] = mapped_column(String(80), nullable=False, default="platform-core")
    external_run_ref: Mapped[str | None] = mapped_column(String(1500), nullable=True)
    assertions_json: Mapped[list] = mapped_column(JSON, default=list)
    evidence_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_by: Mapped[str] = mapped_column(String(255), nullable=False, default="operator")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class ReproducibleVisualKnowledgeSnapshotRecord(Base):
    __tablename__ = "reproducible_visual_knowledge_snapshots"
    __table_args__ = (
        UniqueConstraint("package_id", "revision", name="uq_repro_visual_knowledge_snapshot_revision"),
        Index("ix_repro_visual_knowledge_snapshot_package", "package_id"),
        Index("ix_repro_visual_knowledge_snapshot_hash", "content_hash"),
    )
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    package_id: Mapped[str] = mapped_column(ForeignKey("reproducible_visual_knowledge_packages.id", ondelete="CASCADE"), nullable=False)
    revision: Mapped[int] = mapped_column(Integer, nullable=False)
    content_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    state_json: Mapped[dict] = mapped_column(JSON, nullable=False)
    manifest_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    provenance_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_by: Mapped[str] = mapped_column(String(255), nullable=False, default="operator")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

# v2.42.0 — Open Forensics: Forensic Object Model & Evidence Provenance

class ForensicInvestigationRecord(Base):
    __tablename__ = "forensic_investigations"
    __table_args__ = (
        UniqueConstraint("project_entity_id", "investigation_key", name="uq_forensic_investigation_project_key"),
        Index("ix_forensic_investigation_project", "project_entity_id"),
        Index("ix_forensic_investigation_status", "status"),
        Index("ix_forensic_investigation_visibility", "visibility"),
    )
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    investigation_key: Mapped[str] = mapped_column(String(180), nullable=False)
    name: Mapped[str] = mapped_column(String(300), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    research_question: Mapped[str | None] = mapped_column(Text, nullable=True)
    project_entity_id: Mapped[str] = mapped_column(ForeignKey("entities.id", ondelete="CASCADE"), nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="open")
    visibility: Mapped[str] = mapped_column(String(30), nullable=False, default="private")
    forensic_contract: Mapped[str] = mapped_column(String(120), nullable=False, default="sc.open-forensics.investigation.v1")
    scope_json: Mapped[dict] = mapped_column(JSON, default=dict)
    provenance_json: Mapped[dict] = mapped_column(JSON, default=dict)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_by: Mapped[str] = mapped_column(String(255), nullable=False, default="operator")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)


class ForensicObjectRecord(Base):
    __tablename__ = "forensic_objects"
    __table_args__ = (
        UniqueConstraint("investigation_id", "object_key", name="uq_forensic_object_key"),
        Index("ix_forensic_object_investigation", "investigation_id"),
        Index("ix_forensic_object_kind", "object_kind"),
        Index("ix_forensic_object_entity", "bound_entity_id"),
    )
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    investigation_id: Mapped[str] = mapped_column(ForeignKey("forensic_investigations.id", ondelete="CASCADE"), nullable=False)
    object_key: Mapped[str] = mapped_column(String(180), nullable=False)
    object_kind: Mapped[str] = mapped_column(String(80), nullable=False)
    label: Mapped[str] = mapped_column(String(300), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    bound_entity_id: Mapped[str | None] = mapped_column(ForeignKey("entities.id", ondelete="SET NULL"), nullable=True)
    source_product: Mapped[str | None] = mapped_column(String(80), nullable=True)
    source_ref: Mapped[str | None] = mapped_column(String(1500), nullable=True)
    observed_context_json: Mapped[dict] = mapped_column(JSON, default=dict)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="observed")
    provenance_json: Mapped[dict] = mapped_column(JSON, default=dict)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)


class ForensicEvidenceItemRecord(Base):
    __tablename__ = "forensic_evidence_items"
    __table_args__ = (
        UniqueConstraint("investigation_id", "evidence_key", name="uq_forensic_evidence_key"),
        Index("ix_forensic_evidence_investigation", "investigation_id"),
        Index("ix_forensic_evidence_object", "forensic_object_id"),
        Index("ix_forensic_evidence_hash", "content_hash"),
        Index("ix_forensic_evidence_kind", "evidence_kind"),
    )
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    investigation_id: Mapped[str] = mapped_column(ForeignKey("forensic_investigations.id", ondelete="CASCADE"), nullable=False)
    forensic_object_id: Mapped[str | None] = mapped_column(ForeignKey("forensic_objects.id", ondelete="SET NULL"), nullable=True)
    evidence_key: Mapped[str] = mapped_column(String(180), nullable=False)
    evidence_kind: Mapped[str] = mapped_column(String(80), nullable=False)
    label: Mapped[str] = mapped_column(String(300), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    mime_type: Mapped[str | None] = mapped_column(String(180), nullable=True)
    byte_size: Mapped[int | None] = mapped_column(Integer, nullable=True)
    content_hash: Mapped[str | None] = mapped_column(String(128), nullable=True)
    hash_algorithm: Mapped[str | None] = mapped_column(String(30), nullable=True, default="sha256")
    source_snapshot_id: Mapped[str | None] = mapped_column(ForeignKey("source_snapshots.id", ondelete="SET NULL"), nullable=True)
    evidence_record_id: Mapped[str | None] = mapped_column(ForeignKey("evidence_records.id", ondelete="SET NULL"), nullable=True)
    integrity_state: Mapped[str] = mapped_column(String(50), nullable=False, default="unverified")
    provenance_json: Mapped[dict] = mapped_column(JSON, default=dict)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)


class ForensicEvidenceSourceBindingRecord(Base):
    __tablename__ = "forensic_evidence_source_bindings"
    __table_args__ = (
        UniqueConstraint("evidence_item_id", "binding_key", name="uq_forensic_source_binding_key"),
        Index("ix_forensic_source_binding_evidence", "evidence_item_id"),
        Index("ix_forensic_source_binding_kind", "source_kind"),
    )
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    evidence_item_id: Mapped[str] = mapped_column(ForeignKey("forensic_evidence_items.id", ondelete="CASCADE"), nullable=False)
    binding_key: Mapped[str] = mapped_column(String(180), nullable=False)
    source_kind: Mapped[str] = mapped_column(String(80), nullable=False)
    source_ref: Mapped[str] = mapped_column(String(2000), nullable=False)
    source_version: Mapped[str | None] = mapped_column(String(300), nullable=True)
    locator: Mapped[str | None] = mapped_column(String(2000), nullable=True)
    source_snapshot_id: Mapped[str | None] = mapped_column(ForeignKey("source_snapshots.id", ondelete="SET NULL"), nullable=True)
    evidence_record_id: Mapped[str | None] = mapped_column(ForeignKey("evidence_records.id", ondelete="SET NULL"), nullable=True)
    observed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    retrieved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    content_hash: Mapped[str | None] = mapped_column(String(128), nullable=True)
    hash_algorithm: Mapped[str | None] = mapped_column(String(30), nullable=True, default="sha256")
    provenance_json: Mapped[dict] = mapped_column(JSON, default=dict)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class ForensicProvenanceActivityRecord(Base):
    __tablename__ = "forensic_provenance_activities"
    __table_args__ = (
        Index("ix_forensic_provenance_investigation", "investigation_id"),
        Index("ix_forensic_provenance_evidence", "evidence_item_id"),
        Index("ix_forensic_provenance_kind", "activity_kind"),
    )
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    investigation_id: Mapped[str] = mapped_column(ForeignKey("forensic_investigations.id", ondelete="CASCADE"), nullable=False)
    evidence_item_id: Mapped[str | None] = mapped_column(ForeignKey("forensic_evidence_items.id", ondelete="SET NULL"), nullable=True)
    activity_kind: Mapped[str] = mapped_column(String(80), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    actor_ref: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    tool_ref: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    inputs_json: Mapped[list] = mapped_column(JSON, default=list)
    outputs_json: Mapped[list] = mapped_column(JSON, default=list)
    provenance_json: Mapped[dict] = mapped_column(JSON, default=dict)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class ForensicObjectRelationRecord(Base):
    __tablename__ = "forensic_object_relations"
    __table_args__ = (
        UniqueConstraint("investigation_id", "relation_key", name="uq_forensic_object_relation_key"),
        Index("ix_forensic_relation_investigation", "investigation_id"),
        Index("ix_forensic_relation_source", "source_object_id"),
        Index("ix_forensic_relation_target", "target_object_id"),
        Index("ix_forensic_relation_kind", "relation_kind"),
    )
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    investigation_id: Mapped[str] = mapped_column(ForeignKey("forensic_investigations.id", ondelete="CASCADE"), nullable=False)
    relation_key: Mapped[str] = mapped_column(String(180), nullable=False)
    source_object_id: Mapped[str] = mapped_column(ForeignKey("forensic_objects.id", ondelete="CASCADE"), nullable=False)
    target_object_id: Mapped[str] = mapped_column(ForeignKey("forensic_objects.id", ondelete="CASCADE"), nullable=False)
    relation_kind: Mapped[str] = mapped_column(String(80), nullable=False)
    assertion_state: Mapped[str] = mapped_column(String(50), nullable=False, default="observed")
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    basis_json: Mapped[dict] = mapped_column(JSON, default=dict)
    provenance_json: Mapped[dict] = mapped_column(JSON, default=dict)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class ForensicSnapshotRecord(Base):
    __tablename__ = "forensic_snapshots"
    __table_args__ = (
        UniqueConstraint("investigation_id", "revision", name="uq_forensic_snapshot_revision"),
        Index("ix_forensic_snapshot_investigation", "investigation_id"),
        Index("ix_forensic_snapshot_hash", "content_hash"),
    )
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    investigation_id: Mapped[str] = mapped_column(ForeignKey("forensic_investigations.id", ondelete="CASCADE"), nullable=False)
    revision: Mapped[int] = mapped_column(Integer, nullable=False)
    content_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    state_json: Mapped[dict] = mapped_column(JSON, nullable=False)
    provenance_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_by: Mapped[str] = mapped_column(String(255), nullable=False, default="operator")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


# v2.43.0 — Open Forensics: Evidence Integrity & Chain of Custody

class ForensicCustodianRecord(Base):
    __tablename__ = "forensic_custodians"
    __table_args__ = (
        UniqueConstraint("investigation_id", "custodian_key", name="uq_forensic_custodian_key"),
        Index("ix_forensic_custodian_investigation", "investigation_id"),
        Index("ix_forensic_custodian_actor", "actor_ref"),
    )
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    investigation_id: Mapped[str] = mapped_column(ForeignKey("forensic_investigations.id", ondelete="CASCADE"), nullable=False)
    custodian_key: Mapped[str] = mapped_column(String(180), nullable=False)
    display_name: Mapped[str] = mapped_column(String(300), nullable=False)
    actor_ref: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    organization_ref: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    role: Mapped[str | None] = mapped_column(String(180), nullable=True)
    identity_verification_state: Mapped[str] = mapped_column(String(50), nullable=False, default="unverified")
    external_identity_attestation_ref: Mapped[str | None] = mapped_column(String(2000), nullable=True)
    provenance_json: Mapped[dict] = mapped_column(JSON, default=dict)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class ForensicCustodyEventRecord(Base):
    __tablename__ = "forensic_custody_events"
    __table_args__ = (
        UniqueConstraint("evidence_item_id", "sequence", name="uq_forensic_custody_event_sequence"),
        Index("ix_forensic_custody_event_investigation", "investigation_id"),
        Index("ix_forensic_custody_event_evidence", "evidence_item_id"),
        Index("ix_forensic_custody_event_hash", "event_hash"),
        Index("ix_forensic_custody_event_kind", "event_kind"),
    )
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    investigation_id: Mapped[str] = mapped_column(ForeignKey("forensic_investigations.id", ondelete="CASCADE"), nullable=False)
    evidence_item_id: Mapped[str] = mapped_column(ForeignKey("forensic_evidence_items.id", ondelete="CASCADE"), nullable=False)
    sequence: Mapped[int] = mapped_column(Integer, nullable=False)
    event_kind: Mapped[str] = mapped_column(String(80), nullable=False)
    from_custodian_id: Mapped[str | None] = mapped_column(ForeignKey("forensic_custodians.id", ondelete="SET NULL"), nullable=True)
    to_custodian_id: Mapped[str | None] = mapped_column(ForeignKey("forensic_custodians.id", ondelete="SET NULL"), nullable=True)
    location_ref: Mapped[str | None] = mapped_column(String(1500), nullable=True)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    previous_event_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    event_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    external_attestation_ref: Mapped[str | None] = mapped_column(String(2000), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    provenance_json: Mapped[dict] = mapped_column(JSON, default=dict)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)


class ForensicEvidenceSealRecord(Base):
    __tablename__ = "forensic_evidence_seals"
    __table_args__ = (
        UniqueConstraint("evidence_item_id", "seal_identifier", name="uq_forensic_evidence_seal_identifier"),
        Index("ix_forensic_evidence_seal_evidence", "evidence_item_id"),
        Index("ix_forensic_evidence_seal_status", "status"),
    )
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    evidence_item_id: Mapped[str] = mapped_column(ForeignKey("forensic_evidence_items.id", ondelete="CASCADE"), nullable=False)
    seal_identifier: Mapped[str] = mapped_column(String(300), nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="sealed")
    sealed_by_custodian_id: Mapped[str | None] = mapped_column(ForeignKey("forensic_custodians.id", ondelete="SET NULL"), nullable=True)
    sealed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    unsealed_by_custodian_id: Mapped[str | None] = mapped_column(ForeignKey("forensic_custodians.id", ondelete="SET NULL"), nullable=True)
    unsealed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    content_hash_at_seal: Mapped[str | None] = mapped_column(String(128), nullable=True)
    hash_algorithm: Mapped[str | None] = mapped_column(String(30), nullable=True, default="sha256")
    external_attestation_ref: Mapped[str | None] = mapped_column(String(2000), nullable=True)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    provenance_json: Mapped[dict] = mapped_column(JSON, default=dict)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)


class ForensicIntegrityCheckRecord(Base):
    __tablename__ = "forensic_integrity_checks"
    __table_args__ = (
        UniqueConstraint("evidence_item_id", "check_key", name="uq_forensic_integrity_check_key"),
        Index("ix_forensic_integrity_check_evidence", "evidence_item_id"),
        Index("ix_forensic_integrity_check_status", "status"),
    )
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    evidence_item_id: Mapped[str] = mapped_column(ForeignKey("forensic_evidence_items.id", ondelete="CASCADE"), nullable=False)
    check_key: Mapped[str] = mapped_column(String(180), nullable=False)
    check_kind: Mapped[str] = mapped_column(String(80), nullable=False, default="content-hash")
    hash_algorithm: Mapped[str] = mapped_column(String(30), nullable=False, default="sha256")
    expected_hash: Mapped[str | None] = mapped_column(String(128), nullable=True)
    observed_hash: Mapped[str | None] = mapped_column(String(128), nullable=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False)
    checker_ref: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    tool_ref: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    checked_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    external_attestation_ref: Mapped[str | None] = mapped_column(String(2000), nullable=True)
    evidence_json: Mapped[dict] = mapped_column(JSON, default=dict)
    provenance_json: Mapped[dict] = mapped_column(JSON, default=dict)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class ForensicCustodyContinuityAssessmentRecord(Base):
    __tablename__ = "forensic_custody_continuity_assessments"
    __table_args__ = (
        UniqueConstraint("evidence_item_id", "assessment_key", name="uq_forensic_custody_assessment_key"),
        Index("ix_forensic_custody_assessment_evidence", "evidence_item_id"),
        Index("ix_forensic_custody_assessment_status", "status"),
    )
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    evidence_item_id: Mapped[str] = mapped_column(ForeignKey("forensic_evidence_items.id", ondelete="CASCADE"), nullable=False)
    assessment_key: Mapped[str] = mapped_column(String(180), nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False)
    event_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    gap_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    hash_chain_valid: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    findings_json: Mapped[list] = mapped_column(JSON, default=list)
    assessed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    generated_by: Mapped[str] = mapped_column(String(100), nullable=False, default="platform-core")
    provenance_json: Mapped[dict] = mapped_column(JSON, default=dict)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class ForensicCustodySnapshotRecord(Base):
    __tablename__ = "forensic_custody_snapshots"
    __table_args__ = (
        UniqueConstraint("investigation_id", "revision", name="uq_forensic_custody_snapshot_revision"),
        Index("ix_forensic_custody_snapshot_investigation", "investigation_id"),
        Index("ix_forensic_custody_snapshot_hash", "content_hash"),
    )
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    investigation_id: Mapped[str] = mapped_column(ForeignKey("forensic_investigations.id", ondelete="CASCADE"), nullable=False)
    revision: Mapped[int] = mapped_column(Integer, nullable=False)
    content_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    previous_snapshot_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    state_json: Mapped[dict] = mapped_column(JSON, nullable=False)
    provenance_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_by: Mapped[str] = mapped_column(String(255), nullable=False, default="operator")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


# v2.44.0 — Open Forensics: Claims, Contradictions & Competing Hypotheses

class ForensicClaimRecord(Base):
    __tablename__ = "forensic_claims"
    __table_args__ = (
        UniqueConstraint("investigation_id", "claim_key", name="uq_forensic_claim_key"),
        Index("ix_forensic_claim_investigation", "investigation_id"),
        Index("ix_forensic_claim_kind", "claim_kind"),
        Index("ix_forensic_claim_review_state", "review_state"),
    )
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    investigation_id: Mapped[str] = mapped_column(ForeignKey("forensic_investigations.id", ondelete="CASCADE"), nullable=False)
    claim_key: Mapped[str] = mapped_column(String(180), nullable=False)
    claim_kind: Mapped[str] = mapped_column(String(80), nullable=False, default="factual")
    statement: Mapped[str] = mapped_column(Text, nullable=False)
    subject_ref: Mapped[str | None] = mapped_column(String(1500), nullable=True)
    asserted_by_ref: Mapped[str | None] = mapped_column(String(1500), nullable=True)
    source_ref: Mapped[str | None] = mapped_column(String(2000), nullable=True)
    asserted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    asserted_confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    review_state: Mapped[str] = mapped_column(String(50), nullable=False, default="unassessed")
    provenance_json: Mapped[dict] = mapped_column(JSON, default=dict)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)


class ForensicClaimEvidenceAssessmentRecord(Base):
    __tablename__ = "forensic_claim_evidence_assessments"
    __table_args__ = (
        UniqueConstraint("claim_id", "assessment_key", name="uq_forensic_claim_evidence_assessment_key"),
        Index("ix_forensic_claim_evidence_claim", "claim_id"),
        Index("ix_forensic_claim_evidence_evidence", "evidence_item_id"),
        Index("ix_forensic_claim_evidence_stance", "stance"),
    )
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    claim_id: Mapped[str] = mapped_column(ForeignKey("forensic_claims.id", ondelete="CASCADE"), nullable=False)
    evidence_item_id: Mapped[str] = mapped_column(ForeignKey("forensic_evidence_items.id", ondelete="CASCADE"), nullable=False)
    assessment_key: Mapped[str] = mapped_column(String(180), nullable=False)
    stance: Mapped[str] = mapped_column(String(40), nullable=False)
    diagnosticity: Mapped[float | None] = mapped_column(Float, nullable=True)
    rationale: Mapped[str | None] = mapped_column(Text, nullable=True)
    reliability_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    analyst_ref: Mapped[str | None] = mapped_column(String(1500), nullable=True)
    external_assessment_ref: Mapped[str | None] = mapped_column(String(2000), nullable=True)
    provenance_json: Mapped[dict] = mapped_column(JSON, default=dict)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class ForensicContradictionRecord(Base):
    __tablename__ = "forensic_contradictions"
    __table_args__ = (
        UniqueConstraint("investigation_id", "contradiction_key", name="uq_forensic_contradiction_key"),
        Index("ix_forensic_contradiction_investigation", "investigation_id"),
        Index("ix_forensic_contradiction_left", "left_claim_id"),
        Index("ix_forensic_contradiction_right", "right_claim_id"),
        Index("ix_forensic_contradiction_status", "status"),
    )
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    investigation_id: Mapped[str] = mapped_column(ForeignKey("forensic_investigations.id", ondelete="CASCADE"), nullable=False)
    contradiction_key: Mapped[str] = mapped_column(String(180), nullable=False)
    left_claim_id: Mapped[str] = mapped_column(ForeignKey("forensic_claims.id", ondelete="CASCADE"), nullable=False)
    right_claim_id: Mapped[str] = mapped_column(ForeignKey("forensic_claims.id", ondelete="CASCADE"), nullable=False)
    contradiction_kind: Mapped[str] = mapped_column(String(80), nullable=False, default="direct")
    severity: Mapped[str] = mapped_column(String(30), nullable=False, default="unspecified")
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="open")
    rationale: Mapped[str | None] = mapped_column(Text, nullable=True)
    basis_evidence_ids_json: Mapped[list] = mapped_column(JSON, default=list)
    external_assessment_ref: Mapped[str | None] = mapped_column(String(2000), nullable=True)
    provenance_json: Mapped[dict] = mapped_column(JSON, default=dict)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)


class ForensicHypothesisRecord(Base):
    __tablename__ = "forensic_hypotheses"
    __table_args__ = (
        UniqueConstraint("investigation_id", "hypothesis_key", name="uq_forensic_hypothesis_key"),
        Index("ix_forensic_hypothesis_investigation", "investigation_id"),
        Index("ix_forensic_hypothesis_focal_claim", "focal_claim_id"),
        Index("ix_forensic_hypothesis_status", "status"),
    )
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    investigation_id: Mapped[str] = mapped_column(ForeignKey("forensic_investigations.id", ondelete="CASCADE"), nullable=False)
    hypothesis_key: Mapped[str] = mapped_column(String(180), nullable=False)
    label: Mapped[str] = mapped_column(String(300), nullable=False)
    statement: Mapped[str] = mapped_column(Text, nullable=False)
    focal_claim_id: Mapped[str | None] = mapped_column(ForeignKey("forensic_claims.id", ondelete="SET NULL"), nullable=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="active")
    assumptions_json: Mapped[list] = mapped_column(JSON, default=list)
    predicted_observations_json: Mapped[list] = mapped_column(JSON, default=list)
    disconfirming_conditions_json: Mapped[list] = mapped_column(JSON, default=list)
    provenance_json: Mapped[dict] = mapped_column(JSON, default=dict)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)


class ForensicHypothesisEvidenceAssessmentRecord(Base):
    __tablename__ = "forensic_hypothesis_evidence_assessments"
    __table_args__ = (
        UniqueConstraint("hypothesis_id", "assessment_key", name="uq_forensic_hypothesis_evidence_assessment_key"),
        Index("ix_forensic_hypothesis_evidence_hypothesis", "hypothesis_id"),
        Index("ix_forensic_hypothesis_evidence_evidence", "evidence_item_id"),
        Index("ix_forensic_hypothesis_evidence_consistency", "consistency"),
    )
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    hypothesis_id: Mapped[str] = mapped_column(ForeignKey("forensic_hypotheses.id", ondelete="CASCADE"), nullable=False)
    evidence_item_id: Mapped[str] = mapped_column(ForeignKey("forensic_evidence_items.id", ondelete="CASCADE"), nullable=False)
    assessment_key: Mapped[str] = mapped_column(String(180), nullable=False)
    consistency: Mapped[str] = mapped_column(String(40), nullable=False)
    diagnosticity: Mapped[float | None] = mapped_column(Float, nullable=True)
    rationale: Mapped[str | None] = mapped_column(Text, nullable=True)
    reliability_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    analyst_ref: Mapped[str | None] = mapped_column(String(1500), nullable=True)
    external_assessment_ref: Mapped[str | None] = mapped_column(String(2000), nullable=True)
    provenance_json: Mapped[dict] = mapped_column(JSON, default=dict)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class ForensicHypothesisRelationRecord(Base):
    __tablename__ = "forensic_hypothesis_relations"
    __table_args__ = (
        UniqueConstraint("investigation_id", "relation_key", name="uq_forensic_hypothesis_relation_key"),
        Index("ix_forensic_hypothesis_relation_investigation", "investigation_id"),
        Index("ix_forensic_hypothesis_relation_source", "source_hypothesis_id"),
        Index("ix_forensic_hypothesis_relation_target", "target_hypothesis_id"),
    )
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    investigation_id: Mapped[str] = mapped_column(ForeignKey("forensic_investigations.id", ondelete="CASCADE"), nullable=False)
    relation_key: Mapped[str] = mapped_column(String(180), nullable=False)
    source_hypothesis_id: Mapped[str] = mapped_column(ForeignKey("forensic_hypotheses.id", ondelete="CASCADE"), nullable=False)
    target_hypothesis_id: Mapped[str] = mapped_column(ForeignKey("forensic_hypotheses.id", ondelete="CASCADE"), nullable=False)
    relation_kind: Mapped[str] = mapped_column(String(80), nullable=False)
    rationale: Mapped[str | None] = mapped_column(Text, nullable=True)
    provenance_json: Mapped[dict] = mapped_column(JSON, default=dict)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class ForensicReasoningSnapshotRecord(Base):
    __tablename__ = "forensic_reasoning_snapshots"
    __table_args__ = (
        UniqueConstraint("investigation_id", "revision", name="uq_forensic_reasoning_snapshot_revision"),
        Index("ix_forensic_reasoning_snapshot_investigation", "investigation_id"),
        Index("ix_forensic_reasoning_snapshot_hash", "content_hash"),
    )
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    investigation_id: Mapped[str] = mapped_column(ForeignKey("forensic_investigations.id", ondelete="CASCADE"), nullable=False)
    revision: Mapped[int] = mapped_column(Integer, nullable=False)
    content_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    previous_snapshot_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    state_json: Mapped[dict] = mapped_column(JSON, nullable=False)
    provenance_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_by: Mapped[str] = mapped_column(String(255), nullable=False, default="operator")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
