from copy import deepcopy

import pytest
from pydantic import ValidationError

from app.services.computational_runtime_objects import (
    DependencyKind,
    RuntimeDependency,
    RuntimeEnvironment,
)
from app.services.execution_environment_provenance import (
    CONTRACT_VERSION,
    DependencyEdge,
    DependencyNode,
    EnvironmentRequirement,
    ExecutionEnvironmentProvenance,
    LockfileRecord,
    ReproducibilityStatus,
    compare_environments,
    contract_document,
    julia_v030_reference_provenance,
    verify_requirement,
)


SHA_A = "a" * 64
SHA_B = "b" * 64


def make_record(version="1.0.0", package_version="2.0.0", package_hash=SHA_A):
    env = RuntimeEnvironment(
        environment_id="test-runtime:env-1",
        runtime_id="test-runtime",
        runtime_version=version,
        platform="linux",
        architecture="x86_64",
        os_name="ubuntu",
        os_version="24.04",
    )
    dep = DependencyNode(
        dependency_id="dep:numpy",
        direct=True,
        source_type="package-manager",
        dependency=RuntimeDependency(
            name="numpy",
            kind=DependencyKind.package,
            version=package_version,
            content_sha256=package_hash,
        ),
    )
    return ExecutionEnvironmentProvenance(
        provenance_id="envprov:test-runtime:env-1",
        environment=env,
        reproducibility_status=ReproducibilityStatus.locked,
        dependencies=[dep],
        lockfiles=[
            LockfileRecord(
                path="requirements.lock",
                kind="lock",
                content_sha256=SHA_A,
                package_manager="pip",
            )
        ],
        runtime_flags=["--threads=4"],
        hardware_profile={"cpu_arch": "x86_64"},
    )


def test_contract_and_julia_reference_are_v324():
    doc = contract_document()
    assert doc["release"] == "3.24.0"
    assert doc["contract"] == CONTRACT_VERSION
    assert doc["reference_runtime"]["provider_version"] == "0.3.0"
    assert doc["reference_runtime"]["adapter_status"] == "registered"

    julia = julia_v030_reference_provenance()
    assert julia.environment.runtime_id == "catalyst-julia-runtime"
    assert julia.environment.metadata["provider_version"] == "0.3.0"


def test_environment_fingerprint_is_stable_across_capture_time_and_id():
    a = make_record()
    b = make_record()
    b.provenance_id = "envprov:test-runtime:another-id"
    assert a.fingerprint() == b.fingerprint()
    assert len(a.fingerprint()) == 64


def test_dependency_graph_rejects_unknown_edge_nodes():
    record = make_record()
    with pytest.raises(ValidationError):
        ExecutionEnvironmentProvenance(
            provenance_id="envprov:test-runtime:bad-graph",
            environment=record.environment,
            dependencies=record.dependencies,
            dependency_edges=[
                DependencyEdge(
                    parent_dependency_id="dep:numpy",
                    child_dependency_id="dep:missing",
                )
            ],
        )


def test_compare_detects_dependency_version_and_hash_drift():
    left = make_record()
    right = make_record(package_version="2.1.0", package_hash=SHA_B)
    comparison = compare_environments(left, right)
    categories = {item.category for item in comparison.differences}
    assert comparison.exact_match is False
    assert "dependency-version" in categories
    assert "dependency-hash" in categories


def test_compare_identical_environment_is_exact_match():
    record = make_record()
    comparison = compare_environments(record, deepcopy(record))
    assert comparison.exact_match is True
    assert comparison.differences == []


def test_requirement_verification_passes_exact_requirements():
    record = make_record()
    requirement = EnvironmentRequirement(
        runtime_id="test-runtime",
        runtime_version="1.0.0",
        required_dependencies=[
            RuntimeDependency(
                name="numpy",
                kind=DependencyKind.package,
                version="2.0.0",
                content_sha256=SHA_A,
            )
        ],
        required_lockfile_hashes=[SHA_A],
        reproducibility_status=ReproducibilityStatus.locked,
        require_resolved_dependency_graph=True,
    )
    result = verify_requirement(record, requirement)
    assert result.ok is True
    assert result.mismatches == []


def test_requirement_verification_reports_runtime_and_dependency_drift():
    record = make_record()
    requirement = EnvironmentRequirement(
        runtime_version="9.9.9",
        required_dependencies=[
            RuntimeDependency(
                name="numpy",
                kind=DependencyKind.package,
                version="9.9.9",
            )
        ],
    )
    result = verify_requirement(record, requirement)
    fields = {item.field for item in result.mismatches}
    assert result.ok is False
    assert "runtime_version" in fields
    assert "dependency-version:numpy" in fields


def test_requirement_can_pin_exact_environment_fingerprint():
    record = make_record()
    requirement = EnvironmentRequirement(
        expected_environment_fingerprint_sha256=record.fingerprint()
    )
    assert verify_requirement(record, requirement).ok is True


def test_core_boundaries_remain_non_executing():
    boundaries = contract_document()["boundaries"]
    assert boundaries["core_installs_dependencies"] is False
    assert boundaries["core_mutates_runtime_environment"] is False
    assert boundaries["core_executes_package_manager"] is False
    assert boundaries["core_executes_runtime_directly"] is False


def test_lockfile_hash_validation_rejects_non_sha256():
    record = make_record()
    with pytest.raises(ValidationError):
        ExecutionEnvironmentProvenance(
            provenance_id="envprov:test-runtime:bad-lock",
            environment=record.environment,
            lockfiles=[LockfileRecord(path="x.lock", content_sha256="abc")],
        )
