from copy import deepcopy
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import ValidationError
from app.routers import ml_training_lineage
from app.services.ml_training_lineage import CONTRACT_VERSION, CORE_RELEASE, MLTrainingLineageBundle, contract_document, reference_training_lineage_bundle

def test_contract_identity():
    d=contract_document(); assert CORE_RELEASE=="3.58.0"; assert CONTRACT_VERSION=="sc.core.training-run-checkpoint-experiment-lineage.v1"; assert d["release"]=="3.58.0"; assert d["integration"]["extends_machine_learning_neural_model_foundation_v3570"] is True

def test_lineage_chain_is_first_class(): assert contract_document()["lineage_chain"]==["MLExperimentRecord","MLTrainingRunRecord","MLTrainingEpochRecord","MLCheckpointRecord","MLEvaluationRecord"]

def test_core_does_not_execute_or_promote():
    b=contract_document()["boundaries"]
    for k in ("core_executes_training","core_runs_inference","core_writes_model_weights","core_installs_ml_packages","core_accepts_arbitrary_executable_payloads","core_selects_best_checkpoint","core_promotes_models_autonomously","core_certifies_model_quality","core_claims_evaluation_truth"): assert b[k] is False

def test_reference_bundle_is_valid_and_fingerprinted():
    b=reference_training_lineage_bundle(); assert len(b.fingerprint())==64; assert b.experiment.baseline_run_ref==b.training_runs[0].training_run_id; assert len(b.training_runs[0].epochs)==2; assert len(b.training_runs[0].checkpoints)==2; assert len(b.training_runs[0].evaluations)==1

def test_fingerprint_is_stable_for_same_payload():
    a=reference_training_lineage_bundle(); b=MLTrainingLineageBundle.model_validate(a.model_dump(mode="json")); assert a.fingerprint()==b.fingerprint()

def invalid(mutator):
    p=reference_training_lineage_bundle().model_dump(mode="json"); mutator(p)
    with pytest.raises(ValidationError): MLTrainingLineageBundle.model_validate(p)

def test_experiment_run_refs_must_match_bundle_runs(): invalid(lambda p:p["experiment"].__setitem__("run_refs",["ml-training-run:missing"]))
def test_baseline_must_resolve_to_experiment_run_refs(): invalid(lambda p:p["experiment"].__setitem__("baseline_run_ref","ml-training-run:missing"))
def test_training_run_must_match_experiment(): invalid(lambda p:p["training_runs"][0].__setitem__("experiment_ref","ml-experiment:wrong"))
def test_training_run_must_match_training_plan(): invalid(lambda p:p["training_runs"][0].__setitem__("training_plan_ref","ml-training-plan:wrong"))
def test_duplicate_epoch_index_rejected(): invalid(lambda p:p["training_runs"][0]["epochs"][1].__setitem__("epoch_index",1))
def test_checkpoint_must_reference_own_run(): invalid(lambda p:p["training_runs"][0]["checkpoints"][0].__setitem__("training_run_ref","ml-training-run:wrong"))
def test_evaluation_checkpoint_must_resolve(): invalid(lambda p:p["training_runs"][0]["evaluations"][0].__setitem__("checkpoint_ref","ml-checkpoint:missing"))
def test_runtime_binding_must_be_declared_by_model_spec(): invalid(lambda p:p["training_runs"][0].__setitem__("runtime_binding_ref","ml-runtime-binding:missing"))
def test_code_reference_cannot_embed_arbitrary_executable_payload_flag(): invalid(lambda p:p["training_runs"][0]["code_reference"].__setitem__("arbitrary_executable_payload_embedded",True))

def test_public_contract_route():
    app=FastAPI(); app.include_router(ml_training_lineage.public_router); r=TestClient(app).get("/public/v1/ml-training-lineage/contract"); assert r.status_code==200; assert r.json()["release"]=="3.58.0"

def test_private_reference_route():
    app=FastAPI(); app.include_router(ml_training_lineage.router); r=TestClient(app).get("/api/v1/ml-training-lineage/reference"); assert r.status_code==200; assert len(r.json()["bundle_fingerprint_sha256"])==64
