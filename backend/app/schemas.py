from __future__ import annotations
from datetime import datetime
from typing import Any, Literal
from pydantic import BaseModel, ConfigDict, Field, HttpUrl, model_validator
from .ids import build_entity_id, validate_entity_id, validate_token

Visibility = Literal["public", "internal", "private"]
ValidationStatus = Literal["passed", "warning", "failed", "unknown"]
Severity = Literal["info", "low", "medium", "high", "critical"]
GraphDirection = Literal["outbound", "inbound", "both"]
ReviewDecision = Literal["approve", "reject", "needs_changes", "restore_proposed"]

class AliasCreate(BaseModel):
    namespace: str = Field(min_length=1, max_length=100)
    value: str = Field(min_length=1, max_length=1000)

class AliasRead(AliasCreate):
    id: int
    entity_id: str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class EntityBase(BaseModel):
    entity_type: str = Field(min_length=1, max_length=100)
    slug: str = Field(min_length=1, max_length=200)
    name: str = Field(min_length=1, max_length=300)
    description: str | None = None
    canonical_url: HttpUrl | None = None
    status: str = Field(default="active", min_length=1, max_length=50)
    visibility: Visibility = "public"
    schema_version: str = Field(default="1.0", min_length=1, max_length=20)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_tokens(self):
        validate_token(self.entity_type, "entity_type")
        validate_token(self.slug, "slug")
        return self

class EntityCreate(EntityBase):
    id: str | None = None
    aliases: list[AliasCreate] = Field(default_factory=list)

    @model_validator(mode="after")
    def ensure_id_consistency(self):
        expected = build_entity_id(self.entity_type, self.slug)
        if self.id is None:
            self.id = expected
        else:
            entity_type, slug = validate_entity_id(self.id)
            if entity_type != self.entity_type or slug != self.slug:
                raise ValueError(f"Entity ID must match entity_type and slug. Expected {expected}.")
        return self

class EntityUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=300)
    description: str | None = None
    canonical_url: HttpUrl | None = None
    status: str | None = Field(default=None, min_length=1, max_length=50)
    visibility: Visibility | None = None
    schema_version: str | None = Field(default=None, min_length=1, max_length=20)
    metadata: dict[str, Any] | None = None

class EntityRead(EntityBase):
    id: str
    metadata: dict[str, Any] = Field(default_factory=dict, validation_alias="metadata_json", serialization_alias="metadata")
    aliases: list[AliasRead] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)

class EntityList(BaseModel):
    items: list[EntityRead]
    total: int
    limit: int
    offset: int

class PredicateBase(BaseModel):
    id: str = Field(min_length=1, max_length=100)
    label: str = Field(min_length=1, max_length=150)
    description: str | None = None
    inverse_predicate: str | None = Field(default=None, max_length=100)
    symmetric: bool = False
    transitive: bool = False
    allowed_subject_types: list[str] = Field(default_factory=list)
    allowed_object_types: list[str] = Field(default_factory=list)
    status: str = Field(default="active", max_length=30)
    visibility: Visibility = "public"
    sort_order: int = Field(default=100, ge=0, le=10000)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_predicate(self):
        if not all(c.islower() or c.isdigit() or c in "_-" for c in self.id):
            raise ValueError("Predicate ID must use lowercase letters, numbers, underscores, or hyphens.")
        for entity_type in self.allowed_subject_types + self.allowed_object_types:
            validate_token(entity_type, "allowed entity type")
        return self

class PredicateCreate(PredicateBase):
    pass

class PredicateUpdate(BaseModel):
    label: str | None = Field(default=None, min_length=1, max_length=150)
    description: str | None = None
    inverse_predicate: str | None = Field(default=None, max_length=100)
    symmetric: bool | None = None
    transitive: bool | None = None
    allowed_subject_types: list[str] | None = None
    allowed_object_types: list[str] | None = None
    status: str | None = Field(default=None, max_length=30)
    visibility: Visibility | None = None
    sort_order: int | None = Field(default=None, ge=0, le=10000)
    metadata: dict[str, Any] | None = None

class PredicateRead(PredicateBase):
    metadata: dict[str, Any] = Field(default_factory=dict, validation_alias="metadata_json", serialization_alias="metadata")
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)

class PredicateList(BaseModel):
    items: list[PredicateRead]
    total: int

class RelationshipCreate(BaseModel):
    subject_id: str
    predicate: str = Field(min_length=1, max_length=100)
    object_id: str
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    status: str = Field(default="proposed", min_length=1, max_length=50)
    provenance: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_relationship(self):
        validate_entity_id(self.subject_id)
        validate_entity_id(self.object_id)
        if self.subject_id == self.object_id and self.predicate not in {"same_as", "version_of"}:
            raise ValueError("Self-relationships require same_as or version_of.")
        if not all(c.islower() or c.isdigit() or c in "_-" for c in self.predicate):
            raise ValueError("predicate must contain lowercase letters, numbers, underscores, or hyphens.")
        return self

class RelationshipRead(RelationshipCreate):
    id: str
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)

class RelationshipList(BaseModel):
    items: list[RelationshipRead]
    total: int
    limit: int
    offset: int

class RelationshipReviewCreate(BaseModel):
    decision: ReviewDecision
    reviewer: str = Field(min_length=1, max_length=200)
    note: str | None = Field(default=None, max_length=5000)
    metadata: dict[str, Any] = Field(default_factory=dict)

class RelationshipReviewRead(RelationshipReviewCreate):
    id: str
    relationship_id: str
    previous_status: str
    resulting_status: str
    metadata: dict[str, Any] = Field(default_factory=dict, validation_alias="metadata_json", serialization_alias="metadata")
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class EvidenceFoundationCreate(BaseModel):
    id: str | None = None
    evidence_type: str = Field(min_length=1, max_length=100)
    subject_entity_id: str | None = None
    source_entity_id: str | None = None
    methodology: str | None = None
    confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    review_status: str = Field(default="unreviewed", max_length=50)
    provenance: dict[str, Any] = Field(default_factory=dict)

class EvidenceFoundationRead(EvidenceFoundationCreate):
    id: str
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)

class ValidationEventCreate(BaseModel):
    entity_id: str | None = None
    component: str = Field(min_length=1, max_length=150)
    check_name: str = Field(min_length=1, max_length=200)
    status: ValidationStatus
    severity: Severity = "info"
    details: dict[str, Any] = Field(default_factory=dict)
    observed_at: datetime | None = None

class ValidationEventRead(ValidationEventCreate):
    id: str
    observed_at: datetime
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class GraphNode(BaseModel):
    entity: EntityRead
    depth: int

class GraphEdge(BaseModel):
    relationship: RelationshipRead
    depth: int

class GraphTraversal(BaseModel):
    root_id: str
    direction: GraphDirection
    max_depth: int
    nodes: list[GraphNode]
    edges: list[GraphEdge]

class GraphPath(BaseModel):
    node_ids: list[str]
    relationships: list[RelationshipRead]
    length: int
    score: float

class GraphPathResult(BaseModel):
    source_id: str
    target_id: str
    direction: GraphDirection
    max_depth: int
    paths: list[GraphPath]

class NeighborhoodGroup(BaseModel):
    direction: Literal["outbound", "inbound"]
    predicate: str
    predicate_label: str
    count: int
    entities: list[EntityRead]

