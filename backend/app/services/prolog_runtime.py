from __future__ import annotations

import re
from enum import Enum
from typing import Any
from pydantic import BaseModel, Field, model_validator

from .computational_runtime_objects import canonical_sha256
from .reproducible_environment_packages import (
    EnvironmentAsset, EnvironmentAssetKind, EnvironmentBuildInstruction, EnvironmentPackageState,
    EnvironmentVariableDeclaration, EnvironmentVariableKind, PackageManager, PlatformArchitecture,
    PlatformDescriptor, ReproducibleEnvironmentPackage, RequirementSource,
    RuntimeEnvironmentRequirement, SystemPackageRequirement,
)
from .runtime_security_governance import (
    FilesystemAccessMode, IsolationMechanism, NetworkAccessMode, PackageInstallMode,
    RuntimeIsolationProfile, RuntimeSecurityPolicy,
)

CORE_RELEASE = "3.55.0"
CONTRACT_VERSION = "sc.core.prolog-runtime.v1"
PROVIDER_VERSION = "1.0.0"
SWI_PROLOG_VERSION = "9.0.4"
SWI_PROLOG_PACKAGE_VERSION = "9.0.4+dfsg-3.1ubuntu4"
RUNTIME_ID = "sc-runtime-prolog"
ADAPTER_ID = "adapter:sc-runtime-prolog"
SERVICE_NAME = "sc-prolog-runtime"
SERVICE_ENDPOINT = "http://127.0.0.1:18104"

PROLOG_OPERATIONS = [
    "relation_reachable",
    "relation_paths_bounded",
    "transitive_closure",
    "contradiction_scan",
    "temporal_consistency",
    "graph_coloring",
]
_IDENT = re.compile(r"^[a-z][a-z0-9_]{0,63}$")

class PrologOperation(str, Enum):
    relation_reachable = "relation_reachable"
    relation_paths_bounded = "relation_paths_bounded"
    transitive_closure = "transitive_closure"
    contradiction_scan = "contradiction_scan"
    temporal_consistency = "temporal_consistency"
    graph_coloring = "graph_coloring"

class LogicEdge(BaseModel):
    source: str
    target: str
    @model_validator(mode="after")
    def validate_ids(self):
        if not _IDENT.fullmatch(self.source) or not _IDENT.fullmatch(self.target):
            raise ValueError("logic identifiers must match [a-z][a-z0-9_]{0,63}")
        return self

class PrologLogicInput(BaseModel):
    edges: list[LogicEdge] = Field(default_factory=list)
    source: str | None = None
    target: str | None = None
    max_depth: int = 4
    assertions: list[str] = Field(default_factory=list)
    negations: list[str] = Field(default_factory=list)
    temporal_edges: list[LogicEdge] = Field(default_factory=list)
    vertex_count: int | None = None
    undirected_edges: list[list[int]] = Field(default_factory=list)
    max_colors: int | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)

    def fingerprint(self): return canonical_sha256(self)

class PrologExecutionSettings(BaseModel):
    max_execution_seconds: int = Field(default=30, ge=1, le=300)
    max_solutions: int = Field(default=1000, ge=1, le=10000)
    metadata: dict[str, Any] = Field(default_factory=dict)

class PrologExecutionRequest(BaseModel):
    prolog_request_id: str = Field(min_length=2, max_length=500)
    operation: PrologOperation
    inputs: PrologLogicInput
    settings: PrologExecutionSettings = Field(default_factory=PrologExecutionSettings)
    computational_job_ref: str = Field(min_length=2, max_length=500)
    environment_package_ref: str = "environment-package:prolog-runtime:v1"
    security_policy_ref: str = "runtime-security-policy:prolog-runtime-standard:v1"
    provenance: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_operation(self):
        i=self.inputs
        for name in i.assertions+i.negations:
            if not _IDENT.fullmatch(name): raise ValueError("claim identifiers must be safe Prolog atoms")
        if self.operation in {PrologOperation.relation_reachable, PrologOperation.relation_paths_bounded}:
            if not i.edges or not i.source or not i.target: raise ValueError("relation query requires edges, source and target")
            if not _IDENT.fullmatch(i.source) or not _IDENT.fullmatch(i.target): raise ValueError("source/target must be safe atoms")
        if self.operation == PrologOperation.relation_paths_bounded and not 1 <= i.max_depth <= 12:
            raise ValueError("max_depth must be 1..12")
        if self.operation == PrologOperation.transitive_closure and not i.edges:
            raise ValueError("transitive_closure requires edges")
        if self.operation == PrologOperation.contradiction_scan and not (i.assertions or i.negations):
            raise ValueError("contradiction_scan requires assertions or negations")
        if self.operation == PrologOperation.temporal_consistency and not i.temporal_edges:
            raise ValueError("temporal_consistency requires temporal_edges")
        if self.operation == PrologOperation.graph_coloring:
            if i.vertex_count is None or not 1 <= i.vertex_count <= 256: raise ValueError("vertex_count must be 1..256")
            if i.max_colors is None or not 1 <= i.max_colors <= 16: raise ValueError("max_colors must be 1..16")
            for e in i.undirected_edges:
                if len(e)!=2 or any(isinstance(x,bool) or not isinstance(x,int) for x in e): raise ValueError("undirected edges must be integer pairs")
                if any(x<0 or x>=i.vertex_count for x in e) or e[0]==e[1]: raise ValueError("invalid graph-coloring edge")
        return self
    def fingerprint(self): return canonical_sha256(self)

