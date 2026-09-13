from __future__ import annotations
import hashlib, json, math, random, statistics
from datetime import datetime, timezone
from typing import Any
from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from ..models import (
    UncertaintyDefinitionRecord, UncertaintyComputeRunRecord,
    SensitivityStudyRecord, SensitivityFactorRecord, EnsembleRecord,
)

SUPPORTED_SAMPLERS={"monte-carlo","latin-hypercube","sobol-design","morris-design"}
SUPPORTED_HANDOFFS={"lab","workbench","external"}

def _ser(row):
    out={}
    for c in row.__table__.columns:
        v=getattr(row,c.name)
        if hasattr(v,'isoformat'): v=v.isoformat()
        out[c.name]=v
    return out

def _stable_hash(payload:Any)->str:
    return hashlib.sha256(json.dumps(payload,sort_keys=True,separators=(',',':'),default=str).encode()).hexdigest()

def readiness(db:Session)->dict[str,Any]:
    return {
        "migration_0040_applied": True,
        "runtime_integration": True,
        "deterministic_sampling": True,
        "monte_carlo_sampling": True,
        "latin_hypercube_sampling": True,
        "sobol_design_generation": True,
        "sobol_index_analysis": True,
        "morris_design_generation": True,
        "morris_elementary_effect_analysis": True,
        "ensemble_weight_normalization": True,
        "ensemble_descriptive_statistics": True,
        "empirical_probability_estimation": True,
        "lab_workbench_handoff_manifests": True,
        "arbitrary_code_execution_by_core": False,
        "model_execution_by_core": False,
        "automatic_truth_promotion": False,
        "supported_runtime_products": sorted(SUPPORTED_HANDOFFS),
        "counts":{"compute_runs":int(db.scalar(select(func.count()).select_from(UncertaintyComputeRunRecord)) or 0)},
    }

def _validate_count(n:int,max_samples:int)->int:
    if n<1: raise ValueError('sample_count must be positive.')
    if n>max_samples: raise ValueError(f'sample_count exceeds configured maximum of {max_samples}.')
    return n

def _factor_spec(item:dict[str,Any])->dict[str,Any]:
    key=str(item.get('key') or item.get('factor_key') or '')
    if not key: raise ValueError('Each factor requires key.')
    kind=str(item.get('distribution') or item.get('distribution_name') or item.get('kind') or 'uniform').lower()
    lower=item.get('lower_bound'); upper=item.get('upper_bound'); params=dict(item.get('parameters') or {})
    empirical=list(item.get('empirical_values') or [])
    if kind in {'uniform','interval','triangular'} and (lower is None or upper is None): raise ValueError(f'{key}: lower_bound and upper_bound are required.')
    if lower is not None and upper is not None and float(lower)>float(upper): raise ValueError(f'{key}: lower_bound cannot exceed upper_bound.')
    if kind=='normal' and float(params.get('stddev',params.get('sigma',0)))<=0: raise ValueError(f'{key}: normal stddev must be positive.')
    if kind=='empirical' and not empirical: raise ValueError(f'{key}: empirical_values are required.')
    if kind not in {'uniform','interval','triangular','normal','empirical'}: raise ValueError(f'{key}: unsupported distribution {kind}.')
    return {'key':key,'distribution':kind,'lower_bound':lower,'upper_bound':upper,'parameters':params,'empirical_values':empirical,'unit':item.get('unit')}

def factors_from_uncertainty_definitions(db:Session,ids:list[str])->list[dict[str,Any]]:
    out=[]
    for uid in ids:
        u=db.get(UncertaintyDefinitionRecord,str(uid))
        if u is None: raise ValueError(f'Unknown uncertainty definition: {uid}')
        out.append(_factor_spec({'key':u.uncertainty_key,'distribution':u.distribution_name or ('empirical' if u.empirical_values_json else 'uniform'),'lower_bound':u.lower_bound,'upper_bound':u.upper_bound,'parameters':u.parameters_json,'empirical_values':u.empirical_values_json,'unit':u.unit}))
    return out

