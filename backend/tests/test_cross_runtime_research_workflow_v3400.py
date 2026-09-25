from copy import deepcopy

import pytest
from pydantic import ValidationError

from app.services.cross_runtime_research_workflow import (
    CONTRACT_VERSION,
    REFERENCE_JULIA_RUNTIME,
    REFERENCE_R_RUNTIME,
    CrossRuntimeWorkflowDefinition,
    CrossRuntimeWorkflowPackage,
    CrossRuntimeWorkflowRun,
    CrossRuntimeWorkflowStep,
    HandoffState,
    RuntimeHandoff,
    WorkflowDependency,
    WorkflowDependencyType,
    WorkflowInputBinding,
    WorkflowOutputBinding,
    WorkflowRuntimeBinding,
    WorkflowState,
    WorkflowStepKind,
    WorkflowStepState,
    WorkflowVerification,
    WorkflowVerificationStatus,
    contract_document,
    reference_cross_runtime_workflow_package,
    topological_step_order,
    to_scientific_workflow_artifact,
    workflow_readiness,
)


def reference_package():
    return reference_cross_runtime_workflow_package()


def test_contract_identity():
    doc = contract_document()
    assert doc["release"] == "3.40.0"
    assert doc["contract"] == CONTRACT_VERSION


def test_contract_links_v339_interchange():
    doc = contract_document()
    assert "sc.core.runtime-data-interchange.v1" in doc["depends_on"]


def test_contract_links_statistical_objects():
    doc = contract_document()
    assert "sc.core.statistical-analysis-object.v1" in doc["depends_on"]


def test_contract_links_scientific_registry():
    doc = contract_document()
    assert "sc.core.scientific-result-artifact-registry.v1" in doc["depends_on"]


def test_reference_package_valid():
    package = reference_package()
    assert package.definition.workflow_id == "cross-runtime-workflow:reference-r-julia:v1"
    assert package.run.state == WorkflowState.completed


def test_reference_has_two_runtime_bindings():
    package = reference_package()
    assert len(package.definition.runtime_bindings) == 2
    refs = {item.runtime_ref for item in package.definition.runtime_bindings}
    assert refs == {REFERENCE_R_RUNTIME, REFERENCE_JULIA_RUNTIME}


def test_reference_has_three_steps():
    package = reference_package()
    assert len(package.definition.steps) == 3


def test_reference_has_verified_handoff():
    handoff = reference_package().definition.handoffs[0]
    assert handoff.state == HandoffState.verified
    assert handoff.source_runtime_ref == REFERENCE_R_RUNTIME
    assert handoff.target_runtime_ref == REFERENCE_JULIA_RUNTIME


def test_runtime_binding_rejects_duplicate_operations():
    with pytest.raises(ValidationError):
        WorkflowRuntimeBinding(
            binding_id="binding:test",
            runtime_ref="runtime:test",
            runtime_version="1.0",
            runtime_adapter_ref="adapter:test",
            environment_ref="environment:test",
            required_operations=["op", "op"],
        )


def test_runtime_binding_fingerprint_stable():
    binding = reference_package().definition.runtime_bindings[0]
    assert binding.fingerprint() == deepcopy(binding).fingerprint()


def test_input_requires_source():
    with pytest.raises(ValidationError):
        WorkflowInputBinding(
            input_id="input:test",
            logical_data_ref="logical:test",
        )


def test_input_accepts_artifact_source():
    item = WorkflowInputBinding(
        input_id="input:test",
        logical_data_ref="logical:test",
        source_artifact_ref="artifact:test",
    )
    assert item.source_artifact_ref == "artifact:test"


def test_input_accepts_result_source():
    item = WorkflowInputBinding(
        input_id="input:test",
        logical_data_ref="logical:test",
        source_result_ref="result:test",
    )
    assert item.source_result_ref == "result:test"


def test_input_fingerprint_stable():
    item = reference_package().definition.steps[0].inputs[0]
    assert item.fingerprint() == deepcopy(item).fingerprint()


def test_output_requires_target_ref():
    with pytest.raises(ValidationError):
        WorkflowOutputBinding(
            output_id="output:test",
            logical_data_ref="logical:test",
        )


