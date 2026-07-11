from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse, Response

from ..dependencies import require_write
from ..public_api_auth import PublicApiContext, require_public_scope
from ..services.gateway import GatewayError, GatewayResult

router = APIRouter(tags=["Unified Service Gateway"])


def _request_id(request: Request) -> str:
    return getattr(request.state, "request_id", "")




async def _bounded_request_body(request: Request) -> bytes:
    maximum = request.app.state.gateway_settings.max_request_bytes
    declared = request.headers.get("content-length", "")
    if declared.isdigit() and int(declared) > maximum:
        raise GatewayError("Gateway request body is too large.", status_code=413)
    chunks: list[bytes] = []
    total = 0
    async for chunk in request.stream():
        total += len(chunk)
        if total > maximum:
            raise GatewayError("Gateway request body is too large.", status_code=413)
        chunks.append(chunk)
    return b"".join(chunks)


def _error_response(request: Request, exc: GatewayError) -> JSONResponse:
    detail = str(exc)
    if (
        exc.status_code >= 500
        and not request.app.state.gateway_settings.expose_upstream_errors
    ):
        detail = "The requested gateway service is temporarily unavailable."
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "data": None,
            "meta": {
                "api_version": "v1",
                "request_id": _request_id(request),
                "gateway": True,
            },
            "warnings": [detail],
        },
        headers={"X-Request-ID": _request_id(request)},
    )


def _transparent_response(result: GatewayResult) -> Response:
    return Response(
        content=result.content,
        status_code=result.status_code,
        media_type=result.content_type.split(";", 1)[0],
        headers=result.headers,
    )


def _public_response(request: Request, result: GatewayResult) -> Response:
    if result.json_data is None:
        return _transparent_response(result)
    warnings: list[str] = []
    if result.status_code >= 400:
        warnings.append("The upstream service returned a non-success status.")
    wrapper_headers = {
        key: value
        for key, value in result.headers.items()
        if key.lower() not in {"content-length", "content-type"}
    }
    return JSONResponse(
        status_code=result.status_code,
        content={
            "data": result.json_data,
            "meta": {
                "api_version": "v1",
                "request_id": _request_id(request),
                "service": result.service_id,
                "upstream_status": result.status_code,
                "upstream_latency_ms": result.latency_ms,
                "gateway": True,
            },
            "warnings": warnings,
        },
        headers=wrapper_headers,
    )


@router.get("/v1/gateway/services", dependencies=[Depends(require_write)])
async def internal_service_catalog(request: Request):
    return {
        "ok": True,
        "services": request.app.state.service_registry.public_catalog(),
        "request_id": _request_id(request),
    }


@router.get("/v1/gateway/health", dependencies=[Depends(require_write)])
async def internal_gateway_health(request: Request):
    snapshot = await request.app.state.gateway_runtime.health_snapshot()
    return {"ok": True, **snapshot, "request_id": _request_id(request)}


async def internal_gateway_proxy(
    request: Request,
    service_id: str,
    path: str,
):
    try:
        result = await request.app.state.gateway_runtime.proxy(
            service_id,
            method=request.method,
            path=path,
            query=list(request.query_params.multi_items()),
            incoming_headers=dict(request.headers),
            body=await _bounded_request_body(request),
            request_id=_request_id(request),
        )
        return _transparent_response(result)
    except GatewayError as exc:
        return _error_response(request, exc)


router.add_api_route(
    "/v1/gateway/{service_id}/{path:path}",
    internal_gateway_proxy,
    methods=["GET"],
    dependencies=[Depends(require_write)],
    name="internal_gateway_proxy_get",
)
router.add_api_route(
    "/v1/gateway/{service_id}/{path:path}",
    internal_gateway_proxy,
    methods=["HEAD", "OPTIONS", "POST", "PUT", "PATCH", "DELETE"],
    dependencies=[Depends(require_write)],
    include_in_schema=False,
    name="internal_gateway_proxy_non_get",
)


@router.get("/api/v1/gateway/services")
async def public_service_catalog(
    request: Request,
    _context: PublicApiContext = Depends(require_public_scope("gateway:read")),
):
    return {
        "data": request.app.state.service_registry.public_catalog(),
        "meta": {
            "api_version": "v1",
            "request_id": _request_id(request),
            "gateway": True,
        },
    }


@router.get("/api/v1/gateway/health")
async def public_gateway_health(
    request: Request,
    _context: PublicApiContext = Depends(require_public_scope("gateway:read")),
):
    snapshot = await request.app.state.gateway_runtime.health_snapshot()
    return {
        "data": snapshot,
        "meta": {
            "api_version": "v1",
            "request_id": _request_id(request),
            "gateway": True,
        },
    }


async def _public_proxy(
    request: Request,
    route_prefix: str,
    path: str,
    _context: PublicApiContext,
):
    service = request.app.state.service_registry.resolve_prefix(route_prefix)
    if service is None or not service.public_reads:
        return _error_response(
            request,
            GatewayError("Public gateway route not found.", status_code=404),
        )
    try:
        result = await request.app.state.gateway_runtime.proxy(
            service.service_id,
            method=request.method,
            path=path,
            query=list(request.query_params.multi_items()),
            incoming_headers=dict(request.headers),
            body=b"",
            request_id=_request_id(request),
        )
        return _public_response(request, result)
    except GatewayError as exc:
        return _error_response(request, exc)


def _public_proxy_endpoint(route_prefix: str):
    async def endpoint(
        request: Request,
        path: str,
        _context: PublicApiContext = Depends(require_public_scope("gateway:read")),
    ):
        return await _public_proxy(request, route_prefix, path, _context)

    return endpoint


for _prefix in (
    "site-intelligence",
    "workbench",
    "decision-studio",
    "research-librarian",
    "finance",
    "narrative-risk",
):
    _endpoint = _public_proxy_endpoint(_prefix)
    router.add_api_route(
        f"/api/v1/{_prefix}/{{path:path}}",
        _endpoint,
        methods=["GET"],
        name=f"gateway_{_prefix.replace('-', '_')}_get",
    )
    router.add_api_route(
        f"/api/v1/{_prefix}/{{path:path}}",
        _endpoint,
        methods=["HEAD", "OPTIONS"],
        include_in_schema=False,
        name=f"gateway_{_prefix.replace('-', '_')}_non_get",
    )
