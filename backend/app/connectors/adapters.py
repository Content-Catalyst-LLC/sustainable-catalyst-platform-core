from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
import csv
import io
import json
import math
import re
from typing import Any
from urllib.parse import quote, urlparse
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
    json_body: Any | None = None
    data: dict[str, Any] | None = None


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
    legal_record: dict[str, Any] | None = None
    scientific_record: dict[str, Any] | None = None
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


def _first_text(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, str):
        return value.strip() or None
    if isinstance(value, dict):
        for key in ("title", "value", "name", "label", "description", "text"):
            result = _first_text(value.get(key))
            if result:
                return result
        for item in value.values():
            result = _first_text(item)
            if result:
                return result
    if isinstance(value, list):
        for item in value:
            result = _first_text(item)
            if result:
                return result
    return str(value).strip() or None


def _list_text(value: Any) -> list[str]:
    if value is None:
        return []
    values = value if isinstance(value, list) else [value]
    output: list[str] = []
    for item in values:
        text = _first_text(item)
        if text and text not in output:
            output.append(text)
    return output


def _record_date(record: dict[str, Any], *keys: str, default: datetime) -> datetime:
    for key in keys:
        value = record.get(key)
        if isinstance(value, dict):
            value = value.get("value") or value.get("date") or value.get("created") or value.get("original")
        if value not in (None, ""):
            try:
                return parse_datetime(value)
            except (ValueError, TypeError):
                continue
    return default


def _un_authority(symbol: str | None, title: str | None) -> tuple[str, str]:
    symbol_upper = (symbol or "").upper()
    title_lower = (title or "").lower()
    if symbol_upper.startswith("S/RES/"):
        # A document symbol identifies the issuing body and record type, not by
        # itself the legal basis or binding effect of every operative paragraph.
        return "security_council_resolution", "official_security_council_resolution"
    if symbol_upper.startswith("A/RES/"):
        return "general_assembly_resolution", "recommendatory_resolution"
    if symbol_upper.startswith("A/HRC/RES/"):
        return "human_rights_council_resolution", "recommendatory_resolution"
    if "judgment" in title_lower:
        return "judgment", "judicial_decision"
    if "advisory opinion" in title_lower:
        return "advisory_opinion", "advisory_judicial_opinion"
    return "un_official_document", "official_report"


class UnDigitalLibraryAdapter(ConnectorAdapter):
    adapter_id = "un_digital_library_search_v1"

    def build_request(self, connector, parameters, settings) -> ConnectorRequest:
        query = str(self._required(parameters, "query")).strip()
        page_size = min(max(int(parameters.get("limit", 25)), 1), 100)
        start = min(max(int(parameters.get("start", 1)), 1), 1000000)
        fields = parameters.get("fields") or connector.configuration_json.get(
            "default_fields",
            "recid,title,document_symbol,publication_date,creation_date,language,subjects,collections,urls",
        )
        return ConnectorRequest(
            method="GET",
            url=connector.base_url,
            params={"p": query, "of": "recjson", "rg": page_size, "jrec": start, "ot": fields},
            headers={"User-Agent": settings.live_data_user_agent, "Accept": "application/json"},
        )

    def normalize(self, response, *, connector, parameters, retrieved_at):
        payload = response.json()
        rows = payload if isinstance(payload, list) else payload.get("records") or payload.get("data") or []
        observations: list[NormalizedObservation] = []
        for row in rows:
            if not isinstance(row, dict):
                continue
            recid = str(row.get("recid") or row.get("id") or row.get("record_id") or "").strip()
            if not recid:
                continue
            title = _first_text(row.get("title") or row.get("titles")) or f"UN Digital Library record {recid}"
            symbol = _first_text(
                row.get("document_symbol") or row.get("symbol") or row.get("report_number") or row.get("reportnumber")
            )
            record_type, authority_level = _un_authority(symbol, title)
            published_at = _record_date(
                row, "publication_date", "publication_year", "creation_date", "date", default=retrieved_at
            )
            languages = _list_text(row.get("language") or row.get("languages"))
            subjects = _list_text(row.get("subjects") or row.get("keywords"))
            canonical_url = _first_text(row.get("url") or row.get("urls")) or f"https://digitallibrary.un.org/record/{recid}"
            issuing_body = _first_text(row.get("corporate_author") or row.get("author") or row.get("issuing_body")) or "United Nations"
            observations.append(
                NormalizedObservation(
                    source_record_id=recid,
                    domain="international_law",
                    metric="un_document_record",
                    value_text=title,
                    observed_at=published_at,
                    published_at=published_at,
                    freshness_status="official_record",
                    quality_status="official_metadata",
                    methodology_url="https://digitallibrary.un.org/help/search-engine-api",
                    dimensions={
                        "official_symbol": symbol,
                        "record_type": record_type,
                        "authority_level": authority_level,
                        "languages": languages,
                        "subjects": subjects,
                    },
                    metadata={"source_record": row, "canonical_url": canonical_url},
                    legal_record={
                        "record_type": record_type,
                        "authority_level": authority_level,
                        "title": title,
                        "official_symbol": symbol,
                        "issuing_body": issuing_body,
                        "legal_body": issuing_body,
                        "jurisdiction": "international",
                        "legal_status": "official_record",
                        "publication_date": published_at,
                        "languages": languages,
                        "subjects": subjects,
                        "countries": _list_text(row.get("countries") or row.get("geographic_terms")),
                        "canonical_source_url": canonical_url,
                        "citation": f"United Nations, {symbol or title}.",
                        "summary": _first_text(row.get("abstract") or row.get("summary")),
                        "metadata": {"un_digital_library_recid": recid, "source_record": row},
                    },
                )
            )
        return payload, observations


class UnSdgMetadataAdapter(ConnectorAdapter):
    adapter_id = "un_sdg_metadata_v1"

    def build_request(self, connector, parameters, settings) -> ConnectorRequest:
        reporting_type = str(parameters.get("reporting_type", "National"))
        series = str(self._required(parameters, "series")).strip()
        ref_area = str(parameters.get("ref_area", "ALL")).strip()
        path = f"SDMXReport/{quote(reporting_type, safe='')}.{quote(series, safe='._-')}.{quote(ref_area, safe='._-')}"
        return ConnectorRequest(
            method="GET",
            url=f"{connector.base_url.rstrip('/')}/{path}",
            headers={"User-Agent": settings.live_data_user_agent, "Accept": "application/json,application/xml"},
        )

    def normalize(self, response, *, connector, parameters, retrieved_at):
        try:
            payload = response.json()
        except ValueError:
            payload = {"document": response.text}
        series = str(parameters["series"])
        ref_area = str(parameters.get("ref_area", "ALL"))
        title = _first_text(payload.get("title") if isinstance(payload, dict) else None) or f"SDG metadata for {series}"
        return payload, [
            NormalizedObservation(
                source_record_id=f"{series}:{ref_area}:{parameters.get('reporting_type', 'National')}",
                domain="sustainability",
                metric="sdg_metadata_report",
                value_text=title,
                observed_at=retrieved_at,
                published_at=retrieved_at,
                freshness_status="official_metadata",
                quality_status="official_metadata",
                methodology_url="https://unstats.un.org/SDGMetadataAPI/swagger/index.html",
                dimensions={"series": series, "ref_area": ref_area, "reporting_type": parameters.get("reporting_type", "National")},
                metadata={"source_record": payload},
            )
        ]


