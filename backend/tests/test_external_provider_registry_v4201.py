import copy

import pytest
from pydantic import ValidationError

from app.routers import external_provider_registry as api
from app.services.external_provider_registry import (
    AuthenticationMode,
    ExternalProviderRegistryBundle,
    ProviderKind,
    ProviderLifecycleState,
    contract_document,
    reference_external_provider_registry_bundle,
)


def ref():
    return reference_external_provider_registry_bundle()


def invalid(mutator):
    payload = copy.deepcopy(ref().model_dump(mode="json"))
    mutator(payload)
    with pytest.raises(ValidationError):
        ExternalProviderRegistryBundle.model_validate(payload)


def test_release_contract():
    b = ref()
    assert b.release == "4.20.1"
    assert b.contract == "sc.core.external-provider-registry.v1"
    assert b.predecessor_contract == "sc.core.unified-contextual-reasoning-runtime.v1"


def test_six_provider_classes_exist():
    assert set(ProviderKind) == {
        ProviderKind.knowledge, ProviderKind.data, ProviderKind.computational,
        ProviderKind.geospatial, ProviderKind.event, ProviderKind.intelligence,
    }


def test_reference_provider_inventory():
    b = ref()
    assert len(b.providers) == 6
    assert {p.provider_id for p in b.providers} == {
        "provider:pubmed", "provider:fred-alfred", "provider:wolfram",
        "provider:nasa-earthdata", "provider:gdelt", "provider:data-commons",
    }


def test_reference_records_are_not_live_adapter_claims():
    assert all(p.lifecycle_state == ProviderLifecycleState.reference_only for p in ref().providers)
    assert all(p.adapter_implementation_ref is None for p in ref().providers)
    assert all(p.registration_is_not_adapter_implementation for p in ref().providers)
    assert all(p.registration_is_not_connectivity_verification for p in ref().providers)


def test_authority_is_bounded():
    for p in ref().providers:
        assert p.authority_scopes
        assert all(x.source_is_authoritative_within_scope_only for x in p.authority_scopes)
        assert all(not x.authority_establishes_truth for x in p.authority_scopes)
        assert all(not x.authority_overrides_conflicting_evidence for x in p.authority_scopes)


def test_capabilities_require_provenance():
    for p in ref().providers:
        assert all(c.output_requires_provenance for c in p.capabilities)
        assert all(c.output_is_not_automatically_evidence for c in p.capabilities)


def test_credentials_are_references_not_secrets():
    authenticated = [e for p in ref().providers for e in p.endpoints if e.authentication_mode != AuthenticationMode.none]
    assert authenticated
    assert all(e.credential_reference and e.credential_reference.startswith("credential-ref:") for e in authenticated)
    assert all(not e.secret_material_embedded for p in ref().providers for e in p.endpoints)


def test_usage_terms_remain_provider_authority():
    for p in ref().providers:
        assert p.usage_policy.provider_terms_remain_authoritative
        assert not p.usage_policy.registry_may_override_provider_terms


def test_registry_policy_boundaries():
    p = ref().policy
    assert not p.provider_registration_establishes_connectivity
    assert not p.provider_authority_establishes_truth
    assert not p.provider_output_auto_promotes_evidence
    assert not p.computational_output_auto_promotes_evidence
    assert not p.event_signal_establishes_ground_truth
    assert not p.provider_agreement_establishes_truth
    assert not p.registry_authorizes_automatic_graph_mutation


def test_registry_snapshot_exact():
    b = ref()
    expected = {p.provider_id: p.fingerprint() for p in b.providers}
    assert b.snapshots[0].provider_fingerprints == expected


def test_registry_deterministic():
    assert ref().fingerprint() == ref().fingerprint()


def test_contract_counts():
    r = contract_document()["reference"]
    assert r["providers"] == 6
    assert r["provider_kinds"] == 6
    assert r["capabilities"] == 6
    assert r["authority_scopes"] == 6
    assert r["endpoints"] == 6
    assert r["reference_only_providers"] == 6


def test_contract_roadmap():
    x = contract_document()["roadmap_integration"]
    assert x["extends_v4200_without_reopening_reasoning_arc"]
    assert x["prepares_workbench_wolfram_provider"]
    assert x["prepares_library_provider_runtime"]


def test_api_contract():
    assert api.contract()["release"] == "4.20.1"


def test_api_reference():
    assert api.reference()["ok"] is True


def test_api_reference_providers():
    assert api.reference_providers()["count"] == 6


def test_api_provider_lookup():
    assert api.reference_provider("provider:wolfram")["ok"] is True
    assert api.reference_provider("provider:missing")["ok"] is False


def test_duplicate_provider_id_fails():
    def m(p):
        p["providers"][1]["provider_id"] = p["providers"][0]["provider_id"]
    invalid(m)


def test_capability_kind_must_be_declared_fails():
    def m(p):
        p["providers"][0]["capabilities"][0]["provider_kind"] = "computational"
    invalid(m)


def test_reference_provider_may_not_claim_adapter_fails():
    def m(p):
        p["providers"][0]["adapter_implementation_ref"] = "adapter:pubmed"
    invalid(m)


def test_snapshot_tamper_fails():
    def m(p):
        key = next(iter(p["snapshots"][0]["provider_fingerprints"]))
        p["snapshots"][0]["provider_fingerprints"][key] = "0" * 64
    invalid(m)


def test_embedded_secret_reference_fails():
    def m(p):
        p["providers"][1]["endpoints"][0]["credential_reference"] = "key=abc123"
    invalid(m)


def test_database_migration_none():
    assert ref().database_migration == "none"


def test_main_mounts_v4201_routes():
    from app.main import create_app
    app = create_app()
    paths = {r.path for r in app.routes}
    assert "/v1/providers/contract" in paths
    assert "/public/v1/providers/contract" in paths
