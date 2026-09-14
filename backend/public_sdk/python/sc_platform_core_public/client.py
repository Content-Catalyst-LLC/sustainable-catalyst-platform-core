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


# v2.25.0 Identity, Credential & Cryptographic Key Lifecycle public status helper
def _credential_lifecycle_status(self):
    return self.request("GET", "/credentials/status")

PublicApiClient.credential_lifecycle_status = _credential_lifecycle_status


def _workload_governance_status(self):
    return self.request("GET", "/workload-governance/status")

PublicApiClient.workload_governance_status = _workload_governance_status


# v2.27.0 scientific object storage and processing adapter metadata methods.
def _scientific_object_storage_readiness(self):
    return self.request("GET", "/scientific-objects/readiness")

def _scientific_stored_objects(self, **params):
    clean={k:v for k,v in params.items() if v is not None}
    return self.request("GET", "/scientific-objects", params=clean)

def _scientific_stored_object(self, object_id: str):
    return self.request("GET", f"/scientific-objects/{object_id}")

def _scientific_processing_adapters(self):
    return self.request("GET", "/scientific-objects/adapters")

PublicApiClient.scientific_object_storage_readiness = _scientific_object_storage_readiness
PublicApiClient.scientific_stored_objects = _scientific_stored_objects
PublicApiClient.scientific_stored_object = _scientific_stored_object
PublicApiClient.scientific_processing_adapters = _scientific_processing_adapters


# v2.28.0 Research Object & Model Foundation public metadata methods.
def _research_object_readiness(self):
    return self.request("GET", "/research-objects/readiness")

def _research_objects(self, **params):
    clean={k:v for k,v in params.items() if v is not None}
    return self.request("GET", "/research-objects", params=clean)

def _research_object(self, entity_id: str):
    return self.request("GET", f"/research-objects/{entity_id}")

def _research_project_bundle(self, project_entity_id: str):
    return self.request("GET", f"/research-objects/projects/{project_entity_id}/bundle")

PublicApiClient.research_object_readiness = _research_object_readiness
PublicApiClient.research_objects = _research_objects
PublicApiClient.research_object = _research_object
PublicApiClient.research_project_bundle = _research_project_bundle


# v2.29.0 Visual Reasoning Object Model public metadata methods.
def _visual_reasoning_readiness(self):
    return self.request("GET", "/visual-reasoning/readiness")

def _visual_reasoning_objects(self, **params):
    clean={k:v for k,v in params.items() if v is not None}
    return self.request("GET", "/visual-reasoning/objects", params=clean)

def _visual_reasoning_object(self, entity_id: str):
    return self.request("GET", f"/visual-reasoning/objects/{entity_id}")

def _visual_reasoning_bundle(self, entity_id: str):
    return self.request("GET", f"/visual-reasoning/objects/{entity_id}/bundle")

PublicApiClient.visual_reasoning_readiness = _visual_reasoning_readiness
PublicApiClient.visual_reasoning_objects = _visual_reasoning_objects
PublicApiClient.visual_reasoning_object = _visual_reasoning_object
PublicApiClient.visual_reasoning_bundle = _visual_reasoning_bundle


# v2.30.0 Visualization Specification & Renderer Registry public metadata methods.
def _visualization_readiness(self):
    return self.request("GET", "/visualization/readiness")

def _visualization_renderers(self):
    return self.request("GET", "/visualization/renderers")

def _visualization_specifications(self, **params):
    clean={k:v for k,v in params.items() if v is not None}
    return self.request("GET", "/visualization/specifications", params=clean)

PublicApiClient.visualization_readiness = _visualization_readiness
PublicApiClient.visualization_renderers = _visualization_renderers
PublicApiClient.visualization_specifications = _visualization_specifications


# v2.31.0 System Maps public metadata methods.
def _system_maps_readiness(self):
    return self.request("GET", "/system-maps/readiness")

def _system_maps(self, **params):
    clean={k:v for k,v in params.items() if v is not None}
    return self.request("GET", "/system-maps", params=clean)

def _system_map(self, entity_id: str):
    return self.request("GET", f"/system-maps/{entity_id}")

def _system_map_bundle(self, entity_id: str):
    return self.request("GET", f"/system-maps/{entity_id}/bundle")

PublicApiClient.system_maps_readiness = _system_maps_readiness
PublicApiClient.system_maps = _system_maps
PublicApiClient.system_map = _system_map
PublicApiClient.system_map_bundle = _system_map_bundle


# v2.32.0 Flow Maps public metadata methods.
def _flow_maps_readiness(self):
    return self.request("GET", "/flow-maps/readiness")

