from __future__ import annotations

from collections import defaultdict, deque
from datetime import datetime, timezone
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, model_validator

from .computational_runtime_objects import canonical_sha256

CORE_RELEASE = "3.40.0"
CONTRACT_VERSION = "sc.core.cross-runtime-research-workflow.v1"

RUNTIME_INTERCHANGE_CONTRACT = "sc.core.runtime-data-interchange.v1"
STATISTICAL_ANALYSIS_CONTRACT = "sc.core.statistical-analysis-object.v1"
SCIENTIFIC_REGISTRY_CONTRACT = "sc.core.scientific-result-artifact-registry.v1"
AI_RESEARCH_OBJECT_CONTRACT = "sc.core.ai-research-object-system.v1"
COMPUTATIONAL_JOB_CONTRACT = "sc.core.computational-job.v1"
ENVIRONMENT_PROVENANCE_CONTRACT = "sc.core.execution-environment-provenance.v1"
RUNTIME_ADAPTER_CONTRACT = "sc.core.runtime-adapter.v1"

REFERENCE_R_RUNTIME = "sc-runtime-r"
REFERENCE_R_VERSION = "1.0.0"
REFERENCE_JULIA_RUNTIME = "catalyst-julia-runtime"
REFERENCE_JULIA_VERSION = "0.3.0"


class WorkflowState(str, Enum):
    declared = "declared"
    ready = "ready"
    running = "running"
    blocked = "blocked"
    completed = "completed"
    failed = "failed"
    cancelled = "cancelled"


class WorkflowStepState(str, Enum):
    declared = "declared"
    ready = "ready"
    queued = "queued"
    running = "running"
    completed = "completed"
    failed = "failed"
    blocked = "blocked"
    skipped = "skipped"
    cancelled = "cancelled"


class WorkflowStepKind(str, Enum):
    compute = "compute"
    statistical_analysis = "statistical-analysis"
    data_interchange = "data-interchange"
    scientific_registration = "scientific-registration"
    validation = "validation"
    model_training = "model-training"
    inference = "inference"
    evaluation = "evaluation"
    visualization = "visualization"
    publication = "publication"
    other = "other"


class WorkflowDependencyType(str, Enum):
    hard = "hard"
    soft = "soft"
    data = "data"
    evidence = "evidence"
    provenance = "provenance"


class HandoffState(str, Enum):
    declared = "declared"
    prepared = "prepared"
    transferred = "transferred"
    verified = "verified"
    failed = "failed"


class WorkflowVerificationStatus(str, Enum):
    not_run = "not-run"
    passed = "passed"
    warning = "warning"
    failed = "failed"


