# Sustainable Catalyst Platform Core v2.4.0

**Trust Center and Evaluation Framework**

Platform Core v2.4.0 adds a public accountability and evaluation layer to the Universal Entity Registry, Knowledge Graph, Evidence Ledger, provenance system, and Unified Public API.

The release provides:

- A public Trust Center at `/trust`
- Machine-readable trust status at `/trust/status.json`
- A controlled registry of evaluation definitions
- Immutable evaluation runs and check-level results
- Automated and recorded evaluation methods
- Automatic findings for failed checks
- Incident history and lifecycle records
- Known limitation disclosures
- Evidence-backed attestations
- Trust-related webhook events
- `trust:read` Unified Public API access
- Python and JavaScript SDK support
- WordPress Trust Center and trust-status shortcodes
- Migration `0005`

## Core principle

> Trust status must expose the method, observations, checks, findings, incidents, limitations, and evidence behind the result. A passing score is not a substitute for judgment, professional assurance, or independent verification.

## Public Trust Center

Open:

```text
https://YOUR-PLATFORM-CORE.onrender.com/trust
```

Machine-readable records:

```text
GET /trust/status.json
GET /trust/evaluations.json
```

The public page displays:

- Overall status and score
- Ledger integrity
- Latest evaluation by domain
- Check-level observations and expectations
- Open public findings
- Active public incidents
- Known public limitations
- Active public attestations
- Evaluation methodology and interpretation boundaries

## Unified Public API

The public developer API adds:

```text
GET /api/v1/trust/status
GET /api/v1/trust/evaluations
GET /api/v1/trust/incidents
GET /api/v1/trust/limitations
GET /api/v1/trust/attestations
```

Required scope:

```text
trust:read
```

Existing API plans are automatically updated to include the new scope without replacing custom quota settings.

## Evaluation registry

The release seeds eight evaluation definitions:

| Evaluation | Domain | Evaluator |
|---|---|---|
| Evidence Ledger Integrity | Evidence integrity | Automated |
| Unified Public API Readiness | Platform reliability | Automated |
| Evidence Review Coverage | Evidence quality | Automated |
| Connector Freshness | Source reliability | Context-driven |
| Calculator Validation | Calculation quality | Context-driven |
| AI Grounding and Scope | AI responsibility | Context-driven |
| Accessibility Conformance | Accessibility | Context-driven |
| Webhook Delivery Reliability | Platform reliability | Automated |

Custom definitions can use the `recorded` evaluator to preserve explicit reviewer-supplied checks.

## Evaluation records

Every run stores:

- Evaluation definition and version
- Target entity when applicable
- Triggering actor
- Start and completion times
- Status, score, grade, and summary
- Input observations
- Runtime environment
- Evidence references
- Immutable content hash
- Public disclosure state
- Check-level results

Every check stores:

- Stable check key
- Name
- Passed, warning, failed, error, or not-applicable state
- Score and severity
- Observed values
- Expected values
- Details and evidence references

Evaluation runs and check results are immutable through the ORM.

## Automated findings

Failed or errored checks create an open trust finding in the same transaction. The finding is:

- Linked to the run and check
- Recorded in the tamper-evident ledger
- Emitted as a webhook event
- Public only when the evaluation run is public

Findings support:

```text
open
accepted
resolved
dismissed
```

## Incidents

Incident records include:

- Severity
- Investigation state
- Public summary
- Impact
- Root cause
- Remediation
- Affected entity IDs
- Detection, start, and resolution times
- Public or internal visibility

Lifecycle states:

```text
investigating
identified
monitoring
resolved
```

A critical public incident sets public trust status to `critical`. A high-severity incident sets it to `degraded`.

## Known limitations

Limitations disclose boundaries that may affect interpretation or use:

- Domain
- Description
- Impact
- Mitigation
- Affected entities
- Review date
- Public visibility
- Active, mitigated, or retired state

Limitations remain visible without automatically being converted into a passing or failing score.

## Attestations

Attestations record a scoped statement by an issuer with:

- Subject entity
- Statement and scope
- Evidence references
- Validity window
- Content hash
- Public visibility
- Revocation history

Attestations are not certifications. They record what was asserted, by whom, for what scope, and with what evidence references.

## Status aggregation

The aggregate status uses:

- Latest public run for each active public definition
- Public run freshness
- Public findings
- Active public incidents
- Ledger-chain integrity

Possible values:

```text
operational
attention
degraded
critical
unknown
```

