from copy import deepcopy

import pytest
from pydantic import ValidationError

from app.services.unified_runtime_api import (
    CONTRACT_VERSION,
    REFERENCE_JULIA_ADAPTER,
    REFERENCE_JULIA_RUNTIME,
    REFERENCE_R_ADAPTER,
    REFERENCE_R_RUNTIME,
    ProductId,
    ProductIntegrationState,
    ProductRuntimeIntegrationProfile,
    ProductRuntimeReceipt,
    ReceiptStatus,
    ResolutionMode,
    RuntimeAction,
    RuntimeAvailability,
    RuntimeCapability,
    RuntimeResolutionCandidate,
    UnifiedRuntimeAPIBundle,
    UnifiedRuntimeCatalog,
    UnifiedRuntimeCatalogEntry,
    UnifiedRuntimeInput,
    UnifiedRuntimeInvocation,
    UnifiedRuntimeOutputContract,
    UnifiedRuntimeRequest,
    UnifiedRuntimeResolution,
    build_invocation,
    contract_document,
    reference_product_profiles,
    reference_runtime_catalog,
    reference_unified_runtime_api_bundle,
    resolve_runtime_request,
    to_scientific_unified_runtime_artifact,
)


def ref_bundle():
    return reference_unified_runtime_api_bundle()


def ref_catalog():
    return reference_runtime_catalog()


def ref_profiles():
    return reference_product_profiles()


def profile(product_id):
    return next(item for item in ref_profiles() if item.product_id == product_id)


def test_contract_identity():
    doc = contract_document()
    assert doc["release"] == "3.44.0"
    assert doc["contract"] == CONTRACT_VERSION


def test_contract_links_v343_security():
    assert "sc.core.runtime-security-governance.v1" in contract_document()["depends_on"]


def test_contract_links_v342_reproduction():
    assert "sc.core.verification-reproduction-engine.v1" in contract_document()["depends_on"]


def test_contract_links_v341_environment():
    assert "sc.core.reproducible-environment-package.v1" in contract_document()["depends_on"]


def test_contract_links_v340_workflow():
    assert "sc.core.cross-runtime-research-workflow.v1" in contract_document()["depends_on"]


def test_contract_links_v339_interchange():
    assert "sc.core.runtime-data-interchange.v1" in contract_document()["depends_on"]


def test_reference_catalog_has_r_and_julia():
    refs = {item.runtime_ref for item in ref_catalog().entries}
    assert refs == {REFERENCE_R_RUNTIME, REFERENCE_JULIA_RUNTIME}


def test_reference_r_entry_version_and_adapter():
    item = next(x for x in ref_catalog().entries if x.runtime_ref == REFERENCE_R_RUNTIME)
    assert item.runtime_version == "1.0.0"
    assert item.runtime_adapter_ref == REFERENCE_R_ADAPTER


def test_reference_julia_entry_version_and_adapter():
    item = next(x for x in ref_catalog().entries if x.runtime_ref == REFERENCE_JULIA_RUNTIME)
    assert item.runtime_version == "0.3.0"
    assert item.runtime_adapter_ref == REFERENCE_JULIA_ADAPTER


def test_r_catalog_capabilities_include_regression():
    item = next(x for x in ref_catalog().entries if x.runtime_ref == REFERENCE_R_RUNTIME)
    assert RuntimeCapability.regression in item.capabilities


def test_julia_catalog_capabilities_include_matrix():
    item = next(x for x in ref_catalog().entries if x.runtime_ref == REFERENCE_JULIA_RUNTIME)
    assert RuntimeCapability.matrix_compute in item.capabilities


def test_r_catalog_formats_are_json_csv():
    item = next(x for x in ref_catalog().entries if x.runtime_ref == REFERENCE_R_RUNTIME)
    assert item.readable_formats == ["json", "csv"]
    assert item.writable_formats == ["json", "csv"]


def test_julia_catalog_format_is_json():
    item = next(x for x in ref_catalog().entries if x.runtime_ref == REFERENCE_JULIA_RUNTIME)
    assert item.readable_formats == ["json"]
    assert item.writable_formats == ["json"]


