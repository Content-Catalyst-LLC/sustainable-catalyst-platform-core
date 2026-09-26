from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
import hashlib, json, math, os, subprocess, sys, uuid

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field, model_validator

RUNTIME_ID="sc-runtime-python"; ADAPTER_ID="adapter:sc-runtime-python"; VERSION="1.0.0"
PYTHON_VERSION=os.getenv("SC_PYTHON_VERSION","3.12.3")
PYTHON_BIN=os.getenv("SC_PYTHON_BIN","/usr/bin/python3.12")
PYTHON_PACKAGE_VERSION=os.getenv("SC_PYTHON_PACKAGE_VERSION","")
ARTIFACT_ROOT=Path(os.getenv("SC_PYTHON_ARTIFACT_ROOT","/tmp/sc-python-runtime/artifacts"))
WORK_ROOT=Path(os.getenv("SC_PYTHON_WORK_ROOT","/tmp/sc-python-runtime/work"))
OPERATIONS=["descriptive_summary","linear_regression","matrix_multiply","standardize","bootstrap_mean_ci","token_frequency"]
ARTIFACT_ROOT.mkdir(parents=True,exist_ok=True);WORK_ROOT.mkdir(parents=True,exist_ok=True)
app=FastAPI(title="Sustainable Catalyst Python Runtime",version=VERSION)

def now_iso(): return datetime.now(timezone.utc).isoformat()
def sha256_bytes(b:bytes)->str: return hashlib.sha256(b).hexdigest()
def python_version_output()->str:
    try:return subprocess.check_output([PYTHON_BIN,"--version"],stderr=subprocess.STDOUT,text=True,timeout=10).strip()
    except Exception:return ""
def runtime_ready()->bool: return python_version_output().startswith(f"Python {PYTHON_VERSION}")

def _finite(v:list[Any],name:str,min_len:int=1,max_len:int=262144)->list[float]:
    if not isinstance(v,list) or not min_len<=len(v)<=max_len: raise ValueError(f"{name} must contain {min_len}..{max_len} values")
    out=[float(x) for x in v]
    if any(not math.isfinite(x) for x in out): raise ValueError(f"{name} values must be finite")
    return out

def _matrix(v:Any,name:str)->list[list[float]]:
    if not isinstance(v,list) or not v or not isinstance(v[0],list) or not v[0]: raise ValueError(f"{name} must be non-empty matrix")
    rows=[_finite(row,f"{name} row",1,256) for row in v]; c=len(rows[0])
    if len(rows)>256 or any(len(row)!=c for row in rows) or len(rows)*c>65536: raise ValueError(f"{name} exceeds bounded rectangular matrix size")
    return rows

def validate_payload(op:str,payload:dict[str,Any])->dict[str,Any]:
    if op not in OPERATIONS: raise ValueError("unsupported operation")
    p=dict(payload or {})
    if op in {"descriptive_summary","standardize","bootstrap_mean_ci"}: p["values"]=_finite(p.get("values",[]),"values")
    if op=="linear_regression":
        p["x"]=_finite(p.get("x",[]),"x",2);p["y"]=_finite(p.get("y",[]),"y",2)
        if len(p["x"])!=len(p["y"]):raise ValueError("x/y lengths differ")
        mx=sum(p["x"])/len(p["x"])
        if sum((x-mx)**2 for x in p["x"])==0:raise ValueError("x variance is zero")
    elif op=="matrix_multiply":
        a=_matrix(p.get("matrix_a"),"matrix_a");b=_matrix(p.get("matrix_b"),"matrix_b")
        if len(a[0])!=len(b):raise ValueError("matrix dimensions are incompatible")
        if len(a)*len(b[0])>65536:raise ValueError("matrix output too large")
        p["matrix_a"],p["matrix_b"]=a,b
    elif op=="standardize":
        if len(p["values"])<2:raise ValueError("standardize requires at least two values")
        m=sum(p["values"])/len(p["values"])
        if sum((x-m)**2 for x in p["values"])==0:raise ValueError("variance is zero")
    elif op=="bootstrap_mean_ci":
        p["iterations"]=int(p.get("iterations",1000));p["confidence"]=float(p.get("confidence",0.95));p["seed"]=int(p.get("seed",0))
        if not 100<=p["iterations"]<=10000:raise ValueError("iterations must be 100..10000")
        if not 0.5<=p["confidence"]<1.0:raise ValueError("confidence must be [0.5,1.0)")
        if not -(2**63)<=p["seed"]<2**63:raise ValueError("seed out of range")
    elif op=="token_frequency":
        text=str(p.get("text",""));size=len(text.encode("utf-8"));top_k=int(p.get("top_k",20));lower=bool(p.get("lowercase",True))
        if not 1<=size<=1048576:raise ValueError("text must be 1..1048576 UTF-8 bytes")
        if not 1<=top_k<=1000:raise ValueError("top_k must be 1..1000")
        p.update(text=text,top_k=top_k,lowercase=lower)
    return p

