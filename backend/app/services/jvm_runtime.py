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

CORE_RELEASE = "3.56.0"
CONTRACT_VERSION = "sc.core.jvm-runtime.v1"
PROVIDER_VERSION = "1.0.0"
JVM_MAJOR_VERSION = "21"
JVM_IMPLEMENTATION = "OpenJDK"
JVM_PACKAGE_NAME = "openjdk-21-jdk-headless"
JVM_PACKAGE_VERSION = "ubuntu-noble-openjdk-21"
RUNTIME_ID = "sc-runtime-jvm"
ADAPTER_ID = "adapter:sc-runtime-jvm"
SERVICE_NAME = "sc-jvm-runtime"
SERVICE_ENDPOINT = "http://127.0.0.1:18105"

JVM_OPERATIONS = [
    "jvm_runtime_info",
    "parallel_sum",
    "parallel_map_affine",
    "matrix_row_sums",
    "graph_bfs",
    "batch_sha256",
]

class JVMOperation(str, Enum):
    jvm_runtime_info = "jvm_runtime_info"
    parallel_sum = "parallel_sum"
    parallel_map_affine = "parallel_map_affine"
    matrix_row_sums = "matrix_row_sums"
    graph_bfs = "graph_bfs"
    batch_sha256 = "batch_sha256"

class JVMInput(BaseModel):
    values: list[float] = Field(default_factory=list)
    scale: float = 1.0
    offset: float = 0.0
    matrix: list[list[float]] = Field(default_factory=list)
    adjacency_matrix: list[list[int]] = Field(default_factory=list)
    source_index: int | None = None
    strings: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    def fingerprint(self): return canonical_sha256(self)

class JVMExecutionSettings(BaseModel):
    max_execution_seconds: int = Field(default=120, ge=1, le=1800)
    max_heap_mb: int = Field(default=256, ge=64, le=4096)
    metadata: dict[str, Any] = Field(default_factory=dict)

class JVMExecutionRequest(BaseModel):
    jvm_request_id: str = Field(min_length=2, max_length=500)
    operation: JVMOperation
    inputs: JVMInput = Field(default_factory=JVMInput)
    settings: JVMExecutionSettings = Field(default_factory=JVMExecutionSettings)
    computational_job_ref: str = Field(min_length=2, max_length=500)
    environment_package_ref: str = "environment-package:jvm-runtime:v1"
    security_policy_ref: str = "runtime-security-policy:jvm-runtime-standard:v1"
    provenance: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_operation(self):
        i=self.inputs
        def finite_list(v,name,min_len=1,max_len=262144):
            if not min_len <= len(v) <= max_len: raise ValueError(f"{name} length must be {min_len}..{max_len}")
            if any(not math.isfinite(float(x)) for x in v): raise ValueError(f"{name} values must be finite")
        if self.operation in {JVMOperation.parallel_sum,JVMOperation.parallel_map_affine}:
            finite_list(i.values,"values")
            if not math.isfinite(i.scale) or not math.isfinite(i.offset): raise ValueError("scale/offset must be finite")
        elif self.operation == JVMOperation.matrix_row_sums:
            if not i.matrix or not i.matrix[0] or len(i.matrix)>2048 or len(i.matrix[0])>2048: raise ValueError("matrix dimensions invalid")
            width=len(i.matrix[0])
            if any(len(r)!=width for r in i.matrix): raise ValueError("matrix must be rectangular")
            if any(not math.isfinite(float(x)) for r in i.matrix for x in r): raise ValueError("matrix values must be finite")
        elif self.operation == JVMOperation.graph_bfs:
            m=i.adjacency_matrix
            if not m or len(m)>2048 or any(len(r)!=len(m) for r in m): raise ValueError("adjacency_matrix must be square with <=2048 vertices")
            if any(x not in (0,1) for r in m for x in r): raise ValueError("adjacency_matrix entries must be 0 or 1")
            if i.source_index is None or not 0 <= i.source_index < len(m): raise ValueError("source_index out of range")
        elif self.operation == JVMOperation.batch_sha256:
            if not 1 <= len(i.strings) <= 10000: raise ValueError("strings must contain 1..10000 values")
            if any(not isinstance(s,str) or len(s.encode('utf-8'))>65536 for s in i.strings): raise ValueError("invalid string payload")
        return self
    def fingerprint(self): return canonical_sha256(self)

class JVMRuntimeRegistration(BaseModel):
    registration_id: str
    runtime_id: str = RUNTIME_ID
    provider_version: str = PROVIDER_VERSION
    jvm_major_version: str = JVM_MAJOR_VERSION
    jvm_implementation: str = JVM_IMPLEMENTATION
    jvm_package_name: str = JVM_PACKAGE_NAME
    jvm_package_version: str = JVM_PACKAGE_VERSION
    adapter_id: str = ADAPTER_ID
    service_name: str = SERVICE_NAME
    endpoint: str = SERVICE_ENDPOINT
    operations: list[str] = Field(default_factory=lambda:list(JVM_OPERATIONS))
    runtime_contract: str = CONTRACT_VERSION
    runtime_kind: str = "execution-target"
    language: str = "jvm-bytecode"
    status: str = "active"
    metadata: dict[str, Any] = Field(default_factory=dict)
    def fingerprint(self): return canonical_sha256(self)

