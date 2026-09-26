from __future__ import annotations
import hashlib,json,os,re,subprocess,time,uuid
from dataclasses import dataclass,field
from datetime import datetime,timezone
from pathlib import Path
from typing import Any
from fastapi import FastAPI,HTTPException
from pydantic import BaseModel,Field,model_validator

PROVIDER_VERSION="1.0.0";SWI_PROLOG_VERSION=os.environ.get("SC_PROLOG_VERSION","9.0.4");SWI_PROLOG_PACKAGE_VERSION=os.environ.get("SC_PROLOG_PACKAGE_VERSION","9.0.4+dfsg-3.1ubuntu4")
RUNTIME_ID="sc-runtime-prolog";ADAPTER_ID="adapter:sc-runtime-prolog";RUNTIME_CONTRACT="sc.core.prolog-runtime.v1";ADAPTER_CONTRACT="sc.core.runtime-adapter.v1"
HOST=os.environ.get("SC_PROLOG_RUNTIME_HOST","127.0.0.1");PORT=int(os.environ.get("SC_PROLOG_RUNTIME_PORT","18104"));SWIPL=os.environ.get("SC_PROLOG_BIN","/usr/bin/swipl")
ARTIFACT_ROOT=Path(os.environ.get("SC_PROLOG_ARTIFACT_ROOT","/var/lib/sc-prolog-runtime/artifacts"));WORK_ROOT=Path(os.environ.get("SC_PROLOG_WORK_ROOT","/var/lib/sc-prolog-runtime/work"))
OPERATIONS=["relation_reachable","relation_paths_bounded","transitive_closure","contradiction_scan","temporal_consistency","graph_coloring"]
SAFE=set(OPERATIONS);IDENT=re.compile(r"^[a-z][a-z0-9_]{0,63}$")

def now_iso(): return datetime.now(timezone.utc).isoformat()
def atom(v):
    if not isinstance(v,str) or not IDENT.fullmatch(v): raise ValueError("identifier must match [a-z][a-z0-9_]{0,63}")
    return v

def edge_list(v,name="edges"):
    if not isinstance(v,list) or len(v)>5000: raise ValueError(f"{name} must be a list with <=5000 edges")
    out=[]
    for e in v:
        if not isinstance(e,dict): raise ValueError(f"{name} entries must be objects")
        out.append((atom(e.get("source")),atom(e.get("target"))))
    return out

def validate_payload(op,p):
    if op not in SAFE or not isinstance(p,dict): raise ValueError("unsupported Prolog operation or payload")
    if op in {"relation_reachable","relation_paths_bounded","transitive_closure"}:
        edges=edge_list(p.get("edges",[]));
        if not edges: raise ValueError("edges are required")
        q={"edges":edges}
        if op!="transitive_closure": q.update(source=atom(p.get("source")),target=atom(p.get("target")))
        if op=="relation_paths_bounded":
            d=p.get("max_depth",4)
            if isinstance(d,bool) or not isinstance(d,int) or not 1<=d<=12: raise ValueError("max_depth must be 1..12")
            q["max_depth"]=d
        return q
    if op=="contradiction_scan":
        a=p.get("assertions",[]);n=p.get("negations",[])
        if not isinstance(a,list) or not isinstance(n,list) or len(a)+len(n)>10000: raise ValueError("invalid assertions/negations")
        a=[atom(x) for x in a];n=[atom(x) for x in n]
        if not (a or n): raise ValueError("assertions or negations required")
        return {"assertions":a,"negations":n}
    if op=="temporal_consistency":
        e=edge_list(p.get("temporal_edges",[]),"temporal_edges")
        if not e: raise ValueError("temporal_edges required")
        return {"temporal_edges":e}
    if op=="graph_coloring":
        vc=p.get("vertex_count");mc=p.get("max_colors")
        if isinstance(vc,bool) or not isinstance(vc,int) or not 1<=vc<=256: raise ValueError("vertex_count must be 1..256")
        if isinstance(mc,bool) or not isinstance(mc,int) or not 1<=mc<=16: raise ValueError("max_colors must be 1..16")
        es=p.get("undirected_edges",[])
        if not isinstance(es,list) or len(es)>10000: raise ValueError("undirected_edges invalid")
        clean=[]
        for e in es:
            if not isinstance(e,list) or len(e)!=2 or any(isinstance(x,bool) or not isinstance(x,int) for x in e): raise ValueError("edges must be integer pairs")
            a,b=e
            if a<0 or b<0 or a>=vc or b>=vc or a==b: raise ValueError("invalid graph edge")
            clean.append((a,b))
        return {"vertex_count":vc,"max_colors":mc,"undirected_edges":clean}
    raise ValueError("unsupported operation")

