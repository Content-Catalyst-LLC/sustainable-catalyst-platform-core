from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
from typing import Any
from urllib.parse import urlsplit

from fastapi import HTTPException
from sqlalchemy import and_, func, select
from sqlalchemy.orm import Session

from ..models import (
    ScientificDataAsset,
    ScientificProcessingAdapter,
    ScientificProcessingRun,
    ScientificStorageBackend,
    ScientificStoredObject,
)
from .reliability import emit_event, sanitize_queue_parameters


ALLOWED_EXTERNAL_SCHEMES = {"https", "s3", "gs", "az"}
FORMAT_ALIASES = {
    "application/fits": "fits",
    "image/fits": "fits",
    "application/x-netcdf": "netcdf",
    "nc": "netcdf",
    "grib": "grib2",
    "application/x-grib2": "grib2",
    "geotiff": "cog",
    "tiff": "cog",
    "tif": "cog",
    "parquet": "geoparquet",
    "application/vnd.apache.parquet": "geoparquet",
    "application/x-votable+xml": "votable",
    "application/json": "json",
}
EXTENSIONS = {
    "fits": ".fits",
    "netcdf": ".nc",
    "zarr": ".zarr",
    "geoparquet": ".parquet",
    "cog": ".tif",
    "pmtiles": ".pmtiles",
    "votable": ".xml",
    "grib2": ".grib2",
    "geojson": ".geojson",
    "json": ".json",
}


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def normalise_format(value: str | None) -> str:
    raw = (value or "unknown").strip().lower()
    return FORMAT_ALIASES.get(raw, re.sub(r"[^a-z0-9]+", "_", raw).strip("_") or "unknown")


def _object_root(settings) -> Path:
    root = Path(settings.scientific_object_storage_root).expanduser().resolve()
    root.mkdir(parents=True, exist_ok=True)
    return root


def _safe_local_path(settings, object_key: str) -> Path:
    root = _object_root(settings)
    candidate = (root / object_key).resolve()
    if candidate != root and root not in candidate.parents:
        raise ValueError("Scientific object key resolves outside the configured storage root.")
    return candidate


def _hash_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _object_key(object_id: str, digest: str, format_name: str) -> str:
    suffix = EXTENSIONS.get(format_name, ".bin")
    return f"sha256/{digest[:2]}/{digest[2:4]}/{object_id}{suffix}"


def _backend_or_error(db: Session, key: str) -> ScientificStorageBackend:
    row = db.scalar(select(ScientificStorageBackend).where(ScientificStorageBackend.backend_key == key))
    if row is None or not row.enabled:
        raise ValueError(f"Scientific storage backend is unavailable: {key}")
    return row


def object_or_404(db: Session, object_id: str, *, public_only: bool = False) -> ScientificStoredObject:
    row = db.get(ScientificStoredObject, object_id)
    if row is None or (public_only and not row.public):
        raise HTTPException(status_code=404, detail="Scientific stored object not found.")
    return row


def adapter_or_404(db: Session, adapter_key: str, *, public_only: bool = False) -> ScientificProcessingAdapter:
    row = db.scalar(select(ScientificProcessingAdapter).where(ScientificProcessingAdapter.adapter_key == adapter_key))
    if row is None or (public_only and not row.public_summary):
        raise HTTPException(status_code=404, detail="Scientific processing adapter not found.")
    return row


def _external_uri(value: str) -> str:
    uri = value.strip()
    parsed = urlsplit(uri)
    if parsed.scheme.lower() not in ALLOWED_EXTERNAL_SCHEMES:
        raise ValueError("External scientific object URI must use https, s3, gs, or az.")
    if parsed.username or parsed.password:
        raise ValueError("Credential-bearing scientific object URIs are not accepted.")
    if parsed.query or parsed.fragment:
        raise ValueError("Signed/query-bearing scientific object URIs are not accepted; register a stable credential-free URI.")
    if not parsed.netloc:
        raise ValueError("External scientific object URI must identify a provider or bucket.")
    return uri


