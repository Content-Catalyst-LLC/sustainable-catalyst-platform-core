#!/usr/bin/env python3
from app.config import Settings
from app.main import create_app
from app.models import Entity
from app.services import open_forensics as svc
from app.migrations import migration_status

app=create_app(Settings.from_env())
with app.state.database.session_factory() as db:
    project=db.get(Entity,'project:v249-smoke')
    if project is None:
        db.add(Entity(id='project:v249-smoke',entity_type='research-project',slug='v249-smoke',name='v249 documentary smoke',visibility='private')); db.commit()
    inv=svc.create_investigation(db,{'project_entity_id':'project:v249-smoke','investigation_key':'v249-smoke','name':'v249 documentary smoke'})
    iid=inv['id']
    evidence=svc.add_evidence(db,iid,{'evidence_key':'transcript','evidence_kind':'documentary','label':'Transcript','content_hash':'a'*64})
    claim=svc.add_claim(db,iid,{'claim_key':'c1','claim_kind':'factual','statement':'A meeting occurred in the morning.'})
    st=svc.add_statement(db,iid,{'statement_key':'s1','statement_kind':'testimony','label':'Statement','statement_text':'The meeting started at 10:30.','speaker_ref':'external://speaker/1','evidence_item_id':evidence['id']})
    svc.add_statement_source_context(db,iid,st['id'],{'evidence_item_id':evidence['id'],'source_ref':'external://transcript/1','locator':{'page':1,'paragraph':2},'content_hash':'b'*64})
    svc.bind_statement_claim(db,iid,st['id'],{'claim_id':claim['id'],'binding_kind':'supports','evidence_item_id':evidence['id']})
    doc=svc.add_document(db,iid,{'document_key':'d1','document_kind':'memo','title':'Memo','evidence_item_id':evidence['id'],'source_ref':'external://memo/1','content_hash':'c'*64})
    assertion=svc.add_document_assertion(db,iid,doc['id'],{'assertion_key':'a1','assertion_text':'Meeting scheduled at 10:30.','locator':{'page':1},'claim_id':claim['id'],'evidence_item_id':evidence['id']})
    svc.add_temporal_consistency_assessment(db,iid,{'subject_a_kind':'statement','subject_a_id':st['id'],'subject_b_kind':'document-assertion','subject_b_id':assertion['id'],'assessment':'consistent','evidence_basis_ids':[evidence['id']]})
    snap=svc.create_documentary_snapshot(db,iid,{'created_by':'smoke'})
    bundle=svc.documentary_evidence_bundle(db,iid)
    assert len(bundle['statements'])==1 and len(bundle['documents'])==1 and len(bundle['document_assertions'])==1
    assert len(bundle['source_contexts'])==1 and len(bundle['statement_claim_bindings'])==1 and len(bundle['temporal_consistency_assessments'])==1
    assert snap['revision']==1 and len(snap['content_hash'])==64
    assert bundle['credibility_scoring_by_core'] is False and bundle['identity_verification_by_core'] is False
    status=migration_status(app.state.database); assert status['pending']==[] and status['applied'][-1]=='0053'
print('PASS - Platform Core v2.49.0 Testimony, Statements & Documentary Evidence runtime validation')