def test_catalog_entry_rejects_duplicate_capabilities():
    item = ref_catalog().entries[0].model_dump(mode="python")
    item["capabilities"].append(item["capabilities"][0])
    with pytest.raises(ValidationError):
        UnifiedRuntimeCatalogEntry.model_validate(item)


def test_catalog_entry_rejects_duplicate_operations():
    item = ref_catalog().entries[0].model_dump(mode="python")
    item["operations"].append(item["operations"][0])
    with pytest.raises(ValidationError):
        UnifiedRuntimeCatalogEntry.model_validate(item)


def test_catalog_entry_rejects_duplicate_read_formats():
    item = ref_catalog().entries[0].model_dump(mode="python")
    item["readable_formats"].append(item["readable_formats"][0])
    with pytest.raises(ValidationError):
        UnifiedRuntimeCatalogEntry.model_validate(item)


def test_catalog_entry_rejects_duplicate_write_formats():
    item = ref_catalog().entries[0].model_dump(mode="python")
    item["writable_formats"].append(item["writable_formats"][0])
    with pytest.raises(ValidationError):
        UnifiedRuntimeCatalogEntry.model_validate(item)


def test_catalog_entry_fingerprint_ignores_availability():
    item = ref_catalog().entries[0]
    other = deepcopy(item)
    other.availability = RuntimeAvailability.degraded
    assert item.fingerprint() == other.fingerprint()


def test_catalog_requires_entries():
    with pytest.raises(ValidationError):
        UnifiedRuntimeCatalog(catalog_id="catalog:test", entries=[])


def test_catalog_rejects_duplicate_entry_ids():
    item = ref_catalog().entries[0]
    with pytest.raises(ValidationError):
        UnifiedRuntimeCatalog(catalog_id="catalog:test", entries=[item, deepcopy(item)])


def test_catalog_rejects_duplicate_runtime_refs():
    items = deepcopy(ref_catalog().entries)
    items[1].runtime_ref = items[0].runtime_ref
    with pytest.raises(ValidationError):
        UnifiedRuntimeCatalog(catalog_id="catalog:test", entries=items)


def test_catalog_rejects_duplicate_adapter_refs():
    items = deepcopy(ref_catalog().entries)
    items[1].runtime_adapter_ref = items[0].runtime_adapter_ref
    with pytest.raises(ValidationError):
        UnifiedRuntimeCatalog(catalog_id="catalog:test", entries=items)


def test_catalog_fingerprint_stable():
    catalog = ref_catalog()
    assert catalog.fingerprint() == deepcopy(catalog).fingerprint()
    assert len(catalog.fingerprint()) == 64


def test_reference_profiles_are_workspace_lab_workbench():
    assert [x.product_id for x in ref_profiles()] == [
        ProductId.workspace,
        ProductId.research_lab,
        ProductId.workbench,
    ]


def test_workspace_profile_is_primary_orchestrator():
    item = profile(ProductId.workspace)
    assert item.metadata["role"] == "primary-runtime-orchestrator"
    assert RuntimeAction.reproduce in item.allowed_actions


def test_lab_profile_supports_statistical_analysis():
    item = profile(ProductId.research_lab)
    assert RuntimeAction.statistical_analysis in item.allowed_actions
    assert REFERENCE_R_RUNTIME in item.allowed_runtime_refs


def test_workbench_profile_supports_julia_matrix_multiply():
    item = profile(ProductId.workbench)
    assert "matrix_multiply" in item.allowed_operations[REFERENCE_JULIA_RUNTIME]


def test_product_profile_requires_actions():
    data = profile(ProductId.workspace).model_dump(mode="python")
    data["allowed_actions"] = []
    with pytest.raises(ValidationError):
        ProductRuntimeIntegrationProfile.model_validate(data)


def test_product_profile_rejects_duplicate_actions():
    data = profile(ProductId.workspace).model_dump(mode="python")
    data["allowed_actions"].append(data["allowed_actions"][0])
    with pytest.raises(ValidationError):
        ProductRuntimeIntegrationProfile.model_validate(data)


