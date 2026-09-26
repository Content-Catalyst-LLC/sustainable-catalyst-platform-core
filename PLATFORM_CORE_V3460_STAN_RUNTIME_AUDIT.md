# Platform Core v3.46.0 Audit

PASS criteria:
- Stan has a canonical runtime ID and adapter ID;
- provider and CmdStan versions are pinned;
- operations are bounded and explicit;
- model source is content-addressed;
- include directives are rejected;
- caller-supplied shell/process execution is unavailable;
- caller-supplied filesystem paths are unavailable;
- package installation through runtime API is unavailable;
- v1 chains are limited to one per invocation;
- environment package records toolchain/runtime requirements;
- Stan has a dedicated runtime-security policy;
- runtime-adapter registry includes Stan;
- unified runtime catalog includes Stan;
- Workspace and Research Lab profiles include Stan;
- Workbench remains unchanged;
- explicit Stan resolution does not become autonomous runtime selection;
- provider is deployed before Core promotion;
- native provider smoke test is required;
- Scientific Artifact Registry bridge validates;
- Core does not certify convergence or scientific validity;
- no database migration is introduced.