class PrologRuntimeRegistration(BaseModel):
    registration_id: str
    runtime_id: str = RUNTIME_ID
    provider_version: str = PROVIDER_VERSION
    swi_prolog_version: str = SWI_PROLOG_VERSION
    swi_prolog_package_version: str = SWI_PROLOG_PACKAGE_VERSION
    adapter_id: str = ADAPTER_ID
    service_name: str = SERVICE_NAME
    endpoint: str = SERVICE_ENDPOINT
    operations: list[str] = Field(default_factory=lambda:list(PROLOG_OPERATIONS))
    runtime_contract: str = CONTRACT_VERSION
    runtime_kind: str = "language"
    language: str = "prolog"
    implementation: str = "SWI-Prolog"
    status: str = "active"
    metadata: dict[str, Any] = Field(default_factory=dict)
    def fingerprint(self): return canonical_sha256(self)

class PrologRuntimeBundle(BaseModel):
    bundle_id: str
    registration: PrologRuntimeRegistration
    environment_package: ReproducibleEnvironmentPackage
    security_policy: RuntimeSecurityPolicy
    reference_request: PrologExecutionRequest
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
    manifest=EnvironmentAsset(asset_id="environment-asset:prolog-runtime-manifest",kind=EnvironmentAssetKind.manifest,uri="core-ref://runtime-manifests/swi-prolog-9.0.4-noble.json",content_sha256="3"*64,media_type="application/json",size_bytes=512)
    req=EnvironmentAsset(asset_id="environment-asset:prolog-provider-requirements",kind=EnvironmentAssetKind.lockfile,uri="core-ref://runtime-locks/prolog-provider-requirements.txt",content_sha256="4"*64,media_type="text/plain",size_bytes=256)
    return ReproducibleEnvironmentPackage(
        environment_package_id="environment-package:prolog-runtime:v1",name="Sustainable Catalyst Prolog Runtime Environment",package_version="1.0.0",
        platform=PlatformDescriptor(operating_system="Ubuntu",operating_system_version="24.04",architecture=PlatformArchitecture.amd64,libc="glibc",kernel_family="linux"),
        runtimes=[RuntimeEnvironmentRequirement(runtime_requirement_id="runtime-requirement:prolog-provider",runtime_ref=RUNTIME_ID,runtime_version=PROVIDER_VERSION,runtime_adapter_ref=ADAPTER_ID)],
        system_packages=[SystemPackageRequirement(requirement_id="system-package:swi-prolog-nox",manager=PackageManager.apt,name="swi-prolog-nox",version=SWI_PROLOG_PACKAGE_VERSION,source=RequirementSource.operating_system)],
        language_packages=[],
        environment_variables=[EnvironmentVariableDeclaration(variable_id="environment-variable:prolog-artifact-root",name="SC_PROLOG_ARTIFACT_ROOT",kind=EnvironmentVariableKind.path,value="/var/lib/sc-prolog-runtime/artifacts")],
        assets=[manifest,req],
        build_instructions=[
            EnvironmentBuildInstruction(instruction_id="build-instruction:prolog-runtime",ordinal=1,action="install-pinned-swi-prolog",manager=PackageManager.apt,requirement_refs=["system-package:swi-prolog-nox"]),
            EnvironmentBuildInstruction(instruction_id="build-instruction:prolog-provider",ordinal=2,action="install-provider-python-dependencies",manager=PackageManager.pip,artifact_ref=req.asset_id),
            EnvironmentBuildInstruction(instruction_id="build-instruction:prolog-smoke",ordinal=3,action="run-bounded-prolog-logic-smoke-test"),
        ],
        source_environment_ref="runtime-environment:prolog-provider:v1",source_job_refs=[],source_workflow_refs=[],state=EnvironmentPackageState.verified,
        provenance={"source_release":CORE_RELEASE,"core_builds_environment":False,"execution_host_builds_environment":True},
        metadata={"swi_prolog_version":SWI_PROLOG_VERSION,"swi_prolog_package_version":SWI_PROLOG_PACKAGE_VERSION,"arbitrary_prolog_source":False},
    )

