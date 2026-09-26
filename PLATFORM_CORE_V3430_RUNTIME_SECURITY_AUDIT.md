# Platform Core v3.43.0 Audit

PASS criteria:
- isolation profile identity is deterministic;
- policy identity is versioned and fingerprinted;
- runtime/adapter/operation allowlists are explicit;
- network/filesystem/package/secret/shell/code/egress governance is explicit;
- workspace/allowlist path semantics are deterministic;
- secret values never enter the policy/request model;
- matching active approval is required for approval-gated capabilities;
- allow decisions cannot contain violations;
- deny decisions require violations;
- passed isolation attestations require successful enforcement checks;
- governance records bind exact policy/request/decision fingerprints;
- approval and attestation refs must match the governed request/decision;
- security events have stable provenance fingerprints;
- v3.42 reproduction package refs can be attached;
- bundle bridges to the scientific registry;
- Workspace/execution host remains enforcement owner;
- Core does not launch sandboxes, apply kernel controls, resolve secrets or certify scientific validity;
- no database migration is introduced.