def _flow_maps(self, **params):
    clean={k:v for k,v in params.items() if v is not None}
    return self.request("GET", "/flow-maps", params=clean)

def _flow_map(self, entity_id: str):
    return self.request("GET", f"/flow-maps/{entity_id}")

def _flow_map_bundle(self, entity_id: str):
    return self.request("GET", f"/flow-maps/{entity_id}/bundle")

def _flow_map_balance(self, entity_id: str):
    return self.request("GET", f"/flow-maps/{entity_id}/balance")

PublicApiClient.flow_maps_readiness = _flow_maps_readiness
PublicApiClient.flow_maps = _flow_maps
PublicApiClient.flow_map = _flow_map
PublicApiClient.flow_map_bundle = _flow_map_bundle
PublicApiClient.flow_map_balance = _flow_map_balance


# v2.33.0 Scenario Landscapes public metadata methods.
def _scenario_landscapes_readiness(self):
    return self.request("GET", "/scenario-landscapes/readiness")

def _scenario_landscapes(self, **params):
    clean={k:v for k,v in params.items() if v is not None}
    return self.request("GET", "/scenario-landscapes", params=clean)

def _scenario_landscape(self, entity_id: str):
    return self.request("GET", f"/scenario-landscapes/{entity_id}")

def _scenario_landscape_bundle(self, entity_id: str):
    return self.request("GET", f"/scenario-landscapes/{entity_id}/bundle")

def _scenario_landscape_comparison(self, entity_id: str):
    return self.request("GET", f"/scenario-landscapes/{entity_id}/comparison")

PublicApiClient.scenario_landscapes_readiness = _scenario_landscapes_readiness
PublicApiClient.scenario_landscapes = _scenario_landscapes
PublicApiClient.scenario_landscape = _scenario_landscape
PublicApiClient.scenario_landscape_bundle = _scenario_landscape_bundle
PublicApiClient.scenario_landscape_comparison = _scenario_landscape_comparison


# v2.34.0 Interactive Model Canvas public metadata methods.
def _model_canvases_readiness(self):
    return self.request("GET", "/model-canvases/readiness")

def _model_canvases(self, **params):
    clean={k:v for k,v in params.items() if v is not None}
    return self.request("GET", "/model-canvases", params=clean)

def _model_canvas(self, entity_id: str):
    return self.request("GET", f"/model-canvases/{entity_id}")

def _model_canvas_bundle(self, entity_id: str):
    return self.request("GET", f"/model-canvases/{entity_id}/bundle")

PublicApiClient.model_canvases_readiness = _model_canvases_readiness
PublicApiClient.model_canvases = _model_canvases
PublicApiClient.model_canvas = _model_canvas
PublicApiClient.model_canvas_bundle = _model_canvas_bundle


# v2.35.0 Scenario Compute Engine public metadata helpers
def _scenario_compute_readiness(self):
    return self.request("GET", "/scenario-compute/readiness")

def _scenario_compute_plans(self, **params):
    return self.request("GET", "/scenario-compute/plans", params=params)

def _scenario_compute_plan(self, plan_id: str):
    return self.request("GET", f"/scenario-compute/plans/{plan_id}")

def _scenario_compute_plan_bundle(self, plan_id: str):
    return self.request("GET", f"/scenario-compute/plans/{plan_id}/bundle")

PublicApiClient.scenario_compute_readiness = _scenario_compute_readiness
PublicApiClient.scenario_compute_plans = _scenario_compute_plans
PublicApiClient.scenario_compute_plan = _scenario_compute_plan
PublicApiClient.scenario_compute_plan_bundle = _scenario_compute_plan_bundle


# v2.36.0 Uncertainty, Sensitivity & Ensemble Reasoning public metadata helpers
def _uncertainty_reasoning_readiness(self):
    return self.request("GET", "/uncertainty-reasoning/readiness")

def _uncertainty_definitions(self, **params):
    return self.request("GET", "/uncertainty-reasoning/uncertainties", params=params)

def _sensitivity_studies(self, **params):
    return self.request("GET", "/uncertainty-reasoning/sensitivity-studies", params=params)

def _sensitivity_study_summary(self, study_id: str):
    return self.request("GET", f"/uncertainty-reasoning/sensitivity-studies/{study_id}/summary")

def _ensembles(self, **params):
    return self.request("GET", "/uncertainty-reasoning/ensembles", params=params)

def _ensemble_summary(self, ensemble_id: str):
    return self.request("GET", f"/uncertainty-reasoning/ensembles/{ensemble_id}/summary")

