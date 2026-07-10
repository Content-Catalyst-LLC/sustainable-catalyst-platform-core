# Architecture

Platform Core v2.5.0 combines six infrastructure layers:

1. Universal Entity Registry
2. Governed Knowledge Graph
3. Evidence Ledger and provenance
4. Unified Public API and developer platform
5. Trust Center and evaluation framework
6. Signature Dossiers and end-to-end workflows

## Workflow engine

Workflow definitions are controlled records containing ordered stages. Each stage declares:

- Stable key
- Human-readable name
- Responsible product
- Action type
- Required or optional state
- Extensible metadata

Creating a workflow run copies the stage definition into durable workflow-step records. This prevents later edits to a definition from silently changing an active run.

Workflow transitions are append-only and content-hashed. Each transition records:

- Workflow and optional step
- Prior state
- New state
- Actor
- Reason
- Payload
- Timestamp
- Content hash

Required-step dependencies are enforced in the service layer. Completion creates a workflow content hash over the final run and ordered steps.

## Signature dossier model

A dossier has two phases.

### Draft phase

The dossier can receive:

- Frozen record snapshots
- Human approval, rejection, and change-request records
- Workflow linkage
- Subject linkage
- Visibility and purpose metadata

Each dossier record stores a complete JSON snapshot and its SHA-256 hash. The source record can later change without changing the dossier.

### Finalized phase

Finalization builds a canonical package containing:

- Dossier identity and purpose
- Linked workflow and transition history
- Ordered record snapshots
- Approval history
- Signature context

The canonical package is hashed. Platform Core signs the hash using HMAC-SHA256 and a server-side secret identified by a nonsecret key ID.

## Verification model

Verification checks:

1. The dossier is finalized or superseded.
2. The stored canonical package hashes to the recorded dossier hash.
3. The platform signature matches the dossier hash.
4. Every dossier record snapshot hashes to its recorded snapshot hash.
5. The final package contains the same frozen record snapshots stored in dossier records.

Verification intentionally does not compare the frozen snapshots with current live records. The purpose of a dossier is to preserve the state used at signing time.

## Approval model

Approvals are append-only. Finalization evaluates the latest approval decision for each signer. Any current `reject` or `request_changes` decision blocks finalization. Current `approve` decisions must meet the configured minimum.

## Public boundary

The public API exposes only:

- Public workflow definitions
- Workflow runs explicitly marked public
- Public dossiers in finalized or superseded state
- Dossier records marked public
- Verification results

Private record snapshots are removed from public dossier responses and public canonical snapshots.

## Signature limitations

HMAC signatures are server-verifiable integrity signatures. They do not provide independent public-key verification and are not qualified electronic signatures. A future release can add asymmetric signature adapters while preserving the canonical dossier hash contract.
