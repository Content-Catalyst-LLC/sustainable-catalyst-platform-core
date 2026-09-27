# Platform Core v3.56.2 — Apache Spark Adapter & Distributed Analytical Execution

Platform Core v3.56.2 adds Apache Spark as a separate governed execution target.

## Version target
- Apache Spark: 4.2.0
- Spark Scala binary line: 2.13
- Supported JVM line: Java 17/21
- Sustainable Catalyst deployment: OpenJDK 21
- Provider: `sc-runtime-spark` v1.0.0
- Adapter: `adapter:sc-runtime-spark`
- Local provider endpoint: `http://127.0.0.1:18106`

The general JVM Scala profile remains 3.9.0. Spark's Scala 2.13 binding is adapter-specific and does not downgrade that profile.

## Governed operations
`spark_runtime_info`, `distributed_sum`, `distributed_map_affine`, `dataframe_group_aggregate`, `dataframe_filter_project`, `partition_summary`.

## Security boundary
Provider v1.0.0 is local-only (`local[2]`). It does not accept arbitrary Python, Scala, Java, SQL, UDFs, Spark configuration, package installation, external data sources, shell commands, remote cluster targets, or public listeners.

## Responsibility split
Platform Core defines the contract, governance metadata, adapter registry bridge, provenance semantics, and runtime catalog entry. The Spark provider performs execution. Core does not become an arbitrary Spark code sandbox.