def test_product_profile_rejects_duplicate_runtime_refs():
    data = profile(ProductId.workspace).model_dump(mode="python")
    data["allowed_runtime_refs"].append(data["allowed_runtime_refs"][0])
    with pytest.raises(ValidationError):
        ProductRuntimeIntegrationProfile.model_validate(data)


def test_product_profile_rejects_unknown_operation_runtime():
    data = profile(ProductId.workspace).model_dump(mode="python")
    data["allowed_operations"]["runtime:missing"] = ["op"]
    with pytest.raises(ValidationError):
        ProductRuntimeIntegrationProfile.model_validate(data)


def test_product_profile_rejects_duplicate_operations():
    data = profile(ProductId.workspace).model_dump(mode="python")
    data["allowed_operations"][REFERENCE_R_RUNTIME] = ["mean", "mean"]
    with pytest.raises(ValidationError):
        ProductRuntimeIntegrationProfile.model_validate(data)


def test_product_profile_fingerprint_ignores_state():
    item = profile(ProductId.workspace)
    other = deepcopy(item)
    other.state = ProductIntegrationState.suspended
    assert item.fingerprint() == other.fingerprint()


def test_runtime_input_requires_source():
    with pytest.raises(ValidationError):
        UnifiedRuntimeInput(input_id="input:test", logical_data_ref="logical:test")


def test_runtime_input_accepts_artifact():
    item = UnifiedRuntimeInput(input_id="input:test", logical_data_ref="logical:test", artifact_ref="artifact:test")
    assert item.artifact_ref == "artifact:test"


def test_runtime_input_accepts_result():
    item = UnifiedRuntimeInput(input_id="input:test", logical_data_ref="logical:test", result_ref="result:test")
    assert item.result_ref == "result:test"


def test_output_contract_requires_kind():
    with pytest.raises(ValidationError):
        UnifiedRuntimeOutputContract(output_id="output:test", logical_data_ref="logical:test")


def test_output_contract_accepts_result_kind():
    item = UnifiedRuntimeOutputContract(output_id="output:test", logical_data_ref="logical:test", expected_result_kind="metric")
    assert item.expected_result_kind == "metric"


def test_execute_request_requires_operation():
    with pytest.raises(ValidationError):
        UnifiedRuntimeRequest(
            runtime_request_id="request:test",
            product_id=ProductId.workspace,
            action=RuntimeAction.execute,
            capability=RuntimeCapability.numerical_compute,
        )


def test_statistical_request_requires_operation():
    with pytest.raises(ValidationError):
        UnifiedRuntimeRequest(
            runtime_request_id="request:test",
            product_id=ProductId.research_lab,
            action=RuntimeAction.statistical_analysis,
            capability=RuntimeCapability.statistical_analysis,
        )


def test_workflow_request_requires_workflow_ref():
    with pytest.raises(ValidationError):
        UnifiedRuntimeRequest(
            runtime_request_id="request:test",
            product_id=ProductId.workspace,
            action=RuntimeAction.workflow,
            capability=RuntimeCapability.workflow_execution,
        )


def test_reproduce_request_requires_plan_ref():
    with pytest.raises(ValidationError):
        UnifiedRuntimeRequest(
            runtime_request_id="request:test",
            product_id=ProductId.workspace,
            action=RuntimeAction.reproduce,
            capability=RuntimeCapability.reproduction,
        )


def test_request_rejects_duplicate_input_ids():
    data = ref_bundle().request.model_dump(mode="python")
    data["inputs"] = [data["inputs"][0], deepcopy(data["inputs"][0])]
    with pytest.raises(ValidationError):
        UnifiedRuntimeRequest.model_validate(data)


def test_request_rejects_duplicate_output_ids():
    data = ref_bundle().request.model_dump(mode="python")
    data["outputs"] = [data["outputs"][0], deepcopy(data["outputs"][0])]
    with pytest.raises(ValidationError):
        UnifiedRuntimeRequest.model_validate(data)


