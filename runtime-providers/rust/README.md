# Sustainable Catalyst Rust Runtime v1.0.0

Runtime ID: `sc-runtime-rust`  
Adapter ID: `adapter:sc-runtime-rust`  
Core contract: `sc.core.rust-runtime.v1`  
Native runtime: rustc 1.75.0, Rust 2021 edition

The v1 provider exposes bounded safe-native algorithms for prefix sums, moving averages, connected components, topological sorting, Levenshtein distance, and FNV-1a 64 hashing.

Caller-supplied Rust source is not accepted. Provider-generated source begins with `#![forbid(unsafe_code)]`; API-driven Cargo dependency installation, shell execution, and caller filesystem paths are disabled.
