from fastapi.testclient import TestClient
from app.config import Settings
from app.main import create_app
from app.migrations import migration_status
from app.models import Entity

def app_client(tmp_path):
    app=create_app(Settings(database_url=f"sqlite:///{tmp_path/'v2470.db'}",version='2.50.0'))
    return app,TestClient(app)

def seed(app):
    with app.state.database.session_factory() as db:
        db.add(Entity(id='project:media-v2470',entity_type='research-project',slug='media-v2470',name='Media v2470',visibility='public')); db.commit()

def case(c):
    inv=c.post('/v1/open-forensics/investigations',json={'data':{'project_entity_id':'project:media-v2470','investigation_key':'media-case','name':'Media Case','visibility':'public'}}); assert inv.status_code==200,inv.text; iid=inv.json()['id']
    ev1=c.post(f'/v1/open-forensics/investigations/{iid}/evidence',json={'data':{'evidence_key':'original-file','evidence_kind':'media','label':'Original file','content_hash':'a'*64,'mime_type':'image/jpeg'}})
    ev2=c.post(f'/v1/open-forensics/investigations/{iid}/evidence',json={'data':{'evidence_key':'derived-file','evidence_kind':'media','label':'Derived file','content_hash':'b'*64,'mime_type':'image/jpeg'}})
    assert ev1.status_code==200 and ev2.status_code==200
    return iid,ev1.json()['id'],ev2.json()['id']

def test_v2470_readiness_boundaries_and_migration(tmp_path):
    app,c=app_client(tmp_path); seed(app)
    h=c.get('/health').json(); assert h['version']=='2.50.0' and h['forensic_media_artifact_derivative_provenance'] is True
    r=c.get('/v1/open-forensics/readiness').json(); assert r['release']=='2.50.0' and r['migration_0051_applied'] is True
    for key in ('media_artifact_registry_by_core','declared_derivative_lineage_by_core','media_metadata_preservation_by_core','cryptographic_fingerprint_recording_by_core','perceptual_fingerprint_recording_by_core','frame_segment_reference_registry_by_core','provenance_aware_media_comparisons_by_core','immutable_media_provenance_snapshots_by_core'): assert r[key] is True,key
    for key in ('media_decoding_by_core','perceptual_fingerprint_computation_by_core','media_similarity_execution_by_core','derivative_detection_by_core','authenticity_determination_from_media_by_core','manipulation_intent_determination_by_core','media_authorship_attribution_by_core','automatic_truth_promotion'): assert r[key] is False,key
    assert migration_status(app.state.database)['pending']==[]

def test_media_artifacts_metadata_fingerprints_segments_and_lineage(tmp_path):
    app,c=app_client(tmp_path); seed(app); iid,e1,e2=case(c)
    orig=c.post(f'/v1/open-forensics/investigations/{iid}/media-artifacts',json={'data':{'artifact_key':'original','label':'Original image','media_kind':'image','provenance_role':'original','evidence_item_id':e1,'content_hash':'a'*64,'mime_type':'image/jpeg','width':4000,'height':3000}})
    der=c.post(f'/v1/open-forensics/investigations/{iid}/media-artifacts',json={'data':{'artifact_key':'crop','label':'Cropped image','media_kind':'image','provenance_role':'derivative','evidence_item_id':e2,'content_hash':'b'*64,'mime_type':'image/jpeg','width':1200,'height':800}})
    assert orig.status_code==200,orig.text; assert der.status_code==200,der.text; oid,did=orig.json()['id'],der.json()['id']
    md=c.post(f'/v1/open-forensics/investigations/{iid}/media-artifacts/{oid}/metadata',json={'data':{'record_key':'exif-1','namespace':'exif','metadata':{'Make':'Camera Co','DateTimeOriginal':'2026:09:13 10:00:00'},'extraction_method':'external','extraction_tool_ref':'tool:exif-reader','preserved':True}}); assert md.status_code==200,md.text
    fp=c.post(f'/v1/open-forensics/investigations/{iid}/media-artifacts/{oid}/fingerprints',json={'data':{'fingerprint_key':'sha256','fingerprint_kind':'cryptographic','algorithm':'sha256','fingerprint_value':'a'*64,'producer_ref':'evidence-ledger'}}); assert fp.status_code==200,fp.text
    pfp=c.post(f'/v1/open-forensics/investigations/{iid}/media-artifacts/{oid}/fingerprints',json={'data':{'fingerprint_key':'phash','fingerprint_kind':'perceptual-image','algorithm':'pHash','algorithm_version':'1','fingerprint_value':'f0f0f0f0','producer_ref':'external:perceptual-tool'}}); assert pfp.status_code==200,pfp.text
    seg=c.post(f'/v1/open-forensics/investigations/{iid}/media-artifacts/{oid}/segments',json={'data':{'segment_key':'frame-region','segment_kind':'region','label':'Region of interest','locator':{'description':'upper-left'},'region':{'x':10,'y':20,'width':100,'height':80},'evidence_item_id':e1}}); assert seg.status_code==200,seg.text
    rel=c.post(f'/v1/open-forensics/investigations/{iid}/media-derivations',json={'data':{'derivation_key':'original-to-crop','parent_artifact_id':oid,'child_artifact_id':did,'transformation_kind':'crop','tool_ref':'external:image-editor','parameters':{'rectangle':[10,20,1200,800]}}}); assert rel.status_code==200,rel.text
    bundle=c.get(f'/v1/open-forensics/investigations/{iid}/media-provenance').json(); assert len(bundle['artifacts'])==2 and len(bundle['derivations'])==1 and len(bundle['metadata_records'])==1 and len(bundle['fingerprints'])==2 and len(bundle['segments'])==1; assert bundle['derivative_relations_are_declared_provenance_not_automated_detection'] is True
    graph=c.get(f'/v1/open-forensics/investigations/{iid}/media-lineage-graph').json(); assert len(graph['nodes'])==2 and len(graph['edges'])==1 and graph['derivative_detection_by_core'] is False and graph['authenticity_determination_by_core'] is False