class WorkflowRuntimeBinding(BaseModel):
    binding_id: str = Field(min_length=2, max_length=500)
    runtime_ref: str = Field(min_length=2, max_length=500)
    runtime_version: str = Field(min_length=1, max_length=200)
    runtime_adapter_ref: str = Field(min_length=2, max_length=500)
    environment_ref: str = Field(min_length=2, max_length=500)
    required_operations: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_binding(self):
        if len(self.required_operations) != len(set(self.required_operations)):
            raise ValueError("required runtime operations must be unique")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class WorkflowInputBinding(BaseModel):
    input_id: str = Field(min_length=2, max_length=500)
    logical_data_ref: str = Field(min_length=2, max_length=1000)
    source_artifact_ref: str | None = Field(default=None, max_length=1000)
    source_result_ref: str | None = Field(default=None, max_length=1000)
    schema_ref: str | None = Field(default=None, max_length=1000)
    required: bool = True
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def require_source(self):
        if not self.source_artifact_ref and not self.source_result_ref:
            raise ValueError("workflow input requires artifact or result source")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class WorkflowOutputBinding(BaseModel):
    output_id: str = Field(min_length=2, max_length=500)
    logical_data_ref: str = Field(min_length=2, max_length=1000)
    artifact_ref: str | None = Field(default=None, max_length=1000)
    result_ref: str | None = Field(default=None, max_length=1000)
    schema_ref: str | None = Field(default=None, max_length=1000)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def require_target(self):
        if not self.artifact_ref and not self.result_ref:
            raise ValueError("workflow output requires artifact or result reference")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class CrossRuntimeWorkflowStep(BaseModel):
    step_id: str = Field(min_length=2, max_length=500)
    name: str = Field(min_length=1, max_length=500)
    kind: WorkflowStepKind
    runtime_binding_ref: str | None = Field(default=None, max_length=500)
    computational_job_ref: str | None = Field(default=None, max_length=500)
    statistical_analysis_plan_ref: str | None = Field(default=None, max_length=500)
    scientific_registry_ref: str | None = Field(default=None, max_length=500)
    operation: str | None = Field(default=None, max_length=300)
    inputs: list[WorkflowInputBinding] = Field(default_factory=list)
    outputs: list[WorkflowOutputBinding] = Field(default_factory=list)
    state: WorkflowStepState = WorkflowStepState.declared
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_step(self):
        input_ids = [item.input_id for item in self.inputs]
        output_ids = [item.output_id for item in self.outputs]
        if len(input_ids) != len(set(input_ids)):
            raise ValueError("workflow step input ids must be unique")
        if len(output_ids) != len(set(output_ids)):
            raise ValueError("workflow step output ids must be unique")

        if self.kind in {
            WorkflowStepKind.compute,
            WorkflowStepKind.statistical_analysis,
            WorkflowStepKind.model_training,
            WorkflowStepKind.inference,
            WorkflowStepKind.evaluation,
        } and not self.runtime_binding_ref:
            raise ValueError("computational workflow step requires runtime binding")
        return self

    def fingerprint(self) -> str:
        payload = self.model_dump(mode="json", exclude_none=True)
        payload.pop("state", None)
        return canonical_sha256(payload)


class WorkflowDependency(BaseModel):
    dependency_id: str = Field(min_length=2, max_length=500)
    upstream_step_ref: str = Field(min_length=2, max_length=500)
    downstream_step_ref: str = Field(min_length=2, max_length=500)
    dependency_type: WorkflowDependencyType = WorkflowDependencyType.hard
    required_output_refs: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_dependency(self):
        if self.upstream_step_ref == self.downstream_step_ref:
            raise ValueError("workflow dependency cannot be self-referential")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class RuntimeHandoff(BaseModel):
    handoff_id: str = Field(min_length=2, max_length=500)
    source_step_ref: str = Field(min_length=2, max_length=500)
    target_step_ref: str = Field(min_length=2, max_length=500)
    source_runtime_ref: str = Field(min_length=2, max_length=500)
    target_runtime_ref: str = Field(min_length=2, max_length=500)
    logical_data_ref: str = Field(min_length=2, max_length=1000)
    interchange_transfer_ref: str = Field(min_length=2, max_length=1000)
    source_artifact_ref: str = Field(min_length=2, max_length=1000)
    target_artifact_ref: str = Field(min_length=2, max_length=1000)
    verification_ref: str = Field(min_length=2, max_length=1000)
    state: HandoffState = HandoffState.declared
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_handoff(self):
        if self.source_step_ref == self.target_step_ref:
            raise ValueError("runtime handoff must cross workflow steps")
        if self.source_runtime_ref == self.target_runtime_ref:
            raise ValueError("runtime handoff must cross runtimes")
        return self

    def fingerprint(self) -> str:
        payload = self.model_dump(mode="json", exclude_none=True)
        payload.pop("state", None)
        return canonical_sha256(payload)