class NeighborhoodResult(BaseModel):
    root: EntityRead
    groups: list[NeighborhoodGroup]
    total_relationships: int

class Recommendation(BaseModel):
    entity: EntityRead
    score: float
    relationship_count: int
    predicates: list[str]
    reasons: list[str]

class RecommendationResult(BaseModel):
    root_id: str
    items: list[Recommendation]

class SiteIntelligenceManifest(BaseModel):
    source_name: str = "site-intelligence"
    entities: list[EntityCreate] = Field(default_factory=list)
    relationships: list[RelationshipCreate] = Field(default_factory=list)

class ImportJobRead(BaseModel):
    id: str
    adapter: str
    status: str
    source_name: str | None
    entities_received: int
    entities_created: int
    entities_updated: int
    relationships_received: int
    relationships_created: int
    relationships_skipped: int
    error_message: str | None
    details: dict[str, Any]
    started_at: datetime
    completed_at: datetime | None
    model_config = ConfigDict(from_attributes=True)

class RegistryStats(BaseModel):
    entities: int
    relationships: int
    aliases: int
    predicate_definitions: int
    relationship_reviews: int
    claims: int
    source_snapshots: int
    evidence_records: int
    evidence_reviews: int
    review_assignments: int
    provenance_activities: int
    provenance_links: int
    calculation_traces: int
    ledger_entries: int
    evidence_foundations: int
    validation_events: int
    import_jobs: int
    evaluation_definitions: int
    evaluation_runs: int
    evaluation_check_results: int
    trust_findings: int
    trust_incidents: int
    known_limitations: int
    trust_attestations: int
    live_data_sources: int
    live_data_connectors: int
    live_data_ingestion_runs: int
    live_data_observations: int
    international_law_records: int
    scientific_data_records: int
    economic_data_records: int
    entities_by_type: dict[str, int]
    relationships_by_predicate: dict[str, int]
    relationships_by_status: dict[str, int]

class MetaResponse(BaseModel):
    name: str
    version: str
    environment: str
    public_reads: bool
    write_auth_configured: bool
    max_graph_depth: int
    explorer_enabled: bool
    capabilities: list[str]
    deferred_capabilities: list[str]


class ClaimCreate(BaseModel):
    id: str | None = None
    actor: str = Field(min_length=1, max_length=300)
    claim_text: str = Field(min_length=1, max_length=20000)
    claim_type: str = Field(default="factual", min_length=1, max_length=100)
    subject_entity_id: str | None = None
    status: str = Field(default="draft", min_length=1, max_length=50)
    visibility: Visibility = "public"
    language: str = Field(default="en", min_length=2, max_length=20)
    metadata: dict[str, Any] = Field(default_factory=dict)


class ClaimUpdate(BaseModel):
    claim_text: str | None = Field(default=None, min_length=1, max_length=20000)
    claim_type: str | None = Field(default=None, min_length=1, max_length=100)
    status: str | None = Field(default=None, min_length=1, max_length=50)
    visibility: Visibility | None = None
    language: str | None = Field(default=None, min_length=2, max_length=20)
    metadata: dict[str, Any] | None = None
    actor: str = Field(min_length=1, max_length=300)


class ClaimRead(BaseModel):
    id: str
    claim_text: str
    claim_type: str
    subject_entity_id: str | None
    status: str
    visibility: Visibility
    language: str
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        validation_alias="metadata_json",
        serialization_alias="metadata",
    )
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)


class ClaimList(BaseModel):
    items: list[ClaimRead]
    total: int
    limit: int
    offset: int


class SourceSnapshotCreate(BaseModel):
    id: str | None = None
    source_entity_id: str | None = None
    canonical_url: HttpUrl | None = None
    title: str | None = Field(default=None, max_length=500)
    publisher: str | None = Field(default=None, max_length=300)
    published_at: datetime | None = None
    retrieved_at: datetime | None = None
    media_type: str = Field(default="text/html", min_length=1, max_length=150)
    content: str | None = Field(default=None, max_length=5_000_000)
    content_hash: str | None = Field(default=None, pattern="^[a-f0-9]{64}$")
    storage_uri: str | None = Field(default=None, max_length=2000)
    archived_url: HttpUrl | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    actor: str = Field(min_length=1, max_length=300)

    @model_validator(mode="after")
    def require_content_or_hash(self):
        if self.content is None and self.content_hash is None:
            raise ValueError("Provide content or a lowercase SHA-256 content_hash.")
        return self


class SourceSnapshotRead(BaseModel):
    id: str
    source_entity_id: str | None
    canonical_url: str | None
    title: str | None
    publisher: str | None
    published_at: datetime | None
    retrieved_at: datetime
    media_type: str
    content_hash: str
    content_length: int | None
    content_excerpt: str | None
    storage_uri: str | None
    archived_url: str | None
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        validation_alias="metadata_json",
        serialization_alias="metadata",
    )
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class SnapshotVerificationRequest(BaseModel):
    content: str = Field(max_length=5_000_000)


class SnapshotVerificationResult(BaseModel):
    snapshot_id: str
    expected_hash: str
    observed_hash: str
    matches: bool
    observed_length: int


class ProvenanceActivityCreate(BaseModel):
    id: str | None = None
    activity_type: str = Field(min_length=1, max_length=100)
    name: str = Field(min_length=1, max_length=300)
    description: str | None = None
    agent: str = Field(min_length=1, max_length=300)
    software_entity_id: str | None = None
    started_at: datetime | None = None
    ended_at: datetime | None = None
    parameters: dict[str, Any] = Field(default_factory=dict)
    environment: dict[str, Any] = Field(default_factory=dict)
    status: str = Field(default="completed", max_length=50)
    metadata: dict[str, Any] = Field(default_factory=dict)


class ProvenanceActivityRead(BaseModel):
    id: str
    activity_type: str
    name: str
    description: str | None
    agent: str
    software_entity_id: str | None
    started_at: datetime
    ended_at: datetime | None
    parameters: dict[str, Any]
    environment: dict[str, Any]
    status: str
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        validation_alias="metadata_json",
        serialization_alias="metadata",
    )
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class ProvenanceLinkCreate(BaseModel):
    role: Literal["used", "generated", "derived_from", "informed_by", "was_associated_with"]
    object_type: str = Field(min_length=1, max_length=100)
    object_id: str = Field(min_length=1, max_length=255)
    metadata: dict[str, Any] = Field(default_factory=dict)
    actor: str = Field(min_length=1, max_length=300)


class ProvenanceLinkRead(BaseModel):
    id: str
    activity_id: str
    role: str
    object_type: str
    object_id: str
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        validation_alias="metadata_json",
        serialization_alias="metadata",
    )
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class CalculationTraceCreate(BaseModel):
    id: str | None = None
    tool_entity_id: str
    subject_entity_id: str | None = None
    activity_id: str | None = None
    run_id: str | None = Field(default=None, max_length=255)
    inputs: dict[str, Any] = Field(default_factory=dict)
    outputs: dict[str, Any] = Field(default_factory=dict)
    formula_version: str | None = Field(default=None, max_length=100)
    code_version: str | None = Field(default=None, max_length=100)
    runtime: dict[str, Any] = Field(default_factory=dict)
    status: str = Field(default="completed", max_length=50)
    metadata: dict[str, Any] = Field(default_factory=dict)
    actor: str = Field(min_length=1, max_length=300)


