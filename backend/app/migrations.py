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
    expected = {version for version, _ in MIGRATIONS}
    return {"expected":sorted(expected),"applied":sorted(applied),"pending":sorted(expected-applied),"predicate_definitions":predicates,"api_plans":api_plans,"evaluation_definitions":evaluation_definitions,"workflow_definitions":workflow_definitions,"live_data_sources":live_data_sources,"live_data_connectors":live_data_connectors,"scientific_storage_backends":scientific_storage_backends,"scientific_processing_adapters":scientific_processing_adapters,"research_projects":research_projects,"research_models":research_models,"research_model_versions":research_model_versions,"research_variables":research_variables,"research_parameters":research_parameters,"research_scenarios":research_scenarios,"research_model_runs":research_model_runs,"research_results":research_results,"visual_reasoning_objects":visual_reasoning_objects,"visual_reasoning_elements":visual_reasoning_elements,"visual_reasoning_relations":visual_reasoning_relations,"visual_reasoning_layers":visual_reasoning_layers,"visual_reasoning_annotations":visual_reasoning_annotations,"visual_reasoning_snapshots":visual_reasoning_snapshots,"visualization_specifications":visualization_specifications,"renderer_definitions":renderer_definitions,"renderer_versions":renderer_versions,"renderer_compatibility_rules":renderer_compatibility_rules,"renderer_resolutions":renderer_resolutions,"system_maps":system_maps,"system_map_boundaries":system_map_boundaries,"system_map_domains":system_map_domains,"system_map_memberships":system_map_memberships,"system_map_views":system_map_views,"flow_maps":flow_maps,"flow_map_channels":flow_map_channels,"flow_map_flows":flow_map_flows,"flow_map_node_states":flow_map_node_states,"flow_map_views":flow_map_views,"scenario_landscapes":scenario_landscapes,"scenario_landscape_scenarios":scenario_landscape_scenarios,"scenario_landscape_dimensions":scenario_landscape_dimensions,"scenario_landscape_values":scenario_landscape_values,"scenario_landscape_views":scenario_landscape_views,"model_canvases":model_canvases,"model_canvas_nodes":model_canvas_nodes,"model_canvas_edges":model_canvas_edges,"model_canvas_controls":model_canvas_controls,"model_canvas_states":model_canvas_states,"model_canvas_views":model_canvas_views,"scenario_compute_plans":scenario_compute_plans,"scenario_compute_cases":scenario_compute_cases,"scenario_compute_requests":scenario_compute_requests,"scenario_compute_attempts":scenario_compute_attempts,"scenario_compute_result_bindings":scenario_compute_result_bindings,"uncertainty_definitions":uncertainty_definitions,"sensitivity_studies":sensitivity_studies,"sensitivity_factors":sensitivity_factors,"sensitivity_measures":sensitivity_measures,"ensembles":ensembles,"ensemble_members":ensemble_members,"ensemble_statistics":ensemble_statistics,"uncertainty_compute_runs":uncertainty_compute_runs,"causal_graphs":causal_graphs,"causal_variables":causal_variables,"causal_edges":causal_edges,"causal_interventions":causal_interventions,"causal_identifications":causal_identifications,"causal_estimates":causal_estimates,"causal_diagnostics":causal_diagnostics,"spatial_temporal_scenes":spatial_temporal_scenes,"spatial_temporal_features":spatial_temporal_features,"spatial_temporal_events":spatial_temporal_events,"spatial_temporal_trajectories":spatial_temporal_trajectories,"spatial_temporal_trajectory_points":spatial_temporal_trajectory_points,"spatial_temporal_changes":spatial_temporal_changes,"spatial_temporal_views":spatial_temporal_views,"research_visual_explanations":research_visual_explanations,"research_explanation_nodes":research_explanation_nodes,"research_explanation_relations":research_explanation_relations,"research_explanation_citations":research_explanation_citations,"research_explanation_views":research_explanation_views,"research_explanation_snapshots":research_explanation_snapshots}
