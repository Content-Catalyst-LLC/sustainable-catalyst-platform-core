from pathlib import Path
import json
import sys

HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE))
import catalyst_julia_runtime as module


def test_defaults():
    cfg = module.JuliaRuntimeConfig()
    assert cfg.base_url == "http://127.0.0.1:18093"
    assert cfg.timeout_seconds == 10.0


def test_descriptor_is_native_core_adapter():
    data = json.loads((HERE / "runtime_descriptor.json").read_text())
    assert data["runtime_id"] == "catalyst-julia-runtime"
    assert data["service_version"] == "0.3.0"
    assert data["core_adapter_contract_version"] == "sc.core.runtime-adapter.v1"
    assert data["core_object_contract_version"] == "sc.core.computational-runtime-object.v1"
    assert data["adapter_id"] == "adapter:catalyst-julia-runtime"
    assert data["adapter_status"] == "registered"
    assert len(data["required_adapter_methods"]) == 10
    assert data["arbitrary_code_execution"] is False


def test_client_exposes_all_adapter_methods():
    required = [
        "health", "version", "capabilities", "prepare", "execute", "cancel",
        "inspect", "collect_results", "collect_artifacts", "diagnose"
    ]
    for name in required:
        assert hasattr(module.JuliaRuntimeClient, name)


def test_client_contract_versions():
    client = module.JuliaRuntimeClient
    assert client.service_version == "0.3.0"
    assert client.core_adapter_contract_version == "sc.core.runtime-adapter.v1"
    assert client.core_object_contract_version == "sc.core.computational-runtime-object.v1"
    assert client.environment_schema_version == "sc.environment.v1"


def test_legacy_environment_and_run_methods_remain():
    assert hasattr(module.JuliaRuntimeClient, "environment")
    assert hasattr(module.JuliaRuntimeClient, "environment_fingerprint")
    assert hasattr(module.JuliaRuntimeClient, "validate")
    assert hasattr(module.JuliaRuntimeClient, "run")
