from __future__ import annotations
import hashlib,json,math,os,subprocess,time,uuid
from dataclasses import dataclass,field
from datetime import datetime,timezone
from pathlib import Path
from typing import Any
from fastapi import FastAPI,HTTPException
from pydantic import BaseModel,Field,model_validator
PROVIDER_VERSION="1.0.0";GCC_VERSION=os.environ.get("SC_CPP_GCC_VERSION","13.3.0");GPP_VERSION=os.environ.get("SC_CPP_GPP_VERSION","13.3.0");GCC_PACKAGE_VERSION=os.environ.get("SC_CPP_GCC_PACKAGE_VERSION","13.3.0-6ubuntu2~24.04.1");GPP_PACKAGE_VERSION=os.environ.get("SC_CPP_GPP_PACKAGE_VERSION","13.3.0-6ubuntu2~24.04.1");RUNTIME_ID="sc-runtime-cpp";ADAPTER_ID="adapter:sc-runtime-cpp";ADAPTER_CONTRACT="sc.core.runtime-adapter.v1";HOST=os.environ.get("SC_CPP_RUNTIME_HOST","127.0.0.1");PORT=int(os.environ.get("SC_CPP_RUNTIME_PORT","18100"));GCC_BIN=os.environ.get("SC_CPP_GCC_BIN","/usr/bin/gcc-13");GPP_BIN=os.environ.get("SC_CPP_GPP_BIN","/usr/bin/g++-13");ARTIFACT_ROOT=Path(os.environ.get("SC_CPP_ARTIFACT_ROOT","/var/lib/sc-cpp-runtime/artifacts"));WORK_ROOT=Path(os.environ.get("SC_CPP_WORK_ROOT","/var/lib/sc-cpp-runtime/work"));MAX_EXECUTION_SECONDS=1800;MAX_VECTOR=262144;MAX_MATRIX_DIM=256
OPERATIONS=["dot_product","matrix_multiply","linear_interpolation","polynomial_evaluate","fir_filter","dijkstra_shortest_path"]
OPERATION_LANGUAGE={"dot_product":"c11","matrix_multiply":"cpp17","linear_interpolation":"c11","polynomial_evaluate":"cpp17","fir_filter":"c11","dijkstra_shortest_path":"cpp17"}
def now_iso():return datetime.now(timezone.utc).isoformat()
def compiler_ready(bin_path,version):
 try:
  p=subprocess.run([bin_path,"-dumpfullversion"],capture_output=True,text=True,timeout=10);return p.returncode==0 and p.stdout.strip()==version
 except Exception:return False
def runtime_ready():return compiler_ready(GCC_BIN,GCC_VERSION) and compiler_ready(GPP_BIN,GPP_VERSION)
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def finite(v,n):
 if isinstance(v,bool) or not isinstance(v,(int,float)):raise ValueError(f"{n} must be numeric")
 v=float(v)
 if not math.isfinite(v):raise ValueError(f"{n} must be finite")
 return v
def vector(v,n,min_len=1):
 if not isinstance(v,list) or len(v)<min_len or len(v)>MAX_VECTOR:raise ValueError(f"{n} length invalid")
 return [finite(x,n) for x in v]
def matrix(v,n):
 if not isinstance(v,list) or not v or not isinstance(v[0],list) or not v[0]:raise ValueError(f"{n} matrix invalid")
 r,c=len(v),len(v[0]);
 if r>MAX_MATRIX_DIM or c>MAX_MATRIX_DIM:raise ValueError(f"{n} matrix too large")
 out=[]
 for row in v:
  if len(row)!=c:raise ValueError(f"{n} must be rectangular")
  out.append([finite(x,n) for x in row])
 return out
def validate_payload(op,p):
 if op not in OPERATIONS or not isinstance(p,dict):raise ValueError("unsupported C/C++ operation or payload")
 if op=="dot_product":
  a=vector(p.get("a"),"a");b=vector(p.get("b"),"b");
  if len(a)!=len(b):raise ValueError("dot_product length mismatch")
  return {"a":a,"b":b}
 if op=="matrix_multiply":
  a=matrix(p.get("a"),"a");b=matrix(p.get("b"),"b");
  if len(a[0])!=len(b):raise ValueError("matrix dimension mismatch")
  return {"a":a,"b":b}
 if op=="linear_interpolation":
  x=vector(p.get("x"),"x",2);y=vector(p.get("y"),"y",2);q=finite(p.get("query_x"),"query_x")
  if len(x)!=len(y) or any(x[i+1]<=x[i] for i in range(len(x)-1)) or q<x[0] or q>x[-1]:raise ValueError("linear interpolation inputs invalid")
  return {"x":x,"y":y,"query_x":q}
 if op=="polynomial_evaluate":return {"coefficients":vector(p.get("coefficients"),"coefficients"),"x":finite(p.get("x"),"x")}
 if op=="fir_filter":
  s=vector(p.get("signal"),"signal");k=vector(p.get("kernel"),"kernel");
  if len(k)>1024:raise ValueError("kernel too long")
  return {"signal":s,"kernel":k}
 if op=="dijkstra_shortest_path":
  a=matrix(p.get("adjacency"),"adjacency");n=len(a);s=p.get("source");t=p.get("target")
  if any(len(row)!=n for row in a) or any(x<0 for row in a for x in row):raise ValueError("adjacency invalid")
  if isinstance(s,bool) or isinstance(t,bool) or not isinstance(s,int) or not isinstance(t,int) or not(0<=s<n and 0<=t<n):raise ValueError("indices invalid")
  return {"adjacency":a,"source":s,"target":t}
