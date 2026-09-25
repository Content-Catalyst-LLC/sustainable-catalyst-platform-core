from __future__ import annotations
from datetime import datetime, timezone
from typing import Any, Literal
from pydantic import BaseModel, Field, model_validator
from .computational_job_runtime import ComputationalJob, build_dispatch_envelope, CONTRACT_VERSION as JOB_CONTRACT_VERSION
from .computational_runtime_objects import ExecutionResult, ExecutionState, RuntimeEnvironment, canonical_sha256
from .execution_environment_provenance import ExecutionEnvironmentProvenance, ReproducibilityStatus
from .runtime_adapter_registry import ADAPTER_CONTRACT_VERSION, REQUIRED_ADAPTER_METHODS

CORE_RELEASE='3.26.0'
CONTRACT_VERSION='sc.core.julia-runtime-integration.v1'
RUNTIME_ID='catalyst-julia-runtime'
ADAPTER_ID='adapter:catalyst-julia-runtime'
PROVIDER_VERSION='0.3.0'
EXECUTION_CONTRACT_VERSION='sc.execution.v1'
ENVIRONMENT_CONTRACT_VERSION='sc.environment.v1'
ALLOWLISTED_OPERATIONS=('identity','sum','mean','matrix_multiply')

class JuliaRuntimeRegistration(BaseModel):
    adapter_id:str=ADAPTER_ID
    runtime_id:str=RUNTIME_ID
    provider_version:str=PROVIDER_VERSION
    adapter_contract:str=ADAPTER_CONTRACT_VERSION
    job_contract:str=JOB_CONTRACT_VERSION
    execution_contract:str=EXECUTION_CONTRACT_VERSION
    environment_contract:str=ENVIRONMENT_CONTRACT_VERSION
    integration_contract:str=CONTRACT_VERSION
    service_name:str=RUNTIME_ID
    transport:Literal['http']='http'
    endpoint:str='http://127.0.0.1:18093'
    status:Literal['registered']='registered'
    execution_host:str='contabo-vps'
    required_methods:list[str]=Field(default_factory=lambda:list(REQUIRED_ADAPTER_METHODS))
    operations:list[str]=Field(default_factory=lambda:list(ALLOWLISTED_OPERATIONS))
    arbitrary_code_execution:bool=False
    shell_execution:bool=False
    package_installation:bool=False
    metadata:dict[str,Any]=Field(default_factory=dict)
    @model_validator(mode='after')
    def check(self):
        if self.adapter_id!=ADAPTER_ID or self.runtime_id!=RUNTIME_ID or self.provider_version!=PROVIDER_VERSION: raise ValueError('Julia registration identity mismatch')
        missing=[m for m in REQUIRED_ADAPTER_METHODS if m not in self.required_methods]
        if missing: raise ValueError('missing required methods: '+', '.join(missing))
        bad=[op for op in self.operations if op not in ALLOWLISTED_OPERATIONS]
        if bad: raise ValueError('unsupported operations: '+', '.join(bad))
        if self.arbitrary_code_execution or self.shell_execution or self.package_installation: raise ValueError('Julia security boundaries must remain disabled')
        return self
    def fingerprint(self)->str: return canonical_sha256(self)

class JuliaRuntimeHandshake(BaseModel):
    adapter_id:str; adapter_contract:str; runtime_id:str; provider_version:str; runtime_version:str; status:str
    methods:list[str]=Field(default_factory=list); operations:list[str]=Field(default_factory=list)
    execution_contract:str; environment_contract:str
    environment_fingerprint_sha256:str|None=Field(default=None,pattern=r'^[0-9a-f]{64}$')
    arbitrary_code_execution:bool=False; shell_execution:bool=False; package_installation:bool=False
    observed_at:datetime=Field(default_factory=lambda:datetime.now(timezone.utc))
    metadata:dict[str,Any]=Field(default_factory=dict)

class JuliaHandshakeReport(BaseModel):
    ok:bool; expected_registration_fingerprint_sha256:str
    mismatches:list[dict[str,Any]]=Field(default_factory=list)
    observed_environment_fingerprint_sha256:str|None=None

