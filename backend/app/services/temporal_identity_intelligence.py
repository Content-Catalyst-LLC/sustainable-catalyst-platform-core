from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field, model_validator

from .computational_runtime_objects import canonical_sha256
from .entity_resolution_identity_graph import (
    EntityResolutionIdentityGraphBundle,
    reference_entity_resolution_identity_graph_bundle,
)

CORE_RELEASE = "3.78.0"
CONTRACT_VERSION = "sc.core.temporal-identity-alias-name-variant-intelligence.v1"


def _unique(values: list[str], label: str) -> None:
    if len(values) != len(set(values)):
        raise ValueError(f"{label} must be unique")


def _parse_time(value: str | None) -> datetime | None:
    if value is None:
        return None
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def _check_interval(start: str | None, end: str | None, label: str) -> None:
    s, e = _parse_time(start), _parse_time(end)
    if s and e and e < s:
        raise ValueError(f"{label} valid_to must not precede valid_from")


class TemporalAssertionState(str, Enum):
    asserted = "asserted"
    corroborated = "corroborated"
    disputed = "disputed"
    superseded = "superseded"
    withdrawn = "withdrawn"


class TemporalNameKind(str, Enum):
    canonical = "canonical"
    legal = "legal"
    preferred = "preferred"
    former = "former"
    historical = "historical"
    abbreviation = "abbreviation"
    transliteration = "transliteration"
    translation = "translation"
    source_supplied = "source-supplied"
    other = "other"


class TemporalRoleKind(str, Enum):
    organizational_role = "organizational-role"
    public_title = "public-title"
    employment_title = "employment-title"
    membership = "membership"
    office = "office"
    affiliation = "affiliation"
    other = "other"


class TemporalConflictKind(str, Enum):
    overlapping_names = "overlapping-names"
    overlapping_identifiers = "overlapping-identifiers"
    conflicting_roles = "conflicting-roles"
    chronology_gap = "chronology-gap"
    source_disagreement = "source-disagreement"
    supersession_conflict = "supersession-conflict"
    other = "other"


