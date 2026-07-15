from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
import re
from typing import Any, Iterable

from fastapi import HTTPException
from sqlalchemy import String, and_, func, or_, select, text
from sqlalchemy.orm import Session

from ..models import (
    GeospatialFeature,
    LiveDataConnector,
    LiveDataObservation,
    LiveDataRawRecord,
    LiveDataSource,
    MapLayer,
    ScientificDataAsset,
    ScientificDataRecord,
    StacCollection,
    StacItem,
    TimeSeriesDefinition,
    TimeSeriesPoint,
)


DATA_FORMAT_CAPABILITIES: dict[str, dict[str, Any]] = {
    "geojson": {"category": "geospatial_vector", "media_types": ["application/geo+json", "application/json"], "support": "native_read_write"},
    "stac": {"category": "catalog", "media_types": ["application/json"], "support": "native_catalog_api"},
    "wms": {"category": "map_service", "media_types": ["application/xml", "image/png", "image/jpeg"], "support": "registry_and_proxy_handoff"},
    "wmts": {"category": "tile_service", "media_types": ["application/xml", "image/png", "image/jpeg"], "support": "registry_and_maplibre_handoff"},
    "cog": {"category": "geospatial_raster", "media_types": ["image/tiff; application=geotiff; profile=cloud-optimized"], "support": "remote_asset_registry"},
    "geoparquet": {"category": "geospatial_columnar", "media_types": ["application/vnd.apache.parquet"], "support": "remote_asset_registry"},
    "pmtiles": {"category": "tile_archive", "media_types": ["application/vnd.pmtiles"], "support": "remote_asset_registry"},
    "netcdf": {"category": "scientific_multidimensional", "media_types": ["application/x-netcdf"], "support": "remote_asset_registry"},
    "zarr": {"category": "scientific_multidimensional", "media_types": ["application/vnd+zarr"], "support": "remote_asset_registry"},
    "fits": {"category": "astronomy", "media_types": ["application/fits", "image/fits"], "support": "remote_asset_registry"},
    "votable": {"category": "astronomy_table", "media_types": ["application/x-votable+xml"], "support": "remote_asset_registry"},
    "sdmx": {"category": "official_statistics", "media_types": ["application/vnd.sdmx.data+csv", "application/vnd.sdmx.genericdata+xml", "application/vnd.sdmx.data+json"], "support": "connector_adapter"},
    "tap_adql": {"category": "astronomy_query", "media_types": ["text/csv", "application/x-votable+xml"], "support": "read_only_connector_adapter"},
    "grib2": {"category": "forecast_grid", "media_types": ["application/x-grib2"], "support": "remote_asset_registry"},
}

MAP_LAYER_TYPES = {
    "geojson": "GeoJSON feature collection",
    "vector_tiles": "Vector tile endpoint or PMTiles archive",
    "raster_tiles": "XYZ/TMS raster tile template",
    "wms": "OGC Web Map Service",
    "wmts": "OGC Web Map Tile Service",
    "cog": "Cloud Optimized GeoTIFF",
    "pmtiles": "PMTiles archive",
    "stac": "STAC collection or item search",
}


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _hash(prefix: str, *parts: Any) -> str:
    payload = "|".join([prefix, *(json.dumps(part, sort_keys=True, default=str) if isinstance(part, (dict, list)) else str(part or "") for part in parts)])
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _normalise_format(value: str | None) -> str:
    raw = (value or "unknown").strip().lower()
    aliases = {
        "geotiff": "cog", "cloud optimized geotiff": "cog", "cloud-optimized geotiff": "cog",
        "tiff": "cog", "tif": "cog", "application/fits": "fits", "image/fits": "fits",
        "application/x-netcdf": "netcdf", "nc": "netcdf", "application/x-votable+xml": "votable",
        "grib": "grib2", "application/x-grib2": "grib2", "application/geo+json": "geojson",
        "application/vnd.apache.parquet": "geoparquet", "parquet": "geoparquet",
    }
    return aliases.get(raw, re.sub(r"[^a-z0-9]+", "_", raw).strip("_") or "unknown")


