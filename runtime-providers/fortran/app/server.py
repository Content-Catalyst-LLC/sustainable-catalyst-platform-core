from __future__ import annotations

import hashlib
import json
import math
import os
import subprocess
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field, model_validator

PROVIDER_VERSION = "1.0.0"
GFORTRAN_VERSION = os.environ.get("SC_FORTRAN_GFORTRAN_VERSION", "13.3.0")
GFORTRAN_PACKAGE_VERSION = os.environ.get("SC_FORTRAN_GFORTRAN_PACKAGE_VERSION", "13.3.0-6ubuntu2~24.04.1")
RUNTIME_ID = "sc-runtime-fortran"
ADAPTER_ID = "adapter:sc-runtime-fortran"
ADAPTER_CONTRACT = "sc.core.runtime-adapter.v1"
RUNTIME_CONTRACT = "sc.core.fortran-runtime.v1"
HOST = os.environ.get("SC_FORTRAN_RUNTIME_HOST", "127.0.0.1")
PORT = int(os.environ.get("SC_FORTRAN_RUNTIME_PORT", "18099"))
GFORTRAN_BIN = os.environ.get("SC_FORTRAN_GFORTRAN_BIN", "/usr/bin/gfortran-13")
ARTIFACT_ROOT = Path(os.environ.get("SC_FORTRAN_ARTIFACT_ROOT", "/var/lib/sc-fortran-runtime/artifacts"))
WORK_ROOT = Path(os.environ.get("SC_FORTRAN_WORK_ROOT", "/var/lib/sc-fortran-runtime/work"))
MAX_EXECUTION_SECONDS = int(os.environ.get("SC_FORTRAN_MAX_EXECUTION_SECONDS", "1800"))
MAX_VECTOR = int(os.environ.get("SC_FORTRAN_MAX_VECTOR", "262144"))
MAX_MATRIX_DIM = int(os.environ.get("SC_FORTRAN_MAX_MATRIX_DIM", "256"))

OPERATIONS = [
    "dot_product",
    "matrix_multiply",
    "trapezoidal_integral",
    "central_difference",
    "rk4_linear_step",
    "heat_step_1d",
]
SAFE_OPERATION = set(OPERATIONS)


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def compiler_ready() -> bool:
    try:
        p=subprocess.run([GFORTRAN_BIN,"-dumpfullversion"],capture_output=True,text=True,timeout=10)
        return p.returncode==0 and p.stdout.strip()==GFORTRAN_VERSION
    except Exception:
        return False


def file_sha256(path: Path) -> str:
    h=hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda:f.read(1024*1024),b''): h.update(chunk)
    return h.hexdigest()


def finite_number(value: Any, name: str) -> float:
    if isinstance(value,bool) or not isinstance(value,(int,float)):
        raise ValueError(f"{name} must be a finite number")
    value=float(value)
    if not math.isfinite(value): raise ValueError(f"{name} must be a finite number")
    return value


def finite_vector(values: Any, name: str, *, min_len: int=1) -> list[float]:
    if not isinstance(values,list) or len(values)<min_len or len(values)>MAX_VECTOR:
        raise ValueError(f"{name} length must be between {min_len} and {MAX_VECTOR}")
    return [finite_number(v,f"{name}[]") for v in values]


def finite_matrix(value: Any, name: str) -> list[list[float]]:
    if not isinstance(value,list) or not value or not isinstance(value[0],list) or not value[0]:
        raise ValueError(f"{name} must be a non-empty matrix")
    rows,cols=len(value),len(value[0])
    if rows>MAX_MATRIX_DIM or cols>MAX_MATRIX_DIM:
        raise ValueError(f"{name} dimensions exceed {MAX_MATRIX_DIM}x{MAX_MATRIX_DIM}")
    out=[]
    for row in value:
        if not isinstance(row,list) or len(row)!=cols: raise ValueError(f"{name} must be rectangular")
        out.append([finite_number(v,f"{name}[][]") for v in row])
    return out


