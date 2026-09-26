from __future__ import annotations
import hashlib,json,math,os,subprocess,uuid
from dataclasses import dataclass,field
from datetime import datetime,timezone
from pathlib import Path
from typing import Any
from fastapi import FastAPI,HTTPException
from pydantic import BaseModel,Field,model_validator

PROVIDER_VERSION="1.0.0";JVM_MAJOR_VERSION=os.environ.get("SC_JVM_MAJOR_VERSION","21");JVM_IMPLEMENTATION="OpenJDK"
RUNTIME_ID="sc-runtime-jvm";ADAPTER_ID="adapter:sc-runtime-jvm";RUNTIME_CONTRACT="sc.core.jvm-runtime.v1";ADAPTER_CONTRACT="sc.core.runtime-adapter.v1"
HOST=os.environ.get("SC_JVM_RUNTIME_HOST","127.0.0.1");PORT=int(os.environ.get("SC_JVM_RUNTIME_PORT","18105"));JAVA=os.environ.get("SC_JAVA_BIN","/usr/bin/java");JAVAC=os.environ.get("SC_JAVAC_BIN","/usr/bin/javac")
ARTIFACT_ROOT=Path(os.environ.get("SC_JVM_ARTIFACT_ROOT","/var/lib/sc-jvm-runtime/artifacts"));WORK_ROOT=Path(os.environ.get("SC_JVM_WORK_ROOT","/var/lib/sc-jvm-runtime/work"))
OPERATIONS=["jvm_runtime_info","parallel_sum","parallel_map_affine","matrix_row_sums","graph_bfs","batch_sha256"];SAFE=set(OPERATIONS)

def now_iso():return datetime.now(timezone.utc).isoformat()
def number(v,name):
    if isinstance(v,bool) or not isinstance(v,(int,float)) or not math.isfinite(float(v)):raise ValueError(f"{name} must be finite numeric")
    return float(v)
def numbers(v,name,max_len=262144):
    if not isinstance(v,list) or not 1<=len(v)<=max_len:raise ValueError(f"{name} invalid length")
    return [number(x,name) for x in v]
def validate_payload(op,p):
    if op not in SAFE or not isinstance(p,dict):raise ValueError("unsupported JVM operation or payload")
    if op=="jvm_runtime_info":return {}
    if op in {"parallel_sum","parallel_map_affine"}:
        q={"values":numbers(p.get("values"),"values")}
        if op=="parallel_map_affine":q.update(scale=number(p.get("scale",1.0),"scale"),offset=number(p.get("offset",0.0),"offset"))
        return q
    if op=="matrix_row_sums":
        m=p.get("matrix")
        if not isinstance(m,list) or not m or not isinstance(m[0],list) or not m[0] or len(m)>2048 or len(m[0])>2048:raise ValueError("matrix invalid")
        w=len(m[0]);clean=[]
        for row in m:
            if not isinstance(row,list) or len(row)!=w:raise ValueError("matrix must be rectangular")
            clean.append([number(x,"matrix") for x in row])
        return {"matrix":clean}
    if op=="graph_bfs":
        m=p.get("adjacency_matrix");s=p.get("source_index")
        if not isinstance(m,list) or not m or len(m)>2048 or any(not isinstance(r,list) or len(r)!=len(m) for r in m):raise ValueError("adjacency_matrix must be square")
        if any(x not in (0,1) for r in m for x in r):raise ValueError("adjacency entries must be 0/1")
        if isinstance(s,bool) or not isinstance(s,int) or not 0<=s<len(m):raise ValueError("source_index invalid")
        return {"adjacency_matrix":m,"source_index":s}
    if op=="batch_sha256":
        ss=p.get("strings")
        if not isinstance(ss,list) or not 1<=len(ss)<=10000 or any(not isinstance(s,str) or len(s.encode())>65536 for s in ss):raise ValueError("strings invalid")
        return {"strings":ss}
    raise ValueError("unsupported operation")

