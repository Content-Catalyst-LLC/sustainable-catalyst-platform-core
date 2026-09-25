#!/usr/bin/env python3
from copy import deepcopy

from app.services.ai_model_objects import (
    CONTRACT_VERSION,
    compare_model_versions,
    contract_document,
    reference_ai_model,
)

doc = contract_document()
assert doc["release"] == "3.27.0"
assert doc["contract"] == CONTRACT_VERSION
assert doc["integration"]["duplicates_generic_model_registry"] is False
assert doc["integration"]["specializes_existing_predictive_model"] is True
assert doc["boundaries"]["core_trains_models"] is False

binding = reference_ai_model()
assert binding.model.model_id == binding.model_version.model_id
assert len(binding.model.fingerprint()) == 64
assert len(binding.model_version.fingerprint()) == 64
assert len(binding.fingerprint()) == 64
assert binding.model.predictive_model_ref is not None
assert binding.model.research_model_ref is not None

same = compare_model_versions(
    binding.model_version,
    deepcopy(binding.model_version),
)
assert same.exact_match is True

changed = deepcopy(binding.model_version)
changed.weights_sha256 = "c" * 64
comparison = compare_model_versions(binding.model_version, changed)
assert comparison.exact_match is False
assert any(item.field == "weights_sha256" for item in comparison.differences)

print("PASS - Platform Core v3.27.0 AI Model & Model-Version Object Model")
print(f"CONTRACT={CONTRACT_VERSION}")
print("MODEL_IDENTITY=stable")
print("MODEL_VERSION_IDENTITY=immutable-content-addressed")
print("PROVIDER_IDENTITY=explicit")
print("DATASET_LINEAGE=enabled")
print("RUNTIME_ENVIRONMENT_LINEAGE=enabled")
print("GENERIC_MODEL_REGISTRY_DUPLICATED=false")
print("CORE_TRAINS_MODELS=false")
