# Platform Core v3.73.0 — Link Prediction & Candidate Relationship Objects

- Adds graph link-prediction candidate pairs, tasks, runtimes, model bindings, probabilities, evaluation lineage, candidate relationships, reviews, and promotion gates.
- Extends v3.70 graph ML, v3.71 graph embeddings, and v3.72 node/edge classification.
- Preserves supporting and contradicting evidence references on candidate relationships.
- Enforces that prediction probability, embedding similarity, classification output, and human review do not create graph facts or evidence edges.
- Candidate relationships can become eligible for a separate evidence-validation workflow, but v3.73 cannot perform evidence-edge promotion.
- No database migration.