def test_request_fingerprint_ignores_created_at():
    request = ref_bundle().request
    assert request.fingerprint() == deepcopy(request).fingerprint()


def test_candidate_resolution_for_matrix_multiply_returns_julia():
    request = UnifiedRuntimeRequest(
        runtime_request_id="request:matrix",
        product_id=ProductId.workspace,
        action=RuntimeAction.execute,
        capability=RuntimeCapability.matrix_compute,
        operation="matrix_multiply",
    )
    result = resolve_runtime_request(catalog=ref_catalog(), profile=profile(ProductId.workspace), request=request)
    assert result.mode == ResolutionMode.candidate_discovery
    assert [x.runtime_ref for x in result.candidates] == [REFERENCE_JULIA_RUNTIME]
    assert result.bound_runtime_ref is None


def test_candidate_resolution_for_regression_returns_r():
    request = UnifiedRuntimeRequest(
        runtime_request_id="request:regression",
        product_id=ProductId.research_lab,
        action=RuntimeAction.statistical_analysis,
        capability=RuntimeCapability.regression,
        operation="linear_regression",
    )
    result = resolve_runtime_request(catalog=ref_catalog(), profile=profile(ProductId.research_lab), request=request)
    assert result.mode == ResolutionMode.candidate_discovery
    assert [x.runtime_ref for x in result.candidates] == [REFERENCE_R_RUNTIME]


def test_explicit_r_binding_validates_for_regression():
    request = deepcopy(ref_bundle().request)
    result = resolve_runtime_request(catalog=ref_catalog(), profile=profile(ProductId.research_lab), request=request)
    assert result.mode == ResolutionMode.explicit_binding_validated
    assert result.bound_runtime_ref == REFERENCE_R_RUNTIME


def test_explicit_julia_binding_rejected_for_regression():
    request = deepcopy(ref_bundle().request)
    request.explicit_runtime_ref = REFERENCE_JULIA_RUNTIME
    result = resolve_runtime_request(catalog=ref_catalog(), profile=profile(ProductId.research_lab), request=request)
    assert result.mode == ResolutionMode.unresolved
    assert result.candidates == []


def test_action_not_allowed_for_workbench_reproduction():
    request = UnifiedRuntimeRequest(
        runtime_request_id="request:wb-repro",
        product_id=ProductId.workbench,
        action=RuntimeAction.reproduce,
        capability=RuntimeCapability.reproduction,
        reproduction_plan_ref="plan:test",
    )
    result = resolve_runtime_request(catalog=ref_catalog(), profile=profile(ProductId.workbench), request=request)
    assert result.mode == ResolutionMode.unresolved
    assert any("action not allowed" in x for x in result.rejection_reasons)


def test_product_profile_mismatch_unresolved():
    request = deepcopy(ref_bundle().request)
    result = resolve_runtime_request(catalog=ref_catalog(), profile=profile(ProductId.workspace), request=request)
    assert result.mode == ResolutionMode.unresolved
    assert any("product does not match" in x for x in result.rejection_reasons)


def test_unavailable_runtime_excluded_from_candidates():
    catalog = deepcopy(ref_catalog())
    julia = next(x for x in catalog.entries if x.runtime_ref == REFERENCE_JULIA_RUNTIME)
    julia.availability = RuntimeAvailability.unavailable
    request = UnifiedRuntimeRequest(
        runtime_request_id="request:matrix",
        product_id=ProductId.workspace,
        action=RuntimeAction.execute,
        capability=RuntimeCapability.matrix_compute,
        operation="matrix_multiply",
    )
    result = resolve_runtime_request(catalog=catalog, profile=profile(ProductId.workspace), request=request)
    assert result.mode == ResolutionMode.unresolved


def test_resolution_rejects_duplicate_candidates():
    base = ref_bundle().resolution
    data = base.model_dump(mode="python")
    data["candidates"] = [data["candidates"][0], deepcopy(data["candidates"][0])]
    with pytest.raises(ValidationError):
        UnifiedRuntimeResolution.model_validate(data)


