from __future__ import annotations
import os
from sqlalchemy import select, text
from .database import Base, Database
from .models import (
    ApiPlan, EvaluationDefinition, LiveDataConnector, LiveDataSource, PredicateDefinition,
    SchemaMigration, WorkflowDefinition, ServiceLevelObjective,
    ScientificStorageBackend, ScientificProcessingAdapter,
    ResearchProjectRecord, ResearchModelRecord, ResearchModelVersionRecord, ResearchVariableRecord,
    ResearchParameterRecord, ResearchScenarioRecord, ResearchModelRunRecord, ResearchResultRecord,
    VisualReasoningObjectRecord, VisualReasoningElementRecord, VisualReasoningRelationRecord,
    VisualReasoningLayerRecord, VisualReasoningAnnotationRecord, VisualReasoningSnapshotRecord,
    VisualizationSpecificationRecord, RendererDefinitionRecord, RendererVersionRecord,
    RendererCompatibilityRuleRecord, RendererResolutionRecord,
    SystemMapRecord, SystemMapBoundaryRecord, SystemMapDomainRecord, SystemMapMembershipRecord, SystemMapViewRecord,
    FlowMapRecord, FlowMapChannelRecord, FlowMapFlowRecord, FlowMapNodeStateRecord, FlowMapViewRecord,
    ScenarioLandscapeRecord, ScenarioLandscapeScenarioRecord, ScenarioLandscapeDimensionRecord, ScenarioLandscapeValueRecord, ScenarioLandscapeViewRecord,
    ModelCanvasRecord, ModelCanvasNodeRecord, ModelCanvasEdgeRecord, ModelCanvasControlRecord, ModelCanvasStateRecord, ModelCanvasViewRecord,
    ScenarioComputePlanRecord, ScenarioComputeCaseRecord, ScenarioComputeRequestRecord, ScenarioComputeAttemptRecord, ScenarioComputeResultBindingRecord,
    UncertaintyDefinitionRecord, SensitivityStudyRecord, SensitivityFactorRecord, SensitivityMeasureRecord, EnsembleRecord, EnsembleMemberRecord, EnsembleStatisticRecord, UncertaintyComputeRunRecord,
    CausalGraphRecord, CausalVariableRecord, CausalEdgeRecord, CausalInterventionRecord, CausalIdentificationRecord, CausalEstimateRecord, CausalDiagnosticRecord,
    SpatialTemporalSceneRecord, SpatialFeatureRecord, TemporalEventRecord, TrajectoryRecord, TrajectoryPointRecord, SpatialTemporalChangeRecord, SpatialTemporalViewRecord,
    ResearchVisualExplanationRecord, ResearchExplanationNodeRecord, ResearchExplanationRelationRecord,
    ResearchExplanationCitationRecord, ResearchExplanationViewRecord, ResearchExplanationSnapshotRecord,
    CrossProductVisualResearchObjectRecord, CrossProductVisualResearchMemberRecord, CrossProductVisualResearchRelationRecord,
    CrossProductVisualResearchViewRecord, CrossProductVisualResearchSnapshotRecord,
    ReproducibleVisualKnowledgePackageRecord, ReproducibleVisualKnowledgeInputRecord, ReproducibleVisualKnowledgeEnvironmentRecord,
    ReproducibleVisualKnowledgeReplayPlanRecord, ReproducibleVisualKnowledgeVerificationRecord, ReproducibleVisualKnowledgeSnapshotRecord,
    ForensicInvestigationRecord, ForensicObjectRecord, ForensicEvidenceItemRecord, ForensicEvidenceSourceBindingRecord,
    ForensicProvenanceActivityRecord, ForensicObjectRelationRecord, ForensicSnapshotRecord,
    ForensicCustodianRecord, ForensicCustodyEventRecord, ForensicEvidenceSealRecord, ForensicIntegrityCheckRecord,
    ForensicCustodyContinuityAssessmentRecord, ForensicCustodySnapshotRecord,
    ForensicClaimRecord, ForensicClaimEvidenceAssessmentRecord, ForensicContradictionRecord,
    ForensicHypothesisRecord, ForensicHypothesisEvidenceAssessmentRecord, ForensicHypothesisRelationRecord, ForensicReasoningSnapshotRecord,
    ForensicEventRecord, ForensicEventEvidenceBindingRecord, ForensicEventParticipantRecord, ForensicEventRelationRecord,
    ForensicEventReconstructionRecord, ForensicTimelineViewRecord, ForensicTimelineSnapshotRecord,
    ForensicPlaceRecord, ForensicEvidenceSpatialBindingRecord, ForensicEventPlaceBindingRecord, ForensicSpatialUncertaintyEnvelopeRecord,
    ForensicTrajectoryEvidenceRecord, ForensicSpatialTemporalIntersectionRecord, ForensicSpatialTemporalViewRecord, ForensicSpatialTemporalSnapshotRecord,
    ForensicMediaArtifactRecord, ForensicMediaDerivativeRecord, ForensicMediaMetadataRecord, ForensicMediaFingerprintRecord,
    ForensicMediaSegmentRecord, ForensicMediaComparisonRecord, ForensicMediaProvenanceSnapshotRecord,
    ForensicQuantitativeReconstructionRecord, ForensicQuantitativeMeasurementRecord, ForensicQuantitativeAssumptionRecord,
    ForensicQuantitativeParameterRecord, ForensicQuantitativeScenarioRecord, ForensicQuantitativeHandoffRecord,
    ForensicQuantitativeResultBindingRecord, ForensicQuantitativeReproductionPackageRecord,
    ForensicStatementRecord, ForensicStatementSourceContextRecord, ForensicDocumentRecord, ForensicDocumentAssertionRecord,
    ForensicStatementClaimBindingRecord, ForensicStatementRelationRecord, ForensicTemporalConsistencyRecord, ForensicDocumentarySnapshotRecord,
    ForensicResearchGraphRecord, ForensicResearchGraphNodeRecord, ForensicResearchGraphEdgeRecord, ForensicResearchGraphViewRecord,
    ForensicResearchGraphHandoffRecord, ForensicResearchGraphSnapshotRecord, ForensicResearchGraphPackageRecord,
    ForensicInvestigationPackageRecord, ForensicInvestigationPackageComponentRecord, ForensicInvestigationPackageArtifactRecord,
    ForensicInvestigationPackageEnvironmentRecord, ForensicInvestigationPackageVerificationRecord, ForensicInvestigationPackageReviewRecord,
    ForensicInvestigationPackageSnapshotRecord,
    PredictiveModelRecord, PredictiveTargetRecord, PredictiveFeatureRecord, PredictiveTrainingWindowRecord,
    PredictiveForecastRunRecord, PredictiveForecastObservationRecord, PredictiveEvaluationRecord,
    PredictiveRuntimeHandoffRecord, PredictiveForecastSnapshotRecord,
    PredictiveTimeSeriesDatasetRecord, PredictiveForecastWindowRecord, PredictiveBaselineModelRecord, PredictiveBacktestPlanRecord,
    PredictiveBacktestFoldRecord, PredictiveBacktestObservationRecord, PredictiveBacktestEvaluationRecord, PredictiveBacktestPackageRecord,
    PredictiveProbabilisticForecastRecord, PredictiveCalibrationStudyRecord, PredictiveCalibrationBinRecord, PredictiveCalibrationMappingRecord,
    PredictiveProbabilisticEvaluationRecord, PredictiveCalibrationPackageRecord,
    PredictiveEnsembleRecord, PredictiveEnsembleMemberRecord, PredictiveEnsembleForecastRecord,
    PredictiveComparisonStudyRecord, PredictiveComparisonCandidateRecord, PredictiveComparisonEvidenceRecord,
    PredictivePairwiseComparisonRecord, PredictiveComparisonPackageRecord,
    PredictiveMonitoringStudyRecord, PredictiveDetectionRuleRecord, PredictiveAnomalyObservationRecord,
    PredictiveChangePointRecord, PredictiveEarlyWarningSignalRecord, PredictiveMonitoringEpisodeRecord, PredictiveMonitoringPackageRecord,
    PredictiveSpatialTemporalStudyRecord, PredictiveSpatialUnitRecord, PredictiveSpatialTemporalForecastRecord, PredictiveSpatialTemporalObservationRecord,
    PredictiveSpatialPropagationEvidenceRecord, PredictiveSpatialHotspotEvidenceRecord, PredictiveSpatialTemporalEvaluationRecord, PredictiveSpatialTemporalPackageRecord,
    VisualGrammarSpecificationRecord, VisualGrammarDataBindingRecord, VisualGrammarMarkRecord, VisualGrammarScaleRecord,
    VisualGrammarEncodingRecord, VisualGrammarTransformRecord, VisualGrammarGuideRecord, VisualGrammarSnapshotRecord,
    VisualLinkPolicyRecord, VisualSelectionSetRecord, VisualCrossFilterRecord, VisualBrushRangeRecord,
    VisualFocusHighlightRecord, VisualPropagationRecord, VisualLinkedViewSnapshotRecord,
    VisualExplorationSessionRecord, VisualQueryTargetRecord, VisualQueryRequestRecord, VisualQueryPredicateRecord,
    VisualTraversalRequestRecord, VisualQueryResultBindingRecord, VisualExplorationStateRecord, VisualQuerySnapshotRecord,
    VisualModelConstructionRecord, VisualModelComponentRecord, VisualModelRelationshipRecord, VisualModelAssumptionRecord,
    VisualModelConstraintRecord, VisualModelInterventionRecord, VisualModelHandoffRecord, VisualModelSnapshotRecord,
    VisualPredictiveWorkspaceRecord, VisualForecastOverlayRecord, VisualUncertaintyDisplayRecord, VisualCalibrationDisplayRecord,
    VisualEnsembleComparisonOverlayRecord, VisualMonitoringOverlayRecord, VisualSpatialTemporalForecastLayerRecord,
    VisualCausalPredictiveOverlayRecord, VisualDecisionPredictionBindingRecord, VisualPredictiveSnapshotRecord,
    VisualDecisionWorkspaceRecord, VisualDecisionAlternativeRecord, VisualDecisionCriterionRecord, VisualDecisionEvidenceBindingRecord,
    VisualDecisionScenarioBindingRecord, VisualDecisionRiskOverlayRecord, VisualDecisionTradeoffRecord, VisualDecisionRationaleRecord,
    VisualDecisionHandoffRecord, VisualDecisionSnapshotRecord,
    UnifiedVisualReasoningWorkspaceRecord, UnifiedVisualLayerBindingRecord, UnifiedVisualReasoningPathRecord,
    UnifiedVisualStateBridgeRecord, UnifiedVisualEvidenceChainRecord, UnifiedVisualRuntimeHandoffRecord,
    UnifiedVisualPackageBindingRecord, UnifiedVisualReplayStateRecord, UnifiedVisualReasoningSnapshotRecord,
    CrossProductVisualRuntimeIntegrationRecord, CrossProductVisualObjectBindingRecord, CrossProductVisualContextBindingRecord,
    CrossProductVisualCapabilityBindingRecord, CrossProductVisualViewBindingRecord, CrossProductVisualHandoffRouteRecord,
    CrossProductVisualSyncRecord, CrossProductVisualIntegrationSnapshotRecord,
    UnifiedResearchProjectProfileRecord, UnifiedResearchQuestionRecord, UnifiedResearchObjectiveRecord,
    UnifiedResearchComponentRecord, UnifiedResearchRelationshipRecord, UnifiedResearchProvenanceRecord,
    UnifiedResearchRuntimeHandoffRecord, UnifiedResearchProjectSnapshotRecord,
    ResearchLineageGraphRecord, ResearchLineageNodeRecord, ResearchLineageEdgeRecord, ResearchLineageActivityRecord,
    ResearchLineageTransformationRecord, ResearchLineageSourceBindingRecord, ResearchLineageTraceRecord, ResearchLineageSnapshotRecord,
    UncertaintyEvidenceStudyRecord, UncertaintyDistributionEvidenceRecord, ProbabilisticSummaryEvidenceRecord, SensitivityIndexEvidenceRecord, UncertaintyEnsembleEvidenceRecord, UncertaintyEvidenceInterpretationRecord, UncertaintyEvidenceSnapshotRecord,
)
from .predicate_catalog import DEFAULT_PREDICATES
from .api_plan_catalog import DEFAULT_API_PLANS
from .evaluation_catalog import DEFAULT_EVALUATION_DEFINITIONS
from .workflow_catalog import DEFAULT_WORKFLOW_DEFINITIONS
from .live_data_catalog import DEFAULT_LIVE_DATA_CONNECTORS, DEFAULT_LIVE_DATA_SOURCES

