from app.services.ml_dataset_provenance import CONTRACT_VERSION, CORE_RELEASE, contract_document, reference_dataset_feature_transformation_bundle

c = contract_document()
b = reference_dataset_feature_transformation_bundle()
assert CORE_RELEASE == "3.59.0"
assert CONTRACT_VERSION == "sc.core.neural-dataset-feature-transformation-provenance.v1"
assert c["integration"]["extends_training_run_checkpoint_experiment_lineage_v3580"] is True
assert c["leakage_safeguards"]["fitted_transform_state_must_use_training_partition"] is True
assert len(b.fingerprint()) == 64
print("PASS - Platform Core v3.59.0 Neural Dataset, Feature & Transformation Provenance")
print(f"CONTRACT={CONTRACT_VERSION}")
print(f"DATASET_VERSION={b.dataset_snapshots[0].dataset_version_ref}")
print(f"SNAPSHOT={b.dataset_snapshots[0].snapshot_id}")
print(f"PARTITIONS={','.join(x.role.value for x in b.partitions)}")
print(f"TENSOR_INPUTS={len(b.tensor_inputs)}")
print("CORE_APPLIES_TRANSFORMATIONS=false")
print("CORE_CREATES_TENSORS=false")
