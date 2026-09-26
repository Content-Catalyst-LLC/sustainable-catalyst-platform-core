from __future__ import annotations

import math
from enum import Enum
from typing import Any
from pydantic import BaseModel, Field, model_validator
from .computational_runtime_objects import canonical_sha256
from .reproducible_environment_packages import EnvironmentAsset, EnvironmentAssetKind, EnvironmentBuildInstruction, EnvironmentPackageState, EnvironmentVariableDeclaration, EnvironmentVariableKind, PackageManager, PlatformArchitecture, PlatformDescriptor, ReproducibleEnvironmentPackage, RequirementSource, RuntimeEnvironmentRequirement, SystemPackageRequirement
from .runtime_security_governance import FilesystemAccessMode, IsolationMechanism, NetworkAccessMode, PackageInstallMode, RuntimeIsolationProfile, RuntimeSecurityPolicy

CORE_RELEASE="3.51.0"
CONTRACT_VERSION="sc.core.c-cpp-runtime.v1"
PROVIDER_VERSION="1.0.0"
GCC_VERSION="13.3.0"
GCC_PACKAGE_VERSION="13.3.0-6ubuntu2~24.04.1"
GPP_VERSION="13.3.0"
GPP_PACKAGE_VERSION="13.3.0-6ubuntu2~24.04.1"
RUNTIME_ID="sc-runtime-cpp"
ADAPTER_ID="adapter:sc-runtime-cpp"
SERVICE_NAME="sc-cpp-runtime"
SERVICE_ENDPOINT="http://127.0.0.1:18100"
CPP_OPERATIONS=["dot_product","matrix_multiply","linear_interpolation","polynomial_evaluate","fir_filter","dijkstra_shortest_path"]
OPERATION_LANGUAGE={"dot_product":"c11","matrix_multiply":"cpp17","linear_interpolation":"c11","polynomial_evaluate":"cpp17","fir_filter":"c11","dijkstra_shortest_path":"cpp17"}

class CCppOperation(str,Enum):
    dot_product="dot_product"; matrix_multiply="matrix_multiply"; linear_interpolation="linear_interpolation"; polynomial_evaluate="polynomial_evaluate"; fir_filter="fir_filter"; dijkstra_shortest_path="dijkstra_shortest_path"
class CCppExecutionState(str,Enum):
    declared="declared"; prepared="prepared"; running="running"; completed="completed"; failed="failed"; cancelled="cancelled"
def _finite_vector(v,name,min_len=1,max_len=262144):
    if len(v)<min_len or len(v)>max_len: raise ValueError(f"{name} length must be between {min_len} and {max_len}")
    if any(not math.isfinite(float(x)) for x in v): raise ValueError(f"{name} values must be finite")
def _matrix_shape(m,name):
    if not m or not m[0]: raise ValueError(f"{name} must be a non-empty matrix")
    r,c=len(m),len(m[0])
    if r>256 or c>256: raise ValueError(f"{name} dimensions must not exceed 256x256")
    if any(len(row)!=c for row in m): raise ValueError(f"{name} must be rectangular")
    if any(not math.isfinite(float(x)) for row in m for x in row): raise ValueError(f"{name} values must be finite")
    return r,c
class CCppNumericInput(BaseModel):
    vector_a:list[float]=Field(default_factory=list); vector_b:list[float]=Field(default_factory=list); matrix_a:list[list[float]]=Field(default_factory=list); matrix_b:list[list[float]]=Field(default_factory=list); x:list[float]=Field(default_factory=list); y:list[float]=Field(default_factory=list); query_x:float|None=None; coefficients:list[float]=Field(default_factory=list); scalar_x:float|None=None; signal:list[float]=Field(default_factory=list); kernel:list[float]=Field(default_factory=list); adjacency_matrix:list[list[float]]=Field(default_factory=list); source_index:int|None=None; target_index:int|None=None; metadata:dict[str,Any]=Field(default_factory=dict)
    def fingerprint(self): return canonical_sha256(self)
class CCppExecutionSettings(BaseModel):
    max_execution_seconds:int=Field(default=120,ge=1,le=1800); optimization_level:int=Field(default=2,ge=0,le=2); metadata:dict[str,Any]=Field(default_factory=dict)
    def fingerprint(self): return canonical_sha256(self)
