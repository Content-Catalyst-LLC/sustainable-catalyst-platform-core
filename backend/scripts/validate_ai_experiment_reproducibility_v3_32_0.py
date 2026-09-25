#!/usr/bin/env python3
from copy import deepcopy

from app.services.ai_experiment_reproducibility import (
    CONTRACT_VERSION,
    ReproducibilityAssessmentKind,
    contract_document,
    reference_experiment_bundle,
)

doc = contract_document()
assert doc["release"] == "3.32.0"
assert doc["contract"] == CONTRACT_VERSION
assert doc["capabilities"]["controlled_experiment_definition"] is True
assert doc["capabilities"]["reproduction_attempts"] is True
assert doc["capabilities"]["reproducibility_assessment"] is True
assert doc["boundaries"]["core_executes_experiments"] is False
assert doc["boundaries"]["core_selects_winning_condition"] is False

bundle = reference_experiment_bundle()
assert len(bundle.fingerprint()) == 64
assert bundle.fingerprint() == deepcopy(bundle).fingerprint()

experiment = bundle.experiment
assert len(experiment.fingerprint()) == 64
assert any(item.baseline for item in experiment.conditions)
assert len(bundle.run_bindings) == 2

package = bundle.reproducibility_package
assert package.experiment_fingerprint_sha256 == experiment.fingerprint()
assert len(package.requirements) == 4
assert len(package.fingerprint()) == 64

attempt = bundle.reproduction_attempts[0]
assert len(attempt.observations) == 4
assert all(item.matched is True for item in attempt.observations)

assessment = bundle.assessments[0]
assert assessment.assessment == ReproducibilityAssessmentKind.exact
assert assessment.strict_requirements_total == 4
assert assessment.strict_requirements_matched == 4

print("PASS - Platform Core v3.32.0 AI Experiment & Reproducibility Packages")
print(f"CONTRACT={CONTRACT_VERSION}")
print("CONTROLLED_EXPERIMENT_DEFINITION=enabled")
print("BASELINE_CONDITION=required")
print("FACTOR_ASSIGNMENT_LINEAGE=enabled")
print("RUN_BINDING=enabled")
print("REPRODUCIBILITY_PACKAGE=enabled")
print("STRICT_REQUIREMENTS=enabled")
print("REPRODUCTION_ATTEMPTS=enabled")
print("REPRODUCIBILITY_ASSESSMENT=enabled")
print("CORE_SELECTS_WINNING_CONDITION=false")
print("CORE_EXECUTES_EXPERIMENTS=false")