def validate_payload(operation: str, payload: Any) -> dict[str,Any]:
    if operation not in SAFE_OPERATION: raise ValueError("unsupported Fortran operation")
    if not isinstance(payload,dict): raise ValueError("payload must be an object")
    if operation=="dot_product":
        a=finite_vector(payload.get("a"),"a"); b=finite_vector(payload.get("b"),"b")
        if len(a)!=len(b): raise ValueError("dot_product requires equal vector lengths")
        return {"a":a,"b":b}
    if operation=="matrix_multiply":
        a=finite_matrix(payload.get("a"),"a"); b=finite_matrix(payload.get("b"),"b")
        if len(a[0])!=len(b): raise ValueError("matrix_multiply dimension mismatch")
        if len(a)*len(b[0])>65536: raise ValueError("matrix_multiply output exceeds 65536 elements")
        return {"a":a,"b":b}
    if operation=="trapezoidal_integral":
        x=finite_vector(payload.get("x"),"x",min_len=2); y=finite_vector(payload.get("y"),"y",min_len=2)
        if len(x)!=len(y): raise ValueError("trapezoidal_integral requires equal x/y lengths")
        if any(x[i+1]<=x[i] for i in range(len(x)-1)): raise ValueError("x must be strictly increasing")
        return {"x":x,"y":y}
    if operation=="central_difference":
        x=finite_vector(payload.get("x"),"x",min_len=3); y=finite_vector(payload.get("y"),"y",min_len=3)
        if len(x)!=len(y): raise ValueError("central_difference requires equal x/y lengths")
        idx=payload.get("index")
        if isinstance(idx,bool) or not isinstance(idx,int) or idx<1 or idx>len(x)-2:
            raise ValueError("central_difference index must be an interior zero-based index")
        if x[idx+1]==x[idx-1]: raise ValueError("central_difference denominator cannot be zero")
        return {"x":x,"y":y,"index":idx}
    if operation=="rk4_linear_step":
        y=finite_number(payload.get("y"),"y"); h=finite_number(payload.get("h"),"h")
        a=finite_number(payload.get("a"),"a"); b=finite_number(payload.get("b"),"b")
        if h==0: raise ValueError("h cannot be zero")
        return {"y":y,"h":h,"a":a,"b":b}
    if operation=="heat_step_1d":
        u=finite_vector(payload.get("u"),"u",min_len=3); r=finite_number(payload.get("alpha_dt_dx2"),"alpha_dt_dx2")
        if r<0 or r>0.5: raise ValueError("alpha_dt_dx2 must be between 0 and 0.5")
        return {"u":u,"alpha_dt_dx2":r}
    raise ValueError("unsupported Fortran operation")


def f64(v: float) -> str:
    return f"{float(v):.17e}_real64"


def vec(name: str, values: list[float]) -> list[str]:
    return [f"  real(real64), dimension({len(values)}) :: {name}",
            f"  {name} = [{', '.join(f64(v) for v in values)}]"]


def matrix_assign(name: str, values: list[list[float]]) -> list[str]:
    rows,cols=len(values),len(values[0])
    lines=[f"  real(real64), dimension({rows},{cols}) :: {name}"]
    for i,row in enumerate(values,1):
        for j,v in enumerate(row,1): lines.append(f"  {name}({i},{j}) = {f64(v)}")
    return lines


