# Integration Guide

## Trust Center consumers

Use anonymous routes for public web rendering:

```text
GET /trust/status.json
GET /trust/evaluations.json
```

Use the Unified Public API for authenticated integrations:

```text
GET /api/v1/trust/status
GET /api/v1/trust/evaluations
GET /api/v1/trust/incidents
GET /api/v1/trust/limitations
GET /api/v1/trust/attestations
```

Scope:

```text
trust:read
```

## Workbench

Workbench should run `calculator-validation` for release candidates and substantial calculator changes.

Recommended observations:

```json
{
  "total_cases": 250,
  "passed_cases": 248,
  "tolerance_failures": 0,
  "edge_cases_total": 40,
  "edge_cases_passed": 39
}
```

Attach calculation traces, validation reports, or release manifests through `evidence_references`.

## Research Librarian

The Research Librarian should run `ai-grounding` against a curated evaluation set.

Recommended observations:

```json
{
  "citation_coverage": 0.97,
  "unsupported_claim_rate": 0.015,
  "source_relevance": 0.94,
  "scope_gate_pass_rate": 0.995
}
```

Evaluation samples should be retained outside the aggregate observation when detailed prompt-response content is sensitive. Reference the retained evidence through stable IDs or storage references.

## Site Intelligence

Each connector can run `connector-freshness` with:

```json
{
  "last_success_at": "2026-07-10T12:00:00Z",
  "max_age_hours": 24,
  "connector_status": "active"
}
```

Use the connector entity as `target_entity_id`.

## Decision Studio

Decision Studio can include Trust Center status in exported decision packets and link claims to relevant evaluation runs.

Do not present an aggregate Trust Center score as proof that a decision is correct. Include the underlying domains, incidents, limitations, and evaluation dates.

## Accessibility workflow

Record both automated and manual checks:

```json
{
  "target": "WCAG 2.2 AA",
  "total_checks": 120,
  "passed_checks": 116,
  "critical_failures": 0,
  "manual_checks_pending": 4
}
```

Pending manual checks should remain visible as warnings.

## Custom review methods

Create an evaluation definition with:

```text
evaluator_kind = recorded
```

Then submit check results under `observations.checks`.

This is appropriate for editorial source review, legal authority review, design review, qualitative methodology review, or specialist scientific review.

## Incidents

Create an incident when a material trust condition is active and cannot be represented adequately as only an evaluation finding.

Examples:

- Source connector outage
- Evidence corruption
- Incorrect calculator output
- Public API data exposure
- AI scope-gate failure affecting published output
- Accessibility regression

Resolve the incident only after impact, root cause, and remediation have been recorded when known.

## Limitations

Use a known limitation for persistent boundaries rather than temporary operational incidents.

Examples:

- Experimental calculator without complete validation
- AI evaluation set limited to English
- Source freshness dependent on upstream publication cadence
- Accessibility review incomplete for embedded third-party content

## Attestations

Attestations should be narrow and evidence-backed.

Good:

> The v2.4.0 Platform Core regression suite completed with 36 passing tests on the recorded release environment.

Too broad:

> Platform Core is fully trustworthy.

## Webhooks

Subscribe to:

```text
trust.*
```

or specific events such as:

```text
trust.evaluation.completed
trust.incident.created
trust.incident.updated
trust.finding.created
trust.attestation.revoked
```

## WordPress

```text
[sc_trust_center]
[sc_trust_status]
```

The status shortcode uses the anonymous public JSON route and does not require a public developer key.