class ReliefWebReportsAdapter(ConnectorAdapter):
    adapter_id = "reliefweb_reports_v2"

    def build_request(self, connector, parameters, settings) -> ConnectorRequest:
        if not settings.reliefweb_appname:
            raise ValueError("SC_CORE_RELIEFWEB_APPNAME is required for the ReliefWeb connector.")
        params: dict[str, Any] = {
            "appname": settings.reliefweb_appname,
            "limit": min(max(int(parameters.get("limit", 25)), 1), 1000),
            "profile": str(parameters.get("profile", "full")),
            "preset": str(parameters.get("preset", "latest")),
        }
        if parameters.get("query"):
            params["query[value]"] = str(parameters["query"])
        if parameters.get("country"):
            params["filter[field]"] = "country.name"
            params["filter[value]"] = str(parameters["country"])
        return ConnectorRequest(
            method="GET",
            url=connector.base_url,
            params=params,
            headers={"User-Agent": settings.live_data_user_agent, "Accept": "application/json"},
        )

    def normalize(self, response, *, connector, parameters, retrieved_at):
        payload = response.json()
        observations: list[NormalizedObservation] = []
        for item in payload.get("data", []):
            fields = item.get("fields") or {}
            record_id = str(item.get("id") or fields.get("id") or "").strip()
            if not record_id:
                continue
            title = _first_text(fields.get("title")) or f"ReliefWeb report {record_id}"
            dates = fields.get("date") or {}
            published_at = _record_date(dates, "original", "created", "changed", default=retrieved_at)
            countries = [entry.get("name") for entry in fields.get("country", []) if isinstance(entry, dict) and entry.get("name")]
            sources = [entry.get("name") for entry in fields.get("source", []) if isinstance(entry, dict) and entry.get("name")]
            themes = [entry.get("name") for entry in fields.get("theme", []) if isinstance(entry, dict) and entry.get("name")]
            canonical_url = _first_text(fields.get("url_alias") or fields.get("url")) or item.get("href")
            observations.append(
                NormalizedObservation(
                    source_record_id=record_id,
                    domain="humanitarian",
                    metric="humanitarian_report",
                    value_text=title,
                    observed_at=published_at,
                    published_at=published_at,
                    freshness_status="latest_report",
                    quality_status="curated_humanitarian_report",
                    methodology_url="https://apidoc.reliefweb.int/",
                    dimensions={"countries": countries, "sources": sources, "themes": themes},
                    metadata={"source_record": fields, "canonical_url": canonical_url},
                    legal_record={
                        "record_type": "humanitarian_report",
                        "authority_level": "humanitarian_reporting",
                        "title": title,
                        "issuing_body": "; ".join(sources) if sources else "ReliefWeb information partner",
                        "jurisdiction": "international",
                        "legal_status": "informational",
                        "publication_date": published_at,
                        "countries": countries,
                        "subjects": themes,
                        "canonical_source_url": canonical_url,
                        "citation": f"{'; '.join(sources) if sources else 'ReliefWeb'}, {title}.",
                        "summary": _first_text(fields.get("body") or fields.get("headline")),
                        "metadata": {"reliefweb_id": record_id, "source_record": fields},
                    },
                )
            )
        return payload, observations


class HdxHapiAdapter(ConnectorAdapter):
    adapter_id = "hdx_hapi_v2"

    def build_request(self, connector, parameters, settings) -> ConnectorRequest:
        resource = str(parameters.get("resource") or connector.configuration_json.get("default_resource", "affected-people/refugees-persons-of-concern"))
        allowed = set(connector.configuration_json.get("allowed_resources", []))
        if resource not in allowed:
            raise ValueError(f"Unsupported HDX HAPI resource '{resource}'.")
        params: dict[str, Any] = {
            "output_format": "json",
            "app_identifier": settings.hdx_hapi_app_identifier,
            "limit": min(max(int(parameters.get("limit", 1000)), 1), 10000),
            "offset": max(int(parameters.get("offset", 0)), 0),
        }
        for key in ("location_code", "admin_level", "reference_period_start_min", "reference_period_end_max"):
            if parameters.get(key) is not None:
                params[key] = parameters[key]
        return ConnectorRequest(
            method="GET",
            url=f"{connector.base_url.rstrip('/')}/{resource}",
            params=params,
            headers={"User-Agent": settings.live_data_user_agent, "Accept": "application/json"},
        )

    def normalize(self, response, *, connector, parameters, retrieved_at):
        payload = response.json()
        rows = payload.get("data", payload if isinstance(payload, list) else [])
        resource = str(parameters.get("resource") or connector.configuration_json.get("default_resource"))
        observations: list[NormalizedObservation] = []
        for index, row in enumerate(rows):
            if not isinstance(row, dict):
                continue
            value = finite_float(row.get("population") or row.get("funding") or row.get("requirements") or row.get("value"))
            metric = resource.replace("/", "_").replace("-", "_")
            observed_at = _record_date(row, "reference_period_end", "reference_period_start", "event_date", default=retrieved_at)
            record_id = str(row.get("resource_hdx_id") or row.get("id") or f"{metric}:{index}:{observed_at.isoformat()}")
            geometry = None
            lat, lon = finite_float(row.get("lat") or row.get("latitude")), finite_float(row.get("lon") or row.get("longitude"))
            if lat is not None and lon is not None:
                geometry = {"type": "Point", "coordinates": [lon, lat]}
            observations.append(
                NormalizedObservation(
                    source_record_id=f"{record_id}:{index}",
                    domain="humanitarian",
                    metric=metric,
                    value_number=value,
                    value_text=None if value is not None else _first_text(row.get("name") or row.get("population_group")),
                    unit="people" if row.get("population") is not None else None,
                    geometry=geometry,
                    observed_at=observed_at,
                    published_at=retrieved_at,
                    freshness_status="source_reported",
                    quality_status="standardized_humanitarian_indicator",
                    methodology_url="https://hdx-hapi.readthedocs.io/",
                    dimensions={key: row.get(key) for key in row if key not in {"population", "funding", "requirements", "value"}},
                    metadata={"resource": resource, "source_record": row},
                )
            )
        return payload, observations


class UnPopulationDataAdapter(ConnectorAdapter):
    adapter_id = "un_population_data_v1"

    def build_request(self, connector, parameters, settings) -> ConnectorRequest:
        indicators = str(self._required(parameters, "indicators")).strip()
        locations = str(self._required(parameters, "locations")).strip()
        start_year = int(self._required(parameters, "start_year"))
        end_year = int(self._required(parameters, "end_year"))
        if start_year > end_year:
            raise ValueError("start_year cannot be after end_year.")
        url = f"{connector.base_url.rstrip('/')}/data/indicators/{quote(indicators, safe=',')}/locations/{quote(locations, safe=',')}/start/{start_year}/end/{end_year}/"
        headers = {"User-Agent": settings.live_data_user_agent, "Accept": "application/json"}
        if settings.un_population_bearer_token:
            headers["Authorization"] = f"Bearer {settings.un_population_bearer_token}"
        return ConnectorRequest(method="GET", url=url, params={"format": "json"}, headers=headers)

    def normalize(self, response, *, connector, parameters, retrieved_at):
        payload = response.json()
        rows = payload if isinstance(payload, list) else payload.get("data") or payload.get("Data") or []
        observations: list[NormalizedObservation] = []
        for row in rows:
            if not isinstance(row, dict):
                continue
            indicator = str(row.get("IndicatorId") or row.get("indicatorId") or row.get("Indicator") or parameters["indicators"])
            location = str(row.get("Iso3") or row.get("LocationId") or row.get("Location") or "unknown")
            period = row.get("TimeLabel") or row.get("TimeMid") or row.get("Year")
            try:
                observed_at = parse_datetime(str(int(float(period)))) if period is not None else retrieved_at
            except (ValueError, TypeError):
                observed_at = retrieved_at
            value = finite_float(row.get("Value") if "Value" in row else row.get("value"))
            source_id = f"{location}:{indicator}:{period}:{row.get('SexId')}:{row.get('AgeId')}:{row.get('VariantId')}"
            observations.append(
                NormalizedObservation(
                    source_record_id=source_id,
                    domain="demographics",
                    metric=indicator,
                    value_number=value,
                    unit=row.get("UnitShortLabel") or row.get("Unit") or row.get("unit"),
                    observed_at=observed_at,
                    published_at=retrieved_at,
                    freshness_status="official_release",
                    quality_status="official_statistical_observation",
                    methodology_url="https://population.un.org/dataportalapi/index.html",
                    dimensions={
                        "location": row.get("Location"), "location_id": row.get("LocationId"), "iso3": row.get("Iso3"),
                        "indicator_name": row.get("IndicatorDisplayName") or row.get("Indicator"), "sex": row.get("Sex"),
                        "age": row.get("AgeLabel"), "variant": row.get("Variant"), "estimate_type": row.get("EstimateType"),
                        "source": row.get("Source"), "revision": row.get("Revision"), "period": period,
                    },
                    metadata={"source_record": row},
                )
            )
        return payload, observations