PROGRAM="""import json, math, random, re\nfrom collections import Counter\nfrom pathlib import Path\np=json.loads(Path("input.json").read_text())\nop=p["operation"];d=p["payload"]\ndef mean(v):return sum(v)/len(v)\nif op=="descriptive_summary":\n v=d["values"];m=mean(v);var=sum((x-m)**2 for x in v)/(len(v)-1) if len(v)>1 else 0.0;result={"count":len(v),"mean":m,"minimum":min(v),"maximum":max(v),"sample_stddev":math.sqrt(var)}\nelif op=="linear_regression":\n x=d["x"];y=d["y"];mx=mean(x);my=mean(y);ssx=sum((a-mx)**2 for a in x);sxy=sum((a-mx)*(b-my) for a,b in zip(x,y));slope=sxy/ssx;intercept=my-slope*mx;pred=[intercept+slope*a for a in x];sst=sum((b-my)**2 for b in y);sse=sum((b-c)**2 for b,c in zip(y,pred));r2=1.0-sse/sst if sst else 1.0;result={"slope":slope,"intercept":intercept,"r_squared":r2,"n":len(x)}\nelif op=="matrix_multiply":\n a=d["matrix_a"];b=d["matrix_b"];bt=list(zip(*b));result={"matrix":[[sum(x*y for x,y in zip(row,col)) for col in bt] for row in a]}\nelif op=="standardize":\n v=d["values"];m=mean(v);sd=math.sqrt(sum((x-m)**2 for x in v)/len(v));result={"mean":m,"population_stddev":sd,"values":[(x-m)/sd for x in v]}\nelif op=="bootstrap_mean_ci":\n v=d["values"];n=len(v);rng=random.Random(d["seed"]);means=sorted(mean([v[rng.randrange(n)] for _ in range(n)]) for _ in range(d["iterations"]));alpha=(1.0-d["confidence"])/2.0;lo=means[max(0,min(len(means)-1,int(alpha*(len(means)-1))))];hi=means[max(0,min(len(means)-1,int((1-alpha)*(len(means)-1))))];result={"observed_mean":mean(v),"lower":lo,"upper":hi,"iterations":d["iterations"],"confidence":d["confidence"],"seed":d["seed"]}\nelif op=="token_frequency":\n text=d["text"].lower() if d["lowercase"] else d["text"];tokens=re.findall(r"[A-Za-z0-9_'-]+",text);c=Counter(tokens);items=sorted(c.items(),key=lambda kv:(-kv[1],kv[0]))[:d["top_k"]];result={"token_count":len(tokens),"unique_tokens":len(c),"frequencies":[{"token":k,"count":v} for k,v in items]}\nelse:raise RuntimeError("unsupported operation")\nPath("result.json").write_text(json.dumps(result,separators=(",",":"),sort_keys=True))\nprint("SC_PYTHON_RESULT_OK")\n"""

def generated_source(op:str,payload:dict[str,Any])->str:
    validate_payload(op,payload);return PROGRAM

class PrepareRequest(BaseModel):
    operation:str
    payload:dict[str,Any]=Field(default_factory=dict)
    timeout_seconds:int=Field(default=120,ge=1,le=1800)
    job_ref:str="job:python-runtime"
    environment_ref:str="environment-package:python-runtime:v1"
    @model_validator(mode="after")
    def valid(self): self.payload=validate_payload(self.operation,self.payload);return self
class RunRequest(BaseModel):run_id:str
@dataclass
class RunState:
    run_id:str;request:PrepareRequest;status:str="prepared";created_at:str="";started_at:str|None=None;completed_at:str|None=None;result:dict[str,Any]|None=None;error:str|None=None
RUNS:dict[str,RunState]={}

def adapter_descriptor():
    return {"adapter_id":ADAPTER_ID,"adapter_contract":"sc.core.runtime-adapter.v1","provider_id":RUNTIME_ID,"provider_version":VERSION,"native_runtime":"CPython","native_runtime_version":PYTHON_VERSION,"native_package_version":PYTHON_PACKAGE_VERSION,"runtime_kind":"language","language":"python","status":"registered","execution_state":"active","transport":"HTTP","endpoint":"http://127.0.0.1:18103","capabilities":list(OPERATIONS),"lifecycle_methods":["health","version","capabilities","prepare","execute","cancel","inspect","collect_results","collect_artifacts","diagnose"],"boundaries":{"arbitrary_python_source":False,"shell_execution":False,"runtime_package_install":False,"caller_filesystem_paths":False,"job_network_access":False}}