def fortran_source(operation: str, payload: dict[str,Any]) -> str:
    p=validate_payload(operation,payload)
    head=["program sc_fortran_job","  use iso_fortran_env, only: real64","  implicit none"]
    decl=[]
    body=[]
    if operation=="dot_product":
        decl=[f"  real(real64), dimension({len(p['a'])}) :: a, b","  real(real64) :: value"]
        body=[f"  a = [{', '.join(f64(v) for v in p['a'])}]",f"  b = [{', '.join(f64(v) for v in p['b'])}]","  value = dot_product(a,b)","  write(*,'(A,1X,ES24.16E3)') 'SC_RESULT scalar', value"]
    elif operation=="matrix_multiply":
        a,b=p['a'],p['b']; m,k,n=len(a),len(a[0]),len(b[0])
        decl=[f"  real(real64), dimension({m},{k}) :: a",f"  real(real64), dimension({k},{n}) :: b",f"  real(real64), dimension({m},{n}) :: c","  integer :: i, j"]
        for i,row in enumerate(a,1):
            for j,v in enumerate(row,1): body.append(f"  a({i},{j}) = {f64(v)}")
        for i,row in enumerate(b,1):
            for j,v in enumerate(row,1): body.append(f"  b({i},{j}) = {f64(v)}")
        body += ["  c = matmul(a,b)",f"  write(*,'(A,1X,I0,1X,I0)') 'SC_RESULT matrix', {m}, {n}",f"  do i=1,{m}",f"    do j=1,{n}","      write(*,'(ES24.16E3)') c(i,j)","    end do","  end do"]
    elif operation=="trapezoidal_integral":
        n=len(p['x']); decl=[f"  real(real64), dimension({n}) :: x, y","  real(real64) :: value","  integer :: i"]
        body=[f"  x = [{', '.join(f64(v) for v in p['x'])}]",f"  y = [{', '.join(f64(v) for v in p['y'])}]","  value = 0.0_real64",f"  do i=1,{n-1}","    value = value + 0.5_real64*(x(i+1)-x(i))*(y(i+1)+y(i))","  end do","  write(*,'(A,1X,ES24.16E3)') 'SC_RESULT scalar', value"]
    elif operation=="central_difference":
        n=len(p['x']); fi=p['index']+1; decl=[f"  real(real64), dimension({n}) :: x, y","  real(real64) :: value"]
        body=[f"  x = [{', '.join(f64(v) for v in p['x'])}]",f"  y = [{', '.join(f64(v) for v in p['y'])}]",f"  value = (y({fi+1})-y({fi-1}))/(x({fi+1})-x({fi-1}))","  write(*,'(A,1X,ES24.16E3)') 'SC_RESULT scalar', value"]
    elif operation=="rk4_linear_step":
        decl=["  real(real64) :: y, h, a, b, k1, k2, k3, k4, value"]
        body=[f"  y={f64(p['y'])}",f"  h={f64(p['h'])}",f"  a={f64(p['a'])}",f"  b={f64(p['b'])}","  k1 = a*y + b","  k2 = a*(y + 0.5_real64*h*k1) + b","  k3 = a*(y + 0.5_real64*h*k2) + b","  k4 = a*(y + h*k3) + b","  value = y + h*(k1 + 2.0_real64*k2 + 2.0_real64*k3 + k4)/6.0_real64","  write(*,'(A,1X,ES24.16E3)') 'SC_RESULT scalar', value"]
    elif operation=="heat_step_1d":
        n=len(p['u']); decl=[f"  real(real64), dimension({n}) :: u, next","  real(real64) :: r","  integer :: i"]
        body=[f"  u = [{', '.join(f64(v) for v in p['u'])}]",f"  r={f64(p['alpha_dt_dx2'])}","  next=u",f"  do i=2,{n-1}","    next(i)=u(i)+r*(u(i-1)-2.0_real64*u(i)+u(i+1))","  end do",f"  write(*,'(A,1X,I0)') 'SC_RESULT vector', {n}",f"  do i=1,{n}","    write(*,'(ES24.16E3)') next(i)","  end do"]
    else: raise ValueError("unsupported Fortran operation")
    return "\n".join(head+decl+body+["end program sc_fortran_job",""])


def parse_native_output(stdout: str) -> dict[str,Any]:
    lines=[x.strip() for x in stdout.splitlines() if x.strip()]
    for idx,line in enumerate(lines):
        if not line.startswith('SC_RESULT '): continue
        parts=line.split()
        kind=parts[1]
        if kind=='scalar': return {"kind":"scalar","value":float(parts[2])}
        if kind=='vector':
            n=int(parts[2]); vals=[float(x) for x in lines[idx+1:idx+1+n]]
            if len(vals)!=n: raise ValueError("incomplete native vector output")
            return {"kind":"vector","values":vals}
        if kind=='matrix':
            r,c=int(parts[2]),int(parts[3]); flat=[float(x) for x in lines[idx+1:idx+1+r*c]]
            if len(flat)!=r*c: raise ValueError("incomplete native matrix output")
            return {"kind":"matrix","rows":r,"cols":c,"values":[flat[i*c:(i+1)*c] for i in range(r)]}
    raise ValueError("Fortran execution returned no SC_RESULT marker")