class UnComtradeAdapter(ConnectorAdapter):
    adapter_id = "un_comtrade_public_v1"

    def build_request(self, connector, parameters, settings) -> ConnectorRequest:
        reporter = str(self._required(parameters, "reporter_code")).strip()
        period = str(self._required(parameters, "period")).strip()
        commodity = str(parameters.get("commodity_code", "TOTAL")).strip()
        partner = str(parameters.get("partner_code", 0)).strip()
        flow = str(parameters.get("flow_code", "X,M")).strip()
        params = {
            "reporterCode": reporter,
            "period": period,
            "cmdCode": commodity,
            "partnerCode": partner,
            "flowCode": flow,
            "partner2Code": str(parameters.get("partner2_code", 0)),
            "customsCode": str(parameters.get("customs_code", "C00")),
            "motCode": str(parameters.get("mot_code", 0)),
            "maxRecords": min(max(int(parameters.get("max_records", 500)), 1), 500),
            "aggregateBy": 6,
            "breakdownMode": "classic",
            "includeDesc": "true",
        }
        return ConnectorRequest(method="GET", url=connector.base_url, params=params, headers={"User-Agent": settings.live_data_user_agent, "Accept": "application/json"})

    def normalize(self, response, *, connector, parameters, retrieved_at):
        payload = response.json()
        rows = payload.get("data", payload if isinstance(payload, list) else [])
        observations: list[NormalizedObservation] = []
        for row in rows:
            if not isinstance(row, dict):
                continue
            period = str(row.get("period") or parameters["period"])
            observed_at = parse_datetime(period[:4])
            reporter = str(row.get("reporterCode") or parameters["reporter_code"])
            partner = str(row.get("partnerCode") or parameters.get("partner_code", 0))
            commodity = str(row.get("cmdCode") or parameters.get("commodity_code", "TOTAL"))
            flow = str(row.get("flowCode") or row.get("flowDesc") or "unknown")
            value = finite_float(row.get("primaryValue") or row.get("TradeValue") or row.get("tradeValue"))
            observations.append(
                NormalizedObservation(
                    source_record_id=f"{reporter}:{partner}:{commodity}:{flow}:{period}",
                    domain="economics",
                    metric="international_trade_value",
                    value_number=value,
                    unit="USD",
                    observed_at=observed_at,
                    published_at=retrieved_at,
                    freshness_status="latest_release",
                    quality_status="official_statistical_observation",
                    methodology_url="https://comtradeapi.un.org/",
                    dimensions={
                        "reporter_code": reporter, "reporter": row.get("reporterDesc"), "partner_code": partner,
                        "partner": row.get("partnerDesc"), "commodity_code": commodity, "commodity": row.get("cmdDesc"),
                        "flow_code": row.get("flowCode"), "flow": row.get("flowDesc"), "period": period,
                        "net_weight_kg": finite_float(row.get("netWgt")), "quantity": finite_float(row.get("qty")),
                    },
                    metadata={"source_record": row},
                )
            )
        return payload, observations


class UnhcrPopulationAdapter(ConnectorAdapter):
    adapter_id = "unhcr_population_v1"

    def build_request(self, connector, parameters, settings) -> ConnectorRequest:
        params: dict[str, Any] = {
            "limit": min(max(int(parameters.get("limit", 100)), 1), 1000),
            "page": max(int(parameters.get("page", 1)), 1),
            "yearFrom": int(parameters.get("year_from", parameters.get("year", 2020))),
            "yearTo": int(parameters.get("year_to", parameters.get("year", 2025))),
            "cf_type": str(parameters.get("country_code_type", "ISO")),
        }
        for key in ("coo", "coa"):
            if parameters.get(key):
                params[key] = str(parameters[key])
        return ConnectorRequest(method="GET", url=connector.base_url, params=params, headers={"User-Agent": settings.live_data_user_agent, "Accept": "application/json"})

    def normalize(self, response, *, connector, parameters, retrieved_at):
        payload = response.json()
        rows = payload.get("items") or payload.get("data") or payload.get("results") or []
        observations: list[NormalizedObservation] = []
        population_fields = {
            "refugees": "refugees", "asylum_seekers": "asylum_seekers", "idps": "internally_displaced_persons",
            "stateless": "stateless_persons", "oip": "other_people_in_need_of_international_protection",
            "ooc": "others_of_concern", "returned_refugees": "returned_refugees", "returned_idps": "returned_idps",
        }
        for row in rows:
            if not isinstance(row, dict):
                continue
            year = row.get("year") or row.get("Year")
            if year is None:
                continue
            observed_at = parse_datetime(str(year))
            origin = str(row.get("coo_id") or row.get("coo") or row.get("origin") or "all")
            asylum = str(row.get("coa_id") or row.get("coa") or row.get("asylum") or "all")
            for field_name, metric in population_fields.items():
                value = finite_float(row.get(field_name))
                if value is None:
                    continue
                observations.append(
                    NormalizedObservation(
                        source_record_id=f"{origin}:{asylum}:{year}:{metric}",
                        domain="humanitarian",
                        metric=metric,
                        value_number=value,
                        unit="people",
                        observed_at=observed_at,
                        published_at=retrieved_at,
                        freshness_status="annual_release",
                        quality_status="official_statistical_observation",
                        methodology_url="https://api.unhcr.org/docs/refugee-statistics.html",
                        dimensions={"origin_code": origin, "origin": row.get("coo_name"), "asylum_code": asylum, "asylum": row.get("coa_name"), "year": year},
                        metadata={"source_record": row},
                    )
                )
        return payload, observations


class OhchrUhriAdapter(ConnectorAdapter):
    adapter_id = "ohchr_uhri_v1"

    def build_request(self, connector, parameters, settings) -> ConnectorRequest:
        if not settings.uhri_api_url:
            raise ValueError("SC_CORE_UHRI_API_URL is required after obtaining the free OHCHR UHRI API endpoint documentation.")
        parsed = urlparse(settings.uhri_api_url)
        if parsed.scheme != "https" or not parsed.hostname:
            raise ValueError("SC_CORE_UHRI_API_URL must be an absolute HTTPS endpoint supplied by OHCHR.")
        params: dict[str, Any] = {"limit": min(max(int(parameters.get("limit", 100)), 1), 1000)}
        for key in ("country", "mechanism", "theme", "sdg", "year"):
            if parameters.get(key) is not None:
                params[key] = parameters[key]
        return ConnectorRequest(method="GET", url=settings.uhri_api_url, params=params, headers={"User-Agent": settings.live_data_user_agent, "Accept": "application/json"})

    def normalize(self, response, *, connector, parameters, retrieved_at):
        payload = response.json()
        rows = payload.get("data") or payload.get("items") or payload.get("recommendations") or (payload if isinstance(payload, list) else [])
        observations: list[NormalizedObservation] = []
        for index, row in enumerate(rows):
            if not isinstance(row, dict):
                continue
            record_id = str(row.get("id") or row.get("recommendationId") or f"uhri:{index}")
            text = _first_text(row.get("recommendation") or row.get("text") or row.get("paragraph")) or "OHCHR human-rights recommendation"
            date = _record_date(row, "date", "sessionDate", "publicationDate", default=retrieved_at)
            countries = _list_text(row.get("country") or row.get("countries"))
            themes = _list_text(row.get("theme") or row.get("themes"))
            sdgs = _list_text(row.get("sdg") or row.get("sdgs"))
            mechanism = _first_text(row.get("mechanism") or row.get("mechanismName")) or "UN human-rights mechanism"
            observations.append(
                NormalizedObservation(
                    source_record_id=record_id,
                    domain="international_law",
                    metric="human_rights_recommendation",
                    value_text=text,
                    observed_at=date,
                    published_at=date,
                    freshness_status="official_record",
                    quality_status="official_recommendation",
                    methodology_url="https://uhri.ohchr.org/en/our-data-api",
                    dimensions={"countries": countries, "themes": themes, "sdgs": sdgs, "mechanism": mechanism},
                    metadata={"source_record": row},
                    legal_record={
                        "record_type": "human_rights_recommendation",
                        "authority_level": "non_binding_recommendation",
                        "title": text[:300],
                        "issuing_body": mechanism,
                        "legal_body": mechanism,
                        "jurisdiction": "international",
                        "legal_status": "official_recommendation",
                        "publication_date": date,
                        "countries": countries,
                        "subjects": themes,
                        "related_sdg_targets": sdgs,
                        "canonical_source_url": _first_text(row.get("url") or row.get("documentUrl")),
                        "citation": f"{mechanism}, recommendation {record_id}.",
                        "summary": text,
                        "metadata": {"uhri_id": record_id, "source_record": row},
                    },
                )
            )
        return payload, observations


