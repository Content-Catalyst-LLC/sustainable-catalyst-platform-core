from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, model_validator

from .computational_runtime_objects import canonical_sha256

CORE_RELEASE = "3.45.0"
CONTRACT_VERSION = "sc.core.runtime-fabric-production-certification.v1"

UNIFIED_RUNTIME_CONTRACT = "sc.core.unified-runtime-api.v1"
RUNTIME_SECURITY_CONTRACT = "sc.core.runtime-security-governance.v1"
VERIFICATION_REPRODUCTION_CONTRACT = "sc.core.verification-reproduction-engine.v1"
ENVIRONMENT_PACKAGE_CONTRACT = "sc.core.reproducible-environment-package.v1"
CROSS_RUNTIME_WORKFLOW_CONTRACT = "sc.core.cross-runtime-research-workflow.v1"
RUNTIME_INTERCHANGE_CONTRACT = "sc.core.runtime-data-interchange.v1"
SCIENTIFIC_REGISTRY_CONTRACT = "sc.core.scientific-result-artifact-registry.v1"
COMPUTATIONAL_JOB_CONTRACT = "sc.core.computational-job.v1"
RUNTIME_ADAPTER_CONTRACT = "sc.core.runtime-adapter.v1"

REFERENCE_R_RUNTIME = "sc-runtime-r"
REFERENCE_R_VERSION = "1.0.0"
REFERENCE_R_ADAPTER = "adapter:sc-runtime-r"
REFERENCE_JULIA_RUNTIME = "catalyst-julia-runtime"
REFERENCE_JULIA_VERSION = "0.3.0"
REFERENCE_JULIA_ADAPTER = "adapter:catalyst-julia-runtime"


class CertificationDomain(str, Enum):
    release_identity = "release-identity"
    core_health = "core-health"
    contract_integrity = "contract-integrity"
    runtime_registration = "runtime-registration"
    runtime_catalog = "runtime-catalog"
    security_governance = "security-governance"
    environment_reproducibility = "environment-reproducibility"
    runtime_interchange = "runtime-interchange"
    cross_runtime_workflow = "cross-runtime-workflow"
    reproduction_verification = "reproduction-verification"
    product_runtime_profiles = "product-runtime-profiles"
    scientific_registry = "scientific-registry"


class CriterionSeverity(str, Enum):
    blocker = "blocker"
    required = "required"
    advisory = "advisory"


class EvidenceStatus(str, Enum):
    observed = "observed"
    unavailable = "unavailable"
    invalid = "invalid"


class CriterionOutcome(str, Enum):
    passed = "passed"
    warning = "warning"
    failed = "failed"
    not_run = "not-run"


class CertificationStatus(str, Enum):
    certified = "certified"
    certified_with_warnings = "certified-with-warnings"
    not_certified = "not-certified"
    incomplete = "incomplete"


class ProviderCertificationStatus(str, Enum):
    certified = "certified"
    not_certified = "not-certified"


class ProductProfileCertificationStatus(str, Enum):
    contract_ready = "contract-ready"
    not_ready = "not-ready"


class ProductionCertificationCriterion(BaseModel):
    criterion_id: str = Field(min_length=2, max_length=500)
    domain: CertificationDomain
    name: str = Field(min_length=1, max_length=500)
    severity: CriterionSeverity = CriterionSeverity.required
    expected_value: Any | None = None
    evidence_source_ref: str = Field(min_length=2, max_length=1000)
    notes: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class ProductionCertificationEvidence(BaseModel):
    evidence_id: str = Field(min_length=2, max_length=500)
    criterion_ref: str = Field(min_length=2, max_length=500)
    status: EvidenceStatus = EvidenceStatus.observed
    source_ref: str = Field(min_length=2, max_length=1000)
    observed_value: Any | None = None
    content_sha256: str | None = Field(default=None, pattern=r"^[0-9a-f]{64}$")
    collected_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    provenance: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)

    def fingerprint(self) -> str:
        payload = self.model_dump(mode="json", exclude_none=True)
        payload.pop("collected_at", None)
        return canonical_sha256(payload)


