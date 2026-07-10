# Architecture

## Platform Core layers

### Universal Entity Registry

Stable identifiers, aliases, lifecycle state, visibility, canonical URLs, and metadata.

### Governed Knowledge Graph

Controlled predicates, type constraints, relationship reviews, traversal, paths, neighborhoods, recommendations, and JSON-LD.

### Evidence Ledger

Claims, source snapshots, calculation traces, provenance activities, evidence records, review assignments, manifests, and tamper-evident history.

### Unified Public API

Scoped, versioned external access to selected registry, graph, evidence, ledger, developer, webhook, and trust records.

### Trust Center and Evaluation Framework

The Trust Center introduces five record families:

1. Evaluation definitions
2. Immutable evaluation runs and checks
3. Findings
4. Incidents and limitations
5. Attestations

## Evaluation definitions

A definition specifies:

- Stable ID
- Name and domain
- Methodology
- Evaluator kind
- Target type
- Thresholds
- Cadence
- Failure severity
- Public visibility
- Active state
- Version

Definitions are mutable governance records. Every change is recorded in the Evidence Ledger.

## Evaluation runs

Runs are immutable observations of one definition at one time. The framework stores the complete result before committing it.

A run contains:

```text
definition
optional target entity
status
score
grade
summary
triggering actor
evaluator version
observations
environment
evidence references
content hash
visibility
timestamps
```

Check results are stored separately and linked to the run.

## Evaluator boundary

`services/evaluators.py` provides a stable evaluator interface:

```text
run_evaluator(kind, database_session, observations, settings)
```

Each evaluator returns check dictionaries with:

```text
check_key
name
status
score
severity
observed
expected
details
evidence_references
```

The orchestration service converts those dictionaries into immutable database records, compatibility validation events, ledger entries, findings, and webhooks.

## Automated evaluators

### Ledger integrity

Recalculates all payload hashes, entry hashes, and previous-entry links.

### Public API readiness

Inspects enabled state and required production configuration without exposing secret values.

### Evidence review coverage

Measures verified evidence records against all evidence records.

### Webhook delivery reliability

Measures delivered attempts against completed failed attempts.

## Context-driven evaluators

### Connector freshness

Requires latest successful retrieval time, freshness window, and connector state.

### Calculator validation

Requires test totals, passed tests, tolerance failures, and edge-case results.

### AI grounding

Requires citation coverage, unsupported-claim rate, source relevance, and scope-gate pass rate.

### Accessibility conformance

Requires checks passed, total checks, critical failures, pending manual checks, and declared target.

## Recorded evaluator

The `recorded` evaluator accepts explicit check results. It supports human reviews and specialist evaluations without forcing all methods into a single automated formula.

## Findings

Failed or errored checks create findings in the same transaction as the run. Findings are mutable remediation records, while the originating evaluation remains immutable.

## Aggregate status

The status builder uses the latest public run for every active public definition.

Domain state considers:

- Latest run status
- Average available score
- Evaluation freshness
- Open findings linked to those runs

Overall state considers:

- Ledger integrity
- Critical and high incidents
- Degraded domains
- Attention domains
- Open public findings

Known limitations are disclosed but do not automatically rewrite evaluation scores.

## Public and private boundaries

The anonymous Trust Center includes only records explicitly marked public.

The `trust:read` API uses the same public boundary.

Internal `/v1/trust` routes can access both public and private records under the existing read and write policies.

## Transaction model

Trust writes insert the domain record, ledger entry, and webhook event in one database transaction.

Evaluation runs additionally insert:

- Check results
- ValidationEvent compatibility records
- Automatic findings for failed checks

## Integrity model

Evaluation run content hashes bind the definition ID, target, status, score, summary, observations, environment, evidence references, timestamps, visibility, and check results.

Attestation hashes bind the statement, scope, issuer, subject, evidence references, validity, visibility, and metadata.

Hashing makes records tamper-evident when paired with the existing chained ledger. It does not replace database access control, backups, external archives, or independent verification.
