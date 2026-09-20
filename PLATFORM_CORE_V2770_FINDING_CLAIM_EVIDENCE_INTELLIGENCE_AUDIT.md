# Platform Core v2.77.0 Audit

- Migration: `0081`
- Contract: `sc.research.finding-claim-evidence.v1`
- Research layers remain distinct: evidence → finding → interpretation → claim.
- Findings and claims retain revision history rather than destructive overwrite.
- Evidence strength is researcher-declared metadata with an explicit assessment basis; Core calculates no truth score.
- Contradiction candidates are deterministic only for exact structured subject/predicate/object matches with opposing declared polarity.
- Semantic contradiction inference, truth determination, ranking, recommendation, and contradiction resolution remain outside Core.
