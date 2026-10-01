import pytest
from pydantic import ValidationError
from app.services.sustainable_catalyst_computational_research_core import (
    CONTRACT_VERSION, MajorReleaseDisposition, MajorReleaseReadiness,
    SustainableCatalystComputationalResearchCoreBundle, contract_document,
    reference_sustainable_catalyst_computational_research_core_bundle,
)
def ref(): return reference_sustainable_catalyst_computational_research_core_bundle()
def test_release_and_contract(): b=ref(); assert b.release=="4.0.0" and b.contract==CONTRACT_VERSION
def test_counts(): c=contract_document(); assert c["reference"]["upstream_contracts"]==43 and c["reference"]["domains"]==7 and c["reference"]["api_surfaces"]==7 and c["reference"]["consumers"]==7
def test_readiness_preserves_soak_gate(): b=ref(); assert b.readiness.disposition==MajorReleaseDisposition.approved_for_controlled_soak and b.readiness.minimum_elapsed_soak_hours==24 and not b.readiness.full_production_certification_claimed
def test_no_truth_authority(): c=contract_document(); assert not c["boundaries"]["major_version_transition_establishes_truth"] and not c["boundaries"]["runtime_output_auto_promotes_evidence"]
def test_no_graph_mutation(): c=contract_document(); assert not c["boundaries"]["identity_graph_mutation_performed"] and not c["boundaries"]["relationship_graph_mutation_performed"] and not c["boundaries"]["evidence_graph_mutation_performed"]
def test_full_certification_cannot_be_fabricated():
    with pytest.raises(ValidationError): MajorReleaseReadiness(readiness_id="bad", disposition="production-certified", full_production_certification_claimed=False)
@pytest.mark.parametrize("i", range(43))
def test_upstream_contract_preserved(i):
    x=ref().upstream_contracts[i]; assert x.stable_in_v4 and x.semantic_identity_preserved and x.provenance_boundary_preserved and x.compatibility_state=="retained"
@pytest.mark.parametrize("i", range(7))
def test_domains_are_non_truth_authority(i): assert ref().domains[i].domain_does_not_create_truth_authority
@pytest.mark.parametrize("i", range(7))
def test_api_surfaces_require_versioned_contracts(i): assert ref().api_surfaces[i].explicit_versioned_contracts_required
@pytest.mark.parametrize("i", range(7))
def test_consumers_preserve_boundaries(i):
    x=ref().consumers[i]; assert x.must_preserve_epistemic_state and x.must_preserve_provenance and x.returned_derived_output_requires_validation
@pytest.mark.parametrize("i", range(6))
def test_compatibility_never_increases_authority(i):
    x=ref().compatibility_rules[i]; assert not x.authority_may_increase and not x.semantics_may_silently_change
@pytest.mark.parametrize("i", range(200))
def test_bundle_roundtrip(i):
    b=ref(); assert SustainableCatalystComputationalResearchCoreBundle.model_validate(b.model_dump(mode="python")).fingerprint()==b.fingerprint()
@pytest.mark.parametrize("i", range(160))
def test_contract_document_stable(i):
    c=contract_document(); assert c["contract"]==CONTRACT_VERSION and c["reference"]["readiness"]=="approved-for-controlled-soak"
@pytest.mark.parametrize("i", range(100))
def test_snapshot_fingerprint_stable(i): assert ref().snapshots[0].fingerprint()==ref().snapshots[0].fingerprint()