class JVMRuntimeBundle(BaseModel):
    bundle_id: str
    registration: JVMRuntimeRegistration
    environment_package: ReproducibleEnvironmentPackage
    security_policy: RuntimeSecurityPolicy
    reference_request: JVMExecutionRequest
    source_object_refs: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    @model_validator(mode="after")
    def validate_bundle(self):
        if self.reference_request.environment_package_ref != self.environment_package.environment_package_id: raise ValueError("environment mismatch")
        if self.reference_request.security_policy_ref != self.security_policy.security_policy_id: raise ValueError("security mismatch")
        return self
    def fingerprint(self):
        return canonical_sha256({"bundle_id":self.bundle_id,"registration":self.registration.fingerprint(),"environment":self.environment_package.fingerprint(),"security":self.security_policy.fingerprint(),"request":self.reference_request.fingerprint(),"source_object_refs":sorted(self.source_object_refs),"metadata":self.metadata})

def reference_environment_package():
    manifest=EnvironmentAsset(asset_id="environment-asset:jvm-runtime-manifest",kind=EnvironmentAssetKind.manifest,uri="core-ref://runtime-manifests/openjdk-21-noble.json",content_sha256="5"*64,media_type="application/json",size_bytes=512)
    req=EnvironmentAsset(asset_id="environment-asset:jvm-provider-requirements",kind=EnvironmentAssetKind.lockfile,uri="core-ref://runtime-locks/jvm-provider-requirements.txt",content_sha256="6"*64,media_type="text/plain",size_bytes=256)
    return ReproducibleEnvironmentPackage(
        environment_package_id="environment-package:jvm-runtime:v1",name="Sustainable Catalyst JVM Runtime Environment",package_version="1.0.0",
        platform=PlatformDescriptor(operating_system="Ubuntu",operating_system_version="24.04",architecture=PlatformArchitecture.amd64,libc="glibc",kernel_family="linux"),
        runtimes=[RuntimeEnvironmentRequirement(runtime_requirement_id="runtime-requirement:jvm-provider",runtime_ref=RUNTIME_ID,runtime_version=PROVIDER_VERSION,runtime_adapter_ref=ADAPTER_ID)],
        system_packages=[SystemPackageRequirement(requirement_id="system-package:openjdk-21-jdk-headless",manager=PackageManager.apt,name=JVM_PACKAGE_NAME,version=JVM_PACKAGE_VERSION,source=RequirementSource.operating_system)],
        language_packages=[],
        environment_variables=[EnvironmentVariableDeclaration(variable_id="environment-variable:jvm-artifact-root",name="SC_JVM_ARTIFACT_ROOT",kind=EnvironmentVariableKind.path,value="/var/lib/sc-jvm-runtime/artifacts")],
        assets=[manifest,req],
        build_instructions=[
            EnvironmentBuildInstruction(instruction_id="build-instruction:jvm-runtime",ordinal=1,action="install-openjdk-21-and-record-native-package-version",manager=PackageManager.apt,requirement_refs=["system-package:openjdk-21-jdk-headless"]),
            EnvironmentBuildInstruction(instruction_id="build-instruction:jvm-provider",ordinal=2,action="install-provider-python-dependencies",manager=PackageManager.pip,artifact_ref=req.asset_id),
            EnvironmentBuildInstruction(instruction_id="build-instruction:jvm-smoke",ordinal=3,action="compile-and-run-bounded-jvm-smoke-test"),
        ],
        source_environment_ref="runtime-environment:jvm-provider:v1",source_job_refs=[],source_workflow_refs=[],state=EnvironmentPackageState.verified,
        provenance={"source_release":CORE_RELEASE,"core_builds_environment":False,"execution_host_builds_environment":True,"native_package_version_recorded_at_deploy":True},
        metadata={"jvm_major_version":JVM_MAJOR_VERSION,"jvm_implementation":JVM_IMPLEMENTATION,"jvm_package_name":JVM_PACKAGE_NAME,"language_profiles_deferred_to":"3.56.1","arbitrary_bytecode":False},
    )

