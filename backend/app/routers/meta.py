from fastapi import APIRouter, Depends, Request
from urllib.parse import urlsplit
from sqlalchemy import func, select, text
from sqlalchemy.orm import Session

from ..dependencies import get_session, require_read
from ..models import (
    CalculationTrace,
    ClaimRecord,
    Entity,
    EntityAlias,
    EvidenceFoundation,
    EvidenceRecord,
    EvidenceReview,
    EvidenceReviewAssignment,
    EvaluationCheckResult,
    EvaluationDefinition,
    EvaluationRun,
    ImportJob,
    KnownLimitation,
    LedgerEntry,
    LiveDataConnector,
    LiveDataIngestionRun,
    LiveDataObservation,
    InternationalLawRecord,
    ScientificDataRecord,
    EconomicDataRecord,
    GeospatialFeature,
    TimeSeriesDefinition,
    TimeSeriesPoint,
    ScientificDataAsset,
    MapLayer,
    StacCollection,
    StacItem,
    LiveDataSource,
    OperationalFacility,
    FacilityObservation,
    HumanitarianCondition,
    PredicateDefinition,
    ProvenanceActivity,
    ProvenanceLink,
    Relationship,
    RelationshipReview,
    SourceSnapshot,
    TrustAttestation,
    TrustFinding,
    TrustIncident,
    ValidationEvent,
)
from ..schemas import MetaResponse, RegistryStats

router = APIRouter(tags=["Service"])


@router.get("/health")
def health(request: Request):
    return {
        "ok": True,
        "service": request.app.state.settings.app_name,
        "version": request.app.state.settings.version,
        "environment": request.app.state.settings.environment,
        "knowledge_graph": True,
        "evidence_ledger": True,
        "provenance_records": True,
        "unified_public_api": request.app.state.settings.public_api_enabled,
        "unified_service_gateway": request.app.state.gateway_settings.enabled,
        "developer_portal": request.app.state.settings.developer_portal_enabled,
        "workflow_engine": request.app.state.settings.workflow_engine_enabled,
        "dossier_center": request.app.state.settings.dossier_center_enabled,
        "trust_center": request.app.state.settings.trust_center_enabled,
        "live_data_gateway": request.app.state.settings.live_data_enabled,
        "international_law_un_connector_pack": True,
        "scientific_data_connector_pack": True,
        "economics_official_statistics_connector_pack": True,
        "geospatial_time_series_scientific_data_fabric": request.app.state.settings.data_fabric_enabled,
        "stac_catalog": request.app.state.settings.data_fabric_enabled,
        "data_fabric_auto_materialize": request.app.state.settings.data_fabric_auto_materialize,
        "strict_free_sources": request.app.state.settings.live_data_strict_free_sources,
        "operational_evidence_facility_registry": True,
        "humanitarian_access_essential_services_fabric": request.app.state.settings.humanitarian_fabric_enabled,
        "country_evidence_federation_reconciliation": request.app.state.settings.country_evidence_federation_enabled,
        "earth_ocean_space_scientific_service_fabric": request.app.state.settings.scientific_service_fabric_enabled,
        "cross_product_evidence_exchange": request.app.state.settings.cross_product_exchange_enabled,
    }