class CrossRuntimeWorkflowDefinition(BaseModel):
    workflow_id: str = Field(min_length=2, max_length=500)
    name: str = Field(min_length=1, max_length=500)
    objective: str = Field(min_length=1, max_length=20000)
    runtime_bindings: list[WorkflowRuntimeBinding] = Field(default_factory=list)
    steps: list[CrossRuntimeWorkflowStep] = Field(default_factory=list)
    dependencies: list[WorkflowDependency] = Field(default_factory=list)
    handoffs: list[RuntimeHandoff] = Field(default_factory=list)
    source_object_refs: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    provenance: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_workflow(self):
        runtime_ids = [item.binding_id for item in self.runtime_bindings]
        step_ids = [item.step_id for item in self.steps]
        dependency_ids = [item.dependency_id for item in self.dependencies]
        handoff_ids = [item.handoff_id for item in self.handoffs]

        if len(runtime_ids) != len(set(runtime_ids)):
            raise ValueError("workflow runtime binding ids must be unique")
        if len(step_ids) != len(set(step_ids)):
            raise ValueError("workflow step ids must be unique")
        if len(dependency_ids) != len(set(dependency_ids)):
            raise ValueError("workflow dependency ids must be unique")
        if len(handoff_ids) != len(set(handoff_ids)):
            raise ValueError("workflow handoff ids must be unique")
        if not self.steps:
            raise ValueError("cross-runtime workflow requires steps")

        runtimes = set(runtime_ids)
        steps = set(step_ids)

        for step in self.steps:
            if step.runtime_binding_ref and step.runtime_binding_ref not in runtimes:
                raise ValueError("workflow step references unknown runtime binding")

        for dep in self.dependencies:
            if dep.upstream_step_ref not in steps or dep.downstream_step_ref not in steps:
                raise ValueError("workflow dependency references unknown step")

        for handoff in self.handoffs:
            if handoff.source_step_ref not in steps or handoff.target_step_ref not in steps:
                raise ValueError("runtime handoff references unknown step")

        _validate_acyclic(step_ids, self.dependencies)
        _validate_handoff_dependencies(self.dependencies, self.handoffs)

        runtime_refs = {
            item.binding_id: item.runtime_ref
            for item in self.runtime_bindings
        }
        step_by_id = {item.step_id: item for item in self.steps}
        for handoff in self.handoffs:
            source_step = step_by_id[handoff.source_step_ref]
            target_step = step_by_id[handoff.target_step_ref]
            if not source_step.runtime_binding_ref or not target_step.runtime_binding_ref:
                raise ValueError("runtime handoff steps require runtime bindings")
            if runtime_refs[source_step.runtime_binding_ref] != handoff.source_runtime_ref:
                raise ValueError("handoff source runtime does not match source step")
            if runtime_refs[target_step.runtime_binding_ref] != handoff.target_runtime_ref:
                raise ValueError("handoff target runtime does not match target step")

        return self

    def fingerprint(self) -> str:
        payload = self.model_dump(mode="json", exclude_none=True)
        payload.pop("created_at", None)
        return canonical_sha256(payload)


class WorkflowReadinessStep(BaseModel):
    step_ref: str
    ready: bool
    blockers: list[str] = Field(default_factory=list)


class WorkflowReadinessReport(BaseModel):
    workflow_ref: str
    ready_step_refs: list[str] = Field(default_factory=list)
    blocked_step_refs: list[str] = Field(default_factory=list)
    step_reports: list[WorkflowReadinessStep] = Field(default_factory=list)

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class WorkflowExecutionEvent(BaseModel):
    event_id: str = Field(min_length=2, max_length=500)
    workflow_ref: str = Field(min_length=2, max_length=500)
    step_ref: str | None = Field(default=None, max_length=500)
    event_type: str = Field(min_length=1, max_length=300)
    previous_state: str | None = Field(default=None, max_length=100)
    new_state: str | None = Field(default=None, max_length=100)
    job_ref: str | None = Field(default=None, max_length=500)
    runtime_ref: str | None = Field(default=None, max_length=500)
    artifact_refs: list[str] = Field(default_factory=list)
    result_refs: list[str] = Field(default_factory=list)
    occurred_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    provenance: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)

    def fingerprint(self) -> str:
        payload = self.model_dump(mode="json", exclude_none=True)
        payload.pop("occurred_at", None)
        return canonical_sha256(payload)


