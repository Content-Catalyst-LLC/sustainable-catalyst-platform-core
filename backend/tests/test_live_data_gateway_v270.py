from __future__ import annotations

from datetime import datetime, timezone

import httpx

from app.connectors.adapters import ADAPTERS
from app.models import ApiPlan, LiveDataObservation
from app.services.live_data import LiveDataRuntime


def test_seeded_free_source_and_connector_catalog(client):
    sources = client.get("/v1/live/sources")
    assert sources.status_code == 200
    source_ids = {item["id"] for item in sources.json()}
    assert {
        "met-norway",
        "nasa-earthdata",
        "usgs",
        "world-bank",
        "fred",
        "un-statistics",
    } <= source_ids
    assert all(item["access_cost"] == "free" for item in sources.json())
    assert all(item["credit_card_required"] is False for item in sources.json())

    connectors = client.get("/v1/live/connectors")
    assert connectors.status_code == 200
    connector_ids = {item["id"] for item in connectors.json()}
    assert {
        "met-no.locationforecast",
        "nasa.gibs-wmts",
        "usgs.earthquakes",
        "world-bank.indicators",
        "fred.series-observations",
        "un.sdg-catalog",
    } <= connector_ids


def test_live_data_health_reports_optional_fred_credential(client):
    response = client.get("/v1/live/connectors/health")
    assert response.status_code == 200
    payload = response.json()
    assert payload["enabled"] is True
    assert payload["strict_free_sources"] is True
    assert payload["overall_status"] == "operational_with_configuration_required"
    statuses = {item["id"]: item["configuration_status"] for item in payload["connectors"]}
    assert statuses["fred.series-observations"] == "credential_required"
    assert statuses["usgs.earthquakes"] == "configured"


def test_paid_source_is_rejected_by_strict_free_gate(client, write_headers):
    response = client.post(
        "/v1/live/sources",
        headers=write_headers,
        json={
            "id": "paid-provider",
            "name": "Paid Provider",
            "organization": "Example",
            "access_cost": "paid",
            "credit_card_required": True,
            "review_status": "EXCLUDED_PAID",
            "active": True,
        },
    )
    assert response.status_code == 422
    assert "free" in response.json()["detail"].lower()


def test_unknown_connector_adapter_is_rejected(client, write_headers):
    response = client.post(
        "/v1/live/connectors",
        headers=write_headers,
        json={
            "id": "usgs.invalid",
            "source_id": "usgs",
            "name": "Invalid",
            "domain": "hazards",
            "adapter": "does_not_exist",
            "base_url": "https://example.test/api",
        },
    )
    assert response.status_code == 422
    assert "adapter" in response.json()["detail"].lower()


def test_usgs_ingestion_persists_hash_provenance_and_deduplicates(client, write_headers):
    payload = {
        "type": "FeatureCollection",
        "metadata": {"generated": 1784044800000, "title": "USGS All Earthquakes, Past Hour"},
        "features": [
            {
                "type": "Feature",
                "id": "us-test-1",
                "geometry": {"type": "Point", "coordinates": [-122.1, 37.4, 8.5]},
                "properties": {
                    "mag": 3.2,
                    "magType": "ml",
                    "place": "Test Region",
                    "time": 1784044500000,
                    "updated": 1784044700000,
                    "status": "reviewed",
                    "alert": None,
                    "tsunami": 0,
                    "felt": 4,
                    "title": "M 3.2 - Test Region",
                    "url": "https://earthquake.usgs.gov/earthquakes/eventpage/us-test-1",
                    "detail": "https://earthquake.usgs.gov/earthquakes/feed/v1.0/detail/us-test-1.geojson",
                },
            }
        ],
    }

    async def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path.endswith("/all_hour.geojson")
        return httpx.Response(200, json=payload)

    client.app.state.live_data_runtime = LiveDataRuntime(
        client.app.state.settings,
        transport=httpx.MockTransport(handler),
    )
    first = client.post(
        "/v1/live/connectors/usgs.earthquakes/ingest",
        headers=write_headers,
        json={"parameters": {"feed": "all_hour"}, "requested_by": "pytest"},
    )
    assert first.status_code == 200, first.text
    assert first.json()["status"] == "completed"
    assert first.json()["records_created"] == 1
    assert len(first.json()["raw_content_hash"]) == 64

    second = client.post(
        "/v1/live/connectors/usgs.earthquakes/ingest",
        headers=write_headers,
        json={"parameters": {"feed": "all_hour"}, "requested_by": "pytest"},
    )
    assert second.status_code == 200, second.text
    assert second.json()["records_created"] == 0
    assert second.json()["records_updated"] == 1

    latest = client.get("/v1/live/observations/latest?connector_id=usgs.earthquakes")
    assert latest.status_code == 200
    assert latest.json()["total"] == 1
    observation = latest.json()["items"][0]
    assert observation["metric"] == "earthquake_magnitude"
    assert observation["value_number"] == 3.2
    assert observation["geometry"]["coordinates"] == [-122.1, 37.4]
    assert observation["dimensions"]["depth_km"] == 8.5
    assert observation["attribution"] == "U.S. Geological Survey"

    provenance = client.get(f"/v1/live/provenance/{observation['id']}")
    assert provenance.status_code == 200
    assert provenance.json()["raw_record"]["content_hash"] == observation["raw_record_hash"]
    assert provenance.json()["source"]["id"] == "usgs"
    assert provenance.json()["connector"]["id"] == "usgs.earthquakes"


