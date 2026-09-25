from fastapi import APIRouter
from ..services.ai_research_object_system import (
    CORE_RELEASE,
    CONTRACT_VERSION,
    AIResearchObjectRef,
    AIResearchObjectRegistry,
    AIResearchRelationshipGraph,
    AIResearchLineageQuery,
    AIResearchPackageManifest,
    UnifiedAIResearchObjectBundle,
    contract_document,
    reference_unified_ai_research_bundle,
    trace_lineage,
)

router = APIRouter(
    prefix="/api/v1/ai-research-objects",
    tags=["ai-research-objects"],
)
public_router = APIRouter(
    prefix="/public/v1/ai-research-objects",
    tags=["public-ai-research-objects"],
)

@router.get("/contract")
def get_contract():
    return contract_document()

@public_router.get("/contract")
def get_public_contract():
    return contract_document()

@router.get("/reference")
def get_reference():
    bundle = reference_unified_ai_research_bundle()
    return {
        "ok": True,
        "release": CORE_RELEASE,
        "contract": CONTRACT_VERSION,
        "bundle": bundle.model_dump(mode="json", exclude_none=True),
        "bundle_fingerprint_sha256": bundle.fingerprint(),
        "manifest_fingerprint_sha256": bundle.manifest.fingerprint(),
        "registry_fingerprint_sha256": bundle.registry.fingerprint(),
        "graph_fingerprint_sha256": bundle.graph.fingerprint(),
        "snapshot_fingerprint_sha256": bundle.snapshot.fingerprint(),
    }

@router.post("/validate-object-ref")
def validate_object_ref(body: AIResearchObjectRef):
    return {
        "ok": True,
        "release": CORE_RELEASE,
        "contract": CONTRACT_VERSION,
        "object_ref_fingerprint_sha256": body.fingerprint(),
    }

@router.post("/validate-registry")
def validate_registry(body: AIResearchObjectRegistry):
    return {
        "ok": True,
        "release": CORE_RELEASE,
        "contract": CONTRACT_VERSION,
        "registry_fingerprint_sha256": body.fingerprint(),
        "object_count": len(body.objects),
    }

@router.post("/validate-graph")
def validate_graph(body: AIResearchRelationshipGraph):
    return {
        "ok": True,
        "release": CORE_RELEASE,
        "contract": CONTRACT_VERSION,
        "graph_fingerprint_sha256": body.fingerprint(),
        "relationship_count": len(body.relationships),
    }

@router.post("/trace-lineage")
def lineage(body: AIResearchLineageQuery):
    bundle = reference_unified_ai_research_bundle()
    path = trace_lineage(bundle.graph, body)
    return {
        "ok": True,
        "release": CORE_RELEASE,
        "contract": CONTRACT_VERSION,
        "lineage": path.model_dump(mode="json", exclude_none=True),
        "lineage_fingerprint_sha256": path.fingerprint(),
    }

@router.post("/validate-package")
def validate_package(body: AIResearchPackageManifest):
    return {
        "ok": True,
        "release": CORE_RELEASE,
        "contract": CONTRACT_VERSION,
        "package_fingerprint_sha256": body.fingerprint(),
    }

@router.post("/validate-bundle")
def validate_bundle(body: UnifiedAIResearchObjectBundle):
    return {
        "ok": True,
        "release": CORE_RELEASE,
        "contract": CONTRACT_VERSION,
        "bundle_fingerprint_sha256": body.fingerprint(),
    }
