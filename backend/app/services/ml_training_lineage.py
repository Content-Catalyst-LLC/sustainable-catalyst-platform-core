from __future__ import annotations

from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field, model_validator

from .computational_runtime_objects import canonical_sha256
from .machine_learning_models import MLModelSpecification, MLTrainingPlan, reference_ml_model_bundle

CORE_RELEASE = "3.58.0"
CONTRACT_VERSION = "sc.core.training-run-checkpoint-experiment-lineage.v1"

class MLTrainingRunStatus(str, Enum):
    planned="planned"; queued="queued"; running="running"; completed="completed"; failed="failed"; cancelled="cancelled"; aborted="aborted"

class MLCheckpointKind(str, Enum):
    periodic="periodic"; best="best"; final="final"; manual="manual"; recovery="recovery"

class MLEvaluationSplit(str, Enum):
    train="train"; validation="validation"; test="test"; external="external"; custom="custom"

class MLExperimentRole(str, Enum):
    baseline="baseline"; candidate="candidate"; ablation="ablation"; replication="replication"; sensitivity="sensitivity"; other="other"

class MLSeedState(BaseModel):
    primary_seed: int | None = None
    framework_seeds: dict[str,int] = Field(default_factory=dict)
    deterministic_requested: bool = False
    nondeterminism_notes: list[str] = Field(default_factory=list)
    def fingerprint(self)->str: return canonical_sha256(self)

class MLCodeReference(BaseModel):
    source_ref: str = Field(min_length=2,max_length=1000)
    revision: str = Field(min_length=1,max_length=240)
    content_sha256: str | None = Field(default=None,pattern=r"^[0-9a-f]{64}$")
    dirty_worktree: bool = False
    arbitrary_executable_payload_embedded: Literal[False] = False
    metadata: dict[str,Any] = Field(default_factory=dict)

class MLTrainingEpochRecord(BaseModel):
    epoch_id: str = Field(min_length=2,max_length=300)
    training_run_ref: str = Field(min_length=2,max_length=300)
    epoch_index: int = Field(ge=1)
    global_step_end: int | None = Field(default=None,ge=0)
    scalar_metrics: dict[str,float] = Field(default_factory=dict)
    started_at: str | None = Field(default=None,max_length=80)
    ended_at: str | None = Field(default=None,max_length=80)
    checkpoint_refs: list[str] = Field(default_factory=list)
    metadata: dict[str,Any] = Field(default_factory=dict)
    @model_validator(mode="after")
    def validate_epoch(self):
        if len(self.checkpoint_refs)!=len(set(self.checkpoint_refs)): raise ValueError("epoch checkpoint_refs must be unique")
        return self

class MLCheckpointRecord(BaseModel):
    checkpoint_id: str = Field(min_length=2,max_length=300)
    training_run_ref: str = Field(min_length=2,max_length=300)
    checkpoint_kind: MLCheckpointKind
    artifact_ref: str = Field(min_length=2,max_length=1000)
    artifact_sha256: str | None = Field(default=None,pattern=r"^[0-9a-f]{64}$")
    epoch_index: int | None = Field(default=None,ge=1)
    global_step: int | None = Field(default=None,ge=0)
    metric_snapshot: dict[str,float] = Field(default_factory=dict)
    model_version_ref: str | None = Field(default=None,max_length=500)
    runtime_binding_ref: str | None = Field(default=None,max_length=500)
    environment_ref: str | None = Field(default=None,max_length=500)
    parent_checkpoint_ref: str | None = Field(default=None,max_length=500)
    created_at: str | None = Field(default=None,max_length=80)
    metadata: dict[str,Any] = Field(default_factory=dict)
    @model_validator(mode="after")
    def validate_checkpoint(self):
        if self.parent_checkpoint_ref==self.checkpoint_id: raise ValueError("checkpoint cannot be its own parent")
        return self
    def fingerprint(self)->str: return canonical_sha256(self)

class MLEvaluationRecord(BaseModel):
    evaluation_id: str = Field(min_length=2,max_length=300)
    training_run_ref: str = Field(min_length=2,max_length=300)
    checkpoint_ref: str | None = Field(default=None,max_length=500)
    dataset_version_ref: str = Field(min_length=2,max_length=500)
    split: MLEvaluationSplit
    metrics: dict[str,float] = Field(default_factory=dict)
    evaluation_job_ref: str | None = Field(default=None,max_length=500)
    evaluator_runtime_ref: str | None = Field(default=None,max_length=500)
    artifact_refs: list[str] = Field(default_factory=list)
    created_at: str | None = Field(default=None,max_length=80)
    metadata: dict[str,Any] = Field(default_factory=dict)
    @model_validator(mode="after")
    def validate_evaluation(self):
        if len(self.artifact_refs)!=len(set(self.artifact_refs)): raise ValueError("evaluation artifact_refs must be unique")
        return self
    def fingerprint(self)->str: return canonical_sha256(self)