def media_type_for_format(format_name: str) -> str | None:
    entry = DATA_FORMAT_CAPABILITIES.get(_normalise_format(format_name))
    if not entry:
        return None
    values = entry.get("media_types") or []
    return values[0] if values else None


def _coordinate_pairs(value: Any) -> Iterable[tuple[float, float]]:
    if isinstance(value, (list, tuple)):
        if len(value) >= 2 and all(isinstance(item, (int, float)) for item in value[:2]):
            yield float(value[0]), float(value[1])
        else:
            for item in value:
                yield from _coordinate_pairs(item)


def geometry_bbox(geometry: dict[str, Any] | None) -> list[float]:
    if not geometry:
        return []
    if geometry.get("type") == "Feature":
        geometry = geometry.get("geometry") or {}
    if geometry.get("type") == "FeatureCollection":
        pairs: list[tuple[float, float]] = []
        for feature in geometry.get("features") or []:
            pairs.extend(_coordinate_pairs((feature.get("geometry") or {}).get("coordinates")))
    else:
        pairs = list(_coordinate_pairs(geometry.get("coordinates")))
    if not pairs:
        return []
    xs = [pair[0] for pair in pairs]
    ys = [pair[1] for pair in pairs]
    return [min(xs), min(ys), max(xs), max(ys)]


def _bbox_values(bbox: list[float]) -> dict[str, float | None]:
    if len(bbox) != 4:
        return {"min_x": None, "min_y": None, "max_x": None, "max_y": None}
    return {"min_x": bbox[0], "min_y": bbox[1], "max_x": bbox[2], "max_y": bbox[3]}


def series_identity(observation: LiveDataObservation) -> tuple[str, str, dict[str, Any]]:
    dimensions = dict(observation.dimensions_json or {})
    dataset_id = dimensions.get("dataset_id") or dimensions.get("series_id") or dimensions.get("collection")
    geography = dimensions.get("geography_code") or dimensions.get("country") or dimensions.get("location")
    stable_dimensions = {
        key: value for key, value in dimensions.items()
        if key not in {"retrieved_at", "published_at", "observation_time", "period", "date", "time"}
    }
    dimension_hash = _hash("dimensions", stable_dimensions)
    series_id = _hash("series", observation.connector_id, observation.metric, dimension_hash)
    return series_id, dimension_hash, {"dataset_id": dataset_id, "geography_code": geography, "dimensions": stable_dimensions}


