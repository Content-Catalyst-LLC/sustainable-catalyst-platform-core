from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, model_validator

from .ids import build_entity_id, validate_entity_id, validate_token


Visibility = Literal["public", "internal", "private"]
ValidationStatus = Literal["passed", "warning", "failed", "unknown"]
Severity = Literal["info", "low", "medium", "high", "critical"]


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
    def validate_tokens(self) -> "EntityBase":
        validate_token(self.entity_type, "entity_type")
        validate_token(self.slug, "slug")
        return self


class EntityCreate(EntityBase):
    id: str | None = None
    aliases: list[AliasCreate] = Field(default_factory=list)

    @model_validator(mode="after")
    def ensure_id_consistency(self) -> "EntityCreate":
        expected = build_entity_id(self.entity_type, self.slug)
        if self.id is None:
            self.id = expected
        else:
            id_type, id_slug = validate_entity_id(self.id)
            if id_type != self.entity_type or id_slug != self.slug:
                raise ValueError(
                    f"Entity ID must match entity_type and slug. Expected {expected}."
                )
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
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        validation_alias="metadata_json",
        serialization_alias="metadata",
    )
    aliases: list[AliasRead] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class EntityList(BaseModel):
    items: list[EntityRead]
    total: int
    limit: int
    offset: int


class RelationshipCreate(BaseModel):
    subject_id: str
    predicate: str = Field(min_length=1, max_length=100)
    object_id: str
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    status: str = Field(default="proposed", min_length=1, max_length=50)
    provenance: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_relationship(self) -> "RelationshipCreate":
        validate_entity_id(self.subject_id)
        validate_entity_id(self.object_id)
        if self.subject_id == self.object_id and self.predicate not in {
            "same_as",
            "version_of",
        }:
            raise ValueError("Self-relationships require same_as or version_of.")
        if not all(c.islower() or c.isdigit() or c in "_-" for c in self.predicate):
            raise ValueError(
                "predicate must contain lowercase letters, numbers, underscores, or hyphens."
            )
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
    direction: Literal["outbound", "inbound", "both"]
    max_depth: int
    nodes: list[GraphNode]
    edges: list[GraphEdge]


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
    evidence_foundations: int
    validation_events: int
    import_jobs: int
    entities_by_type: dict[str, int]
    relationships_by_predicate: dict[str, int]


class MetaResponse(BaseModel):
    name: str
    version: str
    environment: str
    public_reads: bool
    write_auth_configured: bool
    max_graph_depth: int
    capabilities: list[str]
    deferred_capabilities: list[str]
