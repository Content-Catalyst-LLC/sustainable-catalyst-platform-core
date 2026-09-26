from __future__ import annotations
import hashlib,json,math,os,subprocess,time,uuid
from dataclasses import dataclass,field
from datetime import datetime,timezone
from pathlib import Path
from typing import Any
from fastapi import FastAPI,HTTPException
from pydantic import BaseModel,Field,model_validator

PROVIDER_VERSION="1.0.0"; GO_VERSION=os.environ.get("SC_GO_VERSION","1.22.2"); GO_PACKAGE_VERSION=os.environ.get("SC_GO_PACKAGE_VERSION","1.22.2-2ubuntu0.4")
RUNTIME_ID="sc-runtime-go"; ADAPTER_ID="adapter:sc-runtime-go"; ADAPTER_CONTRACT="sc.core.runtime-adapter.v1"; RUNTIME_CONTRACT="sc.core.go-runtime.v1"
HOST=os.environ.get("SC_GO_RUNTIME_HOST","127.0.0.1"); PORT=int(os.environ.get("SC_GO_RUNTIME_PORT","18102")); GO_BIN=os.environ.get("SC_GO_BIN","/usr/lib/go-1.22/bin/go")
ARTIFACT_ROOT=Path(os.environ.get("SC_GO_ARTIFACT_ROOT","/var/lib/sc-go-runtime/artifacts")); WORK_ROOT=Path(os.environ.get("SC_GO_WORK_ROOT","/var/lib/sc-go-runtime/work")); MAX_EXECUTION_SECONDS=int(os.environ.get("SC_GO_MAX_EXECUTION_SECONDS","1800"))
OPERATIONS=["parallel_sum","parallel_map_affine","concurrent_histogram","parallel_matrix_row_sums","parallel_graph_degrees","batch_sha256"]; SAFE_OPERATION=set(OPERATIONS)

def now_iso(): return datetime.now(timezone.utc).isoformat()
def go_version_output():
    try:return subprocess.run([GO_BIN,"version"],capture_output=True,text=True,timeout=10).stdout.strip()
    except Exception:return ""
def runtime_ready(): return f"go{GO_VERSION}" in go_version_output()
def sha(path:Path):
    h=hashlib.sha256();
    with path.open('rb') as f:
        for c in iter(lambda:f.read(1024*1024),b''):h.update(c)
    return h.hexdigest()
def finite(x,name):
    if isinstance(x,bool) or not isinstance(x,(int,float)):raise ValueError(f"{name} must be numeric")
    x=float(x)
    if not math.isfinite(x):raise ValueError(f"{name} must be finite")
    return x

def validate_payload(operation,payload):
    if operation not in SAFE_OPERATION or not isinstance(payload,dict):raise ValueError("unsupported Go operation or payload")
    workers=payload.get("workers",4)
    if isinstance(workers,bool) or not isinstance(workers,int) or not 1<=workers<=64:raise ValueError("workers must be 1..64")
    if operation in {"parallel_sum","parallel_map_affine","concurrent_histogram"}:
        vals=payload.get("values")
        if not isinstance(vals,list) or not vals or len(vals)>262144:raise ValueError("values must contain 1..262144 items")
        vals=[finite(x,"values") for x in vals]
        out={"values":vals,"workers":workers}
        if operation=="parallel_map_affine":out.update(scale=finite(payload.get("scale",1.0),"scale"),offset=finite(payload.get("offset",0.0),"offset"))
        if operation=="concurrent_histogram":
            bins=payload.get("bins");lo=finite(payload.get("minimum"),"minimum");hi=finite(payload.get("maximum"),"maximum")
            if isinstance(bins,bool) or not isinstance(bins,int) or not 1<=bins<=4096 or hi<=lo:raise ValueError("invalid histogram configuration")
            out.update(bins=bins,minimum=lo,maximum=hi)
        return out
    if operation=="parallel_matrix_row_sums":
        m=payload.get("matrix")
        if not isinstance(m,list) or not m or not isinstance(m[0],list) or not m[0]:raise ValueError("matrix required")
        c=len(m[0]);
        if len(m)>4096 or c>4096 or len(m)*c>262144 or any(not isinstance(r,list) or len(r)!=c for r in m):raise ValueError("invalid bounded matrix")
        return {"matrix":[[finite(x,"matrix") for x in r] for r in m],"workers":workers}
    if operation=="parallel_graph_degrees":
        m=payload.get("adjacency_matrix")
        if not isinstance(m,list) or not m or len(m)>2048:raise ValueError("adjacency_matrix required")
        n=len(m);clean=[]
        for r in m:
            if not isinstance(r,list) or len(r)!=n:raise ValueError("adjacency_matrix must be square")
            row=[]
            for x in r:
                if isinstance(x,bool) or not isinstance(x,int) or x not in {0,1}:raise ValueError("graph values must be 0 or 1")
                row.append(x)
            clean.append(row)
        return {"adjacency_matrix":clean,"workers":workers}
    if operation=="batch_sha256":
        texts=payload.get("texts")
        if not isinstance(texts,list) or not texts or len(texts)>65536 or any(not isinstance(x,str) for x in texts):raise ValueError("texts required")
        if sum(len(x.encode('utf-8')) for x in texts)>4194304:raise ValueError("text batch too large")
        return {"texts":texts,"workers":workers}
    raise ValueError("unsupported Go operation")