class WorkflowVerification(BaseModel):
    verification_id: str = Field(min_length=2, max_length=500)
    workflow_ref: str = Field(min_length=2, max_length=500)
    status: WorkflowVerificationStatus = WorkflowVerificationStatus.not_run
    step_fingerprints: dict[str, str] = Field(default_factory=dict)
    handoff_fingerprints: dict[str, str] = Field(default_factory=dict)
    completed_step_refs: list[str] = Field(default_factory=list)
    verified_handoff_refs: list[str] = Field(default_factory=list)
    final_artifact_refs: list[str] = Field(default_factory=list)
    final_result_refs: list[str] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_hashes(self):
        for value in list(self.step_fingerprints.values()) + list(self.handoff_fingerprints.values()):
            if len(value) != 64 or any(ch not in "0123456789abcdef" for ch in value):
                raise ValueError("workflow verification fingerprints must be lowercase SHA-256")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class CrossRuntimeWorkflowRun(BaseModel):
    workflow_run_id: str = Field(min_length=2, max_length=500)
    workflow_ref: str = Field(min_length=2, max_length=500)
    workflow_fingerprint_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    state: WorkflowState = WorkflowState.declared
    step_states: dict[str, WorkflowStepState] = Field(default_factory=dict)
    events: list[WorkflowExecutionEvent] = Field(default_factory=list)
    verification: WorkflowVerification | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    provenance: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_run(self):
        event_ids = [item.event_id for item in self.events]
        if len(event_ids) != len(set(event_ids)):
            raise ValueError("workflow event ids must be unique")
        if self.completed_at is not None and self.state != WorkflowState.completed:
            raise ValueError("completed_at requires completed workflow state")
        if self.state == WorkflowState.completed:
            if not self.verification or self.verification.status not in {
                WorkflowVerificationStatus.passed,
                WorkflowVerificationStatus.warning,
            }:
                raise ValueError("completed workflow requires successful verification")
        return self

    def fingerprint(self) -> str:
        payload = self.model_dump(mode="json", exclude_none=True)
        for key in ("state", "step_states", "events", "started_at", "completed_at"):
            payload.pop(key, None)
        return canonical_sha256(payload)


class CrossRuntimeWorkflowPackage(BaseModel):
    package_id: str = Field(min_length=2, max_length=500)
    definition: CrossRuntimeWorkflowDefinition
    run: CrossRuntimeWorkflowRun
    scientific_registry_refs: list[str] = Field(default_factory=list)
    interchange_bundle_refs: list[str] = Field(default_factory=list)
    source_object_refs: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_package(self):
        if self.run.workflow_ref != self.definition.workflow_id:
            raise ValueError("workflow run must reference package definition")
        if self.run.workflow_fingerprint_sha256 != self.definition.fingerprint():
            raise ValueError("workflow run fingerprint does not match definition")
        if self.run.verification and self.run.verification.workflow_ref != self.definition.workflow_id:
            raise ValueError("workflow verification references wrong workflow")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256({
            "package_id": self.package_id,
            "definition_fingerprint_sha256": self.definition.fingerprint(),
            "run_fingerprint_sha256": self.run.fingerprint(),
            "scientific_registry_refs": sorted(self.scientific_registry_refs),
            "interchange_bundle_refs": sorted(self.interchange_bundle_refs),
            "source_object_refs": sorted(self.source_object_refs),
            "metadata": self.metadata,
        })


def _validate_acyclic(
    step_ids: list[str],
    dependencies: list[WorkflowDependency],
) -> None:
    incoming: dict[str, int] = {step_id: 0 for step_id in step_ids}
    outgoing: dict[str, list[str]] = defaultdict(list)

    for dep in dependencies:
        outgoing[dep.upstream_step_ref].append(dep.downstream_step_ref)
        incoming[dep.downstream_step_ref] += 1

    queue = deque(sorted(step for step, count in incoming.items() if count == 0))
    visited = 0
    while queue:
        step = queue.popleft()
        visited += 1
        for downstream in sorted(outgoing.get(step, [])):
            incoming[downstream] -= 1
            if incoming[downstream] == 0:
                queue.append(downstream)

    if visited != len(step_ids):
        raise ValueError("cross-runtime workflow dependency graph must be acyclic")


def _validate_handoff_dependencies(
    dependencies: list[WorkflowDependency],
    handoffs: list[RuntimeHandoff],
) -> None:
    edges = {
        (dep.upstream_step_ref, dep.downstream_step_ref)
        for dep in dependencies
    }
    for handoff in handoffs:
        if (handoff.source_step_ref, handoff.target_step_ref) not in edges:
            raise ValueError("runtime handoff requires matching workflow dependency")


