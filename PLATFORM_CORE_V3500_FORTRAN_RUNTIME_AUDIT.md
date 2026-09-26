# Platform Core v3.50.0 Audit

PASS criteria:
- canonical Fortran runtime and adapter identities;
- GNU Fortran 13.3.0 / Ubuntu 24.04 package provenance;
- bounded scientific/HPC operation allowlist;
- finite numeric validation and matrix/vector size bounds;
- generated Fortran 2008 source only;
- provider-managed bounded compiler invocation;
- transient compiled executable;
- no arbitrary Fortran source;
- no shell execution or runtime package installation;
- no caller-controlled filesystem paths;
- reproducible environment package;
- dedicated runtime-security policy;
- runtime-adapter registry integration;
- Unified Runtime catalog integration;
- Workspace, Research Lab and Workbench profiles;
- native dot-product smoke test required before Core promotion;
- Scientific Artifact Registry bridge;
- no numerical or scientific validity certification;
- no database migration.
