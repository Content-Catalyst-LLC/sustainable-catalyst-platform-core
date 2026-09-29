# Platform Core v3.73.0 — Link Prediction & Candidate Relationship Objects

## Purpose
Formalize graph link-prediction outputs without allowing model output to mutate the evidence graph.

## Contract
`sc.core.graph-link-prediction-candidate-relationship.v1`

## Core objects
- LinkPredictionCandidatePair
- LinkPredictionTask
- LinkPredictionRuntimeContract
- LinkPredictionModelBinding
- RelationshipTypeProbability
- LinkPredictionRecord
- CandidateRelationship
- CandidateRelationshipReviewRecord
- CandidateRelationshipPromotionGate
- LinkPredictionEvaluationRecord
- GraphLinkPredictionBundle

## Evidence boundary
Predicted links and CandidateRelationship objects are derived model/review artifacts. Neither model score, embedding similarity, classification output, nor human review alone creates an evidence edge. A candidate may become eligible for a later evidence-validation workflow, but v3.73 cannot promote it.

## Runtime boundary
Platform Core validates and exchanges graph link-prediction contracts. Workspace/Research Lab or another governed compute runtime performs model execution. Core does not train or execute the link predictor.

## Roadmap
v3.74 adds Graph Anomaly Detection. v3.75 adds Knowledge Graph Representation Learning. v3.76 adds the Evidence Graph Neural Analysis & Validation Workflow that can consume candidates while preserving the rule `GNN prediction != graph fact`.
