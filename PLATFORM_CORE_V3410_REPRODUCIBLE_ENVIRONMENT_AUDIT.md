# Platform Core v3.41.0 Audit

PASS criteria:
- platform identity is fingerprinted;
- runtime requirements are explicit and versioned;
- system and language dependencies are first-class;
- lockfiles/manifests are content-addressed;
- secret values cannot be embedded in environment variables;
- build instruction order is deterministic;
- build instructions reference known requirements/assets only;
- package fingerprint excludes mutable lifecycle timestamp/state;
- reproduction requests bind exact package fingerprints;
- compatibility reports are explicitly preflight-only;
- passed verification cannot contain failed checks;
- workflow/job/environment lineage is preserved;
- environment package bridges into the scientific registry;
- Workspace/execution host remains environment build owner;
- Core does not install packages, build environments or resolve secrets;
- no database migration is introduced.