class CCppExecutionRequest(BaseModel):
    cpp_request_id:str=Field(min_length=2,max_length=500); operation:CCppOperation; inputs:CCppNumericInput; settings:CCppExecutionSettings=Field(default_factory=CCppExecutionSettings); computational_job_ref:str=Field(min_length=2,max_length=500); environment_package_ref:str="environment-package:c-cpp-runtime:v1"; security_policy_ref:str="runtime-security-policy:c-cpp-runtime-standard:v1"; provenance:dict[str,Any]=Field(default_factory=dict); metadata:dict[str,Any]=Field(default_factory=dict)
    @model_validator(mode="after")
    def validate_request(self):
        i,op=self.inputs,self.operation
        if op==CCppOperation.dot_product:
            _finite_vector(i.vector_a,"vector_a"); _finite_vector(i.vector_b,"vector_b")
            if len(i.vector_a)!=len(i.vector_b): raise ValueError("dot_product requires equal vector lengths")
        elif op==CCppOperation.matrix_multiply:
            ar,ac=_matrix_shape(i.matrix_a,"matrix_a"); br,bc=_matrix_shape(i.matrix_b,"matrix_b")
            if ac!=br: raise ValueError("matrix_multiply requires matrix_a columns == matrix_b rows")
            if ar*bc>65536: raise ValueError("matrix_multiply output exceeds 65536 elements")
        elif op==CCppOperation.linear_interpolation:
            _finite_vector(i.x,"x",2); _finite_vector(i.y,"y",2)
            if len(i.x)!=len(i.y): raise ValueError("linear_interpolation requires equal x/y lengths")
            if any(i.x[j+1]<=i.x[j] for j in range(len(i.x)-1)): raise ValueError("x must be strictly increasing")
            if i.query_x is None or not math.isfinite(float(i.query_x)): raise ValueError("linear_interpolation requires finite query_x")
            if i.query_x<i.x[0] or i.query_x>i.x[-1]: raise ValueError("query_x must lie within x range")
        elif op==CCppOperation.polynomial_evaluate:
            _finite_vector(i.coefficients,"coefficients")
            if i.scalar_x is None or not math.isfinite(float(i.scalar_x)): raise ValueError("polynomial_evaluate requires finite scalar_x")
        elif op==CCppOperation.fir_filter:
            _finite_vector(i.signal,"signal"); _finite_vector(i.kernel,"kernel")
            if len(i.kernel)>1024: raise ValueError("fir_filter kernel must not exceed 1024 taps")
        elif op==CCppOperation.dijkstra_shortest_path:
            r,c=_matrix_shape(i.adjacency_matrix,"adjacency_matrix")
            if r!=c: raise ValueError("dijkstra_shortest_path requires a square adjacency matrix")
            if r>512: raise ValueError("dijkstra graph must not exceed 512 vertices")
            if any(v<0 for row in i.adjacency_matrix for v in row): raise ValueError("dijkstra weights must be non-negative")
            if i.source_index is None or i.target_index is None or not (0<=i.source_index<r and 0<=i.target_index<r): raise ValueError("dijkstra indices are out of range")
        return self
    def fingerprint(self): return canonical_sha256(self)
class CCppExecutionResultContract(BaseModel):
    result_contract_id:str=Field(min_length=2,max_length=500); cpp_request_ref:str=Field(min_length=2,max_length=500); operation:CCppOperation; expected_artifact_kinds:list[str]=Field(default_factory=list); expected_result_kinds:list[str]=Field(default_factory=list); state:CCppExecutionState=CCppExecutionState.declared; metadata:dict[str,Any]=Field(default_factory=dict)
    @model_validator(mode="after")
    def validate_contract(self):
        if not self.expected_artifact_kinds and not self.expected_result_kinds: raise ValueError("C/C++ result contract requires artifact or result kinds")
        if len(self.expected_artifact_kinds)!=len(set(self.expected_artifact_kinds)): raise ValueError("duplicate C/C++ artifact kinds")
        if len(self.expected_result_kinds)!=len(set(self.expected_result_kinds)): raise ValueError("duplicate C/C++ result kinds")
        return self
    def fingerprint(self):
        p=self.model_dump(mode="json",exclude_none=True); p.pop("state",None); return canonical_sha256(p)
