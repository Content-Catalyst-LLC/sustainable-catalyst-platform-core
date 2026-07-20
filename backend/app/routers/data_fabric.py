from __future__ import annotations

from datetime import datetime
from fastapi import APIRouter, Depends, Query, Request
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from ..dependencies import get_session, require_read, require_write
from ..public_api_auth import PublicApiContext, require_public_scope
from ..schemas import (
    DataFabricStats,
    GeospatialFeatureRead,
    MapLayerRead,
    PublicEnvelope,
    ScientificDataAssetRead,
    TimeSeriesDefinitionRead,
    TimeSeriesPointRead,
)
from ..services.data_fabric import (
    DATA_FORMAT_CAPABILITIES,
    MAP_LAYER_TYPES,
    asset_or_404,
    backfill_fabric,
    fabric_stats,
    feature_collection,
    feature_or_404,
    list_assets,
    list_features,
    list_map_layers,
    list_points,
    list_series,
    list_stac_collections,
    search_stac_items,
    series_or_404,
    spatial_mode_for_session,
    stac_collection_document,
    stac_collection_or_404,
    stac_item_document,
    stac_item_or_404,
)

router = APIRouter(prefix="/v1/fabric", tags=["Geospatial, Time-Series, and Scientific Data Fabric"])
public_router = APIRouter(prefix="/api/v1/fabric", tags=["Unified Public API — Data Fabric"])
stac_router = APIRouter(prefix="/v1/stac", tags=["STAC Catalog"])
public_stac_router = APIRouter(prefix="/api/v1/stac", tags=["Unified Public API — STAC"])


def envelope(request: Request, data, *, meta: dict | None = None) -> PublicEnvelope:
    payload_meta = {"api_version": "v1", "request_id": request.state.request_id, "documentation": "/docs#tag/Unified-Public-API-Data-Fabric"}
    if meta: payload_meta.update(meta)
    return PublicEnvelope(data=jsonable_encoder(data), meta=payload_meta)


def parse_bbox(value: str | None) -> list[float] | None:
    if not value: return None
    parts = [part.strip() for part in value.split(",")]
    if len(parts) != 4: return None
    try: return [float(part) for part in parts]
    except ValueError: return None


@router.get("/capabilities", response_model=dict, dependencies=[Depends(require_read)])
def capabilities(request: Request, db: Session = Depends(get_session)):
    dialect = request.app.state.database.engine.dialect.name
    return {"formats": DATA_FORMAT_CAPABILITIES, "map_layer_types": MAP_LAYER_TYPES, "database_dialect": dialect, "postgis_mode": spatial_mode_for_session(db), "stac_version": "1.0.0", "geojson": True, "time_series_partition_key": "YYYY-MM"}


@router.get("/stats", response_model=DataFabricStats, dependencies=[Depends(require_read)])
def stats(request: Request, db: Session = Depends(get_session)):
    return fabric_stats(db, dialect=request.app.state.database.engine.dialect.name, spatial_mode=spatial_mode_for_session(db))


@router.post("/materialize", response_model=dict, dependencies=[Depends(require_write)])
def materialize(db: Session = Depends(get_session)):
    return backfill_fabric(db)


@router.get("/features", response_model=dict, dependencies=[Depends(require_read)])
def features(source_id: str | None = None, connector_id: str | None = None, dataset_id: str | None = None, feature_type: str | None = None, geometry_type: str | None = None, bbox: str | None = None, start: datetime | None = None, end: datetime | None = None, limit: int = Query(default=100, ge=1, le=1000), offset: int = Query(default=0, ge=0), db: Session = Depends(get_session)):
    rows, total = list_features(db, source_id=source_id, connector_id=connector_id, dataset_id=dataset_id, feature_type=feature_type, geometry_type=geometry_type, bbox=parse_bbox(bbox), start=start, end=end, limit=limit, offset=offset)
    return {"items": [GeospatialFeatureRead.model_validate(row).model_dump(mode="json", by_alias=True) for row in rows], "total": total, "limit": limit, "offset": offset}