_SAFE_TOKEN = re.compile(r"^[A-Za-z0-9_.:+-]{1,200}$")


def _safe_token(value: Any, label: str) -> str:
    text = str(value or "").strip()
    if not _SAFE_TOKEN.fullmatch(text):
        raise ValueError(f"Parameter '{label}' contains unsupported characters.")
    return text


def _safe_adql(query: Any, *, max_length: int = 12000) -> str:
    text = " ".join(str(query or "").strip().split())
    if not text or len(text) > max_length:
        raise ValueError("A bounded ADQL SELECT query is required.")
    lowered = text.lower()
    if not lowered.startswith("select "):
        raise ValueError("Only read-only SELECT queries are permitted.")
    if ";" in text or re.search(r"\b(insert|update|delete|drop|alter|create|grant|revoke|truncate)\b", lowered):
        raise ValueError("The ADQL query contains a prohibited operation.")
    return text


def _tap_rows(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, list):
        return [row for row in payload if isinstance(row, dict)]
    if not isinstance(payload, dict):
        return []
    if isinstance(payload.get("data"), list) and payload.get("metadata"):
        metadata = payload.get("metadata") or []
        names = [str(item.get("name") or item.get("column_name") or f"column_{i}") if isinstance(item, dict) else str(item) for i, item in enumerate(metadata)]
        output = []
        for row in payload["data"]:
            if isinstance(row, dict):
                output.append(row)
            elif isinstance(row, list):
                output.append({names[i] if i < len(names) else f"column_{i}": value for i, value in enumerate(row)})
        return output
    for key in ("results", "rows", "items"):
        if isinstance(payload.get(key), list):
            return [row for row in payload[key] if isinstance(row, dict)]
    return []


class NasaCmrCollectionsAdapter(ConnectorAdapter):
    adapter_id = "nasa_cmr_collections_v1"

    def build_request(self, connector, parameters, settings) -> ConnectorRequest:
        keyword = str(self._required(parameters, "keyword")).strip()
        params: dict[str, Any] = {
            "keyword": keyword,
            "page_size": min(max(int(parameters.get("page_size", connector.configuration_json.get("default_page_size", 50))), 1), 200),
            "pretty": "false",
        }
        for key in ("temporal", "bounding_box", "provider", "short_name", "version"):
            if parameters.get(key) is not None:
                params[key] = str(parameters[key])
        return ConnectorRequest(method="GET", url=connector.base_url, params=params, headers={"User-Agent": settings.live_data_user_agent, "Accept": "application/json"})

    def normalize(self, response, *, connector, parameters, retrieved_at):
        payload = response.json()
        entries = ((payload.get("feed") or {}).get("entry") or []) if isinstance(payload, dict) else []
        observations: list[NormalizedObservation] = []
        for row in entries:
            if not isinstance(row, dict):
                continue
            concept_id = str(row.get("id") or row.get("concept-id") or row.get("short_name") or "")
            if not concept_id:
                continue
            title = _first_text(row.get("dataset_id") or row.get("title") or row.get("short_name")) or concept_id
            start = _record_date(row, "time_start", "updated", default=retrieved_at)
            end = None
            if row.get("time_end"):
                try: end = parse_datetime(row["time_end"])
                except ValueError: end = None
            links = [item for item in row.get("links", []) if isinstance(item, dict)]
            access = next((item.get("href") for item in links if item.get("href") and not item.get("inherited")), None)
            doi = _first_text(row.get("doi"))
            keywords = _list_text(row.get("organizations")) + _list_text(row.get("browse_flag"))
            boxes = row.get("boxes") or []
            geometry = {"type": "BoundingBox", "coordinates": boxes[0]} if boxes else None
            science = {
                "record_type": "earth_science_dataset",
                "discipline": "earth_science",
                "title": title,
                "summary": _first_text(row.get("summary")),
                "dataset_id": _first_text(row.get("short_name")) or concept_id,
                "collection": _first_text(row.get("data_center")),
                "doi": doi,
                "access_url": access,
                "landing_page_url": next((item.get("href") for item in links if item.get("rel", "").endswith("metadata#")), None),
                "geometry": geometry,
                "observation_start": start,
                "observation_end": end,
                "published_at": _record_date(row, "updated", default=retrieved_at),
                "identifiers": {"cmr_concept_id": concept_id, "short_name": row.get("short_name"), "doi": doi},
                "keywords": keywords,
                "file_formats": _list_text(row.get("archive_center")),
                "metadata": {"version_id": row.get("version_id"), "original_format": row.get("original_format"), "links": links[:20]},
            }
            observations.append(NormalizedObservation(source_record_id=concept_id, domain="earth_science", metric="dataset_available", value_number=1.0, value_text=title, unit="boolean", geometry=geometry, observed_at=start, published_at=science["published_at"], freshness_status="catalog", quality_status="provider_catalog", methodology_url="https://cmr.earthdata.nasa.gov/search/site/docs/search/api", metadata={"short_name": row.get("short_name"), "version_id": row.get("version_id")}, scientific_record=science))
        return payload, observations


class NasaApodAdapter(ConnectorAdapter):
    adapter_id = "nasa_apod_v1"

    def build_request(self, connector, parameters, settings) -> ConnectorRequest:
        params: dict[str, Any] = {"api_key": settings.nasa_api_key, "thumbs": "true"}
        for key in ("date", "start_date", "end_date"):
            if parameters.get(key): params[key] = str(parameters[key])
        if parameters.get("count") is not None:
            params["count"] = min(max(int(parameters["count"]), 1), 25)
        return ConnectorRequest(method="GET", url=connector.base_url, params=params, headers={"User-Agent": settings.live_data_user_agent, "Accept": "application/json"})

    def normalize(self, response, *, connector, parameters, retrieved_at):
        payload = response.json()
        rows = payload if isinstance(payload, list) else [payload]
        observations = []
        for row in rows:
            if not isinstance(row, dict): continue
            date = parse_datetime(row.get("date"), default=retrieved_at)
            title = _first_text(row.get("title")) or "NASA astronomy media"
            url = _first_text(row.get("hdurl") or row.get("url") or row.get("thumbnail_url"))
            media_type = str(row.get("media_type") or "unknown")
            observations.append(NormalizedObservation(source_record_id=f"apod:{date.date().isoformat()}", domain="space_science", metric="astronomy_media_published", value_number=1.0, value_text=title, unit="item", observed_at=date, published_at=date, freshness_status="daily", quality_status="official_media", methodology_url="https://api.nasa.gov/", dimensions={"media_type": media_type, "service_version": row.get("service_version")}, metadata={"url": row.get("url"), "hdurl": row.get("hdurl"), "copyright": row.get("copyright")}, scientific_record={"record_type": "astronomy_image", "discipline": "astronomy", "title": title, "summary": _first_text(row.get("explanation")), "collection": "Astronomy Picture of the Day", "mission": "NASA public science communication", "access_url": url, "landing_page_url": row.get("url"), "observation_start": date, "observation_end": date, "published_at": date, "identifiers": {"apod_date": date.date().isoformat()}, "keywords": ["astronomy", media_type], "file_formats": [media_type], "metadata": {"copyright": row.get("copyright"), "thumbnail_url": row.get("thumbnail_url")}}))
        return payload, observations


