# Country Evidence Federation & Reconciliation — v2.12.0

Core v2.12.0 federates country evidence without flattening unlike records. Country statistics, humanitarian conditions and operational facility evidence remain source-aware and retain their original scope and semantics.

Reconciliation order is exact concept, semantic class, unit, geographic scope, source precedence, authority role, and reference-period freshness. Primary national official evidence is preferred for compatible country-specific statistics when present. Harmonized international benchmarks remain visible for comparison and fallback.

Core never automatically averages disagreeing sources. Different reference periods are not classified as contradictions. Subnational evidence cannot silently replace national evidence, and structural baselines cannot replace operational conditions. Knowledge-context and dataset-discovery records are excluded from factual truth precedence.

A persisted reconciliation audit records the candidate snapshot, selected source, decision state, discrepancy information and rationale without overwriting source records.