class ProductionCriterionResult(BaseModel):
    criterion_ref: str = Field(min_length=2, max_length=500)
    outcome: CriterionOutcome
    evidence_ref: str | None = Field(default=None, max_length=500)
    expected_value: Any | None = None
    observed_value: Any | None = None
    notes: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class RuntimeProviderCertification(BaseModel):
    provider_certification_id: str = Field(min_length=2, max_length=500)
    runtime_ref: str = Field(min_length=2, max_length=500)
    runtime_version: str = Field(min_length=1, max_length=200)
    runtime_adapter_ref: str = Field(min_length=2, max_length=500)
    adapter_contract: str = Field(min_length=2, max_length=300)
    provider_status: ProviderCertificationStatus
    required_operation_refs: list[str] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_provider(self):
        if len(self.required_operation_refs) != len(set(self.required_operation_refs)):
            raise ValueError("provider required operations must be unique")
        if len(self.evidence_refs) != len(set(self.evidence_refs)):
            raise ValueError("provider evidence refs must be unique")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class ProductRuntimeProfileCertification(BaseModel):
    product_certification_id: str = Field(min_length=2, max_length=500)
    product_id: str = Field(min_length=1, max_length=200)
    product_profile_ref: str = Field(min_length=2, max_length=500)
    status: ProductProfileCertificationStatus
    allowed_runtime_refs: list[str] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)
    product_repository_integration_certified: bool = False
    notes: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_product(self):
        if len(self.allowed_runtime_refs) != len(set(self.allowed_runtime_refs)):
            raise ValueError("product allowed runtime refs must be unique")
        if len(self.evidence_refs) != len(set(self.evidence_refs)):
            raise ValueError("product evidence refs must be unique")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class RuntimeFabricCertificationPlan(BaseModel):
    certification_plan_id: str = Field(min_length=2, max_length=500)
    target_release: str = Field(min_length=1, max_length=100)
    target_tag: str = Field(min_length=1, max_length=100)
    criteria: list[ProductionCertificationCriterion] = Field(default_factory=list)
    required_runtime_refs: list[str] = Field(default_factory=list)
    required_product_profile_refs: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_plan(self):
        if not self.criteria:
            raise ValueError("production certification plan requires criteria")
        ids = [item.criterion_id for item in self.criteria]
        if len(ids) != len(set(ids)):
            raise ValueError("certification criterion ids must be unique")
        if len(self.required_runtime_refs) != len(set(self.required_runtime_refs)):
            raise ValueError("required runtime refs must be unique")
        if len(self.required_product_profile_refs) != len(set(self.required_product_profile_refs)):
            raise ValueError("required product profile refs must be unique")
        return self

    def fingerprint(self) -> str:
        payload = self.model_dump(mode="json", exclude_none=True)
        payload.pop("created_at", None)
        return canonical_sha256(payload)


class RuntimeFabricCertificationAssessment(BaseModel):
    assessment_id: str = Field(min_length=2, max_length=500)
    certification_plan_ref: str = Field(min_length=2, max_length=500)
    certification_plan_fingerprint_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    results: list[ProductionCriterionResult] = Field(default_factory=list)
    evidence: list[ProductionCertificationEvidence] = Field(default_factory=list)
    provider_certifications: list[RuntimeProviderCertification] = Field(default_factory=list)
    product_profile_certifications: list[ProductRuntimeProfileCertification] = Field(default_factory=list)
    status: CertificationStatus
    blocker_failures: list[str] = Field(default_factory=list)
    required_failures: list[str] = Field(default_factory=list)
    advisory_warnings: list[str] = Field(default_factory=list)
    assessed_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_assessment(self):
        result_refs = [item.criterion_ref for item in self.results]
        if len(result_refs) != len(set(result_refs)):
            raise ValueError("criterion results must be unique")
        evidence_ids = [item.evidence_id for item in self.evidence]
        if len(evidence_ids) != len(set(evidence_ids)):
            raise ValueError("certification evidence ids must be unique")
        known_evidence = set(evidence_ids)
        for result in self.results:
            if result.evidence_ref and result.evidence_ref not in known_evidence:
                raise ValueError("criterion result references unknown evidence")
        if self.status == CertificationStatus.certified and (
            self.blocker_failures or self.required_failures or self.advisory_warnings
        ):
            raise ValueError("certified assessment cannot contain failures or warnings")
        if self.status == CertificationStatus.certified_with_warnings and (
            self.blocker_failures or self.required_failures
        ):
            raise ValueError("certified-with-warnings cannot contain blocker/required failures")
        if self.status == CertificationStatus.not_certified and not (
            self.blocker_failures or self.required_failures
        ):
            raise ValueError("not-certified assessment requires blocker or required failure")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256({
            "assessment_id": self.assessment_id,
            "certification_plan_ref": self.certification_plan_ref,
            "certification_plan_fingerprint_sha256": self.certification_plan_fingerprint_sha256,
            "result_fingerprints": sorted(item.fingerprint() for item in self.results),
            "evidence_fingerprints": sorted(item.fingerprint() for item in self.evidence),
            "provider_fingerprints": sorted(item.fingerprint() for item in self.provider_certifications),
            "product_profile_fingerprints": sorted(
                item.fingerprint() for item in self.product_profile_certifications
            ),
            "status": self.status.value,
            "blocker_failures": sorted(self.blocker_failures),
            "required_failures": sorted(self.required_failures),
            "advisory_warnings": sorted(self.advisory_warnings),
            "metadata": self.metadata,
        })