def topological_step_order(
    workflow: CrossRuntimeWorkflowDefinition,
) -> list[str]:
    incoming: dict[str, int] = {step.step_id: 0 for step in workflow.steps}
    outgoing: dict[str, list[str]] = defaultdict(list)
    for dep in workflow.dependencies:
        outgoing[dep.upstream_step_ref].append(dep.downstream_step_ref)
        incoming[dep.downstream_step_ref] += 1

    queue = deque(sorted(step for step, count in incoming.items() if count == 0))
    ordered: list[str] = []

    while queue:
        current = queue.popleft()
        ordered.append(current)
        for downstream in sorted(outgoing.get(current, [])):
            incoming[downstream] -= 1
            if incoming[downstream] == 0:
                queue.append(downstream)

    if len(ordered) != len(workflow.steps):
        raise ValueError("workflow cannot be topologically ordered")
    return ordered


def workflow_readiness(
    workflow: CrossRuntimeWorkflowDefinition,
    completed_step_refs: list[str],
    verified_handoff_refs: list[str] | None = None,
) -> WorkflowReadinessReport:
    completed = set(completed_step_refs)
    verified_handoffs = set(verified_handoff_refs or [])
    step_ids = {step.step_id for step in workflow.steps}

    unknown = completed - step_ids
    if unknown:
        raise ValueError("completed step refs contain unknown workflow steps")

    incoming: dict[str, list[WorkflowDependency]] = defaultdict(list)
    for dep in workflow.dependencies:
        incoming[dep.downstream_step_ref].append(dep)

    handoffs_to_target: dict[str, list[RuntimeHandoff]] = defaultdict(list)
    for handoff in workflow.handoffs:
        handoffs_to_target[handoff.target_step_ref].append(handoff)

    reports: list[WorkflowReadinessStep] = []
    ready: list[str] = []
    blocked: list[str] = []

    for step in workflow.steps:
        if step.step_id in completed:
            continue

        blockers: list[str] = []
        for dep in incoming.get(step.step_id, []):
            if dep.dependency_type in {
                WorkflowDependencyType.hard,
                WorkflowDependencyType.data,
            } and dep.upstream_step_ref not in completed:
                blockers.append(f"dependency:{dep.upstream_step_ref}")

        for handoff in handoffs_to_target.get(step.step_id, []):
            if handoff.handoff_id not in verified_handoffs:
                blockers.append(f"handoff:{handoff.handoff_id}")

        is_ready = not blockers
        reports.append(
            WorkflowReadinessStep(
                step_ref=step.step_id,
                ready=is_ready,
                blockers=sorted(blockers),
            )
        )
        if is_ready:
            ready.append(step.step_id)
        else:
            blocked.append(step.step_id)

    return WorkflowReadinessReport(
        workflow_ref=workflow.workflow_id,
        ready_step_refs=sorted(ready),
        blocked_step_refs=sorted(blocked),
        step_reports=reports,
    )


def to_scientific_workflow_artifact(
    package: CrossRuntimeWorkflowPackage,
) -> dict[str, Any]:
    return {
        "artifact_id": f"scientific-artifact:{package.package_id}",
        "artifact_kind": "package",
        "uri": f"core-ref://{package.package_id}",
        "content_sha256": package.fingerprint(),
        "media_type": "application/vnd.sustainable-catalyst.cross-runtime-workflow+json",
        "source_contract": CONTRACT_VERSION,
        "source_object_ref": package.package_id,
        "metadata": {
            "workflow_ref": package.definition.workflow_id,
            "workflow_run_ref": package.run.workflow_run_id,
            "workflow_state": package.run.state.value,
            "runtime_refs": sorted(
                {binding.runtime_ref for binding in package.definition.runtime_bindings}
            ),
        },
    }