def object_read(row: ScientificStoredObject) -> dict[str, Any]:
    return {
        "id": row.id,
        "scientific_asset_id": row.scientific_asset_id,
        "parent_object_id": row.parent_object_id,
        "backend_key": row.backend_key,
        "object_key": row.object_key,
        "canonical_uri": row.canonical_uri,
        "title": row.title,
        "format": row.format,
        "media_type": row.media_type,
        "size_bytes": row.size_bytes,
        "content_hash": row.content_hash,
        "checksum_algorithm": row.checksum_algorithm,
        "integrity_status": row.integrity_status,
        "lifecycle_state": row.lifecycle_state,
        "retention_class": row.retention_class,
        "derived": row.derived,
        "public": row.public,
        "license_name": row.license_name,
        "attribution": row.attribution,
        "provenance": row.provenance_json or {},
        "metadata": row.metadata_json or {},
        "created_by": row.created_by,
        "created_at": row.created_at,
        "updated_at": row.updated_at,
    }


def adapter_read(row: ScientificProcessingAdapter) -> dict[str, Any]:
    return {
        "adapter_key": row.adapter_key,
        "name": row.name,
        "description": row.description,
        "execution_mode": row.execution_mode,
        "runtime": row.runtime,
        "supported_input_formats": row.supported_input_formats_json or [],
        "supported_output_formats": row.supported_output_formats_json or [],
        "operations": row.operations_json or [],
        "enabled": row.enabled,
        "executable": row.executable,
        "metadata": row.metadata_json or {},
    }


def run_read(row: ScientificProcessingRun) -> dict[str, Any]:
    return {
        "id": row.id,
        "adapter_id": row.adapter_id,
        "input_object_id": row.input_object_id,
        "output_object_id": row.output_object_id,
        "operation": row.operation,
        "idempotency_key": row.idempotency_key,
        "state": row.state,
        "parameters": row.parameters_json or {},
        "provenance": row.provenance_json or {},
        "error_message": row.error_message,
        "requested_by": row.requested_by,
        "started_at": row.started_at,
        "completed_at": row.completed_at,
        "created_at": row.created_at,
        "updated_at": row.updated_at,
    }


def readiness(db: Session, settings) -> dict[str, Any]:
    object_count = int(db.scalar(select(func.count()).select_from(ScientificStoredObject)) or 0)
    local_count = int(db.scalar(select(func.count()).select_from(ScientificStoredObject).where(ScientificStoredObject.backend_key == "local-filesystem")) or 0)
    external_count = int(db.scalar(select(func.count()).select_from(ScientificStoredObject).where(ScientificStoredObject.backend_key == "external-reference")) or 0)
    adapter_count = int(db.scalar(select(func.count()).select_from(ScientificProcessingAdapter)) or 0)
    executable_adapters = int(db.scalar(select(func.count()).select_from(ScientificProcessingAdapter).where(ScientificProcessingAdapter.enabled.is_(True), ScientificProcessingAdapter.executable.is_(True))) or 0)
    processing_runs = int(db.scalar(select(func.count()).select_from(ScientificProcessingRun)) or 0)
    completed_runs = int(db.scalar(select(func.count()).select_from(ScientificProcessingRun).where(ScientificProcessingRun.state == "completed")) or 0)
    root_ready = False
    if settings.scientific_object_storage_enabled:
        try:
            root = _object_root(settings)
            probe = root / ".write-probe"
            probe.write_bytes(b"ok")
            probe.unlink(missing_ok=True)
            root_ready = True
        except OSError:
            root_ready = False
    return {
        "enabled": settings.scientific_object_storage_enabled,
        "processing_enabled": settings.scientific_processing_enabled,
        "local_storage_ready": root_ready,
        "stored_objects": object_count,
        "local_objects": local_count,
        "external_references": external_count,
        "processing_adapters": adapter_count,
        "executable_adapters": executable_adapters,
        "processing_runs": processing_runs,
        "completed_processing_runs": completed_runs,
        "max_upload_bytes": settings.scientific_object_max_upload_bytes,
        "storage_backends": ["local-filesystem", "external-reference"],
        "arbitrary_code_execution": False,
        "credential_values_persisted": False,
        "external_fetch_by_core": False,
    }


