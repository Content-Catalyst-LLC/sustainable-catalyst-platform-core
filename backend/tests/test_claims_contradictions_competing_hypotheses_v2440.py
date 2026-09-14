from fastapi.testclient import TestClient
from app.config import Settings
from app.main import create_app
from app.migrations import migration_status
from app.models import Entity


def app_client(tmp_path):
    app=create_app(Settings(database_url=f"sqlite:///{tmp_path/'v2440.db'}",version='2.49.0'))
    return app,TestClient(app)


def seed(app):
    with app.state.database.session_factory() as db:
        db.add(Entity(id='project:reasoning-v2440',entity_type='research-project',slug='reasoning-v2440',name='Reasoning v2440',visibility='public')); db.commit()


def create_case(c):
    inv=c.post('/v1/open-forensics/investigations',json={'data':{'project_entity_id':'project:reasoning-v2440','investigation_key':'case-244','name':'Case 244','visibility':'public'}}); assert inv.status_code==200,inv.text
    iid=inv.json()['id']
    e1=c.post(f'/v1/open-forensics/investigations/{iid}/evidence',json={'data':{'evidence_key':'e1','evidence_kind':'documentary','label':'Evidence 1','content_hash':'a'*64}}); assert e1.status_code==200,e1.text
    e2=c.post(f'/v1/open-forensics/investigations/{iid}/evidence',json={'data':{'evidence_key':'e2','evidence_kind':'record','label':'Evidence 2','content_hash':'b'*64}}); assert e2.status_code==200,e2.text
    return iid,e1.json()['id'],e2.json()['id']


def test_v2440_readiness_boundaries_and_migration(tmp_path):
    app,c=app_client(tmp_path); seed(app)
    h=c.get('/health').json(); assert h['version']=='2.49.0' and h['open_forensics'] is True
    r=c.get('/v1/open-forensics/readiness').json(); assert r['release']=='2.49.0' and r['migration_0048_applied'] is True
    for key in ('structured_claim_registry_by_core','claim_evidence_position_mapping_by_core','explicit_contradiction_registry_by_core','competing_hypothesis_registry_by_core','descriptive_hypothesis_comparison_matrix_by_core','immutable_reasoning_snapshots_by_core'):
        assert r[key] is True,key
    for key in ('automatic_contradiction_detection_by_core','claim_truth_determination_by_core','contradiction_resolution_by_core','hypothesis_probability_assignment_by_core','hypothesis_ranking_by_core','verdict_generation_by_core','automatic_truth_promotion'):
        assert r[key] is False,key
    assert migration_status(app.state.database)['pending']==[]


def test_claims_evidence_contradictions_and_claim_map(tmp_path):
    app,c=app_client(tmp_path); seed(app); iid,e1,e2=create_case(c)
    a=c.post(f'/v1/open-forensics/investigations/{iid}/claims',json={'data':{'claim_key':'claim-a','claim_kind':'temporal','statement':'Event occurred before noon.','asserted_by_ref':'statement:A'}}); assert a.status_code==200,a.text
    b=c.post(f'/v1/open-forensics/investigations/{iid}/claims',json={'data':{'claim_key':'claim-b','claim_kind':'temporal','statement':'Event occurred after noon.','asserted_by_ref':'statement:B'}}); assert b.status_code==200,b.text
    x=c.post(f"/v1/open-forensics/investigations/{iid}/claims/{a.json()['id']}/evidence-assessments",json={'data':{'assessment_key':'a-e1','evidence_item_id':e1,'stance':'supports','diagnosticity':0.8,'rationale':'Timestamp is consistent.'}}); assert x.status_code==200,x.text
    y=c.post(f"/v1/open-forensics/investigations/{iid}/claims/{b.json()['id']}/evidence-assessments",json={'data':{'assessment_key':'b-e2','evidence_item_id':e2,'stance':'supports','diagnosticity':0.7}}); assert y.status_code==200,y.text
    contradiction=c.post(f'/v1/open-forensics/investigations/{iid}/contradictions',json={'data':{'contradiction_key':'time-conflict','left_claim_id':a.json()['id'],'right_claim_id':b.json()['id'],'contradiction_kind':'temporal','basis_evidence_ids':[e1,e2],'rationale':'Both assertions cannot describe the same event time without additional context.'}}); assert contradiction.status_code==200,contradiction.text
    m=c.get(f'/v1/open-forensics/investigations/{iid}/claim-map').json(); assert len(m['claims'])==2 and len(m['evidence_assessments'])==2 and len(m['contradictions'])==1
    assert m['automatic_contradiction_detection'] is False and m['truth_determination'] is False


