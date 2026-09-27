from app.services.ml_training_lineage import CONTRACT_VERSION, CORE_RELEASE, contract_document, reference_training_lineage_bundle

def main():
    d=contract_document(); b=reference_training_lineage_bundle()
    assert CORE_RELEASE=="3.58.0"; assert CONTRACT_VERSION=="sc.core.training-run-checkpoint-experiment-lineage.v1"; assert d["release"]==CORE_RELEASE
    assert d["integration"]["extends_machine_learning_neural_model_foundation_v3570"] is True
    assert d["reproducibility"]["deterministic_bundle_fingerprint"] is True
    assert d["boundaries"]["core_executes_training"] is False; assert d["boundaries"]["core_selects_best_checkpoint"] is False
    assert b.experiment.baseline_run_ref==b.training_runs[0].training_run_id; assert len(b.fingerprint())==64
    print("PASS - Platform Core v3.58.0 Training Run, Checkpoint & Experiment Lineage")
    print(f"CONTRACT={CONTRACT_VERSION}"); print(f"EXPERIMENT={b.experiment.experiment_id}"); print(f"TRAINING_RUN={b.training_runs[0].training_run_id}"); print(f"FINAL_CHECKPOINT={b.training_runs[0].checkpoints[-1].checkpoint_id}"); print(f"BUNDLE_FINGERPRINT={b.fingerprint()}"); print("CORE_EXECUTES_TRAINING=false"); print("CORE_SELECTS_BEST_CHECKPOINT=false")
if __name__=="__main__": main()