def facts(name,edges): return "\n".join(f"{name}({a},{b})." for a,b in edges)

def build_program(op,p):
    q=validate_payload(op,p)
    pre=":- use_module(library(http/json)).\n"
    if op=="relation_reachable":
        return pre+":- table reach/2.\n"+facts("edge",q["edges"])+f"""\nreach(X,Y):-edge(X,Y).\nreach(X,Y):-edge(X,Z),reach(Z,Y).\nmain:-((reach({q['source']},{q['target']}))->B=true;B=false),json_write_dict(current_output,_{{reachable:B}}),nl.\n"""
    if op=="transitive_closure":
        return pre+":- table reach/2.\n"+facts("edge",q["edges"])+"""\nreach(X,Y):-edge(X,Y).\nreach(X,Y):-edge(X,Z),reach(Z,Y).\nmain:-findall([X,Y],reach(X,Y),L0),sort(L0,L),json_write_dict(current_output,_{pairs:L}),nl.\n"""
    if op=="relation_paths_bounded":
        return pre+facts("edge",q["edges"])+f"""\npath(X,Y,Max,P):-path0(X,Y,[X],R,Max),reverse(R,P).\npath0(X,Y,V,[Y|V],Max):-Max>0,edge(X,Y),\\+member(Y,V).\npath0(X,Y,V,P,Max):-Max>1,edge(X,Z),\\+member(Z,V),M is Max-1,path0(Z,Y,[Z|V],P,M).\nmain:-findall(P,path({q['source']},{q['target']},{q['max_depth']},P),L0),sort(L0,L),json_write_dict(current_output,_{{paths:L}}),nl.\n"""
    if op=="contradiction_scan":
        af="\n".join(f"assertion({x})." for x in q["assertions"]); nf="\n".join(f"negation({x})." for x in q["negations"])
        return pre+af+"\n"+nf+"""\nmain:-findall(X,(assertion(X),negation(X)),L0),sort(L0,L),length(L,N),json_write_dict(current_output,_{contradictions:L,count:N}),nl.\n"""
    if op=="temporal_consistency":
        return pre+":- table precedes/2.\n"+facts("before",q["temporal_edges"])+"""\nprecedes(X,Y):-before(X,Y).\nprecedes(X,Y):-before(X,Z),precedes(Z,Y).\nmain:-findall(X,precedes(X,X),C0),sort(C0,C),(C=[]->B=true;B=false),json_write_dict(current_output,_{consistent:B,cycle_nodes:C}),nl.\n"""
    if op=="graph_coloring":
        pairs=",".join(f"{a}-{b}" for a,b in q["undirected_edges"])
        return pre+":- use_module(library(clpfd)).\n"+f"""edge_list([{pairs}]).\nconstrain(_,[]).\nconstrain(C,[A-B|Es]):-nth0(A,C,CA),nth0(B,C,CB),CA#\\=CB,constrain(C,Es).\nmain:-length(C,{q['vertex_count']}),C ins 1..{q['max_colors']},edge_list(E),constrain(C,E),((labeling([ffc],C))->json_write_dict(current_output,_{{satisfiable:true,colors:C}});json_write_dict(current_output,_{{satisfiable:false,colors:[]}})),nl.\n"""
    raise ValueError("unsupported operation")

