from __future__ import annotations
import uuid

def _u(prefix): return f"{prefix}-{uuid.uuid4().hex[:8]}"
def _research(client,h,object_type,name,attributes):
    r=client.post('/v1/research-objects',headers=h,json={'object_type':object_type,'name':name,'slug':_u(name.lower().replace(' ','-')),'visibility':'public','attributes':attributes})
    assert r.status_code==200,r.text;return r.json()
def _project(c,h,name='UQ project'):return _research(c,h,'research-project',_u(name),{'research_question':'Quantify uncertainty'})
def _model(c,h,p,name='UQ model'):return _research(c,h,'model',_u(name),{'project_entity_id':p['id'],'model_kind':'simulation','execution_target':'lab','specification':{},'assumptions':[],'equations':[]})
def _version(c,h,m,name='UQ model v1'):return _research(c,h,'model-version',_u(name),{'model_entity_id':m['id'],'version_label':_u('v1'),'specification':{'kind':'test'},'immutable':True})
def _parameter(c,h,m,name='demand',low=0,high=500):return _research(c,h,'parameter',_u(name),{'model_entity_id':m['id'],'name':_u(name),'data_type':'number','unit':'MW','default_value':{'value':100},'bounds':{'min':low,'max':high},'sensitivity_enabled':True})
def _scenario(c,h,p,name='Baseline'):return _research(c,h,'scenario',_u(name),{'project_entity_id':p['id'],'scenario_state':'ready','parameter_values':{},'assumptions':[]})
def _run(c,h,v,s=None,name='External run'):return _research(c,h,'model-run',_u(name),{'model_version_entity_id':v['id'],'scenario_entity_id':s['id'] if s else None,'executor_product':'lab','run_status':'completed','parameter_values':{}})
def _public_key(c,h):
    app=c.post('/v1/developer/applications',headers=h,json={'name':_u('Uncertainty SDK'),'owner_name':'Tester','owner_email':f"uq-{uuid.uuid4().hex[:6]}@example.com",'organization':'Test','website_url':'https://example.com','use_case':'Read public uncertainty metadata.','status':'approved','plan_id':'free','metadata':{},'actor':'admin'})
    assert app.status_code in (200,201),app.text
    issued=c.post(f"/v1/developer/applications/{app.json()['id']}/credentials",headers=h,json={'label':'UQ','scopes':['data:read'],'created_by':'admin'})
    assert issued.status_code in (200,201),issued.text;return issued.json()['api_key']

def _uncertainty(c,h,p,param,visibility='public',key=None):
    r=c.post('/v1/uncertainty-reasoning/uncertainties',headers=h,json={'uncertainty_key':key or _u('demand-uq'),'name':'Demand uncertainty','visibility':visibility,'project_entity_id':p['id'],'subject_entity_id':param['id'],'uncertainty_kind':'aleatory','distribution_family':'uniform','parameters':{'source':'test'},'lower_bound':80,'upper_bound':120,'unit':'MW','confidence_level':0.95,'provenance':{'provided_by':'test'}})
    assert r.status_code==200,r.text;return r.json()
def _study(c,h,p,m,v,visibility='public'):
    r=c.post('/v1/uncertainty-reasoning/sensitivity-studies',headers=h,json={'study_key':_u('study'),'name':'Sensitivity study','visibility':visibility,'project_entity_id':p['id'],'model_entity_id':m['id'],'model_version_entity_id':v['id'],'method':'sobol','execution_product':'lab','configuration':{'sampling_runtime':'external'}})
    assert r.status_code==200,r.text;return r.json()
def _ensemble(c,h,p,m,v,visibility='public'):
    r=c.post('/v1/uncertainty-reasoning/ensembles',headers=h,json={'ensemble_key':_u('ensemble'),'name':'Model ensemble','visibility':visibility,'project_entity_id':p['id'],'model_entity_id':m['id'],'model_version_entity_id':v['id'],'combination_policy':{'weight_semantics':'declared-only'}})
    assert r.status_code==200,r.text;return r.json()

def test_health_migration_and_readiness(client):
    h=client.get('/health').json();assert h['version']=='2.45.0' and h['uncertainty_sensitivity_ensemble_reasoning'] is True
    r=client.get('/v1/uncertainty-reasoning/readiness');assert r.status_code==200,r.text;d=r.json();assert d['migration_0039_applied'] is True
    assert d['sampling_by_core'] is False and d['sensitivity_algorithm_execution_by_core'] is False and d['ensemble_aggregation_by_core'] is False and d['model_execution_by_core'] is False

def test_uncertainty_definition_preserves_bounds_and_provenance(client,write_headers):
    p=_project(client,write_headers);m=_model(client,write_headers,p);param=_parameter(client,write_headers,m);u=_uncertainty(client,write_headers,p,param)
    assert u['lower_bound']==80 and u['upper_bound']==120 and u['distribution_family']=='uniform';assert u['provenance_json']['provided_by']=='test'

def test_uncertainty_invalid_bounds_and_confidence_rejected(client,write_headers):
    p=_project(client,write_headers,'Bounds');m=_model(client,write_headers,p,'Bounds model');param=_parameter(client,write_headers,m,'x')
    bad=client.post('/v1/uncertainty-reasoning/uncertainties',headers=write_headers,json={'uncertainty_key':_u('bad'),'name':'Bad','project_entity_id':p['id'],'subject_entity_id':param['id'],'lower_bound':5,'upper_bound':1});assert bad.status_code==422,bad.text
    bad2=client.post('/v1/uncertainty-reasoning/uncertainties',headers=write_headers,json={'uncertainty_key':_u('bad2'),'name':'Bad2','project_entity_id':p['id'],'subject_entity_id':param['id'],'confidence_level':1.5});assert bad2.status_code==422,bad2.text