class CalculationTraceRead(BaseModel):
    id: str
    tool_entity_id: str
    subject_entity_id: str | None
    activity_id: str | None
    run_id: str | None
    inputs: dict[str, Any]
    outputs: dict[str, Any]
    formula_version: str | None
    code_version: str | None
    runtime: dict[str, Any]
    status: str
    content_hash: str
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        validation_alias="metadata_json",
        serialization_alias="metadata",
    )
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class EvidenceRecordCreate(BaseModel):
    id: str | None = None
    evidence_type: str = Field(min_length=1, max_length=100)
    stance: Literal["supports", "contradicts", "contextualizes", "neutral"] = "contextualizes"
    claim_id: str | None = None
    subject_entity_id: str | None = None
    source_entity_id: str | None = None
    source_snapshot_id: str | None = None
    relationship_id: str | None = None
    calculation_trace_id: str | None = None
    statement: str | None = Field(default=None, max_length=20000)
    methodology: str | None = Field(default=None, max_length=20000)
    confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    review_status: str = Field(default="unreviewed", max_length=50)
    provenance: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)
    actor: str = Field(min_length=1, max_length=300)

    @model_validator(mode="after")
    def require_evidence_anchor(self):
        anchors = [
            self.source_snapshot_id,
            self.source_entity_id,
            self.calculation_trace_id,
            self.relationship_id,
        ]
        if not any(anchors):
            raise ValueError(
                "Evidence must reference a source snapshot, source entity, "
                "calculation trace, or graph relationship."
            )
        return self


class EvidenceRecordRead(BaseModel):
    id: str
    evidence_type: str
    stance: str
    claim_id: str | None
    subject_entity_id: str | None
    source_entity_id: str | None
    source_snapshot_id: str | None
    relationship_id: str | None
    calculation_trace_id: str | None
    statement: str | None
    methodology: str | None
    confidence: float | None
    review_status: str
    provenance: dict[str, Any]
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        validation_alias="metadata_json",
        serialization_alias="metadata",
    )
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)


class EvidenceRecordList(BaseModel):
    items: list[EvidenceRecordRead]
    total: int
    limit: int
    offset: int


class EvidenceReviewCreate(BaseModel):
    decision: Literal["approve", "reject", "needs_changes", "restore_unreviewed"]
    reviewer: str = Field(min_length=1, max_length=200)
    note: str | None = Field(default=None, max_length=10000)
    metadata: dict[str, Any] = Field(default_factory=dict)


class EvidenceReviewRead(BaseModel):
    id: str
    evidence_id: str
    decision: str
    reviewer: str
    note: str | None
    previous_status: str
    resulting_status: str
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        validation_alias="metadata_json",
        serialization_alias="metadata",
    )
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class EvidenceAssignmentCreate(BaseModel):
    assignee: str = Field(min_length=1, max_length=200)
    assigned_by: str = Field(min_length=1, max_length=200)
    instructions: str | None = Field(default=None, max_length=10000)
    due_at: datetime | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class EvidenceAssignmentRead(BaseModel):
    id: str
    evidence_id: str
    assignee: str
    assigned_by: str
    instructions: str | None
    status: str
    due_at: datetime | None
    completed_at: datetime | None
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        validation_alias="metadata_json",
        serialization_alias="metadata",
    )
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class EvidenceAssignmentComplete(BaseModel):
    completed_by: str = Field(min_length=1, max_length=200)


class LedgerEntryRead(BaseModel):
    sequence: int
    id: str
    record_type: str
    record_id: str
    action: str
    actor: str
    payload_hash: str
    previous_entry_hash: str | None
    entry_hash: str
    payload: dict[str, Any] = Field(
        default_factory=dict,
        validation_alias="payload_json",
        serialization_alias="payload",
    )
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class LedgerVerificationResult(BaseModel):
    valid: bool
    entries_checked: int
    first_sequence: int | None
    last_sequence: int | None
    head_hash: str | None
    errors: list[str]


class EvidenceManifest(BaseModel):
    claim: ClaimRead
    evidence: list[EvidenceRecordRead]
    snapshots: list[SourceSnapshotRead]
    calculation_traces: list[CalculationTraceRead]
    provenance_activities: list[ProvenanceActivityRead]
    provenance_links: list[ProvenanceLinkRead]
    reviews: list[EvidenceReviewRead]
    assignments: list[EvidenceAssignmentRead]
    ledger_entries: list[LedgerEntryRead]
    manifest_hash: str
    generated_at: datetime


class EvidenceLedgerStats(BaseModel):
    claims: int
    source_snapshots: int
    evidence_records: int
    evidence_reviews: int
    review_assignments: int
    provenance_activities: int
    provenance_links: int
    calculation_traces: int
    ledger_entries: int
    ledger_head_hash: str | None
    evidence_by_status: dict[str, int]
    evidence_by_stance: dict[str, int]


class ApiPlanRead(BaseModel):
    id: str
    name: str
    description: str | None
    requests_per_minute: int
    requests_per_day: int
    max_page_size: int
    allowed_scopes: list[str]
    public: bool
    active: bool
    sort_order: int
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        validation_alias="metadata_json",
        serialization_alias="metadata",
    )
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DeveloperApplicationCreate(BaseModel):
    id: str | None = None
    name: str = Field(min_length=1, max_length=300)
    owner_name: str = Field(min_length=1, max_length=300)
    owner_email: str = Field(min_length=3, max_length=500)
    organization: str | None = Field(default=None, max_length=500)
    website_url: HttpUrl | None = None
    use_case: str = Field(min_length=20, max_length=20000)
    status: Literal["pending", "approved", "suspended", "rejected"] = "pending"
    plan_id: str = Field(default="free", min_length=1, max_length=100)
    metadata: dict[str, Any] = Field(default_factory=dict)
    actor: str = Field(min_length=1, max_length=300)


class DeveloperApplicationUpdate(BaseModel):
    status: Literal["pending", "approved", "suspended", "rejected"] | None = None
    plan_id: str | None = Field(default=None, min_length=1, max_length=100)
    name: str | None = Field(default=None, min_length=1, max_length=300)
    owner_name: str | None = Field(default=None, min_length=1, max_length=300)
    owner_email: str | None = Field(default=None, min_length=3, max_length=500)
    organization: str | None = Field(default=None, max_length=500)
    website_url: HttpUrl | None = None
    use_case: str | None = Field(default=None, min_length=20, max_length=20000)
    metadata: dict[str, Any] | None = None
    actor: str = Field(min_length=1, max_length=300)


class DeveloperApplicationRead(BaseModel):
    id: str
    name: str
    owner_name: str
    owner_email: str
    organization: str | None
    website_url: str | None
    use_case: str
    status: str
    plan_id: str
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        validation_alias="metadata_json",
        serialization_alias="metadata",
    )
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ApiCredentialIssue(BaseModel):
    label: str = Field(min_length=1, max_length=300)
    scopes: list[str] = Field(default_factory=list)
    expires_at: datetime | None = None
    created_by: str = Field(min_length=1, max_length=300)
    metadata: dict[str, Any] = Field(default_factory=dict)


