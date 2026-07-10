# Integration Guide

## Research Librarian

The Research Librarian can:

- Resolve claims and evidence to stable IDs
- Surface verified evidence records
- Link answers to source snapshots
- Explain recommendation paths through the graph
- Include manifest hashes in exported research routes

## Workbench

Workbench should create:

1. A provenance activity for the model run
2. A calculation trace with inputs, outputs, code version, and runtime
3. Evidence records that point to the trace
4. Provenance links between the activity, trace, claim, and source inputs

## Decision Studio

Decision Studio should:

- Register material claims
- Import source snapshots from Site Intelligence
- Attach source and calculation evidence
- Assign evidence reviews
- Export claim evidence manifests with decision packets

## Site Intelligence

Site Intelligence should:

- Register source entities
- Capture source snapshots
- Preserve retrieval times and content hashes
- Link connector activities to snapshots
- Notify the future Trust Center when freshness or integrity checks fail

## WordPress

Use server-rendered shortcodes for public summaries:

```text
[sc_evidence_ledger_status]
[sc_evidence_manifest claim_id="sc:claim:..."]
[sc_evidence_explorer]
```

Do not expose write keys, unpublished claims, private snapshots, or internal review notes through public page code.