def test_competing_hypothesis_matrix_is_descriptive_not_ranked(tmp_path):
    app,c=app_client(tmp_path); seed(app); iid,e1,e2=create_case(c)
    focal=c.post(f'/v1/open-forensics/investigations/{iid}/claims',json={'data':{'claim_key':'focal','statement':'Observed discrepancy requires explanation.'}}).json()
    h1=c.post(f'/v1/open-forensics/investigations/{iid}/hypotheses',json={'data':{'hypothesis_key':'h1','label':'Hypothesis 1','statement':'The discrepancy reflects a recording error.','focal_claim_id':focal['id'],'assumptions':['recording process can fail'],'disconfirming_conditions':['independent matching record']}}); assert h1.status_code==200,h1.text
    h2=c.post(f'/v1/open-forensics/investigations/{iid}/hypotheses',json={'data':{'hypothesis_key':'h2','label':'Hypothesis 2','statement':'The discrepancy reflects a real event difference.','focal_claim_id':focal['id']}}); assert h2.status_code==200,h2.text
    rel=c.post(f'/v1/open-forensics/investigations/{iid}/hypothesis-relations',json={'data':{'relation_key':'h1-v-h2','source_hypothesis_id':h1.json()['id'],'target_hypothesis_id':h2.json()['id'],'relation_kind':'competes-with'}}); assert rel.status_code==200,rel.text
    for hid,key,eid,consistency,diag in [(h1.json()['id'],'h1-e1',e1,'supports',0.9),(h1.json()['id'],'h1-e2',e2,'inconsistent',0.6),(h2.json()['id'],'h2-e1',e1,'inconsistent',0.9),(h2.json()['id'],'h2-e2',e2,'supports',0.6)]:
        r=c.post(f'/v1/open-forensics/investigations/{iid}/hypotheses/{hid}/evidence-assessments',json={'data':{'assessment_key':key,'evidence_item_id':eid,'consistency':consistency,'diagnosticity':diag}}); assert r.status_code==200,r.text
    matrix=c.get(f'/v1/open-forensics/investigations/{iid}/hypothesis-matrix').json(); assert len(matrix['hypotheses'])==2 and len(matrix['rows'])==2 and len(matrix['relations'])==1
    assert matrix['descriptive_only'] is True and matrix['ranked'] is False and matrix['probabilities_assigned'] is False and matrix['verdict'] is None
    snap1=c.post(f'/v1/open-forensics/investigations/{iid}/reasoning-snapshots',json={'data':{'created_by':'test'}}); assert snap1.status_code==200 and snap1.json()['revision']==1 and len(snap1.json()['content_hash'])==64
    snap2=c.post(f'/v1/open-forensics/investigations/{iid}/reasoning-snapshots',json={'data':{'created_by':'test'}}); assert snap2.status_code==200 and snap2.json()['revision']==2 and snap2.json()['previous_snapshot_hash']==snap1.json()['content_hash']


def test_v2440_rejects_automatic_verdict_probability_rank_and_invalid_links(tmp_path):
    app,c=app_client(tmp_path); seed(app); iid,e1,_=create_case(c)
    bad=c.post(f'/v1/open-forensics/investigations/{iid}/claims',json={'data':{'claim_key':'bad','statement':'Bad','truth_value':True}}); assert bad.status_code==422 and 'verdict/ranking/probability' in bad.text
    claim=c.post(f'/v1/open-forensics/investigations/{iid}/claims',json={'data':{'claim_key':'c','statement':'Claim'}}).json()
    bad_assessment=c.post(f"/v1/open-forensics/investigations/{iid}/claims/{claim['id']}/evidence-assessments",json={'data':{'assessment_key':'bad','evidence_item_id':e1,'stance':'supports','probability':0.95}}); assert bad_assessment.status_code==422
    h=c.post(f'/v1/open-forensics/investigations/{iid}/hypotheses',json={'data':{'hypothesis_key':'h','label':'H','statement':'Hypothesis'}}).json()
    bad_h=c.post(f"/v1/open-forensics/investigations/{iid}/hypotheses/{h['id']}/evidence-assessments",json={'data':{'assessment_key':'bad-h','evidence_item_id':e1,'consistency':'supports','rank':1}}); assert bad_h.status_code==422
    same=c.post(f'/v1/open-forensics/investigations/{iid}/hypothesis-relations',json={'data':{'relation_key':'same','source_hypothesis_id':h['id'],'target_hypothesis_id':h['id'],'relation_kind':'competes-with'}}); assert same.status_code==422
