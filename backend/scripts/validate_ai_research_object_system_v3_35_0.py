#!/usr/bin/env python3

from app.services.ai_research_object_system import (
    CONTRACT_VERSION,
    AIResearchLineageQuery,
    AIResearchRelationshipType,
    LineageDirection,
    contract_document,
    reference_unified_ai_research_bundle,
    trace_lineage,
)

doc = contract_document()
assert doc["release"] == "3.35.0"
assert doc["contract"] == CONTRACT_VERSION
assert len(doc["unifies"]) == 8
assert doc["capabilities"]["canonical_cross_contract_identity"] is True
assert doc["capabilities"]["typed_relationship_graph"] is True
assert doc["capabilities"]["portable_ai_research_packages"] is True
assert doc["integration"]["core_duplicates_source_payloads"] is False
assert doc["boundaries"]["core_executes_ai_jobs"] is False

bundle = reference_unified_ai_research_bundle()
assert len(bundle.registry.objects) == 13
assert len(bundle.graph.relationships) == 17
assert len(bundle.fingerprint()) == 64
assert bundle.snapshot.source_release_refs[-1] == "v3.34.0"

upstream = trace_lineage(
    bundle.graph,
    AIResearchLineageQuery(
        start_object_ref="monitoring-snapshot:reference:current",
        direction=LineageDirection.upstream,
        max_depth=4,
    ),
)
assert "ai-model-version:reference-classifier:1.0.0" in upstream.object_refs
assert "dataset-version:reference-classification:v1" in upstream.object_refs
assert "robustness-run:reference-classifier-noise:001" in upstream.object_refs

prompt_only = trace_lineage(
    bundle.graph,
    AIResearchLineageQuery(
        start_object_ref="inference-run:reference-classifier:001",
        direction=LineageDirection.upstream,
        relationship_types=[AIResearchRelationshipType.uses_prompt],
        max_depth=2,
    ),
)
assert prompt_only.object_refs[-1] == "prompt-version:research-evidence-synthesis:1.0.0"

downstream = trace_lineage(
    bundle.graph,
    AIResearchLineageQuery(
        start_object_ref="ai-model-version:reference-classifier:1.0.0",
        direction=LineageDirection.downstream,
        max_depth=1,
    ),
)
assert "inference-run:reference-classifier:001" in downstream.object_refs
assert "evaluation-run:reference-classifier:001" in downstream.object_refs

print("PASS - Platform Core v3.35.0 Unified AI Research Object System")
print(f"CONTRACT={CONTRACT_VERSION}")
print("SOURCE_AI_CONTRACTS_UNIFIED=8")
print("CANONICAL_CROSS_CONTRACT_IDENTITY=enabled")
print("REFERENCE_ONLY_PAYLOAD_MODE=enabled")
print("TYPED_RELATIONSHIP_GRAPH=enabled")
print("UPSTREAM_LINEAGE=enabled")
print("DOWNSTREAM_LINEAGE=enabled")
print("RELATIONSHIP_FILTERED_LINEAGE=enabled")
print("IMMUTABLE_SNAPSHOTS=enabled")
print("PORTABLE_AI_RESEARCH_PACKAGES=enabled")
print("CORE_DUPLICATES_SOURCE_PAYLOADS=false")
print("CORE_EXECUTES_AI_JOBS=false")
print("CORE_CERTIFIES_SCIENTIFIC_VALIDITY=false")
