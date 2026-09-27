from __future__ import annotations

import hashlib
import json
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, model_validator

CORE_RELEASE = "3.56.1"
CONTRACT_VERSION = "sc.core.jvm-language-profiles.v1"
RUNTIME_ID = "sc-runtime-jvm"
ADAPTER_ID = "adapter:sc-runtime-jvm"
JVM_MAJOR_VERSION = "21"
JVM_PROVIDER_VERSION = "1.0.0"

JAVA_PROFILE_ID = "jvm-language-profile:java-21"
KOTLIN_PROFILE_ID = "jvm-language-profile:kotlin-2.4.20"
SCALA_PROFILE_ID = "jvm-language-profile:scala-3.9.0"


def canonical_sha256(value: Any) -> str:
    if hasattr(value, "model_dump"):
        value = value.model_dump(mode="json", exclude_none=True)
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


class JVMLanguage(str, Enum):
    java = "java"
    kotlin = "kotlin"
    scala = "scala"


class JVMProfileStatus(str, Enum):
    registered = "registered"
    active = "active"
    unavailable = "unavailable"


class JVMLanguageProfile(BaseModel):
    profile_id: str = Field(min_length=2, max_length=500)
    language: JVMLanguage
    language_version: str
    runtime_ref: str = RUNTIME_ID
    runtime_version: str = JVM_PROVIDER_VERSION
    runtime_adapter_ref: str = ADAPTER_ID
    execution_target: str = "OpenJDK JVM 21"
    bytecode_target: str
    compiler: str
    compiler_distribution: str
    source_extensions: list[str]
    compile_strategy: str
    run_strategy: str
    arbitrary_source_allowed: bool = False
    caller_classpath_allowed: bool = False
    dependency_install_allowed: bool = False
    network_access_allowed: bool = False
    status: JVMProfileStatus = JVMProfileStatus.registered
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_profile(self):
        if self.runtime_ref != RUNTIME_ID or self.runtime_adapter_ref != ADAPTER_ID:
            raise ValueError("JVM language profile runtime binding mismatch")
        if self.arbitrary_source_allowed or self.caller_classpath_allowed or self.dependency_install_allowed:
            raise ValueError("JVM v1 language profiles must remain bounded")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class JVMLanguageProfileCatalog(BaseModel):
    catalog_id: str = "jvm-language-profile-catalog:platform-core:v1"
    runtime_ref: str = RUNTIME_ID
    runtime_version: str = JVM_PROVIDER_VERSION
    profiles: list[JVMLanguageProfile]
    explicit_profile_binding_required: bool = True
    autonomous_profile_selection: bool = False
    allowed_products: list[str] = Field(default_factory=lambda: ["workspace", "research-lab", "workbench"])
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_catalog(self):
        ids = [p.profile_id for p in self.profiles]
        if len(ids) != len(set(ids)):
            raise ValueError("duplicate JVM language profile IDs")
        langs = [p.language.value for p in self.profiles]
        if langs != ["java", "kotlin", "scala"]:
            raise ValueError("canonical JVM profile order must be Java, Kotlin, Scala")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class JVMLanguageProfileResolutionRequest(BaseModel):
    resolution_id: str = Field(min_length=2, max_length=500)
    product_id: str
    profile_id: str
    runtime_ref: str = RUNTIME_ID
    operation: str | None = None
    computational_job_ref: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class JVMLanguageProfileResolution(BaseModel):
    resolution_id: str
    product_id: str
    profile_id: str
    runtime_ref: str
    runtime_adapter_ref: str
    language: JVMLanguage
    language_version: str
    execution_target: str
    mode: str = "explicit-profile-binding-validated"
    status: str = "resolved"
    metadata: dict[str, Any] = Field(default_factory=dict)

    def fingerprint(self) -> str:
        return canonical_sha256(self)


def canonical_profiles() -> list[JVMLanguageProfile]:
    return [
        JVMLanguageProfile(
            profile_id=JAVA_PROFILE_ID,
            language=JVMLanguage.java,
            language_version="21",
            bytecode_target="Java 21 classfile / JVM 21",
            compiler="javac",
            compiler_distribution="OpenJDK 21",
            source_extensions=[".java"],
            compile_strategy="provider-managed-javac-release-21",
            run_strategy="provider-managed-java-classpath",
            status=JVMProfileStatus.active,
            metadata={"toolchain_class": "platform-jdk", "production_certification": "mandatory"},
        ),
        JVMLanguageProfile(
            profile_id=KOTLIN_PROFILE_ID,
            language=JVMLanguage.kotlin,
            language_version="2.4.20",
            bytecode_target="JVM bytecode on OpenJDK 21",
            compiler="kotlinc",
            compiler_distribution="JetBrains Kotlin compiler 2.4.20",
            source_extensions=[".kt", ".kts"],
            compile_strategy="provider-managed-kotlinc-pinned-toolchain",
            run_strategy="provider-managed-java-jar-or-classpath",
            status=JVMProfileStatus.active,
            metadata={
                "toolchain_source": "JetBrains versioned release archive",
                "toolchain_sha256": "59e9ca74c7904ef2c122b12114937673ccce68de820a663f0ed66ccf8799e0b7",
                "production_certification": "mandatory",
            },
        ),
        JVMLanguageProfile(
            profile_id=SCALA_PROFILE_ID,
            language=JVMLanguage.scala,
            language_version="3.9.0",
            bytecode_target="JVM bytecode on OpenJDK 21",
            compiler="scalac",
            compiler_distribution="Scala 3.9.0 LTS distribution",
            source_extensions=[".scala", ".sc"],
            compile_strategy="provider-managed-scalac-pinned-toolchain",
            run_strategy="provider-managed-scala-classpath",
            status=JVMProfileStatus.active,
            metadata={
                "toolchain_source": "Scala versioned release archive",
                "archive_sha256_recorded_at_deploy": True,
                "production_certification": "mandatory",
            },
        ),
    ]