def test_output_accepts_artifact_ref():
    item = WorkflowOutputBinding(
        output_id="output:test",
        logical_data_ref="logical:test",
        artifact_ref="artifact:test",
    )
    assert item.artifact_ref == "artifact:test"


def test_output_accepts_result_ref():
    item = WorkflowOutputBinding(
        output_id="output:test",
        logical_data_ref="logical:test",
        result_ref="result:test",
    )
    assert item.result_ref == "result:test"


def test_compute_step_requires_runtime():
    with pytest.raises(ValidationError):
        CrossRuntimeWorkflowStep(
            step_id="step:test",
            name="test",
            kind=WorkflowStepKind.compute,
        )


def test_statistical_step_requires_runtime():
    with pytest.raises(ValidationError):
        CrossRuntimeWorkflowStep(
            step_id="step:test",
            name="test",
            kind=WorkflowStepKind.statistical_analysis,
        )


def test_registration_step_does_not_require_runtime():
    step = CrossRuntimeWorkflowStep(
        step_id="step:test",
        name="register",
        kind=WorkflowStepKind.scientific_registration,
    )
    assert step.runtime_binding_ref is None


def test_step_rejects_duplicate_input_ids():
    inp = WorkflowInputBinding(
        input_id="input:test",
        logical_data_ref="logical:test",
        source_artifact_ref="artifact:test",
    )
    with pytest.raises(ValidationError):
        CrossRuntimeWorkflowStep(
            step_id="step:test",
            name="test",
            kind=WorkflowStepKind.compute,
            runtime_binding_ref="binding:test",
            inputs=[inp, deepcopy(inp)],
        )


def test_step_rejects_duplicate_output_ids():
    out = WorkflowOutputBinding(
        output_id="output:test",
        logical_data_ref="logical:test",
        artifact_ref="artifact:test",
    )
    with pytest.raises(ValidationError):
        CrossRuntimeWorkflowStep(
            step_id="step:test",
            name="test",
            kind=WorkflowStepKind.compute,
            runtime_binding_ref="binding:test",
            outputs=[out, deepcopy(out)],
        )


def test_step_fingerprint_ignores_state():
    step = reference_package().definition.steps[0]
    other = deepcopy(step)
    other.state = WorkflowStepState.running
    assert step.fingerprint() == other.fingerprint()


def test_dependency_rejects_self_reference():
    with pytest.raises(ValidationError):
        WorkflowDependency(
            dependency_id="dependency:test",
            upstream_step_ref="step:test",
            downstream_step_ref="step:test",
        )


def test_dependency_fingerprint_stable():
    dep = reference_package().definition.dependencies[0]
    assert dep.fingerprint() == deepcopy(dep).fingerprint()


def test_handoff_requires_different_steps():
    with pytest.raises(ValidationError):
        RuntimeHandoff(
            handoff_id="handoff:test",
            source_step_ref="step:a",
            target_step_ref="step:a",
            source_runtime_ref="runtime:a",
            target_runtime_ref="runtime:b",
            logical_data_ref="logical:test",
            interchange_transfer_ref="transfer:test",
            source_artifact_ref="artifact:a",
            target_artifact_ref="artifact:b",
            verification_ref="verification:test",
        )


def test_handoff_requires_different_runtimes():
    with pytest.raises(ValidationError):
        RuntimeHandoff(
            handoff_id="handoff:test",
            source_step_ref="step:a",
            target_step_ref="step:b",
            source_runtime_ref="runtime:a",
            target_runtime_ref="runtime:a",
            logical_data_ref="logical:test",
            interchange_transfer_ref="transfer:test",
            source_artifact_ref="artifact:a",
            target_artifact_ref="artifact:b",
            verification_ref="verification:test",
        )


def test_handoff_fingerprint_ignores_state():
    handoff = reference_package().definition.handoffs[0]
    other = deepcopy(handoff)
    other.state = HandoffState.prepared
    assert handoff.fingerprint() == other.fingerprint()


def test_workflow_requires_steps():
    with pytest.raises(ValidationError):
        CrossRuntimeWorkflowDefinition(
            workflow_id="workflow:test",
            name="test",
            objective="test objective",
            steps=[],
        )


