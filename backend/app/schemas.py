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
