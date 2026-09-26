# Platform Core v3.52.0 Audit

PASS criteria:
- canonical Rust runtime and adapter identity;
- rustc/cargo production package identities pinned;
- Rust 2021 edition declared;
- bounded safe-native operation allowlist;
- no caller-supplied Rust source;
- generated source forbids unsafe code;
- no shell execution;
- no Cargo dependency installation via API;
- no caller-controlled filesystem paths;
- provider-managed compilation and transient executable;
- reproducible environment package;
- dedicated runtime-security policy;
- adapter-registry integration;
- nine-runtime Unified Runtime Catalog;
- Workspace, Research Lab and Workbench profiles;
- provider deployment precedes Core promotion;
- mandatory native production kernel validation;
- Scientific Artifact Registry bridge;
- no numerical/scientific validity certification;
- no database migration.