class ApiCredentialRead(BaseModel):
    id: str
    application_id: str
    label: str
    key_prefix: str
    key_last_four: str
    scopes: list[str]
    status: str
    expires_at: datetime | None
    last_used_at: datetime | None
    created_by: str
    revoked_at: datetime | None
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        validation_alias="metadata_json",
        serialization_alias="metadata",
    )
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ApiCredentialIssued(BaseModel):
    credential: ApiCredentialRead
    api_key: str
    warning: str = (
        "This plaintext API key is returned once. Store it securely; "
        "Platform Core stores only its SHA-256 hash."
    )


class CredentialRevoke(BaseModel):
    revoked_by: str = Field(min_length=1, max_length=300)


class PublicApiIdentity(BaseModel):
    application_id: str
    application_name: str
    credential_id: str
    credential_label: str
    plan_id: str
    plan_name: str
    scopes: list[str]
    requests_per_minute: int
    requests_per_day: int
    max_page_size: int


class ApiUsageSummary(BaseModel):
    application_id: str
    credential_id: str | None
    window_start: datetime
    window_end: datetime
    requests: int
    successful_requests: int
    client_error_requests: int
    server_error_requests: int
    requests_by_path: dict[str, int]
    requests_by_status: dict[str, int]


class WebhookSubscriptionCreate(BaseModel):
    callback_url: HttpUrl
    event_types: list[str] = Field(min_length=1, max_length=100)
    description: str | None = Field(default=None, max_length=5000)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_event_types(self):
        cleaned = []
        for event_type in self.event_types:
            value = event_type.strip().lower()
            if not value:
                raise ValueError("Webhook event types cannot be empty.")
            if not all(char.islower() or char.isdigit() or char in "._-*" for char in value):
                raise ValueError(
                    "Webhook event types may contain lowercase letters, numbers, "
                    "periods, underscores, hyphens, and *."
                )
            cleaned.append(value)
        self.event_types = sorted(set(cleaned))
        return self


class WebhookSubscriptionRead(BaseModel):
    id: str
    application_id: str
    callback_url: str
    event_types: list[str]
    status: str
    description: str | None
    created_by_credential_id: str
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        validation_alias="metadata_json",
        serialization_alias="metadata",
    )
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class WebhookSubscriptionIssued(BaseModel):
    subscription: WebhookSubscriptionRead
    signing_secret: str
    warning: str = (
        "The signing secret is derived for this subscription and is returned "
        "when the subscription is created. Store it securely."
    )


class WebhookSubscriptionUpdate(BaseModel):
    event_types: list[str] | None = None
    status: Literal["active", "paused", "revoked"] | None = None
    description: str | None = Field(default=None, max_length=5000)
    metadata: dict[str, Any] | None = None


class WebhookEventCreate(BaseModel):
    event_type: str = Field(min_length=1, max_length=150)
    resource_type: str = Field(min_length=1, max_length=100)
    resource_id: str = Field(min_length=1, max_length=255)
    payload: dict[str, Any] = Field(default_factory=dict)
    actor: str = Field(min_length=1, max_length=300)


class WebhookEventRead(BaseModel):
    id: str
    event_type: str
    resource_type: str
    resource_id: str
    payload: dict[str, Any] = Field(
        default_factory=dict,
        validation_alias="payload_json",
        serialization_alias="payload",
    )
    status: str
    created_at: datetime
    processed_at: datetime | None

    model_config = ConfigDict(from_attributes=True)


class WebhookDeliveryRead(BaseModel):
    id: str
    subscription_id: str
    event_id: str
    status: str
    attempts: int
    http_status: int | None
    response_excerpt: str | None
    error_message: str | None
    signature: str | None
    attempted_at: datetime | None
    delivered_at: datetime | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class WebhookDispatchResult(BaseModel):
    events_processed: int
    deliveries_attempted: int
    deliveries_succeeded: int
    deliveries_failed: int


class PublicEnvelope(BaseModel):
    data: Any
    meta: dict[str, Any] = Field(default_factory=dict)


class DeveloperPlatformStats(BaseModel):
    plans: int
    applications: int
    active_credentials: int
    public_api_requests: int
    webhook_subscriptions: int
    webhook_events: int
    webhook_deliveries: int
    requests_by_status: dict[str, int]
    requests_by_path: dict[str, int]


class EvaluationDefinitionCreate(BaseModel):
    id: str = Field(pattern="^[a-z0-9][a-z0-9_-]{1,149}$")
    name: str = Field(min_length=1, max_length=300)
    domain: str = Field(min_length=1, max_length=150)
    description: str | None = None
    methodology: str = Field(min_length=1, max_length=30000)
    evaluator_kind: str = Field(min_length=1, max_length=150)
    target_type: str = Field(default="platform", max_length=100)
    thresholds: dict[str, Any] = Field(default_factory=dict)
    cadence: str | None = Field(default=None, max_length=100)
    severity_on_failure: Severity = "medium"
    public: bool = True
    active: bool = True
    version: str = Field(default="1.0", max_length=50)
    sort_order: int = 100
    metadata: dict[str, Any] = Field(default_factory=dict)
    actor: str = Field(min_length=1, max_length=300)


class EvaluationDefinitionUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=300)
    domain: str | None = Field(default=None, min_length=1, max_length=150)
    description: str | None = None
    methodology: str | None = Field(default=None, min_length=1, max_length=30000)
    evaluator_kind: str | None = Field(default=None, min_length=1, max_length=150)
    target_type: str | None = Field(default=None, max_length=100)
    thresholds: dict[str, Any] | None = None
    cadence: str | None = Field(default=None, max_length=100)
    severity_on_failure: Severity | None = None
    public: bool | None = None
    active: bool | None = None
    version: str | None = Field(default=None, max_length=50)
    sort_order: int | None = None
    metadata: dict[str, Any] | None = None
    actor: str = Field(min_length=1, max_length=300)


class EvaluationDefinitionRead(BaseModel):
    id: str
    name: str
    domain: str
    description: str | None
    methodology: str
    evaluator_kind: str
    target_type: str
    thresholds: dict[str, Any]
    cadence: str | None
    severity_on_failure: str
    public: bool
    active: bool
    version: str
    sort_order: int
    metadata: dict[str, Any] = Field(default_factory=dict, validation_alias="metadata_json", serialization_alias="metadata")
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)


class EvaluationRunCreate(BaseModel):
    target_entity_id: str | None = None
    triggered_by: str = Field(min_length=1, max_length=300)
    observations: dict[str, Any] = Field(default_factory=dict)
    environment: dict[str, Any] = Field(default_factory=dict)
    evidence_references: list[str] = Field(default_factory=list)
    public: bool | None = None


class EvaluationCheckRead(BaseModel):
    id: str
    run_id: str
    check_key: str
    name: str
    status: str
    score: float | None
    severity: str
    observed: dict[str, Any]
    expected: dict[str, Any]
    details: dict[str, Any]
    evidence_references: list[str]
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class EvaluationRunRead(BaseModel):
    id: str
    definition_id: str
    target_entity_id: str | None
    status: str
    score: float | None
    grade: str
    summary: str
    triggered_by: str
    evaluator_version: str
    observations: dict[str, Any]
    environment: dict[str, Any]
    evidence_references: list[str]
    content_hash: str
    public: bool
    started_at: datetime
    completed_at: datetime
    created_at: datetime
    checks: list[EvaluationCheckRead] = Field(default_factory=list)
    model_config = ConfigDict(from_attributes=True)


