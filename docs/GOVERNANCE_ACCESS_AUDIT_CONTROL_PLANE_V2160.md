# Platform Core v2.16.0 — Governance, Access & Audit Control Plane

This release adds a central policy-decision and tamper-evident audit plane without changing evidence authority. Policies can match principal, product, resource type, action, and visibility ceiling. Explicit deny wins policy ties. Public reads remain available as a conservative fallback only for public visibility; private/restricted access defaults to deny.

The initial enforcement mode is configurable as `audit` or `enforce`; the release defaults to `audit` so deployment cannot accidentally lock out existing first-party integrations. Products can call the decision endpoint now, while route-by-route mandatory enforcement can be enabled deliberately.

Audit events form a SHA-256-linked chain. Secret-bearing context keys are redacted before persistence. Audit events are not publicly exposed, and the public API exposes readiness metadata only. Governance never changes evidence Truth precedence, source authority, reconciliation selection, or provenance.
