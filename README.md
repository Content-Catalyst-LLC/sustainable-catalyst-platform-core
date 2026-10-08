# Sustainable Catalyst Platform Core

Sustainable Catalyst Platform Core is the governed semantic, provenance, research-object, evidence, visual-reasoning, analytical-contract, and cross-product exchange layer of the Sustainable Catalyst platform.

**Current release:** v4.20.3 — Connector Runtime Scheduling & Provider Compatibility Repair



## v4.20.3 — Connector Runtime Scheduling & Provider Compatibility Repair

- Adds the durable connector worker and automatic connector scheduler production services.
- Schedules only enabled, configured, zero-parameter connectors whose refresh windows are due.
- Preserves manual and parameterized connector boundaries rather than issuing invalid empty requests.
- Adds duplicate active-work suppression and provider freshness-aware scheduling.
- Migrates NASA APOD from the retired legacy API endpoint to the current NASA Science endpoint.
- Correctly treats HDX HAPI as registration-required until a valid generated application identifier is configured.
- Prevents the legacy Sustainable Catalyst HDX placeholder from being treated as valid registration.
- Preserves retry and dead-letter lineage for failed upstream execution attempts.
- Production-certified with Core API, connector worker, and connector scheduler operating concurrently.
- No database migration.

## v4.20.2 — Computational Provider Contract

- Adds a provider-neutral execution/handoff contract for Wolfram, Python, R, Julia, SymPy, Haskell, Workbench Native, and future engines.
- Governs computational provider profiles, explicit capabilities, assumptions, input bindings, execution environments, request/result envelopes, diagnostics, artifacts, and cross-engine comparisons.
- Binds external computational services to the v4.20.1 provider registry while preserving internal runtime references separately.
- Preserves the legacy `sc.core.analytical-runtime-provider.v1` lineage rather than duplicating or replacing it.
- Explicitly keeps execution outside Core and separates computational agreement/discrepancy from truth, evidence promotion, autonomous provider selection, and graph mutation.
- No database migration.

## v4.20.1 — External Provider Registry Contract

- Adds a provider-neutral governed registry for knowledge, data, computational, geospatial, event, and intelligence providers.
- Defines provider identity, capability, authority scope, endpoint, authentication, licensing/usage, quota/cache, lifecycle, provenance, and deterministic snapshot objects.
- Keeps provider registration separate from adapter implementation and live connectivity.
- Enforces provider authority != truth, provider agreement != truth, computational output != evidence, event signal != ground truth, and no automatic graph mutation.
- Preserves the v4.20 contextual reasoning consolidation boundary; this is a compatibility extension, not a reopened reasoning arc.
- No database migration.

## v4.20.0 — Unified Contextual Reasoning Runtime

Consolidates the v4.11–v4.19 contextual reasoning arc into one governed, auditable runtime. It preserves stage order, predecessor object identity, qualifications, unresolved state, original-language authority, translation lineage, source independence, counterevidence, competing explanations, and v4.19 research-answer dispositions across end-to-end reasoning traces. Runtime completion is not truth certification; no automatic evidence promotion, hypothesis selection, canonical identity merge, or graph mutation is authorized. This release is the planned major Core feature-expansion stopping point for the contextual-reasoning arc.

## v4.19.0 — Semantic Synthesis & Research Answer Object

Adds governed research-answer objects that synthesize claims, counterevidence, competing explanations, qualifications, unresolved questions, original-language/source-independence constraints, and reproducible provenance without truth promotion or automatic hypothesis selection.

## v4.18.0 — Contextual Hypothesis & Competing Explanation Objects

Adds governed contextual hypotheses, evidence positions, pairwise explanation comparisons, competing-explanation sets, provenance, and reproducible snapshots over v4.17 cross-source reconciliation. It preserves multiple live explanations for conflicting or incomplete source contexts, explicitly separates supporting, challenging, qualifying, unresolved, and non-independent evidence positions, carries forward causal-identification and identity uncertainty, and allows source-lineage constraints to reject an explanation without turning that rejection into a general truth verdict. Explanatory-fit scores are advisory metadata, not probabilities, evidence weights, or truth values; retained hypotheses are not automatically selected winners and no graph mutation occurs.