class CCppRuntimeRegistration(BaseModel):
    registration_id:str=Field(min_length=2,max_length=500); runtime_id:str=RUNTIME_ID; provider_version:str=PROVIDER_VERSION; gcc_version:str=GCC_VERSION; gcc_package_version:str=GCC_PACKAGE_VERSION; gpp_version:str=GPP_VERSION; gpp_package_version:str=GPP_PACKAGE_VERSION; adapter_id:str=ADAPTER_ID; service_name:str=SERVICE_NAME; endpoint:str=SERVICE_ENDPOINT; operations:list[str]=Field(default_factory=lambda:list(CPP_OPERATIONS)); runtime_contract:str=CONTRACT_VERSION; runtime_kind:str="language"; language:str="c-cpp"; language_profiles:list[str]=Field(default_factory=lambda:["c11","cpp17"]); status:str="active"; metadata:dict[str,Any]=Field(default_factory=dict)
    @model_validator(mode="after")
    def validate_registration(self):
        if self.runtime_id!=RUNTIME_ID or self.adapter_id!=ADAPTER_ID: raise ValueError("C/C++ runtime identity mismatch")
        if self.provider_version!=PROVIDER_VERSION: raise ValueError("C/C++ provider version mismatch")
        if set(self.operations)!=set(CPP_OPERATIONS) or len(self.operations)!=len(set(self.operations)): raise ValueError("C/C++ operation set mismatch")
        if set(self.language_profiles)!={"c11","cpp17"}: raise ValueError("C/C++ language profile mismatch")
        return self
    def fingerprint(self): return canonical_sha256(self)
class CCppRuntimeBundle(BaseModel):
    bundle_id:str=Field(min_length=2,max_length=500); registration:CCppRuntimeRegistration; environment_package:ReproducibleEnvironmentPackage; security_policy:RuntimeSecurityPolicy; reference_request:CCppExecutionRequest; result_contract:CCppExecutionResultContract; source_object_refs:list[str]=Field(default_factory=list); metadata:dict[str,Any]=Field(default_factory=dict)
    @model_validator(mode="after")
    def validate_bundle(self):
        if self.reference_request.environment_package_ref!=self.environment_package.environment_package_id: raise ValueError("C/C++ request/environment mismatch")
        if self.reference_request.security_policy_ref!=self.security_policy.security_policy_id: raise ValueError("C/C++ request/security mismatch")
        if self.result_contract.cpp_request_ref!=self.reference_request.cpp_request_id: raise ValueError("C/C++ result/request mismatch")
        if self.result_contract.operation!=self.reference_request.operation: raise ValueError("C/C++ operation mismatch")
        return self
    def fingerprint(self): return canonical_sha256({"bundle_id":self.bundle_id,"registration":self.registration.fingerprint(),"environment":self.environment_package.fingerprint(),"security":self.security_policy.fingerprint(),"request":self.reference_request.fingerprint(),"result_contract":self.result_contract.fingerprint(),"source_object_refs":sorted(self.source_object_refs),"metadata":self.metadata})