def test_candidate_mode_cannot_bind_runtime():
    base = ref_bundle().resolution.model_dump(mode="python")
    base["mode"] = "candidate-discovery"
    base["bound_runtime_ref"] = REFERENCE_R_RUNTIME
    with pytest.raises(ValidationError):
        UnifiedRuntimeResolution.model_validate(base)


def test_explicit_mode_requires_bound_runtime():
    base = ref_bundle().resolution.model_dump(mode="python")
    base["bound_runtime_ref"] = None
    with pytest.raises(ValidationError):
        UnifiedRuntimeResolution.model_validate(base)


def test_unresolved_mode_cannot_contain_candidates():
    base = ref_bundle().resolution.model_dump(mode="python")
    base["mode"] = "unresolved"
    base["bound_runtime_ref"] = None
    with pytest.raises(ValidationError):
        UnifiedRuntimeResolution.model_validate(base)


def test_resolution_fingerprint_stable():
    item = ref_bundle().resolution
    assert item.fingerprint() == deepcopy(item).fingerprint()


def test_build_invocation_requires_explicit_binding():
    request = UnifiedRuntimeRequest(
        runtime_request_id="request:matrix",
        product_id=ProductId.workspace,
        action=RuntimeAction.execute,
        capability=RuntimeCapability.matrix_compute,
        operation="matrix_multiply",
        computational_job_ref="job:test",
        environment_package_ref="environment-package:test",
    )
    resolution = resolve_runtime_request(catalog=ref_catalog(), profile=profile(ProductId.workspace), request=request)
    with pytest.raises(ValueError):
        build_invocation(
            request=request,
            resolution=resolution,
            profile=profile(ProductId.workspace),
            catalog=ref_catalog(),
            security_decision_ref="security-decision:test",
        )


def test_build_invocation_requires_job_ref():
    request = deepcopy(ref_bundle().request)
    request.computational_job_ref = None
    resolution = resolve_runtime_request(catalog=ref_catalog(), profile=profile(ProductId.research_lab), request=request)
    with pytest.raises(ValueError):
        build_invocation(request=request, resolution=resolution, profile=profile(ProductId.research_lab), catalog=ref_catalog(), security_decision_ref="security-decision:test")


def test_build_invocation_requires_environment_package():
    request = deepcopy(ref_bundle().request)
    request.environment_package_ref = None
    resolution = resolve_runtime_request(catalog=ref_catalog(), profile=profile(ProductId.research_lab), request=request)
    with pytest.raises(ValueError):
        build_invocation(request=request, resolution=resolution, profile=profile(ProductId.research_lab), catalog=ref_catalog(), security_decision_ref="security-decision:test")


def test_build_invocation_requires_security_decision():
    bundle = ref_bundle()
    with pytest.raises(ValueError):
        build_invocation(request=bundle.request, resolution=bundle.resolution, profile=profile(ProductId.research_lab), catalog=bundle.catalog, security_decision_ref="")


def test_reference_invocation_binds_r_runtime():
    invocation = ref_bundle().invocation
    assert invocation is not None
    assert invocation.runtime_ref == REFERENCE_R_RUNTIME
    assert invocation.runtime_adapter_ref == REFERENCE_R_ADAPTER


def test_reference_invocation_binds_security_policy_and_decision():
    invocation = ref_bundle().invocation
    assert invocation is not None
    assert invocation.security_policy_ref == "runtime-security-policy:research-standard:v1"
    assert invocation.security_decision_ref == "security-decision:r-regression:reference"


def test_reference_invocation_dispatch_owner_is_workspace():
    invocation = ref_bundle().invocation
    assert invocation is not None
    assert invocation.metadata["dispatch_owner"] == "workspace-or-execution-host"
    assert invocation.metadata["core_dispatched_execution"] is False


def test_invocation_rejects_duplicate_input_refs():
    data = ref_bundle().invocation.model_dump(mode="python")
    data["input_refs"] = ["a", "a"]
    with pytest.raises(ValidationError):
        UnifiedRuntimeInvocation.model_validate(data)


