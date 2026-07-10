from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse

router = APIRouter(tags=["Evidence Explorer"])


@router.get("/evidence-explorer", response_class=HTMLResponse)
def evidence_explorer(request: Request):
    if not request.app.state.settings.evidence_explorer_enabled:
        raise HTTPException(status_code=404, detail="Evidence Explorer is disabled.")

    return HTMLResponse(content=r'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Sustainable Catalyst Evidence Explorer</title>
<style>
:root{--red:#e60000;--ink:#111;--muted:#666;--cream:#f7f2e9;--line:#ded8cf;--green:#1f6f43}
*{box-sizing:border-box}
body{margin:0;font-family:system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;color:var(--ink);background:#fff}
header{padding:54px 24px;background:var(--cream);border-bottom:1px solid var(--line)}
main{max-width:1180px;margin:auto;padding:32px 24px 72px}
.eyebrow{color:var(--red);font-size:.78rem;font-weight:800;letter-spacing:.1em;text-transform:uppercase}
h1{margin:.25rem 0 .75rem;font-size:clamp(2.2rem,6vw,4.8rem);line-height:.95}
.lede{max-width:850px;font-size:1.08rem;line-height:1.7}
.toolbar{display:flex;gap:10px;flex-wrap:wrap;margin-bottom:24px}
button,.button{padding:12px 16px;border:1px solid var(--red);background:var(--red);color:#fff;font-weight:800;cursor:pointer;text-decoration:none}
.grid{display:grid;grid-template-columns:minmax(280px,.8fr) minmax(0,1.4fr);gap:22px}
.panel{border:1px solid var(--line);padding:22px;min-height:280px}
.card{display:block;width:100%;padding:14px 0;border:0;border-bottom:1px solid var(--line);background:transparent;color:inherit;text-align:left}
.card:hover{color:var(--red)}
.meta,.empty{color:var(--muted);font-size:.88rem}
.badge{display:inline-block;padding:4px 8px;margin:2px;background:var(--cream);border:1px solid var(--line);font-size:.78rem}
.valid{color:var(--green);font-weight:800}
.invalid{color:var(--red);font-weight:800}
pre{overflow:auto;padding:14px;background:#151515;color:#fff;font-size:.78rem}
@media(max-width:800px){.grid{grid-template-columns:1fr}}
</style>
</head>
<body>
<header><div style="max-width:1180px;margin:auto">
<p class="eyebrow">Sustainable Catalyst Platform Core</p>
<h1>Evidence Explorer</h1>
<p class="lede">Inspect claims, evidence records, immutable source snapshots, calculation traces, provenance activities, review history, evidence manifests, and the current integrity state of the ledger.</p>
</div></header>
<main>
<div class="toolbar">
<button id="refresh">Refresh claims</button>
<button id="verify">Verify ledger</button>
<a class="button" href="/docs">Open API documentation</a>
</div>
<div id="ledgerStatus" class="panel" style="min-height:auto;margin-bottom:22px">Ledger status has not been checked.</div>
<div class="grid">
<section class="panel">
<p class="eyebrow">Claims</p>
<div id="claims" class="empty">Loading claims...</div>
</section>
<section class="panel">
<p class="eyebrow">Evidence manifest</p>
<div id="manifest" class="empty">Select a claim to inspect its evidence package.</div>
</section>
</div>
</main>
<script>
const claims=document.getElementById("claims");
const manifest=document.getElementById("manifest");
const ledgerStatus=document.getElementById("ledgerStatus");
const esc=v=>String(v??"").replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#039;"}[c]));

async function loadClaims(){
  claims.innerHTML='<p class="empty">Loading claims...</p>';
  const response=await fetch('/v1/claims?visibility=public&limit=100');
  const data=await response.json();
  if(!data.items||!data.items.length){
    claims.innerHTML='<p class="empty">No public claims have been registered yet.</p>';
    return;
  }
  claims.innerHTML=data.items.map(item=>`<button class="card" data-claim="${esc(item.id)}"><strong>${esc(item.claim_text)}</strong><br><span class="meta">${esc(item.claim_type)} / ${esc(item.status)} / ${esc(item.id)}</span></button>`).join('');
  document.querySelectorAll('[data-claim]').forEach(button=>button.onclick=()=>loadManifest(button.dataset.claim));
}

async function loadManifest(claimId){
  manifest.innerHTML='<p class="empty">Building evidence manifest...</p>';
  const response=await fetch(`/v1/evidence/manifests/${encodeURIComponent(claimId)}`);
  const data=await response.json();
  if(!response.ok){
    manifest.innerHTML=`<p class="invalid">${esc(data.detail||'Manifest unavailable.')}</p>`;
    return;
  }
  manifest.innerHTML=`
    <h2>${esc(data.claim.claim_text)}</h2>
    <p><span class="badge">${data.evidence.length} evidence records</span>
    <span class="badge">${data.snapshots.length} snapshots</span>
    <span class="badge">${data.calculation_traces.length} calculation traces</span>
    <span class="badge">${data.reviews.length} reviews</span></p>
    <p class="meta">Manifest hash: ${esc(data.manifest_hash)}</p>
    <pre>${esc(JSON.stringify(data,null,2))}</pre>`;
}

async function verifyLedger(){
  ledgerStatus.innerHTML='Checking ledger integrity...';
  const response=await fetch('/v1/ledger/verify');
  const data=await response.json();
  ledgerStatus.innerHTML=data.valid
    ? `<span class="valid">Ledger verified</span><p>${data.entries_checked} entries checked. Head hash: ${esc(data.head_hash||'empty ledger')}</p>`
    : `<span class="invalid">Ledger integrity failure</span><p>${esc((data.errors||[]).join(' | '))}</p>`;
}

document.getElementById('refresh').onclick=loadClaims;
document.getElementById('verify').onclick=verifyLedger;
loadClaims();
verifyLedger();
</script>
</body>
</html>''')
