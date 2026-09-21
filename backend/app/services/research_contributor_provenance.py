from __future__ import annotations
from datetime import datetime, timezone
import hashlib, json
from sqlalchemy import func, select
from sqlalchemy.inspection import inspect as sa_inspect
from ..models import (
 ResearchContributorRecord,ResearchRoleDefinitionRecord,ResearchRoleAssignmentRecord,ResearchContributionRecord,
 ResearchAgentProfileRecord,ResearchAgentActionRecord,ResearchAuthorshipAssertionRecord,ResearchResponsibilityStatementRecord,
 ResearchContributionReviewRecord,ResearchContributorRevisionRecord,ResearchContributorSnapshotRecord,
)
CONTRACT="sc.research.roles-agents-contributor-provenance.v1"
ACTOR_TYPES={"human","ai_agent","software_agent","tool","organization","external_system"}
ROLE_CATEGORIES={"credit","specialist","governance","review","technical","institutional","other"}
SCOPE_TYPES={"project","program","portfolio","protocol","workflow","analysis","publication","investigation","dataset","other"}
VISIBILITIES={"private","internal","public"}; STATUSES={"declared","active","inactive","revoked","archived"}
PRODUCTS={"core","library","research_librarian","workspace","research_lab","workbench","site_intelligence","decision_studio","catalyst_data","external"}
CONTRIBUTION_TYPES={"conceptualization","data_curation","formal_analysis","funding_acquisition","investigation","methodology","project_administration","resources","software","supervision","validation","visualization","writing_original_draft","writing_review_editing","evidence_analysis","causal_analysis","forensic_analysis","replication","peer_review","other"}
SPECIALIST_ROLES={"librarian","evidence_analyst","statistician","causal_analyst","forensic_analyst","visualization_analyst","methodologist","reviewer","replication_analyst","data_analyst","research_assistant","other"}
FORBIDDEN={"assign_roles_by_core","authorize_agents_by_core","execute_agent_actions_by_core","infer_contributor_identity_by_core","infer_authorship_by_core","rank_contributors_by_core","score_contributions_by_core","infer_responsibility_by_core","grant_permissions_by_core","decide_credit_by_core","determine_truth_by_core"}
CLASSES=[ResearchContributorRecord,ResearchRoleDefinitionRecord,ResearchRoleAssignmentRecord,ResearchContributionRecord,ResearchAgentProfileRecord,ResearchAgentActionRecord,ResearchAuthorshipAssertionRecord,ResearchResponsibilityStatementRecord,ResearchContributionReviewRecord,ResearchContributorRevisionRecord,ResearchContributorSnapshotRecord]
COUNT_NAMES=["contributors","role_definitions","role_assignments","contributions","agent_profiles","agent_actions","authorship_assertions","responsibility_statements","contribution_reviews","revisions","snapshots"]
def _ser(r):
 o={}
 for a in sa_inspect(r).mapper.column_attrs:
  v=getattr(r,a.key); o[a.key]=v.isoformat() if isinstance(v,datetime) else v
 for k in list(o):
  if k.endswith("_json"): o[k[:-5]]=o.pop(k)
 return o
def _hash(v): return hashlib.sha256(json.dumps(v,sort_keys=True,separators=(",",":"),default=str).encode()).hexdigest()
def _reject(p):
 bad=sorted(k for k in FORBIDDEN if p.get(k) not in (None,False))
 if bad: raise ValueError("Core records declared roles, attribution, contributor provenance, and auditable agent actions; it does not assign authority, authorize or execute agents, infer identity/authorship/responsibility, rank contributors, score contributions, grant permissions, decide credit, or determine truth: "+", ".join(bad))
