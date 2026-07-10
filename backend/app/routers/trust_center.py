from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request
from fastapi.encoders import jsonable_encoder
from fastapi.responses import HTMLResponse, JSONResponse
from sqlalchemy import select

from ..models import EvaluationDefinition, EvaluationRun, KnownLimitation, TrustAttestation, TrustIncident
from ..services.trust import build_trust_status, evaluation_run_read

router = APIRouter(tags=["Public Trust Center"])


def _require_center(request: Request) -> None:
    if not request.app.state.settings.trust_center_enabled:
        raise HTTPException(status_code=404, detail="Trust Center is disabled.")


@router.get("/trust/status.json")
def trust_status_json(request: Request):
    _require_center(request)
    if not request.app.state.settings.trust_public_status_enabled:
        raise HTTPException(status_code=404, detail="Public trust status is disabled.")
    with request.app.state.database.session_factory() as db:
        status = build_trust_status(db, request.app.state.settings, public_only=True)
    return JSONResponse(jsonable_encoder(status))


@router.get("/trust/evaluations.json")
def trust_evaluations_json(request: Request):
    _require_center(request)
    with request.app.state.database.session_factory() as db:
        definitions = list(db.scalars(select(EvaluationDefinition).where(EvaluationDefinition.public.is_(True), EvaluationDefinition.active.is_(True)).order_by(EvaluationDefinition.sort_order)).all())
        output = []
        for definition in definitions:
            run = db.scalar(select(EvaluationRun).where(EvaluationRun.definition_id == definition.id, EvaluationRun.public.is_(True)).order_by(EvaluationRun.completed_at.desc()).limit(1))
            output.append({"definition": definition, "latest_run": evaluation_run_read(db, run) if run else None})
    return JSONResponse(jsonable_encoder(output))