class RuntimeFabricProductionCertificate(BaseModel):
    certificate_id: str = Field(min_length=2, max_length=500)
    certified_release: str = Field(min_length=1, max_length=100)
    certified_tag: str = Field(min_length=1, max_length=100)
    certification_contract: str = CONTRACT_VERSION
    assessment: RuntimeFabricCertificationAssessment
    issuer_ref: str = Field(min_length=2, max_length=500)
    production_target_ref: str = Field(min_length=2, max_length=1000)
    issued_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    source_object_refs: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_certificate(self):
        if self.assessment.status not in {
            CertificationStatus.certified,
            CertificationStatus.certified_with_warnings,
        }:
            raise ValueError("production certificate requires certifiable assessment")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256({
            "certificate_id": self.certificate_id,
            "certified_release": self.certified_release,
            "certified_tag": self.certified_tag,
            "certification_contract": self.certification_contract,
            "assessment_fingerprint_sha256": self.assessment.fingerprint(),
            "issuer_ref": self.issuer_ref,
            "production_target_ref": self.production_target_ref,
            "source_object_refs": sorted(self.source_object_refs),
            "metadata": self.metadata,
        })


def evaluate_criterion(
    criterion: ProductionCertificationCriterion,
    evidence: ProductionCertificationEvidence | None,
) -> ProductionCriterionResult:
    if evidence is None:
        return ProductionCriterionResult(
            criterion_ref=criterion.criterion_id,
            outcome=CriterionOutcome.not_run,
            expected_value=criterion.expected_value,
            notes=["certification evidence unavailable"],
        )
    if evidence.criterion_ref != criterion.criterion_id:
        raise ValueError("evidence criterion_ref mismatch")

    if evidence.status != EvidenceStatus.observed:
        outcome = CriterionOutcome.failed if criterion.severity != CriterionSeverity.advisory else CriterionOutcome.warning
    else:
        outcome = (
            CriterionOutcome.passed
            if evidence.observed_value == criterion.expected_value
            else (
                CriterionOutcome.warning
                if criterion.severity == CriterionSeverity.advisory
                else CriterionOutcome.failed
            )
        )

    return ProductionCriterionResult(
        criterion_ref=criterion.criterion_id,
        outcome=outcome,
        evidence_ref=evidence.evidence_id,
        expected_value=criterion.expected_value,
        observed_value=evidence.observed_value,
    )


