# Platform Core v3.28.0 Audit

PASS criteria:
- dataset conceptual identity is distinct from dataset version identity;
- dataset versions support content and schema hashes;
- feature sets are versioned;
- feature definitions are explicit;
- transformation sequence is ordered and reproducible;
- dataset split lineage is explicit;
- random seed and hyperparameters are captured;
- training lineage binds computational job identity;
- training lineage binds runtime environment identity;
- training lineage binds exact AI model version;
- dataset storage/materialization is not duplicated in Core;
- Core does not execute training;
- no database migration is introduced.
