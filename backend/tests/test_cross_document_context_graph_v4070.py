from copy import deepcopy

import pytest
from pydantic import ValidationError

from app.config import Settings
from app.routers import cross_document_context_graph as api
from app.services.cross_document_context_graph import (
    CONTRACT_VERSION,
    CORE_RELEASE,
    EXTENDS_CONTRACTS,
    ContextEdgeType,
    ContextGraphEdge,
    ContextGraphInterpretation,
    ContextGraphNode,
    ContextNodeType,
    ContextThreadType,
    CrossDocumentContextGraphBundle,
    CrossDocumentContextThread,
    GraphReviewState,
    RelationBasis,
    contract_document,
    reference_cross_document_context_graph_bundle,
)
from app.services.pragmatic_meaning_speech_act_intent import CONTRACT_VERSION as V46_CONTRACT


def ref():
    return reference_cross_document_context_graph_bundle()


def payload():
    return ref().model_dump(mode="python")


def invalid(mutator):
    p = deepcopy(payload())
    mutator(p)
    with pytest.raises(ValidationError):
        CrossDocumentContextGraphBundle.model_validate(p)


def test_release_identity():
    assert CORE_RELEASE == "4.7.0"
    assert CONTRACT_VERSION == "sc.core.cross-document-context-graph.v1"
    assert Settings().version == "4.7.0"
    assert ref().release == "4.7.0"


def test_predecessor_is_v46_pragmatic_semantics():
    assert ref().predecessor_contract == V46_CONTRACT
    assert ref().pragmatic_semantics.release == "4.6.0"
    assert ref().pragmatic_semantics.contract == V46_CONTRACT


def test_dependency_order_is_governed():
    assert ref().extends_contracts == EXTENDS_CONTRACTS
    invalid(lambda p: p["extends_contracts"].reverse())


def test_reference_counts():
    c = contract_document()["reference"]
    assert c["documents"] == 3
    assert c["nodes"] == 12
    assert c["edges"] == 11
    assert c["cross_document_edges"] == 2
    assert c["accepted_edges"] == 9
    assert c["proposed_edges"] == 2
    assert c["threads"] == 2
    assert c["canonical_actor_bindings_created"] == 0
    assert c["interpretations"] == 1
    assert c["snapshots"] == 1


def test_document_bindings_cover_three_predecessor_layers():
    contracts = {x.predecessor_contract for x in ref().documents}
    assert "sc.core.context-object-semantic-frame-foundation.v1" in contracts
    assert "sc.core.temporal-spatial-language-grounding.v1" in contracts
    assert "sc.core.pragmatic-meaning-speech-act-communicative-intent.v1" in contracts


def test_document_binding_hashes_preserve_predecessor_sources():
    b = ref()
    grounding = b.pragmatic_semantics.epistemic_semantics.temporal_spatial_grounding
    context = grounding.referential_identity.discourse_semantics.context_semantics
    by_id = {x.document_id: x for x in b.documents}
    assert by_id["document:context-reference:v1"].content_sha256 == context.source_bindings[0].content_sha256
    assert by_id["document:grounding-reference:v1"].content_sha256 == grounding.source_excerpts[0].content_sha256
    assert by_id["document:pragmatic-hearing:v1"].content_sha256 == b.pragmatic_semantics.source_excerpts[0].content_sha256


def test_document_hash_tamper_rejected():
    invalid(lambda p: p["documents"][0].__setitem__("content_sha256", "0" * 64))


def test_nodes_preserve_upstream_semantics():
    assert all(n.upstream_object_immutable for n in ref().nodes)
    assert all(n.graph_node_does_not_change_upstream_semantics for n in ref().nodes)


def test_document_nodes_are_first_class():
    docs = [n for n in ref().nodes if n.node_type == ContextNodeType.document]
    assert len(docs) == 3
    assert {n.object_ref for n in docs} == {d.document_id for d in ref().documents}


def test_reference_graph_contains_context_ministry_and_proposal_mentions():
    by_id = {n.node_id: n for n in ref().nodes}
    assert by_id["node:mention:ministry"].object_ref == "mention:ministry"
    assert by_id["node:mention:proposal"].object_ref == "mention:proposal"


def test_reference_graph_contains_temporal_and_spatial_grounding_nodes():
    by_id = {n.node_id: n for n in ref().nodes}
    assert by_id["node:place:brussels"].object_ref == "spatial-anchor:brussels-source-place"
    assert by_id["node:time:2025"].object_ref == "temporal-anchor:calendar-year:2025"
    assert by_id["node:time:2026"].object_ref == "temporal-anchor:calendar-year:2026"


