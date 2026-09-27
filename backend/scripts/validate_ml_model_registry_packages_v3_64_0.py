from app.services.ml_model_registry_packages import (
    CONTRACT_VERSION,
    CORE_RELEASE,
    contract_document,
    reference_model_registry_package_bundle,
)

contract = contract_document()
bundle = reference_model_registry_package_bundle()
entry = bundle.registry_entries[0]
package = bundle.model_packages[0]
manifest = bundle.reproducibility_manifests[0]

assert CORE_RELEASE == "3.64.0"
assert CONTRACT_VERSION == "sc.core.neural-model-registry-reproducible-packages.v1"
assert contract["integration"]["extends_neural_inference_prediction_provenance_v3630"] is True
assert contract["registry_capabilities"]["immutable_artifact_hashes"] is True
assert contract["package_capabilities"]["deterministic_reproducibility_manifest"] is True
assert contract["governance"]["registration_does_not_certify_quality"] is True
assert contract["governance"]["portable_package_does_not_guarantee_reproducibility"] is True
assert contract["boundaries"]["core_executes_model_packages"] is False
assert contract["boundaries"]["core_installs_dependencies"] is False
assert contract["boundaries"]["core_certifies_model_quality"] is False
assert entry.registration_implies_certification is False
assert entry.approved_for_autonomous_action is False
assert manifest.reproducibility_guaranteed is False
assert package.core_executes_package is False
assert len(bundle.fingerprint()) == 64
assert len(package.fingerprint()) == 64
print("PASS - Platform Core v3.64.0 Neural Model Registry & Reproducible Model Packages")
print(f"CONTRACT={CONTRACT_VERSION}")
print(f"REGISTRY_ENTRY={entry.registry_entry_id}")
print(f"MODEL_PACKAGE={package.package_id}")
print(f"MANIFEST={manifest.manifest_id}")
print("REGISTRATION_CERTIFIES_QUALITY=false")
print("PACKAGE_GUARANTEES_REPRODUCIBILITY=false")
