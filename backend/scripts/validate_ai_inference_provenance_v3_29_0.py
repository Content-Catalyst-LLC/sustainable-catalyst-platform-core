#!/usr/bin/env python3
from copy import deepcopy

from app.services.ai_inference_provenance import (
    CONTRACT_VERSION,
    compare_inference_runs,
    contract_document,
    reference_inference_run,
)

doc = contract_document()
assert doc["release"] == "3.29.0"
assert doc["contract"] == CONTRACT_VERSION
assert doc["integration"]["duplicates_runtime_artifact_model"] is False
assert doc["provenance_capabilities"]["exact_model_version_binding"] is True
assert doc["provenance_capabilities"]["source_input_to_artifact_lineage"] is True
assert doc["boundaries"]["core_executes_inference"] is False

bundle = reference_inference_run()
run = bundle.inference_run

assert len(run.fingerprint()) == 64
assert len(bundle.fingerprint()) == 64
assert run.ai_model_version_ref == (
    "ai-model-version:reference-scientific-regressor:1.0.0"
)
assert run.computational_job_ref == "job:reference-inference-001"
assert run.execution_result_ref == "result:reference-inference-001"
assert run.runtime_environment_ref == "environment:reference-python"
assert run.parameter_set.random_seed == 429

artifact = run.artifacts[0]
assert artifact.execution_result_ref == "result:reference-inference-001"
assert artifact.source_input_refs == [run.inputs[0].input_id]
assert len(artifact.fingerprint()) == 64

same = compare_inference_runs(run, deepcopy(run))
assert same.exact_match is True

changed = deepcopy(run)
changed.parameter_set.parameters["output"] = "structured"
comparison = compare_inference_runs(run, changed)
assert comparison.exact_match is False
assert any(item.field == "parameter_set" for item in comparison.differences)

print("PASS - Platform Core v3.29.0 Inference Run & AI Artifact Provenance")
print(f"CONTRACT={CONTRACT_VERSION}")
print("MODEL_VERSION_BINDING=enabled")
print("COMPUTATIONAL_JOB_BINDING=enabled")
print("EXECUTION_RESULT_BINDING=enabled")
print("RUNTIME_ENVIRONMENT_BINDING=enabled")
print("INPUT_FINGERPRINTING=enabled")
print("PARAMETER_SET_FINGERPRINTING=enabled")
print("ARTIFACT_CONTENT_HASHING=enabled")
print("INPUT_TO_ARTIFACT_LINEAGE=enabled")
print("RUNTIME_ARTIFACT_MODEL_DUPLICATED=false")
print("CORE_EXECUTES_INFERENCE=false")
