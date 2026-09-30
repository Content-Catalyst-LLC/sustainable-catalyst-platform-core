# Platform Core v3.81.0 — Public Record & Documentary Source Object Model

Contract: `sc.core.public-record-documentary-source-object-model.v1`

v3.81.0 gives Sustainable Catalyst a governed, provenance-preserving object model for public records and documentary sources without turning record acquisition or document authenticity into a truth verdict.

## Core object layers

1. **Source description** — what documentary/public-record item is being represented, its issuing context, record key, observed date, and source provenance.
2. **Acquisition** — how the exact bytes were obtained, when, by whom, from which source location, and with which content hash.
3. **Version and derivative lineage** — original source bytes remain distinct from scans, OCR, transcription, normalized, translated, excerpted, or redacted derivatives.
4. **Custody and integrity** — append-only acquisition, verification, storage, transfer, derivative, redaction, and review events.
5. **Redaction provenance** — redacted scope, stated reason/authority when known, and a strict prohibition on inferring hidden content.
6. **Citation anchors** — page, line, and time-range anchors identify the exact representation used by later research objects.
7. **Authenticity assessment** — source attestation, checksum verification, independent corroboration, or dispute can be represented without implying content truth or legal admissibility.
8. **Disclosure lineage** — public-record request/response scope, disclosed/withheld/redacted item counts, and provenance are preserved without treating absence as proof.
9. **Evidence interpretation** — documentary content becomes an evidence relation only through an explicit, provenance-bearing interpretation record tied to an existing Core evidence object.
10. **Immutable snapshots** — freeze documentary source/version/custody/authenticity/interpretation state for reproducibility without mutating evidence or identity graphs.

## Governing boundaries

- Document existence is not claim truth.
- Document authenticity is not content truth.
- Authenticity is not legal admissibility.
- OCR/transcription is a derived representation, not original source bytes.
- Redaction is not evidence of wrongdoing.
- Withheld or missing material is not proof of a claim.
- Core must not infer redacted or missing content.
- A document does not interpret itself as evidence; evidence use requires an explicit interpretation object.
- Core does not fetch/scrape records or perform OCR/transcription in this contract layer.
- Core does not mutate evidence or identity graphs during documentary ingest.

## Product responsibility

Platform Core defines the governed documentary/public-record contracts. Library can ingest, parse, OCR/HTR/transcribe, chunk, and retrieve source material. Workspace can run document-processing and comparison workloads. Research Lab can experiment with extraction and forensic methods. Downstream products consume Core's provenance-preserving documentary objects.

Database migration: none.
