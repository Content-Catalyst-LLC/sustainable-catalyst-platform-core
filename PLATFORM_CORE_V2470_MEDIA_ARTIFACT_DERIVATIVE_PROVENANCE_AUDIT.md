# v2.47.0 Audit — Media Artifact & Derivative Provenance

- Additive migration: `0051`.
- New tables: 7.
- Cryptographic hashes may be format-validated; raw media decoding is outside Core.
- Perceptual fingerprints are recorded with producer/method provenance; Core does not compute them.
- Derivation edges are explicit asserted provenance; Core does not infer parentage.
- Comparison records are descriptive; authenticity, manipulation intent, authorship, guilt, responsibility, probability, ranking, and verdict determination remain outside Core.
- Immutable snapshots hash canonicalized media-provenance state.