def test_workflow_rejects_duplicate_runtime_binding_ids():
    package = reference_package()
    binding = package.definition.runtime_bindings[0]
    with pytest.raises(ValidationError):
        CrossRuntimeWorkflowDefinition(
            workflow_id="workflow:test",
            name="test",
            objective="test",
            runtime_bindings=[binding, deepcopy(binding)],
            steps=[package.definition.steps[2]],
        )


def test_workflow_rejects_duplicate_step_ids():
    package = reference_package()
    step = package.definition.steps[2]
    with pytest.raises(ValidationError):
        CrossRuntimeWorkflowDefinition(
            workflow_id="workflow:test",
            name="test",
            objective="test",
            steps=[step, deepcopy(step)],
        )


def test_workflow_rejects_duplicate_dependency_ids():
    package = reference_package()
    data = package.definition.model_dump(mode="python")
    data["dependencies"] = [
        data["dependencies"][0],
        deepcopy(data["dependencies"][0]),
    ]
    with pytest.raises(ValidationError):
        CrossRuntimeWorkflowDefinition.model_validate(data)


def test_workflow_rejects_duplicate_handoff_ids():
    package = reference_package()
    data = package.definition.model_dump(mode="python")
    data["handoffs"] = [
        data["handoffs"][0],
        deepcopy(data["handoffs"][0]),
    ]
    with pytest.raises(ValidationError):
        CrossRuntimeWorkflowDefinition.model_validate(data)


def test_workflow_rejects_unknown_runtime_binding():
    package = reference_package()
    data = package.definition.model_dump(mode="python")
    data["steps"][0]["runtime_binding_ref"] = "binding:missing"
    with pytest.raises(ValidationError):
        CrossRuntimeWorkflowDefinition.model_validate(data)


def test_workflow_rejects_unknown_dependency_step():
    package = reference_package()
    data = package.definition.model_dump(mode="python")
    data["dependencies"][0]["downstream_step_ref"] = "step:missing"
    with pytest.raises(ValidationError):
        CrossRuntimeWorkflowDefinition.model_validate(data)


def test_workflow_rejects_unknown_handoff_step():
    package = reference_package()
    data = package.definition.model_dump(mode="python")
    data["handoffs"][0]["target_step_ref"] = "step:missing"
    with pytest.raises(ValidationError):
        CrossRuntimeWorkflowDefinition.model_validate(data)


def test_workflow_rejects_cycle():
    package = reference_package()
    data = package.definition.model_dump(mode="python")
    data["dependencies"].append({
        "dependency_id": "dependency:cycle",
        "upstream_step_ref": "workflow-step:scientific-registration",
        "downstream_step_ref": "workflow-step:r-regression",
        "dependency_type": "hard",
        "required_output_refs": [],
        "metadata": {},
    })
    with pytest.raises(ValidationError):
        CrossRuntimeWorkflowDefinition.model_validate(data)


def test_handoff_requires_matching_dependency():
    package = reference_package()
    data = package.definition.model_dump(mode="python")
    data["dependencies"] = [
        dep for dep in data["dependencies"]
        if dep["dependency_id"] != "dependency:r-to-julia"
    ]
    with pytest.raises(ValidationError):
        CrossRuntimeWorkflowDefinition.model_validate(data)


def test_handoff_source_runtime_matches_step():
    package = reference_package()
    data = package.definition.model_dump(mode="python")
    data["handoffs"][0]["source_runtime_ref"] = REFERENCE_JULIA_RUNTIME
    with pytest.raises(ValidationError):
        CrossRuntimeWorkflowDefinition.model_validate(data)


def test_handoff_target_runtime_matches_step():
    package = reference_package()
    data = package.definition.model_dump(mode="python")
    data["handoffs"][0]["target_runtime_ref"] = REFERENCE_R_RUNTIME
    with pytest.raises(ValidationError):
        CrossRuntimeWorkflowDefinition.model_validate(data)


def test_workflow_fingerprint_ignores_created_at():
    workflow = reference_package().definition
    assert workflow.fingerprint() == deepcopy(workflow).fingerprint()


def test_topological_order_reference():
    workflow = reference_package().definition
    assert topological_step_order(workflow) == [
        "workflow-step:r-regression",
        "workflow-step:julia-matrix",
        "workflow-step:scientific-registration",
    ]