def nums(xs):return ", ".join(f"{float(x):.17g}" for x in xs)
def arr(name,xs):return f"double {name}[{len(xs)}] = {{{nums(xs)}}};"
def generated_source(op,p):
 p=validate_payload(op,p);lang=OPERATION_LANGUAGE[op]
 if op=="dot_product":return lang,f'#include <stdio.h>\nint main(void){{ {arr("a",p["a"])} {arr("b",p["b"])} double v=0; for(int i=0;i<{len(p["a"])};++i)v+=a[i]*b[i]; printf("SC_RESULT scalar %.17g\\n",v); return 0; }}\n'
 if op=="linear_interpolation":return lang,f'#include <stdio.h>\nint main(void){{ {arr("x",p["x"])} {arr("y",p["y"])} double q={p["query_x"]:.17g},v=y[0]; for(int i=0;i<{len(p["x"])-1};++i) if(q>=x[i]&&q<=x[i+1]){{double t=(q-x[i])/(x[i+1]-x[i]);v=y[i]+t*(y[i+1]-y[i]);break;}} printf("SC_RESULT scalar %.17g\\n",v); return 0; }}\n'
 if op=="fir_filter":
  n=len(p["signal"]);m=len(p["kernel"]);return lang,f'#include <stdio.h>\nint main(void){{ {arr("s",p["signal"])} {arr("k",p["kernel"])} double y[{n}]; for(int i=0;i<{n};++i){{y[i]=0;for(int j=0;j<{m};++j){{int z=i-j;if(z>=0)y[i]+=k[j]*s[z];}}}} printf("SC_RESULT vector {n}\\n");for(int i=0;i<{n};++i)printf("%.17g\\n",y[i]);return 0;}}\n'
 if op=="matrix_multiply":
  a,b=p["a"],p["b"];r,k,c=len(a),len(a[0]),len(b[0]);af=[x for row in a for x in row];bf=[x for row in b for x in row];return lang,f'#include <iostream>\n#include <iomanip>\nint main(){{double a[{len(af)}]={{{nums(af)}}},b[{len(bf)}]={{{nums(bf)}}},o[{r*c}]={{0}};for(int i=0;i<{r};++i)for(int j=0;j<{c};++j)for(int z=0;z<{k};++z)o[i*{c}+j]+=a[i*{k}+z]*b[z*{c}+j];std::cout<<"SC_RESULT matrix {r} {c}\\n"<<std::setprecision(17);for(double v:o)std::cout<<v<<"\\n";}}\n'
 if op=="polynomial_evaluate":
  co=p["coefficients"];return lang,f'#include <iostream>\n#include <iomanip>\nint main(){{double c[{len(co)}]={{{nums(co)}}};double x={p["x"]:.17g},v=0;for(int i={len(co)-1};i>=0;--i)v=v*x+c[i];std::cout<<"SC_RESULT scalar "<<std::setprecision(17)<<v<<"\\n";}}\n'
 if op=="dijkstra_shortest_path":
  a=p["adjacency"];n=len(a);flat=[x for row in a for x in row];return lang,f'#include <iostream>\n#include <iomanip>\n#include <limits>\n#include <cmath>\nint main(){{const int n={n};double w[n*n]={{{nums(flat)}}},d[n];bool used[n]={{false}};for(int i=0;i<n;++i)d[i]=std::numeric_limits<double>::infinity();d[{p["source"]}]=0;for(int step=0;step<n;++step){{int u=-1;for(int i=0;i<n;++i)if(!used[i]&&(u<0||d[i]<d[u]))u=i;if(u<0||!std::isfinite(d[u]))break;used[u]=true;for(int v=0;v<n;++v){{double q=w[u*n+v];if(u!=v&&q>0&&d[u]+q<d[v])d[v]=d[u]+q;}}}}std::cout<<"SC_RESULT scalar "<<std::setprecision(17)<<d[{p["target"]}]<<"\\n";}}\n'
