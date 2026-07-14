from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
import math
from typing import Any
from urllib.parse import quote
import xml.etree.ElementTree as ET

import httpx


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def parse_datetime(value: Any, *, default: datetime | None = None) -> datetime:
    if isinstance(value, datetime):
        result = value
    elif isinstance(value, (int, float)):
        timestamp = float(value)
        if timestamp > 10_000_000_000:
            timestamp /= 1000.0
        result = datetime.fromtimestamp(timestamp, tz=timezone.utc)
    elif isinstance(value, str) and value.strip():
        clean = value.strip().replace("Z", "+00:00")
        try:
            result = datetime.fromisoformat(clean)
        except ValueError:
            if len(clean) == 4 and clean.isdigit():
                result = datetime(int(clean), 12, 31, tzinfo=timezone.utc)
            elif len(clean) == 10:
                result = datetime.strptime(clean, "%Y-%m-%d").replace(tzinfo=timezone.utc)
            else:
                raise ValueError(f"Unsupported datetime value: {value}")
    elif default is not None:
        result = default
    else:
        raise ValueError("A datetime value is required.")
    if result.tzinfo is None:
        result = result.replace(tzinfo=timezone.utc)
    return result.astimezone(timezone.utc)


def finite_float(value: Any) -> float | None:
    if value in (None, "", ".", "..", "NaN", "nan"):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


@dataclass(frozen=True)
class ConnectorRequest:
    method: str
    url: str
    params: dict[str, Any] = field(default_factory=dict)
    headers: dict[str, str] = field(default_factory=dict)


@dataclass
class NormalizedObservation:
    source_record_id: str
    domain: str
    metric: str
    observed_at: datetime
    value_number: float | None = None
    value_text: str | None = None
    unit: str | None = None
    geometry: dict[str, Any] | None = None
    dimensions: dict[str, Any] = field(default_factory=dict)
    published_at: datetime | None = None
    freshness_status: str | None = None
    quality_status: str = "source_reported"
    methodology_url: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    public: bool = True


class ConnectorAdapter:
    adapter_id = "base"

    def build_request(self, connector, parameters: dict[str, Any], settings) -> ConnectorRequest:
        raise NotImplementedError

    def normalize(
        self,
        response: httpx.Response,
        *,
        connector,
        parameters: dict[str, Any],
        retrieved_at: datetime,
    ) -> tuple[Any, list[NormalizedObservation]]:
        raise NotImplementedError

    @staticmethod
    def _required(parameters: dict[str, Any], name: str) -> Any:
        value = parameters.get(name)
        if value is None or (isinstance(value, str) and not value.strip()):
            raise ValueError(f"Parameter '{name}' is required.")
        return value


class MetLocationforecastAdapter(ConnectorAdapter):
    adapter_id = "met_locationforecast_v2"
    METRICS = {
        "air_temperature": "celsius",
        "relative_humidity": "percent",
        "wind_speed": "m/s",
        "wind_from_direction": "degrees",
        "air_pressure_at_sea_level": "hPa",
        "cloud_area_fraction": "percent",
        "dew_point_temperature": "celsius",
    }

    def build_request(self, connector, parameters, settings) -> ConnectorRequest:
        lat = float(self._required(parameters, "lat"))
        lon = float(self._required(parameters, "lon"))
        if not -90 <= lat <= 90 or not -180 <= lon <= 180:
            raise ValueError("Latitude or longitude is outside the valid range.")
        return ConnectorRequest(
            method="GET",
            url=connector.base_url,
            params={"lat": round(lat, 5), "lon": round(lon, 5), "altitude": parameters.get("altitude")},
            headers={"User-Agent": settings.live_data_user_agent, "Accept": "application/json"},
        )

    def normalize(self, response, *, connector, parameters, retrieved_at):
        payload = response.json()
        coordinates = payload.get("geometry", {}).get("coordinates") or [float(parameters["lon"]), float(parameters["lat"])]
        geometry = {"type": "Point", "coordinates": coordinates[:2]}
        updated_at = parse_datetime(payload.get("properties", {}).get("meta", {}).get("updated_at"), default=retrieved_at)
        observations: list[NormalizedObservation] = []
        for item in payload.get("properties", {}).get("timeseries", []):
            observed_at = parse_datetime(item.get("time"))
            details = item.get("data", {}).get("instant", {}).get("details", {})
            for metric, unit in self.METRICS.items():
                number = finite_float(details.get(metric))
                if number is None:
                    continue
                observations.append(
                    NormalizedObservation(
                        source_record_id=f"{geometry['coordinates'][1]:.5f},{geometry['coordinates'][0]:.5f}:{observed_at.isoformat()}:{metric}",
                        domain="weather",
                        metric=metric,
                        value_number=number,
                        unit=unit,
                        geometry=geometry,
                        observed_at=observed_at,
                        published_at=updated_at,
                        freshness_status="forecast" if observed_at > retrieved_at else "current",
                        methodology_url="https://api.met.no/weatherapi/locationforecast/2.0/documentation",
                        dimensions={
                            "latitude": geometry["coordinates"][1],
                            "longitude": geometry["coordinates"][0],
                            "altitude": coordinates[2] if len(coordinates) > 2 else None,
                            "forecast_model_updated_at": updated_at.isoformat(),
                        },
                    )
                )
        return payload, observations


