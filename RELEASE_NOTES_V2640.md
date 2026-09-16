# Platform Core v2.64.0 — Linked Views & Cross-Filtering

v2.64.0 turns the v2.61–v2.63 visual runtime into a coordinated analytical interaction substrate. It governs link policies, selection sets, declarative cross-filter predicates, brush ranges, focus/highlight state, external propagation evidence, and immutable linked-view snapshots.

Core stores renderer-neutral interaction semantics and provenance. It does not execute database queries, filter datasets, dispatch browser/UI events, compute selections, render highlights, handle brush gestures, or infer conclusions from visual appearance.

Migration: `0068`.
Contract: `sc.visual-runtime.linked-views.v1`.
