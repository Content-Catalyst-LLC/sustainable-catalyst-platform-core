# Platform Core v3.56.2 Spark Adapter Audit

- Spark is a new execution target, not a replacement for the JVM provider.
- General JVM profiles remain Java 21, Kotlin 2.4.20, Scala 3.9.0.
- Spark 4.2.0 uses adapter-specific Scala 2.13.
- Provider is loopback-only on port 18106 and initially uses `local[2]`.
- Remote masters, arbitrary code/SQL/UDFs, caller Spark config, package installation, shell execution, and external data-source access are disabled.
- Results are computational outputs with provenance, not automatic evidence objects.