@router.get("/ready")
async def ready(request: Request, db: Session = Depends(get_session)):
    """Deployment readiness.

    `/health` is intentionally a liveness endpoint.  `/ready` is stricter: a
    first-party product service marked REQUIRED must be configured, enabled, and
    operational before Core reports release readiness. Optional integrations are
    visible but do not block Core from serving its own registry/evidence/data
    fabric capabilities.
    """
    db.execute(text("SELECT 1"))
    gateway = await request.app.state.gateway_runtime.health_snapshot()
    settings = request.app.state.settings
    configuration_blockers: list[str] = []
    if settings.public_base_url_required:
        parsed = urlsplit(settings.public_base_url)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            configuration_blockers.append("public_base_url")
    if (
        settings.required_cors_origin
        and settings.required_cors_origin not in settings.cors_origins
    ):
        configuration_blockers.append("required_cors_origin")
    release_ready = bool(gateway["release_ready"] and not configuration_blockers)
    gateway_state = (
        "disabled"
        if gateway["gateway"] == "disabled"
        else ("ready" if gateway["release_ready"] else "blocked")
    )
    return {
        "ok": release_ready,
        "core_version": settings.version,
        "public_base_url_configured": bool(settings.public_base_url),
        "public_base_url_required": settings.public_base_url_required,
        "required_cors_origin_configured": (
            not settings.required_cors_origin
            or settings.required_cors_origin in settings.cors_origins
        ),
        "configuration_blockers": configuration_blockers,
        "database": "ready",
        "knowledge_graph": "ready",
        "evidence_ledger": "ready",
        "unified_public_api": "ready" if settings.public_api_enabled else "disabled",
        "unified_service_gateway": gateway_state,
        "gateway_overall_status": gateway["overall_status"],
        "required_service_count": gateway["required_service_count"],
        "required_ready_count": gateway["required_ready_count"],
        "required_blockers": gateway["required_blockers"],
        "configured_service_count": gateway["configured_service_count"],
        "trust_center": "ready" if settings.trust_center_enabled else "disabled",
        "live_data_gateway": "ready" if settings.live_data_enabled else "disabled",
        "international_law_un_connector_pack": "ready",
        "scientific_data_connector_pack": "ready",
        "economics_official_statistics_connector_pack": "ready",
        "geospatial_time_series_scientific_data_fabric": (
            "ready" if settings.data_fabric_enabled else "disabled"
        ),
        "stac_catalog": "ready" if settings.data_fabric_enabled else "disabled",
        "streaming_alerts_source_reliability": "ready" if settings.streaming_enabled else "disabled",
        "connector_worker": "ready" if settings.reliability_worker_enabled else "disabled",
        "provider_failover": "ready" if settings.provider_failover_enabled else "disabled",
        "operational_evidence_facility_registry": "ready",
        "humanitarian_access_essential_services_fabric": "ready" if settings.humanitarian_fabric_enabled else "disabled",
        "country_evidence_federation_reconciliation": "ready" if settings.country_evidence_federation_enabled else "disabled",
        "earth_ocean_space_scientific_service_fabric": "ready" if settings.scientific_service_fabric_enabled else "disabled",
        "cross_product_evidence_exchange": "ready" if settings.cross_product_exchange_enabled else "disabled",
        "external_provider_health_release_blocking": False,
        "services": [
            {
                "service_id": item["service_id"],
                "name": item["name"],
                "required": item["required"],
                "configured": item["configured"],
                "enabled": item["enabled"],
                "status": item["status"],
                "readiness": item["readiness"],
                "upstream_version": item.get("upstream_version"),
            }
            for item in gateway["services"]
        ],
    }


@router.get("/integration/readiness")
async def integration_readiness(request: Request):
    """Public-safe first-party integration status with no URLs or tokens."""
    gateway = await request.app.state.gateway_runtime.health_snapshot()
    settings = request.app.state.settings
    configuration_blockers: list[str] = []
    if settings.public_base_url_required:
        parsed = urlsplit(settings.public_base_url)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            configuration_blockers.append("public_base_url")
    if (
        settings.required_cors_origin
        and settings.required_cors_origin not in settings.cors_origins
    ):
        configuration_blockers.append("required_cors_origin")
    release_ready = bool(gateway["release_ready"] and not configuration_blockers)
    return {
        "ok": release_ready,
        "core_version": settings.version,
        "public_base_url_configured": bool(settings.public_base_url),
        "required_cors_origin_configured": (
            not settings.required_cors_origin
            or settings.required_cors_origin in settings.cors_origins
        ),
        "configuration_blockers": configuration_blockers,
        "gateway": gateway["gateway"],
        "overall_status": gateway["overall_status"],
        "required_service_count": gateway["required_service_count"],
        "required_ready_count": gateway["required_ready_count"],
        "required_blockers": gateway["required_blockers"],
        "services": [
            {
                "service_id": item["service_id"],
                "name": item["name"],
                "required": item["required"],
                "configured": item["configured"],
                "enabled": item["enabled"],
                "status": item["status"],
                "readiness": item["readiness"],
                "upstream_version": item.get("upstream_version"),
            }
            for item in gateway["services"]
        ],
    }


