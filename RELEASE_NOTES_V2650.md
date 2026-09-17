# Platform Core v2.65.0 — Visual Query & Exploration Engine

Migration: `0069`

Adds a governed, renderer-neutral query/exploration layer above linked views. Core records exploration sessions, visual query targets, declarative query and predicate intent, path/subgraph traversal requests, external result/evidence bindings, saved exploration state, and immutable SHA-256 snapshots.

Core does not execute queries, traverse graphs, retrieve/filter/aggregate data, rank or recommend results, or infer visually.