MIGRATIONS = [
    ("0001", "Initial universal entity registry, relationships, aliases, evidence foundations, validation events, and import jobs."),
    ("0002", "Knowledge Graph predicate registry, relationship review records, graph indexes, and default controlled vocabulary."),
    ("0003", "Evidence Ledger claims, source snapshots, evidence records, calculation traces, provenance activities, review assignments, and tamper-evident ledger chain."),
    ("0004", "Unified Public API plans, developer applications, hashed credentials, request usage records, webhooks, and developer portal infrastructure."),
    ("0005", "Trust Center evaluation definitions, immutable evaluation runs and checks, findings, incidents, known limitations, attestations, and public trust status."),
    ("0006", "Signature dossiers, frozen record snapshots, approvals, platform signatures, workflow definitions, runs, steps, and append-only transitions."),
    ("0007", "Free live-data source registry, connector definitions, ingestion runs, bounded raw records, normalized observations, freshness, and provenance."),
    ("0008", "International-law and United Nations connector pack, dedicated legal-authority records, official-document provenance, and public discovery APIs."),
    ("0009", "Scientific data connector pack, normalized scientific dataset records, astronomy and laboratory discovery, and public science APIs."),
    ("0010", "Economics and official-statistics connector pack, normalized economic records, revisions, releases, and public economics APIs."),
    ("0011", "Geospatial, time-series, STAC, map-layer, and scientific-asset data fabric with portable GeoJSON storage and PostgreSQL spatial indexes."),
    ("0012", "Streaming event log, persistent connector work queue, alert rules, geographic subscriptions, dead-letter records, replay, stale-source detection, and provider failover control plane."),
    ("0013", "Operational facility registry, source identifiers, facility-level status observations, geospatial facility lookup, and provenance-preserving operational evidence history."),
    ("0014", "Humanitarian access and essential-services condition fabric with facility linkage, structured-source materialization, semantic roles, and provenance-preserving country evidence."),
    ("0015", "Country evidence federation and reconciliation with authority-role precedence, comparability guards, discrepancy detection, and auditable non-blending selection records."),
    ("0016", "Earth, ocean, space, and scientific service routing with persisted domain bindings, explicit classification provenance, and non-truth-precedence navigation indexes."),
    ("0017", "Cross-product evidence exchange packages, canonical artifact references, governed snapshots, receipts, idempotency, and non-destructive provenance-preserving handoff records."),
    ("0018", "Distributed processing, partition leases, storage-object registry, backpressure, retention, compaction, and scale diagnostics control plane."),
    ("0019", "Governance policies, principal-role bindings, persisted access decisions, tamper-evident audit chain, retention policy controls, and public-safe governance readiness."),
    ("0020", "Production certification runs, migration-assurance snapshots, recovery checkpoints, integrity verification, and release-recovery readiness records."),
    ("0021", "First-party observability metrics, service-level objectives, deployment markers, retention, and public-safe production operations status."),
    ("0022", "Operational incidents, append-only incident-event integrity chain, governed change controls, and operator-confirmed rollback coordination."),
    ("0023", "Continuity, backup-artifact verification, disaster-recovery objectives, restore rehearsals, RPO/RTO evidence, and certification integration."),
    ("0024", "Multi-region service health, failover groups, replication-aware failover assessments, read-only degraded mode, and operator-coordinated recovery routing."),
    ("0025", "Data lifecycle policies, preservation archives, integrity manifests, policy/legal holds, tombstone lineage, and non-destructive archive restoration records."),
    ("0026", "Federated Core trusted-node registry, trust relationships, authenticated exchange manifests, and reference-first remote evidence intake records."),
    ("0027", "Capacity resource profiles, observations, bounded forecast records, resource budgets, and non-actuating governance decisions."),
    ("0028", "Credential registry metadata, cryptographic key versions, overlap-aware rotation records, lifecycle events, and secret-free credential-use audit records."),
    ("0029", "Database-shared distributed quota policies and usage buckets, workload classes, auditable admission decisions, and expiring concurrency leases."),
    ("0030", "Scientific object storage backends, governed stored-object registry, processing adapter contracts, derived-object lineage, and auditable processing runs."),
    ("0031", "Research projects, models, immutable model versions, variables, parameters, scenarios, model runs, results, and graph-native research semantics."),
    ("0032", "Renderer-neutral visual reasoning objects, semantic elements and relations, layers, annotations, source bindings, and immutable semantic snapshots."),
    ("0033", "Immutable visualization specifications, renderer contract registry, renderer-version metadata, governed compatibility rules, and non-executing renderer resolution records."),
    ("0034", "Governed System Maps with explicit system boundaries, domains, element memberships, saved views, structural validation, and deterministic visualization-specification compilation."),
    ("0035", "Governed Flow Maps with typed channels, relation-bound directed flows, quantitative and uncertainty metadata, node-state observations, saved flow views, unit-safe balance summaries, validation, and visualization-specification compilation."),
    ("0036", "Governed Scenario Landscapes binding research scenarios to explicit comparison roles, dimensions, uncertainty-aware values, baseline-relative summaries, saved views, validation, and visualization-specification compilation."),
    ("0037", "Governed Interactive Model Canvas with model-bound nodes, dependency edges, parameter controls, immutable interaction states, saved views, external-execution handoff contracts, structural validation, and visualization-specification compilation."),
    ("0038", "Governed Scenario Compute Engine orchestration with reproducible compute plans, scenario cases, parameter-override validation, deterministic input manifests, idempotent execution requests, external execution attempts, and research run/result bindings."),
    ("0039", "Governed uncertainty definitions, sensitivity-study factors and externally supplied measures, ensemble memberships and externally supplied statistics, with explicit provenance and no Core-side sampling, sensitivity algorithms, ensemble aggregation, or model execution."),
    ("0040", "Reproducible uncertainty compute runtime with Monte Carlo/LHS sampling, Sobol/Morris analysis helpers, ensemble normalization/statistics, exceedance probabilities, and governed Lab/Workbench handoffs; preserves the v2.36 production schema."),
    ("0041", "Causal Systems Explorer with governed causal graphs, interventions, explicit identification assumptions, attributable estimates, diagnostics, deterministic DAG/path reasoning, conservative adjustment candidates, and Lab/Workbench handoffs."),
    ("0042", 'Spatial-temporal visual reasoning with governed scenes, GeoJSON feature bindings, events and intervals, trajectories, change observations, saved views, map/timeline specifications, and explicit Site Intelligence/Lab/Workbench handoffs.'),
    ("0043", 'Research Librarian visual explanation with governed explanation objects, semantic nodes and relations, evidence/citation bindings, saved views, immutable snapshots, renderer-neutral specifications, and explicit Research Librarian/specialist-runtime handoffs.'),
    ("0044", 'Cross-product visual research objects with explicit product-scoped members, semantic relations, saved composite views, immutable snapshots, portable reference-first packages, renderer-neutral composition, and non-executing cross-runtime handoffs.'),
    ("0045", 'Reproducible visual knowledge packages with versioned input references and hashes, captured runtime environments, external-only replay plans, integrity fingerprints, verification evidence, immutable snapshots, and portable provenance-preserving manifests.'),
    ("0046", 'Forensic object model with governed investigations, typed forensic objects, evidence items, source bindings, provenance activities, semantic relations, immutable snapshots, hash/source metadata, and explicit non-custody/non-attribution boundaries.'),
    ("0047", 'Evidence integrity and chain-of-custody records with custodians, hash-chained custody events, seals, integrity checks, continuity assessments, immutable custody snapshots, external attestations, and explicit non-authenticity/non-admissibility boundaries.'),
    ("0048", 'Claims, contradictions, and competing-hypothesis records with evidence-position assessments, explicit contradiction registries, hypothesis relations, descriptive comparison matrices, immutable reasoning snapshots, and explicit non-verdict/non-ranking boundaries.'),
    ("0049", 'Forensic timeline and event reconstruction with evidence-linked events, bounded temporal assertions, participant and event relations, explicit reconstruction hypotheses, saved timeline views, immutable snapshots, and non-determinative sequence boundaries.'),
    ("0050", 'Forensic spatial/temporal evidence integration with places, evidence/event location bindings, uncertainty envelopes, trajectory evidence, explicit space-time intersections, linked map-timeline views, Site Intelligence handoffs, immutable snapshots, and non-analytical boundaries.'),
    ("0051", 'Media artifact and derivative provenance with typed media records, declared transformation lineage, metadata observations, fingerprint records, segment/frame references, comparison records, immutable snapshots, and explicit non-authenticity/non-attribution boundaries.'),
    ("0052", 'Quantitative forensic reconstruction with governed models, measurements, assumptions, parameters, scenarios, external Workbench/Lab handoffs, result bindings, reproducible packages, uncertainty metadata, and explicit non-executing/non-verdict boundaries.'),
    ("0053", 'Testimony, statements, and documentary evidence with governed speaker/author references, source-context preservation, claim bindings, explicit corroboration/contradiction relations, temporal-consistency records, and immutable documentary snapshots without credibility or authorship determination.'),
    ("0054", 'Forensic Research Graph with governed graph registries, typed cross-forensics nodes, explicit evidence-backed edges, renderer-neutral views, cross-product handoffs, immutable snapshots, and portable packages without automated identity, causal, proof, or truth inference.'),
    ("0055", 'Reproducible Investigation Packages with frozen cross-forensics component manifests, artifact and environment records, integrity verification, review records, immutable snapshots, and portable review bundles without authenticity, admissibility, causal, or truth determination.'),
    ("0056", 'Predictive model and forecast provenance with governed models, targets, features, training windows, forecast runs and observations, descriptive evaluation evidence, specialist-runtime handoffs, and immutable snapshots without Core-side fitting, inference, ranking, calibration, or truth promotion.'),
    ("0057", 'Time-series forecasting and backtesting with governed datasets, forecast windows, baselines, rolling/expanding plans, leakage-aware folds, prediction-actual pairs, evaluation evidence, and reproducible packages without Core-side fitting, forecast/backtest execution, metric computation, or ranking.'),
    ("0058", 'Probabilistic forecasting and calibration with governed probability, quantile, interval, distribution, calibration-study, mapping, scoring evidence, and reproducible packages without Core-side recalibration fitting/application, probabilistic inference, or automatic model ranking.'),
    ("0059", 'Predictive ensembles and model comparison with governed ensemble definitions, members, external forecasts, comparison candidates, metric and pairwise evidence, and reproducible packages without Core-side weight optimization, ensemble execution, metric computation, ranking, or model selection.'),
    ("0060", 'Anomaly, change-point, and early-warning intelligence with governed monitoring studies, detection rules, external anomaly/change/signal evidence, monitoring episodes, and reproducible packages without Core-side detection, threshold optimization, alert dispatch, causal attribution, or intervention.'),    ("0061", 'Spatial-temporal predictive intelligence with governed studies, spatial units, forecast/observation fields, propagation and hotspot evidence, external evaluations, and reproducible packages; Core does not interpolate, infer spatially, predict trajectories, model propagation, or detect hotspots.'),
    ("0062", 'Causal-predictive integration with governed studies, bindings, intervention scenarios, external counterfactual forecasts, effect/evaluation evidence, handoffs, and packages; Core does not learn structure, estimate effects, execute counterfactuals, simulate interventions, or optimize decisions.'),
    ("0063", 'Predictive decision intelligence with governed studies, options, criteria, evidence bindings, external assessments/evaluations, handoffs, and packages; Core does not compute utility/regret, rank or recommend options, optimize policies, solve constraints, select actions, or execute decisions.'),
    ("0064", 'Reproducible predictive intelligence packages with governed cross-layer manifests, artifacts, environments, verification/review evidence, and immutable hash-chained snapshots; Core does not execute, refit, regenerate forecasts, rerun analyses, optimize decisions, or reproduce automatically.'),
    ("0065", 'Visual reasoning runtime and scene graph with governed scenes, nodes, edges, layers, views, bindings, and immutable snapshots; Core stores renderer-neutral semantic and interaction state but does not render, compute layout, animate, infer visually, hit-test, or execute GPU work.'),    ("0066", 'Interactive renderer and view composition with governed renderer profiles, compositions, assignments, link groups, propagated interaction state, and immutable snapshots; Core coordinates renderer-neutral views but does not draw, layout, animate, hit-test, run GPU work, or infer visually.'),    ("0067", 'Analytical visualization grammar with governed specifications, bindings, marks, encodings, scales, transforms, guides, and immutable snapshots; Core stores renderer-neutral grammar but does not execute transforms, calculate scales/layout, draw marks, aggregate data, or infer visually.'),
    ("0068", 'Linked views and cross-filtering with governed policies, selections, filters, brush ranges, focus/highlight state, propagation evidence, and immutable snapshots; Core stores interaction contracts but does not execute queries, filter data, dispatch UI events, or infer visually.'),
    ("0069", 'Visual query/exploration with governed sessions, targets, predicates, traversal requests, external result/evidence bindings, saved states, and immutable snapshots; Core records intent/provenance but does not execute queries, traverse graphs, retrieve data, rank results, or infer visually.'),
    ("0070", 'Visual model construction with governed components, relationships, assumptions, constraints, interventions, external runtime handoffs, and immutable snapshots; Core records model semantics/provenance but does not solve equations, optimize constraints, run simulations, or execute models.'),
    ("0071", 'Visual predictive intelligence with governed forecast, uncertainty, calibration, ensemble, monitoring, spatial-temporal, causal, and decision overlays plus immutable snapshots; Core binds predictive evidence to views but does not forecast, calibrate, detect anomalies, simulate, rank, or render.'),
    ("0072", 'Visual forensics workbench with governed evidence, claims, timelines, spatial-temporal, media, reconstruction, documentary, research-graph bindings, and immutable snapshots; Core coordinates forensic views but does not authenticate evidence, infer guilt, reconstruct automatically, or render.'),    ("0073", 'Visual decision intelligence with governed workspaces, alternatives, criteria, evidence, scenarios, risk, tradeoffs, rationale, handoffs, and immutable snapshots; Core coordinates decision views but does not rank, recommend, optimize, select actions, execute decisions, or infer visually.'),    ("0074", 'Unified visual reasoning engine with governed workspaces, bindings, reasoning paths, state bridges, evidence chains, handoffs, replay states, packages, and immutable snapshots; Core coordinates cross-layer semantics but does not render, compute, infer conclusions, rank options, or execute.'),    ("0075", 'Cross-product visual runtime integration with governed product, object, context, capability, view, handoff, sync, and snapshot records; Core coordinates shared visual contracts across Catalyst products but does not render, compute, mutate specialist state, infer conclusions, or execute.'),    ("0076", 'Unified research project model with governed profiles, questions, objectives, typed components, relationships, provenance, runtime handoffs, and immutable snapshots; Core preserves research state and lineage but does not execute analyses, generate findings, infer originality, or promote conclusions.'),    ("0077", 'Research lineage and provenance graph with governed graphs, nodes, explicit edges, activities, transformations, source bindings, deterministic traces, and immutable snapshots; Core traces declared provenance but does not infer missing links, causality, truth, originality, or execute analyses.'),
    ("0078", 'Methodology and analysis run registry with governed methods, versions, variables, assumptions, parameters, environments, runs, inputs, outputs, and snapshots; Core records declared methods and executions but does not run analyses, validate results, infer causality, or judge research quality.'),
    ("0079", 'Reproducible research packages with governed manifests, components, artifacts, environments, replay plans, verification/review evidence, and immutable snapshots; Core freezes declared research state but does not execute replay, rerun analyses, validate findings, or certify scientific truth.'),    ("0080", 'Research notebooks with governed sections, ordered entries, cross-research bindings, citations, analytical narratives, revisions, and immutable snapshots; Core preserves context and provenance but does not execute code, generate narrative, fabricate citations, infer conclusions, or publish.'),
    ("0081", 'Finding, claim, interpretation, and evidence-link intelligence with version history, derivation lineage, structured contradiction flags, declared uncertainty/strength metadata, and immutable snapshots; Core records research judgment but does not infer truth, rank claims, or resolve contradictions.'),
    ("0082", 'Hypothesis/competing-explanation intelligence with governed sets, assumptions, predictions, evidence assessments, relations, discrimination gaps, revisions, comparison matrices, and snapshots; Core does not generate, score, rank, select, confirm, reject, or infer truth.'),
    ("0083", 'Research argument and evidentiary synthesis with governed argument graphs, researcher-authored syntheses, counterarguments, unresolved tensions, revision history, descriptive coverage, and immutable snapshots; Core does not generate, score, rank, resolve, or infer truth.'),
    ("0084", 'Research conclusion governance with researcher-authored conclusions, evidence bindings, caveats, dissent, decision traces, reviews, revision history, descriptive governance summaries, and immutable snapshots; Core does not choose, score, certify, publish, or infer truth.'),
    ("0085", 'Reproducible scholarly publications with sections, references/citations, figures, supplements, identifiers, exports, readiness diagnostics, lineage, revisions, and snapshots; Core does not author conclusions, fabricate citations, judge quality, issue identifiers, or publish externally.'),
    ("0086", 'Peer review, replication, and rebuttal records with comments/responses, replication attempts/comparisons, rebuttal points, revisions, lineage, and snapshots; Core does not generate reviews, score quality, infer replication success, resolve rebuttals, or decide publication.'),
    ("0087", 'Cross-study evidence synthesis and meta-research with governed study inclusion, outcomes, extracted effects, external meta-analysis results, assessments, relations, gaps, revisions, lineage, and snapshots; Core does not search, select, compute, pool, score, rank, infer causality, or infer truth.'),
    ("0088", 'Research programs and longitudinal knowledge graphs with projects, objectives, milestones, declared nodes/edges, knowledge states, evolution events, revisions, lineage, and snapshots; Core does not prioritize, fund, auto-link, rank, forecast success, infer causality, or infer truth.'),    ("0089", 'Research portfolios and institutional knowledge governance with programs, themes, objectives, dependencies, declared resources, risks, reviews, decisions, revisions, lineage, and snapshots; Core does not rank, prioritize, allocate, optimize, decide governance, forecast success, or infer truth.'),    ("0090", 'Universal research protocols with scope, measures, source/acquisition/method/validation plans, assumptions, outputs, deviations, revisions, lineage, and snapshots; Core records declared plans but does not execute, collect data/evidence, analyze, certify ethics, approve, or infer truth.'),
    ("0091", 'Computation/analysis execution lineage with governed external runs, versioned inputs, parameters, assumptions, environments, steps, outputs, research bindings, dependencies, verification evidence, revisions, and snapshots; Core records provenance but does not execute code or infer results.'),    ("0092", 'Unified inference semantics linking findings, claims, conclusions, computation outputs, evidence, assumptions, uncertainty, relations, challenges, revisions, and snapshots; Core records declared classifications/lineage but does not infer, score, validate, resolve, rank, or determine truth.'),    ("0093", 'Research quality and methodological audits with subjects, systematic checks, findings, evidence, bias/method assessments, responses, revisions, lineage, and snapshots; Core records declared audit evidence but does not infer bias, score quality, rank studies, certify validity, or determine truth.'),    ("0094", 'Governed research workflows with stages, transitions, context bindings, handoffs, checkpoints, events, policies, revisions, lineage, and snapshots; Core coordinates recorded state but does not choose paths, execute specialist work, infer completion, approve validity, or determine truth.'),
    ("0095", 'Cross-product research context/handoff with envelopes, bindings, state markers, packages, acknowledgements, conflicts, revisions, lineage, and snapshots; Core preserves declared context but does not auto-route, execute, mutate sources, resolve conflicts, authorize access, or infer truth.'),
    ("0096", 'Research project state/versioning with immutable versions, object/environment bindings, dependencies, checkpoints, reconstruction plans, verification evidence, revisions, and snapshots; Core preserves history but does not replay work, restore state, infer reproducibility, or determine truth.'),    ("0097", 'Research contributor/role provenance with assignments, contributions, agent profiles/actions, authorship, responsibility, reviews, revisions, and snapshots; Core records attribution but does not assign authority, execute agents, decide credit, rank contributors, or infer truth.'),
    ("0098", 'Research validation/challenge records for alternatives, contradiction tests, counterevidence, sensitivity, robustness, replication, reviewer challenges, responses, revisions, and snapshots; Core records evidence but does not resolve hypotheses, certify validity, rank outcomes, or infer truth.'),
    ("0099", 'Scholarly interoperability packages with governed citations, identifiers, dataset/notebook descriptors, provenance manifests, metadata/export profiles, publication bindings, validation evidence, revisions, and snapshots; Core does not mint IDs, publish, execute notebooks, or certify results.'),
    ("0100", 'Unified research runtime contracts for object types, operations, capabilities, product bindings, exchanges, invocations, results, compatibility, revisions, and snapshots; Core standardizes declared interfaces but does not execute work, auto-route, authorize access, validate results, or infer truth.'),
    ("0101", 'Integration certification with suites, product targets, conformance cases/results, exchange/trace/reconstruction checks, evidence, findings, revisions, and snapshots; Core records declared conformance but does not invoke products, certify science, rank quality, authorize, or determine truth.'),    ("0102", 'Unified research/scientific/investigation runtime sessions with project, object, product, execution, visual, validation, package, and handoff bindings plus revisions/snapshots; Core composes declared references but does not execute work, infer conclusions, authorize access, or determine truth.'),    ("0103", 'Analytical runtime provider registry, capabilities, execution requests/results, environments, artifacts, diagnostics, and reproduction references; Core governs declared contracts while Workspace/specialist runtimes execute computation.'),
    ("0104", 'Analytical result and provenance integration with first-class result, estimate, uncertainty, lineage, ingestion-receipt, and immutable snapshot records; Core records governed outputs without executing analysis or certifying scientific validity.'),
    ("0105", 'Statistical reasoning object model with diagnostics, assumptions, robustness evidence, model comparisons, coefficients, intervals, researcher interpretations, and immutable snapshots; Core records statistical evidence without certifying validity, significance, causality, or preferred models.'),
    ("0106", "Platform Core v3.20.0 — Unified Investigation Workspace"),
    ("0107", "Platform Core v3.20.0.1 — Investigation Workspace Schema & Release Identity Repair"),
    ("0108", "Platform Core v3.21.0 — Uncertainty & Probabilistic Evidence Integration"),
]