@router.get("/features.geojson", dependencies=[Depends(require_read)])
def features_geojson(source_id: str | None = None, connector_id: str | None = None, dataset_id: str | None = None, feature_type: str | None = None, geometry_type: str | None = None, bbox: str | None = None, start: datetime | None = None, end: datetime | None = None, limit: int = Query(default=1000, ge=1, le=5000), offset: int = Query(default=0, ge=0), db: Session = Depends(get_session)):
    rows, total = list_features(db, source_id=source_id, connector_id=connector_id, dataset_id=dataset_id, feature_type=feature_type, geometry_type=geometry_type, bbox=parse_bbox(bbox), start=start, end=end, limit=limit, offset=offset)
    payload = feature_collection(rows); payload["numberMatched"] = total; payload["numberReturned"] = len(rows)
    return JSONResponse(payload, media_type="application/geo+json")


@router.get("/features/{feature_id}", response_model=GeospatialFeatureRead, dependencies=[Depends(require_read)])
def feature(feature_id: str, db: Session = Depends(get_session)):
    return feature_or_404(db, feature_id)


@router.get("/timeseries", response_model=dict, dependencies=[Depends(require_read)])
def timeseries(source_id: str | None = None, connector_id: str | None = None, metric: str | None = None, domain: str | None = None, dataset_id: str | None = None, geography_code: str | None = None, limit: int = Query(default=100, ge=1, le=1000), offset: int = Query(default=0, ge=0), db: Session = Depends(get_session)):
    rows, total = list_series(db, source_id=source_id, connector_id=connector_id, metric=metric, domain=domain, dataset_id=dataset_id, geography_code=geography_code, limit=limit, offset=offset)
    return {"items": [TimeSeriesDefinitionRead.model_validate(row).model_dump(mode="json", by_alias=True) for row in rows], "total": total, "limit": limit, "offset": offset}


@router.get("/timeseries/{series_id}", response_model=TimeSeriesDefinitionRead, dependencies=[Depends(require_read)])
def timeseries_record(series_id: str, db: Session = Depends(get_session)):
    return series_or_404(db, series_id)


@router.get("/timeseries/{series_id}/points", response_model=dict, dependencies=[Depends(require_read)])
def timeseries_points(series_id: str, start: datetime | None = None, end: datetime | None = None, limit: int = Query(default=1000, ge=1, le=10000), offset: int = Query(default=0, ge=0), db: Session = Depends(get_session)):
    series_or_404(db, series_id)
    rows, total = list_points(db, series_id, start=start, end=end, limit=limit, offset=offset)
    return {"items": [TimeSeriesPointRead.model_validate(row).model_dump(mode="json", by_alias=True) for row in rows], "total": total, "limit": limit, "offset": offset}


@router.get("/assets", response_model=dict, dependencies=[Depends(require_read)])
def assets(source_id: str | None = None, connector_id: str | None = None, scientific_record_id: str | None = None, dataset_id: str | None = None, format: str | None = None, asset_role: str | None = None, limit: int = Query(default=100, ge=1, le=1000), offset: int = Query(default=0, ge=0), db: Session = Depends(get_session)):
    rows, total = list_assets(db, source_id=source_id, connector_id=connector_id, scientific_record_id=scientific_record_id, dataset_id=dataset_id, format=format, asset_role=asset_role, limit=limit, offset=offset)
    return {"items": [ScientificDataAssetRead.model_validate(row).model_dump(mode="json", by_alias=True) for row in rows], "total": total, "limit": limit, "offset": offset}


@router.get("/assets/{asset_id}", response_model=ScientificDataAssetRead, dependencies=[Depends(require_read)])
def asset(asset_id: str, db: Session = Depends(get_session)):
    return asset_or_404(db, asset_id)


@router.get("/map-layers", response_model=dict, dependencies=[Depends(require_read)])
def map_layers(source_id: str | None = None, layer_type: str | None = None, status: str | None = "active", limit: int = Query(default=100, ge=1, le=1000), offset: int = Query(default=0, ge=0), db: Session = Depends(get_session)):
    rows, total = list_map_layers(db, source_id=source_id, layer_type=layer_type, status=status, limit=limit, offset=offset)
    return {"items": [MapLayerRead.model_validate(row).model_dump(mode="json", by_alias=True) for row in rows], "total": total, "limit": limit, "offset": offset}


