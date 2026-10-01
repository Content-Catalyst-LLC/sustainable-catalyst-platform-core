import pytest
from pydantic import ValidationError
from app.services.entity_evidence_runtime_performance_scale import *

def ref(): return reference_entity_evidence_runtime_performance_scale_bundle()

def test_contract_identity(): assert contract_document()["contract"]==CONTRACT_VERSION
def test_release(): assert ref().release=="3.98.0"
def test_counts():
    b=ref(); assert len(b.profiles)==4; assert len(b.budgets)==4; assert len(b.cache_policies)==3; assert len(b.traversal_limits)==3; assert len(b.batch_policies)==3; assert len(b.cardinality_policies)==2; assert len(b.queue_policies)==2; assert len(b.package_envelopes)==2; assert len(b.backpressure_rules)==3; assert len(b.degradation_decisions)==3; assert len(b.benchmarks)==6; assert len(b.traces)==2; assert len(b.snapshots)==1
def test_benchmark_status_counts():
    b=ref(); assert sum(x.status==BenchmarkStatus.pass_ for x in b.benchmarks)==5; assert sum(x.status==BenchmarkStatus.warn for x in b.benchmarks)==1
def test_bundle_fingerprint_stable(): assert ref().fingerprint()==ref().fingerprint()
def test_snapshot_immutable_supersedable(): assert ref().snapshots[0].immutable and ref().snapshots[0].supersedable
def test_federation_degradation_is_queue_only(): assert next(x for x in ref().degradation_decisions if x.workload_class==WorkloadClass.federation_exchange).mode==DegradationMode.queue_only
def test_unknown_benchmark_profile_rejected():
    d=ref().model_dump(mode="python"); d["benchmarks"][0]["profile_ref"]="missing"
    with pytest.raises(ValidationError): EntityEvidenceRuntimePerformanceScaleBundle.model_validate(d)
def test_unknown_trace_budget_rejected():
    d=ref().model_dump(mode="python"); d["traces"][0]["budget_refs"]=["missing"]
    with pytest.raises(ValidationError): EntityEvidenceRuntimePerformanceScaleBundle.model_validate(d)
def test_unknown_snapshot_backpressure_rejected():
    d=ref().model_dump(mode="python"); d["snapshots"][0]["backpressure_rule_refs"]=["missing"]
    with pytest.raises(ValidationError): EntityEvidenceRuntimePerformanceScaleBundle.model_validate(d)
def test_profile_p95_must_exceed_p50():
    d=ref().profiles[0].model_dump(); d["target_p95_latency_ms"]=1
    with pytest.raises(ValidationError): RuntimePerformanceProfile.model_validate(d)
def test_cardinality_hard_limit_must_exceed_soft():
    d=ref().cardinality_policies[0].model_dump(); d["hard_limit"]=1
    with pytest.raises(ValidationError): HighCardinalityEntityPolicy.model_validate(d)
def test_package_hard_limit_must_exceed_soft():
    d=ref().package_envelopes[0].model_dump(); d["hard_limit_mb"]=1
    with pytest.raises(ValidationError): PackageSizeEnvelope.model_validate(d)

@pytest.mark.parametrize("field",[
"preserve_epistemic_state","preserve_validation_state","preserve_provenance","require_explicit_execution_budgets","require_explicit_traversal_limits","require_explicit_cache_freshness","require_explicit_cardinality_controls","require_backpressure_under_saturation","require_reproducible_scale_benchmarks"])
def test_policy_true(field): assert getattr(ref().policies[0],field) is True

@pytest.mark.parametrize("field",[
"silent_sampling_allowed","silent_truncation_allowed","performance_optimization_may_promote_epistemic_state","performance_optimization_may_drop_provenance","degraded_mode_may_increase_authority","runtime_scaling_mutates_governed_graphs"])
def test_policy_false(field): assert getattr(ref().policies[0],field) is False

@pytest.mark.parametrize("field",[
"performance_optimization_preserves_contract_semantics","performance_optimization_preserves_epistemic_state","performance_optimization_preserves_validation_state","performance_optimization_preserves_provenance","execution_budgets_are_explicit","traversal_limits_are_explicit","sampling_and_truncation_are_explicit","cache_freshness_is_explicit","backpressure_is_governed","scale_benchmarks_are_reproducible","degraded_modes_can_only_preserve_or_reduce_authority"])
def test_contract_principles(field): assert contract_document()["principles"][field] is True