def execute_fortran(*, operation: str, payload: dict[str,Any], timeout_seconds: int, optimization_level: int, run_id: str) -> dict[str,Any]:
    if not compiler_ready(): raise RuntimeError(f"GNU Fortran compiler is not ready at {GFORTRAN_BIN}")
    validated=validate_payload(operation,payload)
    ARTIFACT_ROOT.mkdir(parents=True,exist_ok=True); WORK_ROOT.mkdir(parents=True,exist_ok=True)
    safe=run_id.replace(':','_'); work=WORK_ROOT/safe; art=ARTIFACT_ROOT/safe
    work.mkdir(parents=True,exist_ok=True); art.mkdir(parents=True,exist_ok=True)
    source=art/'job.f90'; result_path=art/'result.json'; compile_log=art/'compile.log'; run_log=art/'run.log'; exe=work/'job.bin'
    source.write_text(fortran_source(operation,validated))
    cmd=[GFORTRAN_BIN,f'-O{optimization_level}','-std=f2008','-fno-unsafe-math-optimizations',str(source),'-o',str(exe)]
    started=time.monotonic(); cp=subprocess.run(cmd,capture_output=True,text=True,timeout=min(timeout_seconds,MAX_EXECUTION_SECONDS),cwd=str(work),env={"PATH":os.environ.get("PATH","/usr/bin:/bin"),"HOME":str(work),"LC_ALL":"C.UTF-8"})
    compile_log.write_text("COMMAND="+' '.join(cmd)+"\nRETURN_CODE="+str(cp.returncode)+"\nSTDOUT:\n"+(cp.stdout or '')+"\nSTDERR:\n"+(cp.stderr or ''))
    if cp.returncode!=0: raise RuntimeError((cp.stderr or cp.stdout or 'Fortran compilation failed').strip())
    rp=subprocess.run([str(exe)],capture_output=True,text=True,timeout=min(timeout_seconds,MAX_EXECUTION_SECONDS),cwd=str(work),env={"PATH":"/usr/bin:/bin","HOME":str(work),"LC_ALL":"C.UTF-8","OMP_NUM_THREADS":"1","OPENBLAS_NUM_THREADS":"1"})
    elapsed_ms=int((time.monotonic()-started)*1000)
    run_log.write_text("RETURN_CODE="+str(rp.returncode)+"\nSTDOUT:\n"+(rp.stdout or '')+"\nSTDERR:\n"+(rp.stderr or ''))
    try: exe.unlink()
    except Exception: pass
    if rp.returncode!=0: raise RuntimeError((rp.stderr or rp.stdout or 'Fortran execution failed').strip())
    native=parse_native_output(rp.stdout or '')
    result={"operation":operation,"elapsed_ms":elapsed_ms,"native_result":native,"source_sha256":file_sha256(source),"compile_log_sha256":file_sha256(compile_log),"run_log_sha256":file_sha256(run_log)}
    result_path.write_text(json.dumps(result,indent=2,sort_keys=True))
    return {**result,"artifacts":[
        {"artifact_kind":"fortran-generated-source","path":str(source),"content_sha256":file_sha256(source)},
        {"artifact_kind":"fortran-result-json","path":str(result_path),"content_sha256":file_sha256(result_path)},
        {"artifact_kind":"fortran-compile-log","path":str(compile_log),"content_sha256":file_sha256(compile_log)},
        {"artifact_kind":"fortran-run-log","path":str(run_log),"content_sha256":file_sha256(run_log)},
    ]}


class PrepareRequest(BaseModel):
    operation: str
    payload: dict[str,Any]
    timeout_seconds: int = Field(default=120, ge=1, le=1800)
    optimization_level: int = Field(default=2, ge=0, le=2)
    job_ref: str|None = Field(default=None,max_length=500)
    environment_ref: str|None = Field(default=None,max_length=1000)
    metadata: dict[str,Any] = Field(default_factory=dict)

    @model_validator(mode='after')
    def validate_request(self):
        validate_payload(self.operation,self.payload); return self

class RunRequest(BaseModel):
    run_id: str = Field(min_length=2,max_length=500)

@dataclass
class RunRecord:
    run_id: str
    request: PrepareRequest
    status: str='prepared'
    created_at: str=field(default_factory=now_iso)
    started_at: str|None=None
    completed_at: str|None=None
    result: dict[str,Any]|None=None
    error: str|None=None

RUNS: dict[str,RunRecord]={}

def adapter_descriptor() -> dict[str,Any]:
    return {"adapter_id":ADAPTER_ID,"adapter_contract":ADAPTER_CONTRACT,"provider_id":RUNTIME_ID,"provider_version":PROVIDER_VERSION,
            "native_runtime":"GNU Fortran","native_runtime_version":GFORTRAN_VERSION,"native_package_version":GFORTRAN_PACKAGE_VERSION,
            "runtime_kind":"language","language":"fortran","status":"registered","execution_state":"active" if compiler_ready() else "degraded",
            "transport":"HTTP","endpoint":f"http://{HOST}:{PORT}","capabilities":OPERATIONS,
            "lifecycle_methods":["health","version","capabilities","prepare","execute","cancel","inspect","collect_results","collect_artifacts","diagnose"],
            "boundaries":{"arbitrary_fortran_source":False,"shell_execution":False,"runtime_package_install":False,"caller_filesystem_paths":False,"provider_managed_compilation":True}}

app=FastAPI(title="Sustainable Catalyst Fortran Runtime",version=PROVIDER_VERSION)

