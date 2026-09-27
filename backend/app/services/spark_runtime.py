from __future__ import annotations
from copy import deepcopy

RELEASE = "3.56.2"
CONTRACT = "sc.core.spark-runtime.v1"
RUNTIME_ID = "sc-runtime-spark"
ADAPTER_ID = "adapter:sc-runtime-spark"
PROVIDER_VERSION = "1.0.0"
SPARK_VERSION = "4.2.0"
SCALA_BINARY_VERSION = "2.13"
JVM_SUPPORTED = ("17", "21")
PROVIDER_ENDPOINT = "http://127.0.0.1:18106"
OPERATIONS = (
    "spark_runtime_info",
    "distributed_sum",
    "distributed_map_affine",
    "dataframe_group_aggregate",
    "dataframe_filter_project",
    "partition_summary",
)
BOUNDARIES = {
    "arbitrary_python_source": False,
    "arbitrary_scala_source": False,
    "arbitrary_java_source": False,
    "arbitrary_spark_sql": False,
    "caller_defined_udf": False,
    "caller_spark_conf": False,
    "runtime_dependency_install": False,
    "remote_cluster_selection": False,
    "external_data_source_access": False,
    "shell_execution": False,
    "public_network_listener": False,
}

def contract_document() -> dict:
    return {
        "ok": True,
        "release": RELEASE,
        "contract": CONTRACT,
        "runtime_id": RUNTIME_ID,
        "adapter_id": ADAPTER_ID,
        "provider_version": PROVIDER_VERSION,
        "spark_version": SPARK_VERSION,
        "scala_binary_version": SCALA_BINARY_VERSION,
        "jvm_supported_versions": list(JVM_SUPPORTED),
        "execution_mode": "provider-managed-local",
        "operations": list(OPERATIONS),
        "capabilities": {
            "distributed_analytical_execution": True,
            "spark_dataframe_execution": True,
            "spark_rdd_execution": True,
            "bounded_parallel_compute": True,
            "partition_aware_execution": True,
            "provenance_ready_results": True,
            "runtime_adapter_registration": True,
            "local_compute_target": True,
            "remote_cluster_target": False,
        },
        "limits": {
            "max_numeric_values": 10000,
            "max_rows": 5000,
            "max_columns": 64,
            "max_partitions": 8,
            "default_partitions": 2,
        },
        "boundaries": deepcopy(BOUNDARIES),
        "compatibility": {
            "jvm_runtime": "sc.core.jvm-runtime.v1",
            "jvm_provider_version": "1.0.0",
            "jvm_major_version": "21",
            "general_scala_profile": "3.9.0",
            "spark_scala_binary_version": SCALA_BINARY_VERSION,
            "spark_scala_binding_is_adapter_specific": True,
        },
        "provider": {
            "endpoint": PROVIDER_ENDPOINT,
            "service_name": "sc-spark-runtime",
            "host_binding": "127.0.0.1",
            "port": 18106,
        },
    }

def adapter_descriptor() -> dict:
    return {
        "adapter_id": ADAPTER_ID,
        "adapter_contract": "sc.core.runtime-adapter.v1",
        "provider_id": RUNTIME_ID,
        "provider_version": PROVIDER_VERSION,
        "provider_contracts": [CONTRACT, "sc.core.runtime-adapter.v1", "sc.core.runtime-security-governance.v1", "sc.core.reproducible-environment-package.v1"],
        "native_runtime": "Apache Spark",
        "native_runtime_version": SPARK_VERSION,
        "runtime_kind": "distributed-analytics-execution-target",
        "language": "spark-dataframe-rdd",
        "status": "registered",
        "execution_state": "active",
        "transport": "HTTP",
        "endpoint": PROVIDER_ENDPOINT,
        "capabilities": list(OPERATIONS),
        "lifecycle_methods": ["health", "version", "capabilities", "execute", "inspect", "collect_results", "diagnose"],
        "boundaries": deepcopy(BOUNDARIES),
        "metadata": {
            "spark_version": SPARK_VERSION,
            "scala_binary_version": SCALA_BINARY_VERSION,
            "jvm_supported_versions": list(JVM_SUPPORTED),
            "default_master": "local[2]",
            "remote_cluster_enabled": False,
            "core_defines_contract_provider_executes": True,
        },
    }

def reference_bundle() -> dict:
    return {
        "ok": True,
        "release": RELEASE,
        "contract": CONTRACT,
        "reference_request": {
            "spark_request_id": "spark-request:reference-distributed-sum:001",
            "operation": "distributed_sum",
            "inputs": {"values": [1.0, 2.0, 3.0, 4.0, 5.0], "partitions": 2},
            "computational_job_ref": "job:spark-reference-distributed-sum:001",
            "runtime_ref": RUNTIME_ID,
            "runtime_adapter_ref": ADAPTER_ID,
            "provenance": {
                "originating_product": "workspace",
                "execution_owner": "workspace-or-execution-host",
                "evidence_semantics": "computed-result-not-source-evidence",
            },
        },
        "expected_result": {"sum": 15.0, "count": 5},
        "metadata": {"reference_is_contract_proof": True, "live_provider_execution_occurs_outside_core": True},
    }

def runtime_catalog_entry() -> dict:
    return {
        "runtime_id": RUNTIME_ID,
        "adapter_id": ADAPTER_ID,
        "runtime_kind": "distributed-analytics-execution-target",
        "implementation": "Apache Spark",
        "runtime_version": SPARK_VERSION,
        "provider_version": PROVIDER_VERSION,
        "service_name": "sc-spark-runtime",
        "endpoint": PROVIDER_ENDPOINT,
        "operations": list(OPERATIONS),
        "status": "active",
        "metadata": {"scala_binary_version": SCALA_BINARY_VERSION, "jvm_major_version": "21", "execution_mode": "provider-managed-local"},
    }