def test_readiness_initially_only_r_step_ready():
    workflow = reference_package().definition
    report = workflow_readiness(workflow, [], [])
    assert report.ready_step_refs == ["workflow-step:r-regression"]
    assert set(report.blocked_step_refs) == {
        "workflow-step:julia-matrix",
        "workflow-step:scientific-registration",
    }


def test_readiness_after_r_without_handoff_keeps_julia_blocked():
    workflow = reference_package().definition
    report = workflow_readiness(
        workflow,
        ["workflow-step:r-regression"],
        [],
    )
    assert "workflow-step:julia-matrix" in report.blocked_step_refs
    julia = [
        item for item in report.step_reports
        if item.step_ref == "workflow-step:julia-matrix"
    ][0]
    assert any(blocker.startswith("handoff:") for blocker in julia.blockers)


def test_readiness_after_r_and_verified_handoff_makes_julia_ready():
    workflow = reference_package().definition
    report = workflow_readiness(
        workflow,
        ["workflow-step:r-regression"],
        ["handoff:r-to-julia:reference-regression"],
    )
    assert report.ready_step_refs == ["workflow-step:julia-matrix"]


def test_readiness_after_r_and_julia_makes_registry_ready():
    workflow = reference_package().definition
    report = workflow_readiness(
        workflow,
        ["workflow-step:r-regression", "workflow-step:julia-matrix"],
        ["handoff:r-to-julia:reference-regression"],
    )
    assert report.ready_step_refs == ["workflow-step:scientific-registration"]


def test_readiness_after_all_steps_has_no_pending():
    workflow = reference_package().definition
    report = workflow_readiness(
        workflow,
        [step.step_id for step in workflow.steps],
        ["handoff:r-to-julia:reference-regression"],
    )
    assert report.ready_step_refs == []
    assert report.blocked_step_refs == []


def test_readiness_rejects_unknown_completed_step():
    workflow = reference_package().definition
    with pytest.raises(ValueError):
        workflow_readiness(workflow, ["step:missing"], [])


def test_readiness_fingerprint_stable():
    workflow = reference_package().definition
    report = workflow_readiness(workflow, [], [])
    assert report.fingerprint() == deepcopy(report).fingerprint()


def test_verification_rejects_bad_step_hash():
    with pytest.raises(ValidationError):
        WorkflowVerification(
            verification_id="verification:test",
            workflow_ref="workflow:test",
            status=WorkflowVerificationStatus.passed,
            step_fingerprints={"step:test": "bad"},
        )


def test_verification_fingerprint_stable():
    verification = reference_package().run.verification
    assert verification is not None
    assert verification.fingerprint() == deepcopy(verification).fingerprint()


def test_run_rejects_duplicate_event_ids():
    package = reference_package()
    data = package.run.model_dump(mode="python")
    data["events"] = [
        data["events"][0],
        deepcopy(data["events"][0]),
    ]
    with pytest.raises(ValidationError):
        CrossRuntimeWorkflowRun.model_validate(data)


def test_completed_run_requires_verification():
    package = reference_package()
    data = package.run.model_dump(mode="python")
    data["verification"] = None
    with pytest.raises(ValidationError):
        CrossRuntimeWorkflowRun.model_validate(data)


def test_completed_run_rejects_failed_verification():
    package = reference_package()
    data = package.run.model_dump(mode="python")
    data["verification"]["status"] = "failed"
    with pytest.raises(ValidationError):
        CrossRuntimeWorkflowRun.model_validate(data)


def test_completed_at_requires_completed_state():
    package = reference_package()
    data = package.run.model_dump(mode="python")
    data["state"] = "running"
    with pytest.raises(ValidationError):
        CrossRuntimeWorkflowRun.model_validate(data)


def test_run_fingerprint_ignores_lifecycle_and_events():
    run = reference_package().run
    other = deepcopy(run)
    other.state = WorkflowState.running
    other.step_states = {}
    other.events = []
    other.started_at = None
    other.completed_at = None
    assert run.fingerprint() == other.fingerprint()