DEFAULT_SCIENTIFIC_STORAGE_BACKENDS = [
    {
        "backend_key": "local-filesystem",
        "name": "Local scientific object store",
        "backend_type": "filesystem",
        "uri_scheme": "file",
        "readable": True,
        "writable": True,
        "enabled": True,
        "public_summary": True,
        "capabilities_json": {"content_addressed": True, "atomic_write": True, "development_default": True},
        "metadata_json": {"seed": "platform-core-v2.27.0", "secret_values_stored": False},
    },
    {
        "backend_key": "external-reference",
        "name": "External scientific object reference",
        "backend_type": "reference",
        "uri_scheme": "provider-neutral",
        "readable": True,
        "writable": False,
        "enabled": True,
        "public_summary": True,
        "capabilities_json": {"schemes": ["https", "s3", "gs", "az"], "fetch_by_core": False},
        "metadata_json": {"seed": "platform-core-v2.27.0", "credential_bearing_urls_allowed": False},
    },
]

DEFAULT_SCIENTIFIC_PROCESSING_ADAPTERS = [
    {
        "adapter_key": "builtin.object-manifest",
        "name": "Scientific object manifest",
        "description": "Built-in deterministic adapter that emits a provenance-preserving JSON manifest for a stored scientific object.",
        "execution_mode": "in-process",
        "runtime": "python",
        "supported_input_formats_json": ["*"],
        "supported_output_formats_json": ["json"],
        "operations_json": ["manifest"],
        "configuration_schema_json": {},
        "enabled": True,
        "executable": True,
        "public_summary": True,
        "metadata_json": {"seed": "platform-core-v2.27.0", "arbitrary_code_execution": False},
    },
    {
        "adapter_key": "external.xarray",
        "name": "xarray processing contract",
        "description": "Provider-neutral contract for future xarray-backed NetCDF, Zarr, and GRIB processing workers.",
        "execution_mode": "external-contract",
        "runtime": "python",
        "supported_input_formats_json": ["netcdf", "zarr", "grib2"],
        "supported_output_formats_json": ["netcdf", "zarr", "json"],
        "operations_json": ["inspect", "subset", "aggregate", "rechunk"],
        "configuration_schema_json": {"worker_service": {"type": "string", "secret": False}},
        "enabled": False,
        "executable": False,
        "public_summary": True,
        "metadata_json": {"seed": "platform-core-v2.27.0", "status": "contract-only"},
    },
    {
        "adapter_key": "external.gdal",
        "name": "GDAL processing contract",
        "description": "Provider-neutral contract for future raster/vector translation, reprojection, tiling, and overview workers.",
        "execution_mode": "external-contract",
        "runtime": "native",
        "supported_input_formats_json": ["cog", "geoparquet", "geojson", "grib2"],
        "supported_output_formats_json": ["cog", "geoparquet", "geojson", "pmtiles"],
        "operations_json": ["inspect", "translate", "reproject", "overview", "tile"],
        "configuration_schema_json": {"worker_service": {"type": "string", "secret": False}},
        "enabled": False,
        "executable": False,
        "public_summary": True,
        "metadata_json": {"seed": "platform-core-v2.27.0", "status": "contract-only"},
    },
    {
        "adapter_key": "external.astropy",
        "name": "Astropy processing contract",
        "description": "Provider-neutral contract for future FITS and VOTable inspection and extraction workers.",
        "execution_mode": "external-contract",
        "runtime": "python",
        "supported_input_formats_json": ["fits", "votable"],
        "supported_output_formats_json": ["fits", "votable", "json"],
        "operations_json": ["inspect", "table-extract", "header-extract"],
        "configuration_schema_json": {"worker_service": {"type": "string", "secret": False}},
        "enabled": False,
        "executable": False,
        "public_summary": True,
        "metadata_json": {"seed": "platform-core-v2.27.0", "status": "contract-only"},
    },
]