class TemporalNameVariant(BaseModel):
    temporal_name_id: str = Field(min_length=2, max_length=500)
    entity_ref: str = Field(min_length=2, max_length=1000)
    value: str = Field(min_length=1, max_length=2000)
    name_kind: TemporalNameKind
    language_tag: str | None = Field(default=None, max_length=80)
    script_code: str | None = Field(default=None, max_length=80)
    valid_from: str | None = Field(default=None, max_length=80)
    valid_to: str | None = Field(default=None, max_length=80)
    source_refs: list[str] = Field(min_length=1)
    provenance_refs: list[str] = Field(min_length=1)
    state: TemporalAssertionState = TemporalAssertionState.asserted
    superseded_by_name_ref: str | None = Field(default=None, max_length=500)
    same_name_across_time_is_not_identity_proof: Literal[True] = True
    historical_name_is_not_current_name_fact: Literal[True] = True
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_record(self):
        _check_interval(self.valid_from, self.valid_to, "temporal name")
        _unique(self.source_refs, "source_refs")
        _unique(self.provenance_refs, "provenance_refs")
        if self.state == TemporalAssertionState.superseded and not self.superseded_by_name_ref:
            raise ValueError("superseded temporal name requires superseded_by_name_ref")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class TemporalIdentifierAssertion(BaseModel):
    temporal_identifier_id: str = Field(min_length=2, max_length=500)
    entity_ref: str = Field(min_length=2, max_length=1000)
    namespace: str = Field(min_length=1, max_length=300)
    identifier_value: str = Field(min_length=1, max_length=1000)
    valid_from: str | None = Field(default=None, max_length=80)
    valid_to: str | None = Field(default=None, max_length=80)
    source_refs: list[str] = Field(min_length=1)
    provenance_refs: list[str] = Field(min_length=1)
    state: TemporalAssertionState = TemporalAssertionState.asserted
    superseded_by_identifier_ref: str | None = Field(default=None, max_length=500)
    identifier_reuse_is_not_identity_proof: Literal[True] = True
    expired_identifier_is_not_current_identifier_fact: Literal[True] = True
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_record(self):
        _check_interval(self.valid_from, self.valid_to, "temporal identifier")
        _unique(self.source_refs, "source_refs")
        _unique(self.provenance_refs, "provenance_refs")
        if self.state == TemporalAssertionState.superseded and not self.superseded_by_identifier_ref:
            raise ValueError("superseded temporal identifier requires superseded_by_identifier_ref")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class TemporalRoleTitleAssertion(BaseModel):
    temporal_role_id: str = Field(min_length=2, max_length=500)
    entity_ref: str = Field(min_length=2, max_length=1000)
    role_kind: TemporalRoleKind
    title: str = Field(min_length=1, max_length=2000)
    organization_or_context_ref: str | None = Field(default=None, max_length=1000)
    valid_from: str | None = Field(default=None, max_length=80)
    valid_to: str | None = Field(default=None, max_length=80)
    source_refs: list[str] = Field(min_length=1)
    provenance_refs: list[str] = Field(min_length=1)
    state: TemporalAssertionState = TemporalAssertionState.asserted
    role_at_one_time_is_not_timeless_affiliation: Literal[True] = True
    title_does_not_establish_current_authority: Literal[True] = True
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_record(self):
        _check_interval(self.valid_from, self.valid_to, "temporal role")
        _unique(self.source_refs, "source_refs")
        _unique(self.provenance_refs, "provenance_refs")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class TemporalSourceIdentityAssertion(BaseModel):
    temporal_source_assertion_id: str = Field(min_length=2, max_length=500)
    entity_ref: str = Field(min_length=2, max_length=1000)
    source_ref: str = Field(min_length=2, max_length=1000)
    source_entity_key: str = Field(min_length=1, max_length=1000)
    asserted_name: str = Field(min_length=1, max_length=2000)
    observed_at: str | None = Field(default=None, max_length=80)
    valid_from: str | None = Field(default=None, max_length=80)
    valid_to: str | None = Field(default=None, max_length=80)
    temporal_name_refs: list[str] = Field(default_factory=list)
    temporal_identifier_refs: list[str] = Field(default_factory=list)
    temporal_role_refs: list[str] = Field(default_factory=list)
    provenance_refs: list[str] = Field(min_length=1)
    source_temporal_assertion_is_not_canonical_identity: Literal[True] = True
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_record(self):
        _check_interval(self.valid_from, self.valid_to, "temporal source assertion")
        for values, label in (
            (self.temporal_name_refs, "temporal_name_refs"),
            (self.temporal_identifier_refs, "temporal_identifier_refs"),
            (self.temporal_role_refs, "temporal_role_refs"),
            (self.provenance_refs, "provenance_refs"),
        ):
            _unique(values, label)
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class TemporalIdentityConflict(BaseModel):
    temporal_conflict_id: str = Field(min_length=2, max_length=500)
    entity_ref: str = Field(min_length=2, max_length=1000)
    conflict_kind: TemporalConflictKind
    assertion_refs: list[str] = Field(min_length=2)
    source_refs: list[str] = Field(min_length=1)
    provenance_refs: list[str] = Field(min_length=1)
    review_required: Literal[True] = True
    conflict_does_not_auto_resolve: Literal[True] = True
    conflicting_temporal_assertions_may_coexist: Literal[True] = True
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_record(self):
        _unique(self.assertion_refs, "assertion_refs")
        _unique(self.source_refs, "source_refs")
        _unique(self.provenance_refs, "provenance_refs")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class TemporalIdentitySnapshot(BaseModel):
    temporal_snapshot_id: str = Field(min_length=2, max_length=500)
    identity_graph_snapshot_ref: str = Field(min_length=2, max_length=500)
    as_of: str = Field(min_length=10, max_length=80)
    entity_refs: list[str] = Field(min_length=1)
    active_temporal_name_refs: list[str] = Field(default_factory=list)
    active_temporal_identifier_refs: list[str] = Field(default_factory=list)
    active_temporal_role_refs: list[str] = Field(default_factory=list)
    unresolved_conflict_refs: list[str] = Field(default_factory=list)
    immutable_snapshot: Literal[True] = True
    as_of_view_does_not_rewrite_historical_assertions: Literal[True] = True
    temporal_selection_is_not_identity_resolution: Literal[True] = True
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_record(self):
        _parse_time(self.as_of)
        for values, label in (
            (self.entity_refs, "entity_refs"),
            (self.active_temporal_name_refs, "active_temporal_name_refs"),
            (self.active_temporal_identifier_refs, "active_temporal_identifier_refs"),
            (self.active_temporal_role_refs, "active_temporal_role_refs"),
            (self.unresolved_conflict_refs, "unresolved_conflict_refs"),
        ):
            _unique(values, label)
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class TemporalIdentityIntelligenceBundle(BaseModel):
    entity_resolution_identity_graph_bundle: EntityResolutionIdentityGraphBundle
    temporal_names: list[TemporalNameVariant] = Field(min_length=1)
    temporal_identifiers: list[TemporalIdentifierAssertion] = Field(min_length=1)
    temporal_roles: list[TemporalRoleTitleAssertion] = Field(min_length=1)
    temporal_source_assertions: list[TemporalSourceIdentityAssertion] = Field(min_length=1)
    temporal_conflicts: list[TemporalIdentityConflict] = Field(min_length=1)
    temporal_snapshots: list[TemporalIdentitySnapshot] = Field(min_length=1)
    temporal_context_cannot_auto_merge_entities: Literal[True] = True
    current_label_does_not_erase_historical_labels: Literal[True] = True
    temporal_overlap_does_not_establish_same_identity: Literal[True] = True
    historical_role_does_not_establish_current_affiliation: Literal[True] = True

    @model_validator(mode="after")
    def validate_bundle(self):
        base = self.entity_resolution_identity_graph_bundle
        entities = {x.entity_id for x in base.entities}
        graph_snapshots = {x.identity_graph_snapshot_id for x in base.identity_graph_snapshots}
        names = {x.temporal_name_id: x for x in self.temporal_names}
        ids = {x.temporal_identifier_id: x for x in self.temporal_identifiers}
        roles = {x.temporal_role_id: x for x in self.temporal_roles}
        conflicts = {x.temporal_conflict_id: x for x in self.temporal_conflicts}

        for group, label in (
            (list(names), "temporal_name_id"),
            (list(ids), "temporal_identifier_id"),
            (list(roles), "temporal_role_id"),
            ([x.temporal_source_assertion_id for x in self.temporal_source_assertions], "temporal_source_assertion_id"),
            (list(conflicts), "temporal_conflict_id"),
            ([x.temporal_snapshot_id for x in self.temporal_snapshots], "temporal_snapshot_id"),
        ):
            _unique(group, label)

        for x in self.temporal_names:
            if x.entity_ref not in entities:
                raise ValueError("temporal name references unknown entity")
            if x.superseded_by_name_ref and x.superseded_by_name_ref not in names:
                raise ValueError("temporal name supersession reference unresolved")
        for x in self.temporal_identifiers:
            if x.entity_ref not in entities:
                raise ValueError("temporal identifier references unknown entity")
            if x.superseded_by_identifier_ref and x.superseded_by_identifier_ref not in ids:
                raise ValueError("temporal identifier supersession reference unresolved")
        for x in self.temporal_roles:
            if x.entity_ref not in entities:
                raise ValueError("temporal role references unknown entity")
        for x in self.temporal_source_assertions:
            if x.entity_ref not in entities:
                raise ValueError("temporal source assertion references unknown entity")
            if any(r not in names for r in x.temporal_name_refs):
                raise ValueError("temporal source assertion contains unresolved temporal name")
            if any(r not in ids for r in x.temporal_identifier_refs):
                raise ValueError("temporal source assertion contains unresolved temporal identifier")
            if any(r not in roles for r in x.temporal_role_refs):
                raise ValueError("temporal source assertion contains unresolved temporal role")
        all_assertions = set(names) | set(ids) | set(roles) | {x.temporal_source_assertion_id for x in self.temporal_source_assertions}
        for x in self.temporal_conflicts:
            if x.entity_ref not in entities:
                raise ValueError("temporal conflict references unknown entity")
            if any(r not in all_assertions for r in x.assertion_refs):
                raise ValueError("temporal conflict contains unresolved assertion")
        for x in self.temporal_snapshots:
            if x.identity_graph_snapshot_ref not in graph_snapshots:
                raise ValueError("temporal snapshot references unknown identity graph snapshot")
            if any(r not in entities for r in x.entity_refs):
                raise ValueError("temporal snapshot contains unknown entity")
            if any(r not in names for r in x.active_temporal_name_refs):
                raise ValueError("temporal snapshot contains unresolved temporal name")
            if any(r not in ids for r in x.active_temporal_identifier_refs):
                raise ValueError("temporal snapshot contains unresolved temporal identifier")
            if any(r not in roles for r in x.active_temporal_role_refs):
                raise ValueError("temporal snapshot contains unresolved temporal role")
            if any(r not in conflicts for r in x.unresolved_conflict_refs):
                raise ValueError("temporal snapshot contains unresolved temporal conflict")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