def test_media_comparisons_snapshot_and_non_determination_guards(tmp_path):
    app,c=app_client(tmp_path); seed(app); iid,e1,e2=case(c)
    a1=c.post(f'/v1/open-forensics/investigations/{iid}/media-artifacts',json={'data':{'artifact_key':'a1','label':'Image A','media_kind':'image','evidence_item_id':e1,'content_hash':'a'*64}}).json(); a2=c.post(f'/v1/open-forensics/investigations/{iid}/media-artifacts',json={'data':{'artifact_key':'a2','label':'Image B','media_kind':'image','evidence_item_id':e2,'content_hash':'b'*64}}).json()
    comp=c.post(f'/v1/open-forensics/investigations/{iid}/media-comparisons',json={'data':{'comparison_key':'cmp','comparison_kind':'perceptual-similarity','left_artifact_id':a1['id'],'right_artifact_id':a2['id'],'method_ref':'external:phash-tool','findings':{'observation':'fingerprints share selected visual features'},'metrics':{'distance':12},'basis_evidence_ids':[e1,e2]}}); assert comp.status_code==200,comp.text
    cb=c.get(f'/v1/open-forensics/investigations/{iid}/media-comparison-bundle').json(); assert cb['descriptive_only'] is True and cb['media_similarity_execution_by_core'] is False and cb['authenticity_determination_from_media_by_core'] is False and cb['media_authorship_attribution_by_core'] is False
    s1=c.post(f'/v1/open-forensics/investigations/{iid}/media-provenance-snapshots',json={'data':{'created_by':'test'}}); assert s1.status_code==200 and s1.json()['revision']==1 and len(s1.json()['content_hash'])==64
    s2=c.post(f'/v1/open-forensics/investigations/{iid}/media-provenance-snapshots',json={'data':{'created_by':'test'}}); assert s2.status_code==200 and s2.json()['revision']==2 and s2.json()['content_hash']==s1.json()['content_hash'] and s2.json()['previous_snapshot_hash']==s1.json()['content_hash']
    bad=c.post(f'/v1/open-forensics/investigations/{iid}/media-comparisons',json={'data':{'comparison_key':'bad','comparison_kind':'external-analysis','left_artifact_id':a1['id'],'right_artifact_id':a2['id'],'verdict':'fake'}}); assert bad.status_code==422 and 'does not determine authenticity' in bad.text
    bad2=c.post(f'/v1/open-forensics/investigations/{iid}/media-artifacts',json={'data':{'artifact_key':'bad-artifact','label':'Bad','media_kind':'image','source_ref':'external:x','authentic':True}}); assert bad2.status_code==422