def _seed_scientific_object_fabric(database: Database) -> tuple[int, int]:
    backends_created = 0
    adapters_created = 0
    with database.session_factory() as session:
        for payload in DEFAULT_SCIENTIFIC_STORAGE_BACKENDS:
            existing = session.scalar(select(ScientificStorageBackend).where(ScientificStorageBackend.backend_key == payload["backend_key"]))
            if existing is None:
                session.add(ScientificStorageBackend(**payload))
                backends_created += 1
        for payload in DEFAULT_SCIENTIFIC_PROCESSING_ADAPTERS:
            existing = session.scalar(select(ScientificProcessingAdapter).where(ScientificProcessingAdapter.adapter_key == payload["adapter_key"]))
            if existing is None:
                session.add(ScientificProcessingAdapter(**payload))
                adapters_created += 1
        session.commit()
    return backends_created, adapters_created


DEFAULT_RENDERER_DEFINITIONS = [
    {
        "renderer_key": "contract.d3",
        "name": "D3 renderer contract",
        "description": "Contract metadata for D3-capable external/browser runtimes. Core does not execute D3.",
        "renderer_family": "d3", "runtime": "browser", "execution_mode": "external-runtime",
        "enabled": True, "executable_by_core": False, "public_summary": True,
        "supported_spec_versions_json": ["1.0"],
        "capabilities_json": {"network": True, "diagram": True, "interaction": True, "map": False},
        "metadata_json": {"seed": "platform-core-v2.30.0", "installed_runtime_asserted": False},
    },
    {
        "renderer_key": "contract.vega-lite",
        "name": "Vega-Lite renderer contract",
        "description": "Contract metadata for Vega-Lite-capable external/browser runtimes. Core does not execute Vega-Lite.",
        "renderer_family": "vega-lite", "runtime": "browser", "execution_mode": "external-runtime",
        "enabled": True, "executable_by_core": False, "public_summary": True,
        "supported_spec_versions_json": ["1.0"],
        "capabilities_json": {"chart": True, "interaction": True, "network": False, "map": False},
        "metadata_json": {"seed": "platform-core-v2.30.0", "installed_runtime_asserted": False},
    },
    {
        "renderer_key": "contract.plotly",
        "name": "Plotly renderer contract",
        "description": "Contract metadata for Plotly-capable external runtimes. Core does not execute Plotly.",
        "renderer_family": "plotly", "runtime": "external-runtime", "execution_mode": "external-runtime",
        "enabled": True, "executable_by_core": False, "public_summary": True,
        "supported_spec_versions_json": ["1.0"],
        "capabilities_json": {"chart": True, "map": True, "interaction": True, "three_dimensional": True},
        "metadata_json": {"seed": "platform-core-v2.30.0", "installed_runtime_asserted": False},
    },
    {
        "renderer_key": "contract.maplibre",
        "name": "MapLibre renderer contract",
        "description": "Contract metadata for MapLibre-capable external/browser runtimes. Core does not execute MapLibre.",
        "renderer_family": "maplibre", "runtime": "browser", "execution_mode": "external-runtime",
        "enabled": True, "executable_by_core": False, "public_summary": True,
        "supported_spec_versions_json": ["1.0"],
        "capabilities_json": {"map": True, "interaction": True, "network": False, "chart": False},
        "metadata_json": {"seed": "platform-core-v2.30.0", "installed_runtime_asserted": False},
    },
]

DEFAULT_RENDERER_VERSIONS = [
    {"renderer_key": key, "version": "contract-v1", "status": "active", "contract_version": "1.0",
     "capabilities_json": {}, "metadata_json": {"seed": "platform-core-v2.30.0", "renderer_package_version_pinned": False}}
    for key in ("contract.d3", "contract.vega-lite", "contract.plotly", "contract.maplibre")
]

DEFAULT_RENDERER_COMPATIBILITY_RULES = [
    ("contract.d3", "system-map", "diagram", 300), ("contract.d3", "causal-map", "network", 320),
    ("contract.d3", "evidence-map", "network", 310), ("contract.d3", "flow-map", "network", 300),
    ("contract.d3", "model-map", "diagram", 300), ("contract.d3", "model-canvas", "diagram", 330), ("contract.vega-lite", "generic", "chart", 280),
    ("contract.vega-lite", "scenario-landscape", "chart", 300), ("contract.plotly", "scenario-landscape", "chart", 290),
    ("contract.plotly", "spatial-temporal-map", "chart", 220), ("contract.maplibre", "spatial-temporal-map", "map", 340),
    ("contract.maplibre", "flow-map", "map", 260), ("contract.d3", "*", "generic", 100),
]

def _seed_renderer_registry(database: Database) -> tuple[int, int, int]:
    definitions_created = versions_created = rules_created = 0
    with database.session_factory() as session:
        for payload in DEFAULT_RENDERER_DEFINITIONS:
            if session.get(RendererDefinitionRecord, payload["renderer_key"]) is None:
                session.add(RendererDefinitionRecord(**payload)); definitions_created += 1
        session.flush()
        for payload in DEFAULT_RENDERER_VERSIONS:
            existing = session.scalar(select(RendererVersionRecord).where(RendererVersionRecord.renderer_key == payload["renderer_key"], RendererVersionRecord.version == payload["version"]))
            if existing is None:
                session.add(RendererVersionRecord(**payload)); versions_created += 1
        for renderer_key, visual_kind, spec_kind, priority in DEFAULT_RENDERER_COMPATIBILITY_RULES:
            existing = session.scalar(select(RendererCompatibilityRuleRecord).where(RendererCompatibilityRuleRecord.renderer_key == renderer_key, RendererCompatibilityRuleRecord.visual_kind == visual_kind, RendererCompatibilityRuleRecord.spec_kind == spec_kind))
            if existing is None:
                session.add(RendererCompatibilityRuleRecord(renderer_key=renderer_key, visual_kind=visual_kind, spec_kind=spec_kind, priority=priority, required_capabilities_json=[], constraints_json={}, enabled=True, metadata_json={"seed":"platform-core-v2.30.0"})); rules_created += 1
        session.commit()
    return definitions_created, versions_created, rules_created

