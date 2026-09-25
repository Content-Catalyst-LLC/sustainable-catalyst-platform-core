from copy import deepcopy

import pytest
from pydantic import ValidationError

from app.services.r_runtime_migration import (
    ADAPTER_ID,
    CONTRACT_VERSION,
    LEGACY_ANALYTICAL_PROVIDER_CONTRACT,
    LEGACY_PROVIDER_ID,
    LEGACY_PROVIDER_VERSION,
    RUNTIME_ADAPTER_CONTRACT,
    RUNTIME_ID,
    RUNTIME_VERSION,
    AnalyticsRMigrationPlan,
    RRuntimeIdentity,
    RRuntimeMigrationBundle,
    RRuntimeMigrationState,
    RRuntimeRegistration,
    capability_mappings,
    contract_document,
    reference_r_runtime_migration,
)


def test_contract_identity():
    doc = contract_document()
    assert doc["release"] == "3.36.0"
    assert doc["contract"] == CONTRACT_VERSION
    assert doc["runtime"]["runtime_id"] == "sc-runtime-r"
    assert doc["runtime"]["runtime_version"] == "1.0.0"


def test_legacy_identity_preserved():
    bundle = reference_r_runtime_migration()
    legacy = bundle.migration_plan.legacy_identity
    assert legacy.provider_id == LEGACY_PROVIDER_ID
    assert legacy.provider_version == LEGACY_PROVIDER_VERSION
    assert legacy.provider_contract == LEGACY_ANALYTICAL_PROVIDER_CONTRACT


def test_runtime_identity_is_canonical():
    runtime = reference_r_runtime_migration().migration_plan.runtime_identity
    assert runtime.runtime_id == RUNTIME_ID
    assert runtime.runtime_version == RUNTIME_VERSION
    assert runtime.adapter_id == ADAPTER_ID
    assert runtime.adapter_contract == RUNTIME_ADAPTER_CONTRACT


def test_runtime_identity_rejects_wrong_id():
    with pytest.raises(ValidationError):
        RRuntimeIdentity(runtime_id="analytics-r")


def test_runtime_identity_rejects_wrong_adapter():
    with pytest.raises(ValidationError):
        RRuntimeIdentity(adapter_id="adapter:analytics-r")


def test_six_capabilities_mapped():
    mappings = capability_mappings()
    assert len(mappings) == 6
    assert {x.runtime_operation for x in mappings} == {
        "descriptive_summary",
        "quantile_summary",
        "correlation_matrix",
        "linear_regression",
        "t_test",
        "one_way_anova",
    }


def test_all_initial_capabilities_are_base_r():
    assert all(x.base_r_only for x in capability_mappings())


def test_capability_fingerprints_are_stable():
    for mapping in capability_mappings():
        assert mapping.fingerprint() == deepcopy(mapping).fingerprint()
        assert len(mapping.fingerprint()) == 64


def test_plan_rejects_duplicate_mapping_ids():
    bundle = reference_r_runtime_migration()
    data = bundle.migration_plan.model_dump(mode="python")
    data["capability_mappings"] = [
        data["capability_mappings"][0],
        deepcopy(data["capability_mappings"][0]),
    ]
    with pytest.raises(ValidationError):
        AnalyticsRMigrationPlan.model_validate(data)


def test_plan_rejects_duplicate_operations():
    bundle = reference_r_runtime_migration()
    data = bundle.migration_plan.model_dump(mode="python")
    second = deepcopy(data["capability_mappings"][1])
    second["runtime_operation"] = data["capability_mappings"][0]["runtime_operation"]
    data["capability_mappings"] = [data["capability_mappings"][0], second]
    with pytest.raises(ValidationError):
        AnalyticsRMigrationPlan.model_validate(data)


def test_plan_is_non_destructive():
    plan = reference_r_runtime_migration().migration_plan
    assert plan.destructive_migration is False
    assert plan.preserve_legacy_resolution is True


def test_plan_rejects_destructive_migration():
    bundle = reference_r_runtime_migration()
    data = bundle.migration_plan.model_dump(mode="python")
    data["destructive_migration"] = True
    with pytest.raises(ValidationError):
        AnalyticsRMigrationPlan.model_validate(data)


def test_plan_rejects_duplicate_execution():
    bundle = reference_r_runtime_migration()
    data = bundle.migration_plan.model_dump(mode="python")
    data["duplicate_runtime_execution"] = True
    with pytest.raises(ValidationError):
        AnalyticsRMigrationPlan.model_validate(data)


def test_plan_fingerprint_ignores_state():
    plan = reference_r_runtime_migration().migration_plan
    other = deepcopy(plan)
    other.state = RRuntimeMigrationState.compatibility
    assert plan.fingerprint() == other.fingerprint()


def test_legacy_provider_alias_maps_to_new_runtime():
    bundle = reference_r_runtime_migration()
    aliases = {
        x.legacy_identifier: x.canonical_identifier
        for x in bundle.migration_plan.aliases
    }
    assert aliases["catalyst-analytics-r"] == "sc-runtime-r"


def test_registration_has_all_adapter_methods():
    registration = reference_r_runtime_migration().runtime_registration
    required = {
        "health", "version", "capabilities", "prepare", "execute",
        "cancel", "inspect", "collect_results", "collect_artifacts", "diagnose",
    }
    assert required.issubset(set(registration.adapter_methods))


def test_registration_rejects_missing_adapter_methods():
    bundle = reference_r_runtime_migration()
    data = bundle.runtime_registration.model_dump(mode="python")
    data["adapter_methods"] = ["health"]
    with pytest.raises(ValidationError):
        RRuntimeRegistration.model_validate(data)


def test_registration_requires_capabilities():
    bundle = reference_r_runtime_migration()
    data = bundle.runtime_registration.model_dump(mode="python")
    data["capabilities"] = []
    with pytest.raises(ValidationError):
        RRuntimeRegistration.model_validate(data)


def test_registration_targets_lab_workbench_workspace():
    surfaces = set(reference_r_runtime_migration().runtime_registration.product_surfaces)
    assert {"research-lab", "workbench", "workspace"}.issubset(surfaces)


def test_bundle_requires_mapping_and_registration_capabilities_match():
    bundle = reference_r_runtime_migration()
    registration = deepcopy(bundle.runtime_registration)
    registration.capabilities = registration.capabilities[:-1]
    with pytest.raises(ValidationError):
        RRuntimeMigrationBundle(
            migration_plan=bundle.migration_plan,
            runtime_registration=registration,
        )


def test_bundle_fingerprint_is_stable():
    bundle = reference_r_runtime_migration()
    assert bundle.fingerprint() == deepcopy(bundle).fingerprint()
    assert len(bundle.fingerprint()) == 64


def test_core_does_not_execute_r():
    doc = contract_document()
    assert doc["boundaries"]["core_executes_r_directly"] is False
    assert doc["integration"]["provider_executes_r"] is True


def test_no_arbitrary_r_or_job_package_install():
    doc = contract_document()
    assert doc["boundaries"]["arbitrary_r_source_execution"] is False
    assert doc["boundaries"]["core_installs_r_packages_during_jobs"] is False


def test_core_does_not_select_method_or_certify_validity():
    doc = contract_document()
    assert doc["boundaries"]["core_selects_statistical_method"] is False
    assert doc["boundaries"]["core_certifies_statistical_validity"] is False


def test_candidate_discovery_only():
    registration = reference_r_runtime_migration().runtime_registration
    assert registration.metadata["candidate_discovery_only"] is True
    assert registration.metadata["core_selects_statistical_method"] is False