PublicApiClient.uncertainty_reasoning_readiness = _uncertainty_reasoning_readiness
PublicApiClient.uncertainty_definitions = _uncertainty_definitions
PublicApiClient.sensitivity_studies = _sensitivity_studies
PublicApiClient.sensitivity_study_summary = _sensitivity_study_summary
PublicApiClient.ensembles = _ensembles
PublicApiClient.ensemble_summary = _ensemble_summary


# v2.36.1.1 Uncertainty Compute Runtime public metadata helper
def _uncertainty_compute_readiness(self):
    return self.request("GET", "/uncertainty-compute/readiness")

PublicApiClient.uncertainty_compute_readiness = _uncertainty_compute_readiness


# v2.37.0 Causal Systems Explorer public metadata helpers
def _causal_systems_readiness(self):
    return self.request("GET", "/causal-systems/readiness")

def _causal_systems_graphs(self, **params):
    return self.request("GET", "/causal-systems/graphs", params=params)

def _causal_systems_bundle(self, graph_id: str):
    return self.request("GET", f"/causal-systems/graphs/{graph_id}/bundle")

PublicApiClient.causal_systems_readiness = _causal_systems_readiness
PublicApiClient.causal_systems_graphs = _causal_systems_graphs
PublicApiClient.causal_systems_bundle = _causal_systems_bundle


# v2.38.0 Spatial & Temporal Visual Reasoning public metadata helpers
def _spatial_temporal_readiness(self):
    return self.request("GET", "/spatial-temporal/readiness")
def _spatial_temporal_scenes(self, **params):
    return self.request("GET", "/spatial-temporal/scenes", params=params)
def _spatial_temporal_bundle(self, scene_id: str):
    return self.request("GET", f"/spatial-temporal/scenes/{scene_id}/bundle")
PublicApiClient.spatial_temporal_readiness = _spatial_temporal_readiness
PublicApiClient.spatial_temporal_scenes = _spatial_temporal_scenes
PublicApiClient.spatial_temporal_bundle = _spatial_temporal_bundle


# v2.39.0 Research Librarian Visual Explanation public metadata helpers
def _research_visual_explanations_readiness(self):
    return self.request("GET", "/research-visual-explanations/readiness")
def _research_visual_explanations(self, **params):
    return self.request("GET", "/research-visual-explanations", params=params)
def _research_visual_explanation_bundle(self, explanation_id: str):
    return self.request("GET", f"/research-visual-explanations/{explanation_id}/bundle")
PublicApiClient.research_visual_explanations_readiness = _research_visual_explanations_readiness
PublicApiClient.research_visual_explanations = _research_visual_explanations
PublicApiClient.research_visual_explanation_bundle = _research_visual_explanation_bundle


# v2.40.0 Cross-Product Visual Research Objects public metadata helpers
def _cross_product_visual_research_readiness(self):
    return self.request("GET", "/cross-product-visual-research/readiness")
def _cross_product_visual_research_objects(self, **params):
    return self.request("GET", "/cross-product-visual-research", params=params)
def _cross_product_visual_research_bundle(self, object_id: str):
    return self.request("GET", f"/cross-product-visual-research/{object_id}/bundle")
PublicApiClient.cross_product_visual_research_readiness = _cross_product_visual_research_readiness
PublicApiClient.cross_product_visual_research_objects = _cross_product_visual_research_objects
PublicApiClient.cross_product_visual_research_bundle = _cross_product_visual_research_bundle


def _reproducible_visual_knowledge_readiness(self):
    return self.request("GET", "/reproducible-visual-knowledge/readiness")
def _reproducible_visual_knowledge_packages(self, **params):
    return self.request("GET", "/reproducible-visual-knowledge", params=params)
def _reproducible_visual_knowledge_bundle(self, package_id: str):
    return self.request("GET", f"/reproducible-visual-knowledge/{package_id}/bundle")
PublicApiClient.reproducible_visual_knowledge_readiness = _reproducible_visual_knowledge_readiness
PublicApiClient.reproducible_visual_knowledge_packages = _reproducible_visual_knowledge_packages
PublicApiClient.reproducible_visual_knowledge_bundle = _reproducible_visual_knowledge_bundle


# v2.43.0 Open Forensics — Evidence Integrity & Chain of Custody.
def _open_forensics_readiness(self):
    return self.request("GET", "/open-forensics/readiness")

def _open_forensics_investigations(self, **params):
    return self.request("GET", "/open-forensics/investigations", params=params)