def reference_temporal_identity_intelligence_bundle() -> TemporalIdentityIntelligenceBundle:
    base = reference_entity_resolution_identity_graph_bundle()
    entity = base.entities[0].entity_id
    graph_snapshot = base.identity_graph_snapshots[0].identity_graph_snapshot_id

    old_name = TemporalNameVariant(
        temporal_name_id="temporal-name:synthetic:former:v1",
        entity_ref=entity,
        value="Synthetic Research Group",
        name_kind=TemporalNameKind.former,
        valid_from="2018-01-01T00:00:00Z",
        valid_to="2023-12-31T23:59:59Z",
        source_refs=["source:synthetic:registry-2019"],
        provenance_refs=["provenance:synthetic:registry-2019:v1"],
        state=TemporalAssertionState.superseded,
        superseded_by_name_ref="temporal-name:synthetic:current:v1",
        metadata={"synthetic_reference": True},
    )
    current_name = TemporalNameVariant(
        temporal_name_id="temporal-name:synthetic:current:v1",
        entity_ref=entity,
        value="Synthetic Catalyst Institute",
        name_kind=TemporalNameKind.legal,
        valid_from="2024-01-01T00:00:00Z",
        source_refs=["source:synthetic:registry-2024"],
        provenance_refs=["provenance:synthetic:registry-2024:v1"],
        state=TemporalAssertionState.corroborated,
        metadata={"synthetic_reference": True},
    )
    disputed_name = TemporalNameVariant(
        temporal_name_id="temporal-name:synthetic:disputed:v1",
        entity_ref=entity,
        value="Synthetic Catalyst Laboratory",
        name_kind=TemporalNameKind.source_supplied,
        valid_from="2024-01-01T00:00:00Z",
        source_refs=["source:synthetic:directory-2024"],
        provenance_refs=["provenance:synthetic:directory-2024:v1"],
        state=TemporalAssertionState.disputed,
        metadata={"synthetic_reference": True},
    )
    temporal_names = [old_name, current_name, disputed_name]

    old_id = TemporalIdentifierAssertion(
        temporal_identifier_id="temporal-identifier:synthetic:old:v1",
        entity_ref=entity,
        namespace="synthetic-registry-id",
        identifier_value="SRG-001",
        valid_from="2018-01-01T00:00:00Z",
        valid_to="2023-12-31T23:59:59Z",
        source_refs=["source:synthetic:registry-2019"],
        provenance_refs=["provenance:synthetic:registry-2019:v1"],
        state=TemporalAssertionState.superseded,
        superseded_by_identifier_ref="temporal-identifier:synthetic:current:v1",
        metadata={"synthetic_reference": True},
    )
    current_id = TemporalIdentifierAssertion(
        temporal_identifier_id="temporal-identifier:synthetic:current:v1",
        entity_ref=entity,
        namespace="synthetic-registry-id",
        identifier_value="SCI-2042",
        valid_from="2024-01-01T00:00:00Z",
        source_refs=["source:synthetic:registry-2024"],
        provenance_refs=["provenance:synthetic:registry-2024:v1"],
        state=TemporalAssertionState.corroborated,
        metadata={"synthetic_reference": True},
    )
    temporal_identifiers = [old_id, current_id]

    former_role = TemporalRoleTitleAssertion(
        temporal_role_id="temporal-role:synthetic:former:v1",
        entity_ref=entity,
        role_kind=TemporalRoleKind.organizational_role,
        title="Research Group",
        organization_or_context_ref="context:synthetic:institutional-classification",
        valid_from="2018-01-01T00:00:00Z",
        valid_to="2023-12-31T23:59:59Z",
        source_refs=["source:synthetic:registry-2019"],
        provenance_refs=["provenance:synthetic:registry-2019:v1"],
        state=TemporalAssertionState.superseded,
        metadata={"synthetic_reference": True},
    )
    current_role = TemporalRoleTitleAssertion(
        temporal_role_id="temporal-role:synthetic:current:v1",
        entity_ref=entity,
        role_kind=TemporalRoleKind.organizational_role,
        title="Independent Research Institute",
        organization_or_context_ref="context:synthetic:institutional-classification",
        valid_from="2024-01-01T00:00:00Z",
        source_refs=["source:synthetic:registry-2024"],
        provenance_refs=["provenance:synthetic:registry-2024:v1"],
        state=TemporalAssertionState.corroborated,
        metadata={"synthetic_reference": True},
    )
    temporal_roles = [former_role, current_role]

    source_assertions = [
        TemporalSourceIdentityAssertion(
            temporal_source_assertion_id="temporal-source-assertion:synthetic:registry-2019:v1",
            entity_ref=entity,
            source_ref="source:synthetic:registry-2019",
            source_entity_key="registry-row:SRG-001",
            asserted_name=old_name.value,
            observed_at="2019-06-01T12:00:00Z",
            valid_from=old_name.valid_from,
            valid_to=old_name.valid_to,
            temporal_name_refs=[old_name.temporal_name_id],
            temporal_identifier_refs=[old_id.temporal_identifier_id],
            temporal_role_refs=[former_role.temporal_role_id],
            provenance_refs=["provenance:synthetic:registry-2019:v1"],
            metadata={"synthetic_reference": True},
        ),
        TemporalSourceIdentityAssertion(
            temporal_source_assertion_id="temporal-source-assertion:synthetic:registry-2024:v1",
            entity_ref=entity,
            source_ref="source:synthetic:registry-2024",
            source_entity_key="registry-row:SCI-2042",
            asserted_name=current_name.value,
            observed_at="2024-03-15T12:00:00Z",
            valid_from=current_name.valid_from,
            temporal_name_refs=[current_name.temporal_name_id],
            temporal_identifier_refs=[current_id.temporal_identifier_id],
            temporal_role_refs=[current_role.temporal_role_id],
            provenance_refs=["provenance:synthetic:registry-2024:v1"],
            metadata={"synthetic_reference": True},
        ),
    ]

    conflict = TemporalIdentityConflict(
        temporal_conflict_id="temporal-conflict:synthetic:2024-name:v1",
        entity_ref=entity,
        conflict_kind=TemporalConflictKind.overlapping_names,
        assertion_refs=[current_name.temporal_name_id, disputed_name.temporal_name_id],
        source_refs=["source:synthetic:registry-2024", "source:synthetic:directory-2024"],
        provenance_refs=["provenance:synthetic:registry-2024:v1", "provenance:synthetic:directory-2024:v1"],
        metadata={"synthetic_reference": True},
    )

    snapshot = TemporalIdentitySnapshot(
        temporal_snapshot_id="temporal-snapshot:synthetic:2026-09-29:v1",
        identity_graph_snapshot_ref=graph_snapshot,
        as_of="2026-09-29T12:00:00Z",
        entity_refs=[entity],
        active_temporal_name_refs=[current_name.temporal_name_id, disputed_name.temporal_name_id],
        active_temporal_identifier_refs=[current_id.temporal_identifier_id],
        active_temporal_role_refs=[current_role.temporal_role_id],
        unresolved_conflict_refs=[conflict.temporal_conflict_id],
        metadata={"synthetic_reference": True},
    )

    return TemporalIdentityIntelligenceBundle(
        entity_resolution_identity_graph_bundle=base,
        temporal_names=temporal_names,
        temporal_identifiers=temporal_identifiers,
        temporal_roles=temporal_roles,
        temporal_source_assertions=source_assertions,
        temporal_conflicts=[conflict],
        temporal_snapshots=[snapshot],
    )


