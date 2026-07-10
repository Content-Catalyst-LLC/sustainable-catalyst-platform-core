# Integration Guide

## Product responsibilities

### Decision Studio

- Creates decision-oriented workflow runs
- Frames the problem and desired decision
- Registers material claims
- Creates the draft dossier
- Coordinates approvals and finalization

### Research Librarian

- Produces research routes
- Returns source and entity IDs
- Adds evidence-manifest references
- Completes research workflow stages

### Site Intelligence

- Captures source snapshots
- Supplies dataset and indicator IDs
- Records connector freshness and lineage
- Completes source-intelligence and dashboard stages

### Workbench

- Creates provenance activities
- Creates calculation traces
- Returns formula, code, runtime, input, and output references
- Completes analysis and validation stages

### Trust Center

- Runs evaluation definitions
- Records findings, incidents, limitations, and attestations
- Supplies evaluation-run and trust-status records to the dossier

### Platform Core

- Enforces stage ordering
- Records transitions
- Freezes dossier records
- Resolves approval state
- Produces the final hash and signature
- Serves public verification records

## Recommended record sections

```text
Decision Context
Research Route
Sources and Datasets
Knowledge Graph
Claims and Evidence
Calculations and Models
Provenance
Trust Evaluations
Findings and Limitations
Approvals
Publication Record
```

## Supported dossier record types

```text
entity
relationship
graph_neighborhood
claim
evidence
evidence_manifest
source_snapshot
calculation_trace
provenance_activity
evaluation_run
trust_finding
trust_incident
known_limitation
trust_attestation
trust_status
workflow_run
ledger_entry
```

## Workflow integration pattern

1. Create a workflow run.
2. Start the run.
3. Transition the current product stage to `in_progress`.
4. Perform the product operation.
5. Save output references using stable Platform Core IDs.
6. Transition the stage to `completed`.
7. Continue until the workflow is complete.
8. Create and assemble the dossier.
9. Add approval records.
10. Finalize and verify the dossier.

## Error handling

- HTTP 409 indicates unmet stage dependencies or approval blockers.
- HTTP 422 indicates an invalid state transition or unsupported record type.
- HTTP 503 indicates production signing configuration is missing.
- A failed dossier verification should be treated as an integrity incident.

## Public clients

Use scopes:

```text
workflow:read
dossier:read
```

Public clients can list finalized dossiers, inspect public workflow records, and verify signatures. They cannot create workflows, add records, approve, or finalize dossiers.
