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


# v2.9.0 streaming endpoint helper. SSE clients should send the normal Bearer credential.
def _reliability_stream_url(self, *, after_id: int = 0, event_type: str | None = None, once: bool = False):
    from urllib.parse import urlencode
    params = {"after_id": after_id, "once": str(once).lower()}
    if event_type:
        params["event_type"] = event_type
    return f"{self.base_url}/api/v1/reliability/stream?{urlencode(params)}"

PublicApiClient.reliability_stream_url = _reliability_stream_url


# v2.10.0 operational facility registry helpers
def _facilities(self, **params):
    clean={k:v for k,v in params.items() if v is not None}
    return self.request("GET", "/facilities", params=clean)

def _facility(self, facility_id: str):
    return self.request("GET", f"/facilities/{facility_id}")

def _facility_observations(self, facility_id: str, **params):
    clean={k:v for k,v in params.items() if v is not None}
    return self.request("GET", f"/facilities/{facility_id}/observations", params=clean)

PublicApiClient.facilities = _facilities
PublicApiClient.facility = _facility
PublicApiClient.facility_observations = _facility_observations


# v2.11.0 humanitarian access helpers
def _humanitarian_conditions(self, **params):
    clean={k:v for k,v in params.items() if v is not None}
    return self.request("GET", "/humanitarian/conditions", params=clean)

def _humanitarian_country_summary(self, country_code: str):
    return self.request("GET", f"/humanitarian/country/{country_code}/summary")

PublicApiClient.humanitarian_conditions = _humanitarian_conditions
PublicApiClient.humanitarian_country_summary = _humanitarian_country_summary


# v2.12.0 country evidence federation and reconciliation helpers
def _country_evidence_federation(self, country_code: str):
    return self.request("GET", f"/country-evidence/country/{country_code}/federation")

def _country_evidence_reconcile(self, country_code: str, concept: str):
    return self.request("GET", f"/country-evidence/country/{country_code}/reconcile", params={"concept": concept})

PublicApiClient.country_evidence_federation = _country_evidence_federation
PublicApiClient.country_evidence_reconcile = _country_evidence_reconcile

# v2.13.0 Earth, Ocean, Space & Scientific Service Fabric helpers
def _scientific_domains(self):
    return self.request("GET", "/scientific-fabric/domains")

def _scientific_domain(self, domain: str):
    return self.request("GET", f"/scientific-fabric/domains/{domain}")

def _scientific_domain_records(self, domain: str, **params):
    clean={k:v for k,v in params.items() if v is not None}
    return self.request("GET", f"/scientific-fabric/domains/{domain}/records", params=clean)

def _scientific_domain_assets(self, domain: str, **params):
    clean={k:v for k,v in params.items() if v is not None}
    return self.request("GET", f"/scientific-fabric/domains/{domain}/assets", params=clean)

def _scientific_domain_time_series(self, domain: str, **params):
    clean={k:v for k,v in params.items() if v is not None}
    return self.request("GET", f"/scientific-fabric/domains/{domain}/timeseries", params=clean)

def _scientific_domain_map_layers(self, domain: str, **params):
    clean={k:v for k,v in params.items() if v is not None}
    return self.request("GET", f"/scientific-fabric/domains/{domain}/map-layers", params=clean)

PublicApiClient.scientific_domains = _scientific_domains
PublicApiClient.scientific_domain = _scientific_domain
PublicApiClient.scientific_domain_records = _scientific_domain_records
PublicApiClient.scientific_domain_assets = _scientific_domain_assets
PublicApiClient.scientific_domain_time_series = _scientific_domain_time_series
PublicApiClient.scientific_domain_map_layers = _scientific_domain_map_layers


# v2.14.0 Cross-Product Evidence Exchange public readiness helper
def _cross_product_exchange_readiness(self):
    return self.request("GET", "/exchange/readiness")

PublicApiClient.cross_product_exchange_readiness = _cross_product_exchange_readiness


# v2.15.0 Distributed Processing, Storage & Scale public readiness helper
def _scale_readiness(self):
    return self.request("GET", "/scale/readiness")

PublicApiClient.scale_readiness = _scale_readiness


# v2.16.0 Governance, Access & Audit public readiness helper
def _governance_readiness(self):
    return self.request("GET", "/governance/readiness")

PublicApiClient.governance_readiness = _governance_readiness


# v2.18.0 Production Certification public readiness helper
def _certification_readiness(self):
    return self.request("GET", "/certification/readiness")
PublicApiClient.certification_readiness = _certification_readiness


# v2.18.0 Observability public status helper
def _observability_status(self):
    return self.request("GET", "/observability/status")
PublicApiClient.observability_status = _observability_status


# v2.19.0 Incident Response & Change Control public status helper
def _operations_status(self):
    return self.request("GET", "/operations/status")
PublicApiClient.operations_status = _operations_status


# v2.20.0 Continuity & Disaster Recovery public status helper
def _continuity_status(self):
    return self.request("GET", "/continuity/status")
PublicApiClient.continuity_status = _continuity_status


# v2.21.0 Multi-Region Resilience public status helper
def _resilience_status(self):
    return self.request("GET", "/resilience/status")
PublicApiClient.resilience_status = _resilience_status

def _lifecycle_status(self):
    return self.request("GET", "/lifecycle/status")
PublicApiClient.lifecycle_status = _lifecycle_status


# v2.23.0 Federated Core public status helper
def _federation_status(self):
    return self.request("GET", "/federation/status")
PublicApiClient.federation_status = _federation_status


# v2.24.0 Capacity Forecasting & Resource Governance public status helper
def _capacity_status(self):
    return self.request("GET", "/capacity/status")

PublicApiClient.capacity_status = _capacity_status