def boundaries(): return {"contributor_registry_by_core":True,"role_definition_registry_by_core":True,"scoped_role_assignment_registry_by_core":True,"contribution_provenance_registry_by_core":True,"credit_taxonomy_registry_by_core":True,"controlled_agent_profile_registry_by_core":True,"agent_action_audit_registry_by_core":True,"authorship_assertion_registry_by_core":True,"responsibility_statement_registry_by_core":True,"contribution_review_registry_by_core":True,"human_ai_tool_distinction_by_core":True,"revision_history_by_core":True,"immutable_contributor_snapshots_by_core":True,**{k:False for k in FORBIDDEN}}
def readiness(db):
 counts={n:db.scalar(select(func.count()).select_from(c)) or 0 for c,n in zip(CLASSES,COUNT_NAMES)}
 return {"release":"2.93.0","contract":CONTRACT,"actor_types":sorted(ACTOR_TYPES),"role_categories":sorted(ROLE_CATEGORIES),"contribution_types":sorted(CONTRIBUTION_TYPES),"specialist_roles":sorted(SPECIALIST_ROLES),"products":sorted(PRODUCTS),"counts":counts,**boundaries()}
def _get(db,cls,i,label):
 r=db.get(cls,i)
 if not r: raise ValueError(label+" not found")
 return r
def _rows(db,cls,field,value): return [_ser(x) for x in db.scalars(select(cls).where(getattr(cls,field)==value).order_by(cls.created_at,cls.id)).all()]
def create_contributor(db,p):
 _reject(p); actor=p.get("actor_type","human"); vis=p.get("visibility","private"); status=p.get("status","active")
 if actor not in ACTOR_TYPES or vis not in VISIBILITIES or status not in STATUSES: raise ValueError("unsupported contributor actor_type/visibility/status")
 r=ResearchContributorRecord(contributor_key=p["contributor_key"],display_name=p["display_name"],actor_type=actor,identity_ref=p.get("identity_ref"),affiliation_ref=p.get("affiliation_ref"),status=status,visibility=vis,metadata_json=p.get("metadata",{}),provenance_json=p.get("provenance",{}),created_by=p.get("created_by","operator")); db.add(r); db.commit(); db.refresh(r); return _ser(r)
def create_role_definition(db,p):
 _reject(p); cat=p.get("role_category","other")
 if cat not in ROLE_CATEGORIES: raise ValueError("unsupported role category")
 r=ResearchRoleDefinitionRecord(role_key=p["role_key"],label=p["label"],role_category=cat,description=p.get("description"),taxonomy_ref=p.get("taxonomy_ref"),capabilities_json=p.get("capabilities",{}),restrictions_json=p.get("restrictions",{}),metadata_json=p.get("metadata",{}),provenance_json=p.get("provenance",{}),created_by=p.get("created_by","operator")); db.add(r); db.commit(); db.refresh(r); return _ser(r)
def assign_role(db,p):
 _reject(p); _get(db,ResearchContributorRecord,p["contributor_id"],"contributor"); _get(db,ResearchRoleDefinitionRecord,p["role_definition_id"],"role definition"); scope=p.get("scope_type","project"); vis=p.get("visibility","internal")
 if scope not in SCOPE_TYPES or vis not in VISIBILITIES: raise ValueError("unsupported assignment scope/visibility")
 r=ResearchRoleAssignmentRecord(assignment_key=p["assignment_key"],contributor_id=p["contributor_id"],role_definition_id=p["role_definition_id"],scope_type=scope,scope_ref=p["scope_ref"],status=p.get("status","declared"),delegated_by_ref=p.get("delegated_by_ref"),effective_from=p.get("effective_from"),effective_to=p.get("effective_to"),visibility=vis,metadata_json=p.get("metadata",{}),provenance_json=p.get("provenance",{}),created_by=p.get("created_by","operator")); db.add(r); db.commit(); db.refresh(r); return _ser(r)
