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
