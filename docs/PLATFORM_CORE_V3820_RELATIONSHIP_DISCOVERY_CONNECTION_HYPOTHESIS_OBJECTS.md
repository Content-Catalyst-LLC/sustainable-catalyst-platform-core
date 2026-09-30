# Platform Core v3.82.0 — Relationship Discovery & Connection Hypothesis Objects

## Purpose

v3.82.0 adds a governed relationship-discovery layer on top of the entity, reconciliation, and documentary-source foundation established in v3.77.0–v3.81.0. It distinguishes source-observed relationships from analytical discovery signals, connection candidates, explicit hypotheses, evidence positions, reviews, and later validated graph relationships.

## Contract

`sc.core.relationship-discovery-connection-hypothesis.v1`

Public contract endpoint:

`/public/v1/relationship-discovery/contract`

Private reference endpoint:

`/v1/relationship-discovery/reference`

## Governed object types

- `RelationshipDiscoveryPolicy`
- `RelationshipDiscoverySignal`
- `SourceObservedRelationship`
- `ConnectionCandidate`
- `ConnectionHypothesisEvidencePosition`
- `ConnectionHypothesisReview`
- `ConnectionHypothesis`
- `RelationshipPromotionGate`
- `RelationshipDiscoverySnapshot`
- `RelationshipDiscoveryHypothesisBundle`

## Evidence and graph boundaries

v3.82.0 explicitly enforces:

- co-occurrence is not a relationship;
- a shared attribute is not a relationship;
- graph proximity is not a relationship;
- embedding similarity is not a relationship;
- a model score is not evidence strength or relationship fact;
- source count does not establish a relationship;
- a source-observed relationship remains source-bound and is not automatically a canonical graph fact;
- a connection candidate is not evidence;
- a connection hypothesis is not a graph fact;
- a reviewer decision does not create a graph edge;
- v3.82.0 cannot create an evidence edge;
- separate v3.76-style evidence validation remains required before downstream graph mutation.

## Reference workflow

The synthetic reference bundle uses two source-resolved entities, two documentary/context signals, one source-observed relationship, one connection candidate, one explicit hypothesis, two independent evidence-position groups, two independent reviewers, and one promotion gate. The workflow terminates at `eligible-for-evidence-validation`; no relationship, evidence, or identity graph is mutated.

## Runtime responsibility

Platform Core defines and validates contracts only. External Workspace/Lab/runtime systems may compute discovery signals and scores, but those outputs return to Core as governed non-factual signals or candidates. Core does not silently promote them.

## Database migration

None.
