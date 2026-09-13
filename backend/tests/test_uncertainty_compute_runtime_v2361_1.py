from __future__ import annotations

def test_health_migration_and_readiness(client):
    h=client.get('/health').json(); assert h['version']=='2.36.1.1' and h['uncertainty_compute_runtime_integration'] is True
    d=client.get('/v1/uncertainty-compute/readiness').json(); assert d['migration_0040_applied'] is True
    assert d['monte_carlo_sampling'] and d['sobol_index_analysis'] and d['ensemble_weight_normalization']
    assert d['model_execution_by_core'] is False and d['automatic_truth_promotion'] is False

def test_deterministic_monte_carlo_and_lhs(client,write_headers):
    factors=[{'key':'x','distribution':'uniform','lower_bound':0,'upper_bound':1},{'key':'y','distribution':'triangular','lower_bound':0,'upper_bound':10,'parameters':{'mode':4}}]
    p={'data':{'method':'monte-carlo','sample_count':25,'seed':123,'factors':factors}}
    a=client.post('/v1/uncertainty-compute/sampling/design',headers=write_headers,json=p);b=client.post('/v1/uncertainty-compute/sampling/design',headers=write_headers,json=p)
    assert a.status_code==200,a.text; assert a.json()['manifest_sha256']==b.json()['manifest_sha256']; assert len(a.json()['samples'])==25
    lhs=client.post('/v1/uncertainty-compute/sampling/design',headers=write_headers,json={'data':{'method':'latin-hypercube','sample_count':20,'seed':7,'factors':factors}});assert lhs.status_code==200,lhs.text;assert len(lhs.json()['samples'])==20

def test_sobol_design_and_analysis(client,write_headers):
    factors=[{'key':'x','distribution':'uniform','lower_bound':0,'upper_bound':1},{'key':'y','distribution':'uniform','lower_bound':0,'upper_bound':1}]
    d=client.post('/v1/uncertainty-compute/sampling/design',headers=write_headers,json={'data':{'method':'sobol-design','sample_count':64,'seed':42,'factors':factors}});assert d.status_code==200,d.text;design=d.json();assert design['total_evaluations']==256
    # deterministic synthetic external model output f=x+2y
    f=lambda row:row['x']+2*row['y']
    payload={'A':[f(x) for x in design['A']],'B':[f(x) for x in design['B']],'AB':{k:[f(x) for x in v] for k,v in design['AB'].items()}}
    r=client.post('/v1/uncertainty-compute/sensitivity/sobol',headers=write_headers,json={'data':payload});assert r.status_code==200,r.text;body=r.json();assert len(body['factors'])==2 and body['model_execution_by_core'] is False

def test_morris_design_and_analysis(client,write_headers):
    factors=[{'key':'x','distribution':'uniform','lower_bound':0,'upper_bound':1},{'key':'y','distribution':'uniform','lower_bound':0,'upper_bound':1}]
    d=client.post('/v1/uncertainty-compute/sampling/design',headers=write_headers,json={'data':{'method':'morris-design','sample_count':8,'seed':9,'levels':6,'factors':factors}});assert d.status_code==200,d.text;design=d.json(); outputs=[3*r['x']+r['y'] for r in design['samples']]
    a=client.post('/v1/uncertainty-compute/sensitivity/morris',headers=write_headers,json={'data':{'samples':design['samples'],'outputs':outputs,'trajectories':design['trajectories']}});assert a.status_code==200,a.text; assert a.json()['factors'][0]['factor_key']=='x'

def test_weight_normalization_statistics_and_probability(client,write_headers):
    n=client.post('/v1/uncertainty-compute/ensembles/normalize-weights',headers=write_headers,json={'data':{'weights':[2,3,5]}});assert n.status_code==200,n.text;assert abs(sum(n.json()['normalized_weights'])-1)<1e-12
    s=client.post('/v1/uncertainty-compute/ensembles/statistics',headers=write_headers,json={'data':{'values':[1,2,10],'weights':[2,3,5],'quantiles':[0.5,0.9]}});assert s.status_code==200,s.text;assert s.json()['aggregation_performed_by_core'] is True
    p=client.post('/v1/uncertainty-compute/probabilities/exceedance',headers=write_headers,json={'data':{'values':[1,2,3,4,5],'threshold':3,'operator':'>='}});assert p.status_code==200,p.text;assert p.json()['probability']==0.6

def test_runtime_handoff_is_manifest_only(client,write_headers):
    r=client.post('/v1/uncertainty-compute/runtime-handoffs',headers=write_headers,json={'data':{'runtime_product':'lab','model_version_entity_id':'model-v','design_manifest':{'manifest_sha256':'abc'},'requested_outputs':['cost']}});assert r.status_code==200,r.text;d=r.json();assert d['dispatch_by_core'] is False and d['arbitrary_code_execution_by_core'] is False and len(d['handoff_sha256'])==64

def test_persisted_compute_run(client,write_headers):
    r=client.post('/v1/uncertainty-compute/ensembles/statistics',headers=write_headers,json={'data':{'values':[1,2,3],'persist':True,'run_key':'stats-1','name':'Stats'}});assert r.status_code==200,r.text;run=r.json()['run'];assert run['method']=='ensemble-statistics'
    listed=client.get('/v1/uncertainty-compute/runs',headers=write_headers);assert listed.status_code==200 and listed.json()['total']>=1

def test_public_readiness(client,write_headers):
    a=client.post('/v1/developer/applications',headers=write_headers,json={'name':'Compute SDK','owner_name':'Tester','owner_email':'compute-sdk@example.com','organization':'Test','website_url':'https://example.com','use_case':'Read uncertainty compute readiness.','status':'approved','plan_id':'free','metadata':{},'actor':'admin'});assert a.status_code in (200,201),a.text
    k=client.post(f"/v1/developer/applications/{a.json()['id']}/credentials",headers=write_headers,json={'label':'read','scopes':['data:read'],'created_by':'admin'});assert k.status_code in (200,201),k.text
    h={'Authorization':f"Bearer {k.json()['api_key']}"};r=client.get('/api/v1/uncertainty-compute/readiness',headers=h);assert r.status_code==200,r.text;assert r.json()['data']['migration_0040_applied'] is True
