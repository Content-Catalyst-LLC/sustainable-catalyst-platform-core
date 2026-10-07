from copy import deepcopy

import pytest
from pydantic import ValidationError

from app.config import Settings
from app.routers import unified_semantic_context_runtime as api
from app.services.unified_semantic_context_runtime import (
    RuntimeExecutionMode,
    RuntimeQualificationCode,
    RuntimeSessionState,
    RuntimeStageKind,
    RuntimeStageState,
    STAGE_CONTRACTS,
    STAGE_ORDER,
    STAGE_RELEASES,
    UnifiedSemanticContextRuntimeBundle,
    contract_document,
    reference_unified_semantic_context_runtime_bundle,
)


def ref():
    return reference_unified_semantic_context_runtime_bundle()


def payload():
    return ref().model_dump(mode="json")


def invalid(mutator):
    p = payload()
    mutator(p)
    with pytest.raises((ValidationError, ValueError)):
        UnifiedSemanticContextRuntimeBundle.model_validate(p)


def test_release_identity():
    version = tuple(int(x) for x in Settings().version.split("."))
    assert version >= (4, 10, 0)
    assert ref().release == "4.10.0"
    assert ref().contract == "sc.core.unified-semantic-contextual-intelligence-runtime.v1"
    assert ref().predecessor_contract == "sc.core.contextual-semantic-evaluation-benchmark-framework.v1"


def test_v49_predecessor_is_preserved():
    assert ref().predecessor_evaluation.release == "4.9.0"
    assert ref().predecessor_evaluation.contract == "sc.core.contextual-semantic-evaluation-benchmark-framework.v1"


def test_runtime_has_nine_ordered_stages():
    xs = sorted(ref().stage_definitions, key=lambda x: x.ordinal)
    assert len(xs) == 9
    assert [x.kind for x in xs] == STAGE_ORDER
    assert [x.ordinal for x in xs] == list(range(1, 10))


def test_stage_release_contract_matrix_is_exact():
    for stage in ref().stage_definitions:
        assert stage.release == STAGE_RELEASES[stage.kind]
        assert stage.contract == STAGE_CONTRACTS[stage.kind]


def test_stage_dependency_chain_is_linear_and_explicit():
    xs = sorted(ref().stage_definitions, key=lambda x: x.ordinal)
    assert xs[0].depends_on_stage_refs == []
    for i in range(1, len(xs)):
        assert xs[i].depends_on_stage_refs == [xs[i-1].stage_id]


def test_stage_reference_fingerprints_are_sha256():
    assert all(len(x.reference_fingerprint_sha256) == 64 for x in ref().stage_definitions)


def test_reference_plan_is_complete_and_governed():
    plan = ref().plans[0]
    assert plan.execution_mode == RuntimeExecutionMode.reference_replay
    assert plan.stage_refs == [x.stage_id for x in sorted(ref().stage_definitions, key=lambda x: x.ordinal)]
    assert plan.stop_on_validation_failure is True
    assert plan.allow_qualified_continuation is True
    assert plan.require_original_language_lineage is True
    assert plan.final_evaluation_required is True


def test_every_stage_has_one_reference_artifact_and_result():
    assert len(ref().artifacts) == 9
    assert len(ref().stage_results) == 9
    stage_ids = {x.stage_id for x in ref().stage_definitions}
    assert {x.stage_ref for x in ref().artifacts} == stage_ids
    assert {x.stage_ref for x in ref().stage_results} == stage_ids


def test_artifact_contract_and_fingerprint_match_stage():
    stages = {x.stage_id: x for x in ref().stage_definitions}
    for a in ref().artifacts:
        s = stages[a.stage_ref]
        assert a.contract_ref == s.contract
        assert a.object_fingerprint_sha256 == s.reference_fingerprint_sha256
        assert a.immutable_reference is True
        assert a.artifact_is_interpretation_not_truth_verdict is True


def test_stage_results_chain_artifacts_in_order():
    results = ref().stage_results
    assert results[0].external_input_refs == ["source:governed-reference-corpus:v4.10"]
    assert results[0].input_artifact_refs == []
    for i in range(1, 9):
        assert results[i].input_artifact_refs == [results[i-1].output_artifact_refs[0]]


def test_all_reference_stage_results_are_qualified_not_failed():
    assert all(x.state == RuntimeStageState.qualified for x in ref().stage_results)
    assert all(x.validation_passed is True for x in ref().stage_results)


def test_each_stage_has_explicit_qualification():
    assert len(ref().qualifications) == 9
    assert {x.stage_ref for x in ref().qualifications} == {x.stage_id for x in ref().stage_definitions}


def test_qualification_taxonomy_covers_semantic_boundaries():
    codes = {x.code for x in ref().qualifications}
    assert codes == set(RuntimeQualificationCode)


def test_ambiguity_is_preserved():
    q = next(x for x in ref().qualifications if x.code == RuntimeQualificationCode.ambiguity_preserved)
    assert "mention:it-unresolved" in q.unresolved_refs


def test_canonical_identity_is_deferred():
    q = next(x for x in ref().qualifications if x.code == RuntimeQualificationCode.canonical_identity_deferred)
    assert "surface-actor:ministry" in q.unresolved_refs