def test_invocation_rejects_duplicate_output_refs():
    data = ref_bundle().invocation.model_dump(mode="python")
    data["output_contract_refs"] = ["a", "a"]
    with pytest.raises(ValidationError):
        UnifiedRuntimeInvocation.model_validate(data)


def test_invocation_fingerprint_stable():
    item = ref_bundle().invocation
    assert item is not None
    assert item.fingerprint() == deepcopy(item).fingerprint()


def test_failed_receipt_requires_error():
    invocation = ref_bundle().invocation
    with pytest.raises(ValidationError):
        ProductRuntimeReceipt(
            receipt_id="receipt:test",
            product_id=ProductId.research_lab,
            invocation_ref=invocation.invocation_id,
            invocation_fingerprint_sha256=invocation.fingerprint(),
            status=ReceiptStatus.failed,
            computational_job_ref=invocation.computational_job_ref,
            runtime_ref=invocation.runtime_ref,
            execution_host_ref=invocation.execution_host_ref,
        )


def test_completed_receipt_cannot_have_error():
    invocation = ref_bundle().invocation
    with pytest.raises(ValidationError):
        ProductRuntimeReceipt(
            receipt_id="receipt:test",
            product_id=ProductId.research_lab,
            invocation_ref=invocation.invocation_id,
            invocation_fingerprint_sha256=invocation.fingerprint(),
            status=ReceiptStatus.completed,
            computational_job_ref=invocation.computational_job_ref,
            runtime_ref=invocation.runtime_ref,
            execution_host_ref=invocation.execution_host_ref,
            error_ref="error:test",
        )


def test_receipt_fingerprint_ignores_completion_time():
    item = ref_bundle().receipts[0]
    assert item.fingerprint() == deepcopy(item).fingerprint()


def test_reference_receipt_completed():
    item = ref_bundle().receipts[0]
    assert item.status == ReceiptStatus.completed
    assert item.security_attestation_ref == "isolation-attestation:r-regression:reference"


def test_bundle_rejects_duplicate_profile_ids():
    data = ref_bundle().model_dump(mode="python")
    data["product_profiles"] = [data["product_profiles"][0], deepcopy(data["product_profiles"][0])]
    with pytest.raises(ValidationError):
        UnifiedRuntimeAPIBundle.model_validate(data)


def test_bundle_requires_matching_product_profile():
    data = ref_bundle().model_dump(mode="python")
    data["product_profiles"] = [x for x in data["product_profiles"] if x["product_id"] != "research-lab"]
    with pytest.raises(ValidationError):
        UnifiedRuntimeAPIBundle.model_validate(data)


def test_bundle_rejects_resolution_request_fingerprint_mismatch():
    data = ref_bundle().model_dump(mode="python")
    data["resolution"]["runtime_request_fingerprint_sha256"] = "f" * 64
    with pytest.raises(ValidationError):
        UnifiedRuntimeAPIBundle.model_validate(data)


def test_bundle_rejects_resolution_profile_mismatch():
    data = ref_bundle().model_dump(mode="python")
    data["resolution"]["product_profile_ref"] = "profile:wrong"
    with pytest.raises(ValidationError):
        UnifiedRuntimeAPIBundle.model_validate(data)


def test_bundle_rejects_resolution_catalog_mismatch():
    data = ref_bundle().model_dump(mode="python")
    data["resolution"]["catalog_ref"] = "catalog:wrong"
    with pytest.raises(ValidationError):
        UnifiedRuntimeAPIBundle.model_validate(data)


def test_bundle_rejects_invocation_request_mismatch():
    data = ref_bundle().model_dump(mode="python")
    data["invocation"]["runtime_request_ref"] = "request:wrong"
    with pytest.raises(ValidationError):
        UnifiedRuntimeAPIBundle.model_validate(data)


def test_bundle_rejects_invocation_resolution_mismatch():
    data = ref_bundle().model_dump(mode="python")
    data["invocation"]["resolution_ref"] = "resolution:wrong"
    with pytest.raises(ValidationError):
        UnifiedRuntimeAPIBundle.model_validate(data)