def store_bytes(
    db: Session,
    settings,
    payload: bytes,
    *,
    title: str,
    format_name: str,
    media_type: str | None = None,
    scientific_asset_id: str | None = None,
    parent_object_id: str | None = None,
    public: bool = False,
    retention_class: str = "standard",
    license_name: str | None = None,
    attribution: str | None = None,
    provenance: dict[str, Any] | None = None,
    metadata: dict[str, Any] | None = None,
    created_by: str = "operator",
    derived: bool = False,
) -> ScientificStoredObject:
    if not settings.scientific_object_storage_enabled:
        raise ValueError("Scientific object storage is disabled.")
    if len(payload) > settings.scientific_object_max_upload_bytes:
        raise ValueError(f"Scientific object exceeds max upload size of {settings.scientific_object_max_upload_bytes} bytes.")
    _backend_or_error(db, "local-filesystem")
    if scientific_asset_id and db.get(ScientificDataAsset, scientific_asset_id) is None:
        raise ValueError("Scientific data asset not found.")
    if parent_object_id and db.get(ScientificStoredObject, parent_object_id) is None:
        raise ValueError("Parent scientific stored object not found.")
    format_name = normalise_format(format_name)
    digest = _hash_bytes(payload)
    row = ScientificStoredObject(
        scientific_asset_id=scientific_asset_id,
        parent_object_id=parent_object_id,
        backend_key="local-filesystem",
        object_key="pending",
        canonical_uri="pending",
        title=title.strip() or "Scientific object",
        format=format_name,
        media_type=media_type,
        size_bytes=len(payload),
        content_hash=digest,
        checksum_algorithm="sha256",
        integrity_status="verified",
        lifecycle_state="active",
        retention_class=retention_class,
        derived=derived,
        public=public,
        license_name=license_name,
        attribution=attribution,
        provenance_json=sanitize_queue_parameters(provenance or {}),
        metadata_json=sanitize_queue_parameters(metadata or {}),
        created_by=created_by,
    )
    db.add(row)
    db.flush()
    row.object_key = _object_key(row.id, digest, format_name)
    row.canonical_uri = f"sc-object://local-filesystem/{row.object_key}"
    path = _safe_local_path(settings, row.object_key)
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_bytes(payload)
    temp.replace(path)
    db.add(row)
    db.commit()
    db.refresh(row)
    emit_event(db, "scientific.object.stored", "scientific_stored_object", row.id, {"backend_key": row.backend_key, "format": row.format, "size_bytes": row.size_bytes, "derived": row.derived}, public=False)
    return row