def test_reference_graph_contains_pragmatic_nodes():
    by_id = {n.node_id: n for n in ref().nodes}
    assert by_id["node:participant:agency"].object_ref == "participant:agency-speaker"
    assert by_id["node:speech-act:warning"].object_ref == "speech-act:warn-disruption"
    assert by_id["node:intent:alert"].object_ref == "intent:alert-disruption"


def test_temporal_continuity_preserves_derivation_without_event_truth():
    edge = next(x for x in ref().edges if x.edge_id == "edge:2025:2026")
    assert edge.edge_type == ContextEdgeType.contextual_continuity
    assert edge.basis == RelationBasis.temporal_alignment
    assert edge.confidence == 1.0
    assert edge.relation_is_contextual_not_truth_verdict is True
    assert edge.metadata["derivation"] == "+P1Y"


def test_warning_to_alert_edge_preserves_pragmatic_link():
    edge = next(x for x in ref().edges if x.edge_id == "edge:warning:alert")
    assert edge.edge_type == ContextEdgeType.pragmatically_realizes
    assert edge.state == GraphReviewState.accepted
    assert edge.reviewer_ref == "reviewer:context-graph:v1"


def test_actor_continuity_is_proposed_not_identity_merge():
    edge = next(x for x in ref().edges if x.edge_id == "edge:ministry:agency:candidate")
    assert edge.cross_document is True
    assert edge.edge_type == ContextEdgeType.candidate_actor_continuity
    assert edge.state == GraphReviewState.proposed
    assert edge.confidence == 0.42
    assert edge.relation_does_not_establish_canonical_identity is True


def test_topic_continuity_is_proposed_not_object_equivalence():
    edge = next(x for x in ref().edges if x.edge_id == "edge:proposal:measure:candidate")
    assert edge.cross_document is True
    assert edge.edge_type == ContextEdgeType.candidate_topic_continuity
    assert edge.state == GraphReviewState.proposed
    assert edge.confidence == 0.36
    assert "not asserted to be the same object" in edge.metadata["reason"]


def test_cross_document_edges_span_distinct_documents():
    nodes = {n.node_id: n for n in ref().nodes}
    for edge in ref().edges:
        if edge.cross_document:
            assert nodes[edge.source_node_ref].document_ref != nodes[edge.target_node_ref].document_ref


def test_cross_document_edge_same_document_rejected():
    p = payload()
    edge = next(x for x in p["edges"] if x["edge_id"] == "edge:ministry:agency:candidate")
    edge["target_node_ref"] = "node:mention:proposal"
    with pytest.raises(ValidationError):
        CrossDocumentContextGraphBundle.model_validate(p)


def test_accepted_edge_requires_reviewer():
    e = next(x for x in ref().edges if x.state == GraphReviewState.accepted).model_dump(mode="python")
    e["reviewer_ref"] = None
    with pytest.raises(ValidationError):
        ContextGraphEdge.model_validate(e)


def test_proposed_edge_may_preserve_no_reviewer():
    e = next(x for x in ref().edges if x.state == GraphReviewState.proposed)
    assert e.reviewer_ref is None


def test_edge_endpoints_must_resolve():
    invalid(lambda p: p["edges"][0].__setitem__("source_node_ref", "node:missing"))


def test_edge_provenance_must_resolve():
    invalid(lambda p: p["edges"][0].__setitem__("provenance_ref", "prov:missing"))


def test_non_document_node_must_reference_governed_predecessor_object():
    idx = next(i for i, x in enumerate(payload()["nodes"]) if x["node_type"] != "document")
    invalid(lambda p: p["nodes"][idx].__setitem__("object_ref", "object:invented"))


def test_document_node_must_reference_document_binding():
    invalid(lambda p: p["nodes"][0].__setitem__("object_ref", "document:missing"))


def test_node_document_ref_must_resolve():
    invalid(lambda p: p["nodes"][3].__setitem__("document_ref", "document:missing"))


def test_actor_thread_is_cross_document_hypothesis():
    t = next(x for x in ref().threads if x.thread_type == ContextThreadType.actor_continuity)
    assert t.state == GraphReviewState.proposed
    assert len(set(t.document_refs)) == 2
    assert "same-actor:ministry-agency" in t.unresolved_refs
    assert t.thread_is_contextual_hypothesis_not_identity_fact is True