def parse_output(s):
 lines=[x.strip() for x in s.splitlines() if x.strip()]
 for i,line in enumerate(lines):
  if not line.startswith("SC_RESULT "):continue
  p=line.split();kind=p[1]
  if kind=="scalar":return {"kind":"scalar","value":float(p[2])}
  if kind=="vector":
   n=int(p[2]);return {"kind":"vector","values":[float(x) for x in lines[i+1:i+1+n]]}
  if kind=="matrix":
   r,c=int(p[2]),int(p[3]);f=[float(x) for x in lines[i+1:i+1+r*c]];return {"kind":"matrix","rows":r,"cols":c,"values":[f[z*c:(z+1)*c] for z in range(r)]}
 raise ValueError("no SC_RESULT marker")
def execute_native(operation,payload,timeout_seconds,optimization_level,run_id):
 if not runtime_ready():raise RuntimeError("GCC/G++ runtime is not ready")
 lang,src=generated_source(operation,payload);ARTIFACT_ROOT.mkdir(parents=True,exist_ok=True);WORK_ROOT.mkdir(parents=True,exist_ok=True);safe=run_id.replace(":","_");w=WORK_ROOT/safe;a=ARTIFACT_ROOT/safe;w.mkdir(parents=True,exist_ok=True);a.mkdir(parents=True,exist_ok=True);ext="c" if lang=="c11" else "cpp";sp=a/f"job.{ext}";ep=w/"job.bin";cl=a/"compile.log";rl=a/"run.log";rp=a/"result.json";sp.write_text(src);cmd=[GCC_BIN,f"-O{optimization_level}","-std=c11","-fno-fast-math",str(sp),"-lm","-o",str(ep)] if lang=="c11" else [GPP_BIN,f"-O{optimization_level}","-std=c++17","-fno-fast-math",str(sp),"-o",str(ep)];cp=subprocess.run(cmd,capture_output=True,text=True,timeout=min(timeout_seconds,MAX_EXECUTION_SECONDS),cwd=str(w));cl.write_text((cp.stdout or "")+(cp.stderr or ""));
 if cp.returncode!=0:raise RuntimeError(cp.stderr or "compile failed")
 start=time.monotonic();run=subprocess.run([str(ep)],capture_output=True,text=True,timeout=min(timeout_seconds,MAX_EXECUTION_SECONDS),cwd=str(w));elapsed=int((time.monotonic()-start)*1000);rl.write_text((run.stdout or "")+(run.stderr or ""));ep.unlink(missing_ok=True)
 if run.returncode!=0:raise RuntimeError(run.stderr or "execution failed")
 native=parse_output(run.stdout);result={"operation":operation,"language_profile":lang,"elapsed_ms":elapsed,"native_result":native,"source_sha256":sha(sp),"compile_log_sha256":sha(cl),"run_log_sha256":sha(rl)};rp.write_text(json.dumps(result,indent=2));return {**result,"artifacts":[{"artifact_kind":"c-cpp-generated-source","path":str(sp),"content_sha256":sha(sp)},{"artifact_kind":"c-cpp-result-json","path":str(rp),"content_sha256":sha(rp)},{"artifact_kind":"c-cpp-compile-log","path":str(cl),"content_sha256":sha(cl)},{"artifact_kind":"c-cpp-run-log","path":str(rl),"content_sha256":sha(rl)}]}
class PrepareRequest(BaseModel):
 operation:str;payload:dict[str,Any];timeout_seconds:int=Field(default=120,ge=1,le=1800);optimization_level:int=Field(default=2,ge=0,le=2);job_ref:str|None=None;environment_ref:str|None=None
 @model_validator(mode="after")
 def v(self):validate_payload(self.operation,self.payload);return self
