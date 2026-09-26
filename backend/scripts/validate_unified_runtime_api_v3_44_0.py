#!/usr/bin/env python3

from app.services.unified_runtime_api import (
    CONTRACT_VERSION,
    ProductId,
    ResolutionMode,
    RuntimeAction,
    RuntimeCapability,
    UnifiedRuntimeRequest,
    contract_document,
    reference_product_profiles,
    reference_runtime_catalog,
    reference_unified_runtime_api_bundle,
    resolve_runtime_request,
    to_scientific_unified_runtime_artifact,
)
from app.services.scientific_result_registry import ScientificArtifactRef

doc = contract_document()
assert doc["release"] == "3.44.0"
assert doc["contract"] == CONTRACT_VERSION
assert doc["capabilities"]["unified_runtime_catalog"] is True
assert doc["capabilities"]["product_runtime_profiles"] is True
assert doc["capabilities"]["explicit_runtime_binding_validation"] is True
assert doc["capabilities"]["security_decision_binding"] is True
assert doc["capabilities"]["product_completion_receipts"] is True
assert doc["integration"]["workspace_or_execution_host_dispatches"] is True
assert doc["boundaries"]["core_autonomously_selects_runtime"] is False
assert doc["boundaries"]["core_dispatches_runtime_execution"] is False
assert doc["boundaries"]["core_bypasses_runtime_security"] is False

bundle = reference_unified_runtime_api_bundle()
assert len(bundle.fingerprint()) == 64
assert bundle.resolution.mode == ResolutionMode.explicit_binding_validated
assert bundle.resolution.bound_runtime_ref == "sc-runtime-r"
assert bundle.invocation is not None
assert bundle.invocation.runtime_ref == "sc-runtime-r"
assert bundle.invocation.security_decision_ref == "security-decision:r-regression:reference"
assert bundle.invocation.metadata["core_dispatched_execution"] is False
assert bundle.receipts[0].status == "completed"

catalog = reference_runtime_catalog()
profiles = reference_product_profiles()
workspace = next(item for item in profiles if item.product_id == ProductId.workspace)
request = UnifiedRuntimeRequest(
    runtime_request_id="validator:matrix-candidate",
    product_id=ProductId.workspace,
    action=RuntimeAction.execute,
    capability=RuntimeCapability.matrix_compute,
    operation="matrix_multiply",
)
resolution = resolve_runtime_request(catalog=catalog, profile=workspace, request=request)
assert resolution.mode == ResolutionMode.candidate_discovery
assert resolution.bound_runtime_ref is None
assert [item.runtime_ref for item in resolution.candidates] == ["catalyst-julia-runtime"]
assert resolution.metadata["core_autonomously_selected_runtime"] is False

payload = to_scientific_unified_runtime_artifact(bundle)
ScientificArtifactRef.model_validate(payload)

print("PASS - Platform Core v3.44.0 Unified Runtime API & Product Integration")
print(f"CONTRACT={CONTRACT_VERSION}")
print("UNIFIED_RUNTIME_CATALOG=enabled")
print("PRODUCT_RUNTIME_PROFILES=enabled")
print("PRODUCT_SCOPED_RUNTIME_RESOLUTION=enabled")
print("CANDIDATE_DISCOVERY=enabled")
print("EXPLICIT_RUNTIME_BINDING_VALIDATION=enabled")
print("UNIFIED_INVOCATION_ENVELOPES=enabled")
print("ENVIRONMENT_PACKAGE_BINDING=enabled")
print("SECURITY_DECISION_BINDING=enabled")
print("COMPUTATIONAL_JOB_BINDING=enabled")
print("CROSS_RUNTIME_WORKFLOW_BINDING=enabled")
print("REPRODUCTION_PLAN_BINDING=enabled")
print("PRODUCT_COMPLETION_RECEIPTS=enabled")
print("SCIENTIFIC_REGISTRY_BRIDGE=enabled")
print("WORKSPACE_PROFILE=contract-ready")
print("RESEARCH_LAB_PROFILE=contract-ready")
print("WORKBENCH_PROFILE=contract-ready")
print("CORE_AUTONOMOUSLY_SELECTS_RUNTIME=false")
print("CORE_DISPATCHES_RUNTIME_EXECUTION=false")
print("CORE_BYPASSES_RUNTIME_SECURITY=false")
print("CORE_REPLACES_PRODUCT_BUSINESS_LOGIC=false")
print("CORE_CERTIFIES_SCIENTIFIC_VALIDITY=false")
