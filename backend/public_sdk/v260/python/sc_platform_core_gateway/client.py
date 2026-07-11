from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import httpx


class GatewayClientError(RuntimeError):
    pass


@dataclass
class GatewayClient:
    base_url: str
    public_api_key: str
    timeout_seconds: float = 30.0

    def __post_init__(self) -> None:
        self.base_url = self.base_url.rstrip("/")
        if not self.base_url.startswith(("https://", "http://")):
            raise ValueError("base_url must be an HTTP or HTTPS URL")
        if not self.public_api_key.strip():
            raise ValueError("public_api_key is required")

    def _get(self, path: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        headers = {
            "Authorization": f"Bearer {self.public_api_key}",
            "Accept": "application/json",
        }
        with httpx.Client(timeout=self.timeout_seconds, follow_redirects=False) as client:
            response = client.get(f"{self.base_url}{path}", params=params, headers=headers)
        try:
            payload = response.json()
        except ValueError as exc:
            raise GatewayClientError(
                f"Gateway returned non-JSON content with status {response.status_code}."
            ) from exc
        if response.status_code >= 400:
            detail = payload.get("detail") or payload.get("warnings") or payload
            raise GatewayClientError(f"Gateway request failed: {detail}")
        return payload

    def services(self) -> dict[str, Any]:
        return self._get("/api/v1/gateway/services")

    def health(self) -> dict[str, Any]:
        return self._get("/api/v1/gateway/health")

    def read(
        self,
        service: str,
        path: str = "",
        *,
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        allowed = {
            "site-intelligence",
            "workbench",
            "decision-studio",
            "research-librarian",
            "finance",
            "narrative-risk",
        }
        if service not in allowed:
            raise ValueError(f"Unknown gateway service: {service}")
        clean_path = path.strip().lstrip("/")
        suffix = f"/{clean_path}" if clean_path else "/"
        return self._get(f"/api/v1/{service}{suffix}", params=params)
