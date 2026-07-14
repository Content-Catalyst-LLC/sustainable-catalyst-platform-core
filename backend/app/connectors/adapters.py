from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
import math
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
    )
}