def materialize_observation(db: Session, observation: LiveDataObservation) -> dict[str, int]:
    series_id, dimension_hash, identity = series_identity(observation)
    series = db.get(TimeSeriesDefinition, series_id)
    series_values = {
        "source_id": observation.source_id,
        "connector_id": observation.connector_id,
        "metric": observation.metric,
        "title": observation.metric.replace("_", " ").strip().title(),
        "description": (observation.metadata_json or {}).get("description"),
        "dataset_id": identity["dataset_id"],
        "domain": observation.domain,
        "unit": observation.unit,
        "frequency": (observation.dimensions_json or {}).get("frequency"),
        "geography_code": identity["geography_code"],
        "dimensions_json": identity["dimensions"],
        "dimension_hash": dimension_hash,
        "license_name": observation.license_name,
        "attribution": observation.attribution,
        "public": observation.public,
    }
    series_created = 0
    if series is None:
        series = TimeSeriesDefinition(id=series_id, **series_values)
        db.add(series)
        series_created = 1
    else:
        for key, value in series_values.items():
            setattr(series, key, value)
        db.add(series)

    observed_at = observation.observed_at
    point_hash = _hash("point", observation.source_record_id, observation.value_number, observation.value_text, observation.dimensions_json)
    point_id = _hash("timeseries-point", series_id, observed_at.isoformat(), point_hash)
    point = db.get(TimeSeriesPoint, point_id)
    point_created = 0
    if point is None:
        point = TimeSeriesPoint(
            id=point_id,
            series_id=series_id,
            observation_id=observation.id,
            raw_record_id=observation.raw_record_id,
            observed_at=observed_at,
            partition_key=observed_at.strftime("%Y-%m"),
            value_number=observation.value_number,
            value_text=observation.value_text,
            quality_status=observation.quality_status,
            freshness_status=observation.freshness_status,
            dimensions_json=dict(observation.dimensions_json or {}),
            point_hash=point_hash,
            public=observation.public,
        )
        db.add(point)
        point_created = 1

    feature_created = 0
    if observation.geometry_json:
        geometry = dict(observation.geometry_json)
        bbox = geometry_bbox(geometry)
        feature_id = _hash("feature", observation.source_id, observation.source_record_id, "live_observation")
        feature = db.get(GeospatialFeature, feature_id)
        values = {
            "source_id": observation.source_id,
            "connector_id": observation.connector_id,
            "raw_record_id": observation.raw_record_id,
            "observation_id": observation.id,
            "scientific_record_id": None,
            "source_record_id": observation.source_record_id,
            "dataset_id": identity["dataset_id"],
            "collection_id": (observation.dimensions_json or {}).get("collection"),
            "feature_type": "live_observation",
            "geometry_type": str(geometry.get("type") or "Unknown"),
            "geometry_json": geometry,
            "bbox_json": bbox,
            **_bbox_values(bbox),
            "srid": 4326,
            "properties_json": {
                "metric": observation.metric,
                "value_number": observation.value_number,
                "value_text": observation.value_text,
                "unit": observation.unit,
                "domain": observation.domain,
                **dict(observation.dimensions_json or {}),
            },
            "observed_at": observation.observed_at,
            "valid_until": None,
            "license_name": observation.license_name,
            "attribution": observation.attribution,
            "content_hash": _hash("geometry", geometry, observation.metric, observation.observed_at),
            "public": observation.public,
        }
        if feature is None:
            db.add(GeospatialFeature(id=feature_id, **values))
            feature_created = 1
        else:
            for key, value in values.items():
                setattr(feature, key, value)
            db.add(feature)
    return {"series_created": series_created, "points_created": point_created, "features_created": feature_created}


def stac_collection_key(record: ScientificDataRecord) -> str:
    basis = record.dataset_id or record.collection or f"{record.source_id}-{record.record_type}"
    safe = re.sub(r"[^A-Za-z0-9_.:-]+", "-", basis).strip("-")
    candidate = f"{record.source_id}:{safe}" if safe else record.source_id
    if len(candidate) <= 500:
        return candidate
    return f"{record.source_id}:{_hash('collection', candidate)}"


