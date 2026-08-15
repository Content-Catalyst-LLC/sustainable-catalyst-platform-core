from __future__ import annotations
from dataclasses import dataclass
import os

def _bool(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}

def _int(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None:
        return default
    try:
        return int(raw)
    except ValueError:
        return default

@dataclass(frozen=True)
class Settings:
    app_name: str = "Sustainable Catalyst Platform Core"
    version: str = "2.22.0"
    environment: str = "development"
    database_url: str = "sqlite:///./platform_core.db"
    write_api_key: str = ""
    public_reads: bool = True
    cors_origins: tuple[str, ...] = ("http://127.0.0.1:8090",)
    public_base_url: str = ""
    public_base_url_required: bool = False
    required_cors_origin: str = ""
    log_level: str = "INFO"
    max_graph_depth: int = 4
    page_size_max: int = 200
    explorer_enabled: bool = True
    evidence_explorer_enabled: bool = True
    snapshot_excerpt_max: int = 1200
    public_api_enabled: bool = True
    developer_portal_enabled: bool = True
    public_api_default_plan: str = "free"
    api_log_salt: str = "development-api-log-salt"
    webhook_signing_secret: str = "development-webhook-signing-secret"
    webhook_delivery_timeout: int = 10
    trust_center_enabled: bool = True
    trust_public_status_enabled: bool = True
    trust_stale_after_days: int = 90
    workflow_engine_enabled: bool = True
    dossier_center_enabled: bool = True
    dossier_signing_secret: str = "development-dossier-signing-secret"
    dossier_signing_key_id: str = "sc-platform-core-development"
    dossier_required_approvals: int = 1
    dossier_max_records: int = 500
    live_data_enabled: bool = True
    live_data_ingest_enabled: bool = True
    live_data_strict_free_sources: bool = True
    live_data_user_agent: str = "SustainableCatalystPlatformCore/2.22.0 (+https://sustainablecatalyst.com/contact/)"
    live_data_timeout_seconds: int = 20
    live_data_max_response_bytes: int = 12582912
    live_data_raw_payload_max_bytes: int = 1048576
    fred_api_key: str = ""
    reliefweb_appname: str = ""
    hdx_hapi_app_identifier: str = "sustainable-catalyst-platform-core"
    uhri_api_url: str = ""
    un_population_bearer_token: str = ""
    nasa_api_key: str = "DEMO_KEY"
    ncbi_api_key: str = ""
    materials_project_api_key: str = ""
    imf_api_base_url: str = ""
    imf_api_token: str = ""
    bea_api_key: str = ""
    bls_registration_key: str = ""
    census_api_key: str = ""
    eia_api_key: str = ""
    faostat_api_base_url: str = "https://fenixservices.fao.org/faostat/api/v1/en/data"
    data_fabric_enabled: bool = True
    data_fabric_auto_materialize: bool = True
    data_fabric_postgis_auto_enable: bool = True
    streaming_enabled: bool = True
    streaming_poll_seconds: int = 2
    streaming_retention_hours: int = 168
    reliability_worker_enabled: bool = True
    reliability_worker_lease_seconds: int = 60
    reliability_worker_max_attempts: int = 3
    provider_failover_enabled: bool = True
    humanitarian_fabric_enabled: bool = True
    humanitarian_auto_materialize: bool = True
    country_evidence_federation_enabled: bool = True
    scientific_service_fabric_enabled: bool = True
    cross_product_exchange_enabled: bool = True
    scale_control_plane_enabled: bool = True
    scale_max_active_jobs: int = 64
    scale_max_partitions_per_job: int = 256
    scale_partition_lease_seconds: int = 120
    scale_inline_result_max_bytes: int = 262144
    scale_queue_backpressure_threshold: int = 1000
    scale_completed_retention_hours: int = 168
    governance_control_plane_enabled: bool = True
    governance_enforcement_mode: str = "audit"
    governance_audit_retention_hours: int = 8760
    governance_decision_retention_hours: int = 2160
    production_certification_enabled: bool = True
    certification_require_zero_pending_migrations: bool = True
    certification_require_valid_audit_chain: bool = True
    certification_require_gateway_release_ready: bool = False
    recovery_checkpoint_enabled: bool = True
    recovery_checkpoint_retention_hours: int = 720
    observability_control_plane_enabled: bool = True
    observability_request_metrics_enabled: bool = True
    observability_public_status_enabled: bool = True
    observability_retention_hours: int = 720
    observability_default_window_minutes: int = 60
    observability_default_availability_target: float = 99.0
    observability_default_latency_p95_ms: int = 1000
    incident_change_control_enabled: bool = True
    incident_public_status_enabled: bool = True
    incident_retention_hours: int = 8760
    change_high_risk_approval_required: bool = True
    continuity_disaster_recovery_enabled: bool = True
    continuity_public_status_enabled: bool = True
    backup_filesystem_verification_enabled: bool = True
    backup_filesystem_root: str = ""
    dr_default_rpo_minutes: int = 1440
    dr_default_rto_minutes: int = 240
    dr_max_backup_age_minutes: int = 1440
    dr_restore_rehearsal_max_age_hours: int = 720
    certification_require_recent_verified_backup: bool = False
    certification_require_recent_restore_rehearsal: bool = False
    multi_region_resilience_enabled: bool = True
    multi_region_public_status_enabled: bool = True
    multi_region_default_max_replication_lag_seconds: int = 300
    multi_region_degraded_read_only_enabled: bool = True
    certification_require_multi_region_ready: bool = False
    data_lifecycle_preservation_enabled: bool = True
    data_lifecycle_public_status_enabled: bool = True
    data_lifecycle_default_min_retention_days: int = 365
    data_lifecycle_default_archive_after_days: int = 90
    data_lifecycle_hard_delete_enabled: bool = False
    certification_require_preservation_ready: bool = False

    @classmethod
    def from_env(cls) -> "Settings":
        origins = tuple(
            value.strip()
            for value in os.getenv(
                "SC_CORE_CORS_ORIGINS",
                "http://localhost:3000,http://127.0.0.1:8090",
            ).split(",")
            if value.strip()
        )
        database_url = os.getenv("SC_CORE_DATABASE_URL", "sqlite:///./platform_core.db")
        if database_url.startswith("postgres://"):
            database_url = database_url.replace("postgres://", "postgresql+psycopg://", 1)
        elif database_url.startswith("postgresql://"):
            database_url = database_url.replace("postgresql://", "postgresql+psycopg://", 1)
        environment = os.getenv(
            "SC_CORE_ENVIRONMENT",
            "development",
        ).strip().lower()
        production = environment == "production"
        return cls(
            environment=environment,
            database_url=database_url,
            write_api_key=os.getenv("SC_CORE_WRITE_API_KEY", "").strip(),
            public_reads=_bool("SC_CORE_PUBLIC_READS", True),
            cors_origins=origins,
            public_base_url=os.getenv("SC_CORE_PUBLIC_BASE_URL", "").strip().rstrip("/"),
            public_base_url_required=_bool("SC_CORE_PUBLIC_BASE_URL_REQUIRED", False),
            required_cors_origin=os.getenv("SC_CORE_REQUIRED_CORS_ORIGIN", "").strip().rstrip("/"),
            log_level=os.getenv("SC_CORE_LOG_LEVEL", "INFO").strip().upper(),
            max_graph_depth=max(1, min(_int("SC_CORE_MAX_GRAPH_DEPTH", 4), 6)),
            page_size_max=max(10, min(_int("SC_CORE_PAGE_SIZE_MAX", 200), 1000)),
            explorer_enabled=_bool("SC_CORE_EXPLORER_ENABLED", True),
            evidence_explorer_enabled=_bool("SC_CORE_EVIDENCE_EXPLORER_ENABLED", True),
            snapshot_excerpt_max=max(0, min(_int("SC_CORE_SNAPSHOT_EXCERPT_MAX", 1200), 10000)),
            public_api_enabled=_bool("SC_CORE_PUBLIC_API_ENABLED", True),
            developer_portal_enabled=_bool("SC_CORE_DEVELOPER_PORTAL_ENABLED", True),
            public_api_default_plan=os.getenv("SC_CORE_PUBLIC_API_DEFAULT_PLAN", "free").strip(),
            api_log_salt=os.getenv(
                "SC_CORE_API_LOG_SALT",
                "" if production else "development-api-log-salt",
            ).strip(),
            webhook_signing_secret=os.getenv(
                "SC_CORE_WEBHOOK_SIGNING_SECRET",
                "" if production else "development-webhook-signing-secret",
            ).strip(),
            webhook_delivery_timeout=max(
                1,
                min(_int("SC_CORE_WEBHOOK_DELIVERY_TIMEOUT", 10), 60),
            ),
            trust_center_enabled=_bool("SC_CORE_TRUST_CENTER_ENABLED", True),
            trust_public_status_enabled=_bool("SC_CORE_TRUST_PUBLIC_STATUS_ENABLED", True),
            trust_stale_after_days=max(1, min(_int("SC_CORE_TRUST_STALE_AFTER_DAYS", 90), 3650)),
            workflow_engine_enabled=_bool("SC_CORE_WORKFLOW_ENGINE_ENABLED", True),
            dossier_center_enabled=_bool("SC_CORE_DOSSIER_CENTER_ENABLED", True),
            dossier_signing_secret=os.getenv(
                "SC_CORE_DOSSIER_SIGNING_SECRET",
                "" if production else "development-dossier-signing-secret",
            ).strip(),
            dossier_signing_key_id=os.getenv(
                "SC_CORE_DOSSIER_SIGNING_KEY_ID",
                "sc-platform-core-development",
            ).strip(),
            dossier_required_approvals=max(
                0,
                min(_int("SC_CORE_DOSSIER_REQUIRED_APPROVALS", 1), 20),
            ),
            dossier_max_records=max(
                1,
                min(_int("SC_CORE_DOSSIER_MAX_RECORDS", 500), 5000),
            ),
            live_data_enabled=_bool("SC_CORE_LIVE_DATA_ENABLED", True),
            live_data_ingest_enabled=_bool("SC_CORE_LIVE_DATA_INGEST_ENABLED", True),
            live_data_strict_free_sources=_bool("SC_CORE_LIVE_DATA_STRICT_FREE_SOURCES", True),
            live_data_user_agent=os.getenv(
                "SC_CORE_LIVE_DATA_USER_AGENT",
                "SustainableCatalystPlatformCore/2.22.0 (+https://sustainablecatalyst.com/contact/)",
            ).strip(),
            live_data_timeout_seconds=max(
                1, min(_int("SC_CORE_LIVE_DATA_TIMEOUT_SECONDS", 20), 120)
            ),
            live_data_max_response_bytes=max(
                1024, min(_int("SC_CORE_LIVE_DATA_MAX_RESPONSE_BYTES", 12582912), 52428800)
            ),
            live_data_raw_payload_max_bytes=max(
                1024, min(_int("SC_CORE_LIVE_DATA_RAW_PAYLOAD_MAX_BYTES", 1048576), 10485760)
            ),
            fred_api_key=os.getenv("SC_CORE_FRED_API_KEY", "").strip(),
            reliefweb_appname=os.getenv("SC_CORE_RELIEFWEB_APPNAME", "").strip(),
            hdx_hapi_app_identifier=os.getenv(
                "SC_CORE_HDX_HAPI_APP_IDENTIFIER",
                "sustainable-catalyst-platform-core",
            ).strip(),
            uhri_api_url=os.getenv("SC_CORE_UHRI_API_URL", "").strip(),
            un_population_bearer_token=os.getenv(
                "SC_CORE_UN_POPULATION_BEARER_TOKEN", ""
            ).strip(),
            nasa_api_key=os.getenv("SC_CORE_NASA_API_KEY", "DEMO_KEY").strip() or "DEMO_KEY",
            ncbi_api_key=os.getenv("SC_CORE_NCBI_API_KEY", "").strip(),
            materials_project_api_key=os.getenv("SC_CORE_MATERIALS_PROJECT_API_KEY", "").strip(),
            imf_api_base_url=os.getenv("SC_CORE_IMF_API_BASE_URL", "").strip(),
            imf_api_token=os.getenv("SC_CORE_IMF_API_TOKEN", "").strip(),
            bea_api_key=os.getenv("SC_CORE_BEA_API_KEY", "").strip(),
            bls_registration_key=os.getenv("SC_CORE_BLS_REGISTRATION_KEY", "").strip(),
            census_api_key=os.getenv("SC_CORE_CENSUS_API_KEY", "").strip(),
            eia_api_key=os.getenv("SC_CORE_EIA_API_KEY", "").strip(),
            faostat_api_base_url=os.getenv("SC_CORE_FAOSTAT_API_BASE_URL", "https://fenixservices.fao.org/faostat/api/v1/en/data").strip(),
            data_fabric_enabled=_bool("SC_CORE_DATA_FABRIC_ENABLED", True),
            data_fabric_auto_materialize=_bool("SC_CORE_DATA_FABRIC_AUTO_MATERIALIZE", True),
            data_fabric_postgis_auto_enable=_bool("SC_CORE_DATA_FABRIC_POSTGIS_AUTO_ENABLE", True),
            streaming_enabled=_bool("SC_CORE_STREAMING_ENABLED", True),
            streaming_poll_seconds=max(1, min(_int("SC_CORE_STREAMING_POLL_SECONDS", 2), 30)),
            streaming_retention_hours=max(1, min(_int("SC_CORE_STREAMING_RETENTION_HOURS", 168), 8760)),
            reliability_worker_enabled=_bool("SC_CORE_RELIABILITY_WORKER_ENABLED", True),
            reliability_worker_lease_seconds=max(5, min(_int("SC_CORE_RELIABILITY_WORKER_LEASE_SECONDS", 60), 3600)),
            reliability_worker_max_attempts=max(1, min(_int("SC_CORE_RELIABILITY_WORKER_MAX_ATTEMPTS", 3), 20)),
            provider_failover_enabled=_bool("SC_CORE_PROVIDER_FAILOVER_ENABLED", True),
            humanitarian_fabric_enabled=_bool("SC_CORE_HUMANITARIAN_FABRIC_ENABLED", True),
            humanitarian_auto_materialize=_bool("SC_CORE_HUMANITARIAN_AUTO_MATERIALIZE", True),
            country_evidence_federation_enabled=_bool("SC_CORE_COUNTRY_EVIDENCE_FEDERATION_ENABLED", True),
            scientific_service_fabric_enabled=_bool("SC_CORE_SCIENTIFIC_SERVICE_FABRIC_ENABLED", True),
            cross_product_exchange_enabled=_bool("SC_CORE_CROSS_PRODUCT_EXCHANGE_ENABLED", True),
            scale_control_plane_enabled=_bool("SC_CORE_SCALE_CONTROL_PLANE_ENABLED", True),
            scale_max_active_jobs=max(1, min(_int("SC_CORE_SCALE_MAX_ACTIVE_JOBS", 64), 4096)),
            scale_max_partitions_per_job=max(1, min(_int("SC_CORE_SCALE_MAX_PARTITIONS_PER_JOB", 256), 10000)),
            scale_partition_lease_seconds=max(5, min(_int("SC_CORE_SCALE_PARTITION_LEASE_SECONDS", 120), 86400)),
            scale_inline_result_max_bytes=max(1024, min(_int("SC_CORE_SCALE_INLINE_RESULT_MAX_BYTES", 262144), 10485760)),
            scale_queue_backpressure_threshold=max(1, min(_int("SC_CORE_SCALE_QUEUE_BACKPRESSURE_THRESHOLD", 1000), 1000000)),
            scale_completed_retention_hours=max(1, min(_int("SC_CORE_SCALE_COMPLETED_RETENTION_HOURS", 168), 87600)),
            governance_control_plane_enabled=_bool("SC_CORE_GOVERNANCE_CONTROL_PLANE_ENABLED", True),
            governance_enforcement_mode=(lambda value: value if value in {"audit", "enforce"} else "audit")(os.getenv("SC_CORE_GOVERNANCE_ENFORCEMENT_MODE", "audit").strip().lower()),
            governance_audit_retention_hours=max(8760, min(_int("SC_CORE_GOVERNANCE_AUDIT_RETENTION_HOURS", 8760), 876000)),
            governance_decision_retention_hours=max(24, min(_int("SC_CORE_GOVERNANCE_DECISION_RETENTION_HOURS", 2160), 87600)),
            production_certification_enabled=_bool("SC_CORE_PRODUCTION_CERTIFICATION_ENABLED", True),
            certification_require_zero_pending_migrations=_bool("SC_CORE_CERTIFICATION_REQUIRE_ZERO_PENDING_MIGRATIONS", True),
            certification_require_valid_audit_chain=_bool("SC_CORE_CERTIFICATION_REQUIRE_VALID_AUDIT_CHAIN", True),
            certification_require_gateway_release_ready=_bool("SC_CORE_CERTIFICATION_REQUIRE_GATEWAY_RELEASE_READY", False),
            recovery_checkpoint_enabled=_bool("SC_CORE_RECOVERY_CHECKPOINT_ENABLED", True),
            recovery_checkpoint_retention_hours=max(24, min(_int("SC_CORE_RECOVERY_CHECKPOINT_RETENTION_HOURS", 720), 87600)),
            observability_control_plane_enabled=_bool("SC_CORE_OBSERVABILITY_CONTROL_PLANE_ENABLED", True),
            observability_request_metrics_enabled=_bool("SC_CORE_OBSERVABILITY_REQUEST_METRICS_ENABLED", True),
            observability_public_status_enabled=_bool("SC_CORE_OBSERVABILITY_PUBLIC_STATUS_ENABLED", True),
            observability_retention_hours=max(24, min(_int("SC_CORE_OBSERVABILITY_RETENTION_HOURS", 720), 87600)),
            observability_default_window_minutes=max(1, min(_int("SC_CORE_OBSERVABILITY_DEFAULT_WINDOW_MINUTES", 60), 10080)),
            observability_default_availability_target=max(0.0, min(float(os.getenv("SC_CORE_OBSERVABILITY_DEFAULT_AVAILABILITY_TARGET", "99.0")), 100.0)),
            observability_default_latency_p95_ms=max(1, min(_int("SC_CORE_OBSERVABILITY_DEFAULT_LATENCY_P95_MS", 1000), 600000)),
            incident_change_control_enabled=_bool("SC_CORE_INCIDENT_CHANGE_CONTROL_ENABLED", True),
            incident_public_status_enabled=_bool("SC_CORE_INCIDENT_PUBLIC_STATUS_ENABLED", True),
            incident_retention_hours=max(168, min(_int("SC_CORE_INCIDENT_RETENTION_HOURS", 8760), 876000)),
            change_high_risk_approval_required=_bool("SC_CORE_CHANGE_HIGH_RISK_APPROVAL_REQUIRED", True),
            continuity_disaster_recovery_enabled=_bool("SC_CORE_CONTINUITY_DISASTER_RECOVERY_ENABLED", True),
            continuity_public_status_enabled=_bool("SC_CORE_CONTINUITY_PUBLIC_STATUS_ENABLED", True),
            backup_filesystem_verification_enabled=_bool("SC_CORE_BACKUP_FILESYSTEM_VERIFICATION_ENABLED", True),
            backup_filesystem_root=os.getenv("SC_CORE_BACKUP_FILESYSTEM_ROOT", "").strip(),
            dr_default_rpo_minutes=max(1, min(_int("SC_CORE_DR_DEFAULT_RPO_MINUTES", 1440), 525600)),
            dr_default_rto_minutes=max(1, min(_int("SC_CORE_DR_DEFAULT_RTO_MINUTES", 240), 10080)),
            dr_max_backup_age_minutes=max(1, min(_int("SC_CORE_DR_MAX_BACKUP_AGE_MINUTES", 1440), 525600)),
            dr_restore_rehearsal_max_age_hours=max(1, min(_int("SC_CORE_DR_RESTORE_REHEARSAL_MAX_AGE_HOURS", 720), 87600)),
            certification_require_recent_verified_backup=_bool("SC_CORE_CERTIFICATION_REQUIRE_RECENT_VERIFIED_BACKUP", False),
            certification_require_recent_restore_rehearsal=_bool("SC_CORE_CERTIFICATION_REQUIRE_RECENT_RESTORE_REHEARSAL", False),
            multi_region_resilience_enabled=_bool("SC_CORE_MULTI_REGION_RESILIENCE_ENABLED", True),
            multi_region_public_status_enabled=_bool("SC_CORE_MULTI_REGION_PUBLIC_STATUS_ENABLED", True),
            multi_region_default_max_replication_lag_seconds=max(0, min(_int("SC_CORE_MULTI_REGION_DEFAULT_MAX_REPLICATION_LAG_SECONDS", 300), 86400)),
            multi_region_degraded_read_only_enabled=_bool("SC_CORE_MULTI_REGION_DEGRADED_READ_ONLY_ENABLED", True),
            certification_require_multi_region_ready=_bool("SC_CORE_CERTIFICATION_REQUIRE_MULTI_REGION_READY", False),
            data_lifecycle_preservation_enabled=_bool("SC_CORE_DATA_LIFECYCLE_PRESERVATION_ENABLED", True),
            data_lifecycle_public_status_enabled=_bool("SC_CORE_DATA_LIFECYCLE_PUBLIC_STATUS_ENABLED", True),
            data_lifecycle_default_min_retention_days=max(1, min(_int("SC_CORE_DATA_LIFECYCLE_DEFAULT_MIN_RETENTION_DAYS", 365), 365000)),
            data_lifecycle_default_archive_after_days=max(0, min(_int("SC_CORE_DATA_LIFECYCLE_DEFAULT_ARCHIVE_AFTER_DAYS", 90), 365000)),
            data_lifecycle_hard_delete_enabled=False,
            certification_require_preservation_ready=_bool("SC_CORE_CERTIFICATION_REQUIRE_PRESERVATION_READY", False),
        )
