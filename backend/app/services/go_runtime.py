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

CORE_RELEASE = "3.53.0"
CONTRACT_VERSION = "sc.core.go-runtime.v1"
PROVIDER_VERSION = "1.0.0"
GO_VERSION = "1.22.2"
GO_PACKAGE_VERSION = "1.22.2-2ubuntu0.4"
RUNTIME_ID = "sc-runtime-go"
ADAPTER_ID = "adapter:sc-runtime-go"
SERVICE_NAME = "sc-go-runtime"
SERVICE_ENDPOINT = "http://127.0.0.1:18102"

GO_OPERATIONS = [
    "parallel_sum",
    "parallel_map_affine",
    "concurrent_histogram",
    "parallel_matrix_row_sums",
    "parallel_graph_degrees",
    "batch_sha256",
]

class GoOperation(str, Enum):
    parallel_sum = "parallel_sum"
    parallel_map_affine = "parallel_map_affine"
    concurrent_histogram = "concurrent_histogram"
    parallel_matrix_row_sums = "parallel_matrix_row_sums"
    parallel_graph_degrees = "parallel_graph_degrees"
    batch_sha256 = "batch_sha256"

class GoExecutionState(str, Enum):
    declared="declared"; prepared="prepared"; running="running"; completed="completed"; failed="failed"; cancelled="cancelled"

def _finite_vector(values:list[float], name:str, max_len:int=262144)->None:
    if not values or len(values)>max_len: raise ValueError(f"{name} must contain 1..{max_len} values")
    if any(not math.isfinite(float(x)) for x in values): raise ValueError(f"{name} values must be finite")

def _matrix_shape(matrix:list[list[float]], name:str)->tuple[int,int]:
    if not matrix or not matrix[0]: raise ValueError(f"{name} must be non-empty")
    r,c=len(matrix),len(matrix[0])
    if r>4096 or c>4096 or r*c>262144: raise ValueError(f"{name} exceeds bounded matrix size")
    if any(len(row)!=c for row in matrix): raise ValueError(f"{name} must be rectangular")
    if any(not math.isfinite(float(x)) for row in matrix for x in row): raise ValueError(f"{name} values must be finite")
    return r,c

class GoInput(BaseModel):
    values:list[float]=Field(default_factory=list)
    scale:float=1.0
    offset:float=0.0
    bins:int|None=None
    minimum:float|None=None
    maximum:float|None=None
    matrix:list[list[float]]=Field(default_factory=list)
    adjacency_matrix:list[list[int]]=Field(default_factory=list)
    texts:list[str]=Field(default_factory=list)
    workers:int=4
    metadata:dict[str,Any]=Field(default_factory=dict)

class GoExecutionSettings(BaseModel):
    max_execution_seconds:int=Field(default=120,ge=1,le=1800)
    workers:int=Field(default=4,ge=1,le=64)
    metadata:dict[str,Any]=Field(default_factory=dict)

class GoExecutionRequest(BaseModel):
    go_request_id:str=Field(min_length=2,max_length=500)
    operation:GoOperation
    inputs:GoInput
    settings:GoExecutionSettings=Field(default_factory=GoExecutionSettings)
    computational_job_ref:str=Field(min_length=2,max_length=500)
    environment_package_ref:str="environment-package:go-runtime:v1"
    security_policy_ref:str="runtime-security-policy:go-runtime-standard:v1"
    provenance:dict[str,Any]=Field(default_factory=dict)
    metadata:dict[str,Any]=Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_request(self):
        i=self.inputs; op=self.operation
        if op in {GoOperation.parallel_sum,GoOperation.parallel_map_affine,GoOperation.concurrent_histogram}:
            _finite_vector(i.values,"values")
        if op==GoOperation.parallel_map_affine:
            if not math.isfinite(i.scale) or not math.isfinite(i.offset): raise ValueError("scale and offset must be finite")
        elif op==GoOperation.concurrent_histogram:
            if i.bins is None or not 1<=i.bins<=4096: raise ValueError("bins must be 1..4096")
            if i.minimum is None or i.maximum is None or not math.isfinite(i.minimum) or not math.isfinite(i.maximum) or i.maximum<=i.minimum:
                raise ValueError("histogram minimum/maximum are invalid")
        elif op==GoOperation.parallel_matrix_row_sums:
            _matrix_shape(i.matrix,"matrix")
        elif op==GoOperation.parallel_graph_degrees:
            r,c=_matrix_shape([[float(x) for x in row] for row in i.adjacency_matrix],"adjacency_matrix")
            if r!=c or r>2048: raise ValueError("adjacency_matrix must be square and <=2048 vertices")
            if any(x not in {0,1} for row in i.adjacency_matrix for x in row): raise ValueError("adjacency_matrix values must be 0 or 1")
        elif op==GoOperation.batch_sha256:
            if not i.texts or len(i.texts)>65536: raise ValueError("batch_sha256 requires 1..65536 texts")
            if sum(len(x.encode('utf-8')) for x in i.texts)>4_194_304: raise ValueError("batch_sha256 input exceeds 4 MiB")
        if not 1<=i.workers<=64: raise ValueError("workers must be 1..64")
        return self

    def fingerprint(self)->str: return canonical_sha256(self)

