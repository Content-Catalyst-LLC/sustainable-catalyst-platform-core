from __future__ import annotations
from collections import Counter
from datetime import datetime
import hashlib, json
from sqlalchemy import func, select
from sqlalchemy.inspection import inspect as sa_inspect
from sqlalchemy.orm import Session
from ..models import (
    ResearchProgramRecord, ResearchPortfolioRecord, ResearchPortfolioProgramRecord,
    ResearchPortfolioThemeRecord, ResearchPortfolioObjectiveRecord, ResearchPortfolioDependencyRecord,
    ResearchPortfolioResourceEnvelopeRecord, ResearchPortfolioRiskRecord, ResearchPortfolioReviewRecord,
    ResearchPortfolioDecisionRecord, ResearchPortfolioRevisionRecord, ResearchPortfolioSnapshotRecord,
)
CONTRACT="sc.research.portfolio-institutional-governance.v1"
PORTFOLIO_STATUSES={"draft","active","paused","completed","archived"}; VISIBILITIES={"private","internal","public"}
MEMBERSHIP_ROLES={"member","lead","supporting","reference"}; MEMBERSHIP_STATUSES={"active","completed","withdrawn","archived"}
THEME_STATUSES={"proposed","active","completed","deferred","archived"}; OBJECTIVE_STATUSES=THEME_STATUSES
DEPENDENCY_TYPES={"depends_on","shares_data","shares_method","informs","overlaps","coordinated_with","other"}
RESOURCE_TYPES={"budget","personnel","compute","data","time","facilities","other"}; RISK_STATUSES={"open","monitoring","mitigated","accepted","closed"}
FORBIDDEN={"prioritize_programs_by_core","allocate_resources_by_core","allocate_funding_by_core","rank_programs_by_core","score_programs_by_core","optimize_portfolio_by_core","decide_governance_by_core","infer_strategic_value_by_core","forecast_program_success_by_core","close_risks_by_core","infer_truth_by_core"}
CLASSES=[ResearchPortfolioRecord,ResearchPortfolioProgramRecord,ResearchPortfolioThemeRecord,ResearchPortfolioObjectiveRecord,ResearchPortfolioDependencyRecord,ResearchPortfolioResourceEnvelopeRecord,ResearchPortfolioRiskRecord,ResearchPortfolioReviewRecord,ResearchPortfolioDecisionRecord,ResearchPortfolioRevisionRecord,ResearchPortfolioSnapshotRecord]
COUNT_NAMES=["portfolios","program_memberships","themes","objectives","dependencies","resource_envelopes","risks","reviews","governance_decisions","revisions","snapshots"]

def _ser(record):
    out={}
    for attr in sa_inspect(record).mapper.column_attrs:
        value=getattr(record,attr.key); out[attr.key]=value.isoformat() if isinstance(value,datetime) else value
    for key in list(out):
        if key.endswith("_json"): out[key[:-5]]=out.pop(key)
    return out

def _hash(value): return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(",",":"),default=str).encode()).hexdigest()
def _reject(payload):
    bad=sorted(k for k in FORBIDDEN if payload.get(k) not in (None,False))
    if bad: raise ValueError("Core records declared research-portfolio governance; it does not rank/prioritize programs, allocate resources or funding, optimize portfolios, make governance decisions, infer strategic value, forecast success, close risks, or infer truth: "+", ".join(bad))

def boundaries():
    return {
      "research_portfolio_registry_by_core":True,"portfolio_program_membership_registry_by_core":True,"portfolio_theme_registry_by_core":True,"portfolio_objective_registry_by_core":True,
      "declared_program_dependency_registry_by_core":True,"declared_resource_envelope_registry_by_core":True,"portfolio_risk_registry_by_core":True,"portfolio_review_registry_by_core":True,
      "researcher_authored_governance_decision_registry_by_core":True,"descriptive_portfolio_map_by_core":True,"portfolio_revision_history_by_core":True,"portfolio_lineage_by_core":True,"immutable_portfolio_snapshots_by_core":True,
      "prioritize_programs_by_core":False,"allocate_resources_by_core":False,"allocate_funding_by_core":False,"rank_programs_by_core":False,"score_programs_by_core":False,"optimize_portfolio_by_core":False,
      "decide_governance_by_core":False,"infer_strategic_value_by_core":False,"forecast_program_success_by_core":False,"close_risks_by_core":False,"infer_truth_by_core":False,
    }

