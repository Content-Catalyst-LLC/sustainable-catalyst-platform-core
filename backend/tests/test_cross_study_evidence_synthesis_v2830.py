from fastapi.testclient import TestClient
from app.config import Settings
from app.main import create_app

def client(tmp_path): return TestClient(create_app(Settings(database_url="sqlite:///"+str(tmp_path/"synthesis.db"))))
def project(c,visibility="public"):
    r=c.post("/v1/research/projects",json={"data":{"title":"Synthesis Program","project_key":"synthesis-program-"+visibility,"visibility":visibility}}); assert r.status_code==200,r.text; return r.json()["project"]["id"]
def synthesis(c,pid):
    r=c.post(f"/v1/research/evidence-synthesis/projects/{pid}",json={"data":{"synthesis_key":"syn-1","title":"Cross-study evidence synthesis","synthesis_type":"systematic_review","protocol_ref":"protocol:1"}}); assert r.status_code==200,r.text; return r.json()["id"]

def test_readiness(tmp_path):
    c=client(tmp_path); d=c.get("/v1/research/evidence-synthesis/readiness").json(); assert d["release"]=="2.83.0"; assert d["migration_0087_applied"] is True; assert d["evidence_synthesis_registry_by_core"] is True; assert d["externally_computed_meta_analysis_registry_by_core"] is True; assert d["search_literature_by_core"] is False; assert d["compute_effect_size_by_core"] is False; assert d["pool_estimates_by_core"] is False; assert d["infer_truth_by_core"] is False; c.close()

def test_study_outcome_effect_and_external_meta_analysis(tmp_path):
    c=client(tmp_path); pid=project(c); sid=synthesis(c,pid)
    st=c.post(f"/v1/research/evidence-synthesis/syntheses/{sid}/studies",json={"data":{"study_key":"study-1","source_type":"publication","source_ref":"doi:10.example/a","title":"Study A","inclusion_status":"included","inclusion_reason":"Matches registered eligibility criteria.","evidence_refs":["source:a"]}}); assert st.status_code==200,st.text; study_id=st.json()["id"]
    oc=c.post(f"/v1/research/evidence-synthesis/syntheses/{sid}/outcomes",json={"data":{"outcome_key":"mortality","label":"All-cause mortality","measure":"risk_ratio","timepoint":"12 months"}}); assert oc.status_code==200,oc.text; outcome_id=oc.json()["id"]
    ef=c.post(f"/v1/research/evidence-synthesis/syntheses/{sid}/effects",json={"data":{"study_id":study_id,"outcome_id":outcome_id,"effect_key":"e1","effect_measure":"risk_ratio","estimate":{"value":0.82},"uncertainty":{"ci95":[0.70,0.96]},"sample_size":{"n":812},"declared_direction":"negative","source_ref":"table:2","externally_computed":True}}); assert ef.status_code==200,ef.text; assert ef.json()["externally_computed"] is True
    ma=c.post(f"/v1/research/evidence-synthesis/syntheses/{sid}/meta-analyses",json={"data":{"analysis_key":"ma1","outcome_id":outcome_id,"method_ref":"method:random-effects","model_type":"random_effects","effect_measure":"risk_ratio","pooled_estimate":{"value":0.88,"ci95":[0.78,0.99]},"heterogeneity":{"i2":41.0},"study_refs":[study_id],"execution_refs":["run:meta-1"],"externally_computed":True}}); assert ma.status_code==200,ma.text; assert ma.json()["externally_computed"] is True
    b=c.get(f"/v1/research/evidence-synthesis/syntheses/{sid}/bundle").json(); assert len(b["studies"])==1; assert len(b["effects"])==1; assert len(b["meta_analyses"])==1; assert b["pool_estimates_by_core"] is False; c.close()

def test_meta_research_relations_gaps_revision_lineage_snapshot(tmp_path):
    c=client(tmp_path); pid=project(c); sid=synthesis(c,pid)
    a=c.post(f"/v1/research/evidence-synthesis/syntheses/{sid}/assessments",json={"data":{"assessment_key":"bias-1","target_type":"study","target_ref":"study:external-1","dimension":"risk_of_bias","framework_ref":"rob2","declared_judgment":"some_concerns","rationale_text":"Researcher-declared judgment.","evidence_refs":["review:1"]}}); assert a.status_code==200,a.text
    rel=c.post(f"/v1/research/evidence-synthesis/syntheses/{sid}/relations",json={"data":{"relation_key":"r1","source_ref":"study:a","target_ref":"study:b","relation_type":"context_dependent","rationale_text":"Effects differ by setting.","evidence_refs":["effect:a","effect:b"]}}); assert rel.status_code==200,rel.text
    gap=c.post(f"/v1/research/evidence-synthesis/syntheses/{sid}/gaps",json={"data":{"gap_key":"g1","gap_type":"geography","description_text":"No included studies from low-income settings.","declared_priority":"high","evidence_refs":["screening:manifest"]}}); assert gap.status_code==200,gap.text
    rev=c.post(f"/v1/research/evidence-synthesis/syntheses/{sid}/revisions",json={"data":{"status":"synthesis","change_summary":"Extraction completed and synthesis begun."}}); assert rev.status_code==200,rev.text; assert rev.json()["revision"]==1
    sm=c.get(f"/v1/research/evidence-synthesis/syntheses/{sid}/summary").json(); assert sm["assessment_dimensions"]["risk_of_bias"]==1; assert sm["declared_cross_study_relations"]["context_dependent"]==1; assert sm["evidence_gap_types"]["geography"]==1; assert sm["study_quality_scored_by_core"] is False
    ln=c.get(f"/v1/research/evidence-synthesis/syntheses/{sid}/lineage").json(); assert ln["lineage_is_declared_not_inferred"] is True; assert len(ln["assessment_edges"])==1; assert len(ln["declared_relation_edges"])==1
    s1=c.post(f"/v1/research/evidence-synthesis/syntheses/{sid}/snapshots",json={"data":{}}).json(); s2=c.post(f"/v1/research/evidence-synthesis/syntheses/{sid}/snapshots",json={"data":{}}).json(); assert s2["previous_snapshot_hash"]==s1["content_hash"]; c.close()

def test_boundary_rejection(tmp_path):
    c=client(tmp_path); pid=project(c)
    bad=c.post(f"/v1/research/evidence-synthesis/projects/{pid}",json={"data":{"synthesis_key":"bad","title":"Bad","search_literature_by_core":True}}); assert bad.status_code==422,bad.text
    sid=synthesis(c,pid); bad2=c.post(f"/v1/research/evidence-synthesis/syntheses/{sid}/meta-analyses",json={"data":{"analysis_key":"bad","method_ref":"m","effect_measure":"rr","pool_estimates_by_core":True}}); assert bad2.status_code==422,bad2.text; c.close()

def test_private_public_boundary(tmp_path):
    c=client(tmp_path); pid=project(c,"private"); sid=synthesis(c,pid); from app.services import cross_study_synthesis as svc
    with c.app.state.database.session_factory() as db:
        try: svc.bundle(db,sid,True); assert False,"expected private-project rejection"
        except ValueError as e: assert "not public" in str(e)
    c.close()