def record_contribution(db,p):
 _reject(p); _get(db,ResearchContributorRecord,p["contributor_id"],"contributor"); ctype=p.get("contribution_type","other"); prod=p.get("product_key","core"); vis=p.get("visibility","internal")
 if ctype not in CONTRIBUTION_TYPES or prod not in PRODUCTS or vis not in VISIBILITIES: raise ValueError("unsupported contribution type/product/visibility")
 if p.get("role_assignment_id"): _get(db,ResearchRoleAssignmentRecord,p["role_assignment_id"],"role assignment")
 r=ResearchContributionRecord(contribution_key=p["contribution_key"],contributor_id=p["contributor_id"],role_assignment_id=p.get("role_assignment_id"),project_ref=p["project_ref"],contribution_type=ctype,action_type=p["action_type"],product_key=prod,object_type=p["object_type"],object_ref=p["object_ref"],object_version_ref=p.get("object_version_ref"),inputs_json=p.get("inputs",[]),outputs_json=p.get("outputs",[]),method_ref=p.get("method_ref"),tool_ref=p.get("tool_ref"),runtime_ref=p.get("runtime_ref"),model_ref=p.get("model_ref"),statement=p.get("statement"),visibility=vis,metadata_json=p.get("metadata",{}),provenance_json=p.get("provenance",{}),created_by=p.get("created_by","operator")); db.add(r); db.commit(); db.refresh(r); return _ser(r)
def create_agent_profile(db,p):
 _reject(p); c=_get(db,ResearchContributorRecord,p["contributor_id"],"contributor"); role=p.get("specialist_role","other"); vis=p.get("visibility","internal")
 if c.actor_type not in {"ai_agent","software_agent","tool"}: raise ValueError("agent profile requires ai_agent, software_agent, or tool contributor")
 if role not in SPECIALIST_ROLES or vis not in VISIBILITIES: raise ValueError("unsupported specialist role/visibility")
 if p.get("autonomy_level","human_supervised") not in {"human_supervised","human_approved","bounded_autonomous","non_autonomous"}: raise ValueError("unsupported autonomy level")
 r=ResearchAgentProfileRecord(agent_key=p["agent_key"],contributor_id=p["contributor_id"],specialist_role=role,provider_ref=p.get("provider_ref"),model_ref=p.get("model_ref"),configuration_hash=p.get("configuration_hash"),autonomy_level=p.get("autonomy_level","human_supervised"),human_supervisor_ref=p.get("human_supervisor_ref"),allowed_actions_json=p.get("allowed_actions",[]),prohibited_actions_json=p.get("prohibited_actions",[]),status=p.get("status","declared"),visibility=vis,metadata_json=p.get("metadata",{}),provenance_json=p.get("provenance",{}),created_by=p.get("created_by","operator")); db.add(r); db.commit(); db.refresh(r); return _ser(r)
def record_agent_action(db,p):
 _reject(p); _get(db,ResearchAgentProfileRecord,p["agent_profile_id"],"agent profile"); vis=p.get("visibility","internal")
 if vis not in VISIBILITIES: raise ValueError("unsupported visibility")
 if p.get("contribution_id"): _get(db,ResearchContributionRecord,p["contribution_id"],"contribution")
 r=ResearchAgentActionRecord(action_key=p["action_key"],agent_profile_id=p["agent_profile_id"],contribution_id=p.get("contribution_id"),project_ref=p["project_ref"],action_type=p["action_type"],inputs_json=p.get("inputs",[]),outputs_json=p.get("outputs",[]),tool_ref=p.get("tool_ref"),runtime_ref=p.get("runtime_ref"),model_ref=p.get("model_ref"),decision_basis_json=p.get("decision_basis",{}),human_review_status=p.get("human_review_status","not_reviewed"),visibility=vis,metadata_json=p.get("metadata",{}),provenance_json=p.get("provenance",{}),created_by=p.get("created_by","operator")); db.add(r); db.commit(); db.refresh(r); return _ser(r)
def assert_authorship(db,p):
 _reject(p); _get(db,ResearchContributorRecord,p["contributor_id"],"contributor"); vis=p.get("visibility","internal")
 if vis not in VISIBILITIES: raise ValueError("unsupported visibility")
 r=ResearchAuthorshipAssertionRecord(assertion_key=p["assertion_key"],contributor_id=p["contributor_id"],project_ref=p["project_ref"],publication_ref=p.get("publication_ref"),authorship_type=p.get("authorship_type","author"),position_label=p.get("position_label"),contribution_statement=p["contribution_statement"],corresponding_author=bool(p.get("corresponding_author",False)),visibility=vis,provenance_json=p.get("provenance",{}),created_by=p.get("created_by","operator")); db.add(r); db.commit(); db.refresh(r); return _ser(r)
