from copy import deepcopy
import pytest
from pydantic import ValidationError
from app.services.machine_learning_models import (
    CONTRACT_VERSION, FeatureDataType, MLDataSplitSpec, MLFeatureSchema, MLFeatureSpec,
    MLModelFamily, MLModelSpecification, NeuralArchitectureKind, NeuralArchitectureSpec,
    NeuralLayerSpec, contract_document, reference_ml_model_bundle,
)

def test_contract_identity_and_boundaries():
    doc=contract_document(); assert doc["release"]=="3.57.0"; assert doc["contract"]==CONTRACT_VERSION
    assert doc["boundaries"]["core_trains_models"] is False; assert doc["boundaries"]["core_runs_inference"] is False
    assert doc["boundaries"]["core_installs_ml_packages"] is False; assert doc["boundaries"]["core_accepts_arbitrary_executable_model_code"] is False

def test_contract_extends_existing_ai_model_system():
    x=contract_document()["integration"]; assert x["extends_ai_model_object_system_v3270"] is True; assert x["reuses_ai_model_identity_and_version_refs"] is True; assert x["reuses_runtime_adapter_registry"] is True

def test_deep_learning_readiness_is_explicit():
    x=contract_document()["deep_learning_readiness"]; assert x["neural_architecture_objects"] is True; assert x["layer_graph_objects"] is True; assert x["framework_neutral_runtime_bindings"] is True

def test_reference_bundle_is_cross_linked():
    b=reference_ml_model_bundle(); assert b.training_plan is not None and b.inference_plan is not None
    assert b.training_plan.model_spec_ref==b.model_spec.model_spec_id; assert b.inference_plan.model_spec_ref==b.model_spec.model_spec_id; assert b.model_spec.ai_model_ref.startswith("ai-model:")

def test_reference_fingerprints_are_stable():
    b=reference_ml_model_bundle(); assert b.fingerprint()==deepcopy(b).fingerprint(); assert len(b.fingerprint())==64; assert len(b.model_spec.feature_schema.fingerprint())==64; assert len(b.model_spec.neural_architecture.fingerprint())==64

def test_duplicate_feature_names_rejected():
    with pytest.raises(ValidationError): MLFeatureSchema(schema_id="schema:test",features=[MLFeatureSpec(name="x",data_type=FeatureDataType.floating),MLFeatureSpec(name="x",data_type=FeatureDataType.floating)])

def test_target_must_be_target_role():
    with pytest.raises(ValidationError): MLFeatureSchema(schema_id="schema:test",features=[MLFeatureSpec(name="y",data_type=FeatureDataType.floating,role="input")],target_names=["y"])

def test_neural_layer_self_reference_rejected():
    with pytest.raises(ValidationError): NeuralLayerSpec(layer_id="x",layer_kind="dense",input_refs=["x"])

def test_unknown_layer_reference_rejected():
    with pytest.raises(ValidationError): NeuralArchitectureSpec(architecture_id="arch:test",architecture_kind=NeuralArchitectureKind.mlp,layers=[NeuralLayerSpec(layer_id="out",layer_kind="dense",input_refs=["missing"])])

def test_neural_family_requires_architecture():
    d=reference_ml_model_bundle().model_spec.model_dump(mode="python"); d["neural_architecture"]=None
    with pytest.raises(ValidationError): MLModelSpecification.model_validate(d)

def test_non_neural_family_can_omit_architecture():
    d=reference_ml_model_bundle().model_spec.model_dump(mode="python"); d["model_family"]=MLModelFamily.linear; d["algorithm_name"]="linear-regression"; d["neural_architecture"]=None
    assert MLModelSpecification.model_validate(d).neural_architecture is None

def test_split_fraction_overflow_rejected():
    with pytest.raises(ValidationError): MLDataSplitSpec(strategy="holdout",train_fraction=0.8,validation_fraction=0.3)

def test_kfold_requires_fold_count():
    with pytest.raises(ValidationError): MLDataSplitSpec(strategy="k-fold")

def test_bundle_rejects_unknown_training_runtime_binding():
    from app.services.machine_learning_models import MLModelBundle
    d=reference_ml_model_bundle().model_dump(mode="python"); d["training_plan"]["runtime_binding_ref"]="ml-runtime-binding:missing"
    with pytest.raises(ValidationError): MLModelBundle.model_validate(d)

def test_runtime_binding_forbids_arbitrary_code_and_package_install():
    from app.services.machine_learning_models import MLRuntimeBinding
    b=reference_ml_model_bundle().model_spec.runtime_bindings[0]; assert b.arbitrary_code_allowed is False and b.package_install_allowed is False
    d=b.model_dump(mode="python"); d["arbitrary_code_allowed"]=True
    with pytest.raises(ValidationError): MLRuntimeBinding.model_validate(d)
