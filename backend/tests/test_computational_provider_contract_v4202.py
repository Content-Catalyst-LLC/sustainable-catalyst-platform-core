import copy

import pytest
from pydantic import ValidationError

from app.routers import computational_provider_contract as api
from app.services.computational_provider_contract import (
    ComputationalComparisonDisposition,
    ComputationalEngineKind,
    ComputationalProviderContractBundle,
    contract_document,
    reference_computational_provider_contract_bundle,
)


def ref():
    return reference_computational_provider_contract_bundle()


def invalid(mutator):
    payload=copy.deepcopy(ref().model_dump(mode="json"))
    mutator(payload)
    with pytest.raises(ValidationError):
        ComputationalProviderContractBundle.model_validate(payload)


def test_release_contract_and_lineage():
    b=ref()
    assert b.release=="4.20.2"
    assert b.contract=="sc.core.computational-provider-contract.v1"
    assert b.predecessor_contract=="sc.core.external-provider-registry.v1"
    assert b.legacy_analytical_contract=="sc.core.analytical-runtime-provider.v1"


def test_reference_provider_profiles():
    b=ref()
    assert len(b.providers)==7
    assert {p.profile_id for p in b.providers}=={"compute:wolfram","compute:python","compute:r","compute:julia","compute:sympy","compute:haskell","compute:workbench-native"}


def test_wolfram_is_registry_bound_but_not_live_claim():
    p=next(x for x in ref().providers if x.profile_id=="compute:wolfram")
    assert p.provider_registry_ref=="provider:wolfram"
    assert p.registry_binding_state=="registered-reference"
    assert p.reference_profile_only is True
    assert p.connectivity_verified is False
    assert p.execution_authorized_by_core is False


def test_internal_runtimes_not_falsely_external_registered():
    for pid in {"compute:python","compute:r","compute:julia","compute:sympy","compute:workbench-native"}:
        p=next(x for x in ref().providers if x.profile_id==pid)
        assert p.provider_registry_ref is None
        assert p.registry_binding_state=="internal-runtime-reference"


def test_haskell_is_proposed_reference():
    p=next(x for x in ref().providers if x.profile_id=="compute:haskell")
    assert p.registry_binding_state=="proposed"
    assert p.provider_registry_ref is None


def test_engine_kind_coverage():
    kinds={k for p in ref().providers for k in p.engine_kinds}
    assert {ComputationalEngineKind.general,ComputationalEngineKind.symbolic,ComputationalEngineKind.numerical,ComputationalEngineKind.statistical,ComputationalEngineKind.simulation,ComputationalEngineKind.optimization,ComputationalEngineKind.functional}.issubset(kinds)


def test_capabilities_require_provenance_and_non_evidence_boundary():
    for p in ref().providers:
        assert all(c.output_requires_provenance for c in p.capabilities)
        assert all(c.output_is_not_automatically_evidence for c in p.capabilities)


def test_request_result_fixture_counts():
    b=ref()
    assert len(b.requests)==4
    assert len(b.results)==4
    assert len(b.comparisons)==2
    assert all(r.reference_fixture_only for r in b.requests)
    assert all(not r.core_executes_request for r in b.requests)
    assert all(not r.external_execution_performed for r in b.results)


def test_multi_engine_comparison_boundaries():
    b=ref()
    assert {x.disposition for x in b.comparisons}=={ComputationalComparisonDisposition.symbolic_equivalence,ComputationalComparisonDisposition.exact_agreement}
    assert all(not x.agreement_establishes_truth for x in b.comparisons)
    assert all(not x.discrepancy_establishes_error for x in b.comparisons)
    assert all(not x.comparison_auto_selects_winner for x in b.comparisons)


def test_policy_boundaries():
    p=ref().policy
    assert p.execution_occurs_outside_core
    assert p.legacy_analytical_runtime_lineage_preserved
    assert not p.computational_output_establishes_truth
    assert not p.computational_output_auto_promotes_evidence
    assert not p.multi_engine_agreement_establishes_truth
    assert not p.discrepancy_auto_identifies_faulty_engine
    assert not p.core_selects_provider_autonomously
    assert not p.core_executes_provider
    assert not p.contract_authorizes_graph_mutation


def test_snapshot_exact_and_deterministic():
    b=ref()
    assert b.snapshots[0].provider_fingerprints=={p.profile_id:p.fingerprint() for p in b.providers}
    assert b.fingerprint()==ref().fingerprint()


def test_contract_reference_counts():
    r=contract_document()["reference"]
    assert r["provider_profiles"]==7
    assert r["registered_external_provider_profiles"]==1
    assert r["internal_runtime_profiles"]==5
    assert r["proposed_profiles"]==1
    assert r["capabilities"]==14
    assert r["requests"]==4 and r["results"]==4 and r["comparisons"]==2


def test_contract_roadmap():
    x=contract_document()["roadmap_integration"]
    assert x["extends_v4201_provider_registry"]
    assert x["prepares_workbench_wolfram_provider"]
    assert x["prepares_multi_engine_verification"]


def test_api_surfaces():
    assert api.contract()["release"]=="4.20.2"
    assert api.reference()["ok"] is True
    assert api.reference_providers()["count"]==7
    assert api.reference_provider("compute:wolfram")["ok"] is True
    assert api.reference_provider("compute:missing")["ok"] is False
    assert api.reference_requests()["count"]==4
    assert api.reference_comparisons()["count"]==2


def test_duplicate_profile_fails():
    invalid(lambda p: p["providers"][1].__setitem__("profile_id",p["providers"][0]["profile_id"]))


def test_registered_reference_requires_provider_registry_ref():
    invalid(lambda p: p["providers"][0].__setitem__("provider_registry_ref",None))


def test_request_capability_must_exist():
    invalid(lambda p: p["requests"][0].__setitem__("capability_id","capability:missing"))


def test_request_environment_provider_must_match():
    invalid(lambda p: p["requests"][0].__setitem__("environment_id","environment:compute:sympy:reference-v1"))


def test_result_provider_must_match_request():
    invalid(lambda p: p["results"][0].__setitem__("provider_profile_id","compute:sympy"))


def test_comparison_requires_known_distinct_results():
    invalid(lambda p: p["comparisons"][0].__setitem__("right_result_id",p["comparisons"][0]["left_result_id"]))


def test_snapshot_tamper_fails():
    def m(p):
        key=next(iter(p["snapshots"][0]["provider_fingerprints"]))
        p["snapshots"][0]["provider_fingerprints"][key]="0"*64
    invalid(m)


def test_database_migration_none():
    assert ref().database_migration=="none"


def test_main_mounts_v4202_routes():
    from app.main import create_app
    app=create_app()
    paths={r.path for r in app.routes}
    assert "/v1/computational-providers/contract" in paths
    assert "/public/v1/computational-providers/contract" in paths