def _seed_predicates(database: Database) -> int:
    created = 0
    with database.session_factory() as session:
        for payload in DEFAULT_PREDICATES:
            if session.get(PredicateDefinition, payload["id"]) is None:
                session.add(PredicateDefinition(**payload, metadata_json={"seed":"platform-core-v2.1.0"}))
                created += 1
        session.commit()
    return created

def _seed_api_plans(database: Database) -> int:
    created = 0
    with database.session_factory() as session:
        for payload in DEFAULT_API_PLANS:
            existing = session.get(ApiPlan, payload["id"])
            if existing is None:
                data = dict(payload)
                metadata = data.pop("metadata", {})
                session.add(ApiPlan(**data, metadata_json=metadata))
                created += 1
            else:
                existing.allowed_scopes = sorted(
                    set(existing.allowed_scopes or [])
                    | set(payload.get("allowed_scopes", []))
                )
                session.add(existing)
        session.commit()
    return created


def _seed_evaluation_definitions(database: Database) -> int:
    created = 0
    with database.session_factory() as session:
        for payload in DEFAULT_EVALUATION_DEFINITIONS:
            if session.get(EvaluationDefinition, payload["id"]) is None:
                data = dict(payload)
                metadata = data.pop("metadata", {})
                session.add(EvaluationDefinition(**data, metadata_json=metadata))
                created += 1
        session.commit()
    return created

def _seed_workflow_definitions(database: Database) -> int:
    created = 0
    with database.session_factory() as session:
        for payload in DEFAULT_WORKFLOW_DEFINITIONS:
            existing = session.get(WorkflowDefinition, payload["id"])
            if existing is None:
                data = dict(payload)
                metadata = data.pop("metadata", {})
                session.add(WorkflowDefinition(**data, metadata_json=metadata))
                created += 1
            else:
                existing.stages = payload["stages"]
                existing.version = payload.get("version", existing.version)
                existing.active = payload.get("active", existing.active)
                existing.public = payload.get("public", existing.public)
                session.add(existing)
        session.commit()
    return created



def _seed_live_data_registry(database: Database) -> tuple[int, int]:
    sources_created = 0
    connectors_created = 0
    with database.session_factory() as session:
        for payload in DEFAULT_LIVE_DATA_SOURCES:
            existing = session.get(LiveDataSource, payload["id"])
            data = dict(payload)
            metadata = data.pop("metadata", {})
            if existing is None:
                session.add(LiveDataSource(**data, metadata_json=metadata))
                sources_created += 1
        session.flush()
        for payload in DEFAULT_LIVE_DATA_CONNECTORS:
            existing = session.get(LiveDataConnector, payload["id"])
            data = dict(payload)
            configuration = data.pop("configuration", {})
            if existing is None:
                session.add(LiveDataConnector(**data, configuration_json=configuration))
                connectors_created += 1
        session.commit()
    return sources_created, connectors_created


def _configure_postgresql_fabric(database: Database) -> dict[str, bool]:
    result = {"postgis_extension": False, "spatial_index": False, "time_series_brin": False}
    enabled = os.getenv("SC_CORE_DATA_FABRIC_POSTGIS_AUTO_ENABLE", "true").strip().lower() in {"1", "true", "yes", "on"}
    if database.engine.dialect.name != "postgresql" or not enabled:
        return result

    def execute(statement: str) -> bool:
        try:
            with database.engine.connect().execution_options(isolation_level="AUTOCOMMIT") as connection:
                connection.execute(text(statement))
            return True
        except Exception:
            return False

    result["postgis_extension"] = execute("CREATE EXTENSION IF NOT EXISTS postgis")
    if result["postgis_extension"]:
        result["spatial_index"] = execute(
            "CREATE INDEX IF NOT EXISTS ix_geospatial_features_geom_gist "
            "ON geospatial_features USING GIST "
            "(ST_SetSRID(ST_GeomFromGeoJSON(geometry_json::text), srid))"
        )
    result["time_series_brin"] = execute(
        "CREATE INDEX IF NOT EXISTS ix_time_series_points_observed_brin "
        "ON time_series_points USING BRIN (observed_at)"
    )
    return result


def _seed_observability_slos(database: Database) -> int:
    created=0
    defaults=[
        {"service":"platform-core","name":"Core availability","indicator":"availability_percent","target":99.0,"comparison":">=","window_minutes":60,"minimum_samples":5,"metadata_json":{"seed":"platform-core-v2.18.0"}},
        {"service":"platform-core","name":"Core p95 latency","indicator":"latency_p95_ms","target":1000.0,"comparison":"<=","window_minutes":60,"minimum_samples":5,"metadata_json":{"seed":"platform-core-v2.18.0"}},
    ]
    with database.session_factory() as session:
        for payload in defaults:
            existing=session.scalar(select(ServiceLevelObjective).where(ServiceLevelObjective.service==payload["service"],ServiceLevelObjective.name==payload["name"]))
            if existing is None:
                session.add(ServiceLevelObjective(**payload)); created+=1
        session.commit()
    return created


def _seed_analytical_runtime_providers(database: Database) -> tuple[int, int]:
    from .models import AnalyticalRuntimeProviderRecord, AnalyticalCapabilityRecord
    providers_created = 0
    capabilities_created = 0
    with database.session_factory() as session:
        provider = session.scalar(select(AnalyticalRuntimeProviderRecord).where(AnalyticalRuntimeProviderRecord.provider_key == "catalystanalyticsr"))
        if provider is None:
            provider = AnalyticalRuntimeProviderRecord(
                provider_key="catalystanalyticsr",
                name="Catalyst Analytics R",
                provider_version="2.2.0",
                runtime="r",
                execution_host="workspace",
                status="active",
                contract_ref="sc.core.analytical-runtime-provider.v1",
                transport_mode="hosted",
                invocation_mode="workspace-managed",
                visibility="public",
                metadata_json={
                    "package":"catalystanalyticsr",
                    "core_release":"3.3.0",
                    "workspace_adapter_release":"3.9.1",
                    "workspace_is_execution_host": True,
                    "core_executes_provider": False,
                    "transport_server_required_in_provider": False,
                    "diagnostics_contract":"sc.analytics-r.statistical-diagnostics-validation.v1"
                },
            )
            session.add(provider); session.flush(); providers_created += 1
        else:
            provider.provider_version = "2.2.0"
            provider.runtime = "r"
            provider.execution_host = "workspace"
            provider.contract_ref = "sc.core.analytical-runtime-provider.v1"
            provider.metadata_json = {**(provider.metadata_json or {}), "package":"catalystanalyticsr", "core_release":"3.3.0", "workspace_adapter_release":"3.9.1", "workspace_is_execution_host":True, "core_executes_provider":False, "transport_server_required_in_provider":False, "diagnostics_contract":"sc.analytics-r.statistical-diagnostics-validation.v1"}
        capabilities = [
            ("scenario_simulation","simulation",["run_catalyst_scenario","run_scenarios"],"active"),
            ("uncertainty_analysis","uncertainty",["run_uncertainty","uncertainty_summary","uncertainty_probabilities"],"active"),
            ("sensitivity_analysis","uncertainty",["local_sensitivity","global_sensitivity","sensitivity_jacobian"],"active"),
            ("econometrics","statistics",["fit_policy_regression","panel_regression"],"active"),
            ("causal_inference","causal",["difference_in_differences","event_study","interrupted_time_series","synthetic_control"],"active"),
            ("policy_evaluation","policy",["policy_evaluation_analysis","policy_effect_summary"],"active"),
            ("forecasting","predictive",["scenario_projection"],"projection_only"),
            ("model_validation","validation",["validate_model_fit","model_validation_analysis","solver_benchmark","stability_assessment"],"active"),
            ("climate_accounting","sustainability",["climate_accounting"],"active"),
            ("natural_capital","sustainability",["natural_capital_account"],"active"),
            ("inclusive_wealth","sustainability",["inclusive_wealth_account"],"active"),
            ("distribution_analysis","statistics",["distributional_analysis","intergenerational_analysis"],"active")
        ]
        for key, category, method_refs, provider_status in capabilities:
            existing = session.scalar(select(AnalyticalCapabilityRecord).where(AnalyticalCapabilityRecord.provider_id == provider.id, AnalyticalCapabilityRecord.capability_key == key))
            meta={"provider":"catalystanalyticsr","provider_version":"2.2.0","provider_capability_status":provider_status}
            if existing is None:
                session.add(AnalyticalCapabilityRecord(provider_id=provider.id, capability_key=key, category=category, method_refs_json=method_refs, input_types_json=["dataset","model","parameter_set"], output_types_json=["analytical_result"], status="active", visibility="public", metadata_json=meta))
                capabilities_created += 1
            else:
                existing.method_refs_json=method_refs
                existing.metadata_json={**(existing.metadata_json or {}), **meta}
        session.commit()
    return providers_created, capabilities_created

def run_migrations(database: Database) -> list[str]:
    Base.metadata.create_all(database.engine)
    applied: list[str] = []
    with database.session_factory() as session:
        for version, description in MIGRATIONS:
            if session.get(SchemaMigration, version) is None:
                session.add(SchemaMigration(version=version, description=description))
                session.commit()
                applied.append(version)
    _seed_predicates(database)
    _seed_api_plans(database)
    _seed_evaluation_definitions(database)
    _seed_workflow_definitions(database)
    _seed_live_data_registry(database)
    _configure_postgresql_fabric(database)
    _seed_observability_slos(database)
    _seed_scientific_object_fabric(database)
    _seed_renderer_registry(database)
    _seed_analytical_runtime_providers(database)
    return applied