def declare_responsibility(db,p):
 _reject(p); _get(db,ResearchContributorRecord,p["contributor_id"],"contributor"); vis=p.get("visibility","internal")
 if vis not in VISIBILITIES: raise ValueError("unsupported visibility")
 r=ResearchResponsibilityStatementRecord(statement_key=p["statement_key"],contributor_id=p["contributor_id"],project_ref=p["project_ref"],scope_type=p.get("scope_type","project"),scope_ref=p["scope_ref"],responsibility_type=p["responsibility_type"],statement=p["statement"],acceptance_status=p.get("acceptance_status","declared"),visibility=vis,provenance_json=p.get("provenance",{}),created_by=p.get("created_by","operator")); db.add(r); db.commit(); db.refresh(r); return _ser(r)
def review_contribution(db,p):
 _reject(p); _get(db,ResearchContributionRecord,p["contribution_id"],"contribution"); _get(db,ResearchContributorRecord,p["reviewer_contributor_id"],"reviewer contributor"); vis=p.get("visibility","internal")
 if vis not in VISIBILITIES: raise ValueError("unsupported visibility")
 r=ResearchContributionReviewRecord(review_key=p["review_key"],contribution_id=p["contribution_id"],reviewer_contributor_id=p["reviewer_contributor_id"],project_ref=p["project_ref"],review_type=p.get("review_type","review"),status=p.get("status","recorded"),notes=p.get("notes"),evidence_json=p.get("evidence",[]),visibility=vis,provenance_json=p.get("provenance",{}),created_by=p.get("created_by","operator")); db.add(r); db.commit(); db.refresh(r); return _ser(r)
def revise(db,p):
 _reject(p); project=p["project_ref"]; n=(db.scalar(select(func.max(ResearchContributorRevisionRecord.revision)).where(ResearchContributorRevisionRecord.project_ref==project)) or 0)+1
 if p.get("contributor_id"): _get(db,ResearchContributorRecord,p["contributor_id"],"contributor")
 r=ResearchContributorRevisionRecord(project_ref=project,revision=n,contributor_id=p.get("contributor_id"),change_type=p.get("change_type","metadata"),prior_state_json=p.get("prior_state",{}),revised_state_json=p.get("revised_state",{}),change_summary=p.get("change_summary"),provenance_json=p.get("provenance",{}),created_by=p.get("created_by","operator")); db.add(r); db.commit(); db.refresh(r); return _ser(r)
def _project_bundle(db,project,public=False):
 contributions=_rows(db,ResearchContributionRecord,"project_ref",project); actions=_rows(db,ResearchAgentActionRecord,"project_ref",project); authorship=_rows(db,ResearchAuthorshipAssertionRecord,"project_ref",project); responsibility=_rows(db,ResearchResponsibilityStatementRecord,"project_ref",project); reviews=_rows(db,ResearchContributionReviewRecord,"project_ref",project)
 contrib_ids={x["contributor_id"] for x in contributions+authorship+responsibility}; contrib_ids.update(x["reviewer_contributor_id"] for x in reviews)
 contributors=[_ser(x) for x in db.scalars(select(ResearchContributorRecord).where(ResearchContributorRecord.id.in_(contrib_ids))).all()] if contrib_ids else []
 assignments=[_ser(x) for x in db.scalars(select(ResearchRoleAssignmentRecord).where(ResearchRoleAssignmentRecord.scope_ref==project)).all()]
 profiles=[]
 if contributors:
  ids={x["id"] for x in contributors}; profiles=[_ser(x) for x in db.scalars(select(ResearchAgentProfileRecord).where(ResearchAgentProfileRecord.contributor_id.in_(ids))).all()]
 roles=[]
 if assignments:
  ids={x["role_definition_id"] for x in assignments}; roles=[_ser(x) for x in db.scalars(select(ResearchRoleDefinitionRecord).where(ResearchRoleDefinitionRecord.id.in_(ids))).all()]
 revisions=_rows(db,ResearchContributorRevisionRecord,"project_ref",project); snapshots=_rows(db,ResearchContributorSnapshotRecord,"project_ref",project)
 if public:
  filt=lambda xs:[x for x in xs if x.get("visibility")=="public"]
  contributions=filt(contributions); actions=filt(actions); authorship=filt(authorship); responsibility=filt(responsibility); reviews=filt(reviews); contributors=filt(contributors); assignments=filt(assignments); profiles=filt(profiles); revisions=[]; snapshots=[]
  allowed={x["id"] for x in contributors}; contributions=[x for x in contributions if x["contributor_id"] in allowed]; authorship=[x for x in authorship if x["contributor_id"] in allowed]; responsibility=[x for x in responsibility if x["contributor_id"] in allowed]; reviews=[x for x in reviews if x["reviewer_contributor_id"] in allowed]; assignments=[x for x in assignments if x["contributor_id"] in allowed]; profiles=[x for x in profiles if x["contributor_id"] in allowed]
 return {"project_ref":project,"contributors":contributors,"role_definitions":roles,"role_assignments":assignments,"contributions":contributions,"agent_profiles":profiles,"agent_actions":actions,"authorship_assertions":authorship,"responsibility_statements":responsibility,"contribution_reviews":reviews,"revisions":revisions,"snapshots":snapshots}
