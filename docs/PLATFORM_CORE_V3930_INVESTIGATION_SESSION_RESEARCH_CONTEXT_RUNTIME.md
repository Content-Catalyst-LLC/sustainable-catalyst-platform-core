# Platform Core v3.93.0 — Investigation Session & Research Context Runtime

Contract: `sc.core.investigation-session-research-context-runtime.v1`

This release adds a persistent governed research-context runtime above v3.92.0. It records investigation questions, selected Core objects, filters, hypotheses, attributed contributions, immutable checkpoints, execution traces, and context snapshots while preserving upstream contract, epistemic, validation, provenance, contradiction, and federation states.

## Boundaries

- Session context is working context, not evidence.
- Persisting a hypothesis does not make it a graph fact.
- Persisting a conclusion does not make it a truth verdict.
- Context selection does not promote epistemic or validation state.
- Remote references remain subject to local validation.
- Checkpoints are immutable but supersedable by later context/evidence.
- No identity, relationship, or evidence graph mutation is performed.

Database migration: none.