def migration_status(database: Database) -> dict:
    Base.metadata.create_all(database.engine)
    with database.session_factory() as session:
        applied = {row.version for row in session.scalars(select(SchemaMigration)).all()}
        predicates = len(session.scalars(select(PredicateDefinition.id)).all())
        api_plans = len(session.scalars(select(ApiPlan.id)).all())
        evaluation_definitions = len(session.scalars(select(EvaluationDefinition.id)).all())
        workflow_definitions = len(session.scalars(select(WorkflowDefinition.id)).all())
        live_data_sources = len(session.scalars(select(LiveDataSource.id)).all())
        live_data_connectors = len(session.scalars(select(LiveDataConnector.id)).all())
        scientific_storage_backends = len(session.scalars(select(ScientificStorageBackend.id)).all())
        scientific_processing_adapters = len(session.scalars(select(ScientificProcessingAdapter.id)).all())
        research_projects = len(session.scalars(select(ResearchProjectRecord.entity_id)).all())
        research_models = len(session.scalars(select(ResearchModelRecord.entity_id)).all())
        research_model_versions = len(session.scalars(select(ResearchModelVersionRecord.entity_id)).all())
        research_variables = len(session.scalars(select(ResearchVariableRecord.entity_id)).all())
        research_parameters = len(session.scalars(select(ResearchParameterRecord.entity_id)).all())
        research_scenarios = len(session.scalars(select(ResearchScenarioRecord.entity_id)).all())
        research_model_runs = len(session.scalars(select(ResearchModelRunRecord.entity_id)).all())
        research_results = len(session.scalars(select(ResearchResultRecord.entity_id)).all())
        visual_reasoning_objects = len(session.scalars(select(VisualReasoningObjectRecord.entity_id)).all())
        visual_reasoning_elements = len(session.scalars(select(VisualReasoningElementRecord.id)).all())
        visual_reasoning_relations = len(session.scalars(select(VisualReasoningRelationRecord.id)).all())
        visual_reasoning_layers = len(session.scalars(select(VisualReasoningLayerRecord.id)).all())
        visual_reasoning_annotations = len(session.scalars(select(VisualReasoningAnnotationRecord.id)).all())
        visual_reasoning_snapshots = len(session.scalars(select(VisualReasoningSnapshotRecord.id)).all())
        visualization_specifications = len(session.scalars(select(VisualizationSpecificationRecord.id)).all())
        renderer_definitions = len(session.scalars(select(RendererDefinitionRecord.renderer_key)).all())
        renderer_versions = len(session.scalars(select(RendererVersionRecord.id)).all())
        renderer_compatibility_rules = len(session.scalars(select(RendererCompatibilityRuleRecord.id)).all())
        renderer_resolutions = len(session.scalars(select(RendererResolutionRecord.id)).all())
        system_maps = len(session.scalars(select(SystemMapRecord.visual_entity_id)).all())
        system_map_boundaries = len(session.scalars(select(SystemMapBoundaryRecord.id)).all())
        system_map_domains = len(session.scalars(select(SystemMapDomainRecord.id)).all())
        system_map_memberships = len(session.scalars(select(SystemMapMembershipRecord.id)).all())
        system_map_views = len(session.scalars(select(SystemMapViewRecord.id)).all())
        flow_maps = len(session.scalars(select(FlowMapRecord.visual_entity_id)).all())
        flow_map_channels = len(session.scalars(select(FlowMapChannelRecord.id)).all())
        flow_map_flows = len(session.scalars(select(FlowMapFlowRecord.id)).all())
        flow_map_node_states = len(session.scalars(select(FlowMapNodeStateRecord.id)).all())
        flow_map_views = len(session.scalars(select(FlowMapViewRecord.id)).all())
        scenario_landscapes = len(session.scalars(select(ScenarioLandscapeRecord.visual_entity_id)).all())
        scenario_landscape_scenarios = len(session.scalars(select(ScenarioLandscapeScenarioRecord.id)).all())
        scenario_landscape_dimensions = len(session.scalars(select(ScenarioLandscapeDimensionRecord.id)).all())
        scenario_landscape_values = len(session.scalars(select(ScenarioLandscapeValueRecord.id)).all())
        scenario_landscape_views = len(session.scalars(select(ScenarioLandscapeViewRecord.id)).all())
        model_canvases = len(session.scalars(select(ModelCanvasRecord.visual_entity_id)).all())
        model_canvas_nodes = len(session.scalars(select(ModelCanvasNodeRecord.id)).all())
        model_canvas_edges = len(session.scalars(select(ModelCanvasEdgeRecord.id)).all())
        model_canvas_controls = len(session.scalars(select(ModelCanvasControlRecord.id)).all())
        model_canvas_states = len(session.scalars(select(ModelCanvasStateRecord.id)).all())
        model_canvas_views = len(session.scalars(select(ModelCanvasViewRecord.id)).all())
        scenario_compute_plans = len(session.scalars(select(ScenarioComputePlanRecord.id)).all())
        scenario_compute_cases = len(session.scalars(select(ScenarioComputeCaseRecord.id)).all())
        scenario_compute_requests = len(session.scalars(select(ScenarioComputeRequestRecord.id)).all())
        scenario_compute_attempts = len(session.scalars(select(ScenarioComputeAttemptRecord.id)).all())
        scenario_compute_result_bindings = len(session.scalars(select(ScenarioComputeResultBindingRecord.id)).all())
        uncertainty_definitions = len(session.scalars(select(UncertaintyDefinitionRecord.id)).all())
        sensitivity_studies = len(session.scalars(select(SensitivityStudyRecord.id)).all())
        sensitivity_factors = len(session.scalars(select(SensitivityFactorRecord.id)).all())
        sensitivity_measures = len(session.scalars(select(SensitivityMeasureRecord.id)).all())
        ensembles = len(session.scalars(select(EnsembleRecord.id)).all())
        ensemble_members = len(session.scalars(select(EnsembleMemberRecord.id)).all())
        ensemble_statistics = len(session.scalars(select(EnsembleStatisticRecord.id)).all())
        uncertainty_compute_runs = len(session.scalars(select(UncertaintyComputeRunRecord.id)).all())
        causal_graphs = len(session.scalars(select(CausalGraphRecord.id)).all())
        causal_variables = len(session.scalars(select(CausalVariableRecord.id)).all())
        causal_edges = len(session.scalars(select(CausalEdgeRecord.id)).all())
        causal_interventions = len(session.scalars(select(CausalInterventionRecord.id)).all())
        causal_identifications = len(session.scalars(select(CausalIdentificationRecord.id)).all())
        causal_estimates = len(session.scalars(select(CausalEstimateRecord.id)).all())
        causal_diagnostics = len(session.scalars(select(CausalDiagnosticRecord.id)).all())
        spatial_temporal_scenes = len(session.scalars(select(SpatialTemporalSceneRecord.id)).all())
        spatial_temporal_features = len(session.scalars(select(SpatialFeatureRecord.id)).all())
        spatial_temporal_events = len(session.scalars(select(TemporalEventRecord.id)).all())
        spatial_temporal_trajectories = len(session.scalars(select(TrajectoryRecord.id)).all())
        spatial_temporal_trajectory_points = len(session.scalars(select(TrajectoryPointRecord.id)).all())
        spatial_temporal_changes = len(session.scalars(select(SpatialTemporalChangeRecord.id)).all())
        spatial_temporal_views = len(session.scalars(select(SpatialTemporalViewRecord.id)).all())
        research_visual_explanations = len(session.scalars(select(ResearchVisualExplanationRecord.id)).all())
        research_explanation_nodes = len(session.scalars(select(ResearchExplanationNodeRecord.id)).all())
        research_explanation_relations = len(session.scalars(select(ResearchExplanationRelationRecord.id)).all())
        research_explanation_citations = len(session.scalars(select(ResearchExplanationCitationRecord.id)).all())
        research_explanation_views = len(session.scalars(select(ResearchExplanationViewRecord.id)).all())
        research_explanation_snapshots = len(session.scalars(select(ResearchExplanationSnapshotRecord.id)).all())
        cross_product_visual_research_objects = len(session.scalars(select(CrossProductVisualResearchObjectRecord.id)).all())
        cross_product_visual_research_members = len(session.scalars(select(CrossProductVisualResearchMemberRecord.id)).all())
        cross_product_visual_research_relations = len(session.scalars(select(CrossProductVisualResearchRelationRecord.id)).all())
        cross_product_visual_research_views = len(session.scalars(select(CrossProductVisualResearchViewRecord.id)).all())
        cross_product_visual_research_snapshots = len(session.scalars(select(CrossProductVisualResearchSnapshotRecord.id)).all())
        reproducible_visual_knowledge_packages = len(session.scalars(select(ReproducibleVisualKnowledgePackageRecord.id)).all())
        reproducible_visual_knowledge_inputs = len(session.scalars(select(ReproducibleVisualKnowledgeInputRecord.id)).all())
        reproducible_visual_knowledge_environments = len(session.scalars(select(ReproducibleVisualKnowledgeEnvironmentRecord.id)).all())
        reproducible_visual_knowledge_replay_plans = len(session.scalars(select(ReproducibleVisualKnowledgeReplayPlanRecord.id)).all())
        reproducible_visual_knowledge_verifications = len(session.scalars(select(ReproducibleVisualKnowledgeVerificationRecord.id)).all())
        reproducible_visual_knowledge_snapshots = len(session.scalars(select(ReproducibleVisualKnowledgeSnapshotRecord.id)).all())
        forensic_investigations = len(session.scalars(select(ForensicInvestigationRecord.id)).all())
        forensic_objects = len(session.scalars(select(ForensicObjectRecord.id)).all())
        forensic_evidence_items = len(session.scalars(select(ForensicEvidenceItemRecord.id)).all())
        forensic_evidence_source_bindings = len(session.scalars(select(ForensicEvidenceSourceBindingRecord.id)).all())
        forensic_provenance_activities = len(session.scalars(select(ForensicProvenanceActivityRecord.id)).all())
        forensic_object_relations = len(session.scalars(select(ForensicObjectRelationRecord.id)).all())
        forensic_snapshots = len(session.scalars(select(ForensicSnapshotRecord.id)).all())
        forensic_custodians = len(session.scalars(select(ForensicCustodianRecord.id)).all())
        forensic_custody_events = len(session.scalars(select(ForensicCustodyEventRecord.id)).all())
        forensic_evidence_seals = len(session.scalars(select(ForensicEvidenceSealRecord.id)).all())
        forensic_integrity_checks = len(session.scalars(select(ForensicIntegrityCheckRecord.id)).all())
        forensic_custody_continuity_assessments = len(session.scalars(select(ForensicCustodyContinuityAssessmentRecord.id)).all())
        forensic_custody_snapshots = len(session.scalars(select(ForensicCustodySnapshotRecord.id)).all())
        forensic_claims = len(session.scalars(select(ForensicClaimRecord.id)).all())
        forensic_claim_evidence_assessments = len(session.scalars(select(ForensicClaimEvidenceAssessmentRecord.id)).all())
        forensic_contradictions = len(session.scalars(select(ForensicContradictionRecord.id)).all())
        forensic_hypotheses = len(session.scalars(select(ForensicHypothesisRecord.id)).all())
        forensic_hypothesis_evidence_assessments = len(session.scalars(select(ForensicHypothesisEvidenceAssessmentRecord.id)).all())
        forensic_hypothesis_relations = len(session.scalars(select(ForensicHypothesisRelationRecord.id)).all())
        forensic_reasoning_snapshots = len(session.scalars(select(ForensicReasoningSnapshotRecord.id)).all())
        forensic_events = len(session.scalars(select(ForensicEventRecord.id)).all())
        forensic_event_evidence_bindings = len(session.scalars(select(ForensicEventEvidenceBindingRecord.id)).all())
        forensic_event_participants = len(session.scalars(select(ForensicEventParticipantRecord.id)).all())
        forensic_event_relations = len(session.scalars(select(ForensicEventRelationRecord.id)).all())
        forensic_event_reconstructions = len(session.scalars(select(ForensicEventReconstructionRecord.id)).all())
        forensic_timeline_views = len(session.scalars(select(ForensicTimelineViewRecord.id)).all())
        forensic_timeline_snapshots = len(session.scalars(select(ForensicTimelineSnapshotRecord.id)).all())
        forensic_places = len(session.scalars(select(ForensicPlaceRecord.id)).all())
        forensic_evidence_spatial_bindings = len(session.scalars(select(ForensicEvidenceSpatialBindingRecord.id)).all())
        forensic_event_place_bindings = len(session.scalars(select(ForensicEventPlaceBindingRecord.id)).all())
        forensic_spatial_uncertainty_envelopes = len(session.scalars(select(ForensicSpatialUncertaintyEnvelopeRecord.id)).all())
        forensic_trajectory_evidence = len(session.scalars(select(ForensicTrajectoryEvidenceRecord.id)).all())
        forensic_spatial_temporal_intersections = len(session.scalars(select(ForensicSpatialTemporalIntersectionRecord.id)).all())
        forensic_spatial_temporal_views = len(session.scalars(select(ForensicSpatialTemporalViewRecord.id)).all())
        forensic_spatial_temporal_snapshots = len(session.scalars(select(ForensicSpatialTemporalSnapshotRecord.id)).all())
        forensic_media_artifacts = len(session.scalars(select(ForensicMediaArtifactRecord.id)).all())
        forensic_media_derivations = len(session.scalars(select(ForensicMediaDerivativeRecord.id)).all())
        forensic_media_metadata_records = len(session.scalars(select(ForensicMediaMetadataRecord.id)).all())
        forensic_media_fingerprints = len(session.scalars(select(ForensicMediaFingerprintRecord.id)).all())
        forensic_media_segments = len(session.scalars(select(ForensicMediaSegmentRecord.id)).all())
        forensic_media_comparisons = len(session.scalars(select(ForensicMediaComparisonRecord.id)).all())
        forensic_media_provenance_snapshots = len(session.scalars(select(ForensicMediaProvenanceSnapshotRecord.id)).all())
        forensic_quantitative_reconstructions = len(session.scalars(select(ForensicQuantitativeReconstructionRecord.id)).all())
        forensic_quantitative_measurements = len(session.scalars(select(ForensicQuantitativeMeasurementRecord.id)).all())
        forensic_quantitative_assumptions = len(session.scalars(select(ForensicQuantitativeAssumptionRecord.id)).all())
        forensic_quantitative_parameters = len(session.scalars(select(ForensicQuantitativeParameterRecord.id)).all())
        forensic_quantitative_scenarios = len(session.scalars(select(ForensicQuantitativeScenarioRecord.id)).all())
        forensic_quantitative_handoffs = len(session.scalars(select(ForensicQuantitativeHandoffRecord.id)).all())
        forensic_quantitative_result_bindings = len(session.scalars(select(ForensicQuantitativeResultBindingRecord.id)).all())
        forensic_quantitative_reproduction_packages = len(session.scalars(select(ForensicQuantitativeReproductionPackageRecord.id)).all())
        forensic_statements = len(session.scalars(select(ForensicStatementRecord.id)).all())
        forensic_statement_source_contexts = len(session.scalars(select(ForensicStatementSourceContextRecord.id)).all())
        forensic_documents = len(session.scalars(select(ForensicDocumentRecord.id)).all())
        forensic_document_assertions = len(session.scalars(select(ForensicDocumentAssertionRecord.id)).all())
        forensic_statement_claim_bindings = len(session.scalars(select(ForensicStatementClaimBindingRecord.id)).all())
        forensic_statement_relations = len(session.scalars(select(ForensicStatementRelationRecord.id)).all())
        forensic_temporal_consistency_assessments = len(session.scalars(select(ForensicTemporalConsistencyRecord.id)).all())
        forensic_documentary_snapshots = len(session.scalars(select(ForensicDocumentarySnapshotRecord.id)).all())
        forensic_research_graphs = len(session.scalars(select(ForensicResearchGraphRecord.id)).all())
        forensic_research_graph_nodes = len(session.scalars(select(ForensicResearchGraphNodeRecord.id)).all())
        forensic_research_graph_edges = len(session.scalars(select(ForensicResearchGraphEdgeRecord.id)).all())
        forensic_research_graph_views = len(session.scalars(select(ForensicResearchGraphViewRecord.id)).all())
        forensic_research_graph_handoffs = len(session.scalars(select(ForensicResearchGraphHandoffRecord.id)).all())
        forensic_research_graph_snapshots = len(session.scalars(select(ForensicResearchGraphSnapshotRecord.id)).all())
        forensic_research_graph_packages = len(session.scalars(select(ForensicResearchGraphPackageRecord.id)).all())
        forensic_investigation_packages = len(session.scalars(select(ForensicInvestigationPackageRecord.id)).all())
        forensic_investigation_package_components = len(session.scalars(select(ForensicInvestigationPackageComponentRecord.id)).all())
        forensic_investigation_package_artifacts = len(session.scalars(select(ForensicInvestigationPackageArtifactRecord.id)).all())
        forensic_investigation_package_environments = len(session.scalars(select(ForensicInvestigationPackageEnvironmentRecord.id)).all())
        forensic_investigation_package_verifications = len(session.scalars(select(ForensicInvestigationPackageVerificationRecord.id)).all())
        forensic_investigation_package_reviews = len(session.scalars(select(ForensicInvestigationPackageReviewRecord.id)).all())
        forensic_investigation_package_snapshots = len(session.scalars(select(ForensicInvestigationPackageSnapshotRecord.id)).all())
        predictive_models = len(session.scalars(select(PredictiveModelRecord.id)).all())
        predictive_targets = len(session.scalars(select(PredictiveTargetRecord.id)).all())
        predictive_features = len(session.scalars(select(PredictiveFeatureRecord.id)).all())
        predictive_training_windows = len(session.scalars(select(PredictiveTrainingWindowRecord.id)).all())
        predictive_forecast_runs = len(session.scalars(select(PredictiveForecastRunRecord.id)).all())
        predictive_forecast_observations = len(session.scalars(select(PredictiveForecastObservationRecord.id)).all())
        predictive_evaluations = len(session.scalars(select(PredictiveEvaluationRecord.id)).all())
        predictive_runtime_handoffs = len(session.scalars(select(PredictiveRuntimeHandoffRecord.id)).all())
        predictive_forecast_snapshots = len(session.scalars(select(PredictiveForecastSnapshotRecord.id)).all())
        predictive_time_series_datasets = len(session.scalars(select(PredictiveTimeSeriesDatasetRecord.id)).all())
        predictive_forecast_windows = len(session.scalars(select(PredictiveForecastWindowRecord.id)).all())
        predictive_baseline_models = len(session.scalars(select(PredictiveBaselineModelRecord.id)).all())
        predictive_backtest_plans = len(session.scalars(select(PredictiveBacktestPlanRecord.id)).all())
        predictive_backtest_folds = len(session.scalars(select(PredictiveBacktestFoldRecord.id)).all())
        predictive_backtest_observations = len(session.scalars(select(PredictiveBacktestObservationRecord.id)).all())
        predictive_backtest_evaluations = len(session.scalars(select(PredictiveBacktestEvaluationRecord.id)).all())
        predictive_backtest_packages = len(session.scalars(select(PredictiveBacktestPackageRecord.id)).all())
        predictive_probabilistic_forecasts = len(session.scalars(select(PredictiveProbabilisticForecastRecord.id)).all())
        predictive_calibration_studies = len(session.scalars(select(PredictiveCalibrationStudyRecord.id)).all())
        predictive_calibration_bins = len(session.scalars(select(PredictiveCalibrationBinRecord.id)).all())
        predictive_calibration_mappings = len(session.scalars(select(PredictiveCalibrationMappingRecord.id)).all())
        predictive_probabilistic_evaluations = len(session.scalars(select(PredictiveProbabilisticEvaluationRecord.id)).all())
        predictive_calibration_packages = len(session.scalars(select(PredictiveCalibrationPackageRecord.id)).all())
        predictive_ensembles = len(session.scalars(select(PredictiveEnsembleRecord.id)).all())
        predictive_ensemble_members = len(session.scalars(select(PredictiveEnsembleMemberRecord.id)).all())
        predictive_ensemble_forecasts = len(session.scalars(select(PredictiveEnsembleForecastRecord.id)).all())
        predictive_comparison_studies = len(session.scalars(select(PredictiveComparisonStudyRecord.id)).all())
        predictive_comparison_candidates = len(session.scalars(select(PredictiveComparisonCandidateRecord.id)).all())
        predictive_comparison_evidence = len(session.scalars(select(PredictiveComparisonEvidenceRecord.id)).all())
        predictive_pairwise_comparisons = len(session.scalars(select(PredictivePairwiseComparisonRecord.id)).all())
        predictive_comparison_packages = len(session.scalars(select(PredictiveComparisonPackageRecord.id)).all())
        predictive_monitoring_studies = len(session.scalars(select(PredictiveMonitoringStudyRecord.id)).all())
        predictive_detection_rules = len(session.scalars(select(PredictiveDetectionRuleRecord.id)).all())
        predictive_anomaly_observations = len(session.scalars(select(PredictiveAnomalyObservationRecord.id)).all())
        predictive_change_points = len(session.scalars(select(PredictiveChangePointRecord.id)).all())
        predictive_early_warning_signals = len(session.scalars(select(PredictiveEarlyWarningSignalRecord.id)).all())
        predictive_monitoring_episodes = len(session.scalars(select(PredictiveMonitoringEpisodeRecord.id)).all())
        predictive_monitoring_packages = len(session.scalars(select(PredictiveMonitoringPackageRecord.id)).all())
        predictive_spatial_temporal_studies = len(session.scalars(select(PredictiveSpatialTemporalStudyRecord.id)).all())
        predictive_spatial_units = len(session.scalars(select(PredictiveSpatialUnitRecord.id)).all())
        predictive_spatial_temporal_forecasts = len(session.scalars(select(PredictiveSpatialTemporalForecastRecord.id)).all())
        predictive_spatial_temporal_observations = len(session.scalars(select(PredictiveSpatialTemporalObservationRecord.id)).all())
        predictive_spatial_propagation_evidence = len(session.scalars(select(PredictiveSpatialPropagationEvidenceRecord.id)).all())
        predictive_spatial_hotspot_evidence = len(session.scalars(select(PredictiveSpatialHotspotEvidenceRecord.id)).all())
        predictive_spatial_temporal_evaluations = len(session.scalars(select(PredictiveSpatialTemporalEvaluationRecord.id)).all())
        predictive_spatial_temporal_packages = len(session.scalars(select(PredictiveSpatialTemporalPackageRecord.id)).all())
    expected = {version for version, _ in MIGRATIONS}
    return {"expected":sorted(expected),"applied":sorted(applied),"pending":sorted(expected-applied),"predicate_definitions":predicates,"api_plans":api_plans,"evaluation_definitions":evaluation_definitions,"workflow_definitions":workflow_definitions,"live_data_sources":live_data_sources,"live_data_connectors":live_data_connectors,"scientific_storage_backends":scientific_storage_backends,"scientific_processing_adapters":scientific_processing_adapters,"research_projects":research_projects,"research_models":research_models,"research_model_versions":research_model_versions,"research_variables":research_variables,"research_parameters":research_parameters,"research_scenarios":research_scenarios,"research_model_runs":research_model_runs,"research_results":research_results,"visual_reasoning_objects":visual_reasoning_objects,"visual_reasoning_elements":visual_reasoning_elements,"visual_reasoning_relations":visual_reasoning_relations,"visual_reasoning_layers":visual_reasoning_layers,"visual_reasoning_annotations":visual_reasoning_annotations,"visual_reasoning_snapshots":visual_reasoning_snapshots,"visualization_specifications":visualization_specifications,"renderer_definitions":renderer_definitions,"renderer_versions":renderer_versions,"renderer_compatibility_rules":renderer_compatibility_rules,"renderer_resolutions":renderer_resolutions,"system_maps":system_maps,"system_map_boundaries":system_map_boundaries,"system_map_domains":system_map_domains,"system_map_memberships":system_map_memberships,"system_map_views":system_map_views,"flow_maps":flow_maps,"flow_map_channels":flow_map_channels,"flow_map_flows":flow_map_flows,"flow_map_node_states":flow_map_node_states,"flow_map_views":flow_map_views,"scenario_landscapes":scenario_landscapes,"scenario_landscape_scenarios":scenario_landscape_scenarios,"scenario_landscape_dimensions":scenario_landscape_dimensions,"scenario_landscape_values":scenario_landscape_values,"scenario_landscape_views":scenario_landscape_views,"model_canvases":model_canvases,"model_canvas_nodes":model_canvas_nodes,"model_canvas_edges":model_canvas_edges,"model_canvas_controls":model_canvas_controls,"model_canvas_states":model_canvas_states,"model_canvas_views":model_canvas_views,"scenario_compute_plans":scenario_compute_plans,"scenario_compute_cases":scenario_compute_cases,"scenario_compute_requests":scenario_compute_requests,"scenario_compute_attempts":scenario_compute_attempts,"scenario_compute_result_bindings":scenario_compute_result_bindings,"uncertainty_definitions":uncertainty_definitions,"sensitivity_studies":sensitivity_studies,"sensitivity_factors":sensitivity_factors,"sensitivity_measures":sensitivity_measures,"ensembles":ensembles,"ensemble_members":ensemble_members,"ensemble_statistics":ensemble_statistics,"uncertainty_compute_runs":uncertainty_compute_runs,"causal_graphs":causal_graphs,"causal_variables":causal_variables,"causal_edges":causal_edges,"causal_interventions":causal_interventions,"causal_identifications":causal_identifications,"causal_estimates":causal_estimates,"causal_diagnostics":causal_diagnostics,"spatial_temporal_scenes":spatial_temporal_scenes,"spatial_temporal_features":spatial_temporal_features,"spatial_temporal_events":spatial_temporal_events,"spatial_temporal_trajectories":spatial_temporal_trajectories,"spatial_temporal_trajectory_points":spatial_temporal_trajectory_points,"spatial_temporal_changes":spatial_temporal_changes,"spatial_temporal_views":spatial_temporal_views,"research_visual_explanations":research_visual_explanations,"research_explanation_nodes":research_explanation_nodes,"research_explanation_relations":research_explanation_relations,"research_explanation_citations":research_explanation_citations,"research_explanation_views":research_explanation_views,"research_explanation_snapshots":research_explanation_snapshots,"cross_product_visual_research_objects":cross_product_visual_research_objects,"cross_product_visual_research_members":cross_product_visual_research_members,"cross_product_visual_research_relations":cross_product_visual_research_relations,"cross_product_visual_research_views":cross_product_visual_research_views,"cross_product_visual_research_snapshots":cross_product_visual_research_snapshots,"reproducible_visual_knowledge_packages":reproducible_visual_knowledge_packages,"reproducible_visual_knowledge_inputs":reproducible_visual_knowledge_inputs,"reproducible_visual_knowledge_environments":reproducible_visual_knowledge_environments,"reproducible_visual_knowledge_replay_plans":reproducible_visual_knowledge_replay_plans,"reproducible_visual_knowledge_verifications":reproducible_visual_knowledge_verifications,"reproducible_visual_knowledge_snapshots":reproducible_visual_knowledge_snapshots,"forensic_investigations":forensic_investigations,"forensic_objects":forensic_objects,"forensic_evidence_items":forensic_evidence_items,"forensic_evidence_source_bindings":forensic_evidence_source_bindings,"forensic_provenance_activities":forensic_provenance_activities,"forensic_object_relations":forensic_object_relations,"forensic_snapshots":forensic_snapshots,"forensic_custodians":forensic_custodians,"forensic_custody_events":forensic_custody_events,"forensic_evidence_seals":forensic_evidence_seals,"forensic_integrity_checks":forensic_integrity_checks,"forensic_custody_continuity_assessments":forensic_custody_continuity_assessments,"forensic_custody_snapshots":forensic_custody_snapshots,"forensic_claims":forensic_claims,"forensic_claim_evidence_assessments":forensic_claim_evidence_assessments,"forensic_contradictions":forensic_contradictions,"forensic_hypotheses":forensic_hypotheses,"forensic_hypothesis_evidence_assessments":forensic_hypothesis_evidence_assessments,"forensic_hypothesis_relations":forensic_hypothesis_relations,"forensic_reasoning_snapshots":forensic_reasoning_snapshots,"forensic_events":forensic_events,"forensic_event_evidence_bindings":forensic_event_evidence_bindings,"forensic_event_participants":forensic_event_participants,"forensic_event_relations":forensic_event_relations,"forensic_event_reconstructions":forensic_event_reconstructions,"forensic_timeline_views":forensic_timeline_views,"forensic_timeline_snapshots":forensic_timeline_snapshots,"forensic_places":forensic_places,"forensic_evidence_spatial_bindings":forensic_evidence_spatial_bindings,"forensic_event_place_bindings":forensic_event_place_bindings,"forensic_spatial_uncertainty_envelopes":forensic_spatial_uncertainty_envelopes,"forensic_trajectory_evidence":forensic_trajectory_evidence,"forensic_spatial_temporal_intersections":forensic_spatial_temporal_intersections,"forensic_spatial_temporal_views":forensic_spatial_temporal_views,"forensic_spatial_temporal_snapshots":forensic_spatial_temporal_snapshots,"forensic_media_artifacts":forensic_media_artifacts,"forensic_media_derivations":forensic_media_derivations,"forensic_media_metadata_records":forensic_media_metadata_records,"forensic_media_fingerprints":forensic_media_fingerprints,"forensic_media_segments":forensic_media_segments,"forensic_media_comparisons":forensic_media_comparisons,"forensic_media_provenance_snapshots":forensic_media_provenance_snapshots,"forensic_quantitative_reconstructions":forensic_quantitative_reconstructions,"forensic_quantitative_measurements":forensic_quantitative_measurements,"forensic_quantitative_assumptions":forensic_quantitative_assumptions,"forensic_quantitative_parameters":forensic_quantitative_parameters,"forensic_quantitative_scenarios":forensic_quantitative_scenarios,"forensic_quantitative_handoffs":forensic_quantitative_handoffs,"forensic_quantitative_result_bindings":forensic_quantitative_result_bindings,"forensic_quantitative_reproduction_packages":forensic_quantitative_reproduction_packages,"forensic_statements":forensic_statements,"forensic_statement_source_contexts":forensic_statement_source_contexts,"forensic_documents":forensic_documents,"forensic_document_assertions":forensic_document_assertions,"forensic_statement_claim_bindings":forensic_statement_claim_bindings,"forensic_statement_relations":forensic_statement_relations,"forensic_temporal_consistency_assessments":forensic_temporal_consistency_assessments,"forensic_documentary_snapshots":forensic_documentary_snapshots,"forensic_research_graphs":forensic_research_graphs,"forensic_research_graph_nodes":forensic_research_graph_nodes,"forensic_research_graph_edges":forensic_research_graph_edges,"forensic_research_graph_views":forensic_research_graph_views,"forensic_research_graph_handoffs":forensic_research_graph_handoffs,"forensic_research_graph_snapshots":forensic_research_graph_snapshots,"forensic_research_graph_packages":forensic_research_graph_packages,"forensic_investigation_packages":forensic_investigation_packages,"forensic_investigation_package_components":forensic_investigation_package_components,"forensic_investigation_package_artifacts":forensic_investigation_package_artifacts,"forensic_investigation_package_environments":forensic_investigation_package_environments,"forensic_investigation_package_verifications":forensic_investigation_package_verifications,"forensic_investigation_package_reviews":forensic_investigation_package_reviews,"forensic_investigation_package_snapshots":forensic_investigation_package_snapshots,"predictive_models":predictive_models,"predictive_targets":predictive_targets,"predictive_features":predictive_features,"predictive_training_windows":predictive_training_windows,"predictive_forecast_runs":predictive_forecast_runs,"predictive_forecast_observations":predictive_forecast_observations,"predictive_evaluations":predictive_evaluations,"predictive_runtime_handoffs":predictive_runtime_handoffs,"predictive_forecast_snapshots":predictive_forecast_snapshots,"predictive_time_series_datasets":predictive_time_series_datasets,"predictive_forecast_windows":predictive_forecast_windows,"predictive_baseline_models":predictive_baseline_models,"predictive_backtest_plans":predictive_backtest_plans,"predictive_backtest_folds":predictive_backtest_folds,"predictive_backtest_observations":predictive_backtest_observations,"predictive_backtest_evaluations":predictive_backtest_evaluations,"predictive_backtest_packages":predictive_backtest_packages,"predictive_probabilistic_forecasts":predictive_probabilistic_forecasts,"predictive_calibration_studies":predictive_calibration_studies,"predictive_calibration_bins":predictive_calibration_bins,"predictive_calibration_mappings":predictive_calibration_mappings,"predictive_probabilistic_evaluations":predictive_probabilistic_evaluations,"predictive_calibration_packages":predictive_calibration_packages,"predictive_ensembles":predictive_ensembles,"predictive_ensemble_members":predictive_ensemble_members,"predictive_ensemble_forecasts":predictive_ensemble_forecasts,"predictive_comparison_studies":predictive_comparison_studies,"predictive_comparison_candidates":predictive_comparison_candidates,"predictive_comparison_evidence":predictive_comparison_evidence,"predictive_pairwise_comparisons":predictive_pairwise_comparisons,"predictive_comparison_packages":predictive_comparison_packages,"predictive_monitoring_studies":predictive_monitoring_studies,"predictive_detection_rules":predictive_detection_rules,"predictive_anomaly_observations":predictive_anomaly_observations,"predictive_change_points":predictive_change_points,"predictive_early_warning_signals":predictive_early_warning_signals,"predictive_monitoring_episodes":predictive_monitoring_episodes,"predictive_monitoring_packages":predictive_monitoring_packages,"predictive_spatial_temporal_studies":predictive_spatial_temporal_studies,"predictive_spatial_units":predictive_spatial_units,"predictive_spatial_temporal_forecasts":predictive_spatial_temporal_forecasts,"predictive_spatial_temporal_observations":predictive_spatial_temporal_observations,"predictive_spatial_propagation_evidence":predictive_spatial_propagation_evidence,"predictive_spatial_hotspot_evidence":predictive_spatial_hotspot_evidence,"predictive_spatial_temporal_evaluations":predictive_spatial_temporal_evaluations,"predictive_spatial_temporal_packages":predictive_spatial_temporal_packages}