def test_package_rejects_wrong_workflow_ref():
    package = reference_package()
    run = deepcopy(package.run)
    run.workflow_ref = "workflow:other"
    with pytest.raises(ValidationError):
        CrossRuntimeWorkflowPackage(
            package_id="package:test",
            definition=package.definition,
            run=run,
        )


def test_package_rejects_wrong_workflow_fingerprint():
    package = reference_package()
    run = deepcopy(package.run)
    run.workflow_fingerprint_sha256 = "f" * 64
    with pytest.raises(ValidationError):
        CrossRuntimeWorkflowPackage(
            package_id="package:test",
            definition=package.definition,
            run=run,
        )


def test_package_rejects_verification_wrong_workflow():
    package = reference_package()
    run = deepcopy(package.run)
    assert run.verification is not None
    run.verification.workflow_ref = "workflow:other"
    with pytest.raises(ValidationError):
        CrossRuntimeWorkflowPackage(
            package_id="package:test",
            definition=package.definition,
            run=run,
        )


def test_package_fingerprint_stable():
    package = reference_package()
    assert package.fingerprint() == deepcopy(package).fingerprint()
    assert len(package.fingerprint()) == 64


def test_reference_verification_covers_all_steps():
    package = reference_package()
    verification = package.run.verification
    assert verification is not None
    assert set(verification.completed_step_refs) == {
        step.step_id for step in package.definition.steps
    }


def test_reference_verification_covers_handoff():
    package = reference_package()
    verification = package.run.verification
    assert verification is not None
    assert verification.verified_handoff_refs == [
        "handoff:r-to-julia:reference-regression"
    ]


def test_reference_events_cover_runtime_steps():
    package = reference_package()
    runtime_refs = {
        event.runtime_ref
        for event in package.run.events
        if event.runtime_ref
    }
    assert REFERENCE_R_RUNTIME in runtime_refs
    assert REFERENCE_JULIA_RUNTIME in runtime_refs


def test_scientific_artifact_bridge():
    package = reference_package()
    payload = to_scientific_workflow_artifact(package)
    assert payload["artifact_kind"] == "package"
    assert payload["source_contract"] == CONTRACT_VERSION
    assert payload["content_sha256"] == package.fingerprint()


def test_scientific_artifact_bridge_validates_v338():
    from app.services.scientific_result_registry import ScientificArtifactRef

    payload = to_scientific_workflow_artifact(reference_package())
    validated = ScientificArtifactRef.model_validate(payload)
    assert validated.source_contract == CONTRACT_VERSION


def test_scientific_artifact_lists_runtime_refs():
    payload = to_scientific_workflow_artifact(reference_package())
    assert payload["metadata"]["runtime_refs"] == [
        REFERENCE_JULIA_RUNTIME,
        REFERENCE_R_RUNTIME,
    ]


def test_workflow_dependency_types_cover_data_and_provenance():
    values = {item.value for item in WorkflowDependencyType}
    assert {"hard", "soft", "data", "evidence", "provenance"}.issubset(values)


def test_workflow_step_kinds_cover_research_pipeline():
    values = {item.value for item in WorkflowStepKind}
    assert {
        "compute",
        "statistical-analysis",
        "data-interchange",
        "scientific-registration",
        "model-training",
        "inference",
        "evaluation",
        "visualization",
        "publication",
    }.issubset(values)


def test_core_does_not_execute_runtime_steps():
    doc = contract_document()
    assert doc["boundaries"]["core_executes_runtime_steps"] is False


def test_core_does_not_schedule_jobs():
    doc = contract_document()
    assert doc["boundaries"]["core_schedules_jobs"] is False
    assert doc["integration"]["workspace_or_execution_host_orchestrates"] is True


def test_core_does_not_autoselect_runtime_or_format():
    doc = contract_document()
    assert doc["boundaries"]["core_autonomously_selects_runtime"] is False
    assert doc["boundaries"]["core_autonomously_selects_interchange_format"] is False


def test_core_does_not_certify_scientific_validity():
    doc = contract_document()
    assert doc["boundaries"]["core_certifies_scientific_validity"] is False


def test_reference_contract_exposes_ready_after_r_step():
    doc = contract_document()
    assert doc["reference"]["ready_after_r_step"] == ["workflow-step:julia-matrix"]
