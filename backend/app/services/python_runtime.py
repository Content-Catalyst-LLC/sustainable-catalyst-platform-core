from __future__ import annotations

import math
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, model_validator

from .computational_runtime_objects import canonical_sha256
from .reproducible_environment_packages import (
    EnvironmentAsset, EnvironmentAssetKind, EnvironmentBuildInstruction,
    EnvironmentPackageState, EnvironmentVariableDeclaration, EnvironmentVariableKind,
    PackageManager, PlatformArchitecture, PlatformDescriptor,
    ReproducibleEnvironmentPackage, RequirementSource,
    RuntimeEnvironmentRequirement, SystemPackageRequirement,
)
from .runtime_security_governance import (
    FilesystemAccessMode, IsolationMechanism, NetworkAccessMode, PackageInstallMode,
    RuntimeIsolationProfile, RuntimeSecurityPolicy,
)

CORE_RELEASE = "3.54.0"
CONTRACT_VERSION = "sc.core.python-runtime.v1"
PROVIDER_VERSION = "1.0.0"
PYTHON_VERSION = "3.12.3"
PYTHON_PACKAGE_CONSTRAINT = "3.12.3-*"
RUNTIME_ID = "sc-runtime-python"
ADAPTER_ID = "adapter:sc-runtime-python"
SERVICE_NAME = "sc-python-runtime"
SERVICE_ENDPOINT = "http://127.0.0.1:18103"

PYTHON_OPERATIONS = [
    "descriptive_summary",
    "linear_regression",
    "matrix_multiply",
    "standardize",
    "bootstrap_mean_ci",
    "token_frequency",
]

class PythonOperation(str, Enum):
    descriptive_summary = "descriptive_summary"
    linear_regression = "linear_regression"
    matrix_multiply = "matrix_multiply"
    standardize = "standardize"
    bootstrap_mean_ci = "bootstrap_mean_ci"
    token_frequency = "token_frequency"

class PythonExecutionState(str, Enum):
    declared="declared"; prepared="prepared"; running="running"; completed="completed"; failed="failed"; cancelled="cancelled"

def _finite_vector(values:list[float], name:str, min_len:int=1, max_len:int=262144)->None:
    if len(values)<min_len or len(values)>max_len: raise ValueError(f"{name} must contain {min_len}..{max_len} values")
    if any(not math.isfinite(float(x)) for x in values): raise ValueError(f"{name} values must be finite")

def _matrix_shape(matrix:list[list[float]], name:str)->tuple[int,int]:
    if not matrix or not matrix[0]: raise ValueError(f"{name} must be non-empty")
    r,c=len(matrix),len(matrix[0])
    if r>256 or c>256 or r*c>65536: raise ValueError(f"{name} exceeds bounded matrix size")
    if any(len(row)!=c for row in matrix): raise ValueError(f"{name} must be rectangular")
    if any(not math.isfinite(float(x)) for row in matrix for x in row): raise ValueError(f"{name} values must be finite")
    return r,c

class PythonInput(BaseModel):
    values:list[float]=Field(default_factory=list)
    x:list[float]=Field(default_factory=list)
    y:list[float]=Field(default_factory=list)
    matrix_a:list[list[float]]=Field(default_factory=list)
    matrix_b:list[list[float]]=Field(default_factory=list)
    iterations:int=1000
    confidence:float=0.95
    seed:int=0
    text:str=""
    top_k:int=20
    lowercase:bool=True
    metadata:dict[str,Any]=Field(default_factory=dict)

class PythonExecutionSettings(BaseModel):
    max_execution_seconds:int=Field(default=120,ge=1,le=1800)
    metadata:dict[str,Any]=Field(default_factory=dict)