class NoaaNceiDataAdapter(ConnectorAdapter):
    adapter_id = "noaa_ncei_data_v1"

    def build_request(self, connector, parameters, settings) -> ConnectorRequest:
        params = {
            "dataset": str(self._required(parameters, "dataset")),
            "startDate": str(self._required(parameters, "start_date")),
            "endDate": str(self._required(parameters, "end_date")),
            "format": "json",
            "includeAttributes": "true",
            "includeStationName": "true",
            "includeStationLocation": "true",
        }
        mapping = {"stations": "stations", "bbox": "boundingBox", "units": "units", "limit": "limit"}
        for source, target in mapping.items():
            if parameters.get(source) is not None: params[target] = parameters[source]
        return ConnectorRequest(method="GET", url=connector.base_url, params=params, headers={"User-Agent": settings.live_data_user_agent, "Accept": "application/json"})

    def normalize(self, response, *, connector, parameters, retrieved_at):
        payload = response.json()
        rows = payload if isinstance(payload, list) else (payload.get("results") or payload.get("data") or [])
        observations = []
        for index, row in enumerate(rows):
            if not isinstance(row, dict): continue
            date = _record_date(row, "DATE", "date", default=retrieved_at)
            station = _first_text(row.get("STATION") or row.get("station")) or f"record-{index}"
            dataset = str(parameters.get("dataset"))
            lat = finite_float(row.get("LATITUDE") or row.get("latitude")); lon = finite_float(row.get("LONGITUDE") or row.get("longitude"))
            geometry = {"type": "Point", "coordinates": [lon, lat]} if lat is not None and lon is not None else None
            excluded = {"DATE","date","STATION","station","NAME","name","LATITUDE","latitude","LONGITUDE","longitude","ELEVATION","elevation"}
            variables = [key for key, value in row.items() if key not in excluded and value not in (None, "")]
            source_id = f"{dataset}:{station}:{date.isoformat()}:{index}"
            observations.append(NormalizedObservation(source_record_id=source_id, domain="earth_science", metric="ncei_environmental_record", value_text=station, geometry=geometry, observed_at=date, published_at=retrieved_at, freshness_status="source_record", quality_status="source_reported", methodology_url="https://www.ncei.noaa.gov/support/access-data-service-api-user-documentation", dimensions={"dataset": dataset, "station": station, "station_name": row.get("NAME") or row.get("name"), "elevation": row.get("ELEVATION") or row.get("elevation")}, metadata={"variables": {key: row.get(key) for key in variables}}, scientific_record={"record_type": "environmental_observation", "discipline": "earth_science", "title": f"{dataset} observation at {station}", "summary": _first_text(row.get("NAME") or row.get("name")), "dataset_id": dataset, "collection": dataset, "geometry": geometry, "observation_start": date, "observation_end": date, "published_at": retrieved_at, "identifiers": {"station": station}, "variables": variables, "quality_status": "source_reported", "metadata": {"record": row}}))
        return payload, observations


class EcmwfOpenDataIndexAdapter(ConnectorAdapter):
    adapter_id = "ecmwf_open_data_index_v1"

    def build_request(self, connector, parameters, settings) -> ConnectorRequest:
        date = _safe_token(self._required(parameters, "date"), "date")
        run = _safe_token(self._required(parameters, "run"), "run").zfill(2)
        if run not in set(connector.configuration_json.get("allowed_runs", [])): raise ValueError("Unsupported ECMWF run.")
        stream = _safe_token(self._required(parameters, "stream"), "stream")
        product_type = _safe_token(self._required(parameters, "type"), "type")
        step = int(self._required(parameters, "step")); model = _safe_token(parameters.get("model", "ifs"), "model"); resolution = _safe_token(parameters.get("resolution", "0p25"), "resolution")
        filename = f"{date}{run}0000-{step}h-{stream}-{product_type}.index"
        url = f"{connector.base_url.rstrip('/')}/{date}/{run}z/{model}/{resolution}/{stream}/{filename}"
        return ConnectorRequest(method="GET", url=url, headers={"User-Agent": settings.live_data_user_agent, "Accept": "application/x-ndjson,application/json,text/plain"})

    def normalize(self, response, *, connector, parameters, retrieved_at):
        rows=[]
        for line in response.text.splitlines():
            line=line.strip()
            if not line: continue
            try: row=json.loads(line)
            except json.JSONDecodeError: continue
            if isinstance(row,dict): rows.append(row)
        observations=[]
        run_time=parse_datetime(f"{parameters['date']}T{str(parameters['run']).zfill(2)}:00:00+00:00", default=retrieved_at)
        for index,row in enumerate(rows):
            param=str(row.get("param") or row.get("shortName") or row.get("name") or f"field-{index}")
            level=row.get("levelist") or row.get("level")
            rec_id=f"{parameters['date']}:{parameters['run']}:{parameters['stream']}:{parameters['type']}:{parameters['step']}:{param}:{level}:{index}"
            observations.append(NormalizedObservation(source_record_id=rec_id,domain="atmospheric_science",metric="forecast_field_available",value_number=1.0,value_text=param,unit="boolean",observed_at=run_time,published_at=run_time,freshness_status="forecast_catalog",quality_status="provider_index",methodology_url="https://www.ecmwf.int/en/forecasts/datasets/open-data",dimensions={"step_hours":int(parameters["step"]),"stream":parameters["stream"],"type":parameters["type"],"level":level,"offset":row.get("_offset"),"length":row.get("_length")},metadata={"index_record":row},scientific_record={"record_type":"forecast_field","discipline":"atmospheric_science","title":f"ECMWF {param} forecast field","summary":"Machine-readable ECMWF open-data GRIB index record.","dataset_id":f"ecmwf:{parameters.get('model','ifs')}:{parameters['stream']}","collection":"ECMWF Open Data","mission":parameters.get("model","ifs"),"observation_start":run_time,"published_at":run_time,"identifiers":{"parameter":param,"step_hours":parameters["step"]},"variables":[param],"file_formats":["GRIB2"],"metadata":{"index_record":row,"request_url":str(response.request.url).removesuffix('.index')}}))
        return {"records":rows}, observations


