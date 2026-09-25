from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, model_validator

from .computational_runtime_objects import canonical_sha256

CORE_RELEASE = "3.36.0"
CONTRACT_VERSION = "sc.core.r-runtime-migration.v1"

LEGACY_ANALYTICAL_PROVIDER_CONTRACT = "sc.core.analytical-runtime-provider.v1"
COMPUTATIONAL_RUNTIME_CONTRACT = "sc.core.computational-runtime-object.v1"
RUNTIME_ADAPTER_CONTRACT = "sc.core.runtime-adapter.v1"
COMPUTATIONAL_JOB_CONTRACT = "sc.core.computational-job.v1"
ENVIRONMENT_PROVENANCE_CONTRACT = "sc.core.execution-environment-provenance.v1"
AI_RESEARCH_OBJECT_CONTRACT = "sc.core.ai-research-object-system.v1"

LEGACY_PROVIDER_ID = "catalyst-analytics-r"
LEGACY_PROVIDER_VERSION = "2.0.1"
RUNTIME_ID = "sc-runtime-r"
RUNTIME_VERSION = "1.0.0"
ADAPTER_ID = "adapter:sc-runtime-r"
DEFAULT_ENDPOINT = "http://127.0.0.1:18094"


class RRuntimeMigrationState(str, Enum):
    declared = "declared"
    compatibility = "compatibility"
    active = "active"
    retired = "retired"


class RCapabilityCategory(str, Enum):
    descriptive_statistics = "descriptive-statistics"
    correlation = "correlation"
    regression = "regression"
    hypothesis_testing = "hypothesis-testing"
    analysis_of_variance = "analysis-of-variance"
    distribution_summary = "distribution-summary"


class LegacyAnalyticsRIdentity(BaseModel):
    provider_id: str = LEGACY_PROVIDER_ID
    provider_version: str = LEGACY_PROVIDER_VERSION
    provider_contract: str = LEGACY_ANALYTICAL_PROVIDER_CONTRACT
    historical_runtime: str = "R"
    migration_role: str = "compatibility-source"

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class RRuntimeIdentity(BaseModel):
    runtime_id: str = RUNTIME_ID
    runtime_version: str = RUNTIME_VERSION
    adapter_id: str = ADAPTER_ID
    adapter_contract: str = RUNTIME_ADAPTER_CONTRACT
    runtime_contract: str = COMPUTATIONAL_RUNTIME_CONTRACT
    runtime_kind: str = "language"
    language: str = "R"
    endpoint: str = DEFAULT_ENDPOINT
    registration_state: str = "registered"
    execution_state: str = "active"
    execution_owner: str = "runtime-provider"
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_identity(self):
        if self.runtime_id != RUNTIME_ID:
            raise ValueError("runtime_id must use canonical sc-runtime-r identity")
        if self.adapter_id != ADAPTER_ID:
            raise ValueError("adapter_id must use canonical R adapter identity")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class RCapabilityMapping(BaseModel):
    mapping_id: str = Field(min_length=2, max_length=300)
    legacy_capability: str = Field(min_length=1, max_length=300)
    runtime_operation: str = Field(min_length=1, max_length=300)
    category: RCapabilityCategory
    base_r_only: bool = True
    legacy_aliases: list[str] = Field(default_factory=list)
    input_contract: str = Field(min_length=2, max_length=300)
    output_contract: str = Field(min_length=2, max_length=300)
    metadata: dict[str, Any] = Field(default_factory=dict)

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class RLegacyAlias(BaseModel):
    alias_id: str = Field(min_length=2, max_length=300)
    legacy_identifier: str = Field(min_length=2, max_length=300)
    canonical_identifier: str = Field(min_length=2, max_length=300)
    alias_kind: str = Field(min_length=2, max_length=100)
    reversible: bool = True
    metadata: dict[str, Any] = Field(default_factory=dict)


class AnalyticsRMigrationPlan(BaseModel):
    migration_plan_id: str = Field(min_length=2, max_length=300)
    state: RRuntimeMigrationState = RRuntimeMigrationState.active
    legacy_identity: LegacyAnalyticsRIdentity
    runtime_identity: RRuntimeIdentity
    capability_mappings: list[RCapabilityMapping] = Field(default_factory=list)
    aliases: list[RLegacyAlias] = Field(default_factory=list)
    preserve_legacy_resolution: bool = True
    destructive_migration: bool = False
    duplicate_runtime_execution: bool = False
    notes: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_plan(self):
        mapping_ids = [item.mapping_id for item in self.capability_mappings]
        if len(mapping_ids) != len(set(mapping_ids)):
            raise ValueError("capability mapping ids must be unique")

        operations = [item.runtime_operation for item in self.capability_mappings]
        if len(operations) != len(set(operations)):
            raise ValueError("runtime operations must be unique")

        alias_ids = [item.alias_id for item in self.aliases]
        if len(alias_ids) != len(set(alias_ids)):
            raise ValueError("legacy alias ids must be unique")

        if self.destructive_migration:
            raise ValueError("v3.36 migration must be non-destructive")
        if self.duplicate_runtime_execution:
            raise ValueError("legacy and canonical R execution must not run in parallel")
        return self

    def fingerprint(self) -> str:
        payload = self.model_dump(mode="json", exclude_none=True)
        payload.pop("state", None)
        return canonical_sha256(payload)