def contract_document() -> dict[str, Any]:
    b = reference_temporal_identity_intelligence_bundle()
    return {
        "ok": True,
        "release": CORE_RELEASE,
        "contract": CONTRACT_VERSION,
        "extends_contract": "sc.core.entity-resolution-identity-graph-foundation.v1",
        "object_types": [
            "TemporalNameVariant",
            "TemporalIdentifierAssertion",
            "TemporalRoleTitleAssertion",
            "TemporalSourceIdentityAssertion",
            "TemporalIdentityConflict",
            "TemporalIdentitySnapshot",
            "TemporalIdentityIntelligenceBundle",
        ],
        "principles": {
            "identity_is_time_contextual_without_becoming_time_relative_truth": True,
            "current_label_does_not_erase_historical_labels": True,
            "same_name_across_time_is_not_identity_proof": True,
            "identifier_reuse_is_not_identity_proof": True,
            "historical_role_does_not_establish_current_affiliation": True,
            "conflicting_temporal_assertions_may_coexist": True,
            "temporal_context_cannot_auto_merge_entities": True,
        },
        "capabilities": {
            "time_bounded_names_and_aliases": True,
            "time_bounded_identifiers": True,
            "time_bounded_roles_and_titles": True,
            "source_observation_time_and_validity_time": True,
            "supersession_lineage": True,
            "temporal_conflict_objects": True,
            "as_of_identity_snapshots": True,
            "multilingual_name_variant_compatibility": True,
            "deterministic_object_fingerprints": True,
        },
        "boundaries": {
            "core_infers_missing_validity_intervals": False,
            "core_treats_current_name_as_historically_canonical": False,
            "core_treats_historical_role_as_current_affiliation": False,
            "core_auto_resolves_temporal_conflicts": False,
            "core_auto_merges_entities_from_temporal_overlap": False,
            "core_rewrites_v3770_identity_graph_during_temporal_selection": False,
        },
        "roadmap_integration": {
            "extends_v3770_entity_resolution_identity_graph_foundation": True,
            "prepares_v3790_probabilistic_record_linkage_entity_matching": True,
            "prepares_v3800_cross_source_entity_reconciliation_identity_provenance": True,
            "preserves_v3760_evidence_validation_boundary": True,
        },
        "reference": {
            "temporal_name_count": len(b.temporal_names),
            "temporal_identifier_count": len(b.temporal_identifiers),
            "temporal_role_count": len(b.temporal_roles),
            "temporal_source_assertion_count": len(b.temporal_source_assertions),
            "temporal_conflict_count": len(b.temporal_conflicts),
            "temporal_snapshot_count": len(b.temporal_snapshots),
            "unresolved_conflicts_preserved": True,
            "identity_graph_mutation_performed": False,
            "bundle_fingerprint_sha256": b.fingerprint(),
        },
    }
