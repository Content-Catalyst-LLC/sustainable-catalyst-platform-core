# Platform Core v3.96.0 — Federation Governance, Trust & Policy Runtime

Contract: `sc.core.federation-governance-trust-policy-runtime.v1`

This release adds a scoped, revocable governance plane above federated evidence exchange and signed runtime attestations. Trust is always capability-, contract-, and object-scope-specific. Remote content remains remote and requires local validation. Valid signatures establish integrity/signer association, not factual truth. Governance decisions never mutate identity, relationship, or evidence graphs.

## Governed objects

- FederationGovernancePolicy
- FederationGovernedNode
- FederationTrustScope
- FederationCapabilityPermission
- FederationRevocationSuspensionRecord
- FederationIntakeRule
- FederationPolicyDecision
- FederationConflictGovernanceRecord
- FederationGovernanceAuditEvent
- FederationGovernanceSnapshot

Database migration: none.