class EvaluationSuiteRequest(BaseModel):
    definition_ids: list[str] | None = None
    triggered_by: str = Field(min_length=1, max_length=300)
    target_entity_id: str | None = None
    contexts: dict[str, dict[str, Any]] = Field(default_factory=dict)
    environment: dict[str, Any] = Field(default_factory=dict)
    public: bool | None = None


class EvaluationSuiteResult(BaseModel):
    runs: list[EvaluationRunRead]
    total: int
    passed: int
    warnings: int
    failed: int
    not_applicable: int


class TrustFindingCreate(BaseModel):
    evaluation_run_id: str | None = None
    check_result_id: str | None = None
    target_entity_id: str | None = None
    finding_type: str = Field(default="manual", max_length=100)
    severity: Severity
    status: Literal["open", "accepted", "resolved", "dismissed"] = "open"
    title: str = Field(min_length=1, max_length=500)
    description: str = Field(min_length=1, max_length=30000)
    remediation: str | None = Field(default=None, max_length=30000)
    owner: str | None = Field(default=None, max_length=300)
    due_at: datetime | None = None
    public: bool = True
    metadata: dict[str, Any] = Field(default_factory=dict)
    actor: str = Field(min_length=1, max_length=300)


class TrustFindingUpdate(BaseModel):
    severity: Severity | None = None
    status: Literal["open", "accepted", "resolved", "dismissed"] | None = None
    title: str | None = Field(default=None, min_length=1, max_length=500)
    description: str | None = Field(default=None, min_length=1, max_length=30000)
    remediation: str | None = Field(default=None, max_length=30000)
    owner: str | None = Field(default=None, max_length=300)
    due_at: datetime | None = None
    public: bool | None = None
    metadata: dict[str, Any] | None = None
    actor: str = Field(min_length=1, max_length=300)


class TrustFindingRead(BaseModel):
    id: str
    evaluation_run_id: str | None
    check_result_id: str | None
    target_entity_id: str | None
    finding_type: str
    severity: str
    status: str
    title: str
    description: str
    remediation: str | None
    owner: str | None
    due_at: datetime | None
    resolved_at: datetime | None
    public: bool
    metadata: dict[str, Any] = Field(default_factory=dict, validation_alias="metadata_json", serialization_alias="metadata")
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)


class TrustIncidentCreate(BaseModel):
    title: str = Field(min_length=1, max_length=500)
    severity: Severity
    status: Literal["investigating", "identified", "monitoring", "resolved"] = "investigating"
    summary: str = Field(min_length=1, max_length=30000)
    impact: str | None = Field(default=None, max_length=30000)
    root_cause: str | None = Field(default=None, max_length=30000)
    remediation: str | None = Field(default=None, max_length=30000)
    affected_entity_ids: list[str] = Field(default_factory=list)
    started_at: datetime | None = None
    detected_at: datetime | None = None
    resolved_at: datetime | None = None
    public: bool = True
    metadata: dict[str, Any] = Field(default_factory=dict)
    actor: str = Field(min_length=1, max_length=300)


class TrustIncidentUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=500)
    severity: Severity | None = None
    status: Literal["investigating", "identified", "monitoring", "resolved"] | None = None
    summary: str | None = Field(default=None, min_length=1, max_length=30000)
    impact: str | None = Field(default=None, max_length=30000)
    root_cause: str | None = Field(default=None, max_length=30000)
    remediation: str | None = Field(default=None, max_length=30000)
    affected_entity_ids: list[str] | None = None
    resolved_at: datetime | None = None
    public: bool | None = None
    metadata: dict[str, Any] | None = None
    actor: str = Field(min_length=1, max_length=300)


class TrustIncidentRead(BaseModel):
    id: str
    title: str
    severity: str
    status: str
    summary: str
    impact: str | None
    root_cause: str | None
    remediation: str | None
    affected_entity_ids: list[str]
    started_at: datetime
    detected_at: datetime
    resolved_at: datetime | None
    public: bool
    metadata: dict[str, Any] = Field(default_factory=dict, validation_alias="metadata_json", serialization_alias="metadata")
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)


class KnownLimitationCreate(BaseModel):
    domain: str = Field(min_length=1, max_length=150)
    title: str = Field(min_length=1, max_length=500)
    description: str = Field(min_length=1, max_length=30000)
    impact: str | None = Field(default=None, max_length=30000)
    mitigation: str | None = Field(default=None, max_length=30000)
    status: Literal["active", "mitigated", "retired"] = "active"
    affected_entity_ids: list[str] = Field(default_factory=list)
    review_after: datetime | None = None
    public: bool = True
    metadata: dict[str, Any] = Field(default_factory=dict)
    actor: str = Field(min_length=1, max_length=300)


class KnownLimitationUpdate(BaseModel):
    domain: str | None = Field(default=None, min_length=1, max_length=150)
    title: str | None = Field(default=None, min_length=1, max_length=500)
    description: str | None = Field(default=None, min_length=1, max_length=30000)
    impact: str | None = Field(default=None, max_length=30000)
    mitigation: str | None = Field(default=None, max_length=30000)
    status: Literal["active", "mitigated", "retired"] | None = None
    affected_entity_ids: list[str] | None = None
    review_after: datetime | None = None
    public: bool | None = None
    metadata: dict[str, Any] | None = None
    actor: str = Field(min_length=1, max_length=300)


class KnownLimitationRead(BaseModel):
    id: str
    domain: str
    title: str
    description: str
    impact: str | None
    mitigation: str | None
    status: str
    affected_entity_ids: list[str]
    review_after: datetime | None
    public: bool
    metadata: dict[str, Any] = Field(default_factory=dict, validation_alias="metadata_json", serialization_alias="metadata")
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)


class TrustAttestationCreate(BaseModel):
    subject_entity_id: str | None = None
    statement: str = Field(min_length=1, max_length=30000)
    scope: str = Field(min_length=1, max_length=300)
    issuer: str = Field(min_length=1, max_length=300)
    evidence_references: list[str] = Field(default_factory=list)
    valid_from: datetime | None = None
    valid_until: datetime | None = None
    public: bool = True
    metadata: dict[str, Any] = Field(default_factory=dict)
    actor: str = Field(min_length=1, max_length=300)


class TrustAttestationRevoke(BaseModel):
    reason: str = Field(min_length=1, max_length=10000)
    revoked_by: str = Field(min_length=1, max_length=300)


class TrustAttestationRead(BaseModel):
    id: str
    subject_entity_id: str | None
    statement: str
    scope: str
    issuer: str
    status: str
    evidence_references: list[str]
    valid_from: datetime
    valid_until: datetime | None
    revoked_at: datetime | None
    revocation_reason: str | None
    content_hash: str
    public: bool
    metadata: dict[str, Any] = Field(default_factory=dict, validation_alias="metadata_json", serialization_alias="metadata")
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class TrustDomainStatus(BaseModel):
    domain: str
    status: str
    score: float | None
    grade: str
    latest_run_id: str | None
    latest_completed_at: datetime | None
    evaluation_count: int
    open_findings: int
    summary: str


