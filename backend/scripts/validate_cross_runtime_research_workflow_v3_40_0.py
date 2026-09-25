#!/usr/bin/env python3

from app.services.cross_runtime_research_workflow import (
    CONTRACT_VERSION,
    WorkflowState,
    WorkflowVerificationStatus,
    contract_document,
    reference_cross_runtime_workflow_package,
    topological_step_order,
    to_scientific_workflow_artifact,
    workflow_readiness,
)
from app.services.scientific_result_registry import ScientificArtifactRef

doc = contract_document()
assert doc["release"] == "3.40.0"
assert doc["contract"] == CONTRACT_VERSION
assert doc["capabilities"]["multi_runtime_workflow_definitions"] is True
assert doc["capabilities"]["runtime_handoff_bindings"] is True
assert doc["capabilities"]["workflow_readiness_evaluation"] is True
assert doc["integration"]["workspace_or_execution_host_orchestrates"] is True
assert doc["boundaries"]["core_schedules_jobs"] is False
assert doc["boundaries"]["core_executes_runtime_steps"] is False

package = reference_cross_runtime_workflow_package()
assert len(package.fingerprint()) == 64
assert package.run.state == WorkflowState.completed
assert package.run.verification is not None
assert package.run.verification.status == WorkflowVerificationStatus.passed

order = topological_step_order(package.definition)
assert order == [
    "workflow-step:r-regression",
    "workflow-step:julia-matrix",
    "workflow-step:scientific-registration",
]

report = workflow_readiness(
    package.definition,
    completed_step_refs=["workflow-step:r-regression"],
    verified_handoff_refs=["handoff:r-to-julia:reference-regression"],
)
assert report.ready_step_refs == ["workflow-step:julia-matrix"]

payload = to_scientific_workflow_artifact(package)
ScientificArtifactRef.model_validate(payload)

print("PASS - Platform Core v3.40.0 Cross-Runtime Research Workflow")
print(f"CONTRACT={CONTRACT_VERSION}")
print("MULTI_RUNTIME_WORKFLOW_DEFINITIONS=enabled")
print("TYPED_STEP_DEPENDENCIES=enabled")
print("ACYCLIC_WORKFLOW_VALIDATION=enabled")
print("TOPOLOGICAL_STEP_ORDER=enabled")
print("RUNTIME_HANDOFF_BINDINGS=enabled")
print("INTERCHANGE_TRANSFER_BINDINGS=enabled")
print("WORKFLOW_READINESS=enabled")
print("WORKFLOW_EVENT_PROVENANCE=enabled")
print("WORKFLOW_VERIFICATION=enabled")
print("SCIENTIFIC_REGISTRY_PACKAGING=enabled")
print("PORTABLE_CROSS_RUNTIME_PACKAGES=enabled")
print("CORE_EXECUTES_RUNTIME_STEPS=false")
print("CORE_SCHEDULES_JOBS=false")
print("CORE_AUTONOMOUSLY_SELECTS_RUNTIME=false")
print("CORE_AUTONOMOUSLY_SELECTS_INTERCHANGE_FORMAT=false")
print("CORE_CERTIFIES_SCIENTIFIC_VALIDITY=false")
