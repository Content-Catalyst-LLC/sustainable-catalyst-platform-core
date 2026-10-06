# Platform Core v4.5.0 — Epistemic, Modal, Negation & Certainty Semantics

v4.5.0 adds a governed semantic layer for representing **what a source says, how strongly it says it, what is negated, what is merely possible or conditional, and whose stance is being represented**.

## Core objects

- `Proposition` — immutable source-bounded proposition spans; never a truth assertion by Core.
- `Attribution` — source/speaker surface attribution without assuming canonical actor identity.
- `EpistemicCue` — attribution, modal, negation, certainty, conditional, or other epistemic cues.
- `NegationScope` — explicit negated linguistic scope.
- `ModalScope` — possible/probable/necessary/etc. interpretation tied to a proposition.
- `ConditionalScope` — explicit condition and consequent binding without asserting the condition occurred.
- `EpistemicAssessment` — reviewed epistemic state, polarity, modality, certainty, attribution, and provenance.
- `EpistemicInterpretation` and `EpistemicSemanticSnapshot` — immutable, supersedable interpretation packages.

## Epistemic boundaries

Core does **not** treat source assertion as platform truth, source certainty as evidence validity, linguistic-confidence scores as claim probabilities, surface source labels as canonical identities, or accepted semantic analysis as graph mutation. Machine/model output remains advisory and governed review is required for accepted interpretations.

## Reference semantics

The reference fixture demonstrates:

- `did not reduce` → explicit negative scope;
- `may lower` and `could increase` → possibility modality;
- `is uncertain` → explicit source-level uncertainty;
- `If subsidies were extended` → unrealized conditional context;
- `The report`, `Researchers`, and `the ministry` → attributed source labels with zero automatic canonical actor bindings.

## Compatibility

v4.5.0 embeds and fingerprints the v4.4.0 Temporal & Spatial Language Grounding predecessor. It is an additive semantic layer and introduces no database migration.
