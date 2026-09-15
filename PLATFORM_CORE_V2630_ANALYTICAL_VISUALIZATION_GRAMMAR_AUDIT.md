# v2.63.0 Analytical Visualization Grammar Audit

- Migration: 0067
- Contract: `sc.visual-runtime.grammar.v1`
- Tables: specifications, data bindings, marks, encodings, scales, transforms, guides, snapshots.
- Integrity: specification scene/composition/view lineage; mark/data, encoding/mark/scale, transform/data, guide/scale relationships remain specification-local.
- Reproducibility: immutable SHA-256 hash-chained snapshots.
- Boundary: Core is declarative and renderer-neutral. Transform execution, aggregation, binning, scale calculation, layout, mark drawing, GPU execution, automatic chart generation, and visual inference remain external.