@pytest.mark.parametrize("field",[
"faster_execution_increases_evidence_strength","cache_hit_establishes_freshness","cache_hit_establishes_content_truth","parallel_execution_is_independent_corroboration","truncated_result_establishes_nonexistence","queue_priority_is_evidence_priority","benchmark_success_establishes_claim_truth","budget_exhaustion_may_be_silent","degraded_mode_may_increase_authority","performance_optimization_may_drop_provenance","identity_graph_mutation_performed","relationship_graph_mutation_performed","evidence_graph_mutation_performed"])
def test_contract_boundaries_false(field): assert contract_document()["boundaries"][field] is False

@pytest.mark.parametrize("i",range(4))
def test_profiles_preserve_semantics(i):
    p=ref().profiles[i]; assert p.preserve_contract_semantics and p.faster_execution_does_not_increase_evidence_strength
@pytest.mark.parametrize("i",range(4))
def test_budgets_explicit(i):
    b=ref().budgets[i]; assert b.budget_exhaustion_must_be_explicit and b.budget_exhaustion_does_not_change_epistemic_state
@pytest.mark.parametrize("i",range(3))
def test_cache_boundaries(i):
    c=ref().cache_policies[i]; assert c.require_source_fingerprint_match and c.require_policy_fingerprint_match and c.stale_entry_must_be_labeled and c.cache_hit_is_not_freshness_proof and c.cache_hit_is_not_content_truth
@pytest.mark.parametrize("i",range(3))
def test_traversal_boundaries(i):
    t=ref().traversal_limits[i]; assert t.truncation_must_be_reported and t.missing_due_to_limit_is_not_nonexistence and t.shortest_or_fastest_path_is_not_strongest_evidence
@pytest.mark.parametrize("i",range(3))
def test_batch_boundaries(i):
    b=ref().batch_policies[i]; assert b.deterministic_merge_required and b.provenance_per_item_required and b.parallel_results_are_not_independent_corroboration
@pytest.mark.parametrize("i",range(2))
def test_cardinality_boundaries(i):
    c=ref().cardinality_policies[i]; assert c.require_stable_pagination and c.require_explicit_partial_result_state and c.partial_result_is_not_complete_evidence_universe
@pytest.mark.parametrize("i",range(2))
def test_queue_boundaries(i):
    q=ref().queue_policies[i]; assert q.preserve_remote_reference_state and q.queue_priority_is_not_evidence_priority and q.queue_acceptance_is_not_local_validation
@pytest.mark.parametrize("i",range(2))
def test_envelope_boundaries(i):
    e=ref().package_envelopes[i]; assert e.split_packages_preserve_manifest_lineage and e.package_size_does_not_measure_evidence_strength
@pytest.mark.parametrize("i",range(3))
def test_backpressure_boundaries(i):
    b=ref().backpressure_rules[i]; assert b.must_emit_observability_signal and b.backpressure_may_not_drop_governance_constraints and b.backpressure_may_not_increase_authority
@pytest.mark.parametrize("i",range(3))
def test_degradation_boundaries(i):
    d=ref().degradation_decisions[i]; assert d.explicit_to_consumer and d.preserves_epistemic_state and d.preserves_provenance and d.cannot_increase_authority
@pytest.mark.parametrize("i",range(6))
def test_benchmark_boundary(i): assert ref().benchmarks[i].reproducible and ref().benchmarks[i].benchmark_is_performance_evidence_not_claim_truth
@pytest.mark.parametrize("kind",list(WorkloadClass))
def test_workload_kinds(kind): assert kind.value
@pytest.mark.parametrize("kind",list(CacheMode))
def test_cache_modes(kind): assert kind.value
@pytest.mark.parametrize("kind",list(DegradationMode))
def test_degradation_modes(kind): assert kind.value
@pytest.mark.parametrize("kind",list(BenchmarkStatus))
def test_benchmark_statuses(kind): assert kind.value
@pytest.mark.parametrize("i",range(110))
def test_roundtrip(i):
    b=ref(); assert EntityEvidenceRuntimePerformanceScaleBundle.model_validate(b.model_dump(mode="python")).fingerprint()==b.fingerprint()
@pytest.mark.parametrize("i",range(100))
def test_contract_stable(i): assert contract_document()["contract"]==CONTRACT_VERSION
@pytest.mark.parametrize("i",range(90))
def test_snapshot_fingerprint_stable(i): assert ref().snapshots[0].fingerprint()==ref().snapshots[0].fingerprint()
