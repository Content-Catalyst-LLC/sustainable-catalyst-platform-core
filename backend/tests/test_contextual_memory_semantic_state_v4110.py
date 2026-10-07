from copy import deepcopy

import pytest
from pydantic import ValidationError

from app.config import Settings
from app.routers import contextual_memory_semantic_state as api
from app.services.contextual_memory_semantic_state import (
    ContextualMemorySemanticStateBundle,
    MemoryReviewState,
    MemoryRevisionState,
    MemoryScopeKind,
    MemoryTransitionKind,
    SemanticMemoryKind,
    contract_document,
    reference_contextual_memory_semantic_state_bundle,
)


def ref():
    return reference_contextual_memory_semantic_state_bundle()


def payload():
    return ref().model_dump(mode="json")


def invalid(mutator):
    p = deepcopy(payload())
    mutator(p)
    with pytest.raises((ValidationError, ValueError)):
        ContextualMemorySemanticStateBundle.model_validate(p)


def test_release_identity():
    assert tuple(map(int, Settings().version.split("."))) >= (4, 11, 0)
    assert ref().release == "4.11.0"
    assert ref().contract == "sc.core.contextual-memory-semantic-state-foundation.v1"
    assert ref().predecessor_contract == "sc.core.unified-semantic-contextual-intelligence-runtime.v1"


def test_v410_predecessor_is_exact_and_preserved():
    assert ref().predecessor_runtime.release == "4.10.0"
    assert ref().predecessor_runtime.contract == ref().predecessor_contract
    assert ref().snapshots[0].predecessor_runtime_fingerprint_sha256 == ref().predecessor_runtime.fingerprint()


def test_reference_has_four_memory_scopes():
    assert len(ref().scopes) == 4
    assert {x.kind for x in ref().scopes} == set(MemoryScopeKind)


def test_scope_hierarchy_connects_document_and_session_to_investigation_and_project():
    scopes = {x.scope_id: x for x in ref().scopes}
    project = scopes["memory-scope:research-project:contextual-intelligence-reference"]
    investigation = scopes["memory-scope:investigation:cross-source-policy"]
    session = scopes["memory-scope:runtime-session:v4.10-reference"]
    document = scopes["memory-scope:document:governed-reference-corpus"]
    assert project.parent_scope_ref is None
    assert investigation.parent_scope_ref == project.scope_id
    assert session.parent_scope_ref == investigation.scope_id
    assert document.parent_scope_ref == investigation.scope_id


def test_reference_has_six_semantic_memories():
    assert len(ref().memories) == 6
    assert {x.kind for x in ref().memories} == set(SemanticMemoryKind)


def test_memory_identity_is_stable_and_contextual_not_fact():
    assert all(x.stable_identity_across_revisions for x in ref().memories)
    assert all(x.memory_entry_is_contextual_state_not_fact for x in ref().memories)


def test_every_memory_has_current_revision():
    revisions = {x.revision_id: x for x in ref().revisions}
    for m in ref().memories:
        assert m.current_revision_ref in revisions
        assert revisions[m.current_revision_ref].memory_ref == m.memory_id


def test_actor_continuity_demonstrates_supersession_without_resolution():
    m = next(x for x in ref().memories if x.memory_id == "memory:continuity:actor-ministry-agency")
    xs = sorted([x for x in ref().revisions if x.memory_ref == m.memory_id], key=lambda x: x.sequence)
    assert len(xs) == 2
    assert xs[0].state == MemoryRevisionState.superseded
    assert xs[1].state == MemoryRevisionState.unresolved
    assert xs[1].review_state == MemoryReviewState.reviewed
    assert xs[1].predecessor_revision_ref == xs[0].revision_id
    assert "thread:actor-continuity:candidate" in xs[1].unresolved_refs


def test_superseded_revision_is_retained():
    assert any(x.state == MemoryRevisionState.superseded for x in ref().revisions)
    assert all(x.immutable for x in ref().revisions)


def test_reference_revisions_are_contiguous_per_memory():
    for m in ref().memories:
        xs = sorted([x for x in ref().revisions if x.memory_ref == m.memory_id], key=lambda x: x.sequence)
        assert [x.sequence for x in xs] == list(range(1, len(xs) + 1))