class RRuntimeRegistration(BaseModel):
    registration_id: str = Field(min_length=2, max_length=300)
    runtime_identity: RRuntimeIdentity
    capabilities: list[str] = Field(default_factory=list)
    adapter_methods: list[str] = Field(default_factory=list)
    environment_contract: str = ENVIRONMENT_PROVENANCE_CONTRACT
    job_contract: str = COMPUTATIONAL_JOB_CONTRACT
    migration_contract: str = CONTRACT_VERSION
    legacy_provider_ref: str = LEGACY_PROVIDER_ID
    product_surfaces: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_registration(self):
        if not self.capabilities:
            raise ValueError("R runtime registration requires capabilities")
        required_methods = {
            "health",
            "version",
            "capabilities",
            "prepare",
            "execute",
            "cancel",
            "inspect",
            "collect_results",
            "collect_artifacts",
            "diagnose",
        }
        if not required_methods.issubset(set(self.adapter_methods)):
            raise ValueError("R runtime registration is missing adapter lifecycle methods")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class RRuntimeMigrationBundle(BaseModel):
    migration_plan: AnalyticsRMigrationPlan
    runtime_registration: RRuntimeRegistration
    source_ai_research_contract: str = AI_RESEARCH_OBJECT_CONTRACT
    core_release: str = CORE_RELEASE

    @model_validator(mode="after")
    def validate_bundle(self):
        if (
            self.runtime_registration.runtime_identity.runtime_id
            != self.migration_plan.runtime_identity.runtime_id
        ):
            raise ValueError("runtime registration must match migration runtime")
        mapped = {item.runtime_operation for item in self.migration_plan.capability_mappings}
        registered = set(self.runtime_registration.capabilities)
        if mapped != registered:
            raise ValueError("registered R capabilities must exactly match migration mapping")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256({
            "migration_plan_fingerprint_sha256": self.migration_plan.fingerprint(),
            "runtime_registration_fingerprint_sha256": (
                self.runtime_registration.fingerprint()
            ),
            "source_ai_research_contract": self.source_ai_research_contract,
            "core_release": self.core_release,
        })


def capability_mappings() -> list[RCapabilityMapping]:
    in_contract = "sc.runtime.r.operation-input.v1"
    out_contract = "sc.runtime.r.operation-result.v1"
    return [
        RCapabilityMapping(
            mapping_id="r-capability:descriptive-summary",
            legacy_capability="descriptive_statistics",
            runtime_operation="descriptive_summary",
            category=RCapabilityCategory.descriptive_statistics,
            legacy_aliases=["summary", "describe"],
            input_contract=in_contract,
            output_contract=out_contract,
        ),
        RCapabilityMapping(
            mapping_id="r-capability:quantile-summary",
            legacy_capability="quantiles",
            runtime_operation="quantile_summary",
            category=RCapabilityCategory.distribution_summary,
            legacy_aliases=["quantile", "five_number_summary"],
            input_contract=in_contract,
            output_contract=out_contract,
        ),
        RCapabilityMapping(
            mapping_id="r-capability:correlation-matrix",
            legacy_capability="correlation",
            runtime_operation="correlation_matrix",
            category=RCapabilityCategory.correlation,
            legacy_aliases=["cor", "pearson_correlation"],
            input_contract=in_contract,
            output_contract=out_contract,
        ),
        RCapabilityMapping(
            mapping_id="r-capability:linear-regression",
            legacy_capability="linear_model",
            runtime_operation="linear_regression",
            category=RCapabilityCategory.regression,
            legacy_aliases=["lm", "ols"],
            input_contract=in_contract,
            output_contract=out_contract,
        ),
        RCapabilityMapping(
            mapping_id="r-capability:t-test",
            legacy_capability="t_test",
            runtime_operation="t_test",
            category=RCapabilityCategory.hypothesis_testing,
            legacy_aliases=["ttest"],
            input_contract=in_contract,
            output_contract=out_contract,
        ),
        RCapabilityMapping(
            mapping_id="r-capability:one-way-anova",
            legacy_capability="anova",
            runtime_operation="one_way_anova",
            category=RCapabilityCategory.analysis_of_variance,
            legacy_aliases=["aov", "oneway"],
            input_contract=in_contract,
            output_contract=out_contract,
        ),
    ]