def jstr(s):return json.dumps(s,ensure_ascii=False)
def jdouble(x):return repr(float(x))
def build_source(op,p):
    q=validate_payload(op,p)
    imports='import java.util.*; import java.security.*; import java.nio.charset.StandardCharsets;\n'
    helper='''static String esc(String s){return s.replace("\\\\","\\\\\\\\").replace("\\\"","\\\\\\\"");}\nstatic String darr(double[] a){StringBuilder b=new StringBuilder("[");for(int i=0;i<a.length;i++){if(i>0)b.append(',');b.append(Double.toString(a[i]));}return b.append(']').toString();}\nstatic String iarr(int[] a){StringBuilder b=new StringBuilder("[");for(int i=0;i<a.length;i++){if(i>0)b.append(',');b.append(Integer.toString(a[i]));}return b.append(']').toString();}\nstatic String sarr(String[] a){StringBuilder b=new StringBuilder("[");for(int i=0;i<a.length;i++){if(i>0)b.append(',');b.append('\\\"').append(esc(a[i])).append('\\\"');}return b.append(']').toString();}\n'''
    if op=="jvm_runtime_info":body='String v=System.getProperty("java.version");String vm=System.getProperty("java.vm.name");String vendor=System.getProperty("java.vendor");int p=Runtime.getRuntime().availableProcessors();System.out.println("{\\\"java_version\\\":\\\""+esc(v)+"\\\",\\\"vm_name\\\":\\\""+esc(vm)+"\\\",\\\"vendor\\\":\\\""+esc(vendor)+"\\\",\\\"available_processors\\\":"+p+"}");'
    elif op=="parallel_sum":
        vals=','.join(jdouble(x) for x in q['values']);body=f'double[] v=new double[]{{{vals}}};double r=Arrays.stream(v).parallel().sum();System.out.println("{{\\\"sum\\\":"+Double.toString(r)+"}}");'
    elif op=="parallel_map_affine":
        vals=','.join(jdouble(x) for x in q['values']);body=f'double[] v=new double[]{{{vals}}};double[] r=Arrays.stream(v).parallel().map(x->x*{jdouble(q["scale"])}+{jdouble(q["offset"])}).toArray();System.out.println("{{\\\"values\\\":"+darr(r)+"}}");'
    elif op=="matrix_row_sums":
        rows=','.join('new double[]{'+','.join(jdouble(x) for x in row)+'}' for row in q['matrix']);body=f'double[][] m=new double[][]{{{rows}}};double[] r=Arrays.stream(m).parallel().mapToDouble(row->Arrays.stream(row).sum()).toArray();System.out.println("{{\\\"row_sums\\\":"+darr(r)+"}}");'
    elif op=="graph_bfs":
        rows=','.join('new int[]{'+','.join(str(x) for x in row)+'}' for row in q['adjacency_matrix']);body=f'int[][] g=new int[][]{{{rows}}};int[] d=new int[g.length];Arrays.fill(d,-1);ArrayDeque<Integer> z=new ArrayDeque<>();d[{q["source_index"]}]=0;z.add({q["source_index"]});while(!z.isEmpty()){{int u=z.remove();for(int i=0;i<g.length;i++)if(g[u][i]!=0&&d[i]<0){{d[i]=d[u]+1;z.add(i);}}}}System.out.println("{{\\\"distances\\\":"+iarr(d)+"}}");'
    elif op=="batch_sha256":
        vals=','.join(jstr(x) for x in q['strings']);body=f'String[] xs=new String[]{{{vals}}};String[] out=new String[xs.length];for(int i=0;i<xs.length;i++){{MessageDigest md=MessageDigest.getInstance("SHA-256");byte[] h=md.digest(xs[i].getBytes(StandardCharsets.UTF_8));StringBuilder b=new StringBuilder();for(byte x:h)b.append(String.format("%02x",x));out[i]=b.toString();}}System.out.println("{{\\\"sha256\\\":"+sarr(out)+"}}");'
    else:raise ValueError("unsupported")
    return imports+'public class Main {\n'+helper+'public static void main(String[] args) throws Exception {'+body+'}\n}\n'

def native_version():
    cp=subprocess.run([JAVA,"-version"],capture_output=True,text=True,timeout=5);return (cp.stderr or cp.stdout).strip().splitlines()[0]
