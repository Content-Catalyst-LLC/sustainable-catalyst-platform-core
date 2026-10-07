from __future__ import annotations

from enum import Enum
from functools import lru_cache
from typing import Literal

from pydantic import BaseModel, Field, model_validator

from .computational_runtime_objects import canonical_sha256
from .unified_semantic_context_runtime import (
    UnifiedSemanticContextRuntimeBundle,
    reference_unified_semantic_context_runtime_bundle,
)

CORE_RELEASE = "4.11.0"
CONTRACT_VERSION = "sc.core.contextual-memory-semantic-state-foundation.v1"
PREDECESSOR_CONTRACT = "sc.core.unified-semantic-contextual-intelligence-runtime.v1"


class MemoryScopeKind(str, Enum):
    document = "document"
    runtime_session = "runtime-session"
    investigation = "investigation"
    research_project = "research-project"


class SemanticMemoryKind(str, Enum):
    referential_ambiguity = "referential-ambiguity"
    geographic_grounding = "geographic-grounding"
    epistemic_stance = "epistemic-stance"
    cross_document_continuity = "cross-document-continuity"
    multilingual_divergence = "multilingual-divergence"
    runtime_qualification_summary = "runtime-qualification-summary"


class MemoryRevisionState(str, Enum):
    active = "active"
    qualified = "qualified"
    unresolved = "unresolved"
    superseded = "superseded"
    disputed = "disputed"


class MemoryReviewState(str, Enum):
    candidate = "candidate"
    reviewed = "reviewed"
    accepted = "accepted"
    disputed = "disputed"


class MemoryTransitionKind(str, Enum):
    created = "created"
    carried_forward = "carried-forward"
    reviewed = "reviewed"
    qualified = "qualified"
    superseded = "superseded"


class MemoryLinkKind(str, Enum):
    derived_from = "derived-from"
    contextualizes = "contextualizes"
    same_thread_candidate = "same-thread-candidate"
    qualification_of = "qualification-of"
    supersedes = "supersedes"


class ContextualMemoryPolicy(BaseModel):
    policy_id: str = Field(min_length=3, max_length=500)
    memory_scope_is_explicit: Literal[True] = True
    stable_memory_identity_is_preserved_across_sessions: Literal[True] = True
    revisions_are_immutable: Literal[True] = True
    supersession_preserves_prior_revisions: Literal[True] = True
    qualification_carry_forward_is_required: Literal[True] = True
    memory_requires_provenance: Literal[True] = True
    predecessor_runtime_objects_remain_immutable: Literal[True] = True
    original_language_lineage_is_preserved: Literal[True] = True
    unresolved_state_may_persist_indefinitely: Literal[True] = True
    storage_backend_is_not_semantic_authority: Literal[True] = True
    memory_persistence_establishes_truth: Literal[False] = False
    memory_repetition_increases_truth: Literal[False] = False
    memory_scope_establishes_source_authority: Literal[False] = False
    carried_forward_state_establishes_canonical_identity: Literal[False] = False
    context_graph_mutation_authorized: Literal[False] = False
    identity_graph_mutation_authorized: Literal[False] = False
    evidence_graph_mutation_authorized: Literal[False] = False
    knowledge_graph_mutation_authorized: Literal[False] = False