def reference_catalog() -> JVMLanguageProfileCatalog:
    return JVMLanguageProfileCatalog(
        profiles=canonical_profiles(),
        metadata={
            "contract": CONTRACT_VERSION,
            "core_release": CORE_RELEASE,
            "jvm_major_version": JVM_MAJOR_VERSION,
            "provider_version": JVM_PROVIDER_VERSION,
            "profile_count": 3,
            "spark_adapter_deferred_to": "3.56.2",
        },
    )


def resolve_profile(request: JVMLanguageProfileResolutionRequest) -> JVMLanguageProfileResolution:
    catalog = reference_catalog()
    if request.runtime_ref != RUNTIME_ID:
        raise ValueError("language profile may only bind to sc-runtime-jvm")
    if request.product_id not in catalog.allowed_products:
        raise ValueError("product is not allowed to use JVM language profiles")
    profile = next((p for p in catalog.profiles if p.profile_id == request.profile_id), None)
    if profile is None:
        raise ValueError("unknown JVM language profile")
    return JVMLanguageProfileResolution(
        resolution_id=request.resolution_id,
        product_id=request.product_id,
        profile_id=profile.profile_id,
        runtime_ref=RUNTIME_ID,
        runtime_adapter_ref=ADAPTER_ID,
        language=profile.language,
        language_version=profile.language_version,
        execution_target=profile.execution_target,
        metadata={
            "operation": request.operation,
            "computational_job_ref": request.computational_job_ref,
            "core_autonomously_selected_profile": False,
            "explicit_profile_binding_present": True,
            "profile_fingerprint_sha256": profile.fingerprint(),
        },
    )


def to_scientific_profile_artifact(catalog: JVMLanguageProfileCatalog | None = None) -> dict[str, Any]:
    catalog = catalog or reference_catalog()
    return {
        "artifact_id": "scientific-artifact:jvm-language-profile-catalog:v1",
        "artifact_kind": "runtime-profile-catalog",
        "uri": "core-ref://jvm-language-profile-catalog:platform-core:v1",
        "content_sha256": catalog.fingerprint(),
        "media_type": "application/vnd.sustainable-catalyst.jvm-language-profiles+json",
        "source_contract": CONTRACT_VERSION,
        "source_object_ref": catalog.catalog_id,
        "metadata": {
            "runtime_id": RUNTIME_ID,
            "runtime_version": JVM_PROVIDER_VERSION,
            "profile_ids": [p.profile_id for p in catalog.profiles],
        },
    }


def contract_document() -> dict[str, Any]:
    catalog = reference_catalog()
    return {
        "ok": True,
        "release": CORE_RELEASE,
        "contract": CONTRACT_VERSION,
        "runtime_id": RUNTIME_ID,
        "runtime_version": JVM_PROVIDER_VERSION,
        "runtime_adapter_id": ADAPTER_ID,
        "jvm_major_version": JVM_MAJOR_VERSION,
        "profile_count": len(catalog.profiles),
        "profiles": [
            {"profile_id": p.profile_id, "language": p.language.value, "language_version": p.language_version, "status": p.status.value}
            for p in catalog.profiles
        ],
        "capabilities": {
            "java_profile": True,
            "kotlin_profile": True,
            "scala_profile": True,
            "explicit_profile_binding": True,
            "profile_toolchain_provenance": True,
            "profile_product_integration": True,
            "scientific_registry_bridge": True,
        },
        "boundaries": {
            "arbitrary_java_source": False,
            "arbitrary_kotlin_source": False,
            "arbitrary_scala_source": False,
            "caller_classpath": False,
            "runtime_dependency_install_via_api": False,
            "network_access": False,
            "core_autonomously_selects_language_profile": False,
            "spark_adapter_deferred_to": "3.56.2",
        },
        "reference": {
            "catalog_id": catalog.catalog_id,
            "catalog_fingerprint_sha256": catalog.fingerprint(),
        },
    }
