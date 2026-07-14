from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from typing import Any
import xml.etree.ElementTree as ET

import httpx
from fastapi import HTTPException
from sqlalchemy import and_, desc, func, select
from sqlalchemy.orm import Session

from ..connectors import ADAPTERS, NormalizedObservation
from ..models import (
    LiveDataConnector,
    LiveDataIngestionRun,
    LiveDataObservation,
    LiveDataRawRecord,
    LiveDataSource,
    InternationalLawRecord,
    ScientificDataRecord,
)

APPROVED_SOURCE_STATUSES = {
    "APPROVED_FREE",
    "APPROVED_WITH_ATTRIBUTION",
    "APPROVED_METADATA_ONLY",
    "APPROVED_SELF_HOSTED",
}


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def ensure_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def international_law_record_id(connector_id: str, source_record_id: str, record_type: str) -> str:
    return hashlib.sha256(f"{connector_id}|{source_record_id}|{record_type}".encode("utf-8")).hexdigest()


def scientific_data_record_id(connector_id: str, source_record_id: str, record_type: str) -> str:
    return hashlib.sha256(f"science|{connector_id}|{source_record_id}|{record_type}".encode("utf-8")).hexdigest()


def observation_id(connector_id: str, observation: NormalizedObservation) -> str:
    basis = "|".join(
        [
            connector_id,
            observation.source_record_id,
            observation.metric,
            ensure_utc(observation.observed_at).isoformat(),
        ]
    )
    return hashlib.sha256(basis.encode("utf-8")).hexdigest()


def classify_freshness(
    requested_status: str | None,
    *,
    observed_at: datetime,
    retrieved_at: datetime,
    freshness_window_seconds: int,
) -> str:
    if requested_status:
        return requested_status
    observed = ensure_utc(observed_at)
    retrieved = ensure_utc(retrieved_at)
    if observed > retrieved:
        return "forecast"
    age = max(0.0, (retrieved - observed).total_seconds())
    if age <= min(freshness_window_seconds, 3600):
        return "near_real_time"
    if age <= freshness_window_seconds:
        return "current"
    return "stale"


class LiveDataRuntimeError(RuntimeError):
    def __init__(self, detail: str, status_code: int = 400):
        super().__init__(detail)
        self.detail = detail
        self.status_code = status_code