def go_float_vec(v):return ",".join(f"{float(x):.17g}" for x in v)
def go_string_vec(v):return ",".join(json.dumps(x) for x in v)
def generated_source(operation,payload):
    p=validate_payload(operation,payload); workers=p.get("workers",4)
    if operation=="parallel_sum":
        vals=go_float_vec(p['values'])
        return f'''package main\nimport ("fmt";"sync")\nfunc main(){{v:=[]float64{{{vals}}};workers:={workers};if workers>len(v){{workers=len(v)}};ch:=make(chan float64,workers);var wg sync.WaitGroup;for w:=0;w<workers;w++{{wg.Add(1);go func(start int){{defer wg.Done();s:=0.0;for i:=start;i<len(v);i+=workers{{s+=v[i]}};ch<-s}}(w)}};go func(){{wg.Wait();close(ch)}}();total:=0.0;for x:=range ch{{total+=x}};fmt.Printf("SC_RESULT scalar %.17g\\n",total)}}\n'''
    if operation=="parallel_map_affine":
        vals=go_float_vec(p['values'])
        return f'''package main\nimport ("fmt";"sync")\nfunc main(){{v:=[]float64{{{vals}}};out:=make([]float64,len(v));workers:={workers};if workers>len(v){{workers=len(v)}};var wg sync.WaitGroup;for w:=0;w<workers;w++{{wg.Add(1);go func(start int){{defer wg.Done();for i:=start;i<len(v);i+=workers{{out[i]=v[i]*{p['scale']:.17g}+{p['offset']:.17g}}}}}(w)}};wg.Wait();fmt.Printf("SC_RESULT vector %d\\n",len(out));for _,x:=range out{{fmt.Printf("%.17g\\n",x)}}}}\n'''
    if operation=="concurrent_histogram":
        vals=go_float_vec(p['values']);bins=p['bins'];lo=p['minimum'];hi=p['maximum']
        return f'''package main\nimport ("fmt";"sync")\nfunc main(){{v:=[]float64{{{vals}}};bins:={bins};lo:=float64({lo:.17g});hi:=float64({hi:.17g});workers:={workers};if workers>len(v){{workers=len(v)}};locals:=make([][]int,workers);var wg sync.WaitGroup;for w:=0;w<workers;w++{{locals[w]=make([]int,bins);wg.Add(1);go func(id int){{defer wg.Done();for i:=id;i<len(v);i+=workers{{x:=v[i];if x<lo||x>hi{{continue}};b:=int((x-lo)/(hi-lo)*float64(bins));if b==bins{{b=bins-1}};locals[id][b]++}}}}(w)}};wg.Wait();out:=make([]int,bins);for _,h:=range locals{{for i,x:=range h{{out[i]+=x}}}};fmt.Printf("SC_RESULT int_vector %d\\n",bins);for _,x:=range out{{fmt.Println(x)}}}}\n'''
    if operation=="parallel_matrix_row_sums":
        rows=["[]float64{"+go_float_vec(r)+"}" for r in p['matrix']]
        return f'''package main\nimport ("fmt";"sync")\nfunc main(){{m:=[][]float64{{{','.join(rows)}}};out:=make([]float64,len(m));jobs:=make(chan int);workers:={workers};if workers>len(m){{workers=len(m)}};var wg sync.WaitGroup;for w:=0;w<workers;w++{{wg.Add(1);go func(){{defer wg.Done();for i:=range jobs{{s:=0.0;for _,x:=range m[i]{{s+=x}};out[i]=s}}}}()}};for i:=range m{{jobs<-i}};close(jobs);wg.Wait();fmt.Printf("SC_RESULT vector %d\\n",len(out));for _,x:=range out{{fmt.Printf("%.17g\\n",x)}}}}\n'''
    if operation=="parallel_graph_degrees":
        rows=["[]int{"+",".join(map(str,r))+"}" for r in p['adjacency_matrix']]
        return f'''package main\nimport ("fmt";"sync")\nfunc main(){{m:=[][]int{{{','.join(rows)}}};out:=make([]int,len(m));jobs:=make(chan int);workers:={workers};if workers>len(m){{workers=len(m)}};var wg sync.WaitGroup;for w:=0;w<workers;w++{{wg.Add(1);go func(){{defer wg.Done();for i:=range jobs{{d:=0;for _,x:=range m[i]{{d+=x}};out[i]=d}}}}()}};for i:=range m{{jobs<-i}};close(jobs);wg.Wait();fmt.Printf("SC_RESULT int_vector %d\\n",len(out));for _,x:=range out{{fmt.Println(x)}}}}\n'''
    if operation=="batch_sha256":
        texts=go_string_vec(p['texts'])
        return f'''package main\nimport ("crypto/sha256";"encoding/hex";"fmt";"sync")\nfunc main(){{v:=[]string{{{texts}}};out:=make([]string,len(v));jobs:=make(chan int);workers:={workers};if workers>len(v){{workers=len(v)}};var wg sync.WaitGroup;for w:=0;w<workers;w++{{wg.Add(1);go func(){{defer wg.Done();for i:=range jobs{{h:=sha256.Sum256([]byte(v[i]));out[i]=hex.EncodeToString(h[:])}}}}()}};for i:=range v{{jobs<-i}};close(jobs);wg.Wait();fmt.Printf("SC_RESULT string_vector %d\\n",len(out));for _,x:=range out{{fmt.Println(x)}}}}\n'''
    raise ValueError("unsupported Go operation")