class UsgsWaterInstantaneousAdapter(ConnectorAdapter):
    adapter_id = "usgs_water_iv_v1"

    def build_request(self, connector, parameters, settings) -> ConnectorRequest:
        params={"format":"json","siteStatus":"all"}
        selectors={"sites":"sites","state_cd":"stateCd","b_box":"bBox"}
        if not any(parameters.get(k) for k in selectors): raise ValueError("One of sites, state_cd, or b_box is required.")
        for source,target in selectors.items():
            if parameters.get(source): params[target]=str(parameters[source])
        params["period"]=str(parameters.get("period") or connector.configuration_json.get("default_period","P1D"))
        if parameters.get("parameter_cd"): params["parameterCd"]=str(parameters["parameter_cd"])
        return ConnectorRequest(method="GET",url=connector.base_url,params=params,headers={"User-Agent":settings.live_data_user_agent,"Accept":"application/json"})

    def normalize(self,response,*,connector,parameters,retrieved_at):
        payload=response.json(); series=(((payload.get("value") or {}).get("timeSeries")) or []) if isinstance(payload,dict) else []
        observations=[]
        for ts in series:
            variable=ts.get("variable") or {}; code=_first_text(variable.get("variableCode")) or "water_value"; unit=_first_text((variable.get("unit") or {}).get("unitCode"))
            source=ts.get("sourceInfo") or {}; site=_first_text(source.get("siteCode")) or _first_text(source.get("siteName")) or "unknown-site"
            geo=((source.get("geoLocation") or {}).get("geogLocation") or {}); lat=finite_float(geo.get("latitude")); lon=finite_float(geo.get("longitude")); geometry={"type":"Point","coordinates":[lon,lat]} if lat is not None and lon is not None else None
            for block in ts.get("values",[]):
                qualifiers=block.get("qualifier") or []
                for item in block.get("value",[]):
                    date=parse_datetime(item.get("dateTime"),default=retrieved_at); val=finite_float(item.get("value")); q=_list_text(item.get("qualifiers") or qualifiers)
                    rec_id=f"{site}:{code}:{date.isoformat()}"
                    observations.append(NormalizedObservation(source_record_id=rec_id,domain="hydrology",metric=code,value_number=val,value_text=None if val is not None else _first_text(item.get("value")),unit=unit,geometry=geometry,observed_at=date,published_at=retrieved_at,freshness_status="near_real_time",quality_status="provisional" if any('P'==x or 'provisional' in x.lower() for x in q) else "source_reported",methodology_url="https://waterservices.usgs.gov/docs/instantaneous-values/instantaneous-values-details/",dimensions={"site":site,"site_name":source.get("siteName"),"variable_name":variable.get("variableDescription"),"qualifiers":q},metadata={"source_info":source},scientific_record={"record_type":"water_observation","discipline":"hydrology","title":f"{variable.get('variableDescription') or code} at {source.get('siteName') or site}","dataset_id":"USGS NWIS Instantaneous Values","collection":"USGS Water Data for the Nation","geometry":geometry,"observation_start":date,"observation_end":date,"published_at":retrieved_at,"identifiers":{"site":site,"parameter_code":code},"variables":[code],"quality_status":"provisional" if any('P'==x or 'provisional' in x.lower() for x in q) else "source_reported","metadata":{"value":item.get("value"),"unit":unit,"qualifiers":q}}))
        return payload,observations


class NcbiEntrezSearchAdapter(ConnectorAdapter):
    adapter_id = "ncbi_entrez_search_v1"

    def build_request(self,connector,parameters,settings)->ConnectorRequest:
        db=_safe_token(self._required(parameters,"db"),"db").lower(); allowed=set(connector.configuration_json.get("allowed_databases",[]))
        if db not in allowed: raise ValueError(f"Unsupported NCBI database '{db}'.")
        params={"db":db,"term":str(self._required(parameters,"term")),"retmode":"json","retmax":min(max(int(parameters.get("retmax",50)),1),200),"tool":connector.configuration_json.get("tool","sustainable_catalyst_core"),"email":str(parameters.get("email") or "platform@sustainablecatalyst.com")}
        if settings.ncbi_api_key: params["api_key"]=settings.ncbi_api_key
        return ConnectorRequest(method="GET",url=f"{connector.base_url.rstrip('/')}/esearch.fcgi",params=params,headers={"User-Agent":settings.live_data_user_agent,"Accept":"application/json"})

    def normalize(self,response,*,connector,parameters,retrieved_at):
        payload=response.json(); result=payload.get("esearchresult") or {}; db=str(parameters.get("db")); term=str(parameters.get("term")); observations=[]
        for uid in result.get("idlist") or []:
            uid=str(uid)
            observations.append(NormalizedObservation(source_record_id=f"{db}:{uid}",domain="biomedical_science",metric="entrez_record_match",value_number=1.0,value_text=uid,unit="record",observed_at=retrieved_at,published_at=retrieved_at,freshness_status="catalog",quality_status="database_match",methodology_url="https://www.ncbi.nlm.nih.gov/books/NBK25501/",dimensions={"database":db,"query":term},metadata={"query_translation":result.get("querytranslation"),"count":result.get("count")},scientific_record={"record_type":"biomedical_database_record","discipline":"biomedical_science","title":f"NCBI {db} record {uid}","summary":f"Record identifier returned for Entrez search: {term}","dataset_id":db,"collection":f"NCBI Entrez {db}","landing_page_url":f"https://www.ncbi.nlm.nih.gov/{db}/{uid}/","published_at":retrieved_at,"identifiers":{"uid":uid,"database":db},"keywords":[term],"metadata":{"query_translation":result.get("querytranslation")}}))
        return payload,observations


class PubchemCompoundPropertiesAdapter(ConnectorAdapter):
    adapter_id = "pubchem_compound_properties_v1"
    PROPERTIES="Title,MolecularFormula,MolecularWeight,CanonicalSMILES,IsomericSMILES,InChI,InChIKey,IUPACName,XLogP,ExactMass,MonoisotopicMass,TPSA,Complexity,HBondDonorCount,HBondAcceptorCount,RotatableBondCount,Charge"

    def build_request(self,connector,parameters,settings)->ConnectorRequest:
        namespace=_safe_token(self._required(parameters,"namespace"),"namespace").lower(); allowed=set(connector.configuration_json.get("allowed_namespaces",[]))
        if namespace not in allowed: raise ValueError("Unsupported PubChem namespace.")
        identifier=quote(str(self._required(parameters,"identifier")).strip(),safe="")
        return ConnectorRequest(method="GET",url=f"{connector.base_url.rstrip('/')}/{namespace}/{identifier}/property/{self.PROPERTIES}/JSON",headers={"User-Agent":settings.live_data_user_agent,"Accept":"application/json"})

    def normalize(self,response,*,connector,parameters,retrieved_at):
        payload=response.json(); rows=((payload.get("PropertyTable") or {}).get("Properties") or []); observations=[]
        for row in rows:
            cid=str(row.get("CID") or row.get("InChIKey") or parameters.get("identifier")); title=_first_text(row.get("Title") or row.get("IUPACName")) or f"PubChem compound {cid}"; weight=finite_float(row.get("MolecularWeight"))
            observations.append(NormalizedObservation(source_record_id=f"cid:{cid}",domain="chemistry",metric="molecular_weight",value_number=weight,value_text=title,unit="g/mol",observed_at=retrieved_at,published_at=retrieved_at,freshness_status="catalog",quality_status="database_record",methodology_url="https://pubchem.ncbi.nlm.nih.gov/docs/pug-rest",dimensions={"molecular_formula":row.get("MolecularFormula"),"iupac_name":row.get("IUPACName"),"inchi_key":row.get("InChIKey")},metadata={"properties":row},scientific_record={"record_type":"chemical_compound","discipline":"chemistry","title":title,"summary":f"PubChem compound record for {row.get('MolecularFormula') or cid}.","dataset_id":"PubChem Compound","collection":"PubChem","landing_page_url":f"https://pubchem.ncbi.nlm.nih.gov/compound/{cid}","published_at":retrieved_at,"identifiers":{"cid":cid,"inchi":row.get("InChI"),"inchikey":row.get("InChIKey"),"canonical_smiles":row.get("ConnectivitySMILES") or row.get("CanonicalSMILES")},"variables":[key for key,value in row.items() if value is not None],"metadata":{"properties":row}}))
        return payload,observations