class TrustStatusResponse(BaseModel):
    service: str
    platform_version: str
    overall_status: str
    overall_score: float | None
    grade: str
    generated_at: datetime
    ledger_valid: bool
    last_evaluated_at: datetime | None
    domains: list[TrustDomainStatus]
    active_incidents: list[TrustIncidentRead]
    known_limitations: list[KnownLimitationRead]
    active_attestations: list[TrustAttestationRead]
    open_findings: int
    public_evaluation_runs: int
    methodology: str

WorkflowStepStatus = Literal["pending", "in_progress", "blocked", "completed", "skipped", "failed"]
WorkflowRunStatus = Literal["draft", "in_progress", "blocked", "completed", "cancelled"]
DossierVisibility = Literal["public", "internal", "private"]
DossierDecision = Literal["approve", "reject", "request_changes"]


class WorkflowDefinitionRead(BaseModel):
    id: str
    name: str
    description: str | None
    version: str
    stages: list[dict[str, Any]]
    public: bool
    active: bool
    sort_order: int
    metadata: dict[str, Any] = Field(default_factory=dict, validation_alias="metadata_json", serialization_alias="metadata")
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)


class WorkflowRunCreate(BaseModel):
    definition_id: str
    title: str = Field(min_length=1, max_length=500)
    subject_entity_id: str | None = None
    requested_by: str = Field(min_length=1, max_length=300)
    owner: str | None = Field(default=None, max_length=300)
    context: dict[str, Any] = Field(default_factory=dict)
    public: bool = False
    metadata: dict[str, Any] = Field(default_factory=dict)


class WorkflowStepRead(BaseModel):
    id: str
    run_id: str
    step_key: str
    name: str
    sequence: int
    product: str
    action: str
    required: bool
    status: str
    assigned_to: str | None
    input_references: list[str]
    output_references: list[str]
    notes: str | None
    due_at: datetime | None
    started_at: datetime | None
    completed_at: datetime | None
    metadata: dict[str, Any] = Field(default_factory=dict, validation_alias="metadata_json", serialization_alias="metadata")
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)


class WorkflowTransitionRead(BaseModel):
    id: str
    run_id: str
    step_id: str | None
    from_status: str | None
    to_status: str
    actor: str
    reason: str | None
    payload: dict[str, Any] = Field(default_factory=dict, validation_alias="payload_json", serialization_alias="payload")
    content_hash: str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class WorkflowRunRead(BaseModel):
    id: str
    definition_id: str
    title: str
    subject_entity_id: str | None
    status: str
    current_step_key: str | None
    requested_by: str
    owner: str | None
    context: dict[str, Any] = Field(default_factory=dict, validation_alias="context_json", serialization_alias="context")
    content_hash: str | None
    public: bool
    metadata: dict[str, Any] = Field(default_factory=dict, validation_alias="metadata_json", serialization_alias="metadata")
    started_at: datetime | None
    completed_at: datetime | None
    created_at: datetime
    updated_at: datetime
    steps: list[WorkflowStepRead] = Field(default_factory=list)
    transitions: list[WorkflowTransitionRead] = Field(default_factory=list)
    model_config = ConfigDict(from_attributes=True)


class WorkflowStartRequest(BaseModel):
    actor: str = Field(min_length=1, max_length=300)
    reason: str | None = Field(default=None, max_length=10000)


class WorkflowStepTransition(BaseModel):
    status: WorkflowStepStatus
    actor: str = Field(min_length=1, max_length=300)
    reason: str | None = Field(default=None, max_length=10000)
    assigned_to: str | None = Field(default=None, max_length=300)
    input_references: list[str] | None = None
    output_references: list[str] | None = None
    notes: str | None = Field(default=None, max_length=30000)
    payload: dict[str, Any] = Field(default_factory=dict)


class WorkflowCancelRequest(BaseModel):
    actor: str = Field(min_length=1, max_length=300)
    reason: str = Field(min_length=1, max_length=10000)


class DossierCreate(BaseModel):
    workflow_run_id: str | None = None
    subject_entity_id: str | None = None
    title: str = Field(min_length=1, max_length=500)
    purpose: str = Field(min_length=1, max_length=30000)
    version: str = Field(default="1.0", max_length=50)
    visibility: DossierVisibility = "private"
    supersedes_dossier_id: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    actor: str = Field(min_length=1, max_length=300)


class DossierRecordCreate(BaseModel):
    section: str = Field(min_length=1, max_length=150)
    record_type: str = Field(min_length=1, max_length=100)
    record_id: str = Field(min_length=1, max_length=255)
    label: str | None = Field(default=None, max_length=500)
    sort_order: int = Field(default=100, ge=0, le=100000)
    public: bool = True
    metadata: dict[str, Any] = Field(default_factory=dict)
    actor: str = Field(min_length=1, max_length=300)


class DossierRecordRead(BaseModel):
    id: str
    dossier_id: str
    section: str
    record_type: str
    record_id: str
    label: str | None
    sort_order: int
    snapshot_hash: str
    snapshot: dict[str, Any] = Field(default_factory=dict, validation_alias="snapshot_json", serialization_alias="snapshot")
    public: bool
    metadata: dict[str, Any] = Field(default_factory=dict, validation_alias="metadata_json", serialization_alias="metadata")
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class DossierApprovalCreate(BaseModel):
    decision: DossierDecision
    signer: str = Field(min_length=1, max_length=300)
    role: str = Field(min_length=1, max_length=200)
    statement: str | None = Field(default=None, max_length=30000)
    evidence_references: list[str] = Field(default_factory=list)


class DossierApprovalRead(BaseModel):
    id: str
    dossier_id: str
    decision: str
    signer: str
    role: str
    statement: str | None
    evidence_references: list[str]
    content_hash: str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class DossierFinalizeRequest(BaseModel):
    signed_by: str = Field(min_length=1, max_length=300)
    actor: str = Field(min_length=1, max_length=300)


class DossierRead(BaseModel):
    id: str
    workflow_run_id: str | None
    subject_entity_id: str | None
    title: str
    purpose: str
    version: str
    status: str
    visibility: str
    dossier_hash: str | None
    signature_algorithm: str | None
    platform_signature: str | None
    signing_key_id: str | None
    signed_by: str | None
    signed_at: datetime | None
    supersedes_dossier_id: str | None
    metadata: dict[str, Any] = Field(default_factory=dict, validation_alias="metadata_json", serialization_alias="metadata")
    created_at: datetime
    updated_at: datetime
    records: list[DossierRecordRead] = Field(default_factory=list)
    approvals: list[DossierApprovalRead] = Field(default_factory=list)
    workflow: WorkflowRunRead | None = None
    model_config = ConfigDict(from_attributes=True)


class DossierVerificationResult(BaseModel):
    dossier_id: str
    valid: bool
    finalized: bool
    hash_matches: bool
    signature_matches: bool
    record_snapshots_match: bool
    expected_hash: str | None
    observed_hash: str | None
    signing_key_id: str | None
    errors: list[str]


class DossierList(BaseModel):
    items: list[DossierRead]
    total: int
    limit: int
    offset: int