## v4.17.0 — Cross-Source Semantic Reconciliation Engine

Adds governed cross-source semantic anchors, correspondence candidates, explicit reconciliation conflicts, review decisions, semantic clusters, provenance, and reproducible snapshots. It reconciles claims, actor references, terminology, temporal scope, spatial/deictic references, multilingual variants, source-independence lineage, and framing context while preserving contradictions, scope/modality differences, unresolved identity, original-language authority, derived translations, and evidence/causal boundaries. Reconciliation is advisory alignment rather than canonicalization: scores do not establish truth, identity, equivalence, or graph facts, and no automatic graph mutation occurs.

## v4.16.0 — Narrative, Framing & Perspective Intelligence

Adds governed source perspectives, framing signals, narrative frames, cross-perspective comparisons, reviewed framing assessments, provenance, and reproducible snapshots. It can describe how sources foreground outcomes, benefits, uncertainty, scope, responsibility, accountability, urgency, and mechanisms while explicitly separating framing from truth, credibility, ideological classification, motive inference, manipulation, deception, causal proof, or evidence validity. Original-language authority and translation derivation remain explicit, and no graph mutation occurs.

## v4.15.0 — Contextual Causal Language & Mechanism Intelligence

Adds governed causal-language signals, proposed mechanisms, intervention contexts, counterfactual questions, causal assessments, provenance, and reproducible snapshots. It separates causal wording from causal identification; temporal sequence and association from causality; mechanism plausibility from validation; intervention language from experimental evidence; and counterfactual questions from estimated causal effects. Evidence-context conflicts, modality, attribution, scope, and translation lineage remain intact, with no causal/evidence/knowledge/identity graph mutation.

## v4.14.0 — Evidence-Context Integration Layer

Connects contextual claim interpretation to governed Evidence Graph-style anchors through a read-only, provenance-preserving bridge. Evidence review status remains upstream authority; translation derivatives cannot count as independent corroboration; contradiction remains unresolved without governed adjudication; no graph or truth promotion occurs.

## v4.13.0 — Claim Alignment, Agreement & Contradiction Intelligence

- Adds governed claim units, source contexts, comparison queries, multidimensional alignment signals, comparison pairs, relation assessments, provenance, and reproducible snapshots.
- Distinguishes agreement, qualified agreement, partial agreement, strict contradiction, apparent contradiction, scope mismatch, distinct claims, and unresolved comparisons.
- Requires polarity, modality, temporal/spatial scope, attribution, multilingual lineage, qualification, and unresolved identity to remain visible during comparison.
- Explicitly separates contradiction detection from truth adjudication, deception detection, evidence validity, source majority, and graph mutation.
- Adds private/public `/claim-comparison` API surfaces and no database migration.

## v4.12.0 — Context Retrieval & Relevance Intelligence

Platform Core v4.12.0 adds governed retrieval over v4.11 contextual memory. It separates candidate generation from explainable ranking, preserves scope, provenance, qualifications, unresolved state, multilingual lineage, and current-revision identity, and exposes reproducible retrieval snapshots. Relevance is contextual and advisory: rank is not truth, evidence weight, authority, credibility, or canonical identity.


## Architecture

Platform Core defines governed research meaning and interoperable contracts while specialist products and runtimes perform domain-specific execution.

