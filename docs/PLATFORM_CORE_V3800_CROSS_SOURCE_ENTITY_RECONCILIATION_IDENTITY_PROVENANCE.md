# v3.80.0 — Cross-Source Entity Reconciliation & Identity Provenance

## Purpose

Provide governed Core objects for reconciling source-specific identity observations without flattening source disagreement or turning agreement/model output into identity truth.

## Architectural rules

- Source-specific identity assertions remain first-class records.
- Source agreement is not identity fact.
- Source count is not identity evidence; source independence is modeled explicitly.
- Linkage probability remains contextual model output.
- Conflicts remain visible and may remain unresolved.
- Reconciliation decisions do not create canonical equivalence edges or merge entities.
- Any identity merge remains subject to the v3.77 governed resolution/mutation workflow.

## Cross-product boundary

Library and other products ingest/fetch sources. Core defines the reconciliation/provenance contracts. Workspace/Lab may compute linkage and reconciliation signals. Core does not scrape sources or execute identity matching models.