def materialize_scientific_record(db: Session, record: ScientificDataRecord) -> dict[str, int]:
    assets_created = 0
    collections_created = 0
    items_created = 0
    features_created = 0
    layers_created = 0

    formats = list(record.file_formats_json or [])
    primary_format = _normalise_format(formats[0] if formats else ((record.metadata_json or {}).get("access_format")))
    asset: ScientificDataAsset | None = None
    if record.access_url:
        asset_id = _hash("asset", record.id, record.access_url, "data")
        asset = db.get(ScientificDataAsset, asset_id)
        values = {
            "scientific_record_id": record.id,
            "source_id": record.source_id,
            "connector_id": record.connector_id,
            "raw_record_id": record.raw_record_id,
            "dataset_id": record.dataset_id,
            "title": f"{record.title} data asset",
            "asset_role": "data",
            "media_type": media_type_for_format(primary_format),
            "format": primary_format,
            "href": record.access_url,
            "storage_mode": "remote",
            "size_bytes": (record.metadata_json or {}).get("size_bytes"),
            "checksum": (record.metadata_json or {}).get("checksum"),
            "stac_roles_json": ["data"],
            "variables_json": list(record.variables_json or []),
            "spatial_extent_json": geometry_bbox(record.geometry_json),
            "temporal_extent_json": [
                record.observation_start.isoformat() if record.observation_start else None,
                record.observation_end.isoformat() if record.observation_end else None,
            ],
            "license_name": record.license_name,
            "attribution": record.attribution,
            "metadata_json": {"reported_formats": formats, "landing_page_url": record.landing_page_url},
            "public": record.public,
        }
        if asset is None:
            asset = ScientificDataAsset(id=asset_id, **values)
            db.add(asset)
            assets_created = 1
        else:
            for key, value in values.items():
                setattr(asset, key, value)
            db.add(asset)

    if record.geometry_json:
        geometry = dict(record.geometry_json)
        bbox = geometry_bbox(geometry)
        feature_id = _hash("feature", record.source_id, record.source_record_id, "scientific_record")
        feature = db.get(GeospatialFeature, feature_id)
        values = {
            "source_id": record.source_id,
            "connector_id": record.connector_id,
            "raw_record_id": record.raw_record_id,
            "observation_id": None,
            "scientific_record_id": record.id,
            "source_record_id": record.source_record_id,
            "dataset_id": record.dataset_id,
            "collection_id": record.collection,
            "feature_type": "scientific_record",
            "geometry_type": str(geometry.get("type") or "Unknown"),
            "geometry_json": geometry,
            "bbox_json": bbox,
            **_bbox_values(bbox),
            "srid": 4326,
            "properties_json": {"title": record.title, "record_type": record.record_type, "discipline": record.discipline, "mission": record.mission, "instrument": record.instrument, "target": record.target},
            "observed_at": record.observation_start,
            "valid_until": record.observation_end,
            "license_name": record.license_name,
            "attribution": record.attribution,
            "content_hash": _hash("geometry", geometry, record.content_hash),
            "public": record.public,
        }
        if feature is None:
            db.add(GeospatialFeature(id=feature_id, **values))
            features_created = 1
        else:
            for key, value in values.items():
                setattr(feature, key, value)
            db.add(feature)

        collection_id = stac_collection_key(record)
        collection = db.get(StacCollection, collection_id)
        spatial_extent = bbox or [-180.0, -90.0, 180.0, 90.0]
        temporal_extent = [
            record.observation_start.isoformat() if record.observation_start else None,
            record.observation_end.isoformat() if record.observation_end else None,
        ]
        collection_values = {
            "source_id": record.source_id,
            "connector_id": record.connector_id,
            "title": record.collection or record.dataset_id or f"{record.source_id} {record.record_type}",
            "description": record.summary or f"STAC collection generated from {record.source_id} scientific records.",
            "license_name": record.license_name,
            "spatial_extent_json": [spatial_extent],
            "temporal_extent_json": [temporal_extent],
            "keywords_json": list(record.keywords_json or []),
            "providers_json": [{"name": record.attribution or record.source_id, "roles": ["producer", "licensor"]}],
            "links_json": [],
            "summaries_json": {"record_type": [record.record_type], "discipline": [record.discipline], "formats": formats},
            "public": record.public,
        }
        if collection is None:
            collection = StacCollection(id=collection_id, **collection_values)
            db.add(collection)
            collections_created = 1
        else:
            for key, value in collection_values.items():
                setattr(collection, key, value)
            db.add(collection)

        item_id = _hash("stac-item", collection_id, record.source_record_id)
        item = db.get(StacItem, item_id)
        assets = {}
        if record.access_url:
            assets["data"] = {
                "href": record.access_url,
                "title": record.title,
                "type": media_type_for_format(primary_format),
                "roles": ["data"],
                "sc:format": primary_format,
            }
        item_values = {
            "collection_id": collection_id,
            "source_id": record.source_id,
            "connector_id": record.connector_id,
            "scientific_record_id": record.id,
            "source_record_id": record.source_record_id,
            "geometry_json": geometry,
            "bbox_json": bbox,
            **_bbox_values(bbox),
            "datetime": record.observation_start,
            "start_datetime": record.observation_start,
            "end_datetime": record.observation_end,
            "properties_json": {
                "title": record.title,
                "description": record.summary,
                "created": record.created_at.isoformat() if record.created_at else None,
                "updated": record.updated_at.isoformat() if record.updated_at else None,
                "sustainable_catalyst:discipline": record.discipline,
                "sustainable_catalyst:record_type": record.record_type,
                "sustainable_catalyst:mission": record.mission,
                "sustainable_catalyst:instrument": record.instrument,
            },
            "assets_json": assets,
            "links_json": [],
            "content_hash": _hash("stac-item", record.content_hash, geometry, assets),
            "public": record.public,
        }
        if item is None:
            db.add(StacItem(id=item_id, **item_values))
            items_created = 1
        else:
            for key, value in item_values.items():
                setattr(item, key, value)
            db.add(item)

    if record.access_url and primary_format in {"cog", "pmtiles", "wms", "wmts", "geojson"}:
        layer_id = _hash("map-layer", record.source_id, record.source_record_id, primary_format)
        layer = db.get(MapLayer, layer_id)
        layer_type = primary_format
        values = {
            "source_id": record.source_id,
            "connector_id": record.connector_id,
            "external_layer_id": record.source_record_id,
            "title": record.title,
            "description": record.summary,
            "layer_type": layer_type,
            "endpoint_url": record.access_url,
            "tile_template": record.access_url if primary_format in {"pmtiles", "wmts"} else None,
            "style_json": {},
            "bounds_json": geometry_bbox(record.geometry_json),
            "min_zoom": None,
            "max_zoom": None,
            "time_enabled": bool(record.observation_start),
            "license_name": record.license_name,
            "attribution": record.attribution,
            "status": "active",
            "public": record.public,
            "metadata_json": {"scientific_record_id": record.id, "format": primary_format},
        }
        if layer is None:
            db.add(MapLayer(id=layer_id, **values))
            layers_created = 1
        else:
            for key, value in values.items():
                setattr(layer, key, value)
            db.add(layer)

    return {
        "assets_created": assets_created,
        "stac_collections_created": collections_created,
        "stac_items_created": items_created,
        "features_created": features_created,
        "map_layers_created": layers_created,
    }