def test_geographic_identity_is_deferred():
    q = next(x for x in ref().qualifications if x.code == RuntimeQualificationCode.geographic_identity_deferred)
    assert "spatial-anchor:brussels-source-place" in q.unresolved_refs


def test_cultural_divergence_is_preserved():
    q = next(x for x in ref().qualifications if x.code == RuntimeQualificationCode.cultural_divergence_preserved)
    assert "universal-equivalence:治理-governance-gobernanza" in q.unresolved_refs


def test_benchmark_is_non_authoritative():
    q = next(x for x in ref().qualifications if x.code == RuntimeQualificationCode.benchmark_non_authoritative)
    assert "evaluation-run:reference-baseline:v1" in q.unresolved_refs


def test_session_is_qualified_complete_not_truth_claim():
    s = ref().sessions[0]
    assert s.state == RuntimeSessionState.qualified_complete
    assert len(s.stage_result_refs) == 9
    assert s.reproducible is True
    assert s.session_completion_does_not_establish_truth_or_authority is True


def test_session_evaluation_run_resolves_to_v49():
    assert ref().sessions[0].evaluation_run_ref in {x.run_id for x in ref().predecessor_evaluation.evaluation_runs}


def test_snapshot_preserves_v49_predecessor_fingerprint():
    s = ref().snapshots[0]
    assert s.predecessor_fingerprint_sha256 == ref().predecessor_evaluation.fingerprint()
    assert len(s.stage_fingerprints) == 9
    assert s.snapshot_does_not_freeze_semantic_truth is True


def test_snapshot_deterministic_runtime_fingerprint_is_stable():
    a = ref().snapshots[0].deterministic_runtime_fingerprint_sha256
    b = reference_unified_semantic_context_runtime_bundle().snapshots[0].deterministic_runtime_fingerprint_sha256
    assert a == b


def test_bundle_fingerprint_is_deterministic():
    assert ref().fingerprint() == reference_unified_semantic_context_runtime_bundle().fingerprint()


def test_policy_boundaries_are_strict():
    p = ref().policy
    assert p.runtime_output_is_interpretation_not_truth is True
    assert p.core_orchestrates_but_does_not_silently_execute_domain_models is True
    assert p.context_graph_mutation_authorized is False
    assert p.identity_graph_mutation_authorized is False
    assert p.evidence_graph_mutation_authorized is False
    assert p.knowledge_graph_mutation_authorized is False


def test_contract_pipeline_lists_nine_stages():
    c = contract_document()
    assert len(c["runtime_pipeline"]) == 9
    assert c["runtime_pipeline"][0]["release"] == "4.1.0"
    assert c["runtime_pipeline"][-1]["release"] == "4.9.0"


def test_contract_boundaries_are_explicit():
    b = contract_document()["boundaries"]
    assert b["runtime_completion_establishes_claim_truth"] is False
    assert b["runtime_completion_establishes_evidence_validity"] is False
    assert b["runtime_completion_establishes_canonical_identity"] is False
    assert b["runtime_completion_establishes_source_authority"] is False
    assert b["core_silently_executes_domain_models"] is False
    assert b["context_graph_mutation_performed"] is False
    assert b["identity_graph_mutation_performed"] is False
    assert b["evidence_graph_mutation_performed"] is False
    assert b["knowledge_graph_mutation_performed"] is False


def test_contract_reference_counts():
    r = contract_document()["reference"]
    assert r["predecessor_release"] == "4.9.0"
    assert r["stages"] == 9
    assert r["stage_results"] == 9
    assert r["qualified_stage_results"] == 9
    assert r["artifacts"] == 9
    assert r["qualifications"] == 9
    assert r["plans"] == 1
    assert r["sessions"] == 1
    assert r["snapshots"] == 1
    assert r["session_state"] == "qualified-complete"
    assert r["context_graph_mutations_created"] == 0


def test_api_contract_functions_are_directly_callable():
    assert api.contract()["release"] == "4.10.0"
    assert api.public_contract()["contract"] == "sc.core.unified-semantic-contextual-intelligence-runtime.v1"
    assert api.reference_stages()["count"] == 9
    assert api.reference_stages(RuntimeStageKind.multilingual)["count"] == 1
    assert api.reference_artifacts()["count"] == 9
    assert api.reference_session()["session"]["state"] == "qualified-complete"


def test_bad_stage_order_fails():
    def mutate(p):
        p["stage_definitions"][0]["ordinal"] = 2
    invalid(mutate)


def test_bad_stage_contract_fails():
    invalid(lambda p: p["stage_definitions"][0].__setitem__("contract", "sc.core.invalid.v1"))


def test_bad_artifact_fingerprint_fails():
    invalid(lambda p: p["artifacts"][0].__setitem__("object_fingerprint_sha256", "0"*64))


def test_bad_session_evaluation_run_fails():
    invalid(lambda p: p["sessions"][0].__setitem__("evaluation_run_ref", "evaluation-run:missing"))


def test_bad_snapshot_predecessor_fingerprint_fails():
    invalid(lambda p: p["snapshots"][0].__setitem__("predecessor_fingerprint_sha256", "0"*64))


def test_main_mounts_v410_routers():
    from app.main import create_app
    app = create_app()
    paths = {r.path for r in app.routes}
    assert "/v1/semantic-context-runtime/contract" in paths
    assert "/public/v1/semantic-context-runtime/contract" in paths
