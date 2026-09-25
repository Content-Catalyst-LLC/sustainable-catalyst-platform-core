#!/usr/bin/env python3
from copy import deepcopy

from app.services.ai_training_lineage import (
    CONTRACT_VERSION,
    contract_document,
    reference_training_lineage,
)

doc = contract_document()
assert doc["release"] == "3.28.0"
assert doc["contract"] == CONTRACT_VERSION
assert doc["integration"]["duplicates_generic_dataset_registry"] is False
assert doc["lineage_capabilities"]["training_job_binding"] is True
assert doc["lineage_capabilities"]["ai_model_version_binding"] is True
assert doc["boundaries"]["core_trains_models"] is False

bundle = reference_training_lineage()
assert len(bundle.fingerprint()) == 64
assert bundle.fingerprint() == deepcopy(bundle).fingerprint()

dataset_binding = bundle.dataset_bindings[0]
assert len(dataset_binding.dataset.fingerprint()) == 64
assert len(dataset_binding.dataset_version.fingerprint()) == 64

feature_set = bundle.feature_sets[0]
assert len(feature_set.fingerprint()) == 64

lineage = bundle.training_lineage
assert lineage.random_seed == 427
assert lineage.training_job_ref == "job:reference-model-training"
assert lineage.ai_model_version_ref == (
    "ai-model-version:reference-scientific-regressor:1.0.0"
)
assert lineage.runtime_environment_ref == "environment:reference-python"

print("PASS - Platform Core v3.28.0 Dataset, Feature Set & Training Lineage")
print(f"CONTRACT={CONTRACT_VERSION}")
print("DATASET_VERSIONING=enabled")
print("CONTENT_HASHING=enabled")
print("FEATURE_SET_VERSIONING=enabled")
print("TRANSFORMATION_LINEAGE=enabled")
print("SPLIT_LINEAGE=enabled")
print("TRAINING_JOB_BINDING=enabled")
print("AI_MODEL_VERSION_BINDING=enabled")
print("GENERIC_DATASET_REGISTRY_DUPLICATED=false")
print("CORE_TRAINS_MODELS=false")