class MLTrainingRunRecord(BaseModel):
    training_run_id: str = Field(min_length=2,max_length=300)
    experiment_ref: str = Field(min_length=2,max_length=300)
    experiment_role: MLExperimentRole = MLExperimentRole.candidate
    training_plan_ref: str = Field(min_length=2,max_length=500)
    model_spec_ref: str = Field(min_length=2,max_length=500)
    dataset_version_refs: list[str] = Field(min_length=1)
    runtime_binding_ref: str = Field(min_length=2,max_length=500)
    environment_ref: str | None = Field(default=None,max_length=500)
    computational_job_ref: str | None = Field(default=None,max_length=500)
    code_reference: MLCodeReference
    seed_state: MLSeedState
    resolved_parameters: dict[str,Any] = Field(default_factory=dict)
    status: MLTrainingRunStatus
    started_at: str | None = Field(default=None,max_length=80)
    ended_at: str | None = Field(default=None,max_length=80)
    parent_run_ref: str | None = Field(default=None,max_length=500)
    resumed_from_checkpoint_ref: str | None = Field(default=None,max_length=500)
    output_model_version_ref: str | None = Field(default=None,max_length=500)
    epochs: list[MLTrainingEpochRecord] = Field(default_factory=list)
    checkpoints: list[MLCheckpointRecord] = Field(default_factory=list)
    evaluations: list[MLEvaluationRecord] = Field(default_factory=list)
    metadata: dict[str,Any] = Field(default_factory=dict)
    @model_validator(mode="after")
    def validate_run(self):
        if len(self.dataset_version_refs)!=len(set(self.dataset_version_refs)): raise ValueError("dataset_version_refs must be unique")
        epoch_ids=[x.epoch_id for x in self.epochs]; epoch_indexes=[x.epoch_index for x in self.epochs]
        checkpoint_ids=[x.checkpoint_id for x in self.checkpoints]; evaluation_ids=[x.evaluation_id for x in self.evaluations]
        if len(epoch_ids)!=len(set(epoch_ids)): raise ValueError("epoch ids must be unique")
        if len(epoch_indexes)!=len(set(epoch_indexes)): raise ValueError("epoch indexes must be unique")
        if len(checkpoint_ids)!=len(set(checkpoint_ids)): raise ValueError("checkpoint ids must be unique")
        if len(evaluation_ids)!=len(set(evaluation_ids)): raise ValueError("evaluation ids must be unique")
        cps=set(checkpoint_ids); epidx=set(epoch_indexes)
        for epoch in self.epochs:
            if epoch.training_run_ref!=self.training_run_id: raise ValueError("epoch training_run_ref must match training run")
            unknown=[r for r in epoch.checkpoint_refs if r not in cps]
            if unknown: raise ValueError(f"epoch references unknown checkpoints: {unknown}")
        for cp in self.checkpoints:
            if cp.training_run_ref!=self.training_run_id: raise ValueError("checkpoint training_run_ref must match training run")
            if cp.epoch_index is not None and cp.epoch_index not in epidx: raise ValueError("checkpoint epoch_index must resolve to an epoch in this run")
            if cp.parent_checkpoint_ref and cp.parent_checkpoint_ref not in cps: raise ValueError("checkpoint parent_checkpoint_ref must resolve within this run")
        for ev in self.evaluations:
            if ev.training_run_ref!=self.training_run_id: raise ValueError("evaluation training_run_ref must match training run")
            if ev.checkpoint_ref and ev.checkpoint_ref not in cps: raise ValueError("evaluation checkpoint_ref must resolve within this run")
        if self.resumed_from_checkpoint_ref and self.resumed_from_checkpoint_ref not in cps: raise ValueError("resumed_from_checkpoint_ref must resolve within this run")
        if self.parent_run_ref==self.training_run_id: raise ValueError("training run cannot be its own parent")
        return self
    def fingerprint(self)->str: return canonical_sha256(self)

class MLExperimentRecord(BaseModel):
    experiment_id: str = Field(min_length=2,max_length=300)
    title: str = Field(min_length=1,max_length=500)
    purpose: str | None = Field(default=None,max_length=4000)
    model_spec_ref: str = Field(min_length=2,max_length=500)
    training_plan_ref: str = Field(min_length=2,max_length=500)
    dataset_version_refs: list[str] = Field(min_length=1)
    run_refs: list[str] = Field(min_length=1)
    baseline_run_ref: str | None = Field(default=None,max_length=500)
    research_project_ref: str | None = Field(default=None,max_length=500)
    hypothesis_ref: str | None = Field(default=None,max_length=500)
    lab_experiment_ref: str | None = Field(default=None,max_length=500)
    workspace_job_group_ref: str | None = Field(default=None,max_length=500)
    created_at: str | None = Field(default=None,max_length=80)
    metadata: dict[str,Any] = Field(default_factory=dict)
    @model_validator(mode="after")
    def validate_experiment(self):
        if len(self.dataset_version_refs)!=len(set(self.dataset_version_refs)): raise ValueError("experiment dataset_version_refs must be unique")
        if len(self.run_refs)!=len(set(self.run_refs)): raise ValueError("experiment run_refs must be unique")
        if self.baseline_run_ref and self.baseline_run_ref not in self.run_refs: raise ValueError("baseline_run_ref must be present in run_refs")
        return self
    def fingerprint(self)->str: return canonical_sha256(self)