def backfill_fabric(db: Session) -> dict[str, int]:
    result = {
        "observations_processed": 0, "scientific_records_processed": 0,
        "series_created": 0, "points_created": 0, "features_created": 0,
        "assets_created": 0, "stac_collections_created": 0, "stac_items_created": 0,
        "map_layers_created": 0,
    }
    for observation in db.scalars(select(LiveDataObservation).order_by(LiveDataObservation.observed_at)).all():
        counts = materialize_observation(db, observation)
        result["observations_processed"] += 1
        for key, value in counts.items(): result[key] += value
    db.flush()
    for record in db.scalars(select(ScientificDataRecord).order_by(ScientificDataRecord.created_at)).all():
        counts = materialize_scientific_record(db, record)
        result["scientific_records_processed"] += 1
        for key, value in counts.items(): result[key] += value
    db.commit()
    return result


def _bbox_filter(model, bbox: list[float] | None):
    if not bbox or len(bbox) != 4:
        return []
    min_x, min_y, max_x, max_y = bbox
    return [model.max_x >= min_x, model.min_x <= max_x, model.max_y >= min_y, model.min_y <= max_y]


def list_features(db: Session, *, source_id: str | None = None, connector_id: str | None = None, dataset_id: str | None = None, feature_type: str | None = None, geometry_type: str | None = None, bbox: list[float] | None = None, start: datetime | None = None, end: datetime | None = None, public_only: bool = False, limit: int = 100, offset: int = 0) -> tuple[list[GeospatialFeature], int]:
    filters = []
    if source_id: filters.append(GeospatialFeature.source_id == source_id)
    if connector_id: filters.append(GeospatialFeature.connector_id == connector_id)
    if dataset_id: filters.append(GeospatialFeature.dataset_id == dataset_id)
    if feature_type: filters.append(GeospatialFeature.feature_type == feature_type)
    if geometry_type: filters.append(GeospatialFeature.geometry_type == geometry_type)
    if start: filters.append(GeospatialFeature.observed_at >= start)
    if end: filters.append(GeospatialFeature.observed_at <= end)
    if public_only: filters.append(GeospatialFeature.public.is_(True))
    filters.extend(_bbox_filter(GeospatialFeature, bbox))
    statement = select(GeospatialFeature)
    count_statement = select(func.count()).select_from(GeospatialFeature)
    if filters:
        statement = statement.where(and_(*filters)); count_statement = count_statement.where(and_(*filters))
    total = int(db.scalar(count_statement) or 0)
    rows = list(db.scalars(statement.order_by(GeospatialFeature.observed_at.desc(), GeospatialFeature.id).limit(limit).offset(offset)).all())
    return rows, total


