from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from app.database import Database,Base
from app.models import AnalyticalRuntimeProviderRecord,AnalyticalExecutionRequestRecord,AnalyticalResultObjectRecord
from app.services import uncertainty_probabilistic_evidence as svc

def db():
    d=Database('sqlite+pysqlite:///:memory:'); Base.metadata.create_all(d.engine); return d

def seed(session):
    p=AnalyticalRuntimeProviderRecord(provider_key='catalystanalyticsr',name='Catalyst Analytics R',provider_version='2.3.0',runtime='r',execution_host='workspace',contract_ref='sc.core.analytical-runtime-provider.v1')
    session.add(p);session.flush()
    q=AnalyticalExecutionRequestRecord(request_key='req-1',provider_id=p.id,analysis_type='uncertainty',runtime='r',execution_host='workspace')
    session.add(q);session.flush()
    r=AnalyticalResultObjectRecord(result_ref='result-1',request_id=q.id,provider_id=p.id,provider_version='2.3.0',analysis_type='uncertainty',provenance_hash='a'*64,result_fingerprint='b'*64)
    session.add(r);session.commit();return r

def evidence(method='sobol'):
    return {'schema_version':'1.0.0','evidence_type':'catalyst_uncertainty_sensitivity_evidence','contract':svc.SOURCE_CONTRACT,'analysis_ref':'analysis-1','method':method,'summary':[{'target':'emissions','metric':'mean','mean':42.0,'n':128}],'sensitivity':[{'target':'parameters.intensity','metric':'emissions','first_order':0.41,'total_order':0.57,'variance':12.4,'n':128,'first_order_estimator':'saltelli_2010','total_order_estimator':'jansen_1999'}],'source_refs':['workspace.execution.1'],'limitations':['conditional'],'provenance':{'provider_key':'catalystanalyticsr','provider_version':'2.3.0','runtime':'r','execution_host':'workspace'},'boundary':{'uncertainty_is_evidence_not_truth':True,'sensitivity_does_not_establish_causality':True,'no_automatic_policy_preference':True,'no_automatic_scientific_validity_certification':True,'human_review_required':True}}

def test_readiness_boundaries():
    d=db()
    with d.session_factory() as s:
        x=svc.readiness(s); assert x['release']=='3.21.0'; assert x['execute_uncertainty_by_core'] is False; assert 'sobol' in x['methods']

def test_ingest_sobol_and_idempotency():
    d=db()
    with d.session_factory() as s:
        seed(s); out=svc.ingest(s,{'result_ref':'result-1','evidence':evidence(),'visibility':'public'}); assert out['idempotent_replay'] is False; assert out['study']['method']=='sobol'
        again=svc.ingest(s,{'result_ref':'result-1','evidence':evidence()}); assert again['idempotent_replay'] is True

def test_boundary_rejected():
    d=db()
    with d.session_factory() as s:
        seed(s); e=evidence();e['boundary']['sensitivity_does_not_establish_causality']=False
        try: svc.ingest(s,{'result_ref':'result-1','evidence':e})
        except ValueError as exc: assert 'boundary' in str(exc)
        else: raise AssertionError('expected rejection')

def test_interpretation_human_only():
    d=db()
    with d.session_factory() as s:
        seed(s); out=svc.ingest(s,{'result_ref':'result-1','evidence':evidence()}); ref=out['study']['study_ref']
        try: svc.interpret(s,ref,{'interpretation_ref':'i1','statement':'x','author_ref':'u1','human_authored':False})
        except ValueError: pass
        else: raise AssertionError('expected rejection')
        good=svc.interpret(s,ref,{'interpretation_ref':'i1','statement':'Conditional sensitivity evidence','author_ref':'u1','human_authored':True}); assert good['human_authored'] is True

def test_supported_methods():
    assert svc.METHODS=={'monte_carlo','latin_hypercube','morris','sobol'}