def _inv_sample(spec:dict[str,Any],u:float,rng:random.Random)->float:
    kind=spec['distribution']; lo=spec.get('lower_bound'); hi=spec.get('upper_bound'); p=spec.get('parameters') or {}
    if kind in {'uniform','interval'}: return float(lo)+(float(hi)-float(lo))*u
    if kind=='triangular':
        mode=float(p.get('mode',(float(lo)+float(hi))/2)); c=(mode-float(lo))/(float(hi)-float(lo)) if float(hi)!=float(lo) else 0.5
        if u<c: return float(lo)+math.sqrt(u*(float(hi)-float(lo))*(mode-float(lo)))
        return float(hi)-math.sqrt((1-u)*(float(hi)-float(lo))*(float(hi)-mode))
    if kind=='normal':
        mean=float(p.get('mean',0)); sd=float(p.get('stddev',p.get('sigma',1)))
        # inverse-normal approximation via NormalDist in stdlib
        return statistics.NormalDist(mu=mean,sigma=sd).inv_cdf(min(max(u,1e-12),1-1e-12))
    vals=[float(x) for x in spec['empirical_values']]; vals.sort(); idx=min(int(u*len(vals)),len(vals)-1); return vals[idx]

def monte_carlo(factors:list[dict[str,Any]],n:int,seed:int)->list[dict[str,float]]:
    rng=random.Random(seed); specs=[_factor_spec(f) for f in factors]
    return [{s['key']:_inv_sample(s,rng.random(),rng) for s in specs} for _ in range(n)]

def latin_hypercube(factors:list[dict[str,Any]],n:int,seed:int)->list[dict[str,float]]:
    rng=random.Random(seed); specs=[_factor_spec(f) for f in factors]; cols={}
    for s in specs:
        us=[(i+rng.random())/n for i in range(n)]; rng.shuffle(us); cols[s['key']]=[_inv_sample(s,u,rng) for u in us]
    return [{s['key']:cols[s['key']][i] for s in specs} for i in range(n)]

def sobol_design(factors:list[dict[str,Any]],n:int,seed:int)->dict[str,Any]:
    specs=[_factor_spec(f) for f in factors]
    A=latin_hypercube(specs,n,seed); B=latin_hypercube(specs,n,seed+104729)
    AB={}
    for s in specs:
        k=s['key']; AB[k]=[{**A[i],k:B[i][k]} for i in range(n)]
    return {'A':A,'B':B,'AB':AB,'base_sample_count':n,'total_evaluations':n*(2+len(specs))}

def morris_design(factors:list[dict[str,Any]],trajectories:int,seed:int,levels:int=6)->dict[str,Any]:
    if levels<4: raise ValueError('levels must be at least 4.')
    rng=random.Random(seed); specs=[_factor_spec(f) for f in factors]; delta=levels/(2*(levels-1)); rows=[]; trajectory_meta=[]
    for t in range(trajectories):
        u={s['key']:rng.randint(0,max(0,levels-2))/(levels-1) for s in specs}; order=[s['key'] for s in specs]; rng.shuffle(order)
        start=len(rows); rows.append({s['key']:_inv_sample(s,u[s['key']],rng) for s in specs})
        for key in order:
            u[key]=min(1.0,u[key]+delta) if u[key]+delta<=1 else max(0.0,u[key]-delta)
            rows.append({s['key']:_inv_sample(s,u[s['key']],rng) for s in specs})
        trajectory_meta.append({'trajectory':t,'start_index':start,'order':order})
    return {'samples':rows,'trajectories':trajectory_meta,'levels':levels,'delta':delta,'total_evaluations':len(rows)}

def generate_design(factors:list[dict[str,Any]],method:str,sample_count:int,seed:int,max_samples:int,levels:int=6)->dict[str,Any]:
    method=method.lower(); _validate_count(sample_count,max_samples)
    if method not in SUPPORTED_SAMPLERS: raise ValueError('Unsupported sampling method.')
    specs=[_factor_spec(f) for f in factors]
    if not specs: raise ValueError('At least one factor is required.')
    if method=='monte-carlo': data={'samples':monte_carlo(specs,sample_count,seed),'total_evaluations':sample_count}
    elif method=='latin-hypercube': data={'samples':latin_hypercube(specs,sample_count,seed),'total_evaluations':sample_count}
    elif method=='sobol-design': data=sobol_design(specs,sample_count,seed)
    else: data=morris_design(specs,sample_count,seed,levels=levels)
    manifest={'method':method,'seed':seed,'sample_count':sample_count,'factor_keys':[s['key'] for s in specs],**data}
    manifest['manifest_sha256']=_stable_hash(manifest)
    return manifest