def parse_output(stdout):
    lines=[x.strip() for x in stdout.splitlines() if x.strip()]
    for i,line in enumerate(lines):
        if not line.startswith('SC_RESULT '):continue
        p=line.split();kind=p[1]
        if kind=='scalar':return {'kind':'scalar','value':float(p[2])}
        if kind=='vector':
            n=int(p[2]);v=[float(x) for x in lines[i+1:i+1+n]];assert len(v)==n;return {'kind':kind,'values':v}
        if kind=='int_vector':
            n=int(p[2]);v=[int(x) for x in lines[i+1:i+1+n]];assert len(v)==n;return {'kind':kind,'values':v}
        if kind=='string_vector':
            n=int(p[2]);v=lines[i+1:i+1+n];assert len(v)==n;return {'kind':kind,'values':v}
    raise ValueError('no SC_RESULT marker')

def execute_native(operation,payload,timeout_seconds,run_id):
    if not runtime_ready():raise RuntimeError('Go runtime is not ready')
    source=generated_source(operation,payload);ARTIFACT_ROOT.mkdir(parents=True,exist_ok=True);WORK_ROOT.mkdir(parents=True,exist_ok=True);safe=run_id.replace(':','_');work=WORK_ROOT/safe;art=ARTIFACT_ROOT/safe;work.mkdir(parents=True,exist_ok=True);art.mkdir(parents=True,exist_ok=True)
    src=art/'main.go';binary=work/'job.bin';clog=art/'compile.log';rlog=art/'run.log';resultp=art/'result.json';src.write_text(source)
    env={"PATH":f"{Path(GO_BIN).parent}:/usr/bin:/bin","HOME":str(work),"LC_ALL":"C.UTF-8","GOTOOLCHAIN":"local","GOPROXY":"off","GOSUMDB":"off","GO111MODULE":"off","CGO_ENABLED":"0","GOCACHE":str(WORK_ROOT/'.gocache'),"GOPATH":str(WORK_ROOT/'.gopath')}
    cp=subprocess.run([GO_BIN,'build','-trimpath','-o',str(binary),str(src)],capture_output=True,text=True,timeout=min(timeout_seconds,MAX_EXECUTION_SECONDS),cwd=str(work),env=env);clog.write_text((cp.stdout or '')+(cp.stderr or ''))
    if cp.returncode!=0:raise RuntimeError(cp.stderr or cp.stdout or 'Go compilation failed')
    start=time.monotonic();rp=subprocess.run([str(binary)],capture_output=True,text=True,timeout=min(timeout_seconds,MAX_EXECUTION_SECONDS),cwd=str(work),env={"PATH":"/usr/bin:/bin","HOME":str(work),"LC_ALL":"C.UTF-8"});elapsed=int((time.monotonic()-start)*1000);rlog.write_text((rp.stdout or '')+(rp.stderr or ''));binary.unlink(missing_ok=True)
    if rp.returncode!=0:raise RuntimeError(rp.stderr or rp.stdout or 'Go execution failed')
    native=parse_output(rp.stdout);result={"operation":operation,"go_version":GO_VERSION,"elapsed_ms":elapsed,"native_result":native,"source_sha256":sha(src),"compile_log_sha256":sha(clog),"run_log_sha256":sha(rlog)};resultp.write_text(json.dumps(result,indent=2,sort_keys=True))
    return {**result,"artifacts":[{"artifact_kind":"go-generated-source","path":str(src),"content_sha256":sha(src)},{"artifact_kind":"go-result-json","path":str(resultp),"content_sha256":sha(resultp)},{"artifact_kind":"go-compile-log","path":str(clog),"content_sha256":sha(clog)},{"artifact_kind":"go-run-log","path":str(rlog),"content_sha256":sha(rlog)}]}

