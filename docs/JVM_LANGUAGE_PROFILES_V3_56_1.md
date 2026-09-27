# Platform Core v3.56.1 — JVM Language Profiles

Adds explicit governed Java 21, Kotlin 2.4.20, and Scala 3.9.0 profiles over `sc-runtime-jvm`.

Profiles are execution bindings, not separate runtimes. Core never autonomously selects a language profile. Caller-supplied source, arbitrary classpaths, runtime dependency installation, and job network access remain disabled.

The profile catalog is available to Workspace, Research Lab, and Workbench through the existing JVM runtime. Spark remains a separate adapter planned for v3.56.2.
