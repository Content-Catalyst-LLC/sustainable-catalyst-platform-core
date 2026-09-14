# Evidence Integrity & Chain of Custody — v2.43.0

## Governed records

- Custodians remain references; identity verification is external.
- Custody events are ordered per evidence item and each event hash commits to the previous event hash.
- Evidence seals preserve seal identifiers, timestamps, custodian references, and the evidence hash at sealing.
- Integrity checks compare expected and observed hashes without making authenticity claims.
- Continuity assessments identify record gaps or custodian discontinuities.
- Custody snapshots are immutable SHA-256 snapshots chained by prior snapshot hash.

## Boundaries

Core can record chain-of-custody data, verify its own tamper-evident event chain, compare hashes, and flag continuity issues. Core does not verify physical transfers, people, ownership, authenticity, admissibility, guilt, or other legal conclusions.