def test_bundle_rejects_invocation_runtime_mismatch():
    data = ref_bundle().model_dump(mode="python")
    data["invocation"]["runtime_ref"] = REFERENCE_JULIA_RUNTIME
    with pytest.raises(ValidationError):
        UnifiedRuntimeAPIBundle.model_validate(data)


def test_bundle_rejects_invocation_catalog_entry_unknown():
    data = ref_bundle().model_dump(mode="python")
    data["invocation"]["catalog_entry_ref"] = "catalog-entry:missing"
    with pytest.raises(ValidationError):
        UnifiedRuntimeAPIBundle.model_validate(data)


def test_bundle_rejects_receipt_unknown_invocation():
    data = ref_bundle().model_dump(mode="python")
    data["receipts"][0]["invocation_ref"] = "invocation:missing"
    with pytest.raises(ValidationError):
        UnifiedRuntimeAPIBundle.model_validate(data)


def test_bundle_rejects_receipt_fingerprint_mismatch():
    data = ref_bundle().model_dump(mode="python")
    data["receipts"][0]["invocation_fingerprint_sha256"] = "f" * 64
    with pytest.raises(ValidationError):
        UnifiedRuntimeAPIBundle.model_validate(data)


def test_bundle_rejects_receipt_runtime_mismatch():
    data = ref_bundle().model_dump(mode="python")
    data["receipts"][0]["runtime_ref"] = REFERENCE_JULIA_RUNTIME
    with pytest.raises(ValidationError):
        UnifiedRuntimeAPIBundle.model_validate(data)


def test_bundle_rejects_receipt_execution_host_mismatch():
    data = ref_bundle().model_dump(mode="python")
    data["receipts"][0]["execution_host_ref"] = "host:wrong"
    with pytest.raises(ValidationError):
        UnifiedRuntimeAPIBundle.model_validate(data)


def test_bundle_fingerprint_stable():
    bundle = ref_bundle()
    assert bundle.fingerprint() == deepcopy(bundle).fingerprint()
    assert len(bundle.fingerprint()) == 64


def test_scientific_artifact_bridge():
    payload = to_scientific_unified_runtime_artifact(ref_bundle())
    assert payload["artifact_kind"] == "package"
    assert payload["source_contract"] == CONTRACT_VERSION
    assert payload["content_sha256"] == ref_bundle().fingerprint()


def test_scientific_artifact_bridge_validates_v338():
    from app.services.scientific_result_registry import ScientificArtifactRef
    payload = to_scientific_unified_runtime_artifact(ref_bundle())
    item = ScientificArtifactRef.model_validate(payload)
    assert item.source_object_ref == ref_bundle().bundle_id


def test_scientific_artifact_metadata_product_and_runtime():
    payload = to_scientific_unified_runtime_artifact(ref_bundle())
    assert payload["metadata"]["product_id"] == "research-lab"
    assert payload["metadata"]["runtime_ref"] == REFERENCE_R_RUNTIME
    assert payload["metadata"]["receipt_count"] == 1


def test_product_ids_cover_platform_products():
    values = {item.value for item in ProductId}
    assert {
        "workspace", "research-lab", "workbench", "knowledge-library",
        "research-librarian", "decision-studio", "site-intelligence", "catalyst-data",
    }.issubset(values)


def test_runtime_actions_cover_runtime_lifecycle():
    values = {item.value for item in RuntimeAction}
    assert {"execute", "statistical-analysis", "workflow", "interchange", "reproduce", "verify", "inspect"}.issubset(values)


def test_runtime_capabilities_cover_scientific_runtime_surface():
    values = {item.value for item in RuntimeCapability}
    assert {"numerical-compute", "matrix-compute", "statistical-analysis", "regression", "hypothesis-test", "reproduction", "verification"}.issubset(values)


def test_contract_product_states():
    integration = contract_document()["product_integration"]
    assert integration["workspace"] == "contract-ready"
    assert integration["research-lab"] == "contract-ready"
    assert integration["workbench"] == "contract-ready"


def test_contract_does_not_claim_other_product_side_changes():
    doc = contract_document()
    assert doc["boundaries"]["core_claims_product_side_integration_without_product_changes"] is False