class ContextualMemoryScope(BaseModel):
    scope_id: str = Field(min_length=3, max_length=500)
    kind: MemoryScopeKind
    label: str = Field(min_length=3, max_length=1000)
    parent_scope_ref: str | None = Field(default=None, max_length=500)
    external_context_refs: list[str] = Field(default_factory=list)
    stable_identity: Literal[True] = True
    scope_membership_does_not_establish_truth_or_authority: Literal[True] = True

    @model_validator(mode="after")
    def validate_refs(self):
        if len(self.external_context_refs) != len(set(self.external_context_refs)):
            raise ValueError("external_context_refs must be unique")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class SemanticMemoryEntry(BaseModel):
    memory_id: str = Field(min_length=3, max_length=500)
    scope_ref: str = Field(min_length=3, max_length=500)
    kind: SemanticMemoryKind
    label: str = Field(min_length=3, max_length=1000)
    current_revision_ref: str = Field(min_length=3, max_length=500)
    source_artifact_refs: list[str] = Field(min_length=1)
    qualification_refs: list[str] = Field(default_factory=list)
    unresolved_refs: list[str] = Field(default_factory=list)
    durable: Literal[True] = True
    stable_identity_across_revisions: Literal[True] = True
    memory_entry_is_contextual_state_not_fact: Literal[True] = True

    @model_validator(mode="after")
    def validate_unique_refs(self):
        for values, label in [
            (self.source_artifact_refs, "source_artifact_refs"),
            (self.qualification_refs, "qualification_refs"),
            (self.unresolved_refs, "unresolved_refs"),
        ]:
            if len(values) != len(set(values)):
                raise ValueError(f"{label} must be unique")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class SemanticStateRevision(BaseModel):
    revision_id: str = Field(min_length=3, max_length=500)
    memory_ref: str = Field(min_length=3, max_length=500)
    sequence: int = Field(ge=1)
    predecessor_revision_ref: str | None = Field(default=None, max_length=500)
    transition: MemoryTransitionKind
    state: MemoryRevisionState
    review_state: MemoryReviewState
    semantic_payload_ref: str = Field(min_length=3, max_length=500)
    semantic_payload_fingerprint_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    source_artifact_refs: list[str] = Field(min_length=1)
    qualification_refs: list[str] = Field(default_factory=list)
    unresolved_refs: list[str] = Field(default_factory=list)
    reviewer_ref: str | None = Field(default=None, max_length=500)
    notes: list[str] = Field(default_factory=list)
    immutable: Literal[True] = True
    revision_does_not_rewrite_source_semantics: Literal[True] = True
    revision_state_is_not_truth_verdict: Literal[True] = True

    @model_validator(mode="after")
    def validate_review(self):
        if self.review_state in {MemoryReviewState.reviewed, MemoryReviewState.accepted, MemoryReviewState.disputed} and not self.reviewer_ref:
            raise ValueError("reviewed/accepted/disputed revision requires reviewer_ref")
        if self.sequence == 1 and self.predecessor_revision_ref is not None:
            raise ValueError("first revision cannot have predecessor_revision_ref")
        if self.sequence > 1 and self.predecessor_revision_ref is None:
            raise ValueError("later revision requires predecessor_revision_ref")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class MemoryCarryForward(BaseModel):
    carry_id: str = Field(min_length=3, max_length=500)
    memory_ref: str = Field(min_length=3, max_length=500)
    from_scope_ref: str = Field(min_length=3, max_length=500)
    to_scope_ref: str = Field(min_length=3, max_length=500)
    revision_ref: str = Field(min_length=3, max_length=500)
    qualification_refs: list[str] = Field(default_factory=list)
    transition: Literal[MemoryTransitionKind.carried_forward] = MemoryTransitionKind.carried_forward
    inherited_without_semantic_rewrite: Literal[True] = True
    inherited_qualifications_remain_active: Literal[True] = True
    carry_forward_does_not_increase_truth_or_authority: Literal[True] = True

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class ContextualMemoryLink(BaseModel):
    link_id: str = Field(min_length=3, max_length=500)
    source_memory_ref: str = Field(min_length=3, max_length=500)
    target_memory_ref: str = Field(min_length=3, max_length=500)
    kind: MemoryLinkKind
    review_state: MemoryReviewState
    reviewer_ref: str | None = Field(default=None, max_length=500)
    notes: list[str] = Field(default_factory=list)
    link_is_contextual_not_identity_or_evidence_fact: Literal[True] = True

    @model_validator(mode="after")
    def validate_link(self):
        if self.source_memory_ref == self.target_memory_ref:
            raise ValueError("memory link source and target must differ")
        if self.review_state in {MemoryReviewState.reviewed, MemoryReviewState.accepted, MemoryReviewState.disputed} and not self.reviewer_ref:
            raise ValueError("reviewed/accepted/disputed memory link requires reviewer_ref")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class MemoryProvenanceRecord(BaseModel):
    provenance_id: str = Field(min_length=3, max_length=500)
    subject_refs: list[str] = Field(min_length=1)
    source_refs: list[str] = Field(min_length=1)
    produced_by_ref: str = Field(min_length=3, max_length=500)
    notes: list[str] = Field(default_factory=list)
    replayable: Literal[True] = True
    provenance_does_not_establish_truth_or_authority: Literal[True] = True

    @model_validator(mode="after")
    def validate_unique_refs(self):
        if len(self.subject_refs) != len(set(self.subject_refs)):
            raise ValueError("provenance subject_refs must be unique")
        if len(self.source_refs) != len(set(self.source_refs)):
            raise ValueError("provenance source_refs must be unique")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class ContextualMemoryCheckpoint(BaseModel):
    checkpoint_id: str = Field(min_length=3, max_length=500)
    scope_ref: str = Field(min_length=3, max_length=500)
    memory_refs: list[str] = Field(min_length=1)
    current_revision_refs: list[str] = Field(min_length=1)
    qualification_refs: list[str] = Field(default_factory=list)
    predecessor_runtime_session_ref: str = Field(min_length=3, max_length=500)
    predecessor_runtime_snapshot_ref: str = Field(min_length=3, max_length=500)
    reproducible: Literal[True] = True
    checkpoint_is_state_capture_not_truth_freeze: Literal[True] = True

    @model_validator(mode="after")
    def validate_unique_refs(self):
        if len(self.memory_refs) != len(set(self.memory_refs)):
            raise ValueError("checkpoint memory_refs must be unique")
        if len(self.current_revision_refs) != len(set(self.current_revision_refs)):
            raise ValueError("checkpoint current_revision_refs must be unique")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class ContextualMemorySnapshot(BaseModel):
    snapshot_id: str = Field(min_length=3, max_length=500)
    predecessor_runtime_fingerprint_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    scope_fingerprints: dict[str, str] = Field(min_length=1)
    memory_fingerprints: dict[str, str] = Field(min_length=1)
    revision_fingerprints: dict[str, str] = Field(min_length=1)
    checkpoint_fingerprint_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    deterministic_memory_fingerprint_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    immutable: Literal[True] = True
    supersedable: Literal[True] = True
    snapshot_does_not_freeze_semantic_truth: Literal[True] = True

    @model_validator(mode="after")
    def validate_hash_maps(self):
        for mapping in (self.scope_fingerprints, self.memory_fingerprints, self.revision_fingerprints):
            for value in mapping.values():
                if len(value) != 64 or any(c not in "0123456789abcdef" for c in value):
                    raise ValueError("snapshot fingerprint maps must contain sha256 hex")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class ContextualMemorySemanticStateBundle(BaseModel):
    release: Literal["4.11.0"] = "4.11.0"
    contract: Literal[CONTRACT_VERSION] = CONTRACT_VERSION
    predecessor_contract: Literal[PREDECESSOR_CONTRACT] = PREDECESSOR_CONTRACT
    policy: ContextualMemoryPolicy
    predecessor_runtime: UnifiedSemanticContextRuntimeBundle
    scopes: list[ContextualMemoryScope] = Field(min_length=4)
    memories: list[SemanticMemoryEntry] = Field(min_length=1)
    revisions: list[SemanticStateRevision] = Field(min_length=1)
    carry_forwards: list[MemoryCarryForward] = Field(default_factory=list)
    links: list[ContextualMemoryLink] = Field(default_factory=list)
    provenance_records: list[MemoryProvenanceRecord] = Field(min_length=1)
    checkpoints: list[ContextualMemoryCheckpoint] = Field(min_length=1)
    snapshots: list[ContextualMemorySnapshot] = Field(min_length=1)
    database_migration: Literal["none"] = "none"

    @model_validator(mode="after")
    def validate_bundle(self):
        if self.predecessor_runtime.release != "4.10.0" or self.predecessor_runtime.contract != PREDECESSOR_CONTRACT:
            raise ValueError("v4.11 must preserve governed v4.10 predecessor runtime")

        def unique(values: list[str], label: str):
            if len(values) != len(set(values)):
                raise ValueError(f"{label} must be unique")

        unique([x.scope_id for x in self.scopes], "scope ids")
        unique([x.memory_id for x in self.memories], "memory ids")
        unique([x.revision_id for x in self.revisions], "revision ids")
        unique([x.carry_id for x in self.carry_forwards], "carry ids")
        unique([x.link_id for x in self.links], "link ids")
        unique([x.provenance_id for x in self.provenance_records], "provenance ids")
        unique([x.checkpoint_id for x in self.checkpoints], "checkpoint ids")
        unique([x.snapshot_id for x in self.snapshots], "snapshot ids")

        scopes = {x.scope_id: x for x in self.scopes}
        memories = {x.memory_id: x for x in self.memories}
        revisions = {x.revision_id: x for x in self.revisions}
        qualifications = {x.qualification_id for x in self.predecessor_runtime.qualifications}
        artifacts = {x.artifact_id: x for x in self.predecessor_runtime.artifacts}
        runtime_session_ids = {x.session_id for x in self.predecessor_runtime.sessions}
        runtime_snapshot_ids = {x.snapshot_id for x in self.predecessor_runtime.snapshots}

        for scope in self.scopes:
            if scope.parent_scope_ref is not None and scope.parent_scope_ref not in scopes:
                raise ValueError("scope parent_scope_ref must resolve")
            # No scope may be its own ancestor.
            seen = {scope.scope_id}
            current = scope.parent_scope_ref
            while current is not None:
                if current in seen:
                    raise ValueError("memory scope hierarchy must be acyclic")
                seen.add(current)
                current = scopes[current].parent_scope_ref

        by_memory: dict[str, list[SemanticStateRevision]] = {mid: [] for mid in memories}
        for rev in self.revisions:
            if rev.memory_ref not in memories:
                raise ValueError("revision memory_ref must resolve")
            by_memory[rev.memory_ref].append(rev)
            for ref in rev.source_artifact_refs:
                if ref not in artifacts:
                    raise ValueError("revision source_artifact_refs must resolve to v4.10 artifacts")
            for ref in rev.qualification_refs:
                if ref not in qualifications:
                    raise ValueError("revision qualification_refs must resolve to v4.10 qualifications")

        for memory in self.memories:
            if memory.scope_ref not in scopes:
                raise ValueError("memory scope_ref must resolve")
            if memory.current_revision_ref not in revisions:
                raise ValueError("memory current_revision_ref must resolve")
            if revisions[memory.current_revision_ref].memory_ref != memory.memory_id:
                raise ValueError("memory current_revision_ref must belong to memory")
            for ref in memory.source_artifact_refs:
                if ref not in artifacts:
                    raise ValueError("memory source_artifact_refs must resolve to v4.10 artifacts")
            for ref in memory.qualification_refs:
                if ref not in qualifications:
                    raise ValueError("memory qualification_refs must resolve to v4.10 qualifications")
            chain = sorted(by_memory[memory.memory_id], key=lambda x: x.sequence)
            if [x.sequence for x in chain] != list(range(1, len(chain) + 1)):
                raise ValueError("memory revision sequence must be contiguous")
            if memory.current_revision_ref != chain[-1].revision_id:
                raise ValueError("memory current_revision_ref must point to latest revision")
            for i, rev in enumerate(chain):
                expected = None if i == 0 else chain[i - 1].revision_id
                if rev.predecessor_revision_ref != expected:
                    raise ValueError("memory revision predecessor chain must be exact")
                if i < len(chain) - 1 and rev.state != MemoryRevisionState.superseded:
                    raise ValueError("non-current memory revisions must be superseded")

        for carry in self.carry_forwards:
            if carry.memory_ref not in memories or carry.revision_ref not in revisions:
                raise ValueError("carry-forward memory/revision refs must resolve")
            if carry.from_scope_ref not in scopes or carry.to_scope_ref not in scopes:
                raise ValueError("carry-forward scope refs must resolve")
            if memories[carry.memory_ref].scope_ref != carry.from_scope_ref:
                raise ValueError("carry-forward from_scope_ref must match memory origin scope")
            if revisions[carry.revision_ref].memory_ref != carry.memory_ref:
                raise ValueError("carry-forward revision must belong to memory")
            for ref in carry.qualification_refs:
                if ref not in qualifications:
                    raise ValueError("carry-forward qualification_refs must resolve")

        for link in self.links:
            if link.source_memory_ref not in memories or link.target_memory_ref not in memories:
                raise ValueError("memory link endpoints must resolve")

        all_subjects = set(scopes) | set(memories) | set(revisions) | {x.carry_id for x in self.carry_forwards} | {x.link_id for x in self.links} | {x.checkpoint_id for x in self.checkpoints}
        for p in self.provenance_records:
            for ref in p.subject_refs:
                if ref not in all_subjects:
                    raise ValueError("memory provenance subject_refs must resolve")

        for checkpoint in self.checkpoints:
            if checkpoint.scope_ref not in scopes:
                raise ValueError("checkpoint scope_ref must resolve")
            if checkpoint.predecessor_runtime_session_ref not in runtime_session_ids:
                raise ValueError("checkpoint runtime session ref must resolve")
            if checkpoint.predecessor_runtime_snapshot_ref not in runtime_snapshot_ids:
                raise ValueError("checkpoint runtime snapshot ref must resolve")
            for ref in checkpoint.memory_refs:
                if ref not in memories:
                    raise ValueError("checkpoint memory_refs must resolve")
            for ref in checkpoint.current_revision_refs:
                if ref not in revisions:
                    raise ValueError("checkpoint current_revision_refs must resolve")
            expected_current = {memories[x].current_revision_ref for x in checkpoint.memory_refs}
            if set(checkpoint.current_revision_refs) != expected_current:
                raise ValueError("checkpoint current revisions must match included memories")
            for ref in checkpoint.qualification_refs:
                if ref not in qualifications:
                    raise ValueError("checkpoint qualification_refs must resolve")

        predecessor_fp = self.predecessor_runtime.fingerprint()
        for snapshot in self.snapshots:
            if snapshot.predecessor_runtime_fingerprint_sha256 != predecessor_fp:
                raise ValueError("snapshot must preserve exact v4.10 predecessor fingerprint")
            if set(snapshot.scope_fingerprints) != set(scopes):
                raise ValueError("snapshot scope fingerprints must cover all scopes")
            if set(snapshot.memory_fingerprints) != set(memories):
                raise ValueError("snapshot memory fingerprints must cover all memories")
            if set(snapshot.revision_fingerprints) != set(revisions):
                raise ValueError("snapshot revision fingerprints must cover all revisions")
            checkpoint = self.checkpoints[0]
            if snapshot.checkpoint_fingerprint_sha256 != checkpoint.fingerprint():
                raise ValueError("snapshot checkpoint fingerprint must match governed checkpoint")

        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


