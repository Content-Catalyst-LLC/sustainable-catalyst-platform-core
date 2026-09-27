from app.services.runtime_adapter_registry import spark_adapter_descriptor_v3562
from app.services.spark_runtime import contract_document, reference_bundle, runtime_catalog_entry
from app.services.unified_runtime_api import spark_runtime_catalog_entry_v3562

c = contract_document()
assert c["release"] == "3.56.2"
assert c["contract"] == "sc.core.spark-runtime.v1"
assert c["spark_version"] == "4.2.0"
assert c["scala_binary_version"] == "2.13"
assert "21" in c["jvm_supported_versions"]
assert c["capabilities"]["distributed_analytical_execution"] is True
assert c["capabilities"]["remote_cluster_target"] is False
assert c["boundaries"]["arbitrary_spark_sql"] is False
assert c["boundaries"]["caller_spark_conf"] is False
assert c["boundaries"]["remote_cluster_selection"] is False
assert c["boundaries"]["external_data_source_access"] is False
assert c["provider"]["port"] == 18106

a = spark_adapter_descriptor_v3562()
assert a["adapter_id"] == "adapter:sc-runtime-spark"
assert a["provider_id"] == "sc-runtime-spark"
assert a["native_runtime_version"] == "4.2.0"
assert spark_runtime_catalog_entry_v3562() == runtime_catalog_entry()
ref = reference_bundle()
assert ref["reference_request"]["operation"] == "distributed_sum"
assert ref["expected_result"]["sum"] == 15.0
print("PASS - Platform Core v3.56.2 Apache Spark Adapter & Distributed Analytical Execution")
print("CONTRACT=sc.core.spark-runtime.v1")
print("SPARK_VERSION=4.2.0")
print("SCALA_BINARY_VERSION=2.13")
print("JVM_COMPATIBLE=17,21")
print("PROVIDER=sc-runtime-spark@1.0.0")
print("PROVIDER_ENDPOINT=http://127.0.0.1:18106")
print("REMOTE_CLUSTER_SELECTION=false")
print("ARBITRARY_SPARK_SQL=false")