def feature_or_404(db: Session, feature_id: str, *, public_only: bool = False) -> GeospatialFeature:
    row = db.get(GeospatialFeature, feature_id)
    if row is None or (public_only and not row.public): raise HTTPException(404, "Geospatial feature not found.")
    return row


def feature_collection(rows: list[GeospatialFeature]) -> dict[str, Any]:
    return {"type": "FeatureCollection", "features": [{"type": "Feature", "id": row.id, "geometry": row.geometry_json, "bbox": row.bbox_json or None, "properties": {**dict(row.properties_json or {}), "source_id": row.source_id, "connector_id": row.connector_id, "dataset_id": row.dataset_id, "feature_type": row.feature_type, "observed_at": row.observed_at.isoformat() if row.observed_at else None, "license_name": row.license_name, "attribution": row.attribution}} for row in rows]}


def list_series(db: Session, *, source_id: str | None = None, connector_id: str | None = None, metric: str | None = None, domain: str | None = None, dataset_id: str | None = None, geography_code: str | None = None, public_only: bool = False, limit: int = 100, offset: int = 0) -> tuple[list[TimeSeriesDefinition], int]:
    filters = []
    if source_id: filters.append(TimeSeriesDefinition.source_id == source_id)
    if connector_id: filters.append(TimeSeriesDefinition.connector_id == connector_id)
    if metric: filters.append(TimeSeriesDefinition.metric == metric)
    if domain: filters.append(TimeSeriesDefinition.domain == domain)
    if dataset_id: filters.append(TimeSeriesDefinition.dataset_id == dataset_id)
    if geography_code: filters.append(TimeSeriesDefinition.geography_code == geography_code)
    if public_only: filters.append(TimeSeriesDefinition.public.is_(True))
    statement = select(TimeSeriesDefinition); count_statement = select(func.count()).select_from(TimeSeriesDefinition)
    if filters: statement = statement.where(and_(*filters)); count_statement = count_statement.where(and_(*filters))
    total = int(db.scalar(count_statement) or 0)
    return list(db.scalars(statement.order_by(TimeSeriesDefinition.metric, TimeSeriesDefinition.id).limit(limit).offset(offset)).all()), total


def series_or_404(db: Session, series_id: str, *, public_only: bool = False) -> TimeSeriesDefinition:
    row = db.get(TimeSeriesDefinition, series_id)
    if row is None or (public_only and not row.public): raise HTTPException(404, "Time series not found.")
    return row


def list_points(db: Session, series_id: str, *, start: datetime | None = None, end: datetime | None = None, public_only: bool = False, limit: int = 1000, offset: int = 0) -> tuple[list[TimeSeriesPoint], int]:
    filters = [TimeSeriesPoint.series_id == series_id]
    if start: filters.append(TimeSeriesPoint.observed_at >= start)
    if end: filters.append(TimeSeriesPoint.observed_at <= end)
    if public_only: filters.append(TimeSeriesPoint.public.is_(True))
    statement = select(TimeSeriesPoint).where(and_(*filters)); count_statement = select(func.count()).select_from(TimeSeriesPoint).where(and_(*filters))
    total = int(db.scalar(count_statement) or 0)
    return list(db.scalars(statement.order_by(TimeSeriesPoint.observed_at).limit(limit).offset(offset)).all()), total