def javac_version():
    cp=subprocess.run([JAVAC,"-version"],capture_output=True,text=True,timeout=5);return (cp.stdout or cp.stderr).strip()
def execute_program(run_id,op,p,timeout,max_heap_mb=256):
    safe=run_id.replace(':','_');work=WORK_ROOT/safe;art=ARTIFACT_ROOT/safe;work.mkdir(parents=True,exist_ok=True);art.mkdir(parents=True,exist_ok=True)
    src=build_source(op,p);source=work/'Main.java';source.write_text(src)
    env={"PATH":"/usr/bin:/bin","HOME":str(work),"LANG":"C.UTF-8","LC_ALL":"C.UTF-8"}
    c=subprocess.run([JAVAC,"--release","21","-encoding","UTF-8",str(source)],capture_output=True,text=True,timeout=timeout,env=env,cwd=work)
    (art/'compile.stdout.txt').write_text(c.stdout);(art/'compile.stderr.txt').write_text(c.stderr);(art/'Main.java').write_text(src)
    if c.returncode!=0:raise RuntimeError((c.stderr or c.stdout or f"javac exit {c.returncode}").strip())
    r=subprocess.run([JAVA,f"-Xmx{max_heap_mb}m","-cp",str(work),"Main"],capture_output=True,text=True,timeout=timeout,env=env,cwd=work)
    (art/'run.stdout.txt').write_text(r.stdout);(art/'run.stderr.txt').write_text(r.stderr)
    if r.returncode!=0:raise RuntimeError((r.stderr or r.stdout or f"java exit {r.returncode}").strip())
    lines=[x for x in r.stdout.splitlines() if x.strip()]
    if not lines:raise RuntimeError("JVM produced no result")
    try:result=json.loads(lines[-1])
    except Exception as e:raise RuntimeError(f"invalid JVM JSON result: {e}: {r.stdout}")
    out={"runtime_id":RUNTIME_ID,"runtime_version":PROVIDER_VERSION,"jvm_major_version":JVM_MAJOR_VERSION,"operation":op,"result":result}
    rp=art/'result.json';rp.write_text(json.dumps(out,indent=2,sort_keys=True))
    artifacts=[]
    for kind,path in [("jvm-bootstrap-source",art/'Main.java'),("jvm-compile-stdout",art/'compile.stdout.txt'),("jvm-compile-stderr",art/'compile.stderr.txt'),("jvm-run-stdout",art/'run.stdout.txt'),("jvm-run-stderr",art/'run.stderr.txt'),("jvm-result",rp)]:artifacts.append({"artifact_kind":kind,"path":str(path),"content_sha256":hashlib.sha256(path.read_bytes()).hexdigest()})
    return out,artifacts

class PrepareRequest(BaseModel):
    operation:str;payload:dict[str,Any]=Field(default_factory=dict);timeout_seconds:int=Field(default=120,ge=1,le=1800);max_heap_mb:int=Field(default=256,ge=64,le=4096);job_ref:str|None=None;environment_ref:str|None=None
    @model_validator(mode="after")
    def valid(self):validate_payload(self.operation,self.payload);return self
class RunRequest(BaseModel):run_id:str
@dataclass
class RunRecord:
    run_id:str;request:PrepareRequest;status:str="prepared";created_at:str=field(default_factory=now_iso);started_at:str|None=None;completed_at:str|None=None;result:dict[str,Any]|None=None;artifacts:list[dict[str,Any]]=field(default_factory=list);error:str|None=None
RUNS={}
def adapter_descriptor():return {"adapter_id":ADAPTER_ID,"adapter_contract":ADAPTER_CONTRACT,"provider_id":RUNTIME_ID,"provider_version":PROVIDER_VERSION,"native_runtime":"OpenJDK JVM","native_runtime_version":JVM_MAJOR_VERSION,"runtime_kind":"execution-target","language":"jvm-bytecode","status":"registered","execution_state":"active","transport":"HTTP","endpoint":f"http://{HOST}:{PORT}","capabilities":OPERATIONS,"lifecycle_methods":["health","version","capabilities","prepare","execute","cancel","inspect","collect_results","collect_artifacts","diagnose"],"boundaries":{"arbitrary_jvm_bytecode":False,"arbitrary_java_source":False,"caller_classpath":False,"shell_execution":False,"runtime_dependency_install":False,"network_access":False,"provider_generated_bootstrap_java":True}}
app=FastAPI(title="Sustainable Catalyst JVM Runtime",version=PROVIDER_VERSION)
@app.get('/health')
def health():
    try:v=native_version();j=javac_version();ok=('version "21.' in v or 'version "21"' in v) and j.startswith('javac 21')
    except Exception:v='unavailable';j='unavailable';ok=False
    return {"ok":ok,"runtime_id":RUNTIME_ID,"version":PROVIDER_VERSION,"jvm_major_version":JVM_MAJOR_VERSION,"java_version_output":v,"javac_version_output":j,"capabilities":len(OPERATIONS)}
