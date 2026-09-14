from fastapi.testclient import TestClient
from app.config import Settings
from app.main import create_app
from app.migrations import migration_status
from app.models import Entity, SourceSnapshot, EvidenceRecord


def app_client(tmp_path):
    app=create_app(Settings(database_url=f"sqlite:///{tmp_path/'v2420.db'}",version="2.52.0"))
    return app,TestClient(app)


def seed(app):
    with app.state.database.session_factory() as db:
        db.add(Entity(id='project:forensics',entity_type='research-project',slug='forensics',name='Open Forensics',visibility='public'))
        db.add(Entity(id='source:doc',entity_type='source',slug='doc',name='Document Source',visibility='public'))
        snap=SourceSnapshot(id='sc:snapshot:forensics',source_entity_id='source:doc',canonical_url='https://example.org/doc',title='Document',content_hash='a'*64)
        ev=EvidenceRecord(id='sc:evidence:forensics',evidence_type='documentary',source_entity_id='source:doc',source_snapshot_id=snap.id,statement='Documentary evidence')
        db.add(snap); db.add(ev); db.commit()


def create_inv(c):
    r=c.post('/v1/open-forensics/investigations',json={'data':{'project_entity_id':'project:forensics','investigation_key':'case-1','name':'Case 1','visibility':'public','research_question':'What does the evidence establish?'}})
    assert r.status_code==200,r.text; return r.json()['id']


def test_readiness_health_and_migration_0046(tmp_path):
    app,c=app_client(tmp_path); seed(app)
    h=c.get('/health').json(); assert h['version']=='2.52.0' and h['open_forensics'] is True
    r=c.get('/v1/open-forensics/readiness').json(); assert r['release']=='2.52.0' and r['migration_0046_applied'] is True
    assert r['evidence_provenance_capture_by_core'] is True and r['content_hash_recording_by_core'] is True
    assert r['chain_of_custody_by_core'] is True
    for key in ('authenticity_determination_by_core','identity_attribution_by_core','causal_conclusion_by_core','legal_conclusion_by_core','automatic_truth_promotion'):
        assert r[key] is False
    assert migration_status(app.state.database)['pending']==[]


def test_forensic_objects_evidence_provenance_graph_snapshot(tmp_path):
    app,c=app_client(tmp_path); seed(app); iid=create_inv(c)
    o1=c.post(f'/v1/open-forensics/investigations/{iid}/objects',json={'data':{'object_key':'document','object_kind':'document','label':'Original document','bound_entity_id':'source:doc','source_product':'core','source_ref':'source:doc'}}); assert o1.status_code==200,o1.text
    o2=c.post(f'/v1/open-forensics/investigations/{iid}/objects',json={'data':{'object_key':'extract','object_kind':'digital-object','label':'Extracted record','source_product':'research-librarian','source_ref':'sc://research-librarian/result/1'}}); assert o2.status_code==200,o2.text
    e=c.post(f'/v1/open-forensics/investigations/{iid}/evidence',json={'data':{'evidence_key':'e1','evidence_kind':'documentary','label':'Document evidence','forensic_object_id':o1.json()['id'],'content_hash':'b'*64,'source_snapshot_id':'sc:snapshot:forensics','evidence_record_id':'sc:evidence:forensics'}}); assert e.status_code==200,e.text
    b=c.post(f"/v1/open-forensics/investigations/{iid}/evidence/{e.json()['id']}/source-bindings",json={'data':{'binding_key':'snapshot','source_kind':'core-source-snapshot','source_ref':'sc:snapshot:forensics','locator':'page 1','content_hash':'a'*64}}); assert b.status_code==200,b.text
    a=c.post(f'/v1/open-forensics/investigations/{iid}/provenance-activities',json={'data':{'activity_kind':'extracted','evidence_item_id':e.json()['id'],'actor_ref':'research-librarian','tool_ref':'extractor:v1','inputs':['sc:snapshot:forensics'],'outputs':[o2.json()['id']]}}); assert a.status_code==200,a.text
    rel=c.post(f'/v1/open-forensics/investigations/{iid}/relations',json={'data':{'relation_key':'extract-from-document','source_object_id':o2.json()['id'],'target_object_id':o1.json()['id'],'relation_kind':'extracted-from','assertion_state':'documented','confidence':0.95,'basis':{'evidence_item_id':e.json()['id']}}}); assert rel.status_code==200,rel.text
    graph=c.get(f'/v1/open-forensics/investigations/{iid}/provenance-graph').json(); assert graph['contract']=='sc.open-forensics.provenance-graph.v1' and len(graph['nodes'])>=3 and len(graph['edges'])>=3
    snap=c.post(f'/v1/open-forensics/investigations/{iid}/snapshots',json={'data':{'created_by':'test'}}).json(); assert snap['revision']==1 and len(snap['content_hash'])==64
    portable=c.get(f'/v1/open-forensics/investigations/{iid}/portable-package').json(); assert portable['chain_of_custody_recorded'] is True and portable['not_chain_of_custody'] is False and portable['not_authenticity_determination'] is True and len(portable['content_hash'])==64


def test_v242_rejects_custody_attribution_and_bad_hash_claims(tmp_path):
    app,c=app_client(tmp_path); seed(app); iid=create_inv(c)
    o1=c.post(f'/v1/open-forensics/investigations/{iid}/objects',json={'data':{'object_key':'a','object_kind':'artifact','label':'A'}}).json()
    o2=c.post(f'/v1/open-forensics/investigations/{iid}/objects',json={'data':{'object_key':'b','object_kind':'artifact','label':'B'}}).json()
    bad_hash=c.post(f'/v1/open-forensics/investigations/{iid}/evidence',json={'data':{'evidence_key':'bad','evidence_kind':'digital','label':'Bad','content_hash':'not-a-sha'}}); assert bad_hash.status_code==422
    custody=c.post(f'/v1/open-forensics/investigations/{iid}/provenance-activities',json={'data':{'activity_kind':'custody-transfer','actor_ref':'person'}}); assert custody.status_code==422 and 'dedicated chain-of-custody API' in custody.text
    attribution=c.post(f'/v1/open-forensics/investigations/{iid}/relations',json={'data':{'relation_key':'bad-rel','source_object_id':o1['id'],'target_object_id':o2['id'],'relation_kind':'authored-by'}}); assert attribution.status_code==422