class LiveDataRuntime:
    def __init__(self, settings, *, transport: httpx.AsyncBaseTransport | None = None):
        self.settings = settings
        self.transport = transport

    def _source_gate(self, source: LiveDataSource) -> None:
        if not source.active:
            raise LiveDataRuntimeError("The source is inactive.", 503)
        if self.settings.live_data_strict_free_sources:
            if source.access_cost != "free" or source.credit_card_required:
                raise LiveDataRuntimeError(
                    "The source does not pass the strict free-source acceptance gate.", 403
                )
            if source.review_status not in APPROVED_SOURCE_STATUSES:
                raise LiveDataRuntimeError(
                    "The source license or automated-access review is incomplete.", 403
                )

    def _connector_or_error(
        self, db: Session, connector_id: str
    ) -> tuple[LiveDataConnector, LiveDataSource]:
        connector = db.get(LiveDataConnector, connector_id)
        if connector is None:
            raise LiveDataRuntimeError("Unknown live-data connector.", 404)
        source = db.get(LiveDataSource, connector.source_id)
        if source is None:
            raise LiveDataRuntimeError("The connector source record is missing.", 500)
        if not self.settings.live_data_enabled:
            raise LiveDataRuntimeError("Live-data integration is disabled.", 503)
        if not connector.enabled or connector.status != "active":
            raise LiveDataRuntimeError("The connector is disabled.", 503)
        self._source_gate(source)
        return connector, source

    def connector_configuration_status(self, connector: LiveDataConnector) -> str:
        if connector.adapter not in ADAPTERS:
            return "adapter_missing"
        if connector.id == "fred.series-observations" and not self.settings.fred_api_key:
            return "credential_required"
        if connector.id == "ocha.reliefweb-reports" and not self.settings.reliefweb_appname:
            return "registration_required"
        if connector.id == "ohchr.uhri-recommendations" and not self.settings.uhri_api_url:
            return "endpoint_registration_required"
        if connector.id == "materials-project.summary" and not self.settings.materials_project_api_key:
            return "credential_required"
        if not self.settings.live_data_enabled:
            return "subsystem_disabled"
        if not connector.enabled:
            return "disabled"
        return "configured"

    async def ingest(
        self,
        db: Session,
        connector_id: str,
        *,
        parameters: dict[str, Any] | None = None,
        requested_by: str = "platform-core",
        run_type: str = "manual",
    ) -> LiveDataIngestionRun:
        if not self.settings.live_data_ingest_enabled:
            raise LiveDataRuntimeError("Live-data ingestion is disabled.", 503)
        connector, source = self._connector_or_error(db, connector_id)
        adapter = ADAPTERS.get(connector.adapter)
        if adapter is None:
            raise LiveDataRuntimeError("The connector adapter is unavailable.", 503)
        if self.connector_configuration_status(connector) != "configured":
            raise LiveDataRuntimeError(
                f"Connector configuration incomplete: {self.connector_configuration_status(connector)}.",
                503,
            )

        clean_parameters = dict(parameters or {})
        run = LiveDataIngestionRun(
            connector_id=connector.id,
            run_type=run_type,
            requested_by=requested_by,
            parameters_json=clean_parameters,
            status="running",
        )
        db.add(run)
        db.commit()
        db.refresh(run)

        retrieved_at = utcnow()
        try:
            request = adapter.build_request(connector, clean_parameters, self.settings)
            request_params = {key: value for key, value in request.params.items() if value is not None}
            timeout = min(connector.timeout_seconds, self.settings.live_data_timeout_seconds)
            limits = httpx.Limits(max_connections=10, max_keepalive_connections=5)
            async with httpx.AsyncClient(
                timeout=timeout,
                follow_redirects=True,
                transport=self.transport,
                limits=limits,
            ) as client:
                response = await client.request(
                    request.method,
                    request.url,
                    params=request_params,
                    headers=request.headers,
                    json=request.json_body,
                    data=request.data,
                )
            run.http_status = response.status_code
            response.raise_for_status()
            max_bytes = min(connector.max_response_bytes, self.settings.live_data_max_response_bytes)
            if len(response.content) > max_bytes:
                raise LiveDataRuntimeError(
                    f"Upstream response exceeded the {max_bytes}-byte connector limit.", 502
                )

            raw_payload, normalized = adapter.normalize(
                response,
                connector=connector,
                parameters=clean_parameters,
                retrieved_at=retrieved_at,
            )
            raw_hash = hashlib.sha256(response.content).hexdigest()
            run.raw_content_hash = raw_hash
            run.records_received = len(normalized)

            raw_limit = self.settings.live_data_raw_payload_max_bytes
            serialized_raw = json.dumps(raw_payload, sort_keys=True, default=str).encode("utf-8")
            truncated = len(serialized_raw) > raw_limit
            stored_payload = (
                raw_payload
                if not truncated
                else {
                    "truncated": True,
                    "reason": "raw_payload_exceeds_storage_limit",
                    "original_size_bytes": len(serialized_raw),
                    "content_hash": raw_hash,
                    "preview": response.text[: min(4096, len(response.text))],
                }
            )
            raw = LiveDataRawRecord(
                connector_id=connector.id,
                ingestion_run_id=run.id,
                source_record_id="response",
                media_type=response.headers.get("content-type", "application/octet-stream").split(";")[0],
                payload_json=stored_payload,
                content_hash=raw_hash,
                size_bytes=len(response.content),
                truncated=truncated,
                retrieved_at=retrieved_at,
            )
            db.add(raw)
            db.flush()

            public_records = bool(connector.configuration_json.get("public_records", True))
            created = 0
            updated = 0
            rejected = 0
            legal_created = 0
            legal_updated = 0
            scientific_created = 0
            scientific_updated = 0
            for item in normalized:
                try:
                    item.observed_at = ensure_utc(item.observed_at)
                    if item.published_at is not None:
                        item.published_at = ensure_utc(item.published_at)
                    record_id = observation_id(connector.id, item)
                    existing = db.get(LiveDataObservation, record_id)
                    values = {
                        "connector_id": connector.id,
                        "source_id": source.id,
                        "raw_record_id": raw.id,
                        "source_record_id": item.source_record_id,
                        "domain": item.domain,
                        "metric": item.metric,
                        "value_number": item.value_number,
                        "value_text": item.value_text,
                        "unit": item.unit,
                        "geometry_json": item.geometry,
                        "dimensions_json": item.dimensions,
                        "observed_at": item.observed_at,
                        "published_at": item.published_at,
                        "retrieved_at": retrieved_at,
                        "freshness_status": classify_freshness(
                            item.freshness_status,
                            observed_at=item.observed_at,
                            retrieved_at=retrieved_at,
                            freshness_window_seconds=connector.freshness_window_seconds,
                        ),
                        "quality_status": item.quality_status,
                        "license_name": source.license_name,
                        "attribution": source.attribution,
                        "methodology_url": item.methodology_url or source.documentation_url,
                        "raw_record_hash": raw_hash,
                        "metadata_json": item.metadata,
                        "public": bool(item.public and connector.public and source.public and public_records),
                    }
                    if existing is None:
                        db.add(LiveDataObservation(id=record_id, **values))
                        created += 1
                    else:
                        for key, value in values.items():
                            setattr(existing, key, value)
                        db.add(existing)
                        updated += 1

                    if item.legal_record:
                        legal = dict(item.legal_record)
                        legal_metadata = legal.pop("metadata", {})
                        record_type = str(legal.get("record_type") or "un_official_document")
                        legal_id = international_law_record_id(connector.id, item.source_record_id, record_type)
                        legal_existing = db.get(InternationalLawRecord, legal_id)
                        legal_values = {
                            "connector_id": connector.id,
                            "source_id": source.id,
                            "raw_record_id": raw.id,
                            "source_record_id": item.source_record_id,
                            "record_type": record_type,
                            "authority_level": str(legal.get("authority_level") or "official_report"),
                            "title": str(legal.get("title") or item.value_text or item.source_record_id),
                            "official_symbol": legal.get("official_symbol"),
                            "issuing_body": legal.get("issuing_body"),
                            "legal_body": legal.get("legal_body"),
                            "jurisdiction": str(legal.get("jurisdiction") or "international"),
                            "legal_status": str(legal.get("legal_status") or "official_record"),
                            "adoption_date": ensure_utc(legal["adoption_date"]) if legal.get("adoption_date") else None,
                            "publication_date": ensure_utc(legal["publication_date"]) if legal.get("publication_date") else item.published_at,
                            "entry_into_force_date": ensure_utc(legal["entry_into_force_date"]) if legal.get("entry_into_force_date") else None,
                            "languages_json": list(legal.get("languages") or []),
                            "countries_json": list(legal.get("countries") or []),
                            "subjects_json": list(legal.get("subjects") or []),
                            "related_instruments_json": list(legal.get("related_instruments") or []),
                            "related_cases_json": list(legal.get("related_cases") or []),
                            "related_resolutions_json": list(legal.get("related_resolutions") or []),
                            "related_sdg_targets_json": list(legal.get("related_sdg_targets") or []),
                            "canonical_source_url": legal.get("canonical_source_url"),
                            "citation": legal.get("citation"),
                            "summary": legal.get("summary"),
                            "license_name": source.license_name,
                            "attribution": source.attribution,
                            "content_hash": hashlib.sha256(json.dumps({**legal, "metadata": legal_metadata}, sort_keys=True, default=str).encode("utf-8")).hexdigest(),
                            "metadata_json": legal_metadata,
                            "public": bool(item.public and connector.public and source.public and public_records),
                        }
                        if legal_existing is None:
                            db.add(InternationalLawRecord(id=legal_id, **legal_values))
                            legal_created += 1
                        else:
                            for key, value in legal_values.items():
                                setattr(legal_existing, key, value)
                            db.add(legal_existing)
                            legal_updated += 1

                    if item.scientific_record:
                        science = dict(item.scientific_record)
                        science_metadata = science.pop("metadata", {})
                        record_type = str(science.get("record_type") or "scientific_dataset")
                        science_id = scientific_data_record_id(connector.id, item.source_record_id, record_type)
                        science_existing = db.get(ScientificDataRecord, science_id)
                        def science_date(name, fallback=None):
                            value = science.get(name)
                            return ensure_utc(value) if isinstance(value, datetime) else fallback
                        science_values = {
                            "connector_id": connector.id,
                            "source_id": source.id,
                            "raw_record_id": raw.id,
                            "source_record_id": item.source_record_id,
                            "record_type": record_type,
                            "discipline": str(science.get("discipline") or item.domain or "science"),
                            "title": str(science.get("title") or item.value_text or item.source_record_id),
                            "summary": science.get("summary"),
                            "dataset_id": science.get("dataset_id"),
                            "collection": science.get("collection"),
                            "mission": science.get("mission"),
                            "instrument": science.get("instrument"),
                            "target": science.get("target"),
                            "doi": science.get("doi"),
                            "access_url": science.get("access_url"),
                            "landing_page_url": science.get("landing_page_url"),
                            "geometry_json": science.get("geometry") or item.geometry,
                            "observation_start": science_date("observation_start", item.observed_at),
                            "observation_end": science_date("observation_end"),
                            "published_at": science_date("published_at", item.published_at),
                            "identifiers_json": dict(science.get("identifiers") or {}),
                            "keywords_json": list(science.get("keywords") or []),
                            "variables_json": list(science.get("variables") or []),
                            "file_formats_json": list(science.get("file_formats") or []),
                            "quality_status": str(science.get("quality_status") or item.quality_status),
                            "license_name": source.license_name,
                            "attribution": source.attribution,
                            "content_hash": hashlib.sha256(json.dumps({**science, "metadata": science_metadata}, sort_keys=True, default=str).encode("utf-8")).hexdigest(),
                            "metadata_json": science_metadata,
                            "public": bool(item.public and connector.public and source.public and public_records),
                        }
                        if science_existing is None:
                            db.add(ScientificDataRecord(id=science_id, **science_values))
                            scientific_created += 1
                        else:
                            for key, value in science_values.items():
                                setattr(science_existing, key, value)
                            db.add(science_existing)
                            scientific_updated += 1
                except Exception:
                    rejected += 1

            run.records_created = created
            run.records_updated = updated
            run.records_rejected = rejected
            run.status = "completed" if rejected == 0 else "completed_with_rejections"
            run.completed_at = utcnow()
            run.details_json = {
                "adapter": connector.adapter,
                "request_url": str(response.request.url).split("?")[0],
                "raw_record_id": raw.id,
                "raw_payload_truncated": truncated,
                "international_law_records_created": legal_created,
                "international_law_records_updated": legal_updated,
                "scientific_data_records_created": scientific_created,
                "scientific_data_records_updated": scientific_updated,
            }
            connector.last_health_status = "operational"
            connector.last_health_checked_at = run.completed_at
            connector.last_success_at = run.completed_at
            connector.last_error = None
            db.add_all([run, connector])
            db.commit()
            db.refresh(run)
            return run
        except LiveDataRuntimeError as exc:
            self._record_failure(db, connector, run, exc.detail)
            raise
        except httpx.HTTPStatusError as exc:
            detail = f"Upstream returned HTTP {exc.response.status_code}."
            self._record_failure(db, connector, run, detail)
            raise LiveDataRuntimeError(detail, 502) from exc
        except httpx.HTTPError as exc:
            detail = f"Upstream connection failed: {exc.__class__.__name__}."
            self._record_failure(db, connector, run, detail)
            raise LiveDataRuntimeError(detail, 502) from exc
        except (ValueError, TypeError, ET.ParseError) as exc:
            detail = f"Connector validation failed: {exc}"
            self._record_failure(db, connector, run, detail)
            raise LiveDataRuntimeError(detail, 422) from exc
        except Exception as exc:
            detail = f"Connector ingestion failed: {exc.__class__.__name__}."
            self._record_failure(db, connector, run, detail)
            raise LiveDataRuntimeError(detail, 500) from exc

    @staticmethod
    def _record_failure(
        db: Session,
        connector: LiveDataConnector,
        run: LiveDataIngestionRun,
        detail: str,
    ) -> None:
        now = utcnow()
        run.status = "failed"
        run.error_message = detail[:10000]
        run.completed_at = now
        connector.last_health_status = "degraded"
        connector.last_health_checked_at = now
        connector.last_failure_at = now
        connector.last_error = detail[:10000]
        db.add_all([run, connector])
        db.commit()