def readiness(db:Session):
    counts={name:db.scalar(select(func.count()).select_from(cls)) or 0 for name,cls in zip(COUNT_NAMES,CLASSES)}
    return {"release":"2.85.0","contract":CONTRACT,"counts":counts,**boundaries()}
def _portfolio(db,id):
    r=db.get(ResearchPortfolioRecord,id)
    if r is None: raise ValueError("research portfolio not found.")
    return r
def _program(db,id):
    r=db.get(ResearchProgramRecord,id)
    if r is None: raise ValueError("research program not found.")
    return r
def _public_portfolio(db,id):
    r=_portfolio(db,id)
    if r.visibility!="public": raise ValueError("research portfolio is not public.")
    return r

def create_portfolio(db,payload):
    _reject(payload); key=str(payload.get("portfolio_key") or "").strip(); title=str(payload.get("title") or "").strip(); status=payload.get("status","active"); vis=payload.get("visibility","private")
    if not key or not title: raise ValueError("portfolio_key and title are required.")
    if status not in PORTFOLIO_STATUSES: raise ValueError("unsupported portfolio status: "+str(status))
    if vis not in VISIBILITIES: raise ValueError("unsupported visibility: "+str(vis))
    r=ResearchPortfolioRecord(portfolio_key=key,title=title,description_text=payload.get("description_text"),status=status,visibility=vis,horizon_start=payload.get("horizon_start"),horizon_end=payload.get("horizon_end"),charter_text=payload.get("charter_text"),scope_json=payload.get("scope",{}),governance_json=payload.get("governance",{}),provenance_json=payload.get("provenance",{}),metadata_json=payload.get("metadata",{}),created_by=payload.get("created_by","operator")); db.add(r); db.commit(); db.refresh(r); return _ser(r)
def add_program(db,pid,payload):
    _reject(payload); _portfolio(db,pid); prg=str(payload.get("program_id") or "").strip(); _program(db,prg); key=str(payload.get("membership_key") or prg); role=payload.get("role","member"); status=payload.get("status","active")
    if role not in MEMBERSHIP_ROLES: raise ValueError("unsupported membership role: "+str(role))
    if status not in MEMBERSHIP_STATUSES: raise ValueError("unsupported membership status: "+str(status))
    r=ResearchPortfolioProgramRecord(portfolio_id=pid,program_id=prg,membership_key=key,role=role,status=status,joined_at=payload.get("joined_at"),left_at=payload.get("left_at"),rationale_text=payload.get("rationale_text"),provenance_json=payload.get("provenance",{}),created_by=payload.get("created_by","operator")); db.add(r); db.commit(); db.refresh(r); return _ser(r)
def add_theme(db,pid,payload):
    _reject(payload); _portfolio(db,pid); key=str(payload.get("theme_key") or "").strip(); title=str(payload.get("title") or "").strip(); status=payload.get("status","active")
    if not key or not title: raise ValueError("theme_key and title are required.")
    if status not in THEME_STATUSES: raise ValueError("unsupported theme status: "+str(status))
    r=ResearchPortfolioThemeRecord(portfolio_id=pid,theme_key=key,title=title,description_text=payload.get("description_text"),status=status,scope_json=payload.get("scope",{}),evidence_refs_json=payload.get("evidence_refs",[]),provenance_json=payload.get("provenance",{}),created_by=payload.get("created_by","operator")); db.add(r); db.commit(); db.refresh(r); return _ser(r)
def add_objective(db,pid,payload):
    _reject(payload); _portfolio(db,pid); key=str(payload.get("objective_key") or "").strip(); title=str(payload.get("title") or "").strip(); status=payload.get("status","active")
    if not key or not title: raise ValueError("objective_key and title are required.")
    if status not in OBJECTIVE_STATUSES: raise ValueError("unsupported objective status: "+str(status))
    r=ResearchPortfolioObjectiveRecord(portfolio_id=pid,objective_key=key,title=title,description_text=payload.get("description_text"),status=status,target_horizon=payload.get("target_horizon"),success_criteria_json=payload.get("success_criteria",[]),evidence_refs_json=payload.get("evidence_refs",[]),provenance_json=payload.get("provenance",{}),created_by=payload.get("created_by","operator")); db.add(r); db.commit(); db.refresh(r); return _ser(r)
