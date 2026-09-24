# Platform Core v3.23.0 Audit

PASS criteria:
- v3.22.0 is the required predecessor.
- `sc.core.runtime-adapter.v1` exists.
- All ten required adapter methods are enforced.
- Julia v0.2.0 is represented as the reference adapter.
- Capability lookup is deterministic.
- Requirement matching returns candidates rather than a selected winner.
- Contract-only adapters can be excluded.
- Existing analytical-provider metadata can be translated without mutating it.
- Core does not execute interpreters, install packages or select providers autonomously.
- No duplicate runtime persistence tables are introduced.