def get_source_or_404(db: Session, source_id: str) -> LiveDataSource:
    source = db.get(LiveDataSource, source_id)
    if source is None:
        raise HTTPException(status_code=404, detail="Live-data source not found.")
    return source


def get_connector_or_404(db: Session, connector_id: str) -> LiveDataConnector:
    connector = db.get(LiveDataConnector, connector_id)
    if connector is None:
        raise HTTPException(status_code=404, detail="Live-data connector not found.")
    return connector


def get_run_or_404(db: Session, run_id: str) -> LiveDataIngestionRun:
    run = db.get(LiveDataIngestionRun, run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="Live-data ingestion run not found.")
    return run


def get_observation_or_404(
    db: Session, observation_id_value: str, *, public_only: bool = False
) -> LiveDataObservation:
    observation = db.get(LiveDataObservation, observation_id_value)
    if observation is None or (public_only and not observation.public):
        raise HTTPException(status_code=404, detail="Live-data observation not found.")
    return observation


def list_sources(
    db: Session,
    *,
    active: bool | None = True,
    review_status: str | None = None,
    public_only: bool = False,
) -> list[LiveDataSource]:
    statement = select(LiveDataSource)
    if active is not None:
        statement = statement.where(LiveDataSource.active == active)
    if review_status:
        statement = statement.where(LiveDataSource.review_status == review_status)
    if public_only:
        statement = statement.where(LiveDataSource.public.is_(True))
    return list(db.scalars(statement.order_by(LiveDataSource.name)).all())


