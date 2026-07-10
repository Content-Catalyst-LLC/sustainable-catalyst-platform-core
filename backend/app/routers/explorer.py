from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse

router = APIRouter(tags=["Knowledge Explorer"])

@router.get("/explorer", response_class=HTMLResponse)
def knowledge_explorer(request: Request):
    if not request.app.state.settings.explorer_enabled:
        raise HTTPException(status_code=404, detail="Knowledge Explorer is disabled.")
    return HTMLResponse(content=r'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Sustainable Catalyst Knowledge Explorer</title>
<style>
:root{--red:#e60000;--ink:#111;--muted:#666;--cream:#f7f2e9;--line:#ded8cf}*{box-sizing:border-box}
body{margin:0;font-family:system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;color:var(--ink)}
header{padding:56px 24px;background:var(--cream);border-bottom:1px solid var(--line)}
main{max-width:1180px;margin:auto;padding:32px 24px 72px}.eyebrow{color:var(--red);font-size:.78rem;font-weight:800;letter-spacing:.1em;text-transform:uppercase}
h1{margin:.25rem 0 .75rem;font-size:clamp(2.2rem,6vw,4.8rem);line-height:.95}.lede{max-width:820px;font-size:1.1rem;line-height:1.7}
.search{display:grid;grid-template-columns:1fr auto;gap:10px;margin-bottom:26px}input{padding:14px 16px;border:1px solid #aaa;font:inherit}
button,.button{padding:13px 18px;border:1px solid var(--red);background:var(--red);color:#fff;font-weight:800;cursor:pointer;text-decoration:none}
.grid{display:grid;grid-template-columns:1fr 1fr;gap:22px}.panel{border:1px solid var(--line);padding:22px;min-height:240px}
.card{display:block;width:100%;padding:14px 0;border:0;border-bottom:1px solid var(--line);background:transparent;color:inherit;text-align:left}
.card:hover{color:var(--red)}.type{color:var(--red);font-size:.72rem;font-weight:800;text-transform:uppercase;letter-spacing:.08em}
.meta,.empty{color:var(--muted);font-size:.88rem}.group{margin:18px 0}.pill{display:inline-block;margin:3px;padding:6px 9px;background:var(--cream);border:1px solid var(--line);font-size:.86rem;color:var(--ink)}
@media(max-width:760px){.grid,.search{grid-template-columns:1fr}}
</style></head>
<body><header><div style="max-width:1180px;margin:auto"><p class="eyebrow">Sustainable Catalyst Platform Core</p><h1>Knowledge Explorer</h1><p class="lede">Search registered entities, inspect reviewed relationships, follow concepts to tools and sources, and open machine-readable JSON-LD records.</p></div></header>
<main><form class="search" id="searchForm"><input id="query" type="search" placeholder="Search concepts, articles, tools, datasets, products, or sources"><button type="submit">Search</button></form>
<div class="grid"><section class="panel"><p class="eyebrow">Entities</p><div id="results" class="empty">Enter a term to search.</div></section><section class="panel"><p class="eyebrow">Selected record</p><div id="detail" class="empty">Select an entity to inspect its neighborhood.</div></section></div></main>
<script>
const results=document.getElementById("results"),detail=document.getElementById("detail"),query=document.getElementById("query");
const esc=v=>String(v??"").replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#039;"}[c]));
async function searchEntities(term){
  results.innerHTML='<p class="empty">Searching...</p>';
  const r=await fetch(`/v1/entities?q=${encodeURIComponent(term)}&visibility=public&limit=40`);
  const d=await r.json();
  if(!d.items||!d.items.length){results.innerHTML='<p class="empty">No matches.</p>';return}
  results.innerHTML=d.items.map(e=>`<button class="card" data-id="${esc(e.id)}"><span class="type">${esc(e.entity_type)}</span><br><strong>${esc(e.name)}</strong><br><span class="meta">${esc(e.id)}</span></button>`).join("");
  document.querySelectorAll("[data-id]").forEach(b=>b.onclick=()=>loadEntity(b.dataset.id));
}
async function loadEntity(id){
  detail.innerHTML='<p class="empty">Loading graph neighborhood...</p>';
  const [er,gr]=await Promise.all([fetch(`/v1/entities/${encodeURIComponent(id)}`),fetch(`/v1/graph/${encodeURIComponent(id)}/neighborhood`)]);
  const e=await er.json(),g=await gr.json();
  const groups=(g.groups||[]).map(x=>`<div class="group"><h3>${esc(x.direction)} / ${esc(x.predicate_label)} (${x.count})</h3>${(x.entities||[]).map(i=>`<button class="pill" data-related-id="${esc(i.id)}">${esc(i.name)}</button>`).join("")}</div>`).join("");
  detail.innerHTML=`<span class="type">${esc(e.entity_type)}</span><h2>${esc(e.name)}</h2><p>${esc(e.description||"No description registered.")}</p><p class="meta">${esc(e.id)} / ${esc(e.status)}</p><p>${e.canonical_url?`<a class="button" href="${esc(e.canonical_url)}">Open resource</a>`:""} <a class="button" href="/v1/entities/${encodeURIComponent(e.id)}/jsonld">JSON-LD</a></p><hr><h3>Relationship neighborhood</h3>${groups||'<p class="empty">No reviewed relationships yet.</p>'}`;
  document.querySelectorAll("[data-related-id]").forEach(b=>b.onclick=()=>loadEntity(b.dataset.relatedId));
}
document.getElementById("searchForm").onsubmit=e=>{e.preventDefault();const t=query.value.trim();if(t)searchEntities(t)};
searchEntities("Sustainable Catalyst");
</script></body></html>''')