class PythonExecutionRequest(BaseModel):
    python_request_id:str=Field(min_length=2,max_length=500)
    operation:PythonOperation
    inputs:PythonInput
    settings:PythonExecutionSettings=Field(default_factory=PythonExecutionSettings)
    computational_job_ref:str=Field(min_length=2,max_length=500)
    environment_package_ref:str="environment-package:python-runtime:v1"
    security_policy_ref:str="runtime-security-policy:python-runtime-standard:v1"
    provenance:dict[str,Any]=Field(default_factory=dict)
    metadata:dict[str,Any]=Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_request(self):
        i=self.inputs; op=self.operation
        if op in {PythonOperation.descriptive_summary,PythonOperation.standardize,PythonOperation.bootstrap_mean_ci}:
            _finite_vector(i.values,"values",1)
        if op==PythonOperation.linear_regression:
            _finite_vector(i.x,"x",2); _finite_vector(i.y,"y",2)
            if len(i.x)!=len(i.y): raise ValueError("linear_regression requires equal x/y lengths")
            mx=sum(i.x)/len(i.x)
            if sum((v-mx)**2 for v in i.x)==0: raise ValueError("linear_regression requires non-zero x variance")
        elif op==PythonOperation.matrix_multiply:
            ar,ac=_matrix_shape(i.matrix_a,"matrix_a"); br,bc=_matrix_shape(i.matrix_b,"matrix_b")
            if ac!=br: raise ValueError("matrix_multiply requires matrix_a columns == matrix_b rows")
            if ar*bc>65536: raise ValueError("matrix_multiply output exceeds 65536 elements")
        elif op==PythonOperation.standardize:
            if len(i.values)<2: raise ValueError("standardize requires at least two values")
            m=sum(i.values)/len(i.values)
            if sum((v-m)**2 for v in i.values)==0: raise ValueError("standardize requires non-zero variance")
        elif op==PythonOperation.bootstrap_mean_ci:
            if not 100<=i.iterations<=10000: raise ValueError("bootstrap iterations must be 100..10000")
            if not 0.5<=i.confidence<1.0: raise ValueError("bootstrap confidence must be in [0.5,1.0)")
            if not -(2**63)<=i.seed<2**63: raise ValueError("seed must fit signed 64-bit range")
        elif op==PythonOperation.token_frequency:
            size=len(i.text.encode('utf-8'))
            if size<1 or size>1_048_576: raise ValueError("token_frequency text must be 1..1048576 UTF-8 bytes")
            if not 1<=i.top_k<=1000: raise ValueError("token_frequency top_k must be 1..1000")
        return self

    def fingerprint(self)->str: return canonical_sha256(self)

class PythonExecutionResultContract(BaseModel):
    result_contract_id:str=Field(min_length=2,max_length=500)
    python_request_ref:str=Field(min_length=2,max_length=500)
    operation:PythonOperation
    expected_artifact_kinds:list[str]=Field(default_factory=list)
    expected_result_kinds:list[str]=Field(default_factory=list)
    state:PythonExecutionState=PythonExecutionState.declared
    metadata:dict[str,Any]=Field(default_factory=dict)
    @model_validator(mode="after")
    def validate_contract(self):
        if not self.expected_artifact_kinds and not self.expected_result_kinds: raise ValueError("Python result contract requires outputs")
        if len(self.expected_artifact_kinds)!=len(set(self.expected_artifact_kinds)): raise ValueError("duplicate artifact kinds")
        if len(self.expected_result_kinds)!=len(set(self.expected_result_kinds)): raise ValueError("duplicate result kinds")
        return self
    def fingerprint(self)->str:
        p=self.model_dump(mode="json",exclude_none=True); p.pop("state",None); return canonical_sha256(p)

class PythonRuntimeRegistration(BaseModel):
    registration_id:str=Field(min_length=2,max_length=500)
    runtime_id:str=RUNTIME_ID
    provider_version:str=PROVIDER_VERSION
    python_version:str=PYTHON_VERSION
    python_package_constraint:str=PYTHON_PACKAGE_CONSTRAINT
    adapter_id:str=ADAPTER_ID
    service_name:str=SERVICE_NAME
    endpoint:str=SERVICE_ENDPOINT
    operations:list[str]=Field(default_factory=lambda:list(PYTHON_OPERATIONS))
    runtime_contract:str=CONTRACT_VERSION
    runtime_kind:str="language"
    language:str="python"
    status:str="active"
    metadata:dict[str,Any]=Field(default_factory=dict)
    @model_validator(mode="after")
    def validate_registration(self):
        if self.runtime_id!=RUNTIME_ID or self.adapter_id!=ADAPTER_ID: raise ValueError("Python runtime identity mismatch")
        if self.provider_version!=PROVIDER_VERSION: raise ValueError("Python provider version mismatch")
        if set(self.operations)!=set(PYTHON_OPERATIONS) or len(self.operations)!=len(set(self.operations)): raise ValueError("Python operation set mismatch")
        return self
    def fingerprint(self)->str: return canonical_sha256(self)

class PythonRuntimeBundle(BaseModel):
    bundle_id:str=Field(min_length=2,max_length=500)
    registration:PythonRuntimeRegistration
    environment_package:ReproducibleEnvironmentPackage
    security_policy:RuntimeSecurityPolicy
    reference_request:PythonExecutionRequest
    result_contract:PythonExecutionResultContract
    source_object_refs:list[str]=Field(default_factory=list)
    metadata:dict[str,Any]=Field(default_factory=dict)
    @model_validator(mode="after")
    def validate_bundle(self):
        if self.reference_request.environment_package_ref!=self.environment_package.environment_package_id: raise ValueError("request/environment mismatch")
        if self.reference_request.security_policy_ref!=self.security_policy.security_policy_id: raise ValueError("request/security mismatch")
        if self.result_contract.python_request_ref!=self.reference_request.python_request_id: raise ValueError("result/request mismatch")
        if self.result_contract.operation!=self.reference_request.operation: raise ValueError("operation mismatch")
        return self
    def fingerprint(self)->str:
        return canonical_sha256({"bundle_id":self.bundle_id,"registration":self.registration.fingerprint(),"environment":self.environment_package.fingerprint(),"security":self.security_policy.fingerprint(),"request":self.reference_request.fingerprint(),"result_contract":self.result_contract.fingerprint(),"source_object_refs":sorted(self.source_object_refs),"metadata":self.metadata})

