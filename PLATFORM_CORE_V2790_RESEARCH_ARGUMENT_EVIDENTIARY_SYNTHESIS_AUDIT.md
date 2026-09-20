# Platform Core v2.79.0 Audit — Research Argument & Evidentiary Synthesis Engine

## Purpose

v2.79.0 converts the research intelligence and competing-hypothesis layers into an explicit, reproducible argument structure suitable for papers, investigations, systematic evidence reviews, graduate research, and other complex analytical work.

## Object model

The release introduces nine additive tables: arguments, argument nodes, argument edges, evidentiary syntheses, synthesis components, counterarguments, argument tensions, argument revisions, and argument snapshots.

## Architectural rule

Evidence, findings, interpretations, claims, hypotheses, arguments, and synthesis remain distinct objects. A synthesis is stored as researcher-authored text plus explicit source bindings rather than an automatically generated conclusion.

## Safety and epistemic boundary

The Core may preserve declared relationships and calculate descriptive counts. It does not determine truth, infer undeclared evidentiary relationships, score the strength of evidence, rank arguments, choose a preferred explanation, resolve conflicting evidence, or publish a conclusion.

## Migration

Migration `0083` is additive and requires the v2.78.0 / migration `0082` hypothesis layer as its predecessor.