@router.get(
    "/v1/meta",
    response_model=MetaResponse,
    dependencies=[Depends(require_read)],
)
def meta(request: Request):
    settings = request.app.state.settings
    return MetaResponse(
        name=settings.app_name,
        version=settings.version,
        environment=settings.environment,
        public_reads=settings.public_reads,
        write_auth_configured=bool(settings.write_api_key),
        max_graph_depth=settings.max_graph_depth,
        explorer_enabled=settings.explorer_enabled,
        capabilities=[
            "universal_entity_registry",
            "operational_evidence_facility_registry",
            "humanitarian_access_essential_services_fabric",
            "earth_ocean_space_scientific_service_fabric",
            "cross_product_evidence_exchange",
            "reference_first_product_handoffs",
            "non_destructive_evidence_exchange",
            "scientific_domain_routing",
            "ocean_front_door_contract",
            "space_front_door_contract",
            "scientific_routing_non_truth_precedence",
            "controlled_predicate_registry",
            "relationship_review_workflow",
            "bounded_graph_traversal",
            "shortest_path_queries",
            "graph_backed_recommendations",
            "jsonld_entity_records",
            "public_knowledge_explorer",
            "claim_registry",
            "immutable_source_snapshots",
            "source_hash_verification",
            "evidence_records",
            "evidence_review_workflow",
            "evidence_review_assignments",
            "calculation_traces",
            "provenance_activities",
            "provenance_links",
            "tamper_evident_ledger",
            "ledger_chain_verification",
            "evidence_manifests",
            "public_evidence_explorer",
            "site_intelligence_manifest_import",
            "validation_event_foundation",
            "openapi",
            "python_client",
            "wordpress_client",
            "unified_public_api_v1",
            "unified_service_gateway",
            "environment_backed_service_registry",
            "aggregated_downstream_health",
            "cross_service_request_tracing",
            "bounded_service_proxy",
            "free_live_data_gateway",
            "free_source_acceptance_gate",
            "live_data_source_registry",
            "live_data_connector_sdk",
            "bounded_raw_response_cache",
            "normalized_live_observations",
            "data_freshness_classification",
            "source_license_and_attribution_registry",
            "live_data_provenance",
            "international_law_record_store",
            "united_nations_connector_pack",
            "legal_authority_classification",
            "scientific_data_connector_pack",
            "scientific_data_record_store",
            "economics_official_statistics_connector_pack",
            "economic_data_record_store",
            "sdmx_statistics_gateway",
            "company_filing_facts",
            "energy_statistics_ingestion",
            "geospatial_data_fabric",
            "portable_geojson_store",
            "postgis_expression_indexing",
            "bbox_spatial_queries",
            "geojson_feature_collections",
            "time_series_registry",
            "monthly_time_series_partition_keys",
            "scientific_asset_registry",
            "stac_1_0_catalog",
            "stac_item_search",
            "map_layer_registry",
            "wms_wmts_handoffs",
            "cog_pmtiles_asset_handoffs",
            "fits_netcdf_zarr_geoparquet_registry",
            "scientific_dataset_discovery",
            "astronomy_archive_discovery",
            "biomedical_and_chemical_discovery",
            "biodiversity_occurrence_discovery",
            "materials_science_discovery",
            "hydrology_observation_ingestion",
            "read_only_adql_gateway",
            "weather_reference_connector",
            "earth_observation_reference_connector",
            "hazard_event_reference_connector",
            "economic_indicator_reference_connectors",
            "sustainability_reference_connector",
            "per_service_circuit_breakers",
            "hashed_developer_credentials",
            "scoped_api_access",
            "plan_aware_rate_limits",
            "request_usage_records",
            "developer_applications",
            "developer_portal",
            "public_openapi",
            "python_public_sdk",
            "javascript_public_sdk",
            "postman_collection",
            "signed_webhooks",
            "webhook_delivery_outbox",
            "workflow_definition_registry",
            "ordered_end_to_end_workflows",
            "append_only_workflow_transitions",
            "signature_dossiers",
            "frozen_record_snapshots",
            "dossier_approvals",
            "platform_dossier_signatures",
            "dossier_signature_verification",
            "public_dossier_center",
            "public_trust_center",
            "evaluation_definition_registry",
            "immutable_evaluation_runs",
            "check_level_evaluation_results",
            "automated_trust_evaluators",
            "trust_findings",
            "public_incident_history",
            "known_limitation_registry",
            "trust_attestations",
            "machine_readable_trust_status",
            "trust_webhook_events",
        ],
        deferred_capabilities=[
            "large_scale_graph_database_adapter",
            "user_casebooks",
            "external_public_key_signature_verification",
            "qualified_electronic_signatures",
            "external_snapshot_object_storage_adapter",
            "developer_self_service_billing",
            "distributed_rate_limit_backend",
            "distributed_connector_workers",
            "server_sent_live_data_events",
            "scientific_object_storage_adapter",
            "native_raster_processing_workers",
            "native_scientific_file_parsers",
        ],
    )


