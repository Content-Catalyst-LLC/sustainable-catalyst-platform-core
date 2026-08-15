# Sustainable Catalyst Platform Core v2.19.0

## Incident Response, Change Control & Rollback Coordination
- Adds migration `0022`.
- Adds governed operational incident records with append-only SHA-256-linked incident-event history.
- Adds risk-aware change control with approval gates for high and critical risk changes.
- Adds rollback assessment linked to incidents, deployment markers, and SLO evaluations.
- Rollback is operator-confirmed only; automatic rollback is disabled.
- Correlation never becomes causal attribution.
- Public status exposes aggregate counts only; incident details and operator metadata remain internal.
- Preserves evidence authority, provenance, country reconciliation, scientific routing, governance, certification, and observability semantics.