class GoExecutionResultContract(BaseModel):
    result_contract_id:str=Field(min_length=2,max_length=500)
    go_request_ref:str=Field(min_length=2,max_length=500)
    operation:GoOperation
    expected_artifact_kinds:list[str]=Field(default_factory=list)
    expected_result_kinds:list[str]=Field(default_factory=list)
    state:GoExecutionState=GoExecutionState.declared
    metadata:dict[str,Any]=Field(default_factory=dict)
    @model_validator(mode="after")
    def validate_contract(self):
        if not self.expected_artifact_kinds and not self.expected_result_kinds: raise ValueError("Go result contract requires outputs")
        if len(self.expected_artifact_kinds)!=len(set(self.expected_artifact_kinds)): raise ValueError("duplicate artifact kinds")
        if len(self.expected_result_kinds)!=len(set(self.expected_result_kinds)): raise ValueError("duplicate result kinds")
        return self
    def fingerprint(self)->str:
        p=self.model_dump(mode="json",exclude_none=True); p.pop("state",None); return canonical_sha256(p)

class GoRuntimeRegistration(BaseModel):
    registration_id:str=Field(min_length=2,max_length=500)
    runtime_id:str=RUNTIME_ID
    provider_version:str=PROVIDER_VERSION
    go_version:str=GO_VERSION
    go_package_version:str=GO_PACKAGE_VERSION
    adapter_id:str=ADAPTER_ID
    service_name:str=SERVICE_NAME
    endpoint:str=SERVICE_ENDPOINT
    operations:list[str]=Field(default_factory=lambda:list(GO_OPERATIONS))
    runtime_contract:str=CONTRACT_VERSION
    runtime_kind:str="language"
    language:str="go"
    status:str="active"
    metadata:dict[str,Any]=Field(default_factory=dict)
    @model_validator(mode="after")
    def validate_registration(self):
        if self.runtime_id!=RUNTIME_ID or self.adapter_id!=ADAPTER_ID: raise ValueError("Go runtime identity mismatch")
        if self.provider_version!=PROVIDER_VERSION: raise ValueError("Go provider version mismatch")
        if set(self.operations)!=set(GO_OPERATIONS) or len(self.operations)!=len(set(self.operations)): raise ValueError("Go operation set mismatch")
        return self
    def fingerprint(self)->str: return canonical_sha256(self)

class GoRuntimeBundle(BaseModel):
    bundle_id:str=Field(min_length=2,max_length=500)
    registration:GoRuntimeRegistration
    environment_package:ReproducibleEnvironmentPackage
    security_policy:RuntimeSecurityPolicy
    reference_request:GoExecutionRequest
    result_contract:GoExecutionResultContract
    source_object_refs:list[str]=Field(default_factory=list)
    metadata:dict[str,Any]=Field(default_factory=dict)
    @model_validator(mode="after")
    def validate_bundle(self):
        if self.reference_request.environment_package_ref!=self.environment_package.environment_package_id: raise ValueError("request/environment mismatch")
        if self.reference_request.security_policy_ref!=self.security_policy.security_policy_id: raise ValueError("request/security mismatch")
        if self.result_contract.go_request_ref!=self.reference_request.go_request_id: raise ValueError("result/request mismatch")
        if self.result_contract.operation!=self.reference_request.operation: raise ValueError("operation mismatch")
        return self
    def fingerprint(self)->str:
        return canonical_sha256({"bundle_id":self.bundle_id,"registration":self.registration.fingerprint(),"environment":self.environment_package.fingerprint(),"security":self.security_policy.fingerprint(),"request":self.reference_request.fingerprint(),"result_contract":self.result_contract.fingerprint(),"source_object_refs":sorted(self.source_object_refs),"metadata":self.metadata})