@router.get("/trust", response_class=HTMLResponse)
def trust_center(request: Request):
    _require_center(request)
    return HTMLResponse(content=r'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Sustainable Catalyst Trust Center</title>
<style>
:root{--red:#e60000;--ink:#111;--muted:#666;--cream:#f7f2e9;--line:#ded8cf;--green:#19663b;--amber:#8b5a00}
*{box-sizing:border-box}body{margin:0;font-family:system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;color:var(--ink);background:#fff}a{color:var(--red)}
header{padding:60px 24px;background:var(--cream);border-bottom:1px solid var(--line)}.wrap{max-width:1180px;margin:auto}.eyebrow{color:var(--red);font-size:.78rem;font-weight:850;letter-spacing:.1em;text-transform:uppercase}
h1{margin:.25rem 0 .9rem;font-size:clamp(2.4rem,7vw,5.5rem);line-height:.93}.lede{max-width:900px;font-size:1.12rem;line-height:1.75}.actions{display:flex;gap:10px;flex-wrap:wrap;margin-top:24px}.button{display:inline-block;padding:13px 17px;border:1px solid var(--red);background:var(--red);color:#fff;text-decoration:none;font-weight:800}.button.secondary{background:#fff;color:var(--red)}
main{max-width:1180px;margin:auto;padding:34px 24px 80px}.summary{display:grid;grid-template-columns:1.1fr repeat(3,.7fr);gap:16px;margin-bottom:28px}.card{border:1px solid var(--line);padding:22px;background:#fff}.metric{font-size:2rem;font-weight:850}.status{display:inline-block;padding:6px 10px;border:1px solid var(--line);font-weight:850;text-transform:uppercase;font-size:.76rem}.operational{color:var(--green)}.attention{color:var(--amber)}.degraded,.critical{color:var(--red)}.unknown{color:var(--muted)}
.section{margin:45px 0}.section h2{font-size:clamp(1.7rem,3vw,2.6rem);margin:0 0 14px}.grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:16px}.domain h3{margin:.3rem 0}.meta{font-size:.86rem;color:var(--muted)}.check{padding:10px 0;border-top:1px solid var(--line)}.incident{border-left:5px solid var(--red)}.limitation{border-left:5px solid #111}.empty{color:var(--muted)}pre{overflow:auto;background:#151515;color:#fff;padding:18px}footer{padding:28px 24px;border-top:1px solid var(--line);color:var(--muted)}
@media(max-width:900px){.summary,.grid{grid-template-columns:1fr}}
</style></head><body>
<header><div class="wrap"><p class="eyebrow">Sustainable Catalyst Platform Core</p><h1>Trust Center</h1><p class="lede">Public evaluation results, incidents, known limitations, attestations, and machine-readable trust status for the Sustainable Catalyst knowledge, evidence, calculation, AI, accessibility, source, and developer infrastructure.</p><div class="actions"><a class="button" href="/trust/status.json">Machine-readable status</a><a class="button secondary" href="/trust/evaluations.json">Evaluation records</a><a class="button secondary" href="/developers">Developer Portal</a></div></div></header>
<main><section id="summary" class="summary"><article class="card">Loading trust status...</article></section>
<section class="section"><p class="eyebrow">Evaluation domains</p><h2>Latest public results</h2><div id="domains" class="grid"></div></section>
<section class="section"><p class="eyebrow">Evaluation framework</p><h2>Methods and check-level evidence</h2><div id="evaluations" class="grid"></div></section>
<section class="section"><p class="eyebrow">Operational disclosure</p><h2>Active incidents</h2><div id="incidents" class="grid"></div></section>
<section class="section"><p class="eyebrow">Boundaries</p><h2>Known limitations</h2><div id="limitations" class="grid"></div></section>
<section class="section"><p class="eyebrow">Attestations</p><h2>Current statements</h2><div id="attestations" class="grid"></div></section>
<section class="section"><p class="eyebrow">Interpretation</p><h2>What this status means</h2><p>No badge establishes truth, regulatory compliance, professional assurance, scientific consensus, or freedom from error. Trust Center results report the checks performed, the observations supplied, and the limitations currently disclosed. Missing or stale evaluations remain visible rather than being silently treated as passing.</p></section></main>
<footer><div class="wrap">Sustainable Catalyst · An open knowledge lab where ideas become public infrastructure.</div></footer>
<script>
const esc=v=>String(v??"").replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#039;"}[c]));
const card=(title,body,cls="")=>`<article class="card ${cls}"><h3>${esc(title)}</h3>${body}</article>`;
async function load(){const [s,e]=await Promise.all([fetch('/trust/status.json').then(r=>r.json()),fetch('/trust/evaluations.json').then(r=>r.json())]);
 document.getElementById('summary').innerHTML=`<article class="card"><p class="eyebrow">Overall status</p><span class="status ${esc(s.overall_status)}">${esc(s.overall_status)}</span><p class="metric">${s.overall_score==null?'N/A':s.overall_score.toFixed(1)}</p><p>${esc(s.methodology)}</p></article>${card('Grade',`<p class="metric">${esc(s.grade)}</p><p class="meta">Platform ${esc(s.platform_version)}</p>`)}${card('Open findings',`<p class="metric">${s.open_findings}</p><p class="meta">Public unresolved or accepted findings</p>`)}${card('Ledger integrity',`<p class="metric">${s.ledger_valid?'Verified':'Failed'}</p><p class="meta">${s.public_evaluation_runs} public evaluation runs</p>`)}`;
 document.getElementById('domains').innerHTML=s.domains.map(d=>card(d.domain,`<span class="status ${esc(d.status)}">${esc(d.status)}</span><p class="metric">${d.score==null?'N/A':d.score.toFixed(1)}</p><p>${esc(d.summary)}</p><p class="meta">Latest: ${esc(d.latest_completed_at||'not evaluated')} · ${d.open_findings} findings</p>`,'domain')).join('')||'<p class="empty">No public evaluation domains are available.</p>';
 document.getElementById('evaluations').innerHTML=e.map(x=>{const r=x.latest_run,d=x.definition;const checks=r?(r.checks||[]).map(c=>`<div class="check"><strong>${esc(c.name)}</strong> · ${esc(c.status)}${c.score==null?'':` · ${c.score.toFixed(1)}`}<br><span class="meta">${esc(JSON.stringify(c.observed))}</span></div>`).join(''):'<p class="empty">Not yet evaluated.</p>';return card(d.name,`<p>${esc(d.description||'')}</p><p class="meta">Domain: ${esc(d.domain)} · Method: ${esc(d.methodology)}</p>${checks}`)}).join('');
 document.getElementById('incidents').innerHTML=s.active_incidents.map(i=>card(i.title,`<span class="status ${esc(i.status)}">${esc(i.status)}</span><p>${esc(i.summary)}</p><p><strong>Impact:</strong> ${esc(i.impact||'Under assessment')}</p><p class="meta">Severity: ${esc(i.severity)} · Started: ${esc(i.started_at)}</p>`,'incident')).join('')||'<p class="empty">No active public incidents.</p>';
 document.getElementById('limitations').innerHTML=s.known_limitations.map(l=>card(l.title,`<p>${esc(l.description)}</p><p><strong>Impact:</strong> ${esc(l.impact||'Not specified')}</p><p><strong>Mitigation:</strong> ${esc(l.mitigation||'Not specified')}</p><p class="meta">Domain: ${esc(l.domain)} · Status: ${esc(l.status)}</p>`,'limitation')).join('')||'<p class="empty">No active public limitations have been registered.</p>';
 document.getElementById('attestations').innerHTML=s.active_attestations.map(a=>card(a.scope,`<p>${esc(a.statement)}</p><p class="meta">Issuer: ${esc(a.issuer)} · Valid from: ${esc(a.valid_from)}${a.valid_until?' · Valid until: '+esc(a.valid_until):''}</p>`)).join('')||'<p class="empty">No active public attestations.</p>';
}
load().catch(error=>{document.getElementById('summary').innerHTML=card('Trust Center unavailable',`<p>${esc(error)}</p>`)});
</script></body></html>''')
