from app.services.machine_learning_models import CONTRACT_VERSION, CORE_RELEASE, contract_document, reference_ml_model_bundle

def main():
    doc=contract_document(); bundle=reference_ml_model_bundle()
    assert CORE_RELEASE=="3.57.0"; assert CONTRACT_VERSION=="sc.core.machine-learning-neural-model-object.v1"
    assert doc["integration"]["extends_ai_model_object_system_v3270"] is True
    assert doc["integration"]["core_defines_workspace_computes_lab_experiments_products_consume"] is True
    assert doc["deep_learning_readiness"]["neural_architecture_objects"] is True
    assert doc["boundaries"]["core_trains_models"] is False; assert doc["boundaries"]["core_runs_inference"] is False
    assert doc["boundaries"]["core_installs_ml_packages"] is False; assert doc["boundaries"]["core_accepts_arbitrary_executable_model_code"] is False
    assert bundle.training_plan is not None and bundle.inference_plan is not None and len(bundle.fingerprint())==64
    print("PASS - Platform Core v3.57.0 Machine Learning & Neural Model Object Foundation")
    print(f"CONTRACT={CONTRACT_VERSION}"); print(f"MODEL_SPEC={bundle.model_spec.model_spec_id}"); print(f"NEURAL_ARCHITECTURE={bundle.model_spec.neural_architecture.architecture_kind.value}")
    print("CORE_TRAINS_MODELS=false"); print("CORE_RUNS_INFERENCE=false"); print("RUNTIME_EXECUTION=external")

if __name__=="__main__": main()