@public_router.get("/capabilities", response_model=PublicEnvelope)
def public_capabilities(request: Request, _context: PublicApiContext = Depends(require_public_scope("data:read")), db: Session = Depends(get_session)):
    dialect = request.app.state.database.engine.dialect.name
    return envelope(request, {"formats": DATA_FORMAT_CAPABILITIES, "map_layer_types": MAP_LAYER_TYPES, "database_dialect": dialect, "postgis_mode": spatial_mode_for_session(db), "stac_version": "1.0.0"})


@public_router.get("/features", response_model=PublicEnvelope)
def public_features(request: Request, source_id: str | None = None, connector_id: str | None = None, dataset_id: str | None = None, feature_type: str | None = None, geometry_type: str | None = None, bbox: str | None = None, start: datetime | None = None, end: datetime | None = None, limit: int = Query(default=100, ge=1), offset: int = Query(default=0, ge=0), context: PublicApiContext = Depends(require_public_scope("data:read")), db: Session = Depends(get_session)):
    limit = min(limit, context.plan.max_page_size, request.app.state.settings.page_size_max)
    rows, total = list_features(db, source_id=source_id, connector_id=connector_id, dataset_id=dataset_id, feature_type=feature_type, geometry_type=geometry_type, bbox=parse_bbox(bbox), start=start, end=end, public_only=True, limit=limit, offset=offset)
    return envelope(request, [GeospatialFeatureRead.model_validate(row) for row in rows], meta={"pagination": {"total": total, "limit": limit, "offset": offset}})


@public_router.get("/features.geojson")
def public_features_geojson(request: Request, source_id: str | None = None, connector_id: str | None = None, dataset_id: str | None = None, feature_type: str | None = None, geometry_type: str | None = None, bbox: str | None = None, start: datetime | None = None, end: datetime | None = None, limit: int = Query(default=500, ge=1), offset: int = Query(default=0, ge=0), context: PublicApiContext = Depends(require_public_scope("data:read")), db: Session = Depends(get_session)):
    limit = min(limit, context.plan.max_page_size, request.app.state.settings.page_size_max)
    rows, total = list_features(db, source_id=source_id, connector_id=connector_id, dataset_id=dataset_id, feature_type=feature_type, geometry_type=geometry_type, bbox=parse_bbox(bbox), start=start, end=end, public_only=True, limit=limit, offset=offset)
    payload = feature_collection(rows); payload["numberMatched"] = total; payload["numberReturned"] = len(rows)
    return JSONResponse(payload, media_type="application/geo+json")


@public_router.get("/timeseries", response_model=PublicEnvelope)
def public_timeseries(request: Request, source_id: str | None = None, connector_id: str | None = None, metric: str | None = None, domain: str | None = None, dataset_id: str | None = None, geography_code: str | None = None, limit: int = Query(default=100, ge=1), offset: int = Query(default=0, ge=0), context: PublicApiContext = Depends(require_public_scope("data:read")), db: Session = Depends(get_session)):
    limit = min(limit, context.plan.max_page_size, request.app.state.settings.page_size_max)
    rows, total = list_series(db, source_id=source_id, connector_id=connector_id, metric=metric, domain=domain, dataset_id=dataset_id, geography_code=geography_code, public_only=True, limit=limit, offset=offset)
    return envelope(request, [TimeSeriesDefinitionRead.model_validate(row) for row in rows], meta={"pagination": {"total": total, "limit": limit, "offset": offset}})


@public_router.get("/timeseries/{series_id}/points", response_model=PublicEnvelope)
def public_timeseries_points(request: Request, series_id: str, start: datetime | None = None, end: datetime | None = None, limit: int = Query(default=1000, ge=1), offset: int = Query(default=0, ge=0), context: PublicApiContext = Depends(require_public_scope("data:read")), db: Session = Depends(get_session)):
    series_or_404(db, series_id, public_only=True)
    limit = min(limit, context.plan.max_page_size, request.app.state.settings.page_size_max)
    rows, total = list_points(db, series_id, start=start, end=end, public_only=True, limit=limit, offset=offset)
    return envelope(request, [TimeSeriesPointRead.model_validate(row) for row in rows], meta={"pagination": {"total": total, "limit": limit, "offset": offset}})


