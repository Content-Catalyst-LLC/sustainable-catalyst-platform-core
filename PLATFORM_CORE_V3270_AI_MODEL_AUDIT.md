# Platform Core v3.27.0 Audit

PASS criteria:
- AI model identity is distinct from model-version identity;
- model versions can be content addressed;
- providers are explicit;
- capabilities are explicit and deduplicated;
- model artifacts can carry SHA-256 hashes;
- model versions link training/evaluation datasets;
- model versions link runtime environments;
- model versions can link future training jobs;
- existing research/predictive model concepts are specialized, not duplicated;
- Core does not train or infer;
- no second generic model registry is created;
- no database migration is introduced.