def _open_forensics_investigation_bundle(self, investigation_id: str):
    return self.request("GET", f"/open-forensics/investigations/{investigation_id}/bundle")

PublicApiClient.open_forensics_readiness = _open_forensics_readiness
PublicApiClient.open_forensics_investigations = _open_forensics_investigations
PublicApiClient.open_forensics_investigation_bundle = _open_forensics_investigation_bundle


def _open_forensics_custody_chain(self, investigation_id: str, evidence_id: str):
    return self.request("GET", f"/open-forensics/investigations/{investigation_id}/evidence/{evidence_id}/custody-chain")
def _open_forensics_custody_bundle(self, investigation_id: str):
    return self.request("GET", f"/open-forensics/investigations/{investigation_id}/custody-bundle")
PublicApiClient.open_forensics_custody_chain = _open_forensics_custody_chain
PublicApiClient.open_forensics_custody_bundle = _open_forensics_custody_bundle


# v2.44.0 Open Forensics — Claims, Contradictions & Competing Hypotheses.
def _open_forensics_claim_map(self, investigation_id: str):
    return self.request("GET", f"/open-forensics/investigations/{investigation_id}/claim-map")
def _open_forensics_hypothesis_matrix(self, investigation_id: str):
    return self.request("GET", f"/open-forensics/investigations/{investigation_id}/hypothesis-matrix")
def _open_forensics_reasoning_bundle(self, investigation_id: str):
    return self.request("GET", f"/open-forensics/investigations/{investigation_id}/reasoning-bundle")
PublicApiClient.open_forensics_claim_map = _open_forensics_claim_map
PublicApiClient.open_forensics_hypothesis_matrix = _open_forensics_hypothesis_matrix
PublicApiClient.open_forensics_reasoning_bundle = _open_forensics_reasoning_bundle


# v2.45.0 Open Forensics — Forensic Timeline & Event Reconstruction.
def _open_forensics_timeline(self, investigation_id: str):
    return self.request("GET", f"/open-forensics/investigations/{investigation_id}/timeline")
def _open_forensics_timeline_specification(self, investigation_id: str):
    return self.request("GET", f"/open-forensics/investigations/{investigation_id}/timeline-specification")
PublicApiClient.open_forensics_timeline = _open_forensics_timeline
PublicApiClient.open_forensics_timeline_specification = _open_forensics_timeline_specification


# v2.46.0 Open Forensics — Forensic Spatial/Temporal Evidence Integration.
def _open_forensics_spatial_temporal_evidence(self, investigation_id: str):
    return self.request("GET", f"/open-forensics/investigations/{investigation_id}/spatial-temporal-evidence")
def _open_forensics_forensic_scene_specification(self, investigation_id: str):
    return self.request("GET", f"/open-forensics/investigations/{investigation_id}/forensic-scene-specification")
def _open_forensics_site_intelligence_handoff(self, investigation_id: str):
    return self.request("GET", f"/open-forensics/investigations/{investigation_id}/site-intelligence-handoff")
PublicApiClient.open_forensics_spatial_temporal_evidence = _open_forensics_spatial_temporal_evidence
PublicApiClient.open_forensics_forensic_scene_specification = _open_forensics_forensic_scene_specification
PublicApiClient.open_forensics_site_intelligence_handoff = _open_forensics_site_intelligence_handoff

# v2.47.0 Open Forensics — Media Artifact & Derivative Provenance.
def _open_forensics_media_provenance(self, investigation_id: str):
    return self.request("GET", f"/open-forensics/investigations/{investigation_id}/media-provenance")
def _open_forensics_media_lineage_graph(self, investigation_id: str):
    return self.request("GET", f"/open-forensics/investigations/{investigation_id}/media-lineage-graph")
def _open_forensics_media_comparison_bundle(self, investigation_id: str):
    return self.request("GET", f"/open-forensics/investigations/{investigation_id}/media-comparison-bundle")
PublicApiClient.open_forensics_media_provenance = _open_forensics_media_provenance
PublicApiClient.open_forensics_media_lineage_graph = _open_forensics_media_lineage_graph
PublicApiClient.open_forensics_media_comparison_bundle = _open_forensics_media_comparison_bundle


# v2.48.0 Open Forensics — Quantitative Reconstruction & Reproduction Handoffs.
def _open_forensics_quantitative_reconstructions(self, investigation_id: str):
    return self.request("GET", f"/open-forensics/investigations/{investigation_id}/quantitative-reconstructions")
PublicApiClient.open_forensics_quantitative_reconstructions = _open_forensics_quantitative_reconstructions