def execute_program(run_id,op,p,timeout):
    safe=run_id.replace(":","_");work=WORK_ROOT/safe;art=ARTIFACT_ROOT/safe;work.mkdir(parents=True,exist_ok=True);art.mkdir(parents=True,exist_ok=True)
    program=build_program(op,p);src=work/"program.pl";src.write_text(program)
    env={"PATH":"/usr/bin:/bin","HOME":str(work),"LANG":"C.UTF-8","LC_ALL":"C.UTF-8"}
    cp=subprocess.run([SWIPL,"-q","-f","none","-s",str(src),"-g","main","-t","halt"],capture_output=True,text=True,timeout=timeout,env=env)
    (art/"stdout.txt").write_text(cp.stdout);(art/"stderr.txt").write_text(cp.stderr);(art/"program.pl").write_text(program)
    if cp.returncode!=0: raise RuntimeError((cp.stderr or cp.stdout or f"swipl exit {cp.returncode}").strip())
    lines=[x for x in cp.stdout.splitlines() if x.strip()]
    if not lines: raise RuntimeError("SWI-Prolog produced no result")
    try: result=json.loads(lines[-1])
    except Exception as e: raise RuntimeError(f"invalid SWI-Prolog JSON result: {e}: {cp.stdout}")
    out={"runtime_id":RUNTIME_ID,"runtime_version":PROVIDER_VERSION,"swi_prolog_version":SWI_PROLOG_VERSION,"operation":op,"result":result}
    result_path=art/"result.json";result_path.write_text(json.dumps(out,indent=2,sort_keys=True))
    artifacts=[]
    for kind,path in [("prolog-program",art/"program.pl"),("prolog-stdout",art/"stdout.txt"),("prolog-stderr",art/"stderr.txt"),("logic-result",result_path)]:
        artifacts.append({"artifact_kind":kind,"path":str(path),"content_sha256":hashlib.sha256(path.read_bytes()).hexdigest()})
    return out,artifacts

class PrepareRequest(BaseModel):
    operation:str;payload:dict[str,Any];timeout_seconds:int=Field(default=30,ge=1,le=300);job_ref:str|None=None;environment_ref:str|None=None
    @model_validator(mode="after")
    def valid(self): validate_payload(self.operation,self.payload);return self
class RunRequest(BaseModel): run_id:str
@dataclass
class RunRecord:
    run_id:str;request:PrepareRequest;status:str="prepared";created_at:str=field(default_factory=now_iso);started_at:str|None=None;completed_at:str|None=None;result:dict[str,Any]|None=None;artifacts:list[dict[str,Any]]=field(default_factory=list);error:str|None=None
RUNS={}

def adapter_descriptor():
    return {"adapter_id":ADAPTER_ID,"adapter_contract":ADAPTER_CONTRACT,"provider_id":RUNTIME_ID,"provider_version":PROVIDER_VERSION,"native_runtime":"SWI-Prolog","native_runtime_version":SWI_PROLOG_VERSION,"native_package_version":SWI_PROLOG_PACKAGE_VERSION,"runtime_kind":"language","language":"prolog","status":"registered","execution_state":"active","transport":"HTTP","endpoint":f"http://{HOST}:{PORT}","capabilities":OPERATIONS,"lifecycle_methods":["health","version","capabilities","prepare","execute","cancel","inspect","collect_results","collect_artifacts","diagnose"],"boundaries":{"arbitrary_prolog_source":False,"shell_execution":False,"runtime_package_install":False,"caller_filesystem_paths":False,"provider_generated_programs":True}}

def runtime_version():
    cp=subprocess.run([SWIPL,"--version"],capture_output=True,text=True,timeout=5);return (cp.stdout or cp.stderr).strip()