class RunRequest(BaseModel):run_id:str
@dataclass
class RunRecord:run_id:str;request:PrepareRequest;status:str="prepared";created_at:str=field(default_factory=now_iso);started_at:str|None=None;completed_at:str|None=None;result:dict|None=None;error:str|None=None
RUNS={}
def adapter_descriptor():return {"adapter_id":ADAPTER_ID,"adapter_contract":ADAPTER_CONTRACT,"provider_id":RUNTIME_ID,"provider_version":PROVIDER_VERSION,"native_runtime":"GCC/G++","native_runtime_version":GCC_VERSION,"native_package_version":GCC_PACKAGE_VERSION,"runtime_kind":"language","language":"c-cpp","language_profiles":["c11","cpp17"],"status":"registered","execution_state":"active" if runtime_ready() else "degraded","transport":"HTTP","endpoint":f"http://{HOST}:{PORT}","capabilities":OPERATIONS,"lifecycle_methods":["health","version","capabilities","prepare","execute","cancel","inspect","collect_results","collect_artifacts","diagnose"],"boundaries":{"arbitrary_c_cpp_source":False,"shell_execution":False,"runtime_package_install":False,"caller_filesystem_paths":False,"provider_managed_compilation":True}}
app=FastAPI(title="Sustainable Catalyst C/C++ Runtime",version=PROVIDER_VERSION)
@app.get("/health")
def health():return {"ok":runtime_ready(),"runtime_id":RUNTIME_ID,"version":PROVIDER_VERSION,"gcc_version":GCC_VERSION,"gcc_package_version":GCC_PACKAGE_VERSION,"gpp_version":GPP_VERSION,"gpp_package_version":GPP_PACKAGE_VERSION,"capabilities":len(OPERATIONS)}
@app.get("/version")
def version():return {"runtime_id":RUNTIME_ID,"version":PROVIDER_VERSION,"gcc_version":GCC_VERSION,"gpp_version":GPP_VERSION,"gcc_package_version":GCC_PACKAGE_VERSION,"gpp_package_version":GPP_PACKAGE_VERSION}
@app.get("/capabilities")
def capabilities():return {"runtime_id":RUNTIME_ID,"version":PROVIDER_VERSION,"operations":OPERATIONS,"language_profiles":["c11","cpp17"],"operation_language":OPERATION_LANGUAGE}
@app.get("/v1/core-adapter")
def ad():return adapter_descriptor()
@app.post("/v1/core-adapter/prepare")
def prepare(b:PrepareRequest):
 rid=f"cpp-run:{uuid.uuid4()}";RUNS[rid]=RunRecord(rid,b);return {"ok":True,"run_id":rid,"status":"prepared","operation":b.operation,"runtime_id":RUNTIME_ID,"runtime_version":PROVIDER_VERSION,"language_profile":OPERATION_LANGUAGE[b.operation]}
@app.post("/v1/core-adapter/execute")
def execute(b:RunRequest):
 r=RUNS.get(b.run_id)
 if not r:raise HTTPException(404,"run not found")
 try:r.status="running";r.started_at=now_iso();r.result=execute_native(r.request.operation,r.request.payload,r.request.timeout_seconds,r.request.optimization_level,r.run_id);r.status="completed";r.completed_at=now_iso();return {"ok":True,"run_id":r.run_id,"status":r.status,"runtime_id":RUNTIME_ID,"runtime_version":PROVIDER_VERSION,"result":r.result}
 except Exception as e:r.status="failed";r.error=str(e);r.completed_at=now_iso();raise HTTPException(500,r.error)

@app.post("/v1/core-adapter/cancel")
def cancel(b:RunRequest):
 r=RUNS.get(b.run_id)
 if not r:raise HTTPException(404,"run not found")
 if r.status=="running":raise HTTPException(409,"v1 synchronous provider cannot interrupt an already-running native process")
 if r.status in {"completed","failed"}:return {"ok":True,"run_id":r.run_id,"status":r.status}
 r.status="cancelled";r.completed_at=now_iso();return {"ok":True,"run_id":r.run_id,"status":r.status}
@app.post("/v1/core-adapter/inspect")
def inspect_run(b:RunRequest):
 r=RUNS.get(b.run_id)
 if not r:raise HTTPException(404,"run not found")
 return {"ok":True,"run_id":r.run_id,"status":r.status,"operation":r.request.operation,"job_ref":r.request.job_ref,"environment_ref":r.request.environment_ref,"created_at":r.created_at,"started_at":r.started_at,"completed_at":r.completed_at,"error":r.error}
@app.post("/v1/core-adapter/collect-results")
def collect_results(b:RunRequest):
 r=RUNS.get(b.run_id)
 if not r:raise HTTPException(404,"run not found")
 return {"ok":True,"run_id":r.run_id,"status":r.status,"result":r.result}
@app.post("/v1/core-adapter/collect-artifacts")
def collect_artifacts(b:RunRequest):
 r=RUNS.get(b.run_id)
 if not r:raise HTTPException(404,"run not found")
 return {"ok":True,"run_id":r.run_id,"status":r.status,"artifacts":list((r.result or {}).get("artifacts") or [])}
@app.post("/v1/core-adapter/diagnose")
def diagnose(b:RunRequest):
 r=RUNS.get(b.run_id)
 if not r:raise HTTPException(404,"run not found")
 return {"ok":True,"run_id":r.run_id,"status":r.status,"runtime_ready":runtime_ready(),"error":r.error,"language_profile":OPERATION_LANGUAGE.get(r.request.operation)}
