from fastapi import APIRouter, Depends, Request
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
    }


@router.get("/ready")
def ready(db: Session = Depends(get_session)):
    db.execute(text("SELECT 1"))
    return {
        "ok": True,
        "database": "ready",
        "knowledge_graph": "ready",
        "evidence_ledger": "ready",
        "unified_public_api": "ready",
        "unified_service_gateway": "ready",
        "trust_center": "ready",
        "live_data_gateway": "ready",
        "international_law_un_connector_pack": "ready",
        "scientific_data_connector_pack": "ready",
        "economics_official_statistics_connector_pack": "ready",
        "geospatial_time_series_scientific_data_fabric": "ready",
        "stac_catalog": "ready",
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