def test_core_does_not_autoselect_runtime():
    assert contract_document()["boundaries"]["core_autonomously_selects_runtime"] is False


def test_core_does_not_dispatch_execution():
    doc = contract_document()
    assert doc["boundaries"]["core_dispatches_runtime_execution"] is False
    assert doc["integration"]["workspace_or_execution_host_dispatches"] is True


def test_core_does_not_bypass_security():
    assert contract_document()["boundaries"]["core_bypasses_runtime_security"] is False


def test_core_does_not_replace_product_business_logic():
    assert contract_document()["boundaries"]["core_replaces_product_business_logic"] is False


def test_core_does_not_certify_scientific_validity():
    assert contract_document()["boundaries"]["core_certifies_scientific_validity"] is False


def test_reference_resolution_is_explicit_r_binding():
    doc = contract_document()
    assert doc["reference"]["reference_resolution_mode"] == "explicit-binding-validated"
    assert doc["reference"]["reference_bound_runtime_ref"] == REFERENCE_R_RUNTIME


def test_reference_receipt_status_completed():
    assert contract_document()["reference"]["reference_receipt_status"] == "completed"


def test_matrix_candidate_discovery_is_julia_only():
    doc = contract_document()
    assert doc["reference"]["matrix_candidate_runtime_refs"] == [REFERENCE_JULIA_RUNTIME]
    assert doc["reference"]["matrix_candidate_resolution_mode"] == "candidate-discovery"


def test_reference_bundle_hash_is_sha256():
    assert len(contract_document()["reference"]["bundle_fingerprint_sha256"]) == 64


def test_requested_unsupported_format_eliminates_candidate():
    request = UnifiedRuntimeRequest(
        runtime_request_id="request:parquet-matrix",
        product_id=ProductId.workspace,
        action=RuntimeAction.execute,
        capability=RuntimeCapability.matrix_compute,
        operation="matrix_multiply",
        requested_formats=["parquet"],
    )
    result = resolve_runtime_request(catalog=ref_catalog(), profile=profile(ProductId.workspace), request=request)
    assert result.mode == ResolutionMode.unresolved
    assert result.candidates == []


def test_build_invocation_rejects_resolution_request_fingerprint_mismatch():
    bundle = ref_bundle()
    resolution = deepcopy(bundle.resolution)
    resolution.runtime_request_fingerprint_sha256 = "f" * 64
    with pytest.raises(ValueError):
        build_invocation(
            request=bundle.request,
            resolution=resolution,
            profile=profile(ProductId.research_lab),
            catalog=bundle.catalog,
            security_decision_ref="security-decision:test",
        )


def test_build_invocation_rejects_resolution_profile_mismatch():
    bundle = ref_bundle()
    resolution = deepcopy(bundle.resolution)
    resolution.product_profile_ref = "profile:wrong"
    with pytest.raises(ValueError):
        build_invocation(
            request=bundle.request,
            resolution=resolution,
            profile=profile(ProductId.research_lab),
            catalog=bundle.catalog,
            security_decision_ref="security-decision:test",
        )


def test_build_invocation_rejects_resolution_catalog_mismatch():
    bundle = ref_bundle()
    resolution = deepcopy(bundle.resolution)
    resolution.catalog_ref = "catalog:wrong"
    with pytest.raises(ValueError):
        build_invocation(
            request=bundle.request,
            resolution=resolution,
            profile=profile(ProductId.research_lab),
            catalog=bundle.catalog,
            security_decision_ref="security-decision:test",
        )


def test_build_invocation_rejects_request_explicit_runtime_mismatch():
    bundle = ref_bundle()
    request = deepcopy(bundle.request)
    request.explicit_runtime_ref = REFERENCE_JULIA_RUNTIME
    with pytest.raises(ValueError):
        build_invocation(
            request=request,
            resolution=bundle.resolution,
            profile=profile(ProductId.research_lab),
            catalog=bundle.catalog,
            security_decision_ref="security-decision:test",
        )