def test_sensitivity_external_measures_and_descriptive_ranking(client,write_headers):
    p=_project(client,write_headers,'Sensitivity');m=_model(client,write_headers,p,'Sensitivity model');v=_version(client,write_headers,m);a=_parameter(client,write_headers,m,'a');b=_parameter(client,write_headers,m,'b');ua=_uncertainty(client,write_headers,p,a,key=_u('ua'));study=_study(client,write_headers,p,m,v)
    f1=client.post(f"/v1/uncertainty-reasoning/sensitivity-studies/{study['id']}/factors",headers=write_headers,json={'data':{'factor_key':'a','parameter_entity_id':a['id'],'lower_bound':80,'upper_bound':120,'uncertainty_definition_id':ua['id']}});assert f1.status_code==200,f1.text
    f2=client.post(f"/v1/uncertainty-reasoning/sensitivity-studies/{study['id']}/factors",headers=write_headers,json={'data':{'factor_key':'b','parameter_entity_id':b['id'],'lower_bound':0,'upper_bound':2}});assert f2.status_code==200,f2.text
    for f,val in [(f1.json(),0.2),(f2.json(),-0.8)]:
        r=client.post(f"/v1/uncertainty-reasoning/sensitivity-studies/{study['id']}/measures",headers=write_headers,json={'data':{'factor_id':f['id'],'output_key':'cost','measure_kind':'total-order','measure_value':val,'provenance':{'runtime':'lab'}}});assert r.status_code==200,r.text
    summary=client.get(f"/v1/uncertainty-reasoning/sensitivity-studies/{study['id']}/summary").json();rank=summary['rankings'][0]['factors'];assert rank[0]['factor_key']=='b' and rank[0]['descriptive_rank']==1;assert summary['sensitivity_algorithm_executed_by_core'] is False

def test_sensitivity_rejects_parameter_from_other_model(client,write_headers):
    p=_project(client,write_headers,'Cross');m=_model(client,write_headers,p,'Main');v=_version(client,write_headers,m);study=_study(client,write_headers,p,m,v);other=_model(client,write_headers,p,'Other');foreign=_parameter(client,write_headers,other,'foreign')
    r=client.post(f"/v1/uncertainty-reasoning/sensitivity-studies/{study['id']}/factors",headers=write_headers,json={'data':{'factor_key':'foreign','parameter_entity_id':foreign['id']}});assert r.status_code==422,r.text

def test_ensemble_members_statistics_are_governed_not_aggregated(client,write_headers):
    p=_project(client,write_headers,'Ensemble');m=_model(client,write_headers,p,'Ensemble model');v=_version(client,write_headers,m);s=_scenario(client,write_headers,p);run=_run(client,write_headers,v,s);e=_ensemble(client,write_headers,p,m,v)
    member=client.post(f"/v1/uncertainty-reasoning/ensembles/{e['id']}/members",headers=write_headers,json={'data':{'member_key':'run-1','scenario_entity_id':s['id'],'model_run_entity_id':run['id'],'member_state':'completed','weight':2.5,'provenance':{'source':'external-run'}}});assert member.status_code==200,member.text
    stat=client.post(f"/v1/uncertainty-reasoning/ensembles/{e['id']}/statistics",headers=write_headers,json={'data':{'output_key':'cost','statistic_kind':'mean','statistic_value':42.5,'unit':'USD','provenance':{'computed_by':'lab'}}});assert stat.status_code==200,stat.text
    summary=client.get(f"/v1/uncertainty-reasoning/ensembles/{e['id']}/summary").json();assert summary['member_count']==1 and summary['declared_weight_total']==2.5;assert summary['weights_normalized_by_core'] is False and summary['ensemble_aggregation_by_core'] is False and summary['statistics_are_externally_supplied'] is True

def test_ensemble_rejects_negative_weight_and_bad_quantile(client,write_headers):
    p=_project(client,write_headers,'Reject');m=_model(client,write_headers,p,'Reject model');v=_version(client,write_headers,m);s=_scenario(client,write_headers,p);e=_ensemble(client,write_headers,p,m,v)
    bad=client.post(f"/v1/uncertainty-reasoning/ensembles/{e['id']}/members",headers=write_headers,json={'data':{'member_key':'bad','scenario_entity_id':s['id'],'weight':-1}});assert bad.status_code==422,bad.text
    bad2=client.post(f"/v1/uncertainty-reasoning/ensembles/{e['id']}/statistics",headers=write_headers,json={'data':{'output_key':'x','statistic_kind':'quantile','statistic_value':1,'quantile':1.2}});assert bad2.status_code==422,bad2.text

def test_public_api_hides_private_uncertainty_objects(client,write_headers):
    p=_project(client,write_headers,'Public');m=_model(client,write_headers,p,'Public model');v=_version(client,write_headers,m);a=_parameter(client,write_headers,m,'public-p');b=_parameter(client,write_headers,m,'private-p');pub=_uncertainty(client,write_headers,p,a,'public',_u('pub'));priv=_uncertainty(client,write_headers,p,b,'private',_u('priv'));_study(client,write_headers,p,m,v,'public');_ensemble(client,write_headers,p,m,v,'public')
    key=_public_key(client,write_headers);headers={'Authorization':f'Bearer {key}'}
    ready=client.get('/api/v1/uncertainty-reasoning/readiness',headers=headers);assert ready.status_code==200,ready.text
    listed=client.get('/api/v1/uncertainty-reasoning/uncertainties',headers=headers);assert listed.status_code==200,listed.text;ids={x['id'] for x in listed.json()['data']};assert pub['id'] in ids and priv['id'] not in ids
