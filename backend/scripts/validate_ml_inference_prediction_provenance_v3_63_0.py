from app.services.ml_inference_prediction_provenance import (
    CONTRACT_VERSION,
    CORE_RELEASE,
    contract_document,
    reference_inference_prediction_provenance_bundle,
)

contract = contract_document()
bundle = reference_inference_prediction_provenance_bundle()
assert CORE_RELEASE == "3.63.0"
assert CONTRACT_VERSION == "sc.core.neural-inference-prediction-provenance.v1"
assert contract["integration"]["extends_neural_embedding_representation_intelligence_v3620"] is True
assert contract["integration"]["resolves_inference_plan_refs"] is True
assert contract["governance"]["prediction_is_analytical_output_not_evidence"] is True
assert contract["governance"]["evidence_promotion_requires_explicit_downstream_research_step"] is True
assert contract["boundaries"]["core_runs_inference"] is False
assert contract["boundaries"]["core_promotes_predictions_to_evidence"] is False
assert contract["boundaries"]["core_promotes_predictions_to_claims"] is False
assert bundle.predictions[0].evidence_promotion_allowed is False
assert bundle.predictions[0].claim_promotion_allowed is False
assert len(bundle.fingerprint()) == 64
print("PASS - Platform Core v3.63.0 Neural Inference & Prediction Provenance")
print(f"CONTRACT={CONTRACT_VERSION}")
print(f"INFERENCE_RUN={bundle.inference_runs[0].inference_run_id}")
print(f"PREDICTION={bundle.predictions[0].prediction_id}")
print(f"CHECKPOINT={bundle.inference_runs[0].checkpoint_ref}")
print("CORE_RUNS_INFERENCE=false")
print("PREDICTION_IS_EVIDENCE=false")