def _reference_payload_fingerprint(artifact_ref: str) -> str:
    runtime = reference_unified_semantic_context_runtime_bundle()
    artifact = next(x for x in runtime.artifacts if x.artifact_id == artifact_ref)
    return artifact.object_fingerprint_sha256


@lru_cache(maxsize=1)
def reference_contextual_memory_semantic_state_bundle() -> ContextualMemorySemanticStateBundle:
    runtime = reference_unified_semantic_context_runtime_bundle()

    scopes = [
        ContextualMemoryScope(
            scope_id="memory-scope:research-project:contextual-intelligence-reference",
            kind=MemoryScopeKind.research_project,
            label="Contextual Intelligence Reference Research Project",
            external_context_refs=["research-project:contextual-intelligence-reference"],
        ),
        ContextualMemoryScope(
            scope_id="memory-scope:investigation:cross-source-policy",
            kind=MemoryScopeKind.investigation,
            label="Cross-Source Policy Investigation",
            parent_scope_ref="memory-scope:research-project:contextual-intelligence-reference",
            external_context_refs=["investigation:cross-source-policy"],
        ),
        ContextualMemoryScope(
            scope_id="memory-scope:runtime-session:v4.10-reference",
            kind=MemoryScopeKind.runtime_session,
            label="v4.10 Unified Semantic Runtime Reference Session",
            parent_scope_ref="memory-scope:investigation:cross-source-policy",
            external_context_refs=[runtime.sessions[0].session_id],
        ),
        ContextualMemoryScope(
            scope_id="memory-scope:document:governed-reference-corpus",
            kind=MemoryScopeKind.document,
            label="Governed Reference Corpus Source Context",
            parent_scope_ref="memory-scope:investigation:cross-source-policy",
            external_context_refs=["source:governed-reference-corpus:v4.10"],
        ),
    ]

    memory_specs = [
        (
            "memory:referential-ambiguity:it",
            "memory-scope:document:governed-reference-corpus",
            SemanticMemoryKind.referential_ambiguity,
            "Unresolved referential alternatives for 'It'",
            "runtime-artifact:stage:03:reference",
            "qualification:01:ambiguity-preserved",
            ["mention:it-unresolved"],
            MemoryRevisionState.unresolved,
        ),
        (
            "memory:geographic-grounding:brussels",
            "memory-scope:investigation:cross-source-policy",
            SemanticMemoryKind.geographic_grounding,
            "Brussels source-place grounding with canonical geography deferred",
            "runtime-artifact:stage:04:reference",
            "qualification:04:geographic-identity-deferred",
            ["spatial-anchor:brussels-source-place"],
            MemoryRevisionState.qualified,
        ),
        (
            "memory:epistemic-state:ministry-uncertainty",
            "memory-scope:document:governed-reference-corpus",
            SemanticMemoryKind.epistemic_stance,
            "Explicit source uncertainty remains attached to the reported estimate",
            "runtime-artifact:stage:05:reference",
            "qualification:05:source-uncertainty-preserved",
            ["assessment:ministry-explicit-uncertainty"],
            MemoryRevisionState.qualified,
        ),
        (
            "memory:continuity:actor-ministry-agency",
            "memory-scope:investigation:cross-source-policy",
            SemanticMemoryKind.cross_document_continuity,
            "Candidate ministry-agency cross-document actor continuity",
            "runtime-artifact:stage:07:reference",
            "qualification:07:continuity-hypothesis-unresolved",
            ["thread:actor-continuity:candidate"],
            MemoryRevisionState.unresolved,
        ),
        (
            "memory:multilingual-divergence:governance",
            "memory-scope:research-project:contextual-intelligence-reference",
            SemanticMemoryKind.multilingual_divergence,
            "Cultural semantic divergence across 治理 / governance / gobernanza",
            "runtime-artifact:stage:08:reference",
            "qualification:08:cultural-divergence-preserved",
            ["universal-equivalence:治理-governance-gobernanza"],
            MemoryRevisionState.qualified,
        ),
        (
            "memory:runtime-summary:v4.10-qualified-complete",
            "memory-scope:runtime-session:v4.10-reference",
            SemanticMemoryKind.runtime_qualification_summary,
            "Qualified-complete v4.10 runtime state with all qualifications preserved",
            "runtime-artifact:stage:09:reference",
            "qualification:09:benchmark-non-authoritative",
            [],
            MemoryRevisionState.qualified,
        ),
    ]

    memories: list[SemanticMemoryEntry] = []
    revisions: list[SemanticStateRevision] = []
    for idx, (memory_id, scope_ref, kind, label, artifact_ref, qualification_ref, unresolved_refs, final_state) in enumerate(memory_specs, start=1):
        rev1_id = f"memory-revision:{idx:02d}:1"
        if memory_id == "memory:continuity:actor-ministry-agency":
            rev2_id = f"memory-revision:{idx:02d}:2"
            current_ref = rev2_id
            revisions.extend([
                SemanticStateRevision(
                    revision_id=rev1_id,
                    memory_ref=memory_id,
                    sequence=1,
                    transition=MemoryTransitionKind.created,
                    state=MemoryRevisionState.superseded,
                    review_state=MemoryReviewState.candidate,
                    semantic_payload_ref=artifact_ref,
                    semantic_payload_fingerprint_sha256=_reference_payload_fingerprint(artifact_ref),
                    source_artifact_refs=[artifact_ref],
                    qualification_refs=[qualification_ref],
                    unresolved_refs=unresolved_refs,
                    notes=["Initial candidate continuity imported from the v4.7 stage artifact."],
                ),
                SemanticStateRevision(
                    revision_id=rev2_id,
                    memory_ref=memory_id,
                    sequence=2,
                    predecessor_revision_ref=rev1_id,
                    transition=MemoryTransitionKind.reviewed,
                    state=final_state,
                    review_state=MemoryReviewState.reviewed,
                    semantic_payload_ref=artifact_ref,
                    semantic_payload_fingerprint_sha256=_reference_payload_fingerprint(artifact_ref),
                    source_artifact_refs=[artifact_ref],
                    qualification_refs=[qualification_ref],
                    unresolved_refs=unresolved_refs,
                    reviewer_ref="reviewer:contextual-memory-reference",
                    notes=["Review preserves the continuity hypothesis as unresolved; no actor merge is authorized."],
                ),
            ])
        else:
            current_ref = rev1_id
            revisions.append(
                SemanticStateRevision(
                    revision_id=rev1_id,
                    memory_ref=memory_id,
                    sequence=1,
                    transition=MemoryTransitionKind.created,
                    state=final_state,
                    review_state=MemoryReviewState.reviewed,
                    semantic_payload_ref=artifact_ref,
                    semantic_payload_fingerprint_sha256=_reference_payload_fingerprint(artifact_ref),
                    source_artifact_refs=[artifact_ref],
                    qualification_refs=[qualification_ref],
                    unresolved_refs=unresolved_refs,
                    reviewer_ref="reviewer:contextual-memory-reference",
                    notes=["Imported from governed v4.10 runtime state without rewriting predecessor semantics."],
                )
            )
        memories.append(
            SemanticMemoryEntry(
                memory_id=memory_id,
                scope_ref=scope_ref,
                kind=kind,
                label=label,
                current_revision_ref=current_ref,
                source_artifact_refs=[artifact_ref],
                qualification_refs=[qualification_ref],
                unresolved_refs=unresolved_refs,
            )
        )

    carry_forwards = [
        MemoryCarryForward(
            carry_id="memory-carry:referential-ambiguity:document-to-investigation",
            memory_ref="memory:referential-ambiguity:it",
            from_scope_ref="memory-scope:document:governed-reference-corpus",
            to_scope_ref="memory-scope:investigation:cross-source-policy",
            revision_ref="memory-revision:01:1",
            qualification_refs=["qualification:01:ambiguity-preserved"],
        ),
        MemoryCarryForward(
            carry_id="memory-carry:epistemic-uncertainty:document-to-project",
            memory_ref="memory:epistemic-state:ministry-uncertainty",
            from_scope_ref="memory-scope:document:governed-reference-corpus",
            to_scope_ref="memory-scope:research-project:contextual-intelligence-reference",
            revision_ref="memory-revision:03:1",
            qualification_refs=["qualification:05:source-uncertainty-preserved"],
        ),
        MemoryCarryForward(
            carry_id="memory-carry:actor-continuity:investigation-to-project",
            memory_ref="memory:continuity:actor-ministry-agency",
            from_scope_ref="memory-scope:investigation:cross-source-policy",
            to_scope_ref="memory-scope:research-project:contextual-intelligence-reference",
            revision_ref="memory-revision:04:2",
            qualification_refs=["qualification:07:continuity-hypothesis-unresolved"],
        ),
    ]

    links = [
        ContextualMemoryLink(
            link_id="memory-link:actor-continuity-contextualized-by-uncertainty",
            source_memory_ref="memory:epistemic-state:ministry-uncertainty",
            target_memory_ref="memory:continuity:actor-ministry-agency",
            kind=MemoryLinkKind.contextualizes,
            review_state=MemoryReviewState.reviewed,
            reviewer_ref="reviewer:contextual-memory-reference",
            notes=["Epistemic state may contextualize actor-continuity interpretation without establishing identity."],
        ),
        ContextualMemoryLink(
            link_id="memory-link:multilingual-divergence-contextualizes-continuity",
            source_memory_ref="memory:multilingual-divergence:governance",
            target_memory_ref="memory:continuity:actor-ministry-agency",
            kind=MemoryLinkKind.contextualizes,
            review_state=MemoryReviewState.reviewed,
            reviewer_ref="reviewer:contextual-memory-reference",
            notes=["Cross-language divergence is retained when later reasoning revisits the cross-document thread."],
        ),
    ]

    checkpoint = ContextualMemoryCheckpoint(
        checkpoint_id="memory-checkpoint:research-project:reference:v1",
        scope_ref="memory-scope:research-project:contextual-intelligence-reference",
        memory_refs=[x.memory_id for x in memories],
        current_revision_refs=[x.current_revision_ref for x in memories],
        qualification_refs=sorted({q for x in memories for q in x.qualification_refs}),
        predecessor_runtime_session_ref=runtime.sessions[0].session_id,
        predecessor_runtime_snapshot_ref=runtime.snapshots[0].snapshot_id,
    )

    provenance_records = [
        MemoryProvenanceRecord(
            provenance_id="memory-provenance:reference:v1",
            subject_refs=[
                *[x.scope_id for x in scopes],
                *[x.memory_id for x in memories],
                *[x.revision_id for x in revisions],
                *[x.carry_id for x in carry_forwards],
                *[x.link_id for x in links],
                checkpoint.checkpoint_id,
            ],
            source_refs=[runtime.sessions[0].session_id, runtime.snapshots[0].snapshot_id, *[x.artifact_id for x in runtime.artifacts]],
            produced_by_ref=CONTRACT_VERSION,
            notes=["Reference memory state is a governed carry-forward of v4.10 artifacts and qualifications."],
        )
    ]

    scope_fps = {x.scope_id: x.fingerprint() for x in scopes}
    memory_fps = {x.memory_id: x.fingerprint() for x in memories}
    revision_fps = {x.revision_id: x.fingerprint() for x in revisions}
    deterministic = canonical_sha256(
        {
            "predecessor_runtime_fingerprint_sha256": runtime.fingerprint(),
            "scope_fingerprints": scope_fps,
            "memory_fingerprints": memory_fps,
            "revision_fingerprints": revision_fps,
            "checkpoint_fingerprint_sha256": checkpoint.fingerprint(),
        }
    )
    snapshot = ContextualMemorySnapshot(
        snapshot_id="memory-snapshot:research-project:reference:v1",
        predecessor_runtime_fingerprint_sha256=runtime.fingerprint(),
        scope_fingerprints=scope_fps,
        memory_fingerprints=memory_fps,
        revision_fingerprints=revision_fps,
        checkpoint_fingerprint_sha256=checkpoint.fingerprint(),
        deterministic_memory_fingerprint_sha256=deterministic,
    )

    return ContextualMemorySemanticStateBundle(
        policy=ContextualMemoryPolicy(policy_id="policy:contextual-memory-semantic-state:v1"),
        predecessor_runtime=runtime,
        scopes=scopes,
        memories=memories,
        revisions=revisions,
        carry_forwards=carry_forwards,
        links=links,
        provenance_records=provenance_records,
        checkpoints=[checkpoint],
        snapshots=[snapshot],
    )


