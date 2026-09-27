from app.server import ADAPTER_ID, OPERATIONS, PROVIDER_VERSION, RUNTIME_ID, SCALA_BINARY_VERSION, SPARK_VERSION, _adapter, _master
assert RUNTIME_ID=="sc-runtime-spark"; assert ADAPTER_ID=="adapter:sc-runtime-spark"; assert PROVIDER_VERSION=="1.0.0"; assert SPARK_VERSION=="4.2.0"; assert SCALA_BINARY_VERSION=="2.13"; assert _master().startswith("local[")
a=_adapter(); assert a["boundaries"]["arbitrary_spark_sql"] is False; assert a["boundaries"]["caller_spark_conf"] is False; assert a["boundaries"]["remote_cluster_selection"] is False; assert a["boundaries"]["external_data_source_access"] is False; assert len(OPERATIONS)==6
print("PASS - Sustainable Catalyst Spark Runtime v1.0.0 contract validation")
print(f"RUNTIME_ID={RUNTIME_ID}"); print(f"ADAPTER_ID={ADAPTER_ID}"); print(f"SPARK_VERSION={SPARK_VERSION}"); print(f"SCALA_BINARY_VERSION={SCALA_BINARY_VERSION}"); print("OPERATIONS="+",".join(OPERATIONS))
