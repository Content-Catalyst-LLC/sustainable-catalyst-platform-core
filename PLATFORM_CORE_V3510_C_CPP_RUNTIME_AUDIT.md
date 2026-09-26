# Platform Core v3.51.0 C/C++ Runtime Audit

PASS criteria:
- canonical `sc-runtime-cpp` / `adapter:sc-runtime-cpp` identities;
- C11 and C++17 language profiles;
- GCC/G++ 13.3.0 production identity;
- Ubuntu 24.04 amd64 package pin `13.3.0-6ubuntu2~24.04.1`;
- six bounded native-engineering operations;
- structured finite numeric input validation;
- provider-generated source only;
- transient native binaries;
- generated source/result/compile/run artifacts retained;
- no arbitrary C/C++ source;
- no shell execution;
- no package installation via API;
- no caller-controlled filesystem paths;
- reproducible environment package;
- dedicated runtime-security policy;
- runtime-adapter registry integration;
- eight-runtime Unified Runtime catalog;
- Workspace, Research Lab and Workbench profiles;
- explicit Workbench C/C++ binding validation;
- Scientific Artifact Registry bridge;
- Core does not select algorithms or certify numerical/scientific validity;
- provider deployment precedes Core promotion;
- no database migration.