def test_revision_payloads_resolve_to_v410_artifacts():
    artifact_ids = {x.artifact_id for x in ref().predecessor_runtime.artifacts}
    for r in ref().revisions:
        assert set(r.source_artifact_refs) <= artifact_ids
        assert len(r.semantic_payload_fingerprint_sha256) == 64


def test_qualification_carry_forward_resolves_to_v410_runtime():
    qids = {x.qualification_id for x in ref().predecessor_runtime.qualifications}
    for m in ref().memories:
        assert set(m.qualification_refs) <= qids
    for r in ref().revisions:
        assert set(r.qualification_refs) <= qids


def test_document_ambiguity_carries_into_investigation():
    c = next(x for x in ref().carry_forwards if x.memory_ref == "memory:referential-ambiguity:it")
    assert c.from_scope_ref == "memory-scope:document:governed-reference-corpus"
    assert c.to_scope_ref == "memory-scope:investigation:cross-source-policy"
    assert c.inherited_qualifications_remain_active is True
    assert c.carry_forward_does_not_increase_truth_or_authority is True


def test_epistemic_uncertainty_carries_to_project():
    c = next(x for x in ref().carry_forwards if x.memory_ref == "memory:epistemic-state:ministry-uncertainty")
    assert c.to_scope_ref == "memory-scope:research-project:contextual-intelligence-reference"
    assert "qualification:05:source-uncertainty-preserved" in c.qualification_refs


def test_actor_continuity_carries_to_project_without_identity_merge():
    c = next(x for x in ref().carry_forwards if x.memory_ref == "memory:continuity:actor-ministry-agency")
    assert c.transition == MemoryTransitionKind.carried_forward
    assert "qualification:07:continuity-hypothesis-unresolved" in c.qualification_refs


def test_memory_links_are_contextual_only():
    assert len(ref().links) == 2
    assert all(x.link_is_contextual_not_identity_or_evidence_fact for x in ref().links)


def test_project_checkpoint_contains_all_current_memories():
    cp = ref().checkpoints[0]
    assert len(cp.memory_refs) == 6
    assert set(cp.current_revision_refs) == {x.current_revision_ref for x in ref().memories}
    assert cp.reproducible is True
    assert cp.checkpoint_is_state_capture_not_truth_freeze is True


def test_checkpoint_binds_v410_session_and_snapshot():
    cp = ref().checkpoints[0]
    assert cp.predecessor_runtime_session_ref == ref().predecessor_runtime.sessions[0].session_id
    assert cp.predecessor_runtime_snapshot_ref == ref().predecessor_runtime.snapshots[0].snapshot_id


def test_snapshot_covers_scopes_memories_and_revisions():
    s = ref().snapshots[0]
    assert set(s.scope_fingerprints) == {x.scope_id for x in ref().scopes}
    assert set(s.memory_fingerprints) == {x.memory_id for x in ref().memories}
    assert set(s.revision_fingerprints) == {x.revision_id for x in ref().revisions}


def test_snapshot_deterministic_memory_fingerprint_is_stable():
    a = ref().snapshots[0].deterministic_memory_fingerprint_sha256
    b = reference_contextual_memory_semantic_state_bundle().snapshots[0].deterministic_memory_fingerprint_sha256
    assert a == b


def test_bundle_fingerprint_is_deterministic():
    assert ref().fingerprint() == reference_contextual_memory_semantic_state_bundle().fingerprint()


def test_policy_persistence_is_not_truth():
    p = ref().policy
    assert p.memory_persistence_establishes_truth is False
    assert p.memory_repetition_increases_truth is False
    assert p.memory_scope_establishes_source_authority is False
    assert p.carried_forward_state_establishes_canonical_identity is False


def test_policy_graph_mutations_are_not_authorized():
    p = ref().policy
    assert p.context_graph_mutation_authorized is False
    assert p.identity_graph_mutation_authorized is False
    assert p.evidence_graph_mutation_authorized is False
    assert p.knowledge_graph_mutation_authorized is False


def test_policy_preserves_unresolved_state_and_predecessor_objects():
    p = ref().policy
    assert p.unresolved_state_may_persist_indefinitely is True
    assert p.predecessor_runtime_objects_remain_immutable is True
    assert p.original_language_lineage_is_preserved is True


