# Platform Core v2.18.0 Observability Audit

- Automatic request metrics are fail-open.
- Query strings are not persisted by the HTTP metric recorder.
- Public status exposes aggregate service indicators only.
- Raw request IDs, raw metric samples, SLO definitions and operator deployment metadata remain non-public.
- SLO state has no evidence or Truth precedence.
- No paid monitoring provider is required.