def add_dependency(db,pid,payload):
    _reject(payload); _portfolio(db,pid); key=str(payload.get("dependency_key") or "").strip(); a=str(payload.get("source_program_id") or "").strip(); b=str(payload.get("target_program_id") or "").strip(); typ=payload.get("relation_type")
    if not key or not a or not b or not typ: raise ValueError("dependency_key, source_program_id, target_program_id, and relation_type are required.")
    _program(db,a); _program(db,b)
    if typ not in DEPENDENCY_TYPES: raise ValueError("unsupported dependency relation_type: "+str(typ))
    r=ResearchPortfolioDependencyRecord(portfolio_id=pid,dependency_key=key,source_program_id=a,target_program_id=b,relation_type=typ,rationale_text=payload.get("rationale_text"),evidence_refs_json=payload.get("evidence_refs",[]),provenance_json=payload.get("provenance",{}),created_by=payload.get("created_by","operator")); db.add(r); db.commit(); db.refresh(r); return _ser(r)
def add_resource_envelope(db,pid,payload):
    _reject(payload); _portfolio(db,pid); key=str(payload.get("envelope_key") or "").strip(); typ=payload.get("resource_type"); label=str(payload.get("label") or "").strip()
    if not key or not typ or not label: raise ValueError("envelope_key, resource_type, and label are required.")
    if typ not in RESOURCE_TYPES: raise ValueError("unsupported resource_type: "+str(typ))
    r=ResearchPortfolioResourceEnvelopeRecord(portfolio_id=pid,envelope_key=key,resource_type=typ,label=label,declared_amount_text=payload.get("declared_amount_text"),unit=payload.get("unit"),period_start=payload.get("period_start"),period_end=payload.get("period_end"),constraints_json=payload.get("constraints",[]),related_refs_json=payload.get("related_refs",[]),provenance_json=payload.get("provenance",{}),created_by=payload.get("created_by","operator")); db.add(r); db.commit(); db.refresh(r); return _ser(r)
def add_risk(db,pid,payload):
    _reject(payload); _portfolio(db,pid); key=str(payload.get("risk_key") or "").strip(); title=str(payload.get("title") or "").strip(); status=payload.get("status","open")
    if not key or not title: raise ValueError("risk_key and title are required.")
    if status not in RISK_STATUSES: raise ValueError("unsupported risk status: "+str(status))
    r=ResearchPortfolioRiskRecord(portfolio_id=pid,risk_key=key,title=title,risk_type=payload.get("risk_type","research"),status=status,description_text=payload.get("description_text"),impact_text=payload.get("impact_text"),mitigation_refs_json=payload.get("mitigation_refs",[]),evidence_refs_json=payload.get("evidence_refs",[]),provenance_json=payload.get("provenance",{}),created_by=payload.get("created_by","operator")); db.add(r); db.commit(); db.refresh(r); return _ser(r)
def add_review(db,pid,payload):
    _reject(payload); _portfolio(db,pid); key=str(payload.get("review_key") or "").strip(); at=str(payload.get("reviewed_at") or "").strip()
    if not key or not at: raise ValueError("review_key and reviewed_at are required.")
    r=ResearchPortfolioReviewRecord(portfolio_id=pid,review_key=key,reviewed_at=at,review_type=payload.get("review_type","periodic"),status=payload.get("status","recorded"),summary_text=payload.get("summary_text"),observations_json=payload.get("observations",[]),recommendations_json=payload.get("recommendations",[]),evidence_refs_json=payload.get("evidence_refs",[]),provenance_json=payload.get("provenance",{}),created_by=payload.get("created_by","operator")); db.add(r); db.commit(); db.refresh(r); return _ser(r)