def assess_runtime_fabric(
    *,
    plan: RuntimeFabricCertificationPlan,
    evidence: list[ProductionCertificationEvidence],
    provider_certifications: list[RuntimeProviderCertification],
    product_profile_certifications: list[ProductRuntimeProfileCertification],
    assessment_id: str = "runtime-fabric-certification-assessment:runtime-fabric:v1",
) -> RuntimeFabricCertificationAssessment:
    evidence_by_criterion: dict[str, ProductionCertificationEvidence] = {}
    for item in evidence:
        if item.criterion_ref in evidence_by_criterion:
            raise ValueError("only one primary evidence object per certification criterion is supported")
        evidence_by_criterion[item.criterion_ref] = item

    results: list[ProductionCriterionResult] = []
    blockers: list[str] = []
    required: list[str] = []
    advisory: list[str] = []

    for criterion in plan.criteria:
        result = evaluate_criterion(criterion, evidence_by_criterion.get(criterion.criterion_id))
        results.append(result)
        if result.outcome == CriterionOutcome.passed:
            continue
        if criterion.severity == CriterionSeverity.blocker:
            blockers.append(criterion.criterion_id)
        elif criterion.severity == CriterionSeverity.required:
            required.append(criterion.criterion_id)
        else:
            advisory.append(criterion.criterion_id)

    providers_by_runtime = {item.runtime_ref: item for item in provider_certifications}
    for runtime_ref in plan.required_runtime_refs:
        item = providers_by_runtime.get(runtime_ref)
        if item is None or item.provider_status != ProviderCertificationStatus.certified:
            blockers.append(f"provider:{runtime_ref}")

    products_by_ref = {item.product_profile_ref: item for item in product_profile_certifications}
    for product_ref in plan.required_product_profile_refs:
        item = products_by_ref.get(product_ref)
        if item is None or item.status != ProductProfileCertificationStatus.contract_ready:
            required.append(f"product-profile:{product_ref}")

    blockers = sorted(set(blockers))
    required = sorted(set(required))
    advisory = sorted(set(advisory))

    if blockers or required:
        status = CertificationStatus.not_certified
    elif advisory:
        status = CertificationStatus.certified_with_warnings
    else:
        status = CertificationStatus.certified

    return RuntimeFabricCertificationAssessment(
        assessment_id=assessment_id,
        certification_plan_ref=plan.certification_plan_id,
        certification_plan_fingerprint_sha256=plan.fingerprint(),
        results=results,
        evidence=evidence,
        provider_certifications=provider_certifications,
        product_profile_certifications=product_profile_certifications,
        status=status,
        blocker_failures=blockers,
        required_failures=required,
        advisory_warnings=advisory,
        metadata={
            "production_certificate_scope": "platform-core-runtime-fabric",
            "external_product_repository_integration_certified": False,
            "scientific_validity_certified": False,
        },
    )



def issue_production_certificate(
    *,
    assessment: RuntimeFabricCertificationAssessment,
    production_target_ref: str,
    issuer_ref: str,
    certificate_id: str = "runtime-fabric-production-certificate:production:v1",
    source_object_refs: list[str] | None = None,
    metadata: dict[str, Any] | None = None,
) -> RuntimeFabricProductionCertificate:
    return RuntimeFabricProductionCertificate(
        certificate_id=certificate_id,
        certified_release=CORE_RELEASE,
        certified_tag="v3.45.0",
        assessment=assessment,
        issuer_ref=issuer_ref,
        production_target_ref=production_target_ref,
        source_object_refs=source_object_refs or [],
        metadata={
            "certificate_kind": "live-production",
            "external_product_repository_integration_certified": False,
            "scientific_validity_certified": False,
            **(metadata or {}),
        },
    )