class NasaGibsWmtsAdapter(ConnectorAdapter):
    adapter_id = "nasa_gibs_wmts_v1"

    def build_request(self, connector, parameters, settings) -> ConnectorRequest:
        return ConnectorRequest(
            method="GET",
            url=connector.base_url,
            headers={"User-Agent": settings.live_data_user_agent, "Accept": "application/xml,text/xml"},
        )

    def normalize(self, response, *, connector, parameters, retrieved_at):
        content = response.content
        root = ET.fromstring(content)
        observations: list[NormalizedObservation] = []
        for layer in root.findall(".//{*}Contents/{*}Layer"):
            identifier = layer.findtext("{*}Identifier")
            if not identifier:
                continue
            title = layer.findtext("{*}Title") or identifier
            abstract = layer.findtext("{*}Abstract")
            formats = [node.text for node in layer.findall("{*}Format") if node.text]
            matrix_sets = [node.findtext("{*}TileMatrixSet") for node in layer.findall("{*}TileMatrixSetLink")]
            dimensions: dict[str, Any] = {
                "formats": formats,
                "tile_matrix_sets": [value for value in matrix_sets if value],
                "projection": connector.configuration_json.get("projection", "EPSG:4326"),
            }
            observed_at = retrieved_at
            for dimension in layer.findall("{*}Dimension"):
                name = dimension.findtext("{*}Identifier")
                default = dimension.findtext("{*}Default")
                values = [node.text for node in dimension.findall("{*}Value") if node.text]
                if name:
                    dimensions[name] = {"default": default, "values": values[:25]}
                if name and name.lower() == "time" and default:
                    try:
                        observed_at = parse_datetime(default)
                    except ValueError:
                        pass
            resource_templates = [
                node.attrib.get("template") for node in layer.findall("{*}ResourceURL") if node.attrib.get("template")
            ]
            observations.append(
                NormalizedObservation(
                    source_record_id=identifier,
                    domain="earth_observation",
                    metric="wmts_layer_available",
                    value_number=1.0,
                    value_text=identifier,
                    unit="boolean",
                    observed_at=observed_at,
                    published_at=retrieved_at,
                    freshness_status="catalog",
                    quality_status="provider_catalog",
                    methodology_url="https://www.earthdata.nasa.gov/engage/open-data-services-software/earthdata-developer-portal/gibs-api",
                    dimensions=dimensions,
                    metadata={
                        "title": title,
                        "abstract": abstract,
                        "resource_templates": resource_templates,
                    },
                )
            )
        raw_payload = {"xml": content.decode(response.encoding or "utf-8", errors="replace")}
        return raw_payload, observations


