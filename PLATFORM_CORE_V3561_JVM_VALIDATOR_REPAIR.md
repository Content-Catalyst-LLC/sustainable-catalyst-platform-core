# Platform Core v3.56.1 — JVM provider/profile identity repair

v3.56.0 established `sc-runtime-jvm` provider version `1.0.0`. The v3.56.1 language-profile implementation introduced Java/Kotlin/Scala profiles but also attempted to bump the underlying provider to `1.1.0`, while inherited provider validation, deployment identity, and catalog contracts remained on `1.0.0`.

This repair keeps the provider identity stable at `1.0.0` across the provider service, Core JVM contract, runtime adapter registry, unified runtime catalog, profile validators, profile tests, native validator, and profile verification script. Java 21, Kotlin 2.4.20, and Scala 3.9.0 remain the v3.56.1 language profiles. The six v3.56.0 JVM operations remain the required compatibility floor; additive governed operations are permitted.

Server provider before repair: `1.0.0`. Core provider before repair: `1.1.0`. Catalog JVM reference before repair: `1.1.0`. Profile-file replacements: `6`.