def reference_cross_runtime_workflow_package() -> CrossRuntimeWorkflowPackage:
    r_binding = WorkflowRuntimeBinding(
        binding_id="runtime-binding:r",
        runtime_ref=REFERENCE_R_RUNTIME,
        runtime_version=REFERENCE_R_VERSION,
        runtime_adapter_ref="adapter:sc-runtime-r",
        environment_ref="environment:reference-r-runtime-1.0",
        required_operations=["linear_regression"],
    )
    julia_binding = WorkflowRuntimeBinding(
        binding_id="runtime-binding:julia",
        runtime_ref=REFERENCE_JULIA_RUNTIME,
        runtime_version=REFERENCE_JULIA_VERSION,
        runtime_adapter_ref="adapter:catalyst-julia-runtime",
        environment_ref="environment:reference-julia-runtime-0.3",
        required_operations=["matrix_multiply"],
    )

    r_step = CrossRuntimeWorkflowStep(
        step_id="workflow-step:r-regression",
        name="R Regression Analysis",
        kind=WorkflowStepKind.statistical_analysis,
        runtime_binding_ref=r_binding.binding_id,
        computational_job_ref="job:reference-r-regression",
        statistical_analysis_plan_ref="stat-plan:reference-regression:v1",
        operation="linear_regression",
        inputs=[
            WorkflowInputBinding(
                input_id="input:r-regression-data",
                logical_data_ref="logical-data:reference-regression-table:v1",
                source_artifact_ref="scientific-artifact:reference-regression-input",
            )
        ],
        outputs=[
            WorkflowOutputBinding(
                output_id="output:r-regression-table",
                logical_data_ref="logical-data:reference-regression-table:v1",
                artifact_ref="interchange-artifact:r-json:reference-regression:v1",
            ),
            WorkflowOutputBinding(
                output_id="output:r-regression-result",
                logical_data_ref="logical-result:reference-regression:v1",
                result_ref="stat-result:reference-regression:001",
            ),
        ],
        state=WorkflowStepState.completed,
    )

    julia_step = CrossRuntimeWorkflowStep(
        step_id="workflow-step:julia-matrix",
        name="Julia Matrix Analysis",
        kind=WorkflowStepKind.compute,
        runtime_binding_ref=julia_binding.binding_id,
        computational_job_ref="job:reference-julia-matrix",
        operation="matrix_multiply",
        inputs=[
            WorkflowInputBinding(
                input_id="input:julia-regression-table",
                logical_data_ref="logical-data:reference-regression-table:v1",
                source_artifact_ref="interchange-artifact:julia-json:reference-regression:v1",
            )
        ],
        outputs=[
            WorkflowOutputBinding(
                output_id="output:julia-matrix-result",
                logical_data_ref="logical-result:reference-julia-matrix:v1",
                result_ref="runtime-result:reference-julia-matrix",
            )
        ],
        state=WorkflowStepState.completed,
    )

    registry_step = CrossRuntimeWorkflowStep(
        step_id="workflow-step:scientific-registration",
        name="Register Cross-Runtime Results",
        kind=WorkflowStepKind.scientific_registration,
        scientific_registry_ref="scientific-registry:cross-runtime-reference:v1",
        inputs=[
            WorkflowInputBinding(
                input_id="input:registration-r-result",
                logical_data_ref="logical-result:reference-regression:v1",
                source_result_ref="stat-result:reference-regression:001",
            ),
            WorkflowInputBinding(
                input_id="input:registration-julia-result",
                logical_data_ref="logical-result:reference-julia-matrix:v1",
                source_result_ref="runtime-result:reference-julia-matrix",
            ),
        ],
        outputs=[
            WorkflowOutputBinding(
                output_id="output:scientific-registry",
                logical_data_ref="logical-registry:cross-runtime-reference:v1",
                artifact_ref="scientific-artifact:cross-runtime-reference-package",
            )
        ],
        state=WorkflowStepState.completed,
    )

    dependencies = [
        WorkflowDependency(
            dependency_id="dependency:r-to-julia",
            upstream_step_ref=r_step.step_id,
            downstream_step_ref=julia_step.step_id,
            dependency_type=WorkflowDependencyType.data,
            required_output_refs=["output:r-regression-table"],
        ),
        WorkflowDependency(
            dependency_id="dependency:r-to-registry",
            upstream_step_ref=r_step.step_id,
            downstream_step_ref=registry_step.step_id,
            dependency_type=WorkflowDependencyType.hard,
            required_output_refs=["output:r-regression-result"],
        ),
        WorkflowDependency(
            dependency_id="dependency:julia-to-registry",
            upstream_step_ref=julia_step.step_id,
            downstream_step_ref=registry_step.step_id,
            dependency_type=WorkflowDependencyType.hard,
            required_output_refs=["output:julia-matrix-result"],
        ),
    ]

    handoff = RuntimeHandoff(
        handoff_id="handoff:r-to-julia:reference-regression",
        source_step_ref=r_step.step_id,
        target_step_ref=julia_step.step_id,
        source_runtime_ref=REFERENCE_R_RUNTIME,
        target_runtime_ref=REFERENCE_JULIA_RUNTIME,
        logical_data_ref="logical-data:reference-regression-table:v1",
        interchange_transfer_ref="interchange-transfer:r-to-julia:reference-regression:v1",
        source_artifact_ref="interchange-artifact:r-json:reference-regression:v1",
        target_artifact_ref="interchange-artifact:julia-json:reference-regression:v1",
        verification_ref="interchange-verification:r-to-julia:reference-regression:v1",
        state=HandoffState.verified,
    )

    definition = CrossRuntimeWorkflowDefinition(
        workflow_id="cross-runtime-workflow:reference-r-julia:v1",
        name="Reference R to Julia Research Workflow",
        objective=(
            "Demonstrate a reproducible research workflow spanning R statistical "
            "analysis, verified runtime-data interchange, Julia computation, and "
            "scientific result registration."
        ),
        runtime_bindings=[r_binding, julia_binding],
        steps=[r_step, julia_step, registry_step],
        dependencies=dependencies,
        handoffs=[handoff],
        source_object_refs=[
            "stat-package:reference-regression:v1",
            "runtime-data-interchange-bundle:reference-r-julia:v1",
        ],
        provenance={
            "core_schedules_workflow": False,
            "workspace_or_execution_host_orchestrates": True,
        },
    )

    events = [
        WorkflowExecutionEvent(
            event_id="workflow-event:r-completed",
            workflow_ref=definition.workflow_id,
            step_ref=r_step.step_id,
            event_type="step-completed",
            previous_state="running",
            new_state="completed",
            job_ref=r_step.computational_job_ref,
            runtime_ref=REFERENCE_R_RUNTIME,
            result_refs=["stat-result:reference-regression:001"],
        ),
        WorkflowExecutionEvent(
            event_id="workflow-event:handoff-verified",
            workflow_ref=definition.workflow_id,
            step_ref=julia_step.step_id,
            event_type="handoff-verified",
            runtime_ref=REFERENCE_JULIA_RUNTIME,
            artifact_refs=[handoff.target_artifact_ref],
        ),
        WorkflowExecutionEvent(
            event_id="workflow-event:julia-completed",
            workflow_ref=definition.workflow_id,
            step_ref=julia_step.step_id,
            event_type="step-completed",
            previous_state="running",
            new_state="completed",
            job_ref=julia_step.computational_job_ref,
            runtime_ref=REFERENCE_JULIA_RUNTIME,
            result_refs=["runtime-result:reference-julia-matrix"],
        ),
        WorkflowExecutionEvent(
            event_id="workflow-event:registry-completed",
            workflow_ref=definition.workflow_id,
            step_ref=registry_step.step_id,
            event_type="step-completed",
            previous_state="running",
            new_state="completed",
            artifact_refs=["scientific-artifact:cross-runtime-reference-package"],
        ),
    ]

    verification = WorkflowVerification(
        verification_id="workflow-verification:reference-r-julia:v1",
        workflow_ref=definition.workflow_id,
        status=WorkflowVerificationStatus.passed,
        step_fingerprints={
            step.step_id: step.fingerprint()
            for step in definition.steps
        },
        handoff_fingerprints={
            handoff.handoff_id: handoff.fingerprint()
        },
        completed_step_refs=[step.step_id for step in definition.steps],
        verified_handoff_refs=[handoff.handoff_id],
        final_artifact_refs=["scientific-artifact:cross-runtime-reference-package"],
        final_result_refs=[
            "stat-result:reference-regression:001",
            "runtime-result:reference-julia-matrix",
        ],
        notes=[
            "Reference workflow is a contract proof; production execution remains owned by Workspace or an execution host.",
            "Core validates dependencies, handoffs, fingerprints and completion evidence but does not schedule jobs.",
        ],
    )

    run = CrossRuntimeWorkflowRun(
        workflow_run_id="cross-runtime-workflow-run:reference-r-julia:001",
        workflow_ref=definition.workflow_id,
        workflow_fingerprint_sha256=definition.fingerprint(),
        state=WorkflowState.completed,
        step_states={
            step.step_id: WorkflowStepState.completed
            for step in definition.steps
        },
        events=events,
        verification=verification,
        started_at=datetime(2026, 9, 25, 9, 0, tzinfo=timezone.utc),
        completed_at=datetime(2026, 9, 25, 9, 5, tzinfo=timezone.utc),
        provenance={
            "execution_host": "reference-contract",
            "core_scheduled_execution": False,
        },
    )

    return CrossRuntimeWorkflowPackage(
        package_id="cross-runtime-workflow-package:reference-r-julia:v1",
        definition=definition,
        run=run,
        scientific_registry_refs=["scientific-registry:cross-runtime-reference:v1"],
        interchange_bundle_refs=["runtime-data-interchange-bundle:reference-r-julia:v1"],
        source_object_refs=[
            "stat-package:reference-regression:v1",
            "scientific-registry-package:reference-regression:v1",
        ],
        metadata={
            "portable": True,
            "reproducible": True,
        },
    )


