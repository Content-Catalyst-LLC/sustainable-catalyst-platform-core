from fastapi.testclient import TestClient
from app.config import Settings
from app.main import create_app
from app.migrations import migration_status
from app.models import Entity


def app_client(tmp_path):
    app=create_app(Settings(database_url=f"sqlite:///{tmp_path/'v2490.db'}",version='2.52.0'))
    return app,TestClient(app)


def seed(app):
    with app.state.database.session_factory() as db:
        db.add(Entity(id='project:doc-v2490',entity_type='research-project',slug='doc-v2490',name='Documentary Forensics',visibility='public')); db.commit()


def case(c):
    inv=c.post('/v1/open-forensics/investigations',json={'data':{'project_entity_id':'project:doc-v2490','investigation_key':'doc-case','name':'Documentary Case','visibility':'public'}}); assert inv.status_code==200,inv.text
    iid=inv.json()['id']
    ev=c.post(f'/v1/open-forensics/investigations/{iid}/evidence',json={'data':{'evidence_key':'transcript-source','evidence_kind':'documentary','label':'Interview transcript','content_hash':'a'*64}}); assert ev.status_code==200,ev.text
    claim=c.post(f'/v1/open-forensics/investigations/{iid}/claims',json={'data':{'claim_key':'claim-1','claim_kind':'factual','statement':'The meeting occurred before noon.'}}); assert claim.status_code==200,claim.text
    return iid,ev.json()['id'],claim.json()['id']


def test_v2490_readiness_boundaries_and_migration(tmp_path):
    app,c=app_client(tmp_path); seed(app)
    h=c.get('/health').json(); assert h['version']=='2.52.0' and h['forensic_testimony_statements_documentary_evidence'] is True
    r=c.get('/v1/open-forensics/readiness').json(); assert r['release']=='2.52.0' and r['migration_0053_applied'] is True
    for key in ('statement_testimony_registry_by_core','documentary_evidence_registry_by_core','speaker_author_reference_binding_by_core','source_context_preservation_by_core','statement_claim_binding_by_core','explicit_corroboration_contradiction_relations_by_core','temporal_consistency_recording_by_core','immutable_documentary_snapshots_by_core'): assert r[key] is True,key
    for key in ('automatic_claim_extraction_by_core','automatic_speaker_identity_resolution_by_core','automatic_authorship_attribution_by_core','automatic_corroboration_detection_by_core','credibility_scoring_by_core','automatic_truth_promotion'): assert r[key] is False,key
    assert migration_status(app.state.database)['pending']==[]


def test_statement_source_context_claim_binding_and_relations(tmp_path):
    app,c=app_client(tmp_path); seed(app); iid,eid,claim_id=case(c)
    s1=c.post(f'/v1/open-forensics/investigations/{iid}/statements',json={'data':{'statement_key':'s1','statement_kind':'testimony','label':'Witness statement A','statement_text':'The meeting began at 10:30.','speaker_ref':'external://person/witness-a','speaker_label':'Witness A','evidence_item_id':eid,'stated_at':'2026-09-13T10:45:00Z'}}); assert s1.status_code==200,s1.text
    sid1=s1.json()['id']
    ctx=c.post(f'/v1/open-forensics/investigations/{iid}/statements/{sid1}/source-contexts',json={'data':{'evidence_item_id':eid,'source_ref':'external://transcript/1','locator':{'page':3,'paragraph':2},'surrounding_context':'Question and response preserved with adjacent transcript context.','content_hash':'b'*64}}); assert ctx.status_code==200,ctx.text
    bind=c.post(f'/v1/open-forensics/investigations/{iid}/statements/{sid1}/claim-bindings',json={'data':{'claim_id':claim_id,'binding_kind':'supports','rationale':'Explicitly reports a pre-noon start time.','evidence_item_id':eid}}); assert bind.status_code==200,bind.text
    s2=c.post(f'/v1/open-forensics/investigations/{iid}/statements',json={'data':{'statement_key':'s2','statement_kind':'interview','label':'Witness statement B','statement_text':'I arrived shortly after ten.','speaker_ref':'external://person/witness-b','speaker_label':'Witness B','evidence_item_id':eid}}); assert s2.status_code==200,s2.text
    rel=c.post(f'/v1/open-forensics/investigations/{iid}/statement-relations',json={'data':{'source_statement_id':sid1,'target_statement_id':s2.json()['id'],'relation_kind':'corroborates','rationale':'Both statements place activity in the same morning window.','evidence_basis_ids':[eid]}}); assert rel.status_code==200,rel.text
    bundle=c.get(f'/v1/open-forensics/investigations/{iid}/documentary-evidence').json(); assert len(bundle['statements'])==2 and len(bundle['source_contexts'])==1 and len(bundle['statement_claim_bindings'])==1 and len(bundle['statement_relations'])==1; assert bundle['descriptive_only'] is True and bundle['credibility_scoring_by_core'] is False