class GbifOccurrenceSearchAdapter(ConnectorAdapter):
    adapter_id = "gbif_occurrence_search_v1"

    def build_request(self,connector,parameters,settings)->ConnectorRequest:
        keys={"scientific_name":"scientificName","taxon_key":"taxon_key","country":"country","geometry":"geometry","year":"year","basis_of_record":"basisOfRecord","has_coordinate":"hasCoordinate"}
        if not any(parameters.get(k) for k in ("scientific_name","taxon_key","country","geometry")): raise ValueError("A taxon or geographic filter is required.")
        params={"limit":min(max(int(parameters.get("limit",100)),1),int(connector.configuration_json.get("max_limit",300))),"offset":max(int(parameters.get("offset",0)),0)}
        for source,target in keys.items():
            if parameters.get(source) is not None: params[target]=parameters[source]
        return ConnectorRequest(method="GET",url=connector.base_url,params=params,headers={"User-Agent":settings.live_data_user_agent,"Accept":"application/json"})

    def normalize(self,response,*,connector,parameters,retrieved_at):
        payload=response.json(); observations=[]
        for row in payload.get("results") or []:
            key=str(row.get("key") or row.get("gbifID") or "")
            if not key: continue
            date=_record_date(row,"eventDate","lastInterpreted","modified",default=retrieved_at); lat=finite_float(row.get("decimalLatitude")); lon=finite_float(row.get("decimalLongitude")); geometry={"type":"Point","coordinates":[lon,lat]} if lat is not None and lon is not None else None
            name=_first_text(row.get("scientificName") or row.get("acceptedScientificName")) or f"GBIF occurrence {key}"
            license_name=_first_text(row.get("license"))
            observations.append(NormalizedObservation(source_record_id=key,domain="biodiversity",metric="species_occurrence",value_number=1.0,value_text=name,unit="occurrence",geometry=geometry,observed_at=date,published_at=_record_date(row,"modified","lastInterpreted",default=retrieved_at),freshness_status="occurrence_record",quality_status="source_reported",methodology_url="https://techdocs.gbif.org/en/openapi/",dimensions={"taxon_key":row.get("taxonKey"),"country_code":row.get("countryCode"),"basis_of_record":row.get("basisOfRecord"),"occurrence_status":row.get("occurrenceStatus")},metadata={"dataset_key":row.get("datasetKey"),"dataset_title":row.get("datasetTitle"),"issues":row.get("issues"),"record_license":license_name},scientific_record={"record_type":"biodiversity_occurrence","discipline":"biodiversity","title":name,"summary":_first_text(row.get("locality") or row.get("verbatimLocality")),"dataset_id":_first_text(row.get("datasetKey")),"collection":_first_text(row.get("datasetTitle")),"landing_page_url":f"https://www.gbif.org/occurrence/{key}","geometry":geometry,"observation_start":date,"observation_end":date,"published_at":_record_date(row,"modified","lastInterpreted",default=retrieved_at),"identifiers":{"gbif_id":key,"taxon_key":row.get("taxonKey"),"occurrence_id":row.get("occurrenceID")},"keywords":_list_text([row.get("kingdom"),row.get("phylum"),row.get("class"),row.get("order"),row.get("family"),row.get("genus")]),"quality_status":"source_reported","metadata":{"basis_of_record":row.get("basisOfRecord"),"issues":row.get("issues"),"record_license":license_name,"publishing_org_key":row.get("publishingOrgKey")}}))
        return payload,observations


class MaterialsProjectSummaryAdapter(ConnectorAdapter):
    adapter_id = "materials_project_summary_v1"

    def build_request(self,connector,parameters,settings)->ConnectorRequest:
        if not settings.materials_project_api_key: raise ValueError("SC_CORE_MATERIALS_PROJECT_API_KEY is required after free Materials Project registration.")
        allowed=("material_ids","formula","chemsys","elements")
        if not any(parameters.get(k) for k in allowed): raise ValueError("A material identifier, formula, chemical system, or element filter is required.")
        params={"_limit":min(max(int(parameters.get("limit",25)),1),100),"_fields":"material_id,formula_pretty,chemsys,nelements,nsites,volume,density,density_atomic,symmetry,energy_per_atom,formation_energy_per_atom,energy_above_hull,is_stable,band_gap,is_gap_direct,is_metal,total_magnetization,ordering,theoretical,database_IDs,last_updated,origins,warnings"}
        for key in allowed:
            if parameters.get(key) is not None: params[key]=parameters[key]
        return ConnectorRequest(method="GET",url=connector.base_url,params=params,headers={"X-API-KEY":settings.materials_project_api_key,"User-Agent":settings.live_data_user_agent,"Accept":"application/json"})

    def normalize(self,response,*,connector,parameters,retrieved_at):
        payload=response.json(); rows=payload.get("data") or []; observations=[]
        db_version=_first_text((payload.get("meta") or {}).get("db_version") or response.headers.get("X-DB-Version"))
        for row in rows:
            mid=str(row.get("material_id") or "")
            if not mid: continue
            title=_first_text(row.get("formula_pretty")) or mid; date=_record_date(row,"last_updated",default=retrieved_at)
            observations.append(NormalizedObservation(source_record_id=mid,domain="materials_science",metric="formation_energy_per_atom",value_number=finite_float(row.get("formation_energy_per_atom")),value_text=title,unit="eV/atom",observed_at=date,published_at=date,freshness_status="database_record",quality_status="computed",methodology_url="https://docs.materialsproject.org/downloading-data/using-the-api/getting-started",dimensions={"chemsys":row.get("chemsys"),"is_stable":row.get("is_stable"),"band_gap":row.get("band_gap"),"is_metal":row.get("is_metal")},metadata={"database_version":db_version,"summary":row},scientific_record={"record_type":"material","discipline":"materials_science","title":title,"summary":f"Computed Materials Project summary for {title}.","dataset_id":mid,"collection":"Materials Project","landing_page_url":f"https://next-gen.materialsproject.org/materials/{mid}","published_at":date,"identifiers":{"material_id":mid,"database_ids":row.get("database_IDs")},"keywords":_list_text([row.get("chemsys"),row.get("ordering")]),"variables":[key for key,value in row.items() if value is not None],"quality_status":"computed","metadata":{"database_version":db_version,"summary":row}}))
        return payload,observations


class MastObservationsAdapter(ConnectorAdapter):
    adapter_id = "mast_observations_v1"

    def build_request(self,connector,parameters,settings)->ConnectorRequest:
        filters=[]
        if parameters.get("target_name"): filters.append({"paramName":"target_name","values":[str(parameters["target_name"])]})
        if parameters.get("collection"): filters.append({"paramName":"obs_collection","values":[str(parameters["collection"])]})
        if parameters.get("instrument"): filters.append({"paramName":"instrument_name","values":[str(parameters["instrument"])]})
        request={"service":"Mast.Caom.Filtered","params":{"columns":"*","filters":filters},"format":"json","pagesize":min(max(int(parameters.get("limit",100)),1),int(connector.configuration_json.get("max_pagesize",200))),"page":1}
        if parameters.get("coordinates"):
            coords=str(parameters["coordinates"]).replace(","," ").split();
            if len(coords)!=2: raise ValueError("coordinates must contain RA and Dec.")
            request["service"]="Mast.Caom.Cone"; request["params"]={"ra":float(coords[0]),"dec":float(coords[1]),"radius":float(parameters.get("radius",0.2))}
        if not filters and request["service"]!="Mast.Caom.Cone": raise ValueError("A target, collection, or coordinates filter is required.")
        return ConnectorRequest(method="POST",url=connector.base_url,data={"request":json.dumps(request,separators=(",",":"))},headers={"User-Agent":settings.live_data_user_agent,"Accept":"application/json"})

    def normalize(self,response,*,connector,parameters,retrieved_at):
        payload=response.json(); observations=[]
        for row in payload.get("data") or []:
            obs_id=str(row.get("obsid") or row.get("obs_id") or row.get("productFilename") or "")
            if not obs_id: continue
            start=retrieved_at
            for key in ("t_min","obs_date","date_obs"):
                if row.get(key) is not None:
                    try:
                        if key=="t_min": start=datetime.fromtimestamp((float(row[key])-40587.0)*86400,tz=timezone.utc)
                        else: start=parse_datetime(row[key])
                        break
                    except (ValueError,TypeError,OverflowError): pass
            ra=finite_float(row.get("s_ra")); dec=finite_float(row.get("s_dec")); geometry={"type":"Point","coordinates":[ra,dec]} if ra is not None and dec is not None else None
            title=_first_text(row.get("target_name") or row.get("obs_id")) or f"MAST observation {obs_id}"
            collection=_first_text(row.get("obs_collection")); instrument=_first_text(row.get("instrument_name"))
            observations.append(NormalizedObservation(source_record_id=obs_id,domain="astronomy",metric="telescope_observation",value_number=1.0,value_text=title,unit="observation",geometry=geometry,observed_at=start,published_at=retrieved_at,freshness_status="archive_record",quality_status="archive_metadata",methodology_url="https://archive.stsci.edu/vo/mast_services.html",dimensions={"collection":collection,"instrument":instrument,"data_rights":row.get("dataRights"),"dataproduct_type":row.get("dataproduct_type")},metadata={"observation":row},scientific_record={"record_type":"telescope_observation","discipline":"astronomy","title":title,"summary":_first_text(row.get("proposal_title") or row.get("intentType")),"dataset_id":obs_id,"collection":collection,"mission":collection,"instrument":instrument,"target":_first_text(row.get("target_name")),"access_url":_first_text(row.get("dataURL")),"landing_page_url":f"https://mast.stsci.edu/portal/Mashup/Clients/Mast/Portal.html?searchQuery={quote(obs_id,safe='')}","geometry":geometry,"observation_start":start,"published_at":retrieved_at,"identifiers":{"obs_id":row.get("obs_id"),"obsid":row.get("obsid"),"proposal_id":row.get("proposal_id")},"keywords":_list_text([collection,instrument,row.get("dataproduct_type")]),"file_formats":_list_text(row.get("dataProductType") or row.get("dataproduct_type")),"quality_status":"archive_metadata","metadata":{"observation":row}}))
        return payload,observations