Missing or not-applicable evaluations remain visible as `unknown`. They are never silently treated as passing.

## Running evaluations

Run the default platform-native suite:

```bash
cd backend
.venv/bin/python scripts/run_trust_evaluations.py
```

The default suite runs evaluations that do not require external observations:

- Ledger integrity
- Public API readiness
- Evidence review coverage
- Webhook delivery reliability

Run selected or context-driven checks:

```bash
.venv/bin/python scripts/run_trust_evaluations.py \
  --context ../examples/trust_evaluation_contexts.json \
  --triggered-by release-validation
```

## Administrative routes

```text
GET   /v1/trust/status
GET   /v1/trust/definitions
POST  /v1/trust/definitions
PATCH /v1/trust/definitions/{definition_id}
POST  /v1/trust/definitions/{definition_id}/runs
POST  /v1/trust/run-suite
GET   /v1/trust/runs
GET   /v1/trust/runs/{run_id}

GET   /v1/trust/findings
POST  /v1/trust/findings
PATCH /v1/trust/findings/{finding_id}

GET   /v1/trust/incidents
POST  /v1/trust/incidents
PATCH /v1/trust/incidents/{incident_id}

GET   /v1/trust/limitations
POST  /v1/trust/limitations
PATCH /v1/trust/limitations/{limitation_id}

GET   /v1/trust/attestations
POST  /v1/trust/attestations
POST  /v1/trust/attestations/{attestation_id}/revoke
```

Administrative writes require `X-SC-API-Key`.

## Example: calculator evaluation

```json
{
  "triggered_by": "workbench-ci",
  "observations": {
    "total_cases": 100,
    "passed_cases": 100,
    "tolerance_failures": 0,
    "edge_cases_total": 20,
    "edge_cases_passed": 20
  },
  "environment": {
    "python": "3.12",
    "release": "2.4.0"
  },
  "evidence_references": [
    "sc:trace:validation-run"
  ]
}
```

Submit to:

```text
POST /v1/trust/definitions/calculator-validation/runs
```

## Example: AI grounding evaluation

```json
{
  "triggered_by": "research-librarian-evaluation",
  "observations": {
    "citation_coverage": 0.98,
    "unsupported_claim_rate": 0.01,
    "source_relevance": 0.95,
    "scope_gate_pass_rate": 0.99
  },
  "environment": {
    "provider": "gemini"
  },
  "evidence_references": []
}
```

The evaluator reports each measure separately. A high aggregate score does not conceal an unsupported-claim failure or scope-gate failure.

## Webhook events

Trust operations emit events such as:

```text
trust.evaluation.completed
trust.finding.created
trust.finding.updated
trust.incident.created
trust.incident.updated
trust.limitation.created
trust.limitation.updated
trust.attestation.issued
trust.attestation.revoked
trust.evaluation_definition.created
trust.evaluation_definition.updated
```

Subscriptions can use exact names, `trust.*`, or `*`.

## Local setup

```bash
cd backend
python3.12 -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -r requirements.txt

cp .env.example .env
.venv/bin/python scripts/migrate.py
.venv/bin/python scripts/seed_registry.py
.venv/bin/python -m uvicorn app.main:app --reload --port 8090
```

Open:

```text
http://127.0.0.1:8090/trust
http://127.0.0.1:8090/trust/status.json
http://127.0.0.1:8090/developers
http://127.0.0.1:8090/explorer
http://127.0.0.1:8090/evidence-explorer
http://127.0.0.1:8090/docs
```

## Production environment

```text
SC_CORE_TRUST_CENTER_ENABLED=true
SC_CORE_TRUST_PUBLIC_STATUS_ENABLED=true
SC_CORE_TRUST_STALE_AFTER_DAYS=90
```

Keep the existing Platform Core variables, including the database, internal write key, API log salt, and webhook signing secret.

## WordPress shortcodes

```text
[sc_trust_center]
[sc_trust_status]
```

The WordPress connector reads public Trust Center routes. It does not store internal write credentials.

## Boundaries

The Trust Center does not establish legal compliance, professional assurance, scientific consensus, financial accuracy, medical safety, engineering adequacy, accessibility certification, or freedom from defects.

Evaluation quality depends on:

- The method used
- The completeness of observations
- The quality of evidence references
- The freshness of the run
- The competence and independence of reviewers
- The correctness of evaluator implementation

The framework is designed to disclose those conditions rather than hide them.

## License

MIT
