from __future__ import annotations

from typing import Any
import httpx


class PublicApiError(RuntimeError):
    pass


class PublicApiClient:
    def __init__(
        self,
        base_url: str,
        api_key: str,
        *,
        timeout: float = 20.0,
    ):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.timeout = timeout

    def request(
        self,
        method: str,
        path: str,
        **kwargs: Any,
    ) -> Any:
        response = httpx.request(
            method,
            f"{self.base_url}/api/v1{path}",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Accept": "application/json",
            },
            timeout=self.timeout,
            **kwargs,
        )
        if response.is_error:
            raise PublicApiError(
                f"{response.status_code}: {response.text}"
            )
        payload = response.json()
        return payload["data"]

    def request_raw(self, method: str, path: str, **kwargs: Any) -> Any:
        response = httpx.request(
            method,
            f"{self.base_url}/api/v1{path}",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Accept": "application/json",
            },
            timeout=self.timeout,
            **kwargs,
        )
        if response.is_error:
            raise PublicApiError(f"{response.status_code}: {response.text}")
        return response.json()

    def status(self):
        return self.request("GET", "/status")

    def entities(self, **params):
        return self.request("GET", "/entities", params=params)

    def entity(self, entity_id: str):
        return self.request("GET", f"/entities/{entity_id}")

    def graph(self, entity_id: str, **params):
        return self.request("GET", f"/graph/{entity_id}", params=params)

    def graph_path(self, source_id: str, target_id: str, **params):
        values = {"source_id": source_id, "target_id": target_id, **params}
        return self.request("GET", "/graph/path", params=values)

    def claims(self, **params):
        return self.request("GET", "/claims", params=params)

    def evidence_records(self, **params):
        return self.request("GET", "/evidence-records", params=params)

    def evidence_manifest(self, claim_id: str):
        return self.request("GET", f"/evidence/manifests/{claim_id}")

    def verify_ledger(self):
        return self.request("GET", "/ledger/verify")

    def trust_status(self):
        return self.request("GET", "/trust/status")

    def trust_evaluations(self, **params):
        return self.request("GET", "/trust/evaluations", params=params)

    def trust_incidents(self, include_resolved: bool = False):
        return self.request("GET", "/trust/incidents", params={"include_resolved": include_resolved})

    def trust_limitations(self, include_retired: bool = False):
        return self.request("GET", "/trust/limitations", params={"include_retired": include_retired})

    def trust_attestations(self):
        return self.request("GET", "/trust/attestations")

    def identity(self):
        return self.request("GET", "/developer/me")

    def usage(self, days: int = 30):
        return self.request("GET", "/developer/usage", params={"days": days})

    def workflow_definitions(self):
        return self.request("GET", "/workflow-definitions")

    def workflow_run(self, run_id: str):
        return self.request("GET", f"/workflow-runs/{run_id}")

    def dossiers(self, **params):
        return self.request("GET", "/dossiers", params=params)

    def dossier(self, dossier_id: str):
        return self.request("GET", f"/dossiers/{dossier_id}")

    def verify_dossier(self, dossier_id: str):
        return self.request("GET", f"/dossiers/{dossier_id}/verify")


    def live_sources(self):
        return self.request("GET", "/live/sources")

    def live_connectors(self, **params):
        return self.request("GET", "/live/connectors", params=params)

    def live_observations(self, **params):
        return self.request("GET", "/live/observations/latest", params=params)

    def live_timeseries(self, metric: str, **params):
        return self.request("GET", "/live/timeseries", params={"metric": metric, **params})

    def live_provenance(self, observation_id: str):
        return self.request("GET", f"/live/provenance/{observation_id}")

    def international_law_records(self, **params):
        return self.request("GET", "/international-law/records", params=params)

    def international_law_record(self, record_id: str):
        return self.request("GET", f"/international-law/records/{record_id}")

    def international_law_authority_taxonomy(self):
        return self.request("GET", "/international-law/authority-taxonomy")


# v2.7.2 scientific-data methods are attached here to retain backward-compatible class layout.
def _scientific_records(self, **params):
    return self.request("GET", "/science/records", params=params)

def _scientific_record(self, record_id: str):
    return self.request("GET", f"/science/records/{record_id}")

def _scientific_record_types(self):
    return self.request("GET", "/science/record-types")

PublicApiClient.scientific_records = _scientific_records
PublicApiClient.scientific_record = _scientific_record
PublicApiClient.scientific_record_types = _scientific_record_types


# v2.7.3 official-statistics methods retain the established public request path.
def _economic_records(self, **params):
    return self.request("GET", "/economics/records", params=params)

def _economic_record(self, record_id: str):
    return self.request("GET", f"/economics/records/{record_id}")

def _economic_record_types(self):
    return self.request("GET", "/economics/record-types")

PublicApiClient.economic_records = _economic_records
PublicApiClient.economic_record = _economic_record
PublicApiClient.economic_record_types = _economic_record_types


# v2.8.0 geospatial, time-series, scientific-asset, and map-layer methods.
def _fabric_capabilities(self):
    return self.request("GET", "/fabric/capabilities")

def _geospatial_features(self, **params):
    return self.request("GET", "/fabric/features", params=params)

def _time_series(self, **params):
    return self.request("GET", "/fabric/timeseries", params=params)

def _time_series_points(self, series_id: str, **params):
    return self.request("GET", f"/fabric/timeseries/{series_id}/points", params=params)

def _scientific_assets(self, **params):
    return self.request("GET", "/fabric/assets", params=params)

def _map_layers(self, **params):
    return self.request("GET", "/fabric/map-layers", params=params)

PublicApiClient.fabric_capabilities = _fabric_capabilities
PublicApiClient.geospatial_features = _geospatial_features
PublicApiClient.time_series = _time_series
PublicApiClient.time_series_points = _time_series_points
PublicApiClient.scientific_assets = _scientific_assets
PublicApiClient.map_layers = _map_layers


def _stac_catalog(self):
    return self.request_raw("GET", "/stac")

def _stac_collections(self, **params):
    return self.request_raw("GET", "/stac/collections", params=params)

def _stac_search(self, **params):
    return self.request_raw("GET", "/stac/search", params=params)

PublicApiClient.stac_catalog = _stac_catalog
PublicApiClient.stac_collections = _stac_collections
PublicApiClient.stac_search = _stac_search