class HeasarcXaminAdapter(ConnectorAdapter):
    adapter_id = "heasarc_xamin_v1"

    def build_request(self,connector,parameters,settings)->ConnectorRequest:
        table=_safe_token(self._required(parameters,"table"),"table")
        params={"table":table,"format":"json","maxrows":min(max(int(parameters.get("maxrows",connector.configuration_json.get("default_maxrows",100))),1),500)}
        for key in ("position","radius","name","fields","sortvar"):
            if parameters.get(key) is not None: params[key]=parameters[key]
        return ConnectorRequest(method="GET",url=connector.base_url,params=params,headers={"User-Agent":settings.live_data_user_agent,"Accept":"application/json,text/csv,text/plain"})

    def normalize(self,response,*,connector,parameters,retrieved_at):
        try: payload=response.json()
        except ValueError:
            rows=list(csv.DictReader(io.StringIO(response.text))); payload={"rows":rows}
        rows=_tap_rows(payload); observations=[]; table=str(parameters.get("table"))
        for index,row in enumerate(rows):
            rid=str(row.get("id") or row.get("name") or row.get("seq_id") or row.get("obsid") or f"{table}:{index}")
            title=_first_text(row.get("name") or row.get("object") or row.get("target_name")) or f"HEASARC {table} record {rid}"
            ra=finite_float(row.get("ra") or row.get("ra_obj")); dec=finite_float(row.get("dec") or row.get("dec_obj")); geometry={"type":"Point","coordinates":[ra,dec]} if ra is not None and dec is not None else None
            observations.append(NormalizedObservation(source_record_id=rid,domain="astronomy",metric="high_energy_catalog_record",value_number=1.0,value_text=title,unit="record",geometry=geometry,observed_at=retrieved_at,published_at=retrieved_at,freshness_status="catalog",quality_status="archive_metadata",methodology_url="https://heasarc.gsfc.nasa.gov/docs/archive/apis.html",dimensions={"table":table},metadata={"record":row},scientific_record={"record_type":"astronomy_catalog_record","discipline":"high_energy_astrophysics","title":title,"summary":f"HEASARC public catalog record from {table}.","dataset_id":table,"collection":table,"mission":_first_text(row.get("mission") or row.get("observatory")),"instrument":_first_text(row.get("instrument")),"target":_first_text(row.get("name") or row.get("object")),"geometry":geometry,"published_at":retrieved_at,"identifiers":{"record_id":rid},"variables":[key for key,value in row.items() if value is not None],"quality_status":"archive_metadata","metadata":{"record":row}}))
        return payload,observations


class IvoaTapJsonAdapter(ConnectorAdapter):
    adapter_id = "ivoa_tap_json_v1"

    def build_request(self,connector,parameters,settings)->ConnectorRequest:
        query=_safe_adql(self._required(parameters,"query")); maxrec=min(max(int(parameters.get("maxrec",connector.configuration_json.get("maxrec",200))),1),500)
        return ConnectorRequest(method="GET",url=connector.base_url,params={"REQUEST":"doQuery","LANG":"ADQL","FORMAT":"json","MAXREC":maxrec,"QUERY":query},headers={"User-Agent":settings.live_data_user_agent,"Accept":"application/json"})

    def normalize(self,response,*,connector,parameters,retrieved_at):
        payload=response.json(); rows=_tap_rows(payload); archive=str(connector.configuration_json.get("archive") or connector.source_id); observations=[]
        for index,row in enumerate(rows):
            rid=str(row.get("obs_publisher_did") or row.get("obs_id") or row.get("source_id") or row.get("main_id") or f"{archive}:{index}")
            title=_first_text(row.get("target_name") or row.get("obs_id") or row.get("main_id") or row.get("source_id")) or f"{archive} record {rid}"
            ra=finite_float(row.get("s_ra") or row.get("ra")); dec=finite_float(row.get("s_dec") or row.get("dec")); geometry={"type":"Point","coordinates":[ra,dec]} if ra is not None and dec is not None else None
            start=retrieved_at
            for key in ("t_min","date_obs","obs_date"):
                if row.get(key) is not None:
                    try:
                        start=datetime.fromtimestamp((float(row[key])-40587.0)*86400,tz=timezone.utc) if key=="t_min" else parse_datetime(row[key]); break
                    except (ValueError,TypeError,OverflowError): pass
            collection=_first_text(row.get("obs_collection") or row.get("collection") or archive); instrument=_first_text(row.get("instrument_name") or row.get("instrument")); access=_first_text(row.get("access_url"))
            observations.append(NormalizedObservation(source_record_id=rid,domain="astronomy",metric="archive_record",value_number=1.0,value_text=title,unit="record",geometry=geometry,observed_at=start,published_at=retrieved_at,freshness_status="archive_record",quality_status="archive_metadata",methodology_url=connector.source_id,dimensions={"archive":archive,"collection":collection,"instrument":instrument,"data_product_type":row.get("dataproduct_type")},metadata={"record":row},scientific_record={"record_type":"telescope_observation" if row.get("obs_id") or row.get("obs_publisher_did") else "astronomy_catalog_record","discipline":"astronomy","title":title,"summary":_first_text(row.get("obs_title") or row.get("proposal_title")),"dataset_id":rid,"collection":collection,"mission":_first_text(row.get("facility_name") or row.get("telescope_name") or collection),"instrument":instrument,"target":_first_text(row.get("target_name") or row.get("main_id")),"access_url":access,"geometry":geometry,"observation_start":start,"published_at":retrieved_at,"identifiers":{"publisher_did":row.get("obs_publisher_did"),"obs_id":row.get("obs_id"),"source_id":row.get("source_id")},"keywords":_list_text([archive,collection,instrument,row.get("dataproduct_type")]),"file_formats":_list_text(row.get("access_format")),"quality_status":"archive_metadata","metadata":{"record":row,"query":parameters.get("query")}}))
        return payload,observations


ADAPTERS: dict[str, ConnectorAdapter] = {
    adapter.adapter_id: adapter
    for adapter in (
        MetLocationforecastAdapter(),
        NasaGibsWmtsAdapter(),
        UsgsEarthquakeAdapter(),
        WorldBankIndicatorsAdapter(),
        FredSeriesObservationsAdapter(),
        UnSdgCatalogAdapter(),
        UnDigitalLibraryAdapter(),
        UnSdgMetadataAdapter(),
        ReliefWebReportsAdapter(),
        HdxHapiAdapter(),
        UnPopulationDataAdapter(),
        UnComtradeAdapter(),
        UnhcrPopulationAdapter(),
        OhchrUhriAdapter(),
        NasaCmrCollectionsAdapter(),
        NasaApodAdapter(),
        NoaaNceiDataAdapter(),
        EcmwfOpenDataIndexAdapter(),
        UsgsWaterInstantaneousAdapter(),
        NcbiEntrezSearchAdapter(),
        PubchemCompoundPropertiesAdapter(),
        GbifOccurrenceSearchAdapter(),
        MaterialsProjectSummaryAdapter(),
        MastObservationsAdapter(),
        HeasarcXaminAdapter(),
        IvoaTapJsonAdapter(),
    )
}