@app.get('/health')
def health(): return {"ok":compiler_ready(),"runtime_id":RUNTIME_ID,"version":PROVIDER_VERSION,"gfortran_version":GFORTRAN_VERSION,"gfortran_package_version":GFORTRAN_PACKAGE_VERSION,"compiler_bin":GFORTRAN_BIN,"capabilities":len(OPERATIONS)}
@app.get('/version')
def version(): return {"runtime_id":RUNTIME_ID,"version":PROVIDER_VERSION,"gfortran_version":GFORTRAN_VERSION,"gfortran_package_version":GFORTRAN_PACKAGE_VERSION}
@app.get('/capabilities')
def capabilities(): return {"runtime_id":RUNTIME_ID,"version":PROVIDER_VERSION,"operations":OPERATIONS}
@app.get('/v1/core-adapter')
def core_adapter(): return adapter_descriptor()
@app.post('/v1/core-adapter/prepare')
def prepare(body:PrepareRequest):
    run_id=f"fortran-run:{uuid.uuid4()}"; RUNS[run_id]=RunRecord(run_id=run_id,request=body)
    return {"ok":True,"run_id":run_id,"status":"prepared","operation":body.operation,"runtime_id":RUNTIME_ID,"runtime_version":PROVIDER_VERSION}
@app.post('/v1/core-adapter/execute')
def execute(body:RunRequest):
    r=RUNS.get(body.run_id)
    if r is None: raise HTTPException(status_code=404,detail='run not found')
    if r.status=='cancelled': raise HTTPException(status_code=409,detail='run is cancelled')
    if r.status=='completed': return {"ok":True,"run_id":r.run_id,"status":r.status,"result":r.result}
    r.status='running'; r.started_at=now_iso()
    try:
        r.result=execute_fortran(operation=r.request.operation,payload=r.request.payload,timeout_seconds=r.request.timeout_seconds,optimization_level=r.request.optimization_level,run_id=r.run_id)
        r.status='completed'; r.completed_at=now_iso(); return {"ok":True,"run_id":r.run_id,"status":r.status,"runtime_id":RUNTIME_ID,"runtime_version":PROVIDER_VERSION,"result":r.result}
    except subprocess.TimeoutExpired:
        r.status='failed'; r.error='Fortran compilation or execution timed out'; r.completed_at=now_iso(); raise HTTPException(status_code=504,detail=r.error)
    except Exception as exc:
        r.status='failed'; r.error=str(exc); r.completed_at=now_iso(); raise HTTPException(status_code=500,detail=r.error)
@app.post('/v1/core-adapter/cancel')
def cancel(body:RunRequest):
    r=RUNS.get(body.run_id)
    if r is None: raise HTTPException(status_code=404,detail='run not found')
    if r.status=='running': raise HTTPException(status_code=409,detail='v1 synchronous provider cannot interrupt an already-running process')
    if r.status in {'completed','failed'}: return {"ok":True,"run_id":r.run_id,"status":r.status}
    r.status='cancelled'; r.completed_at=now_iso(); return {"ok":True,"run_id":r.run_id,"status":r.status}
@app.post('/v1/core-adapter/inspect')
def inspect(body:RunRequest):
    r=RUNS.get(body.run_id)
    if r is None: raise HTTPException(status_code=404,detail='run not found')
    return {"ok":True,"run_id":r.run_id,"status":r.status,"operation":r.request.operation,"job_ref":r.request.job_ref,"environment_ref":r.request.environment_ref,"created_at":r.created_at,"started_at":r.started_at,"completed_at":r.completed_at,"error":r.error}
@app.post('/v1/core-adapter/collect-results')
def collect_results(body:RunRequest):
    r=RUNS.get(body.run_id)
    if r is None: raise HTTPException(status_code=404,detail='run not found')
    return {"ok":True,"run_id":r.run_id,"status":r.status,"result":r.result}
@app.post('/v1/core-adapter/collect-artifacts')
def collect_artifacts(body:RunRequest):
    r=RUNS.get(body.run_id)
    if r is None: raise HTTPException(status_code=404,detail='run not found')
    return {"ok":True,"run_id":r.run_id,"status":r.status,"artifacts":list((r.result or {}).get('artifacts') or [])}
@app.post('/v1/core-adapter/diagnose')
def diagnose(body:RunRequest):
    r=RUNS.get(body.run_id)
    if r is None: raise HTTPException(status_code=404,detail='run not found')
    return {"ok":True,"run_id":r.run_id,"status":r.status,"runtime_ready":compiler_ready(),"error":r.error,"native_result":(r.result or {}).get('native_result')}