def contract_document() -> dict:
    bundle = reference_contextual_memory_semantic_state_bundle()
    latest_revisions = {m.current_revision_ref for m in bundle.memories}
    return {
        "ok": True,
        "release": CORE_RELEASE,
        "contract": CONTRACT_VERSION,
        "predecessor_contract": PREDECESSOR_CONTRACT,
        "identity": {
            "product": "Sustainable Catalyst Platform Core",
            "build": "Contextual Memory & Semantic State Foundation",
            "major_api": "v4",
        },
        "principles": {
            "memory_scope_is_explicit": True,
            "stable_memory_identity_is_preserved_across_sessions": True,
            "revisions_are_immutable": True,
            "supersession_preserves_prior_revisions": True,
            "qualification_carry_forward_is_required": True,
            "predecessor_runtime_objects_remain_immutable": True,
            "unresolved_state_may_persist_indefinitely": True,
            "storage_backend_is_not_semantic_authority": True,
        },
        "boundaries": {
            "memory_persistence_establishes_truth": False,
            "memory_repetition_increases_truth": False,
            "memory_scope_establishes_source_authority": False,
            "carried_forward_state_establishes_canonical_identity": False,
            "memory_revision_rewrites_predecessor_semantics": False,
            "context_graph_mutation_performed": False,
            "identity_graph_mutation_performed": False,
            "evidence_graph_mutation_performed": False,
            "knowledge_graph_mutation_performed": False,
        },
        "roadmap_integration": {
            "extends_v4100_unified_semantic_context_runtime": True,
            "prepares_v4120_context_retrieval_relevance_intelligence": True,
            "prepares_v4130_claim_alignment_contradiction_intelligence": True,
            "prepares_v4140_evidence_context_integration": True,
            "prepares_v4150_contextual_causal_language_mechanism_intelligence": True,
            "prepares_v4200_unified_contextual_reasoning_runtime": True,
        },
        "reference": {
            "predecessor_release": bundle.predecessor_runtime.release,
            "predecessor_fingerprint_sha256": bundle.predecessor_runtime.fingerprint(),
            "scopes": len(bundle.scopes),
            "memories": len(bundle.memories),
            "revisions": len(bundle.revisions),
            "current_revisions": len(latest_revisions),
            "carry_forwards": len(bundle.carry_forwards),
            "links": len(bundle.links),
            "provenance_records": len(bundle.provenance_records),
            "checkpoints": len(bundle.checkpoints),
            "snapshots": len(bundle.snapshots),
            "unresolved_memories": sum(1 for x in bundle.memories if x.unresolved_refs),
            "database_backed_persistence_required_by_v411": False,
            "bundle_fingerprint_sha256": bundle.fingerprint(),
        },
        "database_migration": "none",
    }