def snapshot(db,p):
 _reject(p); project=p["project_ref"]; state=_project_bundle(db,project,False); state["snapshots"]=[]; n=(db.scalar(select(func.max(ResearchContributorSnapshotRecord.revision)).where(ResearchContributorSnapshotRecord.project_ref==project)) or 0)+1; prev=db.scalar(select(ResearchContributorSnapshotRecord).where(ResearchContributorSnapshotRecord.project_ref==project).order_by(ResearchContributorSnapshotRecord.revision.desc()).limit(1)); h=_hash(state); r=ResearchContributorSnapshotRecord(project_ref=project,revision=n,content_hash=h,previous_snapshot_hash=prev.content_hash if prev else None,state_json=state,provenance_json=p.get("provenance",{}),created_by=p.get("created_by","operator")); db.add(r); db.commit(); db.refresh(r); return _ser(r)
def descriptive_summary(db,project,public=False):
 b=_project_bundle(db,project,public); return {"release":"2.93.0","contract":CONTRACT,"project_ref":project,"counts":{k:len(v) for k,v in b.items() if isinstance(v,list)},"actor_types":sorted({x["actor_type"] for x in b["contributors"]}),"summary_is_descriptive_not_credit_or_authority_judgment":True,**boundaries()}
def lineage(db,project,public=False):
 b=_project_bundle(db,project,public); nodes=[]; edges=[]
 for c in b["contributors"]: nodes.append({"id":"contributor:"+c["id"],"type":"contributor","actor_type":c["actor_type"],"label":c["display_name"]})
 for a in b["role_assignments"]: nodes.append({"id":"assignment:"+a["id"],"type":"role_assignment"}); edges.append({"from":"contributor:"+a["contributor_id"],"to":"assignment:"+a["id"],"relation":"has_declared_role"})
 for c in b["contributions"]: nodes.append({"id":"contribution:"+c["id"],"type":"contribution","contribution_type":c["contribution_type"],"object_ref":c["object_ref"]}); edges.append({"from":"contributor:"+c["contributor_id"],"to":"contribution:"+c["id"],"relation":"declared_contributor"})
 for a in b["agent_actions"]: nodes.append({"id":"agent_action:"+a["id"],"type":"agent_action","action_type":a["action_type"]});
 for x in b["authorship_assertions"]: edges.append({"from":"contributor:"+x["contributor_id"],"to":x.get("publication_ref") or project,"relation":"declared_authorship"})
 return {"release":"2.93.0","contract":CONTRACT,"project_ref":project,"nodes":nodes,"edges":edges,"lineage_is_declared_not_inferred":True}
def bundle(db,project,public=False):
 b=_project_bundle(db,project,public); b.update({"release":"2.93.0","contract":CONTRACT,"summary":descriptive_summary(db,project,public),"lineage":lineage(db,project,public),"attribution_is_declared_not_core_decided":True}); return b
