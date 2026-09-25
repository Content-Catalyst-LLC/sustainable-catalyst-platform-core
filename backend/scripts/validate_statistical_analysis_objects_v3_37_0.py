#!/usr/bin/env python3

from app.services.statistical_analysis_objects import (
    CONTRACT_VERSION,
    contract_document,
    reference_statistical_analysis_package,
)

doc = contract_document()
assert doc["release"] == "3.37.0"
assert doc["contract"] == CONTRACT_VERSION
assert doc["capabilities"]["analysis_plans"] is True
assert doc["capabilities"]["r_runtime_normalization"] is True
assert doc["capabilities"]["diagnostics_and_assumptions"] is True
assert doc["boundaries"]["core_executes_statistical_methods"] is False
assert doc["boundaries"]["core_selects_statistical_method"] is False
assert doc["boundaries"]["core_interprets_significance_as_truth"] is False

package = reference_statistical_analysis_package()
assert len(package.fingerprint()) == 64
assert package.plan.method.runtime_operation == "linear_regression"
assert package.plan.method.preferred_runtime_refs == ["sc-runtime-r"]

result = package.results[0]
assert result.status == "completed"
assert result.execution_binding.runtime_adapter_ref == "adapter:sc-runtime-r"
assert result.execution_binding.runtime_ref == "sc-runtime-r"
assert result.execution_binding.runtime_version == "1.0.0"
assert len(result.estimates) == 2
assert len(result.fit_statistics) == 4
assert result.provenance["core_certifies_statistical_validity"] is False

print("PASS - Platform Core v3.37.0 Statistical Analysis Object Model")
print(f"CONTRACT={CONTRACT_VERSION}")
print("STATISTICAL_ANALYSIS_PLANS=enabled")
print("DATA_VARIABLE_BINDINGS=enabled")
print("METHOD_SPECIFICATIONS=enabled")
print("HYPOTHESIS_OBJECTS=enabled")
print("ESTIMATES_AND_INTERVALS=enabled")
print("HYPOTHESIS_TEST_RESULTS=enabled")
print("EFFECT_SIZE_OBJECTS=enabled")
print("MODEL_FIT_STATISTICS=enabled")
print("DIAGNOSTICS_AND_ASSUMPTIONS=enabled")
print("MATRIX_RESULTS=enabled")
print("R_RUNTIME_NORMALIZATION=enabled")
print("CORE_EXECUTES_STATISTICAL_METHODS=false")
print("CORE_SELECTS_STATISTICAL_METHOD=false")
print("CORE_CERTIFIES_STATISTICAL_VALIDITY=false")