def test_document_assertion_temporal_consistency_and_snapshot(tmp_path):
    app,c=app_client(tmp_path); seed(app); iid,eid,claim_id=case(c)
    doc=c.post(f'/v1/open-forensics/investigations/{iid}/documents',json={'data':{'document_key':'memo-1','document_kind':'memo','title':'Operations memo','evidence_item_id':eid,'author_ref':'external://person/author-1','author_label':'Named author as recorded','source_ref':'external://document/memo-1','source_context':{'collection':'case-file-a'},'content_hash':'c'*64}}); assert doc.status_code==200,doc.text
    did=doc.json()['id']
    assertion=c.post(f'/v1/open-forensics/investigations/{iid}/documents/{did}/assertions',json={'data':{'assertion_key':'a1','assertion_text':'The meeting started at 10:30.','locator':{'page':1,'section':'Schedule'},'claim_id':claim_id,'evidence_item_id':eid}}); assert assertion.status_code==200,assertion.text
    st=c.post(f'/v1/open-forensics/investigations/{iid}/statements',json={'data':{'statement_key':'s1','statement_kind':'statement','label':'Statement','statement_text':'The meeting began in the morning.','evidence_item_id':eid}}); assert st.status_code==200,st.text
    tc=c.post(f'/v1/open-forensics/investigations/{iid}/temporal-consistency',json={'data':{'subject_a_kind':'statement','subject_a_id':st.json()['id'],'subject_b_kind':'document-assertion','subject_b_id':assertion.json()['id'],'assessment':'consistent','rationale':'Both records indicate a morning start.','evidence_basis_ids':[eid]}}); assert tc.status_code==200,tc.text
    snap=c.post(f'/v1/open-forensics/investigations/{iid}/documentary-snapshots',json={'data':{'created_by':'test'}}); assert snap.status_code==200,snap.text; assert snap.json()['revision']==1 and len(snap.json()['content_hash'])==64
    bundle=c.get(f'/v1/open-forensics/investigations/{iid}/documentary-evidence').json(); assert len(bundle['documents'])==1 and len(bundle['document_assertions'])==1 and len(bundle['temporal_consistency_assessments'])==1 and len(bundle['snapshots'])==1


def test_documentary_non_determinative_guards(tmp_path):
    app,c=app_client(tmp_path); seed(app); iid,eid,_=case(c)
    bad=c.post(f'/v1/open-forensics/investigations/{iid}/statements',json={'data':{'statement_key':'bad','statement_kind':'testimony','label':'Bad','statement_text':'Text','credibility_score':0.99}}); assert bad.status_code==422 and 'does not verify identity' in bad.text
    bad2=c.post(f'/v1/open-forensics/investigations/{iid}/documents',json={'data':{'document_key':'bad-doc','document_kind':'document','title':'Bad','verified_author':True}}); assert bad2.status_code==422
