from app.services.runtime_adapter_registry import spark_adapter_descriptor_v3562
from app.services.spark_runtime import adapter_descriptor, contract_document, reference_bundle, runtime_catalog_entry
from app.services.unified_runtime_api import spark_runtime_contract_v3562

def test_contract_identity():
    d = contract_document(); assert d["release"] == "3.56.2"; assert d["contract"] == "sc.core.spark-runtime.v1"; assert d["runtime_id"] == "sc-runtime-spark"; assert d["provider_version"] == "1.0.0"

def test_official_runtime_compatibility_target():
    d = contract_document(); assert d["spark_version"] == "4.2.0"; assert d["scala_binary_version"] == "2.13"; assert d["jvm_supported_versions"] == ["17", "21"]; assert d["compatibility"]["general_scala_profile"] == "3.9.0"; assert d["compatibility"]["spark_scala_binding_is_adapter_specific"] is True

def test_bounded_operations():
    d = contract_document(); assert len(d["operations"]) == 6; assert d["limits"]["max_rows"] == 5000; assert d["limits"]["max_partitions"] == 8

def test_security_boundaries():
    b = contract_document()["boundaries"]; assert all(v is False for v in b.values())

def test_adapter_descriptor():
    a = adapter_descriptor(); assert a["adapter_id"] == "adapter:sc-runtime-spark"; assert a["provider_id"] == "sc-runtime-spark"; assert a["endpoint"] == "http://127.0.0.1:18106"; assert a["metadata"]["default_master"] == "local[2]"

def test_registry_bridge():
    assert spark_adapter_descriptor_v3562()["adapter_id"] == "adapter:sc-runtime-spark"

def test_unified_runtime_bridge():
    assert spark_runtime_contract_v3562()["contract"] == "sc.core.spark-runtime.v1"

def test_catalog_entry():
    e = runtime_catalog_entry(); assert e["runtime_kind"] == "distributed-analytics-execution-target"; assert e["runtime_version"] == "4.2.0"

def test_reference_bundle():
    r = reference_bundle(); assert r["expected_result"] == {"sum": 15.0, "count": 5}; assert r["reference_request"]["provenance"]["evidence_semantics"] == "computed-result-not-source-evidence"
