from __future__ import annotations
from typing import Any
import httpx

class PlatformCoreError(RuntimeError):
    pass

class PlatformCoreClient:
    def __init__(self, base_url: str, *, api_key: str | None = None, timeout: float = 15.0):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.timeout = timeout

    def _headers(self, write: bool = False) -> dict[str, str]:
        headers = {"Accept": "application/json"}
        if write and self.api_key:
            headers["X-SC-API-Key"] = self.api_key
        return headers

    def _request(self, method: str, path: str, *, write: bool = False, **kwargs: Any) -> Any:
        response = httpx.request(method, f"{self.base_url}{path}", headers=self._headers(write=write), timeout=self.timeout, **kwargs)
        if response.is_error:
            raise PlatformCoreError(f"{response.status_code}: {response.text}")
        return response.json()

    def health(self): return self._request("GET", "/health")
    def stats(self): return self._request("GET", "/v1/stats")
    def get_entity(self, entity_id: str): return self._request("GET", f"/v1/entities/{entity_id}")
    def get_entity_jsonld(self, entity_id: str): return self._request("GET", f"/v1/entities/{entity_id}/jsonld")
    def list_predicates(self): return self._request("GET", "/v1/predicates")

    def list_entities(self, *, entity_type: str | None = None, query: str | None = None, limit: int = 50):
        params = {"limit": limit}
        if entity_type: params["entity_type"] = entity_type
        if query: params["q"] = query
        return self._request("GET", "/v1/entities", params=params)

    def create_entity(self, payload: dict[str, Any]):
        return self._request("POST", "/v1/entities", write=True, json=payload)

    def create_relationship(self, payload: dict[str, Any]):
        return self._request("POST", "/v1/relationships", write=True, json=payload)

    def review_relationship(self, relationship_id: str, *, decision: str, reviewer: str, note: str | None = None):
        return self._request("POST", f"/v1/relationships/{relationship_id}/reviews", write=True, json={"decision": decision, "reviewer": reviewer, "note": note, "metadata": {}})

    def graph(self, entity_id: str, *, direction: str = "both", depth: int = 1, predicates: list[str] | None = None):
        params: list[tuple[str, str | int]] = [("direction", direction), ("depth", depth)]
        for predicate in predicates or []:
            params.append(("predicates", predicate))
        return self._request("GET", f"/v1/graph/{entity_id}", params=params)

    def path(self, source_id: str, target_id: str, *, depth: int = 4, direction: str = "both"):
        return self._request("GET", "/v1/graph/path", params={"source_id": source_id, "target_id": target_id, "depth": depth, "direction": direction})

    def neighborhood(self, entity_id: str):
        return self._request("GET", f"/v1/graph/{entity_id}/neighborhood")

    def recommendations(self, entity_id: str, *, target_type: str | None = None, limit: int = 10):
        params: dict[str, Any] = {"limit": limit}
        if target_type: params["target_type"] = target_type
        return self._request("GET", f"/v1/graph/{entity_id}/recommendations", params=params)


    def create_claim(self, payload: dict[str, Any]):
        return self._request("POST", "/v1/claims", write=True, json=payload)

    def create_source_snapshot(self, payload: dict[str, Any]):
        return self._request("POST", "/v1/source-snapshots", write=True, json=payload)

    def create_provenance_activity(self, payload: dict[str, Any]):
        return self._request("POST", "/v1/provenance/activities", write=True, json=payload)

    def create_calculation_trace(self, payload: dict[str, Any]):
        return self._request("POST", "/v1/calculation-traces", write=True, json=payload)

    def create_evidence_record(self, payload: dict[str, Any]):
        return self._request("POST", "/v1/evidence-records", write=True, json=payload)

    def review_evidence(self, evidence_id: str, payload: dict[str, Any]):
        return self._request(
            "POST",
            f"/v1/evidence-records/{evidence_id}/reviews",
            write=True,
            json=payload,
        )

    def evidence_manifest(self, claim_id: str):
        return self._request("GET", f"/v1/evidence/manifests/{claim_id}")

    def verify_ledger(self):
        return self._request("GET", "/v1/ledger/verify")

    def evidence_stats(self):
        return self._request("GET", "/v1/evidence/stats")


    def api_plans(self):
        return self._request("GET", "/v1/developer/plans")

    def create_developer_application(self, payload: dict[str, Any]):
        return self._request(
            "POST",
            "/v1/developer/applications",
            write=True,
            json=payload,
        )

    def update_developer_application(
        self,
        application_id: str,
        payload: dict[str, Any],
    ):
        return self._request(
            "PATCH",
            f"/v1/developer/applications/{application_id}",
            write=True,
            json=payload,
        )

    def issue_public_api_key(
        self,
        application_id: str,
        payload: dict[str, Any],
    ):
        return self._request(
            "POST",
            f"/v1/developer/applications/{application_id}/credentials",
            write=True,
            json=payload,
        )

    def revoke_public_api_key(
        self,
        credential_id: str,
        *,
        revoked_by: str,
    ):
        return self._request(
            "POST",
            f"/v1/developer/credentials/{credential_id}/revoke",
            write=True,
            json={"revoked_by": revoked_by},
        )

    def developer_platform_stats(self):
        return self._request(
            "GET",
            "/v1/developer/stats",
            write=True,
        )

    def publish_webhook_event(self, payload: dict[str, Any]):
        return self._request(
            "POST",
            "/v1/developer/events",
            write=True,
            json=payload,
        )

    def dispatch_webhooks(self, limit: int = 100):
        return self._request(
            "POST",
            "/v1/developer/webhooks/dispatch",
            write=True,
            params={"limit": limit},
        )


    def trust_status(self):
        return self._request("GET", "/v1/trust/status")

    def evaluation_definitions(self, *, domain: str | None = None):
        params = {"domain": domain} if domain else None
        return self._request("GET", "/v1/trust/definitions", params=params)

    def run_evaluation(self, definition_id: str, payload: dict[str, Any]):
        return self._request(
            "POST",
            f"/v1/trust/definitions/{definition_id}/runs",
            write=True,
            json=payload,
        )

    def run_trust_suite(self, payload: dict[str, Any]):
        return self._request("POST", "/v1/trust/run-suite", write=True, json=payload)

    def create_trust_incident(self, payload: dict[str, Any]):
        return self._request("POST", "/v1/trust/incidents", write=True, json=payload)

    def create_known_limitation(self, payload: dict[str, Any]):
        return self._request("POST", "/v1/trust/limitations", write=True, json=payload)

    def create_trust_attestation(self, payload: dict[str, Any]):
        return self._request("POST", "/v1/trust/attestations", write=True, json=payload)


    def workflow_definitions(self):
        return self._request("GET", "/v1/workflow-definitions")

    def create_workflow_run(self, payload: dict[str, Any]):
        return self._request("POST", "/v1/workflow-runs", write=True, json=payload)

    def start_workflow_run(self, run_id: str, payload: dict[str, Any]):
        return self._request("POST", f"/v1/workflow-runs/{run_id}/start", write=True, json=payload)

    def transition_workflow_step(self, run_id: str, step_key: str, payload: dict[str, Any]):
        return self._request("POST", f"/v1/workflow-runs/{run_id}/steps/{step_key}/transition", write=True, json=payload)

    def create_dossier(self, payload: dict[str, Any]):
        return self._request("POST", "/v1/dossiers", write=True, json=payload)

    def add_dossier_record(self, dossier_id: str, payload: dict[str, Any]):
        return self._request("POST", f"/v1/dossiers/{dossier_id}/records", write=True, json=payload)

    def approve_dossier(self, dossier_id: str, payload: dict[str, Any]):
        return self._request("POST", f"/v1/dossiers/{dossier_id}/approvals", write=True, json=payload)

    def finalize_dossier(self, dossier_id: str, payload: dict[str, Any]):
        return self._request("POST", f"/v1/dossiers/{dossier_id}/finalize", write=True, json=payload)

    def verify_dossier(self, dossier_id: str):
        return self._request("GET", f"/v1/dossiers/{dossier_id}/verify")

    # Platform Core v2.7.0 free live-data gateway
    def live_data_sources(self, *, active: bool | None = True, review_status: str | None = None):
        params: dict[str, Any] = {}
        if active is not None: params["active"] = active
        if review_status: params["review_status"] = review_status
        return self._request("GET", "/v1/live/sources", params=params)

    def live_data_connectors(self, *, domain: str | None = None, source_id: str | None = None):
        params: dict[str, Any] = {}
        if domain: params["domain"] = domain
        if source_id: params["source_id"] = source_id
        return self._request("GET", "/v1/live/connectors", params=params)

    def live_data_health(self):
        return self._request("GET", "/v1/live/connectors/health")

    def ingest_live_data(self, connector_id: str, parameters: dict[str, Any], *, requested_by: str = "python-client", run_type: str = "manual"):
        return self._request(
            "POST",
            f"/v1/live/connectors/{connector_id}/ingest",
            write=True,
            json={"parameters": parameters, "requested_by": requested_by, "run_type": run_type},
        )

    def live_observations(self, **params):
        return self._request("GET", "/v1/live/observations/latest", params=params)

    def live_timeseries(self, metric: str, **params):
        return self._request("GET", "/v1/live/timeseries", params={"metric": metric, **params})

    def live_provenance(self, observation_id: str):
        return self._request("GET", f"/v1/live/provenance/{observation_id}")