def list_assets(db: Session, *, source_id: str | None = None, connector_id: str | None = None, scientific_record_id: str | None = None, dataset_id: str | None = None, format: str | None = None, asset_role: str | None = None, public_only: bool = False, limit: int = 100, offset: int = 0) -> tuple[list[ScientificDataAsset], int]:
    filters = []
    if source_id: filters.append(ScientificDataAsset.source_id == source_id)
    if connector_id: filters.append(ScientificDataAsset.connector_id == connector_id)
    if scientific_record_id: filters.append(ScientificDataAsset.scientific_record_id == scientific_record_id)
    if dataset_id: filters.append(ScientificDataAsset.dataset_id == dataset_id)
    if format: filters.append(ScientificDataAsset.format == _normalise_format(format))
    if asset_role: filters.append(ScientificDataAsset.asset_role == asset_role)
    if public_only: filters.append(ScientificDataAsset.public.is_(True))
    statement = select(ScientificDataAsset); count_statement = select(func.count()).select_from(ScientificDataAsset)
    if filters: statement = statement.where(and_(*filters)); count_statement = count_statement.where(and_(*filters))
    total = int(db.scalar(count_statement) or 0)
    return list(db.scalars(statement.order_by(ScientificDataAsset.created_at.desc()).limit(limit).offset(offset)).all()), total


def asset_or_404(db: Session, asset_id: str, *, public_only: bool = False) -> ScientificDataAsset:
    row = db.get(ScientificDataAsset, asset_id)
    if row is None or (public_only and not row.public): raise HTTPException(404, "Scientific asset not found.")
    return row


def list_map_layers(db: Session, *, source_id: str | None = None, layer_type: str | None = None, status: str | None = "active", public_only: bool = False, limit: int = 100, offset: int = 0) -> tuple[list[MapLayer], int]:
    filters = []
    if source_id: filters.append(MapLayer.source_id == source_id)
    if layer_type: filters.append(MapLayer.layer_type == layer_type)
    if status: filters.append(MapLayer.status == status)
    if public_only: filters.append(MapLayer.public.is_(True))
    statement = select(MapLayer); count_statement = select(func.count()).select_from(MapLayer)
    if filters: statement = statement.where(and_(*filters)); count_statement = count_statement.where(and_(*filters))
    total = int(db.scalar(count_statement) or 0)
    return list(db.scalars(statement.order_by(MapLayer.title).limit(limit).offset(offset)).all()), total


def stac_collection_or_404(db: Session, collection_id: str, *, public_only: bool = False) -> StacCollection:
    row = db.get(StacCollection, collection_id)
    if row is None or (public_only and not row.public): raise HTTPException(404, "STAC collection not found.")
    return row


def stac_item_or_404(db: Session, collection_id: str, item_id: str, *, public_only: bool = False) -> StacItem:
    row = db.get(StacItem, item_id)
    if row is None or row.collection_id != collection_id or (public_only and not row.public): raise HTTPException(404, "STAC item not found.")
    return row


def list_stac_collections(db: Session, *, public_only: bool = False, limit: int = 100, offset: int = 0) -> tuple[list[StacCollection], int]:
    filters = [StacCollection.public.is_(True)] if public_only else []
    statement = select(StacCollection); count_statement = select(func.count()).select_from(StacCollection)
    if filters: statement = statement.where(and_(*filters)); count_statement = count_statement.where(and_(*filters))
    total = int(db.scalar(count_statement) or 0)
    return list(db.scalars(statement.order_by(StacCollection.title).limit(limit).offset(offset)).all()), total


def search_stac_items(db: Session, *, collections: list[str] | None = None, bbox: list[float] | None = None, start: datetime | None = None, end: datetime | None = None, query: str | None = None, public_only: bool = False, limit: int = 100, offset: int = 0) -> tuple[list[StacItem], int]:
    filters = []
    if collections: filters.append(StacItem.collection_id.in_(collections))
    if start: filters.append(or_(StacItem.datetime >= start, StacItem.end_datetime >= start))
    if end: filters.append(or_(StacItem.datetime <= end, StacItem.start_datetime <= end))
    if query: filters.append(StacItem.properties_json.cast(String).ilike(f"%{query}%"))
    if public_only: filters.append(StacItem.public.is_(True))
    filters.extend(_bbox_filter(StacItem, bbox))
    statement = select(StacItem); count_statement = select(func.count()).select_from(StacItem)
    if filters: statement = statement.where(and_(*filters)); count_statement = count_statement.where(and_(*filters))
    total = int(db.scalar(count_statement) or 0)
    return list(db.scalars(statement.order_by(StacItem.datetime.desc(), StacItem.id).limit(limit).offset(offset)).all()), total