def reference_environment_package():
    platform=PlatformDescriptor(operating_system="Ubuntu",operating_system_version="24.04",architecture=PlatformArchitecture.amd64,libc="glibc",kernel_family="linux")
    manifest=EnvironmentAsset(asset_id="environment-asset:c-cpp-runtime-manifest",kind=EnvironmentAssetKind.manifest,uri="core-ref://runtime-manifests/gcc-gpp-13.3.0-noble.json",content_sha256="1"*64,media_type="application/json",size_bytes=512)
    reqs=EnvironmentAsset(asset_id="environment-asset:c-cpp-provider-requirements",kind=EnvironmentAssetKind.lockfile,uri="core-ref://runtime-locks/c-cpp-provider-requirements.txt",content_sha256="2"*64,media_type="text/plain",size_bytes=256)
    return ReproducibleEnvironmentPackage(environment_package_id="environment-package:c-cpp-runtime:v1",name="Sustainable Catalyst C/C++ Runtime Environment",package_version="1.0.0",platform=platform,runtimes=[RuntimeEnvironmentRequirement(runtime_requirement_id="runtime-requirement:c-cpp-provider",runtime_ref=RUNTIME_ID,runtime_version=PROVIDER_VERSION,runtime_adapter_ref=ADAPTER_ID)],system_packages=[SystemPackageRequirement(requirement_id="system-package:gcc-13",manager=PackageManager.apt,name="gcc-13",version=GCC_PACKAGE_VERSION,source=RequirementSource.operating_system),SystemPackageRequirement(requirement_id="system-package:gpp-13",manager=PackageManager.apt,name="g++-13",version=GPP_PACKAGE_VERSION,source=RequirementSource.operating_system)],language_packages=[],environment_variables=[EnvironmentVariableDeclaration(variable_id="environment-variable:c-cpp-artifact-root",name="SC_CPP_ARTIFACT_ROOT",kind=EnvironmentVariableKind.path,value="/var/lib/sc-cpp-runtime/artifacts"),EnvironmentVariableDeclaration(variable_id="environment-variable:c-cpp-work-root",name="SC_CPP_WORK_ROOT",kind=EnvironmentVariableKind.path,value="/var/lib/sc-cpp-runtime/work")],assets=[manifest,reqs],build_instructions=[EnvironmentBuildInstruction(instruction_id="build-instruction:c-cpp-system-packages",ordinal=1,action="install-pinned-gcc-gpp-13",manager=PackageManager.apt,requirement_refs=["system-package:gcc-13","system-package:gpp-13"]),EnvironmentBuildInstruction(instruction_id="build-instruction:c-cpp-provider-python",ordinal=2,action="install-provider-python-dependencies",manager=PackageManager.pip,artifact_ref=reqs.asset_id),EnvironmentBuildInstruction(instruction_id="build-instruction:c-cpp-smoke-test",ordinal=3,action="run-bounded-native-c-cpp-smoke-tests")],source_environment_ref="runtime-environment:c-cpp-provider:v1",source_job_refs=[],source_workflow_refs=[],state=EnvironmentPackageState.verified,provenance={"source_release":CORE_RELEASE,"core_builds_environment":False,"execution_host_builds_environment":True},metadata={"gcc_version":GCC_VERSION,"gcc_package_version":GCC_PACKAGE_VERSION,"gpp_version":GPP_VERSION,"gpp_package_version":GPP_PACKAGE_VERSION,"provider_version":PROVIDER_VERSION,"arbitrary_c_cpp_source":False,"language_profiles":["c11","cpp17"],"compiler_flags":["-O2","-fno-fast-math"]})
def reference_security_policy():
    isolation=RuntimeIsolationProfile(isolation_profile_id="isolation-profile:c-cpp-runtime-standard:v1",mechanism=IsolationMechanism.process,network_mode=NetworkAccessMode.none,filesystem_mode=FilesystemAccessMode.allowlist,package_install_mode=PackageInstallMode.denied,process_namespace_isolated=True,user_namespace_isolated=True,privilege_escalation_allowed=False,host_filesystem_mounted=False,shell_allowed=False,arbitrary_code_allowed=False,outbound_artifact_egress_allowed=True,resource_budget_ref="resource-budget:c-cpp-runtime-standard:v1",syscall_policy_ref="syscall-policy:c-cpp-runtime-standard:v1")
    return RuntimeSecurityPolicy(security_policy_id="runtime-security-policy:c-cpp-runtime-standard:v1",policy_version="1.0.0",name="C/C++ Runtime Standard Policy",isolation_profile=isolation,allowed_runtime_refs=[RUNTIME_ID],allowed_adapter_refs=[ADAPTER_ID],allowed_operations={RUNTIME_ID:list(CPP_OPERATIONS)},allowed_filesystem_prefixes=["/workspace","/tmp/sc-cpp-runtime","/var/lib/sc-cpp-runtime/artifacts","/var/lib/sc-cpp-runtime/work"],allowed_artifact_egress_classes=["research-artifact","native-engineering-result","c-cpp-diagnostics"],execution_policy_ref="execution-policy:c-cpp-runtime-standard:v1",provenance={"source_release":CORE_RELEASE,"policy_owner":"platform-governance"},metadata={"arbitrary_c_cpp_source_allowed":False,"runtime_package_install_allowed":False,"caller_filesystem_paths_allowed":False,"compiler_invocation_provider_managed":True})