def test_world_bank_adapter_normalizes_indicator_timeseries(client, write_headers):
    payload = [
        {"page": 1, "pages": 1, "per_page": 1000, "total": 2},
        [
            {
                "indicator": {"id": "SP.POP.TOTL", "value": "Population, total"},
                "country": {"id": "US", "value": "United States"},
                "countryiso3code": "USA",
                "date": "2025",
                "value": 340000000,
                "unit": "people",
                "obs_status": "",
                "decimal": 0,
            },
            {
                "indicator": {"id": "SP.POP.TOTL", "value": "Population, total"},
                "country": {"id": "US", "value": "United States"},
                "countryiso3code": "USA",
                "date": "2024",
                "value": 338000000,
                "unit": "people",
                "obs_status": "",
                "decimal": 0,
            },
        ],
    ]

    async def handler(request: httpx.Request) -> httpx.Response:
        assert "/country/USA/indicator/SP.POP.TOTL" in request.url.path
        return httpx.Response(200, json=payload)

    client.app.state.live_data_runtime = LiveDataRuntime(
        client.app.state.settings,
        transport=httpx.MockTransport(handler),
    )
    response = client.post(
        "/v1/live/connectors/world-bank.indicators/ingest",
        headers=write_headers,
        json={
            "parameters": {"country": "USA", "indicator": "SP.POP.TOTL"},
            "requested_by": "pytest",
        },
    )
    assert response.status_code == 200, response.text
    assert response.json()["records_created"] == 2

    series = client.get("/v1/live/timeseries?metric=SP.POP.TOTL")
    assert series.status_code == 200
    assert series.json()["total"] == 2
    assert series.json()["items"][0]["freshness_status"] == "latest_release"
    assert series.json()["items"][0]["dimensions"]["country_iso3"] == "USA"


def test_met_and_un_adapters_are_registered():
    assert "met_locationforecast_v2" in ADAPTERS
    assert "un_sdg_catalog_v1" in ADAPTERS
    assert "nasa_gibs_wmts_v1" in ADAPTERS


def test_data_read_scope_is_seeded_for_all_plans(client):
    with client.app.state.database.session_factory() as db:
        plans = db.query(ApiPlan).all()
        assert plans
        assert all("data:read" in plan.allowed_scopes for plan in plans)


def test_registry_stats_include_live_data_counts(client):
    response = client.get("/v1/stats")
    assert response.status_code == 200
    payload = response.json()
    assert payload["live_data_sources"] == 40
    assert payload["live_data_connectors"] == 39
    assert payload["live_data_ingestion_runs"] == 0
    assert payload["live_data_observations"] == 0
    assert payload["international_law_records"] == 0


def test_health_advertises_live_data_gateway(client):
    health = client.get("/health").json()
    assert health["version"] == "2.7.3"
    assert health["live_data_gateway"] is True
    assert health["strict_free_sources"] is True

    meta = client.get("/v1/meta").json()
    assert "free_live_data_gateway" in meta["capabilities"]
    assert "server_sent_live_data_events" in meta["deferred_capabilities"]


def _create_public_key(client, write_headers, scopes):
    application = client.post(
        "/v1/developer/applications",
        headers=write_headers,
        json={
            "name": "Live Data Test Application",
            "owner_name": "Test Developer",
            "owner_email": "live-data@example.com",
            "organization": "Example Organization",
            "website_url": "https://example.com",
            "use_case": "Read reviewed free live-data source and connector metadata for a public research dashboard.",
            "status": "approved",
            "plan_id": "free",
            "metadata": {},
            "actor": "platform-administrator",
        },
    )
    assert application.status_code == 201, application.text
    issued = client.post(
        f"/v1/developer/applications/{application.json()['id']}/credentials",
        headers=write_headers,
        json={
            "label": "Live data key",
            "scopes": scopes,
            "created_by": "platform-administrator",
            "metadata": {},
        },
    )
    assert issued.status_code == 201, issued.text
    return issued.json()["api_key"]


def test_scoped_public_live_data_api_sanitizes_connector_configuration(client, write_headers):
    key = _create_public_key(client, write_headers, ["data:read"])
    headers = {"Authorization": f"Bearer {key}"}

    sources = client.get("/api/v1/live/sources", headers=headers)
    assert sources.status_code == 200
    assert sources.json()["meta"]["api_version"] == "v1"
    assert len(sources.json()["data"]) == 40

    connectors = client.get("/api/v1/live/connectors", headers=headers)
    assert connectors.status_code == 200
    assert len(connectors.json()["data"]) == 39
    for connector in connectors.json()["data"]:
        assert "base_url" not in connector
        assert "adapter" not in connector
        assert "configuration" not in connector


