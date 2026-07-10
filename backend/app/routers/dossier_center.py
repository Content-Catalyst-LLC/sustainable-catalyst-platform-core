from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse

router = APIRouter(tags=["Dossier Center"])


@router.get("/dossier-center", response_class=HTMLResponse)
def dossier_center(request: Request):
    if not request.app.state.settings.dossier_center_enabled:
        raise HTTPException(status_code=404, detail="Dossier Center is disabled.")
    return HTMLResponse(content="""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Sustainable Catalyst Signature Dossiers</title>
<style>
:root{--r:#e60000;--i:#111;--m:#666;--c:#f7f2e9;--l:#ded8cf}*{box-sizing:border-box}body{margin:0;font-family:system-ui,sans-serif;color:var(--i)}header{padding:58px 24px;background:var(--c);border-bottom:1px solid var(--l)}main{max-width:1120px;margin:auto;padding:32px 24px 72px}.wrap{max-width:1120px;margin:auto}.eye{color:var(--r);font-size:.78rem;font-weight:800;letter-spacing:.1em;text-transform:uppercase}h1{font-size:clamp(2.4rem,7vw,5.2rem);line-height:.94;margin:.3rem 0}.lede{max-width:850px;font-size:1.1rem;line-height:1.7}.grid{display:grid;grid-template-columns:.8fr 1.3fr;gap:20px}.panel{border:1px solid var(--l);padding:21px}.card{display:block;width:100%;text-align:left;background:#fff;border:0;border-bottom:1px solid var(--l);padding:14px 0;cursor:pointer}.card:hover{color:var(--r)}.meta{color:var(--m);font-size:.85rem}.valid{color:#176b3a;font-weight:800}.invalid{color:var(--r);font-weight:800}pre{overflow:auto;background:#151515;color:#fff;padding:15px;font-size:.78rem}@media(max-width:760px){.grid{grid-template-columns:1fr}}
</style></head><body>
<header><div class="wrap"><p class="eye">Sustainable Catalyst Platform</p><h1>Signature Dossiers</h1><p class="lede">Verifiable decision and assurance packages that freeze evidence, graph context, calculations, evaluations, disclosures, approvals, and workflow history into a signed canonical record.</p></div></header>
<main><div class="grid"><section class="panel"><p class="eye">Public dossiers</p><div id="list">Loading...</div></section><section class="panel"><p class="eye">Dossier record</p><div id="detail" class="meta">Select a dossier.</div></section></div></main>
<script>
const esc=v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#039;'}[c]));
async function load(){const r=await fetch('/public/dossiers');const d=await r.json();const x=document.getElementById('list');x.innerHTML=d.items?.length?d.items.map(i=>`<button class="card" data-id="${esc(i.id)}"><strong>${esc(i.title)}</strong><br><span class="meta">${esc(i.version)} · ${esc(i.signed_at)}<br>${esc(i.dossier_hash)}</span></button>`).join(''):'<p class="meta">No public finalized dossiers yet.</p>';document.querySelectorAll('[data-id]').forEach(b=>b.onclick=()=>show(b.dataset.id));}
async function show(id){const [a,b]=await Promise.all([fetch('/public/dossiers/'+encodeURIComponent(id)),fetch('/public/dossiers/'+encodeURIComponent(id)+'/verify')]);const d=await a.json(),v=await b.json();document.getElementById('detail').innerHTML=`<h2>${esc(d.title)}</h2><p>${esc(d.purpose)}</p><p class="${v.valid?'valid':'invalid'}">${v.valid?'Signature verified':'Verification failed'}</p><p class="meta">Hash: ${esc(d.dossier_hash)}<br>Key: ${esc(d.signing_key_id)}<br>Signed by: ${esc(d.signed_by)}</p><p><strong>${d.records.length}</strong> public records · <strong>${d.approvals.length}</strong> approvals</p><pre>${esc(JSON.stringify(d,null,2))}</pre>`;}
load();
</script></body></html>""")