def analyze_sobol(payload:dict[str,Any])->dict[str,Any]:
    ya=[float(x) for x in payload.get('A') or []]; yb=[float(x) for x in payload.get('B') or []]; ab=dict(payload.get('AB') or {})
    if not ya or len(ya)!=len(yb): raise ValueError('A and B output vectors must be non-empty and equal length.')
    n=len(ya); all_y=ya+yb; var=statistics.pvariance(all_y)
    if var<=0: raise ValueError('Output variance must be positive for Sobol analysis.')
    rows=[]
    for key,vals in ab.items():
        y=[float(x) for x in vals]
        if len(y)!=n: raise ValueError(f'AB output vector for {key} has wrong length.')
        s1=sum(yb[i]*(y[i]-ya[i]) for i in range(n))/n/var
        st=sum((ya[i]-y[i])**2 for i in range(n))/(2*n*var)
        rows.append({'factor_key':key,'sobol_first':s1,'sobol_total':st})
    rows.sort(key=lambda x:abs(x['sobol_total']),reverse=True)
    for i,row in enumerate(rows,1): row['rank_position']=i
    return {'method':'sobol','sample_count':n,'output_variance':var,'factors':rows,'calculated_by_core':True,'model_execution_by_core':False}

def analyze_morris(payload:dict[str,Any])->dict[str,Any]:
    samples=list(payload.get('samples') or []); outputs=[float(x) for x in payload.get('outputs') or []]; trajectories=list(payload.get('trajectories') or [])
    if len(samples)!=len(outputs): raise ValueError('samples and outputs must have equal length.')
    effects={}
    for tr in trajectories:
        start=int(tr['start_index']); order=list(tr['order'])
        for j,key in enumerate(order):
            a=samples[start+j]; b=samples[start+j+1]; dx=float(b[key])-float(a[key])
            if dx==0: continue
            effects.setdefault(key,[]).append((outputs[start+j+1]-outputs[start+j])/dx)
    rows=[]
    for key,vals in effects.items():
        rows.append({'factor_key':key,'mu':statistics.fmean(vals),'mu_star':statistics.fmean(abs(v) for v in vals),'sigma':statistics.pstdev(vals) if len(vals)>1 else 0.0,'effects':len(vals)})
    rows.sort(key=lambda x:x['mu_star'],reverse=True)
    for i,row in enumerate(rows,1): row['rank_position']=i
    return {'method':'morris','factors':rows,'calculated_by_core':True,'model_execution_by_core':False}

def normalize_weights(weights:list[float],policy:str='explicit')->dict[str,Any]:
    vals=[float(w) for w in weights]
    if not vals: raise ValueError('weights are required.')
    if any(w<0 for w in vals): raise ValueError('weights cannot be negative.')
    if policy=='equal': vals=[1.0]*len(vals)
    total=sum(vals)
    if total<=0: raise ValueError('weight total must be positive.')
    norm=[w/total for w in vals]
    return {'policy':policy,'raw_weights':weights,'normalized_weights':norm,'raw_sum':total,'normalized_sum':sum(norm),'normalization_performed_by_core':True}

def _weighted_quantile(values:list[float],weights:list[float],q:float)->float:
    pairs=sorted(zip(values,weights),key=lambda x:x[0]); target=q*sum(weights); c=0.0
    for v,w in pairs:
        c+=w
        if c>=target:return v
    return pairs[-1][0]

def ensemble_statistics(values:list[float],weights:list[float]|None=None,quantiles:list[float]|None=None)->dict[str,Any]:
    vals=[float(x) for x in values]
    if not vals: raise ValueError('values are required.')
    if weights is None: weights=[1.0]*len(vals)
    if len(weights)!=len(vals): raise ValueError('weights length must match values.')
    nw=normalize_weights(weights)['normalized_weights']
    mean=sum(v*w for v,w in zip(vals,nw)); var=sum(w*(v-mean)**2 for v,w in zip(vals,nw)); qs=quantiles or [0.05,0.5,0.95]
    if any(not 0<=float(q)<=1 for q in qs):raise ValueError('quantiles must be between 0 and 1.')
    return {'count':len(vals),'mean':mean,'variance':var,'stddev':math.sqrt(var),'min':min(vals),'max':max(vals),'quantiles':{str(q):_weighted_quantile(vals,nw,float(q)) for q in qs},'normalized_weights':nw,'aggregation_performed_by_core':True}

