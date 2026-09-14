from fastapi.testclient import TestClient
from app.config import Settings
from app.main import create_app
from app.migrations import migration_status
from app.models import Entity


def app_client(tmp_path):
    app=create_app(Settings(database_url=f"sqlite:///{tmp_path/'v2480.db'}",version='2.53.0'))
    return app,TestClient(app)


def seed(app):
    with app.state.database.session_factory() as db:
        db.add(Entity(id='project:quant-v2480',entity_type='research-project',slug='quant-v2480',name='Quantitative Forensics',visibility='public')); db.commit()


def case(c):
    inv=c.post('/v1/open-forensics/investigations',json={'data':{'project_entity_id':'project:quant-v2480','investigation_key':'quant-case','name':'Quantitative Case','visibility':'public'}}); assert inv.status_code==200,inv.text
    iid=inv.json()['id']
    ev=c.post(f'/v1/open-forensics/investigations/{iid}/evidence',json={'data':{'evidence_key':'measurement-source','evidence_kind':'measurement','label':'Measured distance','content_hash':'a'*64}}); assert ev.status_code==200,ev.text
    return iid,ev.json()['id']


def test_v2480_readiness_boundaries_and_migration(tmp_path):
    app,c=app_client(tmp_path); seed(app)
    h=c.get('/health').json(); assert h['version']=='2.53.0' and h['forensic_quantitative_reconstruction_reproduction_handoffs'] is True
    r=c.get('/v1/open-forensics/readiness').json(); assert r['release']=='2.53.0' and r['migration_0052_applied'] is True
    for key in ('quantitative_reconstruction_registry_by_core','measurement_and_uncertainty_capture_by_core','assumption_parameter_registry_by_core','scenario_manifest_registry_by_core','workbench_lab_handoff_contracts_by_core','external_result_binding_by_core','reproducible_quantitative_packages_by_core'): assert r[key] is True,key
    for key in ('quantitative_model_execution_by_core','numerical_solution_by_core','statistical_inference_execution_by_core','uncertainty_propagation_execution_by_core','sensitivity_execution_by_core','parameter_optimization_by_core','automatic_truth_promotion'): assert r[key] is False,key
    assert migration_status(app.state.database)['pending']==[]


def test_quantitative_reconstruction_inputs_scenario_and_handoff(tmp_path):
    app,c=app_client(tmp_path); seed(app); iid,eid=case(c)
    rec=c.post(f'/v1/open-forensics/investigations/{iid}/quantitative-reconstructions',json={'data':{'reconstruction_key':'trajectory-energy','label':'Trajectory energy reconstruction','reconstruction_kind':'physical','question':'What energy range is consistent with the recorded measurements?','model_ref':'sc://workbench/model/energy-balance','model_version_ref':'v3','preferred_runtime':'workbench','unit_system':'SI','basis_evidence_ids':[eid]}}); assert rec.status_code==200,rec.text; rid=rec.json()['id']
    m=c.post(f'/v1/open-forensics/investigations/{iid}/quantitative-reconstructions/{rid}/measurements',json={'data':{'measurement_key':'distance','label':'Distance','value':{'value':125.0},'unit':'m','uncertainty':{'kind':'interval','lower':123.5,'upper':126.5},'evidence_item_id':eid}}); assert m.status_code==200,m.text
    a=c.post(f'/v1/open-forensics/investigations/{iid}/quantitative-reconstructions/{rid}/assumptions',json={'data':{'assumption_key':'constant-mass','statement':'Mass is treated as constant during the modeled interval.','assumption_kind':'model','basis_evidence_ids':[eid]}}); assert a.status_code==200,a.text
    p=c.post(f'/v1/open-forensics/investigations/{iid}/quantitative-reconstructions/{rid}/parameters',json={'data':{'parameter_key':'mass','label':'Mass','symbol':'m','value':{'value':80.0},'unit':'kg','bounds':{'lower':78.0,'upper':82.0},'uncertainty':{'kind':'interval'},'parameter_role':'observed','evidence_item_id':eid}}); assert p.status_code==200,p.text
    sc=c.post(f'/v1/open-forensics/investigations/{iid}/quantitative-reconstructions/{rid}/scenarios',json={'data':{'scenario_key':'baseline','label':'Baseline','assumption_ids':[a.json()['id']],'measurement_ids':[m.json()['id']],'parameter_overrides':{},'requested_analyses':['energy-balance','uncertainty-propagation'],'uncertainty_plan':{'method':'external-monte-carlo','samples':10000}}}); assert sc.status_code==200,sc.text
    hc=c.get(f'/v1/open-forensics/investigations/{iid}/quantitative-reconstructions/{rid}/handoff/workbench'); assert hc.status_code==200,hc.text; assert hc.json()['target_product']=='workbench' and hc.json()['execute_by_core'] is False and hc.json()['specialist_runtime_required'] is True
    ho=c.post(f'/v1/open-forensics/investigations/{iid}/quantitative-reconstructions/{rid}/handoffs',json={'data':{'handoff_key':'wb-run-1','target_product':'workbench','scenario_id':sc.json()['id'],'execution_request':{'operation':'run-reconstruction'}}}); assert ho.status_code==200,ho.text
    bundle=c.get(f'/v1/open-forensics/investigations/{iid}/quantitative-reconstructions').json(); assert len(bundle['reconstructions'])==1 and len(bundle['measurements'])==1 and len(bundle['assumptions'])==1 and len(bundle['parameters'])==1 and len(bundle['scenarios'])==1 and len(bundle['handoffs'])==1; assert bundle['execution_by_core'] is False