def add_decision(db,pid,payload):
    _reject(payload); _portfolio(db,pid); key=str(payload.get("decision_key") or "").strip(); at=str(payload.get("decided_at") or "").strip(); typ=str(payload.get("decision_type") or "").strip(); stmt=str(payload.get("statement_text") or "").strip()
    if not key or not at or not typ or not stmt: raise ValueError("decision_key, decided_at, decision_type, and statement_text are required.")
    r=ResearchPortfolioDecisionRecord(portfolio_id=pid,decision_key=key,decided_at=at,decision_type=typ,status=payload.get("status","recorded"),statement_text=stmt,rationale_text=payload.get("rationale_text"),decision_maker=payload.get("decision_maker"),related_refs_json=payload.get("related_refs",[]),evidence_refs_json=payload.get("evidence_refs",[]),provenance_json=payload.get("provenance",{}),created_by=payload.get("created_by","operator")); db.add(r); db.commit(); db.refresh(r); return _ser(r)
def _rows(db,cls,pid): return [_ser(x) for x in db.scalars(select(cls).where(cls.portfolio_id==pid).order_by(cls.created_at.asc())).all()]
def descriptive_summary(db,pid,public=False):
    p=_public_portfolio(db,pid) if public else _portfolio(db,pid); memberships=_rows(db,ResearchPortfolioProgramRecord,pid)
    if public:
        public_ids={x.id for x in db.scalars(select(ResearchProgramRecord).where(ResearchProgramRecord.visibility=="public")).all()}; memberships=[x for x in memberships if x["program_id"] in public_ids]
    risks=_rows(db,ResearchPortfolioRiskRecord,pid); deps=_rows(db,ResearchPortfolioDependencyRecord,pid)
    return {"release":"2.85.0","contract":CONTRACT,"portfolio_id":pid,"portfolio_status":p.status,"program_count":len(memberships),"theme_count":db.scalar(select(func.count()).select_from(ResearchPortfolioThemeRecord).where(ResearchPortfolioThemeRecord.portfolio_id==pid)) or 0,"objective_count":db.scalar(select(func.count()).select_from(ResearchPortfolioObjectiveRecord).where(ResearchPortfolioObjectiveRecord.portfolio_id==pid)) or 0,"dependency_count":len(deps),"open_risk_count":sum(1 for x in risks if x["status"] in {"open","monitoring"}),"review_count":db.scalar(select(func.count()).select_from(ResearchPortfolioReviewRecord).where(ResearchPortfolioReviewRecord.portfolio_id==pid)) or 0,"governance_decision_count":db.scalar(select(func.count()).select_from(ResearchPortfolioDecisionRecord).where(ResearchPortfolioDecisionRecord.portfolio_id==pid)) or 0,"summary_is_descriptive_only":True,**boundaries()}
def portfolio_map(db,pid,public=False):
    _public_portfolio(db,pid) if public else _portfolio(db,pid); members=_rows(db,ResearchPortfolioProgramRecord,pid); deps=_rows(db,ResearchPortfolioDependencyRecord,pid)
    if public:
        public_ids={x.id for x in db.scalars(select(ResearchProgramRecord).where(ResearchProgramRecord.visibility=="public")).all()}; members=[x for x in members if x["program_id"] in public_ids]; deps=[x for x in deps if x["source_program_id"] in public_ids and x["target_program_id"] in public_ids]
    return {"release":"2.85.0","contract":CONTRACT,"portfolio_id":pid,"programs":members,"dependencies":deps,"map_is_declared_not_inferred":True,"rank_programs_by_core":False,"infer_strategic_value_by_core":False}
def lineage(db,pid,public=False):
    p=_public_portfolio(db,pid) if public else _portfolio(db,pid); b=bundle(db,pid,public,include_lineage=False)
    return {"release":"2.85.0","contract":CONTRACT,"portfolio_id":pid,"program_membership_edges":[{"membership_id":x["id"],"program_id":x["program_id"],"role":x["role"]} for x in b["program_memberships"]],"dependency_edges":[{"dependency_id":x["id"],"source_program_id":x["source_program_id"],"target_program_id":x["target_program_id"],"relation_type":x["relation_type"],"evidence_refs":x.get("evidence_refs",[])} for x in b["dependencies"]],"objective_evidence_edges":[{"objective_id":x["id"],"evidence_refs":x.get("evidence_refs",[])} for x in b["objectives"]],"risk_evidence_edges":[{"risk_id":x["id"],"evidence_refs":x.get("evidence_refs",[])} for x in b["risks"]],"decision_evidence_edges":[{"decision_id":x["id"],"related_refs":x.get("related_refs",[]),"evidence_refs":x.get("evidence_refs",[])} for x in b["governance_decisions"]],"lineage_is_declared_not_inferred":True,"missing_links_inferred_by_core":False}