def test_topic_thread_preserves_claim_non_equivalence():
    t = next(x for x in ref().threads if x.thread_type == ContextThreadType.topic_continuity)
    assert t.state == GraphReviewState.proposed
    assert "same-object:proposal-measure" in t.unresolved_refs
    assert t.thread_does_not_establish_claim_truth is True


def test_thread_requires_two_distinct_documents():
    t = ref().threads[0].model_dump(mode="python")
    t["document_refs"] = ["document:context-reference:v1", "document:context-reference:v1"]
    with pytest.raises(ValidationError):
        CrossDocumentContextThread.model_validate(t)


def test_accepted_thread_requires_reviewer():
    t = ref().threads[0].model_dump(mode="python")
    t["state"] = "accepted"
    t["reviewer_ref"] = None
    with pytest.raises(ValidationError):
        CrossDocumentContextThread.model_validate(t)


def test_thread_document_refs_must_resolve():
    invalid(lambda p: p["threads"][0]["document_refs"].append("document:missing"))


def test_thread_node_refs_must_resolve():
    invalid(lambda p: p["threads"][0]["node_refs"].append("node:missing"))


def test_thread_edge_refs_must_resolve():
    invalid(lambda p: p["threads"][0]["edge_refs"].append("edge:missing"))


def test_interpretation_spans_all_three_documents():
    i = ref().interpretations[0]
    assert len(i.document_refs) == 3
    assert set(i.thread_refs) == {x.thread_id for x in ref().threads}
    assert "same-actor:ministry-agency" in i.unresolved_refs


def test_accepted_interpretation_requires_reviewer():
    i = ref().interpretations[0].model_dump(mode="python")
    i["reviewer_ref"] = None
    with pytest.raises(ValidationError):
        ContextGraphInterpretation.model_validate(i)


def test_interpretation_predecessor_ref_must_resolve():
    invalid(lambda p: p["interpretations"][0]["predecessor_pragmatic_interpretation_refs"].__setitem__(0, "interpretation:missing"))


def test_interpretation_graph_refs_must_resolve():
    invalid(lambda p: p["interpretations"][0]["node_refs"].append("node:missing"))
    invalid(lambda p: p["interpretations"][0]["edge_refs"].append("edge:missing"))
    invalid(lambda p: p["interpretations"][0]["thread_refs"].append("thread:missing"))


def test_snapshot_is_immutable_and_supersedable():
    s = ref().snapshots[0]
    assert s.immutable is True
    assert s.supersedable is True
    assert s.snapshot_does_not_freeze_truth_identity_or_authority is True


def test_snapshot_binds_exact_predecessor_fingerprint():
    assert ref().snapshots[0].predecessor_fingerprint_sha256 == ref().pragmatic_semantics.fingerprint()


def test_snapshot_predecessor_tamper_rejected():
    invalid(lambda p: p["snapshots"][0].__setitem__("predecessor_fingerprint_sha256", "0" * 64))


def test_snapshot_interpretation_ref_must_resolve():
    invalid(lambda p: p["snapshots"][0]["interpretation_refs"].append("interpretation:missing"))


def test_provenance_subject_refs_must_resolve():
    invalid(lambda p: p["provenance_records"][0]["subject_refs"].append("edge:missing"))


def test_policy_preserves_context_graph_boundaries():
    p = ref().policy
    assert p.graph_is_contextual_index_not_truth_store is True
    assert p.predecessor_objects_remain_immutable is True
    assert p.cross_document_links_preserve_uncertainty is True
    assert p.canonical_identity_requires_identity_authority is True
    assert p.evidence_validity_requires_evidence_workflow is True
    assert p.source_authority_is_not_inferred_from_connectivity is True
    assert p.graph_density_is_not_confidence is True


def test_policy_forbids_authoritative_graph_mutation():
    p = ref().policy
    assert p.identity_graph_mutation_authorized is False
    assert p.evidence_graph_mutation_authorized is False
    assert p.knowledge_graph_mutation_authorized is False
    assert p.predecessor_context_rewrite_authorized is False


def test_contract_boundaries_are_explicit():
    b = contract_document()["boundaries"]
    assert b["context_graph_establishes_world_truth"] is False
    assert b["graph_connectivity_establishes_source_authority"] is False
    assert b["cross_document_link_establishes_canonical_identity"] is False
    assert b["candidate_actor_continuity_merges_entities"] is False
    assert b["graph_density_is_confidence"] is False
    assert b["accepted_context_edge_establishes_evidence_validity"] is False
    assert b["accepted_graph_interpretation_rewrites_v460_predecessor"] is False


