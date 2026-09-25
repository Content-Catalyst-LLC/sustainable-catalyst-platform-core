# Platform Core v3.30.0 Audit

PASS criteria:
- prompt conceptual identity is distinct from prompt-version identity;
- prompt versions preserve ordered message structure;
- prompt variables are explicitly declared;
- retrieval queries have stable identity;
- retrieval query scope is explicit;
- embedding/reranker model versions can be bound;
- retrieval results preserve rank and scoring;
- citations survive retrieval into context assembly;
- context ordering and token budgets are explicit;
- context items trace to retrieved items;
- inference runs can bind prompt/context bundles;
- Knowledge Library retains retrieval execution;
- Core does not duplicate documents/chunks/indexes;
- Core does not execute retrieval;
- no database migration is introduced.