def reference_certification_plan() -> RuntimeFabricCertificationPlan:
    criteria = [
        ProductionCertificationCriterion(
            criterion_id="criterion:release-version",
            domain=CertificationDomain.release_identity,
            name="Platform Core release version matches certification target",
            severity=CriterionSeverity.blocker,
            expected_value=CORE_RELEASE,
            evidence_source_ref="core://health.version",
        ),
        ProductionCertificationCriterion(
            criterion_id="criterion:release-tag",
            domain=CertificationDomain.release_identity,
            name="Production Git tag matches release",
            severity=CriterionSeverity.blocker,
            expected_value="v3.45.0",
            evidence_source_ref="git://production/tag",
        ),
        ProductionCertificationCriterion(
            criterion_id="criterion:core-health",
            domain=CertificationDomain.core_health,
            name="Platform Core health is ready",
            severity=CriterionSeverity.blocker,
            expected_value=True,
            evidence_source_ref="core://health",
        ),
        ProductionCertificationCriterion(
            criterion_id="criterion:unified-runtime-contract",
            domain=CertificationDomain.contract_integrity,
            name="Unified runtime API contract is available",
            severity=CriterionSeverity.blocker,
            expected_value=UNIFIED_RUNTIME_CONTRACT,
            evidence_source_ref="core://public/v1/unified-runtime/contract",
        ),
        ProductionCertificationCriterion(
            criterion_id="criterion:r-provider",
            domain=CertificationDomain.runtime_registration,
            name="R runtime provider is registered",
            severity=CriterionSeverity.blocker,
            expected_value=REFERENCE_R_VERSION,
            evidence_source_ref=f"core://runtime-adapters/{REFERENCE_R_ADAPTER}",
        ),
        ProductionCertificationCriterion(
            criterion_id="criterion:julia-provider",
            domain=CertificationDomain.runtime_registration,
            name="Julia runtime provider is registered",
            severity=CriterionSeverity.blocker,
            expected_value=REFERENCE_JULIA_VERSION,
            evidence_source_ref=f"core://runtime-adapters/{REFERENCE_JULIA_ADAPTER}",
        ),
        ProductionCertificationCriterion(
            criterion_id="criterion:runtime-catalog",
            domain=CertificationDomain.runtime_catalog,
            name="Unified runtime catalog contains R and Julia",
            severity=CriterionSeverity.required,
            expected_value=[REFERENCE_R_RUNTIME, REFERENCE_JULIA_RUNTIME],
            evidence_source_ref="core://api/v1/unified-runtime/catalog",
        ),
        ProductionCertificationCriterion(
            criterion_id="criterion:security-governance",
            domain=CertificationDomain.security_governance,
            name="Runtime security governance reference is valid",
            severity=CriterionSeverity.blocker,
            expected_value=["allow", "allow", "deny"],
            evidence_source_ref="core://api/v1/runtime-security/reference",
        ),
        ProductionCertificationCriterion(
            criterion_id="criterion:environment-verification",
            domain=CertificationDomain.environment_reproducibility,
            name="Reference reproducible environment is verified",
            severity=CriterionSeverity.required,
            expected_value="passed",
            evidence_source_ref="core://api/v1/reproducible-environments/reference",
        ),
        ProductionCertificationCriterion(
            criterion_id="criterion:interchange-verification",
            domain=CertificationDomain.runtime_interchange,
            name="R to Julia interchange verification passes",
            severity=CriterionSeverity.required,
            expected_value="passed",
            evidence_source_ref="core://api/v1/runtime-data-interchange/reference",
        ),
        ProductionCertificationCriterion(
            criterion_id="criterion:workflow-verification",
            domain=CertificationDomain.cross_runtime_workflow,
            name="Reference cross-runtime workflow verification passes",
            severity=CriterionSeverity.required,
            expected_value="passed",
            evidence_source_ref="core://api/v1/cross-runtime-workflows/reference",
        ),
        ProductionCertificationCriterion(
            criterion_id="criterion:reproduction-verification",
            domain=CertificationDomain.reproduction_verification,
            name="Reference reproduction comparison is equivalent",
            severity=CriterionSeverity.required,
            expected_value="equivalent",
            evidence_source_ref="core://api/v1/verification-reproduction/reference",
        ),
        ProductionCertificationCriterion(
            criterion_id="criterion:product-profiles",
            domain=CertificationDomain.product_runtime_profiles,
            name="Workspace, Research Lab and Workbench profiles are contract-ready",
            severity=CriterionSeverity.required,
            expected_value=["workspace", "research-lab", "workbench"],
            evidence_source_ref="core://api/v1/unified-runtime/product-profiles",
        ),
        ProductionCertificationCriterion(
            criterion_id="criterion:scientific-registry-bridge",
            domain=CertificationDomain.scientific_registry,
            name="Unified runtime reference exposes scientific registry bridge",
            severity=CriterionSeverity.required,
            expected_value=True,
            evidence_source_ref="core://api/v1/unified-runtime/reference",
        ),
    ]
    return RuntimeFabricCertificationPlan(
        certification_plan_id="runtime-fabric-certification-plan:production:v1",
        target_release=CORE_RELEASE,
        target_tag="v3.45.0",
        criteria=criteria,
        required_runtime_refs=[REFERENCE_R_RUNTIME, REFERENCE_JULIA_RUNTIME],
        required_product_profile_refs=[
            "product-runtime-profile:workspace:v1",
            "product-runtime-profile:research-lab:v1",
            "product-runtime-profile:workbench:v1",
        ],
        metadata={
            "scope": "platform-core-runtime-fabric",
            "external_product_repository_integration_certified": False,
            "live_deployment_script_supplies_production_evidence": True,
        },
    )


