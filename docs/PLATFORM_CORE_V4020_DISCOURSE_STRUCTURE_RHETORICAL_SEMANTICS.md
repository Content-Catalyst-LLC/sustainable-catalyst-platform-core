# Platform Core v4.2.0 — Discourse Structure & Rhetorical Semantics

Contract: `sc.core.discourse-structure-rhetorical-semantics.v1`

## Purpose

v4.2.0 extends the v4.1 Context Object & Semantic Frame Foundation with governed discourse structure and rhetorical semantics. It makes clause/sentence/paragraph-level relationships persistent, inspectable, provenance-bearing Core objects without treating rhetorical interpretation as factual truth.

The release defines:

- hierarchical `DiscourseSegment` objects bound to exact v4.1 context spans;
- lexical `DiscourseSignal` objects such as *after* and *nevertheless*;
- typed `RhetoricalRelation` objects for elaboration, contrast, cause, consequence, condition, concession, background, evidence, example, explanation, restatement, sequence, temporal sequence, purpose, attribution, question/answer, claim/support, rebuttal, comparison, and other relations;
- explicit rhetorical nuclearity;
- `ArgumentUnit` and `ArgumentRelation` objects for descriptive argument structure;
- provenance and review state for discourse interpretations;
- immutable, supersedable `DiscourseSnapshot` objects tied to an exact v4.1 contextual-semantics fingerprint.

## Epistemic boundaries

Core v4.2.0 stores and validates discourse interpretations. It does **not**:

- execute an autonomous discourse parser;
- silently infer or select the single correct rhetorical relation;
- resolve coreference or referential identity;
- treat a rhetorical `cause` relation as proof of real-world causality;
- treat a rhetorical `evidence` relation as an evidence-strength grade;
- treat an argument role as proof of truth, credibility, admissibility, or correctness;
- mutate identity, relationship, evidence, or context graphs.

Machine- or graph-assisted discourse analysis remains advisory and must preserve model/tool provenance.

## Reference case

The governed reference text remains:

> The commission rejected the proposal after the ministry revised its estimate. It nevertheless remained politically viable.

v4.2.0 represents:

- `after` as a temporal-sequence discourse signal connecting the revision clause to the rejection clause;
- `nevertheless` as a concessive/contrast signal connecting the first and second sentence;
- the revision clause as rhetorical background/context for the rejection assertion;
- `It` as the same unresolved v4.1 mention, with referent selection explicitly deferred to v4.3.0.

This demonstrates that discourse structure can become persistent semantic data without collapsing ambiguity.

## Roadmap handoff

v4.2.0 prepares governed discourse objects for:

- v4.3.0 — Coreference, Reference & Referential Identity Intelligence;
- v4.4.0 — Temporal & Spatial Language Grounding;
- v4.5.0 — Epistemic, Modal, Negation & Certainty Semantics;
- v4.6.0 — Pragmatic Meaning, Speech Act & Communicative Intent;
- v4.7.0 — Cross-Document Context Graph;
- v4.8.0 — Multilingual Context & Semantic Alignment;
- v4.9.0 — Contextual Semantic Evaluation & Benchmark Framework.

## Database

No database migration is introduced in v4.2.0.