class UsgsEarthquakeAdapter(ConnectorAdapter):
    adapter_id = "usgs_earthquakes_geojson_v1"

    def build_request(self, connector, parameters, settings) -> ConnectorRequest:
        feed = str(parameters.get("feed") or connector.configuration_json.get("default_feed", "all_hour"))
        allowed = set(connector.configuration_json.get("allowed_feeds", []))
        if feed not in allowed:
            raise ValueError(f"Unsupported USGS feed '{feed}'.")
        return ConnectorRequest(
            method="GET",
            url=f"{connector.base_url.rstrip('/')}/{quote(feed, safe='')}.geojson",
            headers={"User-Agent": settings.live_data_user_agent, "Accept": "application/geo+json,application/json"},
        )

    def normalize(self, response, *, connector, parameters, retrieved_at):
        payload = response.json()
        published_at = parse_datetime(payload.get("metadata", {}).get("generated"), default=retrieved_at)
        observations: list[NormalizedObservation] = []
        for feature in payload.get("features", []):
            props = feature.get("properties", {})
            event_id = str(feature.get("id") or props.get("code") or "")
            if not event_id:
                continue
            observed_at = parse_datetime(props.get("time"), default=retrieved_at)
            coordinates = (feature.get("geometry") or {}).get("coordinates") or []
            geometry = {"type": "Point", "coordinates": coordinates[:2]} if len(coordinates) >= 2 else None
            magnitude = finite_float(props.get("mag"))
            observations.append(
                NormalizedObservation(
                    source_record_id=event_id,
                    domain="hazards",
                    metric="earthquake_magnitude",
                    value_number=magnitude,
                    unit=props.get("magType") or "magnitude",
                    geometry=geometry,
                    observed_at=observed_at,
                    published_at=published_at,
                    freshness_status="near_real_time",
                    methodology_url="https://earthquake.usgs.gov/earthquakes/feed/v1.0/geojson.php",
                    dimensions={
                        "depth_km": finite_float(coordinates[2]) if len(coordinates) > 2 else None,
                        "place": props.get("place"),
                        "status": props.get("status"),
                        "alert": props.get("alert"),
                        "tsunami": bool(props.get("tsunami")),
                        "felt_reports": props.get("felt"),
                    },
                    metadata={
                        "title": props.get("title"),
                        "detail_url": props.get("detail"),
                        "event_url": props.get("url"),
                        "updated_at": parse_datetime(props.get("updated"), default=published_at).isoformat(),
                    },
                )
            )
        return payload, observations


class WorldBankIndicatorsAdapter(ConnectorAdapter):
    adapter_id = "world_bank_indicators_v2"

    def build_request(self, connector, parameters, settings) -> ConnectorRequest:
        indicator = str(self._required(parameters, "indicator")).strip()
        country = str(parameters.get("country") or connector.configuration_json.get("default_country", "all")).strip()
        params: dict[str, Any] = {
            "format": "json",
            "per_page": min(max(int(parameters.get("per_page", 1000)), 1), 20000),
        }
        if parameters.get("date"):
            params["date"] = str(parameters["date"])
        if parameters.get("source"):
            params["source"] = str(parameters["source"])
        return ConnectorRequest(
            method="GET",
            url=f"{connector.base_url.rstrip('/')}/country/{quote(country, safe=';')}/indicator/{quote(indicator, safe='.')}",
            params=params,
            headers={"User-Agent": settings.live_data_user_agent, "Accept": "application/json"},
        )

    def normalize(self, response, *, connector, parameters, retrieved_at):
        payload = response.json()
        if not isinstance(payload, list) or len(payload) < 2:
            raise ValueError("Unexpected World Bank API response shape.")
        meta, rows = payload[0] or {}, payload[1] or []
        observations: list[NormalizedObservation] = []
        for row in rows:
            indicator = (row.get("indicator") or {}).get("id") or str(parameters.get("indicator"))
            country = row.get("countryiso3code") or (row.get("country") or {}).get("id") or "unknown"
            period = str(row.get("date") or "")
            try:
                observed_at = parse_datetime(period)
            except ValueError:
                continue
            value = finite_float(row.get("value"))
            observations.append(
                NormalizedObservation(
                    source_record_id=f"{country}:{indicator}:{period}",
                    domain="economics",
                    metric=indicator,
                    value_number=value,
                    value_text=None if value is not None else str(row.get("value")) if row.get("value") is not None else None,
                    unit=None,
                    observed_at=observed_at,
                    published_at=retrieved_at,
                    freshness_status="latest_release" if period == str(rows[0].get("date")) else "historical",
                    quality_status="source_reported" if value is not None else "missing",
                    methodology_url="https://datahelpdesk.worldbank.org/knowledgebase/topics/125589-developer-information",
                    dimensions={
                        "country_id": (row.get("country") or {}).get("id"),
                        "country_name": (row.get("country") or {}).get("value"),
                        "country_iso3": row.get("countryiso3code"),
                        "indicator_name": (row.get("indicator") or {}).get("value"),
                        "period": period,
                        "decimal": row.get("decimal"),
                        "unit": row.get("unit"),
                        "obs_status": row.get("obs_status"),
                    },
                    metadata={"api_page": meta.get("page"), "api_pages": meta.get("pages")},
                )
            )
        return payload, observations