def reference_environment_package()->ReproducibleEnvironmentPackage:
    manifest=EnvironmentAsset(asset_id="environment-asset:python-runtime-manifest",kind=EnvironmentAssetKind.manifest,uri="core-ref://runtime-manifests/python-3.12.3-noble.json",content_sha256="3"*64,media_type="application/json",size_bytes=768)
    reqs=EnvironmentAsset(asset_id="environment-asset:python-provider-requirements",kind=EnvironmentAssetKind.lockfile,uri="core-ref://runtime-locks/python-provider-requirements.txt",content_sha256="4"*64,media_type="text/plain",size_bytes=256)
    return ReproducibleEnvironmentPackage(
        environment_package_id="environment-package:python-runtime:v1",name="Sustainable Catalyst Python Runtime Environment",package_version="1.0.0",
        platform=PlatformDescriptor(operating_system="Ubuntu",operating_system_version="24.04",architecture=PlatformArchitecture.amd64,libc="glibc",kernel_family="linux"),
        runtimes=[RuntimeEnvironmentRequirement(runtime_requirement_id="runtime-requirement:python-provider",runtime_ref=RUNTIME_ID,runtime_version=PROVIDER_VERSION,runtime_adapter_ref=ADAPTER_ID)],
        system_packages=[SystemPackageRequirement(requirement_id="system-package:python3.12",manager=PackageManager.apt,name="python3.12",version=PYTHON_PACKAGE_CONSTRAINT,source=RequirementSource.operating_system),SystemPackageRequirement(requirement_id="system-package:python3.12-venv",manager=PackageManager.apt,name="python3.12-venv",version=PYTHON_PACKAGE_CONSTRAINT,source=RequirementSource.operating_system)],
        language_packages=[],
        environment_variables=[EnvironmentVariableDeclaration(variable_id="environment-variable:python-artifact-root",name="SC_PYTHON_ARTIFACT_ROOT",kind=EnvironmentVariableKind.path,value="/var/lib/sc-python-runtime/artifacts"),EnvironmentVariableDeclaration(variable_id="environment-variable:python-work-root",name="SC_PYTHON_WORK_ROOT",kind=EnvironmentVariableKind.path,value="/var/lib/sc-python-runtime/work")],
        assets=[manifest,reqs],
        build_instructions=[EnvironmentBuildInstruction(instruction_id="build-instruction:python-system-runtime",ordinal=1,action="install-python3.12-and-venv",manager=PackageManager.apt,requirement_refs=["system-package:python3.12","system-package:python3.12-venv"]),EnvironmentBuildInstruction(instruction_id="build-instruction:python-provider",ordinal=2,action="create-provider-venv-and-install-api-dependencies",manager=PackageManager.pip,artifact_ref=reqs.asset_id),EnvironmentBuildInstruction(instruction_id="build-instruction:python-smoke",ordinal=3,action="run-isolated-bounded-python-smoke-tests")],
        source_environment_ref="runtime-environment:python-provider:v1",source_job_refs=[],source_workflow_refs=[],state=EnvironmentPackageState.verified,
        provenance={"source_release":CORE_RELEASE,"core_builds_environment":False,"execution_host_builds_environment":True},
        metadata={"python_version":PYTHON_VERSION,"python_package_constraint":PYTHON_PACKAGE_CONSTRAINT,"provider_version":PROVIDER_VERSION,"arbitrary_python_code":False,"isolated_mode":True,"site_imports_disabled_for_jobs":True,"runtime_package_install":False},
    )