class MLTrainingLineageBundle(BaseModel):
    model_spec: MLModelSpecification
    training_plan: MLTrainingPlan
    experiment: MLExperimentRecord
    training_runs: list[MLTrainingRunRecord] = Field(min_length=1)
    @model_validator(mode="after")
    def validate_bundle(self):
        if self.training_plan.model_spec_ref!=self.model_spec.model_spec_id: raise ValueError("training plan must reference bundled model specification")
        if self.experiment.model_spec_ref!=self.model_spec.model_spec_id: raise ValueError("experiment model_spec_ref must match bundled model specification")
        if self.experiment.training_plan_ref!=self.training_plan.training_plan_id: raise ValueError("experiment training_plan_ref must match bundled training plan")
        if set(self.experiment.dataset_version_refs)!=set(self.training_plan.dataset_version_refs): raise ValueError("experiment datasets must match training plan datasets")
        run_ids=[r.training_run_id for r in self.training_runs]
        if len(run_ids)!=len(set(run_ids)): raise ValueError("training run ids must be unique")
        if set(run_ids)!=set(self.experiment.run_refs): raise ValueError("experiment run_refs must exactly match bundled training runs")
        runtime_ids={b.runtime_binding_id for b in self.model_spec.runtime_bindings}
        for run in self.training_runs:
            if run.experiment_ref!=self.experiment.experiment_id: raise ValueError("training run experiment_ref must match bundled experiment")
            if run.training_plan_ref!=self.training_plan.training_plan_id: raise ValueError("training run training_plan_ref must match bundled training plan")
            if run.model_spec_ref!=self.model_spec.model_spec_id: raise ValueError("training run model_spec_ref must match bundled model specification")
            if set(run.dataset_version_refs)!=set(self.training_plan.dataset_version_refs): raise ValueError("training run datasets must match training plan datasets")
            if run.runtime_binding_ref not in runtime_ids: raise ValueError("training run runtime binding must be declared by model specification")
            if self.training_plan.runtime_binding_ref!=run.runtime_binding_ref: raise ValueError("training run runtime binding must match training plan")
        parents={r.parent_run_ref for r in self.training_runs if r.parent_run_ref}
        unknown=parents-set(run_ids)
        if unknown: raise ValueError(f"parent_run_ref must resolve within lineage bundle: {sorted(unknown)}")
        return self
    def fingerprint(self)->str: return canonical_sha256(self)