def test_external_results_and_reproduction_package(tmp_path):
    app,c=app_client(tmp_path); seed(app); iid,eid=case(c)
    rec=c.post(f'/v1/open-forensics/investigations/{iid}/quantitative-reconstructions',json={'data':{'reconstruction_key':'r','label':'R','reconstruction_kind':'engineering','preferred_runtime':'lab','basis_evidence_ids':[eid]}}).json(); rid=rec['id']
    ho=c.post(f'/v1/open-forensics/investigations/{iid}/quantitative-reconstructions/{rid}/handoffs',json={'data':{'handoff_key':'lab-run','target_product':'lab','execution_request':{'operation':'simulate'}}}); assert ho.status_code==200,ho.text; hid=ho.json()['id']
    res=c.post(f'/v1/open-forensics/investigations/{iid}/quantitative-handoffs/{hid}/results',json={'data':{'result_key':'result-1','result_kind':'simulation-output','external_result_ref':'sc://lab/run/123/result/1','output_manifest':{'files':['result.json']},'metrics':{'reported_peak':42.1},'content_hash':'b'*64,'evidence_item_id':eid}}); assert res.status_code==200,res.text
    pkg=c.post(f'/v1/open-forensics/investigations/{iid}/quantitative-reconstructions/{rid}/reproduction-packages',json={'data':{'package_key':'repro-1','created_by':'test'}}); assert pkg.status_code==200,pkg.text; body=pkg.json(); assert body['revision']==1 and len(body['manifest_hash'])==64 and body['manifest_json']['specialist_execution_required'] is True and body['manifest_json']['quantitative_model_execution_by_core'] is False
    bundle=c.get(f'/v1/open-forensics/investigations/{iid}/quantitative-reconstructions').json(); assert len(bundle['result_bindings'])==1 and len(bundle['reproduction_packages'])==1


def test_quantitative_non_execution_and_non_verdict_guards(tmp_path):
    app,c=app_client(tmp_path); seed(app); iid,eid=case(c)
    bad=c.post(f'/v1/open-forensics/investigations/{iid}/quantitative-reconstructions',json={'data':{'reconstruction_key':'bad','label':'Bad','reconstruction_kind':'physical','execute_by_core':True}}); assert bad.status_code==422 and 'does not execute models' in bad.text
    rec=c.post(f'/v1/open-forensics/investigations/{iid}/quantitative-reconstructions',json={'data':{'reconstruction_key':'good','label':'Good','reconstruction_kind':'physical','basis_evidence_ids':[eid]}}).json(); rid=rec['id']
    bad2=c.post(f'/v1/open-forensics/investigations/{iid}/quantitative-reconstructions/{rid}/parameters',json={'data':{'parameter_key':'p','label':'P','value':{'value':1},'probability':0.99}}); assert bad2.status_code==422
    bad3=c.post(f'/v1/open-forensics/investigations/{iid}/quantitative-reconstructions/{rid}/handoffs',json={'data':{'handoff_key':'x','target_product':'core'}}); assert bad3.status_code==422