def stac_collection_document(row: StacCollection, base_path: str = "/v1/stac") -> dict[str, Any]:
    return {"stac_version": "1.0.0", "type": "Collection", "id": row.id, "title": row.title, "description": row.description, "license": row.license_name or "proprietary", "extent": {"spatial": {"bbox": row.spatial_extent_json or [[-180, -90, 180, 90]]}, "temporal": {"interval": row.temporal_extent_json or [[None, None]]}}, "keywords": row.keywords_json or [], "providers": row.providers_json or [], "summaries": row.summaries_json or {}, "links": [{"rel": "self", "href": f"{base_path}/collections/{row.id}", "type": "application/json"}, {"rel": "items", "href": f"{base_path}/collections/{row.id}/items", "type": "application/geo+json"}, *list(row.links_json or [])]}


def stac_item_document(row: StacItem, base_path: str = "/v1/stac") -> dict[str, Any]:
    properties = dict(row.properties_json or {})
    properties.setdefault("datetime", row.datetime.isoformat() if row.datetime else None)
    if row.start_datetime: properties.setdefault("start_datetime", row.start_datetime.isoformat())
    if row.end_datetime: properties.setdefault("end_datetime", row.end_datetime.isoformat())
    return {"stac_version": "1.0.0", "type": "Feature", "id": row.id, "collection": row.collection_id, "geometry": row.geometry_json, "bbox": row.bbox_json or None, "properties": properties, "assets": row.assets_json or {}, "links": [{"rel": "self", "href": f"{base_path}/collections/{row.collection_id}/items/{row.id}", "type": "application/geo+json"}, {"rel": "collection", "href": f"{base_path}/collections/{row.collection_id}", "type": "application/json"}, *list(row.links_json or [])]}


def spatial_mode_for_session(db: Session) -> str:
    """Report active spatial support without inferring PostGIS from PostgreSQL alone."""
    dialect = db.get_bind().dialect.name
    if dialect != "postgresql":
        return "portable_geojson"
    try:
        db.execute(text("SELECT PostGIS_Version()"))
        return "native_postgis"
    except Exception:
        # A failed capability probe aborts PostgreSQL transactions; reset it so
        # portable GeoJSON queries remain usable.
        db.rollback()
        return "portable_geojson_postgresql"


def fabric_stats(db: Session, *, dialect: str = "unknown", spatial_mode: str | None = None) -> dict[str, Any]:
    def count(model) -> int: return int(db.scalar(select(func.count()).select_from(model)) or 0)
    formats = {key: int(value) for key, value in db.execute(select(ScientificDataAsset.format, func.count(ScientificDataAsset.id)).group_by(ScientificDataAsset.format)).all()}
    layer_types = {key: int(value) for key, value in db.execute(select(MapLayer.layer_type, func.count(MapLayer.id)).group_by(MapLayer.layer_type)).all()}
    active_spatial_mode = spatial_mode or spatial_mode_for_session(db)
    return {"geospatial_features": count(GeospatialFeature), "time_series": count(TimeSeriesDefinition), "time_series_points": count(TimeSeriesPoint), "scientific_assets": count(ScientificDataAsset), "map_layers": count(MapLayer), "stac_collections": count(StacCollection), "stac_items": count(StacItem), "assets_by_format": formats, "map_layers_by_type": layer_types, "database_dialect": dialect, "postgis_mode": active_spatial_mode, "time_series_partitioning": "monthly_partition_key_with_postgresql_brin" if dialect == "postgresql" else "monthly_partition_key"}