def reference_runtime_bundle():
    req=CCppExecutionRequest(cpp_request_id="cpp-request:reference-dot-product:001",operation=CCppOperation.dot_product,inputs=CCppNumericInput(vector_a=[1.0,2.0,3.0],vector_b=[4.0,5.0,6.0]),computational_job_ref="job:cpp-reference-dot-product:001",provenance={"originating_product":"workbench","execution_owner":"workspace-or-execution-host"})
    rc=CCppExecutionResultContract(result_contract_id="cpp-result-contract:reference-dot-product:001",cpp_request_ref=req.cpp_request_id,operation=req.operation,expected_artifact_kinds=["c-cpp-generated-source","c-cpp-result-json","c-cpp-compile-log","c-cpp-run-log"],expected_result_kinds=["native-engineering-result","c-cpp-diagnostics"],metadata={"scientific_validity_certified":False,"source_is_provider_generated":True})
    return CCppRuntimeBundle(bundle_id="c-cpp-runtime-bundle:reference:v1",registration=CCppRuntimeRegistration(registration_id="c-cpp-runtime-registration:v1",metadata={"native_c_compiler":"gcc-13","native_cpp_compiler":"g++-13","c_standard":"C11","cpp_standard":"C++17","arbitrary_c_cpp_code":False}),environment_package=reference_environment_package(),security_policy=reference_security_policy(),reference_request=req,result_contract=rc,source_object_refs=["unified-runtime-catalog:platform-core:v1","fortran-runtime-bundle:reference:v1"],metadata={"reference_is_contract_proof":True,"live_provider_execution_occurs_outside_core":True})
def to_scientific_cpp_artifact(b): return {"artifact_id":f"scientific-artifact:{b.bundle_id}","artifact_kind":"package","uri":f"core-ref://{b.bundle_id}","content_sha256":b.fingerprint(),"media_type":"application/vnd.sustainable-catalyst.c-cpp-runtime+json","source_contract":CONTRACT_VERSION,"source_object_ref":b.bundle_id,"metadata":{"runtime_id":b.registration.runtime_id,"provider_version":b.registration.provider_version,"gcc_version":b.registration.gcc_version,"gpp_version":b.registration.gpp_version,"reference_operation":b.reference_request.operation.value}}
def contract_document():
    b=reference_runtime_bundle(); return {"ok":True,"release":CORE_RELEASE,"contract":CONTRACT_VERSION,"provider_version":PROVIDER_VERSION,"gcc_version":GCC_VERSION,"gcc_package_version":GCC_PACKAGE_VERSION,"gpp_version":GPP_VERSION,"gpp_package_version":GPP_PACKAGE_VERSION,"runtime_id":RUNTIME_ID,"adapter_id":ADAPTER_ID,"language":"c-cpp","language_profiles":["c11","cpp17"],"operations":list(CPP_OPERATIONS),"operation_language":dict(OPERATION_LANGUAGE),"capabilities":{"native_engineering":True,"numerical_compute":True,"matrix_compute":True,"signal_processing":True,"graph_algorithms":True,"provider_managed_compilation":True,"reproducible_environment_package":True,"runtime_security_policy":True,"runtime_adapter_registration":True,"unified_runtime_catalog_integration":True,"workspace_product_profile_integration":True,"research_lab_product_profile_integration":True,"workbench_product_profile_integration":True,"scientific_registry_bridge":True},"boundaries":{"core_executes_c_cpp":False,"provider_executes_c_cpp":True,"arbitrary_c_cpp_source":False,"shell_execution":False,"runtime_package_install_via_api":False,"caller_filesystem_paths":False,"core_selects_algorithm":False,"core_certifies_numerical_validity":False,"core_certifies_scientific_validity":False},"reference":{"bundle_id":b.bundle_id,"environment_package_id":b.environment_package.environment_package_id,"security_policy_id":b.security_policy.security_policy_id,"reference_request_id":b.reference_request.cpp_request_id,"reference_operation":b.reference_request.operation.value,"bundle_fingerprint_sha256":b.fingerprint()}}