class WorkflowPlatformStats(BaseModel):
    workflow_definitions: int
    workflow_runs: int
    active_workflows: int
    completed_workflows: int
    workflow_steps: int
    workflow_transitions: int
    dossiers: int
    finalized_dossiers: int
    approvals: int


# Platform Core v2.7.0 — Free Live Data Gateway
LiveDataReviewStatus = Literal[
    "APPROVED_FREE",
    "APPROVED_WITH_ATTRIBUTION",
    "APPROVED_METADATA_ONLY",
    "APPROVED_SELF_HOSTED",
    "RESEARCH_ONLY",
    "LICENSE_REVIEW_REQUIRED",
    "EXCLUDED_PAID",
    "EXCLUDED_RESTRICTED",
    "DEPRECATED",
    "UNAVAILABLE",
]


class LiveDataSourceCreate(BaseModel):
    id: str = Field(pattern=r"^[a-z0-9][a-z0-9.-]{1,149}$")
    name: str = Field(min_length=1, max_length=300)
    organization: str = Field(min_length=1, max_length=300)
    description: str | None = Field(default=None, max_length=20000)
    homepage_url: HttpUrl | None = None
    documentation_url: HttpUrl | None = None
    license_name: str | None = Field(default=None, max_length=300)
    license_url: HttpUrl | None = None
    attribution: str | None = Field(default=None, max_length=10000)
    access_cost: Literal["free", "paid", "mixed", "unknown"] = "free"
    credit_card_required: bool = False
    api_key_requirement: str = Field(default="none", max_length=100)
    commercial_use_status: str = Field(default="review_required", max_length=100)
    redistribution_status: str = Field(default="review_required", max_length=100)
    automated_access_status: str = Field(default="allowed", max_length=100)
    rate_limit_summary: str | None = Field(default=None, max_length=10000)
    review_status: LiveDataReviewStatus = "LICENSE_REVIEW_REQUIRED"
    last_reviewed_at: datetime | None = None
    active: bool = True
    public: bool = True
    metadata: dict[str, Any] = Field(default_factory=dict)


class LiveDataSourceUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=300)
    organization: str | None = Field(default=None, min_length=1, max_length=300)
    description: str | None = Field(default=None, max_length=20000)
    homepage_url: HttpUrl | None = None
    documentation_url: HttpUrl | None = None
    license_name: str | None = Field(default=None, max_length=300)
    license_url: HttpUrl | None = None
    attribution: str | None = Field(default=None, max_length=10000)
    access_cost: Literal["free", "paid", "mixed", "unknown"] | None = None
    credit_card_required: bool | None = None
    api_key_requirement: str | None = Field(default=None, max_length=100)
    commercial_use_status: str | None = Field(default=None, max_length=100)
    redistribution_status: str | None = Field(default=None, max_length=100)
    automated_access_status: str | None = Field(default=None, max_length=100)
    rate_limit_summary: str | None = Field(default=None, max_length=10000)
    review_status: LiveDataReviewStatus | None = None
    last_reviewed_at: datetime | None = None
    active: bool | None = None
    public: bool | None = None
    metadata: dict[str, Any] | None = None


class LiveDataSourceRead(BaseModel):
    id: str
    name: str
    organization: str
    description: str | None
    homepage_url: str | None
    documentation_url: str | None
    license_name: str | None
    license_url: str | None
    attribution: str | None
    access_cost: str
    credit_card_required: bool
    api_key_requirement: str
    commercial_use_status: str
    redistribution_status: str
    automated_access_status: str
    rate_limit_summary: str | None
    review_status: str
    last_reviewed_at: datetime | None
    active: bool
    public: bool
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        validation_alias="metadata_json",
        serialization_alias="metadata",
    )
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)


class LiveDataConnectorCreate(BaseModel):
    id: str = Field(pattern=r"^[a-z0-9][a-z0-9._-]{1,179}$")
    source_id: str = Field(min_length=2, max_length=150)
    name: str = Field(min_length=1, max_length=300)
    domain: str = Field(pattern=r"^[a-z0-9][a-z0-9_-]{1,99}$")
    description: str | None = Field(default=None, max_length=20000)
    adapter: str = Field(min_length=1, max_length=180)
    base_url: HttpUrl
    refresh_policy: str = Field(default="manual", max_length=100)
    freshness_window_seconds: int = Field(default=86400, ge=60, le=31536000)
    timeout_seconds: int = Field(default=20, ge=1, le=120)
    max_response_bytes: int = Field(default=5242880, ge=1024, le=52428800)
    schema_version: str = Field(default="1.0", max_length=30)
    capabilities: list[str] = Field(default_factory=list)
    configuration: dict[str, Any] = Field(default_factory=dict)
    enabled: bool = True
    public: bool = True
    status: Literal["active", "paused", "deprecated", "disabled"] = "active"


class LiveDataConnectorUpdate(BaseModel):
    source_id: str | None = Field(default=None, min_length=2, max_length=150)
    name: str | None = Field(default=None, min_length=1, max_length=300)
    domain: str | None = Field(default=None, pattern=r"^[a-z0-9][a-z0-9_-]{1,99}$")
    description: str | None = Field(default=None, max_length=20000)
    adapter: str | None = Field(default=None, min_length=1, max_length=180)
    base_url: HttpUrl | None = None
    refresh_policy: str | None = Field(default=None, max_length=100)
    freshness_window_seconds: int | None = Field(default=None, ge=60, le=31536000)
    timeout_seconds: int | None = Field(default=None, ge=1, le=120)
    max_response_bytes: int | None = Field(default=None, ge=1024, le=52428800)
    schema_version: str | None = Field(default=None, max_length=30)
    capabilities: list[str] | None = None
    configuration: dict[str, Any] | None = None
    enabled: bool | None = None
    public: bool | None = None
    status: Literal["active", "paused", "deprecated", "disabled"] | None = None


class LiveDataConnectorRead(BaseModel):
    id: str
    source_id: str
    name: str
    domain: str
    description: str | None
    adapter: str
    base_url: str
    refresh_policy: str
    freshness_window_seconds: int
    timeout_seconds: int
    max_response_bytes: int
    schema_version: str
    capabilities: list[str]
    configuration: dict[str, Any] = Field(
        default_factory=dict,
        validation_alias="configuration_json",
        serialization_alias="configuration",
    )
    enabled: bool
    public: bool
    status: str
    last_health_status: str
    last_health_checked_at: datetime | None
    last_success_at: datetime | None
    last_failure_at: datetime | None
    last_error: str | None
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)


class LiveDataConnectorPublicRead(BaseModel):
    id: str
    source_id: str
    name: str
    domain: str
    description: str | None
    refresh_policy: str
    freshness_window_seconds: int
    schema_version: str
    capabilities: list[str]
    enabled: bool
    status: str
    last_health_status: str
    last_health_checked_at: datetime | None
    last_success_at: datetime | None
    model_config = ConfigDict(from_attributes=True)


class LiveDataIngestRequest(BaseModel):
    parameters: dict[str, Any] = Field(default_factory=dict)
    requested_by: str = Field(default="platform-core", min_length=1, max_length=300)
    run_type: Literal["manual", "scheduled", "replay", "validation"] = "manual"


