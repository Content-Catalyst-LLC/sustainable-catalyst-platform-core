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

    def identity(self):
        return self.request("GET", "/developer/me")

    def usage(self, days: int = 30):
        return self.request("GET", "/developer/usage", params={"days": days})
