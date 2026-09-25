#!/usr/bin/env python3
from copy import deepcopy

from app.services.ai_error_robustness import (
    CONTRACT_VERSION,
    contract_document,
    reference_robustness_failure_bundle,
)

doc = contract_document()
assert doc["release"] == "3.33.0"
assert doc["contract"] == CONTRACT_VERSION
assert doc["capabilities"]["failure_taxonomy"] is True
assert doc["capabilities"]["slice_level_metrics"] is True
assert doc["capabilities"]["robustness_perturbations"] is True
assert doc["capabilities"]["failure_clustering"] is True
assert doc["boundaries"]["core_executes_robustness_tests"] is False
assert doc["boundaries"]["core_certifies_model_robustness"] is False

bundle = reference_robustness_failure_bundle()
assert len(bundle.fingerprint()) == 64
assert bundle.fingerprint() == deepcopy(bundle).fingerprint()

taxonomy = bundle.failure_taxonomy
assert taxonomy.version == "1.0.0"
assert len(taxonomy.failure_modes) == 3
assert len(taxonomy.fingerprint()) == 64

observation = bundle.error_observations[0]
assert observation.ai_model_version_ref == "ai-model-version:reference-classifier:1.0.0"
assert observation.evaluation_run_ref is not None
assert observation.inference_run_ref is not None

robustness_run = bundle.robustness_runs[0]
assert robustness_run.overall_passed is False
assert robustness_run.computational_job_refs
assert robustness_run.runtime_environment_refs

report = bundle.error_analysis_report
assert report.error_observation_refs
assert report.robustness_run_refs
assert report.provenance["core_certifies_robustness"] is False

print("PASS - Platform Core v3.33.0 AI Error Analysis, Robustness & Failure Taxonomy")
print(f"CONTRACT={CONTRACT_VERSION}")
print("FAILURE_TAXONOMY=enabled")
print("ERROR_OBSERVATIONS=enabled")
print("SLICE_LEVEL_METRICS=enabled")
print("ROBUSTNESS_PERTURBATIONS=enabled")
print("ROBUSTNESS_TOLERANCE_RULES=enabled")
print("FAILURE_CLUSTERING=enabled")
print("ERROR_ANALYSIS_REPORTS=enabled")
print("CORE_DIAGNOSES_CAUSALITY_AUTONOMOUSLY=false")
print("CORE_CERTIFIES_MODEL_ROBUSTNESS=false")
print("CORE_EXECUTES_ROBUSTNESS_TESTS=false")