def reference_security_policy():
    isolation=RuntimeIsolationProfile(isolation_profile_id="isolation-profile:jvm-runtime-standard:v1",mechanism=IsolationMechanism.process,network_mode=NetworkAccessMode.none,filesystem_mode=FilesystemAccessMode.allowlist,package_install_mode=PackageInstallMode.denied,process_namespace_isolated=True,user_namespace_isolated=True,privilege_escalation_allowed=False,host_filesystem_mounted=False,shell_allowed=False,arbitrary_code_allowed=False,outbound_artifact_egress_allowed=True,resource_budget_ref="resource-budget:jvm-runtime-standard:v1",syscall_policy_ref="syscall-policy:jvm-runtime-standard:v1")
    return RuntimeSecurityPolicy(security_policy_id="runtime-security-policy:jvm-runtime-standard:v1",policy_version="1.0.0",name="JVM Runtime Standard Policy",isolation_profile=isolation,allowed_runtime_refs=[RUNTIME_ID],allowed_adapter_refs=[ADAPTER_ID],allowed_operations={RUNTIME_ID:list(JVM_OPERATIONS)},allowed_filesystem_prefixes=["/workspace","/tmp/sc-jvm-runtime","/var/lib/sc-jvm-runtime/artifacts","/var/lib/sc-jvm-runtime/work"],allowed_artifact_egress_classes=["research-artifact","jvm-result","jvm-diagnostics"],execution_policy_ref="execution-policy:jvm-runtime-standard:v1",provenance={"source_release":CORE_RELEASE,"policy_owner":"platform-governance"},metadata={"arbitrary_jvm_bytecode_allowed":False,"caller_classpath_allowed":False,"runtime_dependency_install_allowed":False,"provider_generated_bootstrap_java":True})

def reference_runtime_bundle():
    req=JVMExecutionRequest(jvm_request_id="jvm-request:reference-parallel-sum:001",operation=JVMOperation.parallel_sum,inputs=JVMInput(values=[1,2,3,4,5]),computational_job_ref="job:jvm-reference-parallel-sum:001",provenance={"originating_product":"workspace","execution_owner":"workspace-or-execution-host"})
    return JVMRuntimeBundle(bundle_id="jvm-runtime-bundle:reference:v1",registration=JVMRuntimeRegistration(registration_id="jvm-runtime-registration:v1",metadata={"execution_target":"JVM","bootstrap_language":"Java","language_profiles_deferred":True,"arbitrary_bytecode":False}),environment_package=reference_environment_package(),security_policy=reference_security_policy(),reference_request=req,source_object_refs=["prolog-runtime-bundle:reference:v1","unified-runtime-catalog:platform-core:v1"],metadata={"reference_is_contract_proof":True,"live_provider_execution_occurs_outside_core":True})

def to_scientific_jvm_artifact(bundle):
    return {"artifact_id":f"scientific-artifact:{bundle.bundle_id}","artifact_kind":"package","uri":f"core-ref://{bundle.bundle_id}","content_sha256":bundle.fingerprint(),"media_type":"application/vnd.sustainable-catalyst.jvm-runtime+json","source_contract":CONTRACT_VERSION,"source_object_ref":bundle.bundle_id,"metadata":{"runtime_id":bundle.registration.runtime_id,"provider_version":bundle.registration.provider_version,"jvm_major_version":bundle.registration.jvm_major_version,"reference_operation":bundle.reference_request.operation.value}}

def contract_document():
    b=reference_runtime_bundle()
    return {"ok":True,"release":CORE_RELEASE,"contract":CONTRACT_VERSION,"provider_version":PROVIDER_VERSION,"jvm_major_version":JVM_MAJOR_VERSION,"jvm_implementation":JVM_IMPLEMENTATION,"jvm_package_name":JVM_PACKAGE_NAME,"runtime_id":RUNTIME_ID,"adapter_id":ADAPTER_ID,"runtime_kind":"execution-target","language":"jvm-bytecode","operations":list(JVM_OPERATIONS),"capabilities":{"managed_vm_execution":True,"parallel_compute":True,"graph_processing":True,"deterministic_hashing":True,"provider_managed_compilation":True,"reproducible_environment_package":True,"runtime_security_policy":True,"runtime_adapter_registration":True,"unified_runtime_catalog_integration":True,"workspace_product_profile_integration":True,"research_lab_product_profile_integration":True,"workbench_product_profile_integration":True,"scientific_registry_bridge":True,"language_profiles_ready":True},"boundaries":{"core_executes_jvm":False,"provider_executes_jvm":True,"arbitrary_jvm_bytecode":False,"arbitrary_java_source":False,"caller_classpath":False,"shell_execution":False,"runtime_dependency_install_via_api":False,"network_access":False,"core_selects_jvm_language_profile":False,"java_kotlin_scala_profiles_deferred_to":"3.56.1","spark_adapter_deferred_to":"3.56.2"},"reference":{"bundle_id":b.bundle_id,"environment_package_id":b.environment_package.environment_package_id,"security_policy_id":b.security_policy.security_policy_id,"reference_request_id":b.reference_request.jvm_request_id,"reference_operation":b.reference_request.operation.value,"bundle_fingerprint_sha256":b.fingerprint()}}