def execute_run(r:RunState)->dict[str,Any]:
    safe=r.run_id.replace(":","_");work=WORK_ROOT/safe;art=ARTIFACT_ROOT/safe;work.mkdir(parents=True,exist_ok=True);art.mkdir(parents=True,exist_ok=True)
    source=generated_source(r.request.operation,r.request.payload);source_path=work/'program.py';input_path=work/'input.json';result_path=work/'result.json'
    source_path.write_text(source);input_path.write_text(json.dumps({"operation":r.request.operation,"payload":r.request.payload},sort_keys=True,separators=(",",":")))
    env={"PATH":"/usr/bin:/bin","HOME":str(work),"LC_ALL":"C.UTF-8","LANG":"C.UTF-8","PYTHONHASHSEED":"0"}
    cp=subprocess.run([PYTHON_BIN,"-I","-S",str(source_path)],cwd=work,env=env,text=True,capture_output=True,timeout=r.request.timeout_seconds,check=False)
    (art/'stdout.txt').write_text(cp.stdout);(art/'stderr.txt').write_text(cp.stderr);(art/'program.py').write_text(source);(art/'input.json').write_text(input_path.read_text())
    if cp.returncode!=0 or not result_path.exists(): raise RuntimeError((cp.stderr or cp.stdout or f"Python job failed with exit {cp.returncode}")[-12000:])
    native=json.loads(result_path.read_text());(art/'result.json').write_text(json.dumps(native,indent=2,sort_keys=True))
    artifacts=[]
    for kind,path in [("python-source",art/'program.py'),("python-input-json",art/'input.json'),("python-stdout-log",art/'stdout.txt'),("python-stderr-log",art/'stderr.txt'),("python-result-json",art/'result.json')]:
        b=path.read_bytes();artifacts.append({"kind":kind,"path":str(path),"sha256":sha256_bytes(b),"size_bytes":len(b)})
    return {"operation":r.request.operation,"native_result":native,"artifacts":artifacts,"python_version":PYTHON_VERSION,"provider_version":VERSION,"isolated_mode":True,"site_imports_disabled":True}

@app.get('/health')
def health():return {"ok":runtime_ready(),"runtime_id":RUNTIME_ID,"version":VERSION,"python_version":PYTHON_VERSION,"python_package_version":PYTHON_PACKAGE_VERSION,"python_bin":PYTHON_BIN,"capabilities":len(OPERATIONS)}
@app.get('/version')
def version():return {"runtime_id":RUNTIME_ID,"version":VERSION,"python_version":PYTHON_VERSION,"python_version_output":python_version_output(),"python_package_version":PYTHON_PACKAGE_VERSION}
@app.get('/capabilities')
def capabilities():return {"runtime_id":RUNTIME_ID,"operations":list(OPERATIONS)}
@app.get('/v1/core-adapter')
def core_adapter():return adapter_descriptor()
@app.post('/v1/core-adapter/prepare')
def prepare(body:PrepareRequest):
    rid=f"python-run:{uuid.uuid4()}";r=RunState(rid,body,created_at=now_iso());RUNS[rid]=r;return {"ok":True,"run_id":rid,"status":r.status,"operation":body.operation,"runtime_id":RUNTIME_ID,"runtime_version":VERSION,"input_sha256":sha256_bytes(json.dumps(body.payload,sort_keys=True,separators=(",",":"),default=str).encode())}
@app.post('/v1/core-adapter/execute')
def execute(body:RunRequest):
    r=RUNS.get(body.run_id)
    if not r:raise HTTPException(404,'run not found')
    if r.status!='prepared':raise HTTPException(409,f'run status is {r.status}')
    r.status='running';r.started_at=now_iso()
    try:r.result=execute_run(r);r.status='completed';r.completed_at=now_iso();return {"ok":True,"run_id":r.run_id,"status":r.status,"result":r.result}
    except Exception as e:r.status='failed';r.error=str(e);r.completed_at=now_iso();raise HTTPException(500,str(e))
@app.post('/v1/core-adapter/cancel')
def cancel(body:RunRequest):
    r=RUNS.get(body.run_id)
    if not r:raise HTTPException(404,'run not found')
    if r.status=='prepared':r.status='cancelled';r.completed_at=now_iso()
    return {"ok":True,"run_id":r.run_id,"status":r.status}
@app.post('/v1/core-adapter/inspect')
def inspect(body:RunRequest):
    r=RUNS.get(body.run_id)
    if not r:raise HTTPException(404,'run not found')
    return {"ok":True,"run_id":r.run_id,"status":r.status,"operation":r.request.operation,"job_ref":r.request.job_ref,"environment_ref":r.request.environment_ref,"created_at":r.created_at,"started_at":r.started_at,"completed_at":r.completed_at,"error":r.error}
@app.post('/v1/core-adapter/collect_results')
def collect_results(body:RunRequest):
    r=RUNS.get(body.run_id)
    if not r:raise HTTPException(404,'run not found')
    return {"ok":True,"run_id":r.run_id,"status":r.status,"result":r.result}
@app.post('/v1/core-adapter/collect_artifacts')
def collect_artifacts(body:RunRequest):
    r=RUNS.get(body.run_id)
    if not r:raise HTTPException(404,'run not found')
    return {"ok":True,"run_id":r.run_id,"status":r.status,"artifacts":(r.result or {}).get('artifacts',[])}
@app.post('/v1/core-adapter/diagnose')
def diagnose(body:RunRequest):
    r=RUNS.get(body.run_id)
    if not r:raise HTTPException(404,'run not found')
    return {"ok":True,"run_id":r.run_id,"status":r.status,"runtime_ready":runtime_ready(),"python_version_output":python_version_output(),"error":r.error}