def exceedance_probability(values:list[float],threshold:float,operator:str='>')->dict[str,Any]:
    vals=[float(x) for x in values]
    if not vals:raise ValueError('values are required.')
    t=float(threshold); ops={'>':lambda x:x>t,'>=':lambda x:x>=t,'<':lambda x:x<t,'<=':lambda x:x<=t}
    if operator not in ops:raise ValueError('operator must be one of >, >=, <, <=.')
    k=sum(1 for x in vals if ops[operator](x)); n=len(vals); p=k/n; z=1.959963984540054; denom=1+z*z/n; center=(p+z*z/(2*n))/denom; half=z*math.sqrt(p*(1-p)/n+z*z/(4*n*n))/denom
    return {'threshold':t,'operator':operator,'sample_count':n,'exceedances':k,'probability':p,'confidence_interval_95':[max(0,center-half),min(1,center+half)],'estimator':'empirical-binomial','probability_estimation_performed_by_core':True}

def runtime_handoff(payload:dict[str,Any])->dict[str,Any]:
    product=str(payload.get('runtime_product') or 'lab')
    if product not in SUPPORTED_HANDOFFS:raise ValueError('Unsupported runtime_product.')
    manifest={'runtime_product':product,'model_version_entity_id':payload.get('model_version_entity_id'),'scenario_entity_id':payload.get('scenario_entity_id'),'design_manifest':payload.get('design_manifest') or {},'requested_outputs':payload.get('requested_outputs') or [],'callback_contract':payload.get('callback_contract') or {},'dispatch_by_core':False,'arbitrary_code_execution_by_core':False}
    manifest['handoff_sha256']=_stable_hash(manifest);return manifest

def persist_run(db:Session,payload:dict[str,Any],output:dict[str,Any])->dict[str,Any]:
    row=UncertaintyComputeRunRecord(run_key=str(payload.get('run_key') or _stable_hash({'m':payload.get('method'),'i':payload})[:24]),name=str(payload.get('name') or payload.get('method') or 'Uncertainty compute run'),method=str(payload.get('method') or 'compute'),run_state='completed',project_entity_id=payload.get('project_entity_id'),model_entity_id=payload.get('model_entity_id'),model_version_entity_id=payload.get('model_version_entity_id'),sensitivity_study_visual_entity_id=payload.get('sensitivity_study_visual_entity_id'),ensemble_visual_entity_id=payload.get('ensemble_visual_entity_id'),runtime_product=str(payload.get('runtime_product') or 'core-statistics'),seed=payload.get('seed'),sample_count=payload.get('sample_count'),input_manifest_json=dict(payload.get('input_manifest') or {}),output_summary_json=output,provenance_json={'generated_at':datetime.now(timezone.utc).isoformat(),'core_compute':True,**dict(payload.get('provenance') or {})},metadata_json=dict(payload.get('metadata') or {}),created_by=str(payload.get('created_by') or 'operator'))
    db.add(row)
    try:db.commit();db.refresh(row)
    except IntegrityError as exc:db.rollback();raise HTTPException(status_code=409,detail='uncertainty compute run_key already exists.') from exc
    return _ser(row)

def list_runs(db:Session,limit:int=100,offset:int=0):
    total=int(db.scalar(select(func.count()).select_from(UncertaintyComputeRunRecord)) or 0); rows=db.scalars(select(UncertaintyComputeRunRecord).order_by(UncertaintyComputeRunRecord.created_at.desc()).limit(limit).offset(offset)).all(); return [_ser(x) for x in rows],total

def read_run(db:Session,run_id:str):
    row=db.get(UncertaintyComputeRunRecord,run_id)
    if row is None:raise HTTPException(status_code=404,detail='Uncertainty compute run not found.')
    return _ser(row)