class JuliaExecutionRequest(BaseModel):
    request_id:str; runtime_id:str=RUNTIME_ID; operation:str
    inputs:dict[str,Any]=Field(default_factory=dict); parameters:dict[str,Any]=Field(default_factory=dict)
    expected_environment_fingerprint_sha256:str|None=Field(default=None,pattern=r'^[0-9a-f]{64}$')
    provenance:dict[str,Any]=Field(default_factory=dict)
    @model_validator(mode='after')
    def check(self):
        if self.runtime_id!=RUNTIME_ID: raise ValueError('runtime_id mismatch')
        if self.operation not in ALLOWLISTED_OPERATIONS: raise ValueError('operation is not allowlisted')
        return self

class JuliaExecutionRunPayload(BaseModel):
    run_id:str; request_id:str; runtime_id:str; state:ExecutionState
    external_execution_ref:str|None=None; started_at:datetime|None=None; finished_at:datetime|None=None; elapsed_ms:float|None=None
    environment_fingerprint_sha256:str|None=Field(default=None,pattern=r'^[0-9a-f]{64}$')
    diagnostics:list[dict[str,Any]]=Field(default_factory=list)

class JuliaExecutionResultPayload(BaseModel):
    result_id:str; run_id:str; request_id:str; runtime_id:str; state:ExecutionState
    environment_fingerprint_sha256:str|None=Field(default=None,pattern=r'^[0-9a-f]{64}$')
    scalar_result:Any=None; structured_result:Any=None; artifact_refs:list[str]=Field(default_factory=list)
    diagnostics:list[dict[str,Any]]=Field(default_factory=list); provenance:dict[str,Any]=Field(default_factory=dict)
    completed_at:datetime|None=None; metadata:dict[str,Any]=Field(default_factory=dict)

class JuliaExecutionResponse(BaseModel):
    ok:bool; adapter_contract:str; run:JuliaExecutionRunPayload; result:JuliaExecutionResultPayload
    @model_validator(mode='after')
    def check(self):
        if self.adapter_contract!=ADAPTER_CONTRACT_VERSION: raise ValueError('adapter contract mismatch')
        if self.run.runtime_id!=RUNTIME_ID or self.result.runtime_id!=RUNTIME_ID: raise ValueError('runtime identity mismatch')
        if self.result.request_id!=self.run.request_id or self.result.run_id!=self.run.run_id: raise ValueError('run/result identity mismatch')
        return self

class JuliaEnvironmentSnapshot(BaseModel):
    runtime_version:str; environment_fingerprint_sha256:str=Field(pattern=r'^[0-9a-f]{64}$')
    provider_version:str=PROVIDER_VERSION; platform:str|None=None; architecture:str|None=None; os_name:str|None=None; os_version:str|None=None
    project_hash_sha256:str|None=Field(default=None,pattern=r'^[0-9a-f]{64}$'); manifest_hash_sha256:str|None=Field(default=None,pattern=r'^[0-9a-f]{64}$')
    dependencies:list[dict[str,Any]]=Field(default_factory=list); metadata:dict[str,Any]=Field(default_factory=dict)

def reference_registration():
    return JuliaRuntimeRegistration(metadata={'native_core_adapter':True,'provider_release':'Catalyst Julia Runtime v0.3.0'})

def validate_handshake(h,registration=None):
    r=registration or reference_registration(); mm=[]
    for f,e,o in [('adapter_id',r.adapter_id,h.adapter_id),('adapter_contract',r.adapter_contract,h.adapter_contract),('runtime_id',r.runtime_id,h.runtime_id),('provider_version',r.provider_version,h.provider_version),('status',r.status,h.status),('execution_contract',r.execution_contract,h.execution_contract),('environment_contract',r.environment_contract,h.environment_contract),('arbitrary_code_execution',False,h.arbitrary_code_execution),('shell_execution',False,h.shell_execution),('package_installation',False,h.package_installation)]:
        if e!=o: mm.append({'field':f,'expected':e,'observed':o})
    missing=[m for m in r.required_methods if m not in h.methods]
    if missing: mm.append({'field':'methods','missing':missing,'expected':r.required_methods,'observed':h.methods})
    missing_ops=[op for op in r.operations if op not in h.operations]
    if missing_ops: mm.append({'field':'operations','missing':missing_ops,'expected':r.operations,'observed':h.operations})
    return JuliaHandshakeReport(ok=not mm,expected_registration_fingerprint_sha256=r.fingerprint(),mismatches=mm,observed_environment_fingerprint_sha256=h.environment_fingerprint_sha256)