class PrepareRequest(BaseModel):
    operation:str;payload:dict[str,Any];timeout_seconds:int=Field(default=120,ge=1,le=1800);workers:int=Field(default=4,ge=1,le=64);job_ref:str|None=Field(default=None,max_length=500);environment_ref:str|None=Field(default=None,max_length=1000)
    @model_validator(mode='after')
    def valid(self): self.payload.setdefault('workers',self.workers);validate_payload(self.operation,self.payload);return self
class RunRequest(BaseModel):run_id:str=Field(min_length=2,max_length=500)
@dataclass
class RunRecord:
    run_id:str;request:PrepareRequest;status:str='prepared';created_at:str=field(default_factory=now_iso);started_at:str|None=None;completed_at:str|None=None;result:dict[str,Any]|None=None;error:str|None=None
RUNS={}

def adapter_descriptor():return {"adapter_id":ADAPTER_ID,"adapter_contract":ADAPTER_CONTRACT,"provider_id":RUNTIME_ID,"provider_version":PROVIDER_VERSION,"native_runtime":"go","native_runtime_version":GO_VERSION,"native_package_version":GO_PACKAGE_VERSION,"runtime_kind":"language","language":"go","status":"registered","execution_state":"active","transport":"HTTP","endpoint":f"http://{HOST}:{PORT}","capabilities":OPERATIONS,"lifecycle_methods":["health","version","capabilities","prepare","execute","cancel","inspect","collect_results","collect_artifacts","diagnose"],"boundaries":{"arbitrary_go_source":False,"shell_execution":False,"go_module_download":False,"runtime_package_install":False,"caller_filesystem_paths":False}}
app=FastAPI(title='Sustainable Catalyst Go Runtime',version=PROVIDER_VERSION)
@app.get('/health')
def health():return {"ok":runtime_ready(),"runtime_id":RUNTIME_ID,"version":PROVIDER_VERSION,"go_version":GO_VERSION,"go_package_version":GO_PACKAGE_VERSION,"go_bin":GO_BIN,"capabilities":len(OPERATIONS)}
@app.get('/version')
def version():return {"runtime_id":RUNTIME_ID,"version":PROVIDER_VERSION,"go_version":GO_VERSION,"go_package_version":GO_PACKAGE_VERSION,"raw":go_version_output()}
@app.get('/capabilities')
def capabilities():return {"runtime_id":RUNTIME_ID,"operations":OPERATIONS}
@app.get('/v1/core-adapter')
def adapter():return adapter_descriptor()
@app.post('/v1/core-adapter/prepare')
def prepare(body:PrepareRequest):
    run_id=f"go-run:{uuid.uuid4()}";RUNS[run_id]=RunRecord(run_id,body);return {"ok":True,"run_id":run_id,"status":"prepared","operation":body.operation,"runtime_id":RUNTIME_ID,"runtime_version":PROVIDER_VERSION}
@app.post('/v1/core-adapter/execute')
def execute(body:RunRequest):
    r=RUNS.get(body.run_id)
    if not r:raise HTTPException(404,'run not found')
    if r.status not in {'prepared','failed'}:raise HTTPException(409,'run not executable')
    r.status='running';r.started_at=now_iso()
    try:r.result=execute_native(r.request.operation,r.request.payload,r.request.timeout_seconds,r.run_id);r.status='completed';r.completed_at=now_iso();return {"ok":True,"run_id":r.run_id,"status":r.status,"result":r.result}
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
    return {"ok":True,"run_id":r.run_id,"status":r.status,"runtime_ready":runtime_ready(),"go_version_output":go_version_output(),"error":r.error}
