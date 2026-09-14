# Platform Core v2.47.0 — Media Artifact & Derivative Provenance

This release adds a governed, reference-first media provenance layer to Open Forensics. It records media artifacts, declared derivative relationships, metadata observations, cryptographic or externally produced perceptual fingerprints, frame/segment locators, descriptive comparison records, lineage graphs, and immutable snapshots.

## Execution and inference boundaries
Core does not decode media, compute perceptual fingerprints, execute media-similarity analysis, automatically detect derivative relationships, determine authenticity, infer manipulation intent, or attribute authorship. External analysis can be preserved as provenance-aware records without being promoted to Core truth.

## Contracts
- `sc.open-forensics.media-provenance.v1`
- `sc.open-forensics.media-lineage-graph.v1`
- `sc.open-forensics.media-comparison-bundle.v1`
