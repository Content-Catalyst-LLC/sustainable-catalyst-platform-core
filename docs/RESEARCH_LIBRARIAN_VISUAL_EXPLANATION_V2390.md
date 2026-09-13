# Platform Core v2.39.0 — Research Librarian Visual Explanation

Platform Core v2.39.0 turns research explanations into governed, citation-aware visual objects that can move cleanly between Research Librarian, the Evidence Ledger, the visual reasoning layer, and external rendering or specialist-analysis runtimes.

## Core object model

A visual explanation contains semantic nodes such as questions, claims, evidence, sources, concepts, methods, results, uncertainties, counterclaims, and context. Explicit relations connect those nodes. Citation bindings point to existing Evidence Ledger records, source snapshots, Core entities, or declared external sources with a required locator. Saved views define renderer-neutral presentation intent. Immutable snapshots preserve reproducible explanation state.

## Visual contract

`sc.research-librarian-visual-explanation.v1` carries explanation metadata, nodes, relations, citations, citation-coverage status, a saved view, and renderer contract metadata. The contract preserves semantic meaning and provenance without hard-coding layout or styling.

## Research Librarian integration

Core can hand an explanation to `research-librarian` for evidence collection, retrieval, synthesis, or explanation authoring, and to Lab, Workbench, Site Intelligence, or an external runtime when specialist computation or spatial analysis is required. The returned work can be bound back into governed nodes, citations, evidence records, and snapshots.

## Execution boundary

Platform Core does **not** retrieve sources, generate natural-language explanations, select citations, rank sources, execute analytical models, perform layout, render graphics, or automatically promote inferred claims to truth. Those actions remain explicit responsibilities of Research Librarian or declared specialist runtimes. Core validates structure, preserves provenance, compiles contracts, and records reproducible explanation state.