@router.get(
    "/v1/stats",
    response_model=RegistryStats,
    dependencies=[Depends(require_read)],
)
def stats(db: Session = Depends(get_session)):
    entity_rows = db.execute(
        select(Entity.entity_type, func.count(Entity.id))
        .group_by(Entity.entity_type)
        .order_by(Entity.entity_type)
    ).all()
    predicate_rows = db.execute(
        select(Relationship.predicate, func.count(Relationship.id))
        .group_by(Relationship.predicate)
        .order_by(Relationship.predicate)
    ).all()
    relationship_status_rows = db.execute(
        select(Relationship.status, func.count(Relationship.id))
        .group_by(Relationship.status)
        .order_by(Relationship.status)
    ).all()

    def count(model) -> int:
        return int(db.scalar(select(func.count()).select_from(model)) or 0)

    return RegistryStats(
        entities=count(Entity),
        relationships=count(Relationship),
        aliases=count(EntityAlias),
        predicate_definitions=count(PredicateDefinition),
        relationship_reviews=count(RelationshipReview),
        claims=count(ClaimRecord),
        source_snapshots=count(SourceSnapshot),
        evidence_records=count(EvidenceRecord),
        evidence_reviews=count(EvidenceReview),
        review_assignments=count(EvidenceReviewAssignment),
        provenance_activities=count(ProvenanceActivity),
        provenance_links=count(ProvenanceLink),
        calculation_traces=count(CalculationTrace),
        ledger_entries=count(LedgerEntry),
        evidence_foundations=count(EvidenceFoundation),
        validation_events=count(ValidationEvent),
        import_jobs=count(ImportJob),
        evaluation_definitions=count(EvaluationDefinition),
        evaluation_runs=count(EvaluationRun),
        evaluation_check_results=count(EvaluationCheckResult),
        trust_findings=count(TrustFinding),
        trust_incidents=count(TrustIncident),
        known_limitations=count(KnownLimitation),
        trust_attestations=count(TrustAttestation),
        live_data_sources=count(LiveDataSource),
        live_data_connectors=count(LiveDataConnector),
        live_data_ingestion_runs=count(LiveDataIngestionRun),
        live_data_observations=count(LiveDataObservation),
        international_law_records=count(InternationalLawRecord),
        scientific_data_records=count(ScientificDataRecord),
        economic_data_records=count(EconomicDataRecord),
        geospatial_features=count(GeospatialFeature),
        time_series_definitions=count(TimeSeriesDefinition),
        time_series_points=count(TimeSeriesPoint),
        scientific_data_assets=count(ScientificDataAsset),
        map_layers=count(MapLayer),
        stac_collections=count(StacCollection),
        stac_items=count(StacItem),
        entities_by_type={key: int(value) for key, value in entity_rows},
        relationships_by_predicate={
            key: int(value) for key, value in predicate_rows
        },
        relationships_by_status={
            key: int(value) for key, value in relationship_status_rows
        },
    )
