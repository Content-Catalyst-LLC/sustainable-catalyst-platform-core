from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from sqlalchemy import select

from ..models import ApiPlan

router = APIRouter(tags=["Developer Portal"])

BACKEND_ROOT = Path(__file__).resolve().parents[2]
SDK_ROOT = BACKEND_ROOT / "public_sdk"


def _require_portal(request: Request) -> None:
    if not request.app.state.settings.developer_portal_enabled:
        raise HTTPException(status_code=404, detail="Developer Portal is disabled.")


@router.get("/developers", response_class=HTMLResponse)
def developer_portal(request: Request):
    _require_portal(request)
    return HTMLResponse(content=r'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Sustainable Catalyst Developer Portal</title>
<style>
:root{--red:#e60000;--ink:#111;--muted:#666;--cream:#f7f2e9;--line:#ded8cf;--panel:#fff}
*{box-sizing:border-box}
body{margin:0;font-family:system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;color:var(--ink);background:#fff}
a{color:var(--red)}
header{padding:62px 24px;background:var(--cream);border-bottom:1px solid var(--line)}
.wrap{max-width:1180px;margin:auto}
.eyebrow{color:var(--red);font-size:.78rem;font-weight:850;letter-spacing:.1em;text-transform:uppercase}
h1{margin:.25rem 0 .9rem;font-size:clamp(2.4rem,7vw,5.6rem);line-height:.92}
.lede{max-width:900px;font-size:1.13rem;line-height:1.75}
.actions{display:flex;gap:10px;flex-wrap:wrap;margin-top:24px}
.button{display:inline-block;padding:13px 17px;border:1px solid var(--red);background:var(--red);color:#fff;text-decoration:none;font-weight:800}
.button.secondary{background:#fff;color:var(--red)}
main{max-width:1180px;margin:auto;padding:34px 24px 80px}
.grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:18px}
.card{border:1px solid var(--line);padding:22px;background:var(--panel)}
.card h3{margin:.2rem 0 .6rem}
.section{margin:46px 0}
.section h2{font-size:clamp(1.7rem,3vw,2.6rem);margin:0 0 12px}
table{width:100%;border-collapse:collapse}
th,td{text-align:left;vertical-align:top;padding:12px;border-bottom:1px solid var(--line)}
code{font-family:ui-monospace,SFMono-Regular,Menlo,monospace;font-size:.9em}
pre{overflow:auto;background:#151515;color:#fff;padding:18px;line-height:1.55}
.scope{display:inline-block;margin:4px 3px;padding:6px 9px;border:1px solid var(--line);background:var(--cream);font-family:ui-monospace,SFMono-Regular,Menlo,monospace;font-size:.78rem}
.note{padding:16px;border-left:4px solid var(--red);background:var(--cream)}
footer{padding:28px 24px;border-top:1px solid var(--line);color:var(--muted)}
@media(max-width:850px){.grid{grid-template-columns:1fr}}
</style>
</head>
<body>
<header>
<div class="wrap">
<p class="eyebrow">Sustainable Catalyst Platform Core</p>
<h1>Developer Portal</h1>
<p class="lede">Build public-interest research, sustainability, evidence, knowledge-graph, and decision-support integrations on one versioned API. The unified public surface exposes reviewed registry, graph, evidence, and ledger records without exposing Platform Core administrative controls.</p>
<div class="actions">
<a class="button" href="/developers/console">Open API Console</a>
<a class="button secondary" href="/developers/openapi.json">Public OpenAPI</a>
<a class="button secondary" href="/developers/postman.json">Postman Collection</a>
<a class="button secondary" href="/trust">Trust Center</a>
</div>
</div>
</header>
<main>
<section class="grid">
<article class="card"><p class="eyebrow">One surface</p><h3><code>/api/v1</code></h3><p>Stable external routes for entities, graph paths, claims, evidence manifests, ledger verification, usage, and webhooks.</p></article>
<article class="card"><p class="eyebrow">Scoped access</p><h3>Hashed API keys</h3><p>Keys are shown once, stored only as SHA-256 hashes, assigned explicit scopes, and governed by approved applications and plans.</p></article>
<article class="card"><p class="eyebrow">Observable use</p><h3>Quotas and request IDs</h3><p>Every response returns request and rate-limit headers. Usage records retain hashed client identifiers rather than raw addresses.</p></article>
</section>

<section class="section">
<p class="eyebrow">Quick start</p>
<h2>Make your first request</h2>
<pre><code>curl "https://YOUR-PLATFORM-CORE.onrender.com/api/v1/status" \
  -H "Authorization: Bearer scpk_your_api_key"</code></pre>
<p>Every public response uses a consistent envelope:</p>
<pre><code>{
  "data": { "status": "operational" },
  "meta": {
    "api_version": "v1",
    "request_id": "...",
    "documentation": "/developers"
  }
}</code></pre>
</section>

<section class="section">
<p class="eyebrow">API domains</p>
<h2>Unified public routes</h2>
<table>
<thead><tr><th>Domain</th><th>Representative routes</th><th>Scope</th></tr></thead>
<tbody>
<tr><td>Service</td><td><code>GET /api/v1/status</code></td><td><code>public:status</code></td></tr>
<tr><td>Registry</td><td><code>GET /api/v1/entities</code><br><code>GET /api/v1/predicates</code></td><td><code>registry:read</code></td></tr>
<tr><td>Knowledge graph</td><td><code>GET /api/v1/graph/{entity_id}</code><br><code>GET /api/v1/graph/path</code></td><td><code>graph:read</code></td></tr>
<tr><td>Evidence</td><td><code>GET /api/v1/claims</code><br><code>GET /api/v1/evidence-records</code><br><code>GET /api/v1/evidence/manifests/{claim_id}</code></td><td><code>evidence:read</code></td></tr>
<tr><td>Ledger</td><td><code>GET /api/v1/ledger/verify</code><br><code>GET /api/v1/ledger/entries</code></td><td><code>ledger:read</code></td></tr>
<tr><td>Trust Center</td><td><code>GET /api/v1/trust/status</code><br><code>GET /api/v1/trust/evaluations</code><br><code>GET /api/v1/trust/incidents</code></td><td><code>trust:read</code></td></tr>
<tr><td>Developer account</td><td><code>GET /api/v1/developer/me</code><br><code>GET /api/v1/developer/usage</code></td><td><code>developer:read</code></td></tr>
<tr><td>Webhooks</td><td><code>GET/POST /api/v1/developer/webhooks</code></td><td><code>webhooks:manage</code></td></tr>
</tbody>
</table>
</section>

<section class="section">
<p class="eyebrow">Scopes</p>
<h2>Least-privilege credentials</h2>
<p>
<span class="scope">public:status</span>
<span class="scope">registry:read</span>
<span class="scope">graph:read</span>
<span class="scope">evidence:read</span>
<span class="scope">ledger:read</span>
<span class="scope">trust:read</span>
<span class="scope">developer:read</span>
<span class="scope">webhooks:manage</span>
</p>
<p class="note">The unified public API is read-only for registry, graph, evidence, and ledger data. Administrative key issuance, application approval, event publication, and webhook dispatch remain behind the internal Platform Core write key.</p>
</section>

<section class="section">
<p class="eyebrow">Rate limits</p>
<h2>Plan-aware quotas</h2>
<div id="plans" class="grid"><article class="card">Loading API plans...</article></div>
<p>Responses include <code>X-RateLimit-Limit-Minute</code>, <code>X-RateLimit-Remaining-Minute</code>, <code>X-RateLimit-Limit-Day</code>, <code>X-RateLimit-Remaining-Day</code>, <code>X-Request-ID</code>, and <code>X-SC-API-Version</code>.</p>
</section>

<section class="section">
<p class="eyebrow">Webhooks</p>
<h2>Signed event delivery</h2>
<p>Subscriptions can listen to exact event types, <code>*</code>, or prefixes such as <code>evidence.*</code>. Deliveries include:</p>
<pre><code>X-SC-Webhook-ID: sc:webhook-event:...
X-SC-Webhook-Timestamp: 1783650000
X-SC-Webhook-Signature: v1=&lt;hex-hmac&gt;</code></pre>
<p>Verify the HMAC-SHA256 signature over:</p>
<pre><code>{timestamp}.{raw_request_body}</code></pre>
<p>Production callback URLs must use HTTPS and cannot target localhost or private network addresses.</p>
</section>

<section class="section">
<p class="eyebrow">Downloads</p>
<h2>SDKs and machine-readable assets</h2>
<div class="actions">
<a class="button" href="/developers/sdk/python.zip">Python SDK</a>
<a class="button" href="/developers/sdk/javascript.zip">JavaScript SDK</a>
<a class="button secondary" href="/developers/openapi.json">OpenAPI JSON</a>
<a class="button secondary" href="/developers/postman.json">Postman Collection</a>
<a class="button secondary" href="/trust">Trust Center</a>
</div>
</section>

<section class="section">
<p class="eyebrow">Access</p>
<h2>Request a developer key</h2>
<p>Developer applications are reviewed before keys are issued. The Platform Core administrator creates or approves an application, assigns a plan, and generates a scoped key. Plaintext keys are returned once and cannot be recovered later.</p>
<p><a class="button" href="https://sustainablecatalyst.com/contact/">Contact Sustainable Catalyst</a></p>
</section>
</main>
<footer><div class="wrap">Sustainable Catalyst · An open knowledge lab where ideas become public infrastructure.</div></footer>
<script>
async function loadPlans(){
  const target=document.getElementById("plans");
  try{
    const response=await fetch("/developers/plans.json");
    const plans=await response.json();
    target.innerHTML=plans.map(plan=>`
      <article class="card">
        <p class="eyebrow">${plan.id}</p>
        <h3>${plan.name}</h3>
        <p>${plan.description||""}</p>
        <p><strong>${plan.requests_per_minute}</strong> requests/minute<br>
        <strong>${plan.requests_per_day}</strong> requests/day<br>
        Maximum page size: <strong>${plan.max_page_size}</strong></p>
      </article>`).join("");
  }catch(error){
    target.innerHTML='<article class="card">API plans are temporarily unavailable.</article>';
  }
}
loadPlans();
</script>
</body>
</html>''')


@router.get("/developers/console", response_class=HTMLResponse)
def developer_console(request: Request):
    _require_portal(request)
    return HTMLResponse(content=r'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Sustainable Catalyst API Console</title>
<style>
:root{--red:#e60000;--ink:#111;--cream:#f7f2e9;--line:#ded8cf}
*{box-sizing:border-box}body{margin:0;font-family:system-ui,sans-serif;color:var(--ink)}
header{padding:40px 24px;background:var(--cream);border-bottom:1px solid var(--line)}
main{max-width:1000px;margin:auto;padding:30px 24px 70px}
label{display:block;font-weight:800;margin:14px 0 6px}
input,select,textarea{width:100%;padding:12px;border:1px solid #aaa;font:inherit}
button{margin-top:16px;padding:13px 18px;border:1px solid var(--red);background:var(--red);color:#fff;font-weight:800;cursor:pointer}
pre{min-height:260px;overflow:auto;background:#151515;color:#fff;padding:18px;line-height:1.5}
.note{padding:14px;background:var(--cream);border-left:4px solid var(--red)}
</style></head>
<body>
<header><div style="max-width:1000px;margin:auto"><p><a href="/developers">← Developer Portal</a></p><h1>API Console</h1><p>Test public endpoints without storing your key in the page or browser storage.</p></div></header>
<main>
<p class="note">Your API key remains only in this page's memory and is sent directly to the selected Platform Core endpoint.</p>
<label for="key">Public API key</label>
<input id="key" type="password" autocomplete="off" placeholder="scpk_...">
<label for="endpoint">Endpoint</label>
<select id="endpoint">
<option value="/api/v1/status">Service status</option>
<option value="/api/v1/entities?entity_type=product">Product entities</option>
<option value="/api/v1/graph/sc:product:research-librarian?depth=2">Research Librarian graph</option>
<option value="/api/v1/claims">Public claims</option>
<option value="/api/v1/evidence-records">Verified evidence</option>
<option value="/api/v1/ledger/verify">Ledger verification</option>
<option value="/api/v1/trust/status">Trust status</option>
<option value="/api/v1/trust/evaluations">Trust evaluations</option>
<option value="/api/v1/developer/me">Developer identity</option>
<option value="/api/v1/developer/usage?days=30">Credential usage</option>
</select>
<label for="custom">Or enter a custom <code>/api/v1</code> GET path</label>
<input id="custom" placeholder="/api/v1/entities?q=climate">
<button id="send">Send request</button>
<h2>Response</h2>
<pre id="output">No request sent.</pre>
<script>
document.getElementById("send").onclick=async()=>{
  const key=document.getElementById("key").value.trim();
  const custom=document.getElementById("custom").value.trim();
  const endpoint=custom||document.getElementById("endpoint").value;
  const output=document.getElementById("output");
  if(!key){output.textContent="Enter a public API key.";return}
  if(!endpoint.startsWith("/api/v1")){output.textContent="Only /api/v1 paths are allowed.";return}
  output.textContent="Loading...";
  try{
    const response=await fetch(endpoint,{headers:{Authorization:`Bearer ${key}`,Accept:"application/json"}});
    const text=await response.text();
    let body=text;
    try{body=JSON.stringify(JSON.parse(text),null,2)}catch(error){}
    const headers=[
      `HTTP ${response.status}`,
      `X-Request-ID: ${response.headers.get("X-Request-ID")||""}`,
      `X-RateLimit-Remaining-Minute: ${response.headers.get("X-RateLimit-Remaining-Minute")||""}`,
      `X-RateLimit-Remaining-Day: ${response.headers.get("X-RateLimit-Remaining-Day")||""}`,
    ].join("\n");
    output.textContent=`${headers}\n\n${body}`;
  }catch(error){output.textContent=String(error)}
};
</script>
</main></body></html>''')


@router.get("/developers/plans.json")
def developer_plans(request: Request):
    _require_portal(request)
    with request.app.state.database.session_factory() as db:
        plans = list(
            db.scalars(
                select(ApiPlan)
                .where(ApiPlan.public.is_(True), ApiPlan.active.is_(True))
                .order_by(ApiPlan.sort_order, ApiPlan.name)
            ).all()
        )
    return [
        {
            "id": plan.id,
            "name": plan.name,
            "description": plan.description,
            "requests_per_minute": plan.requests_per_minute,
            "requests_per_day": plan.requests_per_day,
            "max_page_size": plan.max_page_size,
            "allowed_scopes": plan.allowed_scopes,
        }
        for plan in plans
    ]


@router.get("/developers/openapi.json")
def public_openapi(request: Request):
    _require_portal(request)
    schema = request.app.openapi()
    public_paths = {
        path: value
        for path, value in schema.get("paths", {}).items()
        if path.startswith("/api/v1")
    }
    components = dict(schema.get("components", {}))
    security_schemes = dict(components.get("securitySchemes", {}))
    security_schemes.update(
        {
            "SCPublicKey": {
                "type": "apiKey",
                "in": "header",
                "name": "X-SC-Public-Key",
                "description": "Sustainable Catalyst public API key.",
            },
            "BearerAuth": {
                "type": "http",
                "scheme": "bearer",
                "bearerFormat": "scpk_...",
            },
        }
    )
    components["securitySchemes"] = security_schemes
    for path_item in public_paths.values():
        for operation_name, operation in path_item.items():
            if operation_name.lower() in {
                "get", "post", "put", "patch", "delete", "options", "head"
            }:
                operation["security"] = [
                    {"SCPublicKey": []},
                    {"BearerAuth": []},
                ]

    filtered = {
        "openapi": schema.get("openapi"),
        "info": {
            **schema.get("info", {}),
            "title": "Sustainable Catalyst Unified Public API",
            "version": "1.0",
            "description": (
                "Versioned public registry, knowledge graph, evidence, "
                "ledger, usage, and webhook API."
            ),
        },
        "servers": [{"url": str(request.base_url).rstrip("/")}],
        "paths": public_paths,
        "components": components,
    }
    return JSONResponse(filtered)


@router.get("/developers/postman.json")
def postman_collection(request: Request):
    _require_portal(request)
    path = (
        SDK_ROOT
        / "postman"
        / "Sustainable_Catalyst_Public_API_v1.postman_collection.json"
    )
    if not path.exists():
        raise HTTPException(status_code=404, detail="Postman collection is unavailable.")
    return FileResponse(
        path,
        media_type="application/json",
        filename="Sustainable_Catalyst_Public_API_v1.postman_collection.json",
    )


@router.get("/developers/sdk/python.zip")
def python_sdk(request: Request):
    _require_portal(request)
    path = SDK_ROOT / "downloads" / "sc-platform-core-public-python-v2.4.0.zip"
    if not path.exists():
        raise HTTPException(status_code=404, detail="Python SDK is unavailable.")
    return FileResponse(
        path,
        media_type="application/zip",
        filename=path.name,
    )


@router.get("/developers/sdk/javascript.zip")
def javascript_sdk(request: Request):
    _require_portal(request)
    path = (
        SDK_ROOT
        / "downloads"
        / "sc-platform-core-public-javascript-v2.4.0.zip"
    )
    if not path.exists():
        raise HTTPException(status_code=404, detail="JavaScript SDK is unavailable.")
    return FileResponse(
        path,
        media_type="application/zip",
        filename=path.name,
    )