def test_contract_reference_counts():
    r = contract_document()["reference"]
    assert r["predecessor_release"] == "4.10.0"
    assert r["scopes"] == 4
    assert r["memories"] == 6
    assert r["revisions"] == 7
    assert r["current_revisions"] == 6
    assert r["carry_forwards"] == 3
    assert r["links"] == 2
    assert r["checkpoints"] == 1
    assert r["snapshots"] == 1
    assert r["unresolved_memories"] == 5
    assert r["database_backed_persistence_required_by_v411"] is False


def test_contract_boundaries_are_explicit():
    b = contract_document()["boundaries"]
    assert b["memory_persistence_establishes_truth"] is False
    assert b["memory_repetition_increases_truth"] is False
    assert b["carried_forward_state_establishes_canonical_identity"] is False
    assert b["memory_revision_rewrites_predecessor_semantics"] is False
    assert b["context_graph_mutation_performed"] is False
    assert b["identity_graph_mutation_performed"] is False
    assert b["evidence_graph_mutation_performed"] is False
    assert b["knowledge_graph_mutation_performed"] is False


def test_contract_roadmap_prepares_retrieval_and_reasoning_line():
    r = contract_document()["roadmap_integration"]
    assert r["extends_v4100_unified_semantic_context_runtime"] is True
    assert r["prepares_v4120_context_retrieval_relevance_intelligence"] is True
    assert r["prepares_v4130_claim_alignment_contradiction_intelligence"] is True
    assert r["prepares_v4200_unified_contextual_reasoning_runtime"] is True


def test_api_functions_are_directly_callable():
    assert api.contract()["release"] == "4.11.0"
    assert api.public_contract()["contract"] == "sc.core.contextual-memory-semantic-state-foundation.v1"
    assert api.reference_scopes()["count"] == 4
    assert api.reference_scopes(MemoryScopeKind.research_project)["count"] == 1
    assert api.reference_memories()["count"] == 6
    assert api.reference_memories(SemanticMemoryKind.cross_document_continuity)["count"] == 1
    assert api.reference_revisions("memory:continuity:actor-ministry-agency")["count"] == 2
    assert api.reference_checkpoint()["checkpoint"]["reproducible"] is True


def test_bad_scope_parent_fails():
    invalid(lambda p: p["scopes"][1].__setitem__("parent_scope_ref", "memory-scope:missing"))


def test_scope_cycle_fails():
    def mutate(p):
        p["scopes"][0]["parent_scope_ref"] = p["scopes"][1]["scope_id"]
    invalid(mutate)


def test_bad_current_revision_fails():
    invalid(lambda p: p["memories"][0].__setitem__("current_revision_ref", "memory-revision:missing"))


def test_bad_revision_sequence_fails():
    invalid(lambda p: p["revisions"][0].__setitem__("sequence", 2))


def test_bad_revision_artifact_fails():
    invalid(lambda p: p["revisions"][0]["source_artifact_refs"].__setitem__(0, "runtime-artifact:missing"))


def test_bad_revision_qualification_fails():
    invalid(lambda p: p["revisions"][0]["qualification_refs"].__setitem__(0, "qualification:missing"))


def test_reviewed_revision_requires_reviewer():
    def mutate(p):
        p["revisions"][0]["review_state"] = "reviewed"
        p["revisions"][0]["reviewer_ref"] = None
    invalid(mutate)


def test_bad_carry_scope_fails():
    invalid(lambda p: p["carry_forwards"][0].__setitem__("to_scope_ref", "memory-scope:missing"))


def test_bad_memory_link_fails():
    invalid(lambda p: p["links"][0].__setitem__("target_memory_ref", "memory:missing"))


def test_bad_checkpoint_current_revision_fails():
    invalid(lambda p: p["checkpoints"][0]["current_revision_refs"].__setitem__(0, "memory-revision:missing"))


def test_bad_snapshot_predecessor_fingerprint_fails():
    invalid(lambda p: p["snapshots"][0].__setitem__("predecessor_runtime_fingerprint_sha256", "0" * 64))


def test_database_migration_is_none():
    assert ref().database_migration == "none"
    assert contract_document()["database_migration"] == "none"


def test_main_mounts_v411_routers():
    from app.main import create_app
    app = create_app()
    paths = {r.path for r in app.routes}
    assert "/v1/context-memory/contract" in paths
    assert "/public/v1/context-memory/contract" in paths