@public_router.get("/assets", response_model=PublicEnvelope)
def public_assets(request: Request, source_id: str | None = None, connector_id: str | None = None, scientific_record_id: str | None = None, dataset_id: str | None = None, format: str | None = None, asset_role: str | None = None, limit: int = Query(default=100, ge=1), offset: int = Query(default=0, ge=0), context: PublicApiContext = Depends(require_public_scope("data:read")), db: Session = Depends(get_session)):
    limit = min(limit, context.plan.max_page_size, request.app.state.settings.page_size_max)
    rows, total = list_assets(db, source_id=source_id, connector_id=connector_id, scientific_record_id=scientific_record_id, dataset_id=dataset_id, format=format, asset_role=asset_role, public_only=True, limit=limit, offset=offset)
    return envelope(request, [ScientificDataAssetRead.model_validate(row) for row in rows], meta={"pagination": {"total": total, "limit": limit, "offset": offset}})


@public_router.get("/map-layers", response_model=PublicEnvelope)
def public_map_layers(request: Request, source_id: str | None = None, layer_type: str | None = None, limit: int = Query(default=100, ge=1), offset: int = Query(default=0, ge=0), context: PublicApiContext = Depends(require_public_scope("data:read")), db: Session = Depends(get_session)):
    limit = min(limit, context.plan.max_page_size, request.app.state.settings.page_size_max)
    rows, total = list_map_layers(db, source_id=source_id, layer_type=layer_type, status="active", public_only=True, limit=limit, offset=offset)
    return envelope(request, [MapLayerRead.model_validate(row) for row in rows], meta={"pagination": {"total": total, "limit": limit, "offset": offset}})


@stac_router.get("")
def stac_root(request: Request, _read=Depends(require_read)):
    return {"stac_version": "1.0.0", "type": "Catalog", "id": "sustainable-catalyst-core", "title": "Sustainable Catalyst Data Fabric", "description": "Source-aware scientific and geospatial records generated by Sustainable Catalyst Core.", "links": [{"rel": "self", "href": "/v1/stac", "type": "application/json"}, {"rel": "data", "href": "/v1/stac/collections", "type": "application/json"}, {"rel": "search", "href": "/v1/stac/search", "type": "application/geo+json", "method": "GET"}]}


@stac_router.get("/collections")
def stac_collections(limit: int = Query(default=100, ge=1, le=1000), offset: int = Query(default=0, ge=0), _read=Depends(require_read), db: Session = Depends(get_session)):
    rows, total = list_stac_collections(db, limit=limit, offset=offset)
    return {"collections": [stac_collection_document(row) for row in rows], "links": [], "numberMatched": total, "numberReturned": len(rows)}


@stac_router.get("/collections/{collection_id}")
def stac_collection(collection_id: str, _read=Depends(require_read), db: Session = Depends(get_session)):
    return stac_collection_document(stac_collection_or_404(db, collection_id))


@stac_router.get("/collections/{collection_id}/items")
def stac_items(collection_id: str, bbox: str | None = None, start: datetime | None = None, end: datetime | None = None, limit: int = Query(default=100, ge=1, le=1000), offset: int = Query(default=0, ge=0), _read=Depends(require_read), db: Session = Depends(get_session)):
    stac_collection_or_404(db, collection_id)
    rows, total = search_stac_items(db, collections=[collection_id], bbox=parse_bbox(bbox), start=start, end=end, limit=limit, offset=offset)
    return JSONResponse({"type": "FeatureCollection", "features": [stac_item_document(row) for row in rows], "links": [], "numberMatched": total, "numberReturned": len(rows)}, media_type="application/geo+json")


@stac_router.get("/collections/{collection_id}/items/{item_id}")
def stac_item(collection_id: str, item_id: str, _read=Depends(require_read), db: Session = Depends(get_session)):
    return JSONResponse(stac_item_document(stac_item_or_404(db, collection_id, item_id)), media_type="application/geo+json")