def reference_environment_package()->ReproducibleEnvironmentPackage:
    manifest=EnvironmentAsset(asset_id="environment-asset:go-runtime-manifest",kind=EnvironmentAssetKind.manifest,uri="core-ref://runtime-manifests/go-1.22.2-noble.json",content_sha256="1"*64,media_type="application/json",size_bytes=512)
    reqs=EnvironmentAsset(asset_id="environment-asset:go-provider-requirements",kind=EnvironmentAssetKind.lockfile,uri="core-ref://runtime-locks/go-provider-requirements.txt",content_sha256="2"*64,media_type="text/plain",size_bytes=256)
    return ReproducibleEnvironmentPackage(
        environment_package_id="environment-package:go-runtime:v1",name="Sustainable Catalyst Go Runtime Environment",package_version="1.0.0",
        platform=PlatformDescriptor(operating_system="Ubuntu",operating_system_version="24.04",architecture=PlatformArchitecture.amd64,libc="glibc",kernel_family="linux"),
        runtimes=[RuntimeEnvironmentRequirement(runtime_requirement_id="runtime-requirement:go-provider",runtime_ref=RUNTIME_ID,runtime_version=PROVIDER_VERSION,runtime_adapter_ref=ADAPTER_ID)],
        system_packages=[SystemPackageRequirement(requirement_id="system-package:golang-1.22-go",manager=PackageManager.apt,name="golang-1.22-go",version=GO_PACKAGE_VERSION,source=RequirementSource.operating_system)],
        language_packages=[],
        environment_variables=[
            EnvironmentVariableDeclaration(variable_id="environment-variable:go-artifact-root",name="SC_GO_ARTIFACT_ROOT",kind=EnvironmentVariableKind.path,value="/var/lib/sc-go-runtime/artifacts"),
            EnvironmentVariableDeclaration(variable_id="environment-variable:go-work-root",name="SC_GO_WORK_ROOT",kind=EnvironmentVariableKind.path,value="/var/lib/sc-go-runtime/work"),
        ],
        assets=[manifest,reqs],
        build_instructions=[
            EnvironmentBuildInstruction(instruction_id="build-instruction:go-toolchain",ordinal=1,action="install-pinned-go-toolchain",manager=PackageManager.apt,requirement_refs=["system-package:golang-1.22-go"]),
            EnvironmentBuildInstruction(instruction_id="build-instruction:go-provider",ordinal=2,action="install-provider-python-dependencies",manager=PackageManager.pip,artifact_ref=reqs.asset_id),
            EnvironmentBuildInstruction(instruction_id="build-instruction:go-smoke",ordinal=3,action="compile-and-run-bounded-go-smoke-test"),
        ],
        source_environment_ref="runtime-environment:go-provider:v1",source_job_refs=[],source_workflow_refs=[],state=EnvironmentPackageState.verified,
        provenance={"source_release":CORE_RELEASE,"core_builds_environment":False,"execution_host_builds_environment":True},
        metadata={"go_version":GO_VERSION,"go_package_version":GO_PACKAGE_VERSION,"provider_version":PROVIDER_VERSION,"arbitrary_go_code":False,"external_module_downloads":False,"cgo_enabled":False},
    )

def reference_security_policy()->RuntimeSecurityPolicy:
    iso=RuntimeIsolationProfile(isolation_profile_id="isolation-profile:go-runtime-standard:v1",mechanism=IsolationMechanism.process,network_mode=NetworkAccessMode.none,filesystem_mode=FilesystemAccessMode.allowlist,package_install_mode=PackageInstallMode.denied,process_namespace_isolated=True,user_namespace_isolated=True,privilege_escalation_allowed=False,host_filesystem_mounted=False,shell_allowed=False,arbitrary_code_allowed=False,outbound_artifact_egress_allowed=True,resource_budget_ref="resource-budget:go-runtime-standard:v1",syscall_policy_ref="syscall-policy:go-runtime-standard:v1")
    return RuntimeSecurityPolicy(security_policy_id="runtime-security-policy:go-runtime-standard:v1",policy_version="1.0.0",name="Go Runtime Standard Policy",isolation_profile=iso,allowed_runtime_refs=[RUNTIME_ID],allowed_adapter_refs=[ADAPTER_ID],allowed_operations={RUNTIME_ID:list(GO_OPERATIONS)},allowed_filesystem_prefixes=["/workspace","/tmp/sc-go-runtime","/var/lib/sc-go-runtime/artifacts","/var/lib/sc-go-runtime/work"],allowed_artifact_egress_classes=["research-artifact","concurrent-result","go-diagnostics"],execution_policy_ref="execution-policy:go-runtime-standard:v1",provenance={"source_release":CORE_RELEASE,"policy_owner":"platform-governance"},metadata={"arbitrary_go_source_allowed":False,"go_module_download_allowed":False,"runtime_package_install_allowed":False,"caller_filesystem_paths_allowed":False,"provider_managed_compilation":True})