def reference_training_lineage_bundle()->MLTrainingLineageBundle:
    base=reference_ml_model_bundle(); assert base.training_plan is not None
    spec=base.model_spec; plan=base.training_plan; run_id="ml-training-run:reference-energy:run-001"
    cp1=MLCheckpointRecord(checkpoint_id="ml-checkpoint:reference-energy:epoch-1",training_run_ref=run_id,checkpoint_kind=MLCheckpointKind.periodic,artifact_ref="artifact:reference-energy:checkpoint-epoch-1",artifact_sha256="1"*64,epoch_index=1,global_step=25,metric_snapshot={"loss":0.42,"mae":0.51},runtime_binding_ref=plan.runtime_binding_ref,environment_ref=plan.environment_ref,created_at="2026-09-27T00:10:00Z")
    cp2=MLCheckpointRecord(checkpoint_id="ml-checkpoint:reference-energy:final",training_run_ref=run_id,checkpoint_kind=MLCheckpointKind.final,artifact_ref="artifact:reference-energy:checkpoint-final",artifact_sha256="2"*64,epoch_index=2,global_step=50,metric_snapshot={"loss":0.31,"mae":0.44},model_version_ref="ai-model-version:reference-scientific-regressor:1.0.1",runtime_binding_ref=plan.runtime_binding_ref,environment_ref=plan.environment_ref,parent_checkpoint_ref=cp1.checkpoint_id,created_at="2026-09-27T00:20:00Z")
    epochs=[MLTrainingEpochRecord(epoch_id="ml-epoch:reference-energy:1",training_run_ref=run_id,epoch_index=1,global_step_end=25,scalar_metrics={"loss":0.42,"mae":0.51},checkpoint_refs=[cp1.checkpoint_id]),MLTrainingEpochRecord(epoch_id="ml-epoch:reference-energy:2",training_run_ref=run_id,epoch_index=2,global_step_end=50,scalar_metrics={"loss":0.31,"mae":0.44},checkpoint_refs=[cp2.checkpoint_id])]
    evals=[MLEvaluationRecord(evaluation_id="ml-evaluation:reference-energy:validation-final",training_run_ref=run_id,checkpoint_ref=cp2.checkpoint_id,dataset_version_ref="dataset-version:reference-energy:v1",split=MLEvaluationSplit.validation,metrics={"mae":0.44,"rmse":0.58},evaluator_runtime_ref=plan.runtime_binding_ref,created_at="2026-09-27T00:21:00Z")]
    run=MLTrainingRunRecord(training_run_id=run_id,experiment_ref="ml-experiment:reference-energy:v1",experiment_role=MLExperimentRole.baseline,training_plan_ref=plan.training_plan_id,model_spec_ref=spec.model_spec_id,dataset_version_refs=list(plan.dataset_version_refs),runtime_binding_ref=plan.runtime_binding_ref,environment_ref=plan.environment_ref,computational_job_ref="computational-job:reference-energy-training:001",code_reference=MLCodeReference(source_ref="repository:sustainable-catalyst/reference-ml-runtime",revision="reference-revision-001",content_sha256="3"*64),seed_state=MLSeedState(primary_seed=plan.random_seed,framework_seeds={"python":570,"numpy":570,"framework":570},deterministic_requested=True),resolved_parameters={"epochs":2,"batch_size":32,"learning_rate":0.001},status=MLTrainingRunStatus.completed,started_at="2026-09-27T00:00:00Z",ended_at="2026-09-27T00:22:00Z",output_model_version_ref="ai-model-version:reference-scientific-regressor:1.0.1",epochs=epochs,checkpoints=[cp1,cp2],evaluations=evals)
    exp=MLExperimentRecord(experiment_id="ml-experiment:reference-energy:v1",title="Reference energy neural-regression training experiment",purpose="Demonstrate governed run, epoch, checkpoint, evaluation, seed, code, dataset, runtime, and environment lineage.",model_spec_ref=spec.model_spec_id,training_plan_ref=plan.training_plan_id,dataset_version_refs=list(plan.dataset_version_refs),run_refs=[run.training_run_id],baseline_run_ref=run.training_run_id,research_project_ref="research-project:reference-energy",lab_experiment_ref="lab-experiment:reference-energy:001",workspace_job_group_ref="workspace-job-group:reference-energy:001",created_at="2026-09-27T00:00:00Z")
    return MLTrainingLineageBundle(model_spec=spec,training_plan=plan,experiment=exp,training_runs=[run])

def contract_document()->dict[str,Any]:
    ref=reference_training_lineage_bundle(); run=ref.training_runs[0]
    return {"ok":True,"release":CORE_RELEASE,"contract":CONTRACT_VERSION,"object_types":["MLSeedState","MLCodeReference","MLTrainingEpochRecord","MLCheckpointRecord","MLEvaluationRecord","MLTrainingRunRecord","MLExperimentRecord","MLTrainingLineageBundle"],"lineage_chain":["MLExperimentRecord","MLTrainingRunRecord","MLTrainingEpochRecord","MLCheckpointRecord","MLEvaluationRecord"],"integration":{"extends_machine_learning_neural_model_foundation_v3570":True,"embeds_v3570_model_specification":True,"embeds_v3570_training_plan":True,"links_dataset_versions":True,"links_code_revision_and_content_hash":True,"links_execution_environment":True,"links_runtime_binding":True,"links_computational_job":True,"captures_random_seed_state":True,"workspace_remains_default_compute_host":True,"lab_remains_experiment_host":True},"reproducibility":{"deterministic_bundle_fingerprint":True,"checkpoint_artifact_hashes_supported":True,"epoch_metric_snapshots_supported":True,"evaluation_metric_records_supported":True,"run_parentage_supported":True,"checkpoint_parentage_supported":True,"resume_lineage_supported":True},"boundaries":{"core_executes_training":False,"core_runs_inference":False,"core_writes_model_weights":False,"core_installs_ml_packages":False,"core_accepts_arbitrary_executable_payloads":False,"core_selects_best_checkpoint":False,"core_promotes_models_autonomously":False,"core_certifies_model_quality":False,"core_claims_evaluation_truth":False},"reference":{"experiment_id":ref.experiment.experiment_id,"training_run_id":run.training_run_id,"checkpoint_id":run.checkpoints[-1].checkpoint_id,"evaluation_id":run.evaluations[-1].evaluation_id,"bundle_fingerprint_sha256":ref.fingerprint()}}