def reference_provider_certifications() -> list[RuntimeProviderCertification]:
    return [
        RuntimeProviderCertification(
            provider_certification_id="provider-certification:sc-runtime-r:1.0.0",
            runtime_ref=REFERENCE_R_RUNTIME,
            runtime_version=REFERENCE_R_VERSION,
            runtime_adapter_ref=REFERENCE_R_ADAPTER,
            adapter_contract=RUNTIME_ADAPTER_CONTRACT,
            provider_status=ProviderCertificationStatus.certified,
            required_operation_refs=[
                "descriptive_summary",
                "correlation_matrix",
                "linear_regression",
                "t_test",
                "one_way_anova",
            ],
            evidence_refs=["evidence:r-provider"],
            metadata={"arbitrary_code_execution": False},
        ),
        RuntimeProviderCertification(
            provider_certification_id="provider-certification:catalyst-julia-runtime:0.3.0",
            runtime_ref=REFERENCE_JULIA_RUNTIME,
            runtime_version=REFERENCE_JULIA_VERSION,
            runtime_adapter_ref=REFERENCE_JULIA_ADAPTER,
            adapter_contract=RUNTIME_ADAPTER_CONTRACT,
            provider_status=ProviderCertificationStatus.certified,
            required_operation_refs=["identity", "sum", "mean", "matrix_multiply"],
            evidence_refs=["evidence:julia-provider"],
            metadata={"arbitrary_code_execution": False},
        ),
    ]


def reference_product_profile_certifications() -> list[ProductRuntimeProfileCertification]:
    return [
        ProductRuntimeProfileCertification(
            product_certification_id="product-certification:workspace:v1",
            product_id="workspace",
            product_profile_ref="product-runtime-profile:workspace:v1",
            status=ProductProfileCertificationStatus.contract_ready,
            allowed_runtime_refs=[REFERENCE_R_RUNTIME, REFERENCE_JULIA_RUNTIME],
            evidence_refs=["evidence:product-profiles"],
            product_repository_integration_certified=False,
            notes=["Core-side runtime integration contract is certified; Workspace repository wiring is outside this certificate."],
        ),
        ProductRuntimeProfileCertification(
            product_certification_id="product-certification:research-lab:v1",
            product_id="research-lab",
            product_profile_ref="product-runtime-profile:research-lab:v1",
            status=ProductProfileCertificationStatus.contract_ready,
            allowed_runtime_refs=[REFERENCE_R_RUNTIME, REFERENCE_JULIA_RUNTIME],
            evidence_refs=["evidence:product-profiles"],
            product_repository_integration_certified=False,
        ),
        ProductRuntimeProfileCertification(
            product_certification_id="product-certification:workbench:v1",
            product_id="workbench",
            product_profile_ref="product-runtime-profile:workbench:v1",
            status=ProductProfileCertificationStatus.contract_ready,
            allowed_runtime_refs=[REFERENCE_R_RUNTIME, REFERENCE_JULIA_RUNTIME],
            evidence_refs=["evidence:product-profiles"],
            product_repository_integration_certified=False,
        ),
    ]


def reference_certification_evidence() -> list[ProductionCertificationEvidence]:
    values = {
        "criterion:release-version": CORE_RELEASE,
        "criterion:release-tag": "v3.45.0",
        "criterion:core-health": True,
        "criterion:unified-runtime-contract": UNIFIED_RUNTIME_CONTRACT,
        "criterion:r-provider": REFERENCE_R_VERSION,
        "criterion:julia-provider": REFERENCE_JULIA_VERSION,
        "criterion:runtime-catalog": [REFERENCE_R_RUNTIME, REFERENCE_JULIA_RUNTIME],
        "criterion:security-governance": ["allow", "allow", "deny"],
        "criterion:environment-verification": "passed",
        "criterion:interchange-verification": "passed",
        "criterion:workflow-verification": "passed",
        "criterion:reproduction-verification": "equivalent",
        "criterion:product-profiles": ["workspace", "research-lab", "workbench"],
        "criterion:scientific-registry-bridge": True,
    }
    return [
        ProductionCertificationEvidence(
            evidence_id=f"evidence:{criterion_id.split(':', 1)[1]}",
            criterion_ref=criterion_id,
            status=EvidenceStatus.observed,
            source_ref=f"reference-contract://{criterion_id}",
            observed_value=value,
            provenance={
                "reference_contract_proof": True,
                "live_production_evidence": False,
            },
        )
        for criterion_id, value in values.items()
    ]


