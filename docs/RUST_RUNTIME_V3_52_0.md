# Platform Core v3.52.0 — Rust Runtime

v3.52.0 adds the Safe Native Systems runtime to the Sustainable Catalyst computational research fabric.

Core contract: `sc.core.rust-runtime.v1`  
Runtime ID: `sc-runtime-rust`  
Adapter ID: `adapter:sc-runtime-rust`  
Provider version: `1.0.0`  
Compiler: rustc 1.75.0  
Cargo: 1.75.0  
Rust edition: 2021

## v1 operations

- prefix sum
- moving average
- connected components
- topological sort
- ASCII Levenshtein distance
- FNV-1a 64 hashing over UTF-8 bytes

## Safety model

Caller-supplied Rust source is not accepted. Every provider-generated program begins with `#![forbid(unsafe_code)]`. Shell execution, Cargo dependency installation through the runtime API, and caller-controlled filesystem paths are disabled. Compilation and native execution occur only in provider-managed work directories.

## Product integration

Rust is added to the Unified Runtime API profiles for Workspace, Research Lab, and Workbench. Its role is safe native systems computation, graph processing, deterministic hashing, text algorithms, and bounded streaming/numeric transforms.

## Reproducibility

The reference environment pins Ubuntu 24.04 amd64 package versions for `rustc` and `cargo`, records the Rust 2021 edition, compiler/runtime identity, security policy, artifacts, and native execution evidence.

## Execution boundaries

Platform Core owns runtime identity, adapter registration, environment/security contracts, runtime discovery/binding, provenance, and exchange. The Rust provider owns bounded native compilation and execution. Calling products own algorithm and methodological selection. Core does not certify numerical or scientific validity.

No database migration.

Next mapped build: Platform Core v3.53.0 — Go Runtime.