class LiveDataIngestionRunRead(BaseModel):
    id: str
    connector_id: str
    run_type: str
    status: str
    requested_by: str
    parameters: dict[str, Any] = Field(
        default_factory=dict,
        validation_alias="parameters_json",
        serialization_alias="parameters",
    )
    http_status: int | None
    records_received: int
    records_created: int
    records_updated: int
    records_rejected: int
    raw_content_hash: str | None
    error_message: str | None
    details: dict[str, Any] = Field(
        default_factory=dict,
        validation_alias="details_json",
        serialization_alias="details",
    )
    started_at: datetime
    completed_at: datetime | None
    model_config = ConfigDict(from_attributes=True)


class LiveDataObservationRead(BaseModel):
    id: str
    connector_id: str
    source_id: str
    raw_record_id: str | None
    source_record_id: str
    domain: str
    metric: str
    value_number: float | None
    value_text: str | None
    unit: str | None
    geometry: dict[str, Any] | None = Field(
        default=None,
        validation_alias="geometry_json",
        serialization_alias="geometry",
    )
    dimensions: dict[str, Any] = Field(
        default_factory=dict,
        validation_alias="dimensions_json",
        serialization_alias="dimensions",
    )
    observed_at: datetime
    published_at: datetime | None
    retrieved_at: datetime
    freshness_status: str
    quality_status: str
    license_name: str | None
    attribution: str | None
    methodology_url: str | None
    raw_record_hash: str | None
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        validation_alias="metadata_json",
        serialization_alias="metadata",
    )
    public: bool
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)


class LiveDataStats(BaseModel):
    sources: int
    connectors: int
    ingestion_runs: int
    raw_records: int
    observations: int
    connectors_by_domain: dict[str, int]
    observations_by_freshness: dict[str, int]


class LiveDataHealthConnector(BaseModel):
    id: str
    source_id: str
    domain: str
    status: str
    configuration_status: str
    last_health_status: str
    last_health_checked_at: datetime | None
    last_success_at: datetime | None
    last_failure_at: datetime | None
    last_error: str | None


class LiveDataHealthSnapshot(BaseModel):
    enabled: bool
    ingest_enabled: bool
    strict_free_sources: bool
    overall_status: str
    source_count: int
    connector_count: int
    operational_connectors: int
    connectors: list[LiveDataHealthConnector]
    generated_at: datetime

InternationalLawRecordType = Literal[
    "treaty", "treaty_action", "reservation", "declaration", "judgment", "advisory_opinion",
    "procedural_order", "security_council_resolution", "general_assembly_resolution",
    "human_rights_council_resolution", "human_rights_recommendation", "ilc_draft_text",
    "un_official_document", "humanitarian_report", "statistical_observation", "commentary"
]


class InternationalLawRecordRead(BaseModel):
    id: str
    connector_id: str
    source_id: str
    raw_record_id: str | None
    source_record_id: str
    record_type: str
    authority_level: str
    title: str
    official_symbol: str | None
    issuing_body: str | None
    legal_body: str | None
    jurisdiction: str
    legal_status: str
    adoption_date: datetime | None
    publication_date: datetime | None
    entry_into_force_date: datetime | None
    languages: list[str] = Field(default_factory=list, validation_alias="languages_json", serialization_alias="languages")
    countries: list[str] = Field(default_factory=list, validation_alias="countries_json", serialization_alias="countries")
    subjects: list[str] = Field(default_factory=list, validation_alias="subjects_json", serialization_alias="subjects")
    related_instruments: list[str] = Field(default_factory=list, validation_alias="related_instruments_json", serialization_alias="related_instruments")
    related_cases: list[str] = Field(default_factory=list, validation_alias="related_cases_json", serialization_alias="related_cases")
    related_resolutions: list[str] = Field(default_factory=list, validation_alias="related_resolutions_json", serialization_alias="related_resolutions")
    related_sdg_targets: list[str] = Field(default_factory=list, validation_alias="related_sdg_targets_json", serialization_alias="related_sdg_targets")
    canonical_source_url: str | None
    citation: str | None
    summary: str | None
    license_name: str | None
    attribution: str | None
    content_hash: str
    metadata: dict[str, Any] = Field(default_factory=dict, validation_alias="metadata_json", serialization_alias="metadata")
    public: bool
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)


class InternationalLawStats(BaseModel):
    records: int
    by_record_type: dict[str, int]
    by_authority_level: dict[str, int]
    by_legal_body: dict[str, int]
    public_records: int



class ScientificDataRecordRead(BaseModel):
    id: str
    connector_id: str
    source_id: str
    raw_record_id: str | None
    source_record_id: str
    record_type: str
    discipline: str
    title: str
    summary: str | None
    dataset_id: str | None
    collection: str | None
    mission: str | None
    instrument: str | None
    target: str | None
    doi: str | None
    access_url: str | None
    landing_page_url: str | None
    geometry: dict[str, Any] | None = Field(default=None, validation_alias="geometry_json", serialization_alias="geometry")
    observation_start: datetime | None
    observation_end: datetime | None
    published_at: datetime | None
    identifiers: dict[str, Any] = Field(default_factory=dict, validation_alias="identifiers_json", serialization_alias="identifiers")
    keywords: list[str] = Field(default_factory=list, validation_alias="keywords_json", serialization_alias="keywords")
    variables: list[str] = Field(default_factory=list, validation_alias="variables_json", serialization_alias="variables")
    file_formats: list[str] = Field(default_factory=list, validation_alias="file_formats_json", serialization_alias="file_formats")
    quality_status: str
    license_name: str | None
    attribution: str | None
    content_hash: str
    metadata: dict[str, Any] = Field(default_factory=dict, validation_alias="metadata_json", serialization_alias="metadata")
    public: bool
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)


class ScientificDataStats(BaseModel):
    records: int
    public_records: int
    by_record_type: dict[str, int]
    by_discipline: dict[str, int]
    by_source: dict[str, int]
    by_mission: dict[str, int]


class EconomicDataRecordRead(BaseModel):
    id: str
    connector_id: str
    source_id: str
    raw_record_id: str | None
    source_record_id: str
    record_type: str
    subject: str
    indicator_code: str | None
    indicator_name: str | None
    dataset_id: str | None
    geography_code: str | None
    geography_name: str | None
    counterpart_code: str | None
    period: str | None
    period_start: datetime | None
    period_end: datetime | None
    frequency: str | None
    value_number: float | None
    value_text: str | None
    unit: str | None
    multiplier: str | None
    seasonal_adjustment: str | None
    price_basis: str | None
    status: str
    release_name: str | None
    vintage_date: datetime | None
    published_at: datetime | None
    dimensions: dict[str, Any] = Field(default_factory=dict, validation_alias="dimensions_json", serialization_alias="dimensions")
    notes: str | None
    source_url: str | None
    license_name: str | None
    attribution: str | None
    content_hash: str
    metadata: dict[str, Any] = Field(default_factory=dict, validation_alias="metadata_json", serialization_alias="metadata")
    public: bool
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)


class EconomicDataStats(BaseModel):
    records: int
    public_records: int
    by_record_type: dict[str, int]
    by_subject: dict[str, int]
    by_source: dict[str, int]
    by_frequency: dict[str, int]
