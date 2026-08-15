# Platform Core v2.14.0 Cross-Product Evidence Exchange Audit

The release is designed to prevent provenance loss when evidence moves between Site Intelligence, Workspace, Lab, Library, Decision Studio, and other Sustainable Catalyst products.

The exchange is reference-first. Every item points to a canonical Core subject and carries `truth_precedence=inherit-from-subject`. The exchange itself never becomes a new authority layer.

Public escalation is prohibited: a non-public canonical subject cannot be inserted into a public exchange package. Credential-like keys in snapshot or provenance structures are rejected before persistence. Source records are retained after package acceptance or derivation.

Automatic push delivery is intentionally deferred. v2.14.0 uses pull/receipt semantics so product integrations can adopt the contract without making a transient downstream outage a Core release blocker.