def contract_document() -> dict[str, Any]:
    reference = reference_cross_runtime_workflow_package()
    readiness = workflow_readiness(
        reference.definition,
        completed_step_refs=["workflow-step:r-regression"],
        verified_handoff_refs=["handoff:r-to-julia:reference-regression"],
    )
    return {
        "ok": True,
        "release": CORE_RELEASE,
        "contract": CONTRACT_VERSION,
        "depends_on": [
            RUNTIME_INTERCHANGE_CONTRACT,
            STATISTICAL_ANALYSIS_CONTRACT,
            SCIENTIFIC_REGISTRY_CONTRACT,
            AI_RESEARCH_OBJECT_CONTRACT,
            COMPUTATIONAL_JOB_CONTRACT,
            ENVIRONMENT_PROVENANCE_CONTRACT,
            RUNTIME_ADAPTER_CONTRACT,
        ],
        "object_types": [
            "WorkflowRuntimeBinding",
            "WorkflowInputBinding",
            "WorkflowOutputBinding",
            "CrossRuntimeWorkflowStep",
            "WorkflowDependency",
            "RuntimeHandoff",
            "CrossRuntimeWorkflowDefinition",
            "WorkflowReadinessReport",
            "WorkflowExecutionEvent",
            "WorkflowVerification",
            "CrossRuntimeWorkflowRun",
            "CrossRuntimeWorkflowPackage",
        ],
        "capabilities": {
            "multi_runtime_workflow_definitions": True,
            "typed_step_dependencies": True,
            "acyclic_workflow_validation": True,
            "topological_step_order": True,
            "runtime_handoff_bindings": True,
            "interchange_transfer_bindings": True,
            "workflow_readiness_evaluation": True,
            "workflow_event_provenance": True,
            "workflow_verification": True,
            "scientific_registry_packaging": True,
            "portable_cross_runtime_packages": True,
        },
        "integration": {
            "r_runtime": True,
            "julia_runtime": True,
            "runtime_data_interchange": True,
            "statistical_analysis_objects": True,
            "scientific_result_registry": True,
            "workspace_or_execution_host_orchestrates": True,
            "core_schedules_execution": False,
        },
        "boundaries": {
            "core_executes_runtime_steps": False,
            "core_schedules_jobs": False,
            "core_autonomously_selects_runtime": False,
            "core_autonomously_selects_interchange_format": False,
            "core_certifies_scientific_validity": False,
            "core_owns_workflow_contracts_dependencies_handoffs_and_provenance": True,
        },
        "reference": {
            "workflow_id": reference.definition.workflow_id,
            "workflow_run_id": reference.run.workflow_run_id,
            "package_id": reference.package_id,
            "topological_order": topological_step_order(reference.definition),
            "ready_after_r_step": readiness.ready_step_refs,
            "package_fingerprint_sha256": reference.fingerprint(),
        },
    }