@app.get('/version')
def version():return {"runtime_id":RUNTIME_ID,"version":PROVIDER_VERSION,"jvm_major_version":JVM_MAJOR_VERSION,"java_version_output":native_version(),"javac_version_output":javac_version()}
@app.get('/capabilities')
def capabilities():return {"runtime_id":RUNTIME_ID,"operations":OPERATIONS}
@app.get('/v1/core-adapter')
def adapter():return adapter_descriptor()
@app.post('/v1/core-adapter/prepare')
def prepare(body:PrepareRequest):
    rid=f"jvm-run:{uuid.uuid4()}";RUNS[rid]=RunRecord(rid,body);return {"ok":True,"run_id":rid,"status":"prepared","operation":body.operation,"runtime_id":RUNTIME_ID,"runtime_version":PROVIDER_VERSION}
@app.post('/v1/core-adapter/execute')
def execute(body:RunRequest):
    rec=RUNS.get(body.run_id)
    if not rec:raise HTTPException(404,'run not found')
    if rec.status not in {'prepared','failed'}:raise HTTPException(409,'run not executable')
    rec.status='running';rec.started_at=now_iso()
    try:rec.result,rec.artifacts=execute_program(rec.run_id,rec.request.operation,rec.request.payload,rec.request.timeout_seconds,rec.request.max_heap_mb);rec.status='completed';rec.completed_at=now_iso();return {"ok":True,"run_id":rec.run_id,"status":rec.status,"result":rec.result}
    except Exception as e:rec.status='failed';rec.error=str(e);rec.completed_at=now_iso();raise HTTPException(500,str(e))
@app.post('/v1/core-adapter/cancel')
def cancel(body:RunRequest):
    rec=RUNS.get(body.run_id)
    if not rec:raise HTTPException(404,'run not found')
    if rec.status=='prepared':rec.status='cancelled';rec.completed_at=now_iso()
    return {"ok":True,"run_id":rec.run_id,"status":rec.status}
@app.post('/v1/core-adapter/inspect')
def inspect(body:RunRequest):
    rec=RUNS.get(body.run_id)
    if not rec:raise HTTPException(404,'run not found')
    return {"ok":True,"run_id":rec.run_id,"status":rec.status,"operation":rec.request.operation,"job_ref":rec.request.job_ref,"environment_ref":rec.request.environment_ref,"created_at":rec.created_at,"started_at":rec.started_at,"completed_at":rec.completed_at,"error":rec.error}
@app.post('/v1/core-adapter/collect_results')
def collect_results(body:RunRequest):
    rec=RUNS.get(body.run_id)
    if not rec:raise HTTPException(404,'run not found')
    return {"ok":True,"run_id":rec.run_id,"status":rec.status,"result":rec.result}
@app.post('/v1/core-adapter/collect_artifacts')
def collect_artifacts(body:RunRequest):
    rec=RUNS.get(body.run_id)
    if not rec:raise HTTPException(404,'run not found')
    return {"ok":True,"run_id":rec.run_id,"status":rec.status,"artifacts":rec.artifacts}
@app.post('/v1/core-adapter/diagnose')
def diagnose(body:RunRequest):
    rec=RUNS.get(body.run_id)
    if not rec:raise HTTPException(404,'run not found')
    return {"ok":True,"run_id":rec.run_id,"status":rec.status,"java_version_output":native_version(),"javac_version_output":javac_version(),"error":rec.error}