class FredSeriesObservationsAdapter(ConnectorAdapter):
    adapter_id = "fred_series_observations_v1"

    def build_request(self, connector, parameters, settings) -> ConnectorRequest:
        if not settings.fred_api_key:
            raise ValueError("SC_CORE_FRED_API_KEY is required for the FRED connector.")
        series_id = str(self._required(parameters, "series_id")).strip()
        params: dict[str, Any] = {
            "series_id": series_id,
            "api_key": settings.fred_api_key,
            "file_type": "json",
            "limit": min(max(int(parameters.get("limit", 1000)), 1), 100000),
            "sort_order": str(parameters.get("sort_order", "desc")),
        }
        for key in ("observation_start", "observation_end", "realtime_start", "realtime_end", "frequency", "aggregation_method"):
            if parameters.get(key) is not None:
                params[key] = str(parameters[key])
        return ConnectorRequest(
            method="GET",
            url=connector.base_url,
            params=params,
            headers={"User-Agent": settings.live_data_user_agent, "Accept": "application/json"},
        )

    def normalize(self, response, *, connector, parameters, retrieved_at):
        payload = response.json()
        series_id = str(parameters["series_id"])
        observations: list[NormalizedObservation] = []
        rows = payload.get("observations", [])
        for index, row in enumerate(rows):
            observed_at = parse_datetime(row.get("date"))
            value = finite_float(row.get("value"))
            observations.append(
                NormalizedObservation(
                    source_record_id=f"{series_id}:{row.get('date')}:{row.get('realtime_start')}:{row.get('realtime_end')}",
                    domain="economics",
                    metric=series_id,
                    value_number=value,
                    value_text=None if value is not None else row.get("value"),
                    observed_at=observed_at,
                    published_at=retrieved_at,
                    freshness_status="latest_release" if index == 0 else "historical",
                    quality_status="source_reported" if value is not None else "missing",
                    methodology_url="https://fred.stlouisfed.org/docs/api/fred/series_observations.html",
                    dimensions={
                        "realtime_start": row.get("realtime_start"),
                        "realtime_end": row.get("realtime_end"),
                        "series_id": series_id,
                    },
                )
            )
        return payload, observations


class UnSdgCatalogAdapter(ConnectorAdapter):
    adapter_id = "un_sdg_catalog_v1"

    def build_request(self, connector, parameters, settings) -> ConnectorRequest:
        resource = str(parameters.get("resource") or connector.configuration_json.get("default_resource", "goals"))
        allowed = set(connector.configuration_json.get("allowed_resources", []))
        if resource not in allowed:
            raise ValueError(f"Unsupported UN SDG catalog resource '{resource}'.")
        if resource == "goals":
            url = f"{connector.base_url.rstrip('/')}/Goal/List"
        else:
            indicator_code = str(self._required(parameters, "indicator_code")).strip()
            url = f"{connector.base_url.rstrip('/')}/Indicator/{quote(indicator_code, safe='.')}/Series/List"
        return ConnectorRequest(
            method="GET",
            url=url,
            headers={"User-Agent": settings.live_data_user_agent, "Accept": "application/json"},
        )

    def normalize(self, response, *, connector, parameters, retrieved_at):
        payload = response.json()
        resource = str(parameters.get("resource") or connector.configuration_json.get("default_resource", "goals"))
        rows = payload if isinstance(payload, list) else payload.get("data") or payload.get("items") or []
        observations: list[NormalizedObservation] = []
        for row in rows:
            if resource == "goals":
                code = str(row.get("code") or row.get("goal") or row.get("id") or "").strip()
                title = row.get("title") or row.get("description") or row.get("name")
                metric = "sdg_goal"
            else:
                code = str(row.get("code") or row.get("seriesCode") or row.get("id") or "").strip()
                title = row.get("description") or row.get("title") or row.get("name")
                metric = "sdg_indicator_series"
            if not code:
                continue
            observations.append(
                NormalizedObservation(
                    source_record_id=f"{resource}:{code}",
                    domain="sustainability",
                    metric=metric,
                    value_text=title or code,
                    observed_at=retrieved_at,
                    published_at=retrieved_at,
                    freshness_status="catalog",
                    quality_status="official_metadata",
                    methodology_url="https://unstats.un.org/sdgs/UNSDGAPIV5/swagger/index.html",
                    dimensions={"code": code, "resource": resource, "indicator_code": parameters.get("indicator_code")},
                    metadata={"source_record": row},
                )
            )
        return payload, observations


ADAPTERS: dict[str, ConnectorAdapter] = {
    adapter.adapter_id: adapter
    for adapter in (
        MetLocationforecastAdapter(),
        NasaGibsWmtsAdapter(),
        UsgsEarthquakeAdapter(),
        WorldBankIndicatorsAdapter(),
        FredSeriesObservationsAdapter(),
        UnSdgCatalogAdapter(),
    )
}