def reference_runtime_fabric_certificate() -> RuntimeFabricProductionCertificate:
    plan = reference_certification_plan()
    assessment = assess_runtime_fabric(
        plan=plan,
        evidence=reference_certification_evidence(),
        provider_certifications=reference_provider_certifications(),
        product_profile_certifications=reference_product_profile_certifications(),
    )
    return RuntimeFabricProductionCertificate(
        certificate_id="runtime-fabric-production-certificate:reference:v1",
        certified_release=CORE_RELEASE,
        certified_tag="v3.45.0",
        assessment=assessment,
        issuer_ref="platform-core:certification-engine",
        production_target_ref="production-target:reference-contract-proof",
        source_object_refs=[
            "unified-runtime-api-bundle:research-lab:r-regression:v1",
            "runtime-security-governance-bundle:reference:v1",
            "reproduction-package:reference-r-julia:v1",
            "environment-package-bundle:reference-r-julia:v1",
            "cross-runtime-workflow-package:reference-r-julia:v1",
            "runtime-data-interchange-bundle:reference-r-julia:v1",
        ],
        metadata={
            "certificate_kind": "reference-contract-proof",
            "live_production_certification_occurs_in_deploy_verifier": True,
            "external_product_repository_integration_certified": False,
            "scientific_validity_certified": False,
        },
    )


def to_scientific_certification_artifact(
    certificate: RuntimeFabricProductionCertificate,
) -> dict[str, Any]:
    return {
        "artifact_id": f"scientific-artifact:{certificate.certificate_id}",
        "artifact_kind": "package",
        "uri": f"core-ref://{certificate.certificate_id}",
        "content_sha256": certificate.fingerprint(),
        "media_type": "application/vnd.sustainable-catalyst.runtime-fabric-certification+json",
        "source_contract": CONTRACT_VERSION,
        "source_object_ref": certificate.certificate_id,
        "metadata": {
            "certified_release": certificate.certified_release,
            "certified_tag": certificate.certified_tag,
            "certification_status": certificate.assessment.status.value,
            "provider_count": len(certificate.assessment.provider_certifications),
            "product_profile_count": len(certificate.assessment.product_profile_certifications),
        },
    }


def contract_document() -> dict[str, Any]:
    certificate = reference_runtime_fabric_certificate()
    assessment = certificate.assessment
    return {
        "ok": True,
        "release": CORE_RELEASE,
        "contract": CONTRACT_VERSION,
        "depends_on": [
            UNIFIED_RUNTIME_CONTRACT,
            RUNTIME_SECURITY_CONTRACT,
            VERIFICATION_REPRODUCTION_CONTRACT,
            ENVIRONMENT_PACKAGE_CONTRACT,
            CROSS_RUNTIME_WORKFLOW_CONTRACT,
            RUNTIME_INTERCHANGE_CONTRACT,
            SCIENTIFIC_REGISTRY_CONTRACT,
            COMPUTATIONAL_JOB_CONTRACT,
            RUNTIME_ADAPTER_CONTRACT,
        ],
        "object_types": [
            "ProductionCertificationCriterion",
            "ProductionCertificationEvidence",
            "ProductionCriterionResult",
            "RuntimeProviderCertification",
            "ProductRuntimeProfileCertification",
            "RuntimeFabricCertificationPlan",
            "RuntimeFabricCertificationAssessment",
            "RuntimeFabricProductionCertificate",
        ],
        "capabilities": {
            "release_identity_certification": True,
            "runtime_provider_certification": True,
            "unified_runtime_api_certification": True,
            "security_governance_certification": True,
            "environment_reproducibility_certification": True,
            "runtime_interchange_certification": True,
            "cross_runtime_workflow_certification": True,
            "reproduction_verification_certification": True,
            "product_profile_contract_certification": True,
            "scientific_registry_packaging": True,
            "blocker_required_advisory_gates": True,
            "portable_production_certificates": True,
        },
        "boundaries": {
            "reference_certificate_is_live_production_evidence": False,
            "deploy_verifier_supplies_live_production_evidence": True,
            "external_product_repository_integration_certified": False,
            "core_certifies_scientific_validity": False,
            "core_autonomously_selects_or_executes_runtime": False,
            "core_owns_runtime_fabric_certification_contracts_and_evidence_model": True,
        },
        "reference": {
            "certificate_id": certificate.certificate_id,
            "assessment_status": assessment.status.value,
            "blocker_failures": assessment.blocker_failures,
            "required_failures": assessment.required_failures,
            "advisory_warnings": assessment.advisory_warnings,
            "provider_runtime_refs": [
                item.runtime_ref for item in assessment.provider_certifications
            ],
            "product_profile_refs": [
                item.product_profile_ref
                for item in assessment.product_profile_certifications
            ],
            "certificate_fingerprint_sha256": certificate.fingerprint(),
        },
    }