def reference_security_policy()->RuntimeSecurityPolicy:
    isolation=RuntimeIsolationProfile(isolation_profile_id="isolation-profile:python-runtime-standard:v1",mechanism=IsolationMechanism.process,network_mode=NetworkAccessMode.none,filesystem_mode=FilesystemAccessMode.allowlist,package_install_mode=PackageInstallMode.denied,process_namespace_isolated=True,user_namespace_isolated=True,privilege_escalation_allowed=False,host_filesystem_mounted=False,shell_allowed=False,arbitrary_code_allowed=False,outbound_artifact_egress_allowed=True,resource_budget_ref="resource-budget:python-runtime-standard:v1",syscall_policy_ref="syscall-policy:python-runtime-standard:v1")
    return RuntimeSecurityPolicy(security_policy_id="runtime-security-policy:python-runtime-standard:v1",policy_version="1.0.0",name="Python Runtime Standard Policy",isolation_profile=isolation,allowed_runtime_refs=[RUNTIME_ID],allowed_adapter_refs=[ADAPTER_ID],allowed_operations={RUNTIME_ID:list(PYTHON_OPERATIONS)},allowed_filesystem_prefixes=["/workspace","/tmp/sc-python-runtime","/var/lib/sc-python-runtime/artifacts","/var/lib/sc-python-runtime/work"],allowed_artifact_egress_classes=["research-artifact","python-result","python-diagnostics"],execution_policy_ref="execution-policy:python-runtime-standard:v1",provenance={"source_release":CORE_RELEASE,"policy_owner":"platform-governance"},metadata={"arbitrary_python_source_allowed":False,"runtime_package_install_allowed":False,"caller_filesystem_paths_allowed":False,"provider_managed_execution":True,"isolated_python_jobs":True})

def reference_runtime_bundle()->PythonRuntimeBundle:
    req=PythonExecutionRequest(python_request_id="python-request:reference-descriptive-summary:001",operation=PythonOperation.descriptive_summary,inputs=PythonInput(values=[1.0,2.0,3.0,4.0,5.0]),computational_job_ref="job:python-reference-descriptive-summary:001",provenance={"originating_product":"research-lab","execution_owner":"workspace-or-execution-host"})
    result=PythonExecutionResultContract(result_contract_id="python-result-contract:reference-descriptive-summary:001",python_request_ref=req.python_request_id,operation=req.operation,expected_artifact_kinds=["python-source","python-input-json","python-stdout-log","python-stderr-log","python-result-json"],expected_result_kinds=["descriptive-statistics","python-diagnostics"],metadata={"expected_mean":3.0,"scientific_validity_certified":False})
    return PythonRuntimeBundle(bundle_id="python-runtime-bundle:reference:v1",registration=PythonRuntimeRegistration(registration_id="python-runtime-registration:v1",metadata={"system_python":"/usr/bin/python3.12","job_flags":["-I","-S"],"arbitrary_python_code":False,"provider_managed_execution":True}),environment_package=reference_environment_package(),security_policy=reference_security_policy(),reference_request=req,result_contract=result,source_object_refs=["go-runtime-bundle:reference:v1","unified-runtime-catalog:platform-core:v1"],metadata={"reference_is_contract_proof":True,"live_provider_execution_occurs_outside_core":True,"existing_core_python_implementation_remains_internal":True})

def to_scientific_python_artifact(bundle:PythonRuntimeBundle)->dict[str,Any]:
    return {"artifact_id":f"scientific-artifact:{bundle.bundle_id}","artifact_kind":"package","uri":f"core-ref://{bundle.bundle_id}","content_sha256":bundle.fingerprint(),"media_type":"application/vnd.sustainable-catalyst.python-runtime+json","source_contract":CONTRACT_VERSION,"source_object_ref":bundle.bundle_id,"metadata":{"runtime_id":bundle.registration.runtime_id,"provider_version":bundle.registration.provider_version,"python_version":bundle.registration.python_version,"reference_operation":bundle.reference_request.operation.value}}

def contract_document()->dict[str,Any]:
    b=reference_runtime_bundle()
    return {"ok":True,"release":CORE_RELEASE,"contract":CONTRACT_VERSION,"provider_version":PROVIDER_VERSION,"python_version":PYTHON_VERSION,"python_package_constraint":PYTHON_PACKAGE_CONSTRAINT,"runtime_id":RUNTIME_ID,"adapter_id":ADAPTER_ID,"language":"python","operations":list(PYTHON_OPERATIONS),"capabilities":{"general_scientific":True,"data_analysis":True,"descriptive_statistics":True,"regression":True,"matrix_compute":True,"reproducible_randomness":True,"text_analysis":True,"provider_managed_execution":True,"reproducible_environment_package":True,"runtime_security_policy":True,"runtime_adapter_registration":True,"unified_runtime_catalog_integration":True,"workspace_product_profile_integration":True,"research_lab_product_profile_integration":True,"workbench_product_profile_integration":True,"scientific_registry_bridge":True},"boundaries":{"core_executes_python_jobs":False,"provider_executes_python_jobs":True,"arbitrary_python_source":False,"shell_execution":False,"runtime_package_install_via_api":False,"caller_filesystem_paths":False,"network_access_for_jobs":False,"core_selects_algorithm":False,"core_certifies_numerical_validity":False,"core_certifies_scientific_validity":False},"reference":{"bundle_id":b.bundle_id,"environment_package_id":b.environment_package.environment_package_id,"security_policy_id":b.security_policy.security_policy_id,"reference_request_id":b.reference_request.python_request_id,"reference_operation":b.reference_request.operation.value,"bundle_fingerprint_sha256":b.fingerprint()}}