@stac_router.get("/search")
def stac_search(collections: str | None = None, bbox: str | None = None, start: datetime | None = None, end: datetime | None = None, query: str | None = None, limit: int = Query(default=100, ge=1, le=1000), offset: int = Query(default=0, ge=0), _read=Depends(require_read), db: Session = Depends(get_session)):
    rows, total = search_stac_items(db, collections=[part for part in (collections or "").split(",") if part] or None, bbox=parse_bbox(bbox), start=start, end=end, query=query, limit=limit, offset=offset)
    return JSONResponse({"type": "FeatureCollection", "features": [stac_item_document(row) for row in rows], "links": [], "numberMatched": total, "numberReturned": len(rows)}, media_type="application/geo+json")


@public_stac_router.get("")
def public_stac_root(request: Request, _context: PublicApiContext = Depends(require_public_scope("data:read"))):
    return {"stac_version": "1.0.0", "type": "Catalog", "id": "sustainable-catalyst-core-public", "title": "Sustainable Catalyst Public Data Fabric", "description": "Public source-aware scientific and geospatial records.", "links": [{"rel": "self", "href": "/api/v1/stac", "type": "application/json"}, {"rel": "data", "href": "/api/v1/stac/collections", "type": "application/json"}, {"rel": "search", "href": "/api/v1/stac/search", "type": "application/geo+json", "method": "GET"}]}


@public_stac_router.get("/collections")
def public_stac_collections(limit: int = Query(default=100, ge=1), offset: int = Query(default=0, ge=0), context: PublicApiContext = Depends(require_public_scope("data:read")), db: Session = Depends(get_session)):
    limit = min(limit, context.plan.max_page_size)
    rows, total = list_stac_collections(db, public_only=True, limit=limit, offset=offset)
    return {"collections": [stac_collection_document(row, "/api/v1/stac") for row in rows], "links": [], "numberMatched": total, "numberReturned": len(rows)}



@public_stac_router.get("/collections/{collection_id}")
def public_stac_collection(collection_id: str, _context: PublicApiContext = Depends(require_public_scope("data:read")), db: Session = Depends(get_session)):
    return stac_collection_document(stac_collection_or_404(db, collection_id, public_only=True), "/api/v1/stac")


@public_stac_router.get("/collections/{collection_id}/items")
def public_stac_items(collection_id: str, bbox: str | None = None, start: datetime | None = None, end: datetime | None = None, limit: int = Query(default=100, ge=1), offset: int = Query(default=0, ge=0), context: PublicApiContext = Depends(require_public_scope("data:read")), db: Session = Depends(get_session)):
    stac_collection_or_404(db, collection_id, public_only=True)
    limit = min(limit, context.plan.max_page_size)
    rows, total = search_stac_items(db, collections=[collection_id], bbox=parse_bbox(bbox), start=start, end=end, public_only=True, limit=limit, offset=offset)
    return JSONResponse({"type": "FeatureCollection", "features": [stac_item_document(row, "/api/v1/stac") for row in rows], "links": [], "numberMatched": total, "numberReturned": len(rows)}, media_type="application/geo+json")


@public_stac_router.get("/collections/{collection_id}/items/{item_id}")
def public_stac_item(collection_id: str, item_id: str, _context: PublicApiContext = Depends(require_public_scope("data:read")), db: Session = Depends(get_session)):
    return JSONResponse(stac_item_document(stac_item_or_404(db, collection_id, item_id, public_only=True), "/api/v1/stac"), media_type="application/geo+json")


@public_stac_router.get("/search")
def public_stac_search(collections: str | None = None, bbox: str | None = None, start: datetime | None = None, end: datetime | None = None, query: str | None = None, limit: int = Query(default=100, ge=1), offset: int = Query(default=0, ge=0), context: PublicApiContext = Depends(require_public_scope("data:read")), db: Session = Depends(get_session)):
    limit = min(limit, context.plan.max_page_size)
    rows, total = search_stac_items(db, collections=[part for part in (collections or "").split(",") if part] or None, bbox=parse_bbox(bbox), start=start, end=end, query=query, public_only=True, limit=limit, offset=offset)
    return JSONResponse({"type": "FeatureCollection", "features": [stac_item_document(row, "/api/v1/stac") for row in rows], "links": [], "numberMatched": total, "numberReturned": len(rows)}, media_type="application/geo+json")
