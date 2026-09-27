from app.services.ml_evaluation_uncertainty import CONTRACT_VERSION, CORE_RELEASE, contract_document, reference_evaluation_calibration_uncertainty_bundle

doc=contract_document(); bundle=reference_evaluation_calibration_uncertainty_bundle()
assert CORE_RELEASE=="3.60.0"
assert CONTRACT_VERSION=="sc.core.neural-evaluation-calibration-uncertainty.v1"
assert doc["integration"]["extends_neural_dataset_feature_transformation_provenance_v3590"] is True
assert doc["governance"]["metric_is_analytical_result_not_evidence"] is True
assert doc["boundaries"]["core_computes_metrics"] is False
assert len(bundle.fingerprint())==64
print("PASS - Platform Core v3.60.0 Neural Evaluation, Calibration & Uncertainty Objects")
print(f"CONTRACT={CONTRACT_VERSION}")
print(f"EVALUATION={bundle.evaluation.evaluation_id}")
print(f"CHECKPOINT={bundle.checkpoint_ref}")
print(f"PARTITION={bundle.dataset_partition.partition_id}")
print(f"BUNDLE_SHA256={bundle.fingerprint()}")
print("CORE_COMPUTES_METRICS=false")
print("CORE_CERTIFIES_MODEL_QUALITY=false")