def job_to_julia_request(job:ComputationalJob):
    if job.provider_binding.adapter_id!=ADAPTER_ID or job.provider_binding.runtime_id!=RUNTIME_ID: raise ValueError('job is not bound to Catalyst Julia Runtime')
    if job.provider_binding.provider_version not in (None,PROVIDER_VERSION): raise ValueError('provider version mismatch')
    e=build_dispatch_envelope(job)
    if not e.operation: raise ValueError('operation required')
    return JuliaExecutionRequest(request_id=e.request_id,runtime_id=e.runtime_id,operation=e.operation,inputs=e.inputs,parameters=e.parameters,expected_environment_fingerprint_sha256=e.expected_environment_fingerprint_sha256,provenance={**e.provenance,'core_release':CORE_RELEASE,'integration_contract':CONTRACT_VERSION,'adapter_id':ADAPTER_ID,'provider_version':PROVIDER_VERSION})

def normalize_julia_execution_response(response:JuliaExecutionResponse):
    r=response.result
    return ExecutionResult(result_id=r.result_id,run_id=r.run_id,request_id=r.request_id,runtime_id=r.runtime_id,state=r.state,environment_fingerprint_sha256=r.environment_fingerprint_sha256,scalar_result=r.scalar_result,structured_result=r.structured_result,artifact_refs=r.artifact_refs,diagnostics=r.diagnostics,provenance={**r.provenance,'normalized_by':CONTRACT_VERSION,'provider_version':PROVIDER_VERSION},completed_at=r.completed_at,metadata={**r.metadata,'adapter_id':ADAPTER_ID,'adapter_contract':ADAPTER_CONTRACT_VERSION})

def julia_environment_to_core(s:JuliaEnvironmentSnapshot):
    env=RuntimeEnvironment(environment_id=f'{RUNTIME_ID}:observed:{s.environment_fingerprint_sha256[:12]}',runtime_id=RUNTIME_ID,schema_version=ENVIRONMENT_CONTRACT_VERSION,runtime_version=s.runtime_version,platform=s.platform,architecture=s.architecture,os_name=s.os_name,os_version=s.os_version,project_hash_sha256=s.project_hash_sha256,manifest_hash_sha256=s.manifest_hash_sha256,metadata={'provider_version':s.provider_version,'adapter_id':ADAPTER_ID,'observed_environment_fingerprint_sha256':s.environment_fingerprint_sha256,**s.metadata})
    return ExecutionEnvironmentProvenance(provenance_id=f'envprov:{RUNTIME_ID}:{s.environment_fingerprint_sha256[:16]}',environment=env,capture_source='runtime-provider',reproducibility_status=ReproducibilityStatus.locked,provenance={'adapter_id':ADAPTER_ID,'provider_version':s.provider_version,'provider_environment_fingerprint_sha256':s.environment_fingerprint_sha256},metadata={'dependency_count_reported_by_provider':len(s.dependencies),'provider_dependencies_raw':s.dependencies})

def reference_handshake():
    return JuliaRuntimeHandshake(adapter_id=ADAPTER_ID,adapter_contract=ADAPTER_CONTRACT_VERSION,runtime_id=RUNTIME_ID,provider_version=PROVIDER_VERSION,runtime_version='1.13.0',status='registered',methods=list(REQUIRED_ADAPTER_METHODS),operations=list(ALLOWLISTED_OPERATIONS),execution_contract=EXECUTION_CONTRACT_VERSION,environment_contract=ENVIRONMENT_CONTRACT_VERSION,environment_fingerprint_sha256='a'*64)

def contract_document():
    r=reference_registration()
    return {'ok':True,'release':CORE_RELEASE,'contract':CONTRACT_VERSION,'registration':r.model_dump(mode='json',exclude_none=True),'integration_capabilities':{'provider_handshake_validation':True,'core_job_to_julia_request_mapping':True,'julia_response_normalization':True,'environment_snapshot_normalization':True,'environment_fingerprint_preservation':True,'capability_allowlist_enforcement':True},'boundaries':{'core_executes_julia_directly':False,'core_installs_julia_packages':False,'core_runs_shell_commands':False,'core_selects_scientific_method':False,'runtime_provider_owns_interpreter':True,'workspace_or_runtime_provider_dispatches':True}}