def test_contract_graph_mutation_boundaries_are_false():
    b = contract_document()["boundaries"]
    assert b["identity_graph_mutation_performed"] is False
    assert b["evidence_graph_mutation_performed"] is False
    assert b["knowledge_graph_mutation_performed"] is False


def test_roadmap_handoff_is_explicit():
    r = contract_document()["roadmap_integration"]
    assert r["extends_v460_pragmatic_meaning_speech_act_intent"] is True
    assert r["integrates_v410_through_v460_contextual_semantics"] is True
    assert r["prepares_v480_multilingual_context_alignment"] is True
    assert r["prepares_v490_contextual_semantic_evaluation"] is True
    assert r["prepares_v4100_unified_contextual_intelligence_runtime"] is True


def test_fingerprint_is_deterministic():
    assert ref().fingerprint() == reference_cross_document_context_graph_bundle().fingerprint()
    assert len(ref().fingerprint()) == 64


def test_contract_fingerprint_matches_bundle():
    assert contract_document()["reference"]["bundle_fingerprint_sha256"] == ref().fingerprint()


def test_all_ids_are_unique():
    assert len({x.document_id for x in ref().documents}) == len(ref().documents)
    assert len({x.node_id for x in ref().nodes}) == len(ref().nodes)
    assert len({x.edge_id for x in ref().edges}) == len(ref().edges)
    assert len({x.thread_id for x in ref().threads}) == len(ref().threads)


def test_duplicate_node_id_rejected():
    invalid(lambda p: p["nodes"].append(deepcopy(p["nodes"][0])))


def test_duplicate_edge_id_rejected():
    invalid(lambda p: p["edges"].append(deepcopy(p["edges"][0])))


def test_direct_router_contract_matches_service_contract():
    assert api.public_contract() == contract_document()
    assert api.contract() == contract_document()


def test_direct_router_reference_returns_bundle():
    out = api.reference()
    assert out["ok"] is True
    assert out["bundle"]["release"] == "4.7.0"
    assert out["bundle_fingerprint_sha256"] == ref().fingerprint()


def test_direct_router_validate_edge():
    out = api.validate_edge(ref().edges[0])
    assert out["ok"] is True
    assert len(out["fingerprint_sha256"]) == 64


def test_direct_router_validate_thread():
    out = api.validate_thread(ref().threads[0])
    assert out["ok"] is True
    assert len(out["fingerprint_sha256"]) == 64


def test_direct_router_validate_interpretation():
    out = api.validate_interpretation(ref().interpretations[0])
    assert out["ok"] is True
    assert len(out["fingerprint_sha256"]) == 64


def test_direct_router_validate_bundle():
    out = api.validate_bundle(ref())
    assert out["ok"] is True
    assert out["fingerprint_sha256"] == ref().fingerprint()


def test_model_schema_includes_core_graph_objects():
    schema = CrossDocumentContextGraphBundle.model_json_schema()
    defs = schema["$defs"]
    for name in ["ContextDocumentBinding", "ContextGraphNode", "ContextGraphEdge", "CrossDocumentContextThread", "ContextGraphInterpretation", "CrossDocumentContextGraphSnapshot"]:
        assert name in defs


def test_main_app_mounts_v47_routes():
    from app.main import create_app
    paths = {route.path for route in create_app().routes}
    assert "/v1/context-graph/contract" in paths
    assert "/public/v1/context-graph/contract" in paths
    assert "/v1/context-graph/reference" in paths



def test_reference_node_query_filters_by_type_and_document():
    out = api.reference_nodes(node_type=ContextNodeType.temporal_anchor, document_ref="document:grounding-reference:v1")
    assert out["ok"] is True
    assert out["count"] == 2


def test_reference_edge_query_can_surface_cross_document_hypotheses():
    out = api.reference_edges(cross_document=True, state=GraphReviewState.proposed)
    assert out["ok"] is True
    assert out["count"] == 2
    assert {x["edge_type"] for x in out["items"]} == {"candidate-actor-continuity", "candidate-topic-continuity"}


def test_reference_thread_query_preserves_proposed_state():
    out = api.reference_threads(state=GraphReviewState.proposed)
    assert out["ok"] is True
    assert out["count"] == 2
