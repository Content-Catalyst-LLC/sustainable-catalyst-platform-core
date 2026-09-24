"""Platform Core adapter client for Catalyst Julia Runtime v0.3.0."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any
import json
import urllib.error
import urllib.parse
import urllib.request


@dataclass(frozen=True)
class JuliaRuntimeConfig:
    base_url: str = "http://127.0.0.1:18093"
    timeout_seconds: float = 10.0


class JuliaRuntimeError(RuntimeError):
    pass


class JuliaRuntimeClient:
    runtime_name = "julia"
    runtime_id = "catalyst-julia-runtime"
    service_version = "0.3.0"
    execution_contract_version = "sc.execution.v1"
    environment_schema_version = "sc.environment.v1"
    core_adapter_contract_version = "sc.core.runtime-adapter.v1"
    core_object_contract_version = "sc.core.computational-runtime-object.v1"

    def __init__(self, config: JuliaRuntimeConfig | None = None):
        self.config = config or JuliaRuntimeConfig()

    def _request(
        self,
        method: str,
        path: str,
        payload: dict[str, Any] | None = None,
        query: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        url = self.config.base_url.rstrip("/") + path
        if query:
            url += "?" + urllib.parse.urlencode(query)
        body = None if payload is None else json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=body,
            method=method,
            headers={"Content-Type": "application/json"},
        )
        try:
            with urllib.request.urlopen(req, timeout=self.config.timeout_seconds) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise JuliaRuntimeError(f"Julia runtime HTTP {exc.code}: {detail}") from exc
        except OSError as exc:
            raise JuliaRuntimeError(f"Julia runtime unavailable: {exc}") from exc

    def health(self) -> dict[str, Any]:
        return self._request("GET", "/health")

    def version(self) -> dict[str, Any]:
        return self._request("GET", "/version")

    def capabilities(self) -> dict[str, Any]:
        return self._request("GET", "/capabilities")

    def core_adapter(self) -> dict[str, Any]:
        return self._request("GET", "/v1/core-adapter")

    def environment(self) -> dict[str, Any]:
        return self._request("GET", "/v1/environment")

    def environment_fingerprint(self) -> str:
        data = self._request("GET", "/v1/environment/fingerprint")
        return str(data["environment_fingerprint_sha256"])

    def validate(self, job: dict[str, Any]) -> dict[str, Any]:
        return self._request("POST", "/v1/jobs/validate", job)

    def run(self, job: dict[str, Any], *, require_current_environment: bool = False) -> dict[str, Any]:
        payload = dict(job)
        if require_current_environment and not payload.get("expected_environment_fingerprint_sha256"):
            payload["expected_environment_fingerprint_sha256"] = self.environment_fingerprint()
        return self._request("POST", "/v1/jobs/run", payload)

    def prepare(self, execution_request: dict[str, Any]) -> dict[str, Any]:
        return self._request("POST", "/v1/core-adapter/prepare", execution_request)

    def execute(self, execution_request: dict[str, Any]) -> dict[str, Any]:
        return self._request("POST", "/v1/core-adapter/execute", execution_request)

    def cancel(self, run_id: str) -> dict[str, Any]:
        return self._request("POST", "/v1/core-adapter/cancel", {"run_id": run_id})

    def inspect(self, run_id: str) -> dict[str, Any]:
        return self._request("GET", "/v1/core-adapter/inspect", query={"run_id": run_id})

    def collect_results(self, run_id: str) -> dict[str, Any]:
        return self._request("GET", "/v1/core-adapter/results", query={"run_id": run_id})

    def collect_artifacts(self, run_id: str) -> dict[str, Any]:
        return self._request("GET", "/v1/core-adapter/artifacts", query={"run_id": run_id})

    def diagnose(self, run_id: str | None = None) -> dict[str, Any]:
        query = {} if run_id is None else {"run_id": run_id}
        return self._request("GET", "/v1/core-adapter/diagnose", query=query or None)
