import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import Settings
from .request_tracing import RequestTraceMiddleware
from .service_registry import GatewaySettings, ServiceRegistry
from .services.gateway import GatewayRuntime
from .services.live_data import LiveDataRuntime
from .database import Database
from .migrations import run_migrations
from .public_api_auth import PublicApiMiddleware
from .routers import (
    developer_admin,
    dossier_center,
    dossier_public_site,
    developer_portal,
    data_fabric,
    entities,
    economic_data,
    evidence,
    evidence_explorer,
    explorer,
    gateway,
    facilities,
    humanitarian,
    country_evidence,
    cross_product_exchange,
    scale,
    governance,
    certification,
    observability,
    operations,
    continuity,
    resilience,
    lifecycle,
    federation,
    capacity,
    credentials,
    workload_governance,
    foundations,
    imports,
    international_law,
    scientific_data,
    scientific_service_fabric,
    scientific_objects,
    research_objects,
    visual_reasoning,
    visual_runtime,
    visual_composition,
    visual_grammar,
    visual_linked_views,
    visual_query_exploration,
    visual_model_construction,
    visual_predictive_intelligence,
    visual_forensics_workbench,
    visual_decision_intelligence,
    unified_visual_reasoning,
    cross_product_visual_runtime_integration,
    unified_research_projects,
    research_lineage,
    visualization_registry,
    system_maps,
    flow_maps,
    scenario_landscapes,
    model_canvas,
    scenario_compute,
    uncertainty_reasoning,
    uncertainty_compute,
    causal_systems,
    spatial_temporal,
    research_visual_explanations,
    cross_product_visual_research,
    reproducible_visual_knowledge,
    open_forensics,
    predictive_intelligence,
    ledger,
    live_data,
    meta,
    predicates,
    public_api,
    relationships,
    reliability,
    trust_admin,
    trust_center,
    trust_public,
    workflow_public,
    workflows,
)


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or Settings.from_env()
    logging.basicConfig(level=getattr(logging, settings.log_level, logging.INFO))

    app = FastAPI(
        title=settings.app_name,
        version=settings.version,
        description=(
            "Universal Entity Registry, governed Knowledge Graph, Evidence Ledger, "
            "source snapshots, calculation traces, provenance records, review "
            "workflows, tamper-evident audit infrastructure, a unified public API, "
            "developer applications, scoped credentials, usage controls, webhooks, "
            "SDK assets, a public Trust Center, evaluation runs, incidents, "
            "limitations, attestations, signature dossiers, end-to-end workflows, a unified service gateway, and a governed free live-data connector gateway, an international-law and United Nations record layer, a scientific data connector and discovery layer, an economics and official-statistics record layer, a geospatial, time-series, STAC, map-layer, and scientific-asset fabric, a streaming, alerts, connector-worker, replay, stale-source, and provider-failover reliability plane, and a provenance-preserving operational facility and status-observation registry, and a humanitarian access and essential-services evidence fabric, plus a country evidence federation and reconciliation plane, and an Earth, Ocean, Space, and Scientific Service Fabric, plus a governed Cross-Product Evidence Exchange for Sustainable Catalyst, and a distributed processing, storage, backpressure, retention, and scale-control plane, plus a governance, access-decision, retention-policy, and tamper-evident audit control plane, and a production certification, migration-assurance, and recovery-readiness control plane, plus a first-party observability, service-level-objective, and production-operations control plane, and an incident-response, change-control, and operator-confirmed rollback-coordination plane, plus continuity, backup-verification, restore-rehearsal, and disaster-recovery objective controls, and multi-region resilience, replication-aware failover assessment, degraded-mode routing, and operator-coordinated recovery controls, plus governed data lifecycle, archival integrity, preservation manifests, policy/legal holds, tombstone lineage, and non-destructive restoration controls, and a Federated Core trusted-node exchange with authenticated reference-first manifests and conflict-safe remote-reference intake, plus capacity forecasting and resource governance with bounded forecasts, budgets, advisory soft limits, public-safe status, and non-actuating certification controls, and secret-free identity, credential, cryptographic-key version, rotation, revocation, and credential-use lifecycle governance, plus database-shared distributed quotas, workload classes, priority and fairness controls, SLO/capacity-aware admission, and auditable hard workload protection, plus governed scientific object storage, credential-free external references, derived-object lineage, and a provider-neutral processing adapter fabric, and a graph-native research object and model foundation spanning projects, models, immutable versions, variables, parameters, scenarios, model runs, and results, plus a governed scenario compute orchestration plane for reproducible external Lab/Workbench execution handoffs, bounded uncertainty compute runtime integration for deterministic sampling, sensitivity post-processing, ensemble statistics, empirical probability estimation, and governed runtime handoffs, and a renderer-neutral visual reasoning object model for semantic visual objects, elements, relations, layers, annotations, source bindings, and reproducible snapshots, and a governed visualization specification and renderer-contract registry with compatibility resolution and non-executing renderer selection records, plus governed System Maps with explicit boundaries, domains, memberships, saved views, structural validation, and renderer-neutral specification compilation, and governed Flow Maps with typed channels, relation-bound directed flows, quantitative metadata, node-state observations, unit-safe balance summaries, validation, and renderer-neutral specification compilation, plus governed cross-product visual research objects that preserve product identity, references, provenance, semantic relations, portable packages, and renderer-neutral composition contracts across Sustainable Catalyst runtimes, and a Reproducible Visual Knowledge Layer for locked input manifests, environment capture, external replay plans, integrity fingerprints, verification records, immutable snapshots, and portable reproducibility packages, plus Open Forensics with governed investigations, typed forensic objects, evidence/source provenance, semantic relations, immutable forensic snapshots, tamper-evident custody event chains, evidence seals, integrity checks, continuity assessments, and externally attestable custody records, plus structured claims, explicit contradictions, competing hypotheses, evidence-position assessments, descriptive hypothesis matrices, and immutable reasoning snapshots without automated contradiction detection, truth determination, hypothesis ranking, probability assignment, verdict generation, or legal-conclusion inference, plus forensic timeline and event reconstruction with evidence-linked events, bounded temporal assertions, explicit event relations, reconstruction hypotheses, saved timeline views, renderer-neutral timeline specifications, and immutable timeline snapshots without automated event inference or sequence-truth determination, plus forensic spatial/temporal evidence integration with governed places, evidence/location and event/place bindings, spatial uncertainty envelopes, trajectory evidence, explicit space-time intersections, linked map-timeline scene specifications, and reference-first Site Intelligence handoffs without Core-side reprojection, routing, spatial joins, or remote sensing, plus testimony, statements, and documentary evidence with source-context preservation, speaker/author references, claim bindings, explicit corroboration/contradiction relations, temporal-consistency records, and immutable snapshots without automated identity, authorship, credibility, or truth determination, plus a Forensic Research Graph that unifies explicit references across evidence, objects, custody, claims, hypotheses, events, places, media, quantitative reconstructions, documentary sources, and cross-product handoffs without automated identity, causal, proof, or truth inference, plus Reproducible Investigation Packages that freeze cross-forensics component manifests, environment and artifact references, integrity verifications, review records, and portable snapshots without treating reproducibility as authenticity, admissibility, causation, proof, or truth, plus Predictive Intelligence with governed model identity, target and feature provenance, training-window manifests, forecast runs and observations, time-series dataset and forecast-window registries, rolling/expanding backtest plans, baseline references, leakage-aware folds, prediction-actual records, descriptive evaluation evidence, specialist-runtime handoffs, immutable forecast snapshots, and reproducible backtest packages without Core-side model fitting, forecast/backtest execution, metric computation, ranking, calibration, or truth promotion."
        ),
        contact={
            "name": "Sustainable Catalyst",
            "url": "https://sustainablecatalyst.com/",
        },
        license_info={"name": "MIT"},
    )

    database = Database(settings.database_url)
    run_migrations(database)
    app.state.database = database
    app.state.settings = settings
    gateway_settings = GatewaySettings.from_env()
    app.state.gateway_settings = gateway_settings
    app.state.service_registry = ServiceRegistry.from_env()
    app.state.gateway_runtime = GatewayRuntime(
        app.state.service_registry,
        gateway_settings,
        core_version=settings.version,
    )
    app.state.live_data_runtime = LiveDataRuntime(settings)

    app.add_middleware(PublicApiMiddleware)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=list(settings.cors_origins),
        allow_credentials=False,
        allow_methods=["GET", "POST", "PATCH", "OPTIONS"],
        allow_headers=[
            "Content-Type",
            "Authorization",
            "X-SC-API-Key",
            "X-SC-Public-Key",
            "X-Request-ID",
            "Last-Event-ID",
            "X-SC-Principal",
            "X-SC-Principal-Type",
            "X-SC-Product",
        ],
        expose_headers=[
            "X-Request-ID",
            "Last-Event-ID",
            "X-SC-Principal",
            "X-SC-Principal-Type",
            "X-SC-Product",
            "X-SC-API-Version",
            "X-RateLimit-Limit-Minute",
            "X-RateLimit-Remaining-Minute",
            "X-RateLimit-Limit-Day",
            "X-RateLimit-Remaining-Day",
            "Retry-After",
            "X-SC-Core-Version",
            "X-SC-Gateway-Service",
            "X-SC-Upstream-Latency-Ms",
            "Server-Timing",
        ],
    )

    app.add_middleware(RequestTraceMiddleware)

    app.include_router(meta.router)
    app.include_router(dossier_center.router)
    app.include_router(dossier_public_site.router)
    app.include_router(trust_center.router)
    app.include_router(developer_portal.router)
    app.include_router(explorer.router)
    app.include_router(evidence_explorer.router)
    app.include_router(predicates.router)
    app.include_router(public_api.router)
    app.include_router(gateway.router)
    app.include_router(live_data.router)
    app.include_router(live_data.public_router)
    app.include_router(reliability.router)
    app.include_router(reliability.public_router)
    app.include_router(facilities.router)
    app.include_router(facilities.public_router)
    app.include_router(humanitarian.router)
    app.include_router(humanitarian.public_router)
    app.include_router(country_evidence.router)
    app.include_router(country_evidence.public_router)
    app.include_router(cross_product_exchange.router)
    app.include_router(cross_product_exchange.public_router)
    app.include_router(scale.router)
    app.include_router(scale.public_router)
    app.include_router(governance.router)
    app.include_router(governance.public_router)
    app.include_router(certification.router)
    app.include_router(certification.public_router)
    app.include_router(observability.router)
    app.include_router(observability.public_router)
    app.include_router(operations.router)
    app.include_router(operations.public_router)
    app.include_router(continuity.router)
    app.include_router(continuity.public_router)
    app.include_router(resilience.router)
    app.include_router(resilience.public_router)
    app.include_router(lifecycle.router)
    app.include_router(lifecycle.public_router)
    app.include_router(federation.router)
    app.include_router(federation.public_router)
    app.include_router(capacity.router)
    app.include_router(capacity.public_router)
    app.include_router(credentials.router)
    app.include_router(credentials.public_router)
    app.include_router(workload_governance.router)
    app.include_router(workload_governance.public_router)
    app.include_router(international_law.router)
    app.include_router(international_law.public_router)
    app.include_router(scientific_data.router)
    app.include_router(scientific_data.public_router)
    app.include_router(scientific_service_fabric.router)
    app.include_router(scientific_service_fabric.public_router)
    app.include_router(scientific_objects.router)
    app.include_router(scientific_objects.public_router)
    app.include_router(research_objects.router)
    app.include_router(research_objects.public_router)
    app.include_router(visual_reasoning.router)
    app.include_router(visual_reasoning.public_router)
    app.include_router(visualization_registry.router)
    app.include_router(visualization_registry.public_router)
    app.include_router(system_maps.router)
    app.include_router(system_maps.public_router)
    app.include_router(flow_maps.router)
    app.include_router(flow_maps.public_router)
    app.include_router(scenario_landscapes.router)
    app.include_router(scenario_landscapes.public_router)
    app.include_router(model_canvas.router)
    app.include_router(model_canvas.public_router)
    app.include_router(scenario_compute.router)
    app.include_router(scenario_compute.public_router)
    app.include_router(uncertainty_reasoning.router)
    app.include_router(uncertainty_reasoning.public_router)
    app.include_router(uncertainty_compute.router)
    app.include_router(uncertainty_compute.public_router)
    app.include_router(causal_systems.router)
    app.include_router(causal_systems.public_router)
    app.include_router(spatial_temporal.router)
    app.include_router(spatial_temporal.public_router)
    app.include_router(research_visual_explanations.router)
    app.include_router(research_visual_explanations.public_router)
    app.include_router(cross_product_visual_research.router)
    app.include_router(cross_product_visual_research.public_router)
    app.include_router(reproducible_visual_knowledge.router)
    app.include_router(reproducible_visual_knowledge.public_router)
    # v2.61.0 renderer-neutral Visual Reasoning Runtime & Scene Graph.
    app.include_router(visual_runtime.router)
    app.include_router(visual_runtime.public_router)
    # v2.62.0 governed interactive renderer and coordinated view composition.
    app.include_router(visual_composition.router)
    # v2.63.0 renderer-neutral Analytical Visualization Grammar.
    app.include_router(visual_grammar.router)
    app.include_router(visual_grammar.public_router)
    # v2.64.0 governed linked views and cross-filter interaction contracts.
    app.include_router(visual_linked_views.router)
    app.include_router(visual_linked_views.public_router)
    # v2.65.0 governed visual query and exploration contracts.
    app.include_router(visual_query_exploration.router)
    app.include_router(visual_query_exploration.public_router)
    # v2.66.0 governed visual model construction and external execution handoffs.
    app.include_router(visual_model_construction.router)
    app.include_router(visual_model_construction.public_router)
    # v2.67.0 governed Visual Predictive Intelligence bindings and overlays.
    app.include_router(visual_predictive_intelligence.router)
    app.include_router(visual_predictive_intelligence.public_router)
    # v2.68.0 governed Visual Forensics Workbench bindings.
    app.include_router(visual_forensics_workbench.router)
    app.include_router(visual_forensics_workbench.public_router)
    # v2.69.0 governed Visual Decision Intelligence workspaces.
    app.include_router(visual_decision_intelligence.router)
    app.include_router(visual_decision_intelligence.public_router)
    # v2.70.0 convergence layer for the Unified Visual Reasoning Engine.
    app.include_router(unified_visual_reasoning.router)
    app.include_router(unified_visual_reasoning.public_router)
    # v2.71.0 shared visual-runtime contracts for specialist Catalyst products.
    app.include_router(cross_product_visual_runtime_integration.router)
    app.include_router(cross_product_visual_runtime_integration.public_router)
    # v2.72.0 first-class Unified Research Project Object Model.
    app.include_router(unified_research_projects.router)
    app.include_router(unified_research_projects.public_router)
    # v2.73.0 Research Lineage & Provenance Graph.
    app.include_router(research_lineage.router)
    app.include_router(research_lineage.public_router)
    # Open Forensics includes v2.51.0 Reproducible Investigation Packages.
    app.include_router(open_forensics.router)
    app.include_router(open_forensics.public_router)
    # Predictive Intelligence v2.59.0 adds governed predictive decision intelligence above the v2.58.0 causal-predictive layer.
    app.include_router(predictive_intelligence.router)
    app.include_router(predictive_intelligence.public_router)
    app.include_router(economic_data.router)
    app.include_router(economic_data.public_router)
    app.include_router(data_fabric.router)
    app.include_router(data_fabric.public_router)
    app.include_router(data_fabric.stac_router)
    app.include_router(data_fabric.public_stac_router)
    app.include_router(trust_public.router)
    app.include_router(workflow_public.router)
    app.include_router(entities.router)
    app.include_router(relationships.router)
    app.include_router(evidence.router)
    app.include_router(ledger.router)
    app.include_router(foundations.router)
    app.include_router(imports.router)
    app.include_router(developer_admin.router)
    app.include_router(trust_admin.router)
    app.include_router(workflows.router)

    return app


app = create_app()