def test_public_live_data_api_enforces_data_read_scope(client, write_headers):
    key = _create_public_key(client, write_headers, ["public:status"])
    response = client.get(
        "/api/v1/live/sources",
        headers={"Authorization": f"Bearer {key}"},
    )
    assert response.status_code == 403
    assert "data:read" in response.json()["detail"]


def test_met_adapter_builds_identified_request_and_normalizes_forecast():
    from types import SimpleNamespace
    from app.connectors.adapters import MetLocationforecastAdapter

    adapter = MetLocationforecastAdapter()
    connector = SimpleNamespace(base_url="https://api.met.no/weatherapi/locationforecast/2.0/compact")
    settings = SimpleNamespace(live_data_user_agent="SustainableCatalyst/2.7 test@example.com")
    request = adapter.build_request(connector, {"lat": 41.8781, "lon": -87.6298}, settings)
    assert request.headers["User-Agent"] == settings.live_data_user_agent
    assert request.params["lat"] == 41.8781

    response = httpx.Response(
        200,
        request=httpx.Request("GET", request.url),
        json={
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [-87.6298, 41.8781, 181]},
            "properties": {
                "meta": {"updated_at": "2026-07-14T18:00:00Z"},
                "timeseries": [
                    {
                        "time": "2026-07-14T19:00:00Z",
                        "data": {
                            "instant": {
                                "details": {
                                    "air_temperature": 29.2,
                                    "relative_humidity": 54.0,
                                    "wind_speed": 4.2,
                                }
                            }
                        },
                    }
                ],
            },
        },
    )
    _, observations = adapter.normalize(
        response,
        connector=connector,
        parameters={"lat": 41.8781, "lon": -87.6298},
        retrieved_at=datetime(2026, 7, 14, 18, 30, tzinfo=timezone.utc),
    )
    metrics = {item.metric for item in observations}
    assert {"air_temperature", "relative_humidity", "wind_speed"} <= metrics
    assert all(item.freshness_status == "forecast" for item in observations)


def test_nasa_gibs_adapter_normalizes_wmts_layer_catalog():
    from types import SimpleNamespace
    from app.connectors.adapters import NasaGibsWmtsAdapter

    xml = b'''<?xml version="1.0" encoding="UTF-8"?>
    <Capabilities xmlns="http://www.opengis.net/wmts/1.0" xmlns:ows="http://www.opengis.net/ows/1.1">
      <Contents>
        <Layer>
          <ows:Title>Corrected Reflectance</ows:Title>
          <ows:Identifier>MODIS_Terra_CorrectedReflectance_TrueColor</ows:Identifier>
          <Format>image/jpeg</Format>
          <TileMatrixSetLink><TileMatrixSet>250m</TileMatrixSet></TileMatrixSetLink>
          <Dimension><ows:Identifier>Time</ows:Identifier><Default>2026-07-14</Default><Value>2026-07-14</Value></Dimension>
          <ResourceURL format="image/jpeg" resourceType="tile" template="https://example/{Time}/{TileMatrix}.jpg" />
        </Layer>
      </Contents>
    </Capabilities>'''
    response = httpx.Response(
        200,
        content=xml,
        request=httpx.Request("GET", "https://gibs.earthdata.nasa.gov/wmts/capabilities.xml"),
        headers={"content-type": "application/xml"},
    )
    connector = SimpleNamespace(configuration_json={"projection": "EPSG:4326"})
    _, observations = NasaGibsWmtsAdapter().normalize(
        response,
        connector=connector,
        parameters={},
        retrieved_at=datetime(2026, 7, 14, 20, 0, tzinfo=timezone.utc),
    )
    assert len(observations) == 1
    assert observations[0].metric == "wmts_layer_available"
    assert observations[0].value_text == "MODIS_Terra_CorrectedReflectance_TrueColor"
    assert observations[0].dimensions["projection"] == "EPSG:4326"


def test_un_sdg_adapter_uses_current_v5_catalog_routes():
    from types import SimpleNamespace
    from app.connectors.adapters import UnSdgCatalogAdapter

    connector = SimpleNamespace(
        base_url="https://unstats.un.org/sdgs/UNSDGAPIV5/v1/sdg",
        configuration_json={"default_resource": "goals", "allowed_resources": ["goals", "series"]},
    )
    settings = SimpleNamespace(live_data_user_agent="SustainableCatalyst/2.7 test@example.com")
    adapter = UnSdgCatalogAdapter()
    goals = adapter.build_request(connector, {"resource": "goals"}, settings)
    series = adapter.build_request(
        connector,
        {"resource": "series", "indicator_code": "1.1.1"},
        settings,
    )
    assert goals.url.endswith("/Goal/List")
    assert series.url.endswith("/Indicator/1.1.1/Series/List")