def reference_r_runtime_migration() -> RRuntimeMigrationBundle:
    runtime = RRuntimeIdentity(
        metadata={
            "provider": "Sustainable Catalyst R Runtime",
            "provider_version": RUNTIME_VERSION,
            "transport": "HTTP",
            "loopback_only": True,
            "default_port": 18094,
            "arbitrary_r_source": False,
            "package_installation": False,
        }
    )

    plan = AnalyticsRMigrationPlan(
        migration_plan_id="r-migration:catalyst-analytics-r-to-sc-runtime-r:v1",
        legacy_identity=LegacyAnalyticsRIdentity(),
        runtime_identity=runtime,
        capability_mappings=capability_mappings(),
        aliases=[
            RLegacyAlias(
                alias_id="alias:legacy-provider-id",
                legacy_identifier=LEGACY_PROVIDER_ID,
                canonical_identifier=RUNTIME_ID,
                alias_kind="runtime-provider",
            ),
            RLegacyAlias(
                alias_id="alias:legacy-provider-contract",
                legacy_identifier=LEGACY_ANALYTICAL_PROVIDER_CONTRACT,
                canonical_identifier=RUNTIME_ADAPTER_CONTRACT,
                alias_kind="provider-contract",
            ),
        ],
        notes=[
            "Analytics R execution migrates into the Platform Core runtime fabric.",
            "Legacy identifiers remain resolvable during the compatibility window.",
            "Core stores contracts, registration and provenance; the provider executes R.",
        ],
        metadata={
            "legacy_provider_retained_as_alias": True,
            "analytics_r_standalone_runtime_deprecated": True,
        },
    )

    registration = RRuntimeRegistration(
        registration_id="runtime-registration:sc-runtime-r:1.0.0",
        runtime_identity=runtime,
        capabilities=[item.runtime_operation for item in plan.capability_mappings],
        adapter_methods=[
            "health",
            "version",
            "capabilities",
            "prepare",
            "execute",
            "cancel",
            "inspect",
            "collect_results",
            "collect_artifacts",
            "diagnose",
        ],
        product_surfaces=["research-lab", "workbench", "workspace"],
        metadata={
            "candidate_discovery_only": True,
            "core_selects_statistical_method": False,
            "core_certifies_statistical_validity": False,
        },
    )

    return RRuntimeMigrationBundle(
        migration_plan=plan,
        runtime_registration=registration,
    )


def contract_document() -> dict[str, Any]:
    reference = reference_r_runtime_migration()
    return {
        "ok": True,
        "release": CORE_RELEASE,
        "contract": CONTRACT_VERSION,
        "depends_on": [
            LEGACY_ANALYTICAL_PROVIDER_CONTRACT,
            COMPUTATIONAL_RUNTIME_CONTRACT,
            RUNTIME_ADAPTER_CONTRACT,
            COMPUTATIONAL_JOB_CONTRACT,
            ENVIRONMENT_PROVENANCE_CONTRACT,
            AI_RESEARCH_OBJECT_CONTRACT,
        ],
        "runtime": {
            "runtime_id": RUNTIME_ID,
            "runtime_version": RUNTIME_VERSION,
            "adapter_id": ADAPTER_ID,
            "endpoint": DEFAULT_ENDPOINT,
            "language": "R",
            "runtime_kind": "language",
        },
        "migration": {
            "legacy_provider_id": LEGACY_PROVIDER_ID,
            "legacy_provider_version": LEGACY_PROVIDER_VERSION,
            "canonical_runtime_id": RUNTIME_ID,
            "non_destructive": True,
            "legacy_alias_resolution": True,
            "duplicate_execution": False,
        },
        "capabilities": [
            item.model_dump(mode="json", exclude_none=True)
            for item in capability_mappings()
        ],
        "adapter_methods": reference.runtime_registration.adapter_methods,
        "integration": {
            "research_lab_primary_analysis_surface": True,
            "workbench_interactive_analysis_surface": True,
            "workspace_orchestrates_jobs": True,
            "core_owns_runtime_contracts_provenance_and_registration": True,
            "provider_executes_r": True,
        },
        "boundaries": {
            "core_executes_r_directly": False,
            "core_installs_r_packages_during_jobs": False,
            "arbitrary_r_source_execution": False,
            "core_selects_statistical_method": False,
            "core_certifies_statistical_validity": False,
        },
        "reference": {
            "migration_plan_id": reference.migration_plan.migration_plan_id,
            "registration_id": reference.runtime_registration.registration_id,
            "bundle_fingerprint_sha256": reference.fingerprint(),
        },
    }