- **Research and evidence objects** — projects, sources, claims, findings, hypotheses, arguments, investigations, protocols, reviews, and reproducibility objects.
- **Provenance and lineage** — immutable snapshots, evidence lineage, analytical lineage, execution references, custody/integrity records, and cross-product traceability.
- **Visual reasoning** — renderer-neutral scenes, views, analytical visualization grammar, linked views, visual query, predictive/forensic visual objects, and scene contracts.
- **Predictive and causal contracts** — governed forecast, uncertainty, ensemble, calibration, causal, and decision-intelligence objects while specialist runtimes retain execution.
- **Scientific and computational runtime contracts** — registered runtime providers, environments, jobs, results, artifacts, and reproducibility semantics across Python, R, Julia, JVM, Rust, Go, C/C++, Fortran, Haskell, Prolog, and related providers.
- **Multilingual and linguistic knowledge contracts** — original-language identity, translation/transliteration/alignment provenance, language/script/variant metadata, and cross-lingual semantic exchange.
- **Contextual semantic and discourse contracts** — persistent context objects, semantic mentions, frame/participant structures, hierarchical discourse segments, rhetorical signals/relations, descriptive argument structure, first-class reference expressions, ranked referent candidates, reviewed coreference chains, referential identity handoffs, temporal/spatial expressions, relative-time derivations, spatial-deictic antecedents, reviewed language groundings, first-class propositions, source attribution, epistemic stance, modal and negation scope, conditional scope, certainty semantics, pragmatic participants, genre/register context, speech acts, communicative intents, interpretation provenance, ambiguity preservation, non-authoritative semantic snapshots, and a persistent cross-document context graph that links governed semantic objects across sources while preserving uncertainty, unresolved identity, and source-specific provenance; v4.8 adds multilingual context representations, directional context alignment, first-class semantic divergence, culturally/historically conditioned meaning, and non-mutating cross-language context projections; v4.9 adds governed contextual-semantic benchmark cases, reviewed gold targets, reproducible evaluation runs, explicit error taxonomy, ambiguity-sensitive scoring, multilingual drift evaluation, and benchmark metrics that remain separate from truth, evidence validity, safety, and domain authority.; v4.10 converges the v4.1-v4.9 stack into a nine-stage governed semantic/context runtime with immutable artifact handoffs, stage qualifications, original-language lineage, reproducible sessions/snapshots, and validation gates that prevent interpretation from silently becoming truth, identity, evidence, or authority.; v4.11 adds stable scoped contextual memory, immutable revision lineage, qualification carry-forward, research-project checkpoints, and supersedable semantic-state snapshots so governed context can persist without gaining truth or authority merely through repetition or storage.
- **Graph and neural knowledge contracts** — graph representations, node/edge classification, link prediction, anomaly detection, representation learning, and evidence-graph neural analysis.
- **Cross-product exchange** — reference-first handoff and interoperability contracts for Workspace, Lab, Library, Workbench, Decision Studio, Site Intelligence, and other Sustainable Catalyst products.

Core governs contracts, identity, provenance, and exchange. It does not silently replace specialist computation, rendering, retrieval, scientific judgment, or domain-authoritative systems.

## Repository layout

- `backend/` — FastAPI backend, persistence, migrations, APIs, object services, graph services, and Core runtime logic.
- `deployment/` — production deployment and environment configuration.
- `docs/` — current architecture, contracts, and operational documentation.
- `examples/` — example Core payloads and integration patterns.
- `runtime-providers/` — runtime-provider descriptors and integrations.
- `schemas/` — governed object, exchange, runtime, visual, evidence, and research schemas.
- `scripts/` — active build, validation, migration, release, and operational tooling.
- `wordpress-plugin/` — Sustainable Catalyst Platform Core WordPress connector.
- `.github/` — repository automation.

## Release history

Historical release notes, validation reports, audit records, terminal-command files, version-specific environment examples, backend-package summaries, and per-version deployment/build helpers are intentionally not retained at the root of `main`.

The exact repository state immediately before the September 29, 2026 cleanup is preserved on:

`archive/pre-root-cleanup-2026-09-29-core`

Git history continues to preserve prior source and release artifacts. Generated release material should live in release bundles or ignored staging directories instead of accumulating in the source-tree root.
