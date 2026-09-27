from app.services.ml_explainability_interpretation import CONTRACT_VERSION, CORE_RELEASE, contract_document, reference_explainability_interpretation_bundle

doc=contract_document(); bundle=reference_explainability_interpretation_bundle()
assert CORE_RELEASE=="3.61.0"
assert CONTRACT_VERSION=="sc.core.explainability-model-interpretation.v1"
assert doc["integration"]["extends_neural_evaluation_calibration_uncertainty_v3600"] is True
assert doc["governance"]["feature_attribution_is_not_causation"] is True
assert doc["governance"]["counterfactual_is_model_relative_not_real_world_causal_effect"] is True
assert doc["boundaries"]["core_computes_explanations"] is False
assert len(bundle.fingerprint())==64
print("PASS - Platform Core v3.61.0 Explainability & Model Interpretation Objects")
print(f"CONTRACT={CONTRACT_VERSION}")
print(f"EVALUATION={bundle.evaluation_bundle.evaluation.evaluation_id}")
print(f"FEATURE_ATTRIBUTION={bundle.feature_attributions[0].feature_attribution_id}")
print(f"COUNTERFACTUAL={bundle.counterfactual_explanations[0].counterfactual_id}")
print("CORE_COMPUTES_EXPLANATIONS=false")
print("EXPLANATION_IS_EVIDENCE=false")
