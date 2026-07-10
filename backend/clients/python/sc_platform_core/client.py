from __future__ import annotations

from typing import Any

import httpx


class PlatformCoreError(RuntimeError):
    pass


class PlatformCoreClient:
    def __init__(
        self,
        base_url: str,
        *,
        api_key: str | None = None,
        timeout: float = 15.0,
    ):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.timeout = timeout

    def _headers(self, write: bool = False) -> dict[str, str]:
        headers = {"Accept": "application/json"}
        if write and self.api_key:
            headers["X-SC-API-Key"] = self.api_key
        return headers

    def _request(
        self,
        method: str,
        path: str,
        *,
        write: bool = False,
        **kwargs: Any,
    ) -> Any:
        response = httpx.request(
            method,
            f"{self.base_url}{path}",
            headers=self._headers(write=write),
            timeout=self.timeout,
            **kwargs,
        )
        if response.is_error:
            raise PlatformCoreError(
                f"{response.status_code}: {response.text}"
            )
        return response.json()

    def health(self) -> dict[str, Any]:
        return self._request("GET", "/health")

    def stats(self) -> dict[str, Any]:
        return self._request("GET", "/v1/stats")

    def get_entity(self, entity_id: str) -> dict[str, Any]:
        return self._request("GET", f"/v1/entities/{entity_id}")

    def list_entities(
        self,
        *,
        entity_type: str | None = None,
        query: str | None = None,
        limit: int = 50,
    ) -> dict[str, Any]:
        params = {"limit": limit}
        if entity_type:
            params["entity_type"] = entity_type
        if query:
            params["q"] = query
        return self._request("GET", "/v1/entities", params=params)

    def create_entity(self, payload: dict[str, Any]) -> dict[str, Any]:
        return self._request(
            "POST",
            "/v1/entities",
            write=True,
            json=payload,
        )

    def create_relationship(
        self,
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        return self._request(
            "POST",
            "/v1/relationships",
            write=True,
            json=payload,
        )

    def graph(
        self,
        entity_id: str,
        *,
        direction: str = "both",
        depth: int = 1,
        predicates: list[str] | None = None,
    ) -> dict[str, Any]:
        params: list[tuple[str, str | int]] = [
            ("direction", direction),
            ("depth", depth),
        ]
        for predicate in predicates or []:
            params.append(("predicates", predicate))
        return self._request(
            "GET",
            f"/v1/graph/{entity_id}",
            params=params,
        )
