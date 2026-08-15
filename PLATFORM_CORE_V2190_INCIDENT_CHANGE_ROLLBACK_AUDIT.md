# Platform Core v2.19.0 Incident / Change / Rollback Audit

- Incident visibility cannot be public.
- Incident metadata strips credential-like fields before persistence.
- Incident events are SHA-256 linked and independently verifiable.
- Invalid state transitions are rejected.
- High/critical risk changes require approval when the default policy is enabled.
- Rollback execution requires prior operator acknowledgement.
- Automatic rollback execution is disabled.
- SLO/deployment correlation never creates causal attribution.
- Public status is aggregate only.
- Evidence/provenance semantics are unchanged.