def register_external_reference(
    db: Session,
    settings,
    *,
    uri: str,
    title: str,
    format_name: str,
    media_type: str | None = None,
    size_bytes: int | None = None,
    content_hash: str | None = None,
    checksum_algorithm: str | None = None,
    scientific_asset_id: str | None = None,
    parent_object_id: str | None = None,
    public: bool = False,
    retention_class: str = "provider-managed",
    license_name: str | None = None,
    attribution: str | None = None,
    provenance: dict[str, Any] | None = None,
    metadata: dict[str, Any] | None = None,
    created_by: str = "operator",
    derived: bool = False,
) -> ScientificStoredObject:
    if not settings.scientific_object_storage_enabled:
        raise ValueError("Scientific object storage is disabled.")
    _backend_or_error(db, "external-reference")
    stable_uri = _external_uri(uri)
    if scientific_asset_id and db.get(ScientificDataAsset, scientific_asset_id) is None:
        raise ValueError("Scientific data asset not found.")
    if parent_object_id and db.get(ScientificStoredObject, parent_object_id) is None:
        raise ValueError("Parent scientific stored object not found.")
    parsed = urlsplit(stable_uri)
    format_name = normalise_format(format_name)
    row = ScientificStoredObject(
        scientific_asset_id=scientific_asset_id,
        parent_object_id=parent_object_id,
        backend_key="external-reference",
        object_key=f"{parsed.scheme}:{parsed.netloc}{parsed.path}",
        canonical_uri=stable_uri,
        title=title.strip() or "Scientific object",
        format=format_name,
        media_type=media_type,
        size_bytes=size_bytes,
        content_hash=content_hash.strip().lower() if content_hash else None,
        checksum_algorithm=checksum_algorithm,
        integrity_status="declared" if content_hash else "unverified",
        lifecycle_state="active",
        retention_class=retention_class,
        derived=derived,
        public=public,
        license_name=license_name,
        attribution=attribution,
        provenance_json=sanitize_queue_parameters(provenance or {}),
        metadata_json=sanitize_queue_parameters(metadata or {}),
        created_by=created_by,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    emit_event(db, "scientific.object.reference.registered", "scientific_stored_object", row.id, {"backend_key": row.backend_key, "format": row.format, "derived": row.derived}, public=False)
    return row


def list_objects(
    db: Session,
    *,
    backend_key: str | None = None,
    format_name: str | None = None,
    scientific_asset_id: str | None = None,
    parent_object_id: str | None = None,
    derived: bool | None = None,
    public_only: bool = False,
    limit: int = 100,
    offset: int = 0,
) -> tuple[list[ScientificStoredObject], int]:
    filters = []
    if backend_key:
        filters.append(ScientificStoredObject.backend_key == backend_key)
    if format_name:
        filters.append(ScientificStoredObject.format == normalise_format(format_name))
    if scientific_asset_id:
        filters.append(ScientificStoredObject.scientific_asset_id == scientific_asset_id)
    if parent_object_id:
        filters.append(ScientificStoredObject.parent_object_id == parent_object_id)
    if derived is not None:
        filters.append(ScientificStoredObject.derived.is_(derived))
    if public_only:
        filters.append(ScientificStoredObject.public.is_(True))
    statement = select(ScientificStoredObject)
    count_statement = select(func.count()).select_from(ScientificStoredObject)
    if filters:
        statement = statement.where(and_(*filters))
        count_statement = count_statement.where(and_(*filters))
    total = int(db.scalar(count_statement) or 0)
    rows = list(db.scalars(statement.order_by(ScientificStoredObject.created_at.desc()).limit(limit).offset(offset)).all())
    return rows, total


def list_adapters(db: Session, *, public_only: bool = False) -> list[ScientificProcessingAdapter]:
    statement = select(ScientificProcessingAdapter)
    if public_only:
        statement = statement.where(ScientificProcessingAdapter.public_summary.is_(True))
    return list(db.scalars(statement.order_by(ScientificProcessingAdapter.adapter_key)).all())


def content_path(db: Session, settings, object_id: str) -> Path:
    row = object_or_404(db, object_id)
    if row.backend_key != "local-filesystem":
        raise ValueError("Object content is provider-managed and is not fetched by Platform Core.")
    path = _safe_local_path(settings, row.object_key)
    if not path.is_file():
        raise ValueError("Stored scientific object bytes are unavailable.")
    digest = _hash_bytes(path.read_bytes())
    if row.content_hash and digest != row.content_hash:
        raise ValueError("Stored scientific object failed integrity verification.")
    return path


def process_object(
    db: Session,
    settings,
    *,
    input_object_id: str,
    adapter_key: str,
    operation: str,
    idempotency_key: str,
    parameters: dict[str, Any] | None = None,
    requested_by: str = "operator",
) -> ScientificProcessingRun:
    if not settings.scientific_processing_enabled:
        raise ValueError("Scientific object processing is disabled.")
    input_object = object_or_404(db, input_object_id)
    adapter = adapter_or_404(db, adapter_key)
    existing = db.scalar(
        select(ScientificProcessingRun).where(
            ScientificProcessingRun.adapter_id == adapter.id,
            ScientificProcessingRun.input_object_id == input_object.id,
            ScientificProcessingRun.operation == operation,
            ScientificProcessingRun.idempotency_key == idempotency_key,
        )
    )
    if existing is not None:
        return existing
    if not adapter.enabled or not adapter.executable:
        raise ValueError("Processing adapter is registered as a contract but is not executable in this release.")
    if operation not in (adapter.operations_json or []):
        raise ValueError("Operation is not supported by the selected processing adapter.")
    inputs = adapter.supported_input_formats_json or []
    if "*" not in inputs and input_object.format not in inputs:
        raise ValueError("Input object format is not supported by the selected processing adapter.")
    run = ScientificProcessingRun(
        adapter_id=adapter.id,
        input_object_id=input_object.id,
        operation=operation,
        idempotency_key=idempotency_key,
        state="running",
        parameters_json=sanitize_queue_parameters(parameters or {}),
        provenance_json={"input_object_id": input_object.id, "adapter_key": adapter.adapter_key, "core_release": settings.version},
        requested_by=requested_by,
        started_at=utcnow(),
    )
    db.add(run)
    db.commit()
    db.refresh(run)
    try:
        if adapter.adapter_key == "builtin.object-manifest" and operation == "manifest":
            manifest = {
                "schema": "sc:scientific-object-manifest:v1",
                "source_object": object_read(input_object),
                "processing": {
                    "adapter": adapter.adapter_key,
                    "operation": operation,
                    "parameters": sanitize_queue_parameters(parameters or {}),
                    "core_release": settings.version,
                },
            }
            payload = (json.dumps(manifest, sort_keys=True, default=str, indent=2) + "\n").encode("utf-8")
            output = store_bytes(
                db,
                settings,
                payload,
                title=f"Manifest — {input_object.title}",
                format_name="json",
                media_type="application/json",
                parent_object_id=input_object.id,
                public=input_object.public,
                retention_class=input_object.retention_class,
                license_name=input_object.license_name,
                attribution=input_object.attribution,
                provenance={"derived_from": input_object.id, "processing_run_id": run.id, "adapter_key": adapter.adapter_key, "operation": operation},
                metadata={"scientific_processing_run_id": run.id, "manifest_schema": "sc:scientific-object-manifest:v1"},
                created_by=requested_by,
                derived=True,
            )
        else:
            raise ValueError("No executable implementation is registered for the requested adapter operation.")
        run.output_object_id = output.id
        run.state = "completed"
        run.completed_at = utcnow()
        run.updated_at = utcnow()
        db.add(run)
        db.commit()
        db.refresh(run)
        emit_event(db, "scientific.processing.completed", "scientific_processing_run", run.id, {"adapter_key": adapter.adapter_key, "operation": operation, "input_object_id": input_object.id, "output_object_id": output.id}, public=False)
        return run
    except Exception as exc:
        run.state = "failed"
        run.error_message = str(exc)[:8000]
        run.completed_at = utcnow()
        run.updated_at = utcnow()
        db.add(run)
        db.commit()
        raise


def processing_run_or_404(db: Session, run_id: str) -> ScientificProcessingRun:
    row = db.get(ScientificProcessingRun, run_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Scientific processing run not found.")
    return row


def certification_snapshot(db: Session, settings) -> dict[str, Any]:
    data = readiness(db, settings)
    ready = bool(
        data["enabled"]
        and data["local_storage_ready"]
        and data["processing_adapters"] >= 1
        and data["executable_adapters"] >= 1
    )
    return {
        "state": "ready" if ready else ("disabled" if not data["enabled"] else "attention"),
        "scientific_object_storage_ready": ready,
        "local_storage_ready": data["local_storage_ready"],
        "processing_adapters": data["processing_adapters"],
        "executable_adapters": data["executable_adapters"],
        "arbitrary_code_execution": False,
        "credential_values_persisted": False,
        "external_fetch_by_core": False,
    }