def bundle(db,pid,public=False,include_lineage=True):
    p=_public_portfolio(db,pid) if public else _portfolio(db,pid); memberships=_rows(db,ResearchPortfolioProgramRecord,pid); dependencies=_rows(db,ResearchPortfolioDependencyRecord,pid)
    if public:
        public_ids={x.id for x in db.scalars(select(ResearchProgramRecord).where(ResearchProgramRecord.visibility=="public")).all()}; memberships=[x for x in memberships if x["program_id"] in public_ids]; dependencies=[x for x in dependencies if x["source_program_id"] in public_ids and x["target_program_id"] in public_ids]
    out={"release":"2.85.0","contract":CONTRACT,"portfolio":_ser(p),"program_memberships":memberships,"themes":_rows(db,ResearchPortfolioThemeRecord,pid),"objectives":_rows(db,ResearchPortfolioObjectiveRecord,pid),"dependencies":dependencies,"resource_envelopes":_rows(db,ResearchPortfolioResourceEnvelopeRecord,pid),"risks":_rows(db,ResearchPortfolioRiskRecord,pid),"reviews":_rows(db,ResearchPortfolioReviewRecord,pid),"governance_decisions":_rows(db,ResearchPortfolioDecisionRecord,pid),"revisions":_rows(db,ResearchPortfolioRevisionRecord,pid),"snapshots":_rows(db,ResearchPortfolioSnapshotRecord,pid),"descriptive_summary":descriptive_summary(db,pid,public),"portfolio_map":portfolio_map(db,pid,public),**boundaries()}
    if include_lineage: out["lineage"]=lineage(db,pid,public)
    return out
def revise_portfolio(db,pid,payload):
    _reject(payload); p=_portfolio(db,pid); prior=_ser(p); allowed={"title","description_text","status","visibility","horizon_start","horizon_end","charter_text"}
    for k in allowed:
        if k in payload: setattr(p,k,payload[k])
    if "scope" in payload: p.scope_json=payload["scope"]
    if "governance" in payload: p.governance_json=payload["governance"]
    if p.status not in PORTFOLIO_STATUSES or p.visibility not in VISIBILITIES: raise ValueError("unsupported revised status or visibility.")
    rev=(db.scalar(select(func.max(ResearchPortfolioRevisionRecord.revision)).where(ResearchPortfolioRevisionRecord.portfolio_id==pid)) or 0)+1; revised=_ser(p); row=ResearchPortfolioRevisionRecord(portfolio_id=pid,revision=rev,state_hash=_hash(revised),prior_state_json=prior,revised_state_json=revised,change_summary=payload.get("change_summary"),provenance_json=payload.get("provenance",{}),created_by=payload.get("created_by","operator")); db.add(row); db.commit(); db.refresh(row); return _ser(row)
def snapshot(db,pid,payload):
    _reject(payload); _portfolio(db,pid); state=bundle(db,pid); state.pop("snapshots",None); h=_hash(state); prev=db.scalar(select(ResearchPortfolioSnapshotRecord).where(ResearchPortfolioSnapshotRecord.portfolio_id==pid).order_by(ResearchPortfolioSnapshotRecord.revision.desc()).limit(1)); rev=1 if prev is None else prev.revision+1
    r=ResearchPortfolioSnapshotRecord(portfolio_id=pid,revision=rev,content_hash=h,previous_snapshot_hash=None if prev is None else prev.content_hash,state_json=state,provenance_json=payload.get("provenance",{}),created_by=payload.get("created_by","operator")); db.add(r); db.commit(); db.refresh(r); return _ser(r)
