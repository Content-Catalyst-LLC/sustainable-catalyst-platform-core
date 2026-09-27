# Platform Core v3.56.1.2 — Live JVM Profile Descriptor Repair

This hotfix adds the missing live `GET /v1/language-profiles` route to the JVM provider. The route exposes the already-governed Java 21, Kotlin 2.4.20, and Scala 3.9.0 profiles without changing the JVM provider identity (`1.0.0`) or enabling arbitrary source execution, autonomous profile selection, shell execution, or runtime package installation via API.
