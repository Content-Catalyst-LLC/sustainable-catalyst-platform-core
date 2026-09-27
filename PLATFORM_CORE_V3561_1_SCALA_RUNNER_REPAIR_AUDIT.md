# Platform Core v3.56.1.1 — Scala Runner Repair Audit

## Failure observed
The v3.56.1 Contabo native profile certification passed Java 21 and Kotlin 2.4.20, then failed because the Scala 3.9.0 distribution exposed the Scala CLI runner, which interpreted `Main` as a subcommand/input rather than a main class.

## Repair
The validator now executes compiled Scala classes with `scala run -classpath <classes> --main-class Main`. The underlying JVM provider remains 1.0.0 and profile versions remain Java 21, Kotlin 2.4.20, and Scala 3.9.0.

## Deployment-path hardening
The v3.56.1 deployer fallback selected an archival repository under `/opt/sustainable-catalyst/backups/`. The v3.56.1.1 deployer rejects backup paths and uses a canonical checkout at `$HOME/sustainable-catalyst-platform-core` unless `SC_CORE_REPO` explicitly points to another non-backup checkout.