def reference_security_policy():
    isolation=RuntimeIsolationProfile(isolation_profile_id="isolation-profile:prolog-runtime-standard:v1",mechanism=IsolationMechanism.process,network_mode=NetworkAccessMode.none,filesystem_mode=FilesystemAccessMode.allowlist,package_install_mode=PackageInstallMode.denied,process_namespace_isolated=True,user_namespace_isolated=True,privilege_escalation_allowed=False,host_filesystem_mounted=False,shell_allowed=False,arbitrary_code_allowed=False,outbound_artifact_egress_allowed=True,resource_budget_ref="resource-budget:prolog-runtime-standard:v1",syscall_policy_ref="syscall-policy:prolog-runtime-standard:v1")
    return RuntimeSecurityPolicy(security_policy_id="runtime-security-policy:prolog-runtime-standard:v1",policy_version="1.0.0",name="Prolog Runtime Standard Policy",isolation_profile=isolation,allowed_runtime_refs=[RUNTIME_ID],allowed_adapter_refs=[ADAPTER_ID],allowed_operations={RUNTIME_ID:list(PROLOG_OPERATIONS)},allowed_filesystem_prefixes=["/workspace","/tmp/sc-prolog-runtime","/var/lib/sc-prolog-runtime/artifacts","/var/lib/sc-prolog-runtime/work"],allowed_artifact_egress_classes=["research-artifact","logic-result","prolog-diagnostics"],execution_policy_ref="execution-policy:prolog-runtime-standard:v1",provenance={"source_release":CORE_RELEASE,"policy_owner":"platform-governance"},metadata={"arbitrary_prolog_source_allowed":False,"runtime_package_install_allowed":False,"caller_filesystem_paths_allowed":False,"provider_generated_programs":True})

def reference_runtime_bundle():
    req=PrologExecutionRequest(prolog_request_id="prolog-request:reference-reachability:001",operation=PrologOperation.relation_reachable,inputs=PrologLogicInput(edges=[LogicEdge(source="source_a",target="entity_b"),LogicEdge(source="entity_b",target="target_c")],source="source_a",target="target_c"),computational_job_ref="job:prolog-reference-reachability:001",provenance={"originating_product":"research-lab","execution_owner":"workspace-or-execution-host"})
    return PrologRuntimeBundle(bundle_id="prolog-runtime-bundle:reference:v1",registration=PrologRuntimeRegistration(registration_id="prolog-runtime-registration:v1",metadata={"arbitrary_prolog_source":False,"provider_generated_programs":True,"logic_role":"logic-constraint-reasoning"}),environment_package=reference_environment_package(),security_policy=reference_security_policy(),reference_request=req,source_object_refs=["python-runtime-bundle:reference:v1","unified-runtime-catalog:platform-core:v1"],metadata={"reference_is_contract_proof":True,"live_provider_execution_occurs_outside_core":True})

def to_scientific_prolog_artifact(bundle):
    return {"artifact_id":f"scientific-artifact:{bundle.bundle_id}","artifact_kind":"package","uri":f"core-ref://{bundle.bundle_id}","content_sha256":bundle.fingerprint(),"media_type":"application/vnd.sustainable-catalyst.prolog-runtime+json","source_contract":CONTRACT_VERSION,"source_object_ref":bundle.bundle_id,"metadata":{"runtime_id":bundle.registration.runtime_id,"provider_version":bundle.registration.provider_version,"swi_prolog_version":bundle.registration.swi_prolog_version,"reference_operation":bundle.reference_request.operation.value}}

def contract_document():
    b=reference_runtime_bundle()
    return {"ok":True,"release":CORE_RELEASE,"contract":CONTRACT_VERSION,"provider_version":PROVIDER_VERSION,"swi_prolog_version":SWI_PROLOG_VERSION,"swi_prolog_package_version":SWI_PROLOG_PACKAGE_VERSION,"runtime_id":RUNTIME_ID,"adapter_id":ADAPTER_ID,"language":"prolog","implementation":"SWI-Prolog","operations":list(PROLOG_OPERATIONS),"capabilities":{"logic_constraint_reasoning":True,"relation_reasoning":True,"graph_reasoning":True,"contradiction_analysis":True,"temporal_reasoning":True,"constraint_solving":True,"reproducible_environment_package":True,"runtime_security_policy":True,"runtime_adapter_registration":True,"unified_runtime_catalog_integration":True,"workspace_product_profile_integration":True,"research_lab_product_profile_integration":True,"scientific_registry_bridge":True},"boundaries":{"core_executes_prolog":False,"provider_executes_prolog":True,"arbitrary_prolog_source":False,"shell_execution":False,"runtime_package_install_via_api":False,"caller_filesystem_paths":False,"core_infers_facts":False,"core_certifies_truth":False,"core_selects_investigative_conclusion":False},"reference":{"bundle_id":b.bundle_id,"environment_package_id":b.environment_package.environment_package_id,"security_policy_id":b.security_policy.security_policy_id,"reference_request_id":b.reference_request.prolog_request_id,"reference_operation":b.reference_request.operation.value,"bundle_fingerprint_sha256":b.fingerprint()}}