def reference_runtime_bundle()->GoRuntimeBundle:
    req=GoExecutionRequest(go_request_id="go-request:reference-parallel-sum:001",operation=GoOperation.parallel_sum,inputs=GoInput(values=[1.0,2.0,3.0,4.0],workers=4),computational_job_ref="job:go-reference-parallel-sum:001",provenance={"originating_product":"workspace","execution_owner":"workspace-or-execution-host"})
    result=GoExecutionResultContract(result_contract_id="go-result-contract:reference-parallel-sum:001",go_request_ref=req.go_request_id,operation=req.operation,expected_artifact_kinds=["go-source","go-compile-log","go-run-log","native-result-json"],expected_result_kinds=["scalar-result","go-diagnostics"],metadata={"expected_value":10.0,"scientific_validity_certified":False})
    return GoRuntimeBundle(bundle_id="go-runtime-bundle:reference:v1",registration=GoRuntimeRegistration(registration_id="go-runtime-registration:v1",metadata={"compiler":"go1.22.2","arbitrary_go_code":False,"external_module_downloads":False,"provider_managed_compilation":True}),environment_package=reference_environment_package(),security_policy=reference_security_policy(),reference_request=req,result_contract=result,source_object_refs=["rust-runtime-bundle:reference:v1","unified-runtime-catalog:platform-core:v1"],metadata={"reference_is_contract_proof":True,"live_provider_execution_occurs_outside_core":True})

def to_scientific_go_artifact(bundle:GoRuntimeBundle)->dict[str,Any]:
    return {"artifact_id":f"scientific-artifact:{bundle.bundle_id}","artifact_kind":"package","uri":f"core-ref://{bundle.bundle_id}","content_sha256":bundle.fingerprint(),"media_type":"application/vnd.sustainable-catalyst.go-runtime+json","source_contract":CONTRACT_VERSION,"source_object_ref":bundle.bundle_id,"metadata":{"runtime_id":bundle.registration.runtime_id,"provider_version":bundle.registration.provider_version,"go_version":bundle.registration.go_version,"reference_operation":bundle.reference_request.operation.value}}

def contract_document()->dict[str,Any]:
    b=reference_runtime_bundle()
    return {"ok":True,"release":CORE_RELEASE,"contract":CONTRACT_VERSION,"provider_version":PROVIDER_VERSION,"go_version":GO_VERSION,"go_package_version":GO_PACKAGE_VERSION,"runtime_id":RUNTIME_ID,"adapter_id":ADAPTER_ID,"language":"go","operations":list(GO_OPERATIONS),"capabilities":{"concurrent_distributed":True,"parallel_compute":True,"batch_processing":True,"graph_processing":True,"deterministic_hashing":True,"provider_managed_compilation":True,"reproducible_environment_package":True,"runtime_security_policy":True,"runtime_adapter_registration":True,"unified_runtime_catalog_integration":True,"workspace_product_profile_integration":True,"research_lab_product_profile_integration":True,"workbench_product_profile_integration":True,"scientific_registry_bridge":True},"boundaries":{"core_executes_go":False,"provider_executes_go":True,"arbitrary_go_source":False,"shell_execution":False,"go_module_download_via_api":False,"runtime_package_install_via_api":False,"caller_filesystem_paths":False,"core_selects_algorithm":False,"core_certifies_numerical_validity":False,"core_certifies_scientific_validity":False},"reference":{"bundle_id":b.bundle_id,"environment_package_id":b.environment_package.environment_package_id,"security_policy_id":b.security_policy.security_policy_id,"reference_request_id":b.reference_request.go_request_id,"reference_operation":b.reference_request.operation.value,"bundle_fingerprint_sha256":b.fingerprint()}}