app=FastAPI(title="Sustainable Catalyst Prolog Runtime",version=PROVIDER_VERSION)
@app.get("/health")
def health():
    try:v=runtime_version();ok=SWI_PROLOG_VERSION in v
    except Exception:v="unavailable";ok=False
    return {"ok":ok,"runtime_id":RUNTIME_ID,"version":PROVIDER_VERSION,"swi_prolog_version":SWI_PROLOG_VERSION,"swi_prolog_package_version":SWI_PROLOG_PACKAGE_VERSION,"native_version_output":v,"capabilities":len(OPERATIONS)}
@app.get("/version")
def version(): return {"runtime_id":RUNTIME_ID,"version":PROVIDER_VERSION,"swi_prolog_version":SWI_PROLOG_VERSION,"native_version_output":runtime_version()}
@app.get("/capabilities")
def capabilities(): return {"runtime_id":RUNTIME_ID,"operations":OPERATIONS}
@app.get("/v1/core-adapter")
def adapter(): return adapter_descriptor()
@app.post("/v1/core-adapter/prepare")
def prepare(body:PrepareRequest):
    rid=f"prolog-run:{uuid.uuid4()}";RUNS[rid]=RunRecord(rid,body);return {"ok":True,"run_id":rid,"status":"prepared","operation":body.operation,"runtime_id":RUNTIME_ID,"runtime_version":PROVIDER_VERSION}
@app.post("/v1/core-adapter/execute")
def execute(body:RunRequest):
    r=RUNS.get(body.run_id)
    if not r: raise HTTPException(404,"run not found")
    if r.status not in {"prepared","failed"}: raise HTTPException(409,"run not executable")
    r.status="running";r.started_at=now_iso()
    try:
        r.result,r.artifacts=execute_program(r.run_id,r.request.operation,r.request.payload,r.request.timeout_seconds);r.status="completed";r.completed_at=now_iso();return {"ok":True,"run_id":r.run_id,"status":r.status,"result":r.result}
    except Exception as e:
        r.status="failed";r.error=str(e);r.completed_at=now_iso();raise HTTPException(500,str(e))
@app.post("/v1/core-adapter/cancel")
def cancel(body:RunRequest):
    r=RUNS.get(body.run_id)
    if not r: raise HTTPException(404,"run not found")
    if r.status=="prepared":r.status="cancelled";r.completed_at=now_iso()
    return {"ok":True,"run_id":r.run_id,"status":r.status}
@app.post("/v1/core-adapter/inspect")
def inspect(body:RunRequest):
    r=RUNS.get(body.run_id)
    if not r: raise HTTPException(404,"run not found")
    return {"ok":True,"run_id":r.run_id,"status":r.status,"operation":r.request.operation,"job_ref":r.request.job_ref,"environment_ref":r.request.environment_ref,"created_at":r.created_at,"started_at":r.started_at,"completed_at":r.completed_at,"error":r.error}
@app.post("/v1/core-adapter/collect_results")
def collect_results(body:RunRequest):
    r=RUNS.get(body.run_id)
    if not r: raise HTTPException(404,"run not found")
    return {"ok":True,"run_id":r.run_id,"status":r.status,"result":r.result}
@app.post("/v1/core-adapter/collect_artifacts")
def collect_artifacts(body:RunRequest):
    r=RUNS.get(body.run_id)
    if not r: raise HTTPException(404,"run not found")
    return {"ok":True,"run_id":r.run_id,"status":r.status,"artifacts":r.artifacts}
@app.post("/v1/core-adapter/diagnose")
def diagnose(body:RunRequest):
    r=RUNS.get(body.run_id)
    if not r: raise HTTPException(404,"run not found")
    return {"ok":True,"run_id":r.run_id,"status":r.status,"native_version_output":runtime_version(),"error":r.error}
