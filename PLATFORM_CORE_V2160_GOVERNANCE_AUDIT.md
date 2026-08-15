# v2.16.0 Governance Audit

Release invariants: default private access is deny; public read fallback applies only to public visibility; explicit deny wins a same-priority policy tie; product-scoped roles do not escape their scope; secret-bearing context keys are redacted before audit persistence; audit chain tampering is detectable; audit retention cannot be configured for deletion and has a one-year minimum; governance decisions never change canonical evidence authority or provenance.