def list_connectors(
    db: Session,
    *,
    domain: str | None = None,
    source_id: str | None = None,
    enabled: bool | None = True,
    public_only: bool = False,
) -> list[LiveDataConnector]:
    statement = select(LiveDataConnector)
    if domain:
        statement = statement.where(LiveDataConnector.domain == domain)
    if source_id:
        statement = statement.where(LiveDataConnector.source_id == source_id)
    if enabled is not None:
        statement = statement.where(LiveDataConnector.enabled == enabled)
    if public_only:
        statement = statement.where(LiveDataConnector.public.is_(True))
    return list(db.scalars(statement.order_by(LiveDataConnector.domain, LiveDataConnector.name)).all())


def list_runs(
    db: Session,
    *,
    connector_id: str | None = None,
    status: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> tuple[list[LiveDataIngestionRun], int]:
    filters = []
    if connector_id:
        filters.append(LiveDataIngestionRun.connector_id == connector_id)
    if status:
        filters.append(LiveDataIngestionRun.status == status)
    base = select(LiveDataIngestionRun)
    count_statement = select(func.count()).select_from(LiveDataIngestionRun)
    if filters:
        base = base.where(and_(*filters))
        count_statement = count_statement.where(and_(*filters))
    total = int(db.scalar(count_statement) or 0)
    items = list(
        db.scalars(
            base.order_by(desc(LiveDataIngestionRun.started_at)).limit(limit).offset(offset)
        ).all()
    )
    return items, total


def list_observations(
    db: Session,
    *,
    connector_id: str | None = None,
    source_id: str | None = None,
    domain: str | None = None,
    metric: str | None = None,
    freshness_status: str | None = None,
    start: datetime | None = None,
    end: datetime | None = None,
    public_only: bool = False,
    latest_per_metric: bool = False,
    limit: int = 100,
    offset: int = 0,
) -> tuple[list[LiveDataObservation], int]:
    filters = []
    if connector_id:
        filters.append(LiveDataObservation.connector_id == connector_id)
    if source_id:
        filters.append(LiveDataObservation.source_id == source_id)
    if domain:
        filters.append(LiveDataObservation.domain == domain)
    if metric:
        filters.append(LiveDataObservation.metric == metric)
    if freshness_status:
        filters.append(LiveDataObservation.freshness_status == freshness_status)
    if start:
        filters.append(LiveDataObservation.observed_at >= start)
    if end:
        filters.append(LiveDataObservation.observed_at <= end)
    if public_only:
        filters.append(LiveDataObservation.public.is_(True))

    base = select(LiveDataObservation)
    count_statement = select(func.count()).select_from(LiveDataObservation)
    if filters:
        base = base.where(and_(*filters))
        count_statement = count_statement.where(and_(*filters))
    if latest_per_metric:
        # Portable correlated subquery that works on SQLite and PostgreSQL.
        latest = (
            select(func.max(LiveDataObservation.observed_at))
            .where(LiveDataObservation.metric == metric)
            .scalar_subquery()
        ) if metric else None
        if latest is not None:
            base = base.where(LiveDataObservation.observed_at == latest)
    total = int(db.scalar(count_statement) or 0)
    items = list(
        db.scalars(
            base.order_by(desc(LiveDataObservation.observed_at), LiveDataObservation.metric)
            .limit(limit)
            .offset(offset)
        ).all()
    )
    return items, total


def live_data_stats(db: Session) -> dict[str, Any]:
    def count(model) -> int:
        return int(db.scalar(select(func.count()).select_from(model)) or 0)

    domain_rows = db.execute(
        select(LiveDataConnector.domain, func.count(LiveDataConnector.id))
        .group_by(LiveDataConnector.domain)
        .order_by(LiveDataConnector.domain)
    ).all()
    freshness_rows = db.execute(
        select(LiveDataObservation.freshness_status, func.count(LiveDataObservation.id))
        .group_by(LiveDataObservation.freshness_status)
        .order_by(LiveDataObservation.freshness_status)
    ).all()
    return {
        "sources": count(LiveDataSource),
        "connectors": count(LiveDataConnector),
        "ingestion_runs": count(LiveDataIngestionRun),
        "raw_records": count(LiveDataRawRecord),
        "observations": count(LiveDataObservation),
        "connectors_by_domain": {key: int(value) for key, value in domain_rows},
        "observations_by_freshness": {key: int(value) for key, value in freshness_rows},
    }


def observation_provenance(db: Session, observation: LiveDataObservation) -> dict[str, Any]:
    source = db.get(LiveDataSource, observation.source_id)
    connector = db.get(LiveDataConnector, observation.connector_id)
    raw = db.get(LiveDataRawRecord, observation.raw_record_id) if observation.raw_record_id else None
    run = db.get(LiveDataIngestionRun, raw.ingestion_run_id) if raw else None
    return {
        "observation_id": observation.id,
        "source_record_id": observation.source_record_id,
        "source": source,
        "connector": connector,
        "ingestion_run": run,
        "raw_record": {
            "id": raw.id,
            "content_hash": raw.content_hash,
            "media_type": raw.media_type,
            "size_bytes": raw.size_bytes,
            "truncated": raw.truncated,
            "retrieved_at": raw.retrieved_at,
        } if raw else None,
        "lineage": {
            "observed_at": observation.observed_at,
            "published_at": observation.published_at,
            "retrieved_at": observation.retrieved_at,
            "raw_record_hash": observation.raw_record_hash,
            "license_name": observation.license_name,
            "attribution": observation.attribution,
            "methodology_url": observation.methodology_url,
            "quality_status": observation.quality_status,
            "freshness_status": observation.freshness_status,
        },
    }
