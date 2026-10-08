from __future__ import annotations

from enum import Enum
from functools import lru_cache
from typing import Literal

from pydantic import BaseModel, Field, model_validator

from .computational_runtime_objects import canonical_sha256

CORE_RELEASE = "4.20.1"
CONTRACT_VERSION = "sc.core.external-provider-registry.v1"
PREDECESSOR_CONTRACT = "sc.core.unified-contextual-reasoning-runtime.v1"


class ProviderKind(str, Enum):
    knowledge = "knowledge"
    data = "data"
    computational = "computational"
    geospatial = "geospatial"
    event = "event"
    intelligence = "intelligence"


class ProviderLifecycleState(str, Enum):
    reference_only = "reference-only"
    configured = "configured"
    active = "active"
    disabled = "disabled"


class AuthenticationMode(str, Enum):
    none = "none"
    api_key = "api-key"
    bearer_token = "bearer-token"
    oauth2 = "oauth2"
    account = "account"
    provider_specific = "provider-specific"


class EndpointProtocol(str, Enum):
    rest = "rest"
    graphql = "graphql"
    sparql = "sparql"
    sdmx = "sdmx"
    stac = "stac"
    rpc = "rpc"
    other = "other"


class ProviderAuthorityScope(BaseModel):
    authority_id: str = Field(min_length=3)
    scope: str = Field(min_length=3, max_length=1000)
    authority_class: str = Field(min_length=3, max_length=100)
    source_is_authoritative_within_scope_only: Literal[True] = True
    authority_establishes_truth: Literal[False] = False
    authority_overrides_conflicting_evidence: Literal[False] = False

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class ProviderCapability(BaseModel):
    capability_id: str = Field(min_length=3)
    provider_kind: ProviderKind
    operation: str = Field(min_length=3, max_length=160)
    object_types: list[str] = Field(min_length=1)
    supports_historical_versions: bool = False
    supports_structured_query: bool = True
    supports_reproducible_retrieval: bool = True
    output_requires_provenance: Literal[True] = True
    output_is_not_automatically_evidence: Literal[True] = True

    @model_validator(mode="after")
    def validate_unique_object_types(self):
        if len(self.object_types) != len(set(self.object_types)):
            raise ValueError("object_types must be unique")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class ProviderEndpoint(BaseModel):
    endpoint_id: str = Field(min_length=3)
    protocol: EndpointProtocol
    endpoint_label: str = Field(min_length=3, max_length=300)
    authentication_mode: AuthenticationMode = AuthenticationMode.none
    credential_reference: str | None = None
    endpoint_uri: str | None = None
    secret_material_embedded: Literal[False] = False
    endpoint_registration_establishes_connectivity: Literal[False] = False

    @model_validator(mode="after")
    def validate_credentials(self):
        if self.authentication_mode == AuthenticationMode.none and self.credential_reference is not None:
            raise ValueError("unauthenticated endpoint may not declare credential reference")
        if self.credential_reference and any(x in self.credential_reference.lower() for x in ("secret=", "token=", "key=")):
            raise ValueError("credential_reference must name a secret reference, not embed secret material")
        return self


class ProviderUsagePolicy(BaseModel):
    policy_id: str = Field(min_length=3)
    license_label: str = Field(min_length=1, max_length=300)
    commercial_use_status: Literal["allowed", "restricted", "unknown", "provider-specific"]
    redistribution_status: Literal["allowed", "restricted", "unknown", "provider-specific"]
    attribution_required: bool
    caching_status: Literal["allowed", "restricted", "unknown", "provider-specific"]
    quota_model: Literal["none", "request-limit", "volume-limit", "paid-tier", "unknown", "provider-specific"]
    terms_reference: str = Field(min_length=3, max_length=1000)
    provider_terms_remain_authoritative: Literal[True] = True
    registry_may_override_provider_terms: Literal[False] = False


class ExternalProviderRecord(BaseModel):
    provider_id: str = Field(min_length=3)
    display_name: str = Field(min_length=2, max_length=300)
    kinds: list[ProviderKind] = Field(min_length=1)
    lifecycle_state: ProviderLifecycleState
    description: str = Field(min_length=3, max_length=2000)
    authority_scopes: list[ProviderAuthorityScope] = Field(min_length=1)
    capabilities: list[ProviderCapability] = Field(min_length=1)
    endpoints: list[ProviderEndpoint] = Field(default_factory=list)
    usage_policy: ProviderUsagePolicy
    provider_metadata_version: str = Field(min_length=1, max_length=100)
    adapter_implementation_ref: str | None = None
    source_identity_must_be_preserved: Literal[True] = True
    retrieval_provenance_required: Literal[True] = True
    registration_is_not_adapter_implementation: Literal[True] = True
    registration_is_not_connectivity_verification: Literal[True] = True
    registration_establishes_evidence_truth: Literal[False] = False
    registration_authorizes_graph_mutation: Literal[False] = False

    @model_validator(mode="after")
    def validate_provider(self):
        if len(self.kinds) != len(set(self.kinds)):
            raise ValueError("provider kinds must be unique")
        cap_ids = [x.capability_id for x in self.capabilities]
        if len(cap_ids) != len(set(cap_ids)):
            raise ValueError("capability ids must be unique per provider")
        endpoint_ids = [x.endpoint_id for x in self.endpoints]
        if len(endpoint_ids) != len(set(endpoint_ids)):
            raise ValueError("endpoint ids must be unique per provider")
        authority_ids = [x.authority_id for x in self.authority_scopes]
        if len(authority_ids) != len(set(authority_ids)):
            raise ValueError("authority ids must be unique per provider")
        if any(cap.provider_kind not in self.kinds for cap in self.capabilities):
            raise ValueError("capability provider_kind must be declared by provider")
        if self.lifecycle_state == ProviderLifecycleState.reference_only and self.adapter_implementation_ref is not None:
            raise ValueError("reference-only provider may not claim implemented adapter")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class ExternalProviderRegistryPolicy(BaseModel):
    policy_id: str = Field(min_length=3)
    provider_identity_is_governed: Literal[True] = True
    capability_identity_is_governed: Literal[True] = True
    endpoint_identity_is_governed: Literal[True] = True
    authority_scope_must_be_explicit: Literal[True] = True
    provider_terms_must_be_preserved: Literal[True] = True
    credentials_must_be_reference_only: Literal[True] = True
    retrieval_provenance_required: Literal[True] = True
    provider_registration_establishes_connectivity: Literal[False] = False
    provider_authority_establishes_truth: Literal[False] = False
    provider_output_auto_promotes_evidence: Literal[False] = False
    computational_output_auto_promotes_evidence: Literal[False] = False
    event_signal_establishes_ground_truth: Literal[False] = False
    provider_agreement_establishes_truth: Literal[False] = False
    registry_authorizes_automatic_graph_mutation: Literal[False] = False


class ProviderRegistrySnapshot(BaseModel):
    snapshot_id: str = Field(min_length=3)
    provider_fingerprints: dict[str, str]
    deterministic_registry_fingerprint_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    supersedable: Literal[True] = True
    snapshot_is_not_connectivity_or_truth_certification: Literal[True] = True


class ExternalProviderRegistryBundle(BaseModel):
    release: Literal["4.20.1"] = "4.20.1"
    contract: Literal[CONTRACT_VERSION] = CONTRACT_VERSION
    predecessor_contract: Literal[PREDECESSOR_CONTRACT] = PREDECESSOR_CONTRACT
    policy: ExternalProviderRegistryPolicy
    providers: list[ExternalProviderRecord] = Field(min_length=1)
    snapshots: list[ProviderRegistrySnapshot] = Field(min_length=1, max_length=1)
    database_migration: Literal["none"] = "none"

    @model_validator(mode="after")
    def validate_registry(self):
        provider_ids = [x.provider_id for x in self.providers]
        if len(provider_ids) != len(set(provider_ids)):
            raise ValueError("provider ids must be unique")
        expected = {x.provider_id: x.fingerprint() for x in self.providers}
        deterministic = canonical_sha256({"contract": self.contract, "providers": expected})
        snap = self.snapshots[0]
        if snap.provider_fingerprints != expected:
            raise ValueError("provider registry snapshot fingerprint map mismatch")
        if snap.deterministic_registry_fingerprint_sha256 != deterministic:
            raise ValueError("provider registry deterministic fingerprint mismatch")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


def _usage(provider_id: str, *, license_label: str = "provider-governed") -> ProviderUsagePolicy:
    return ProviderUsagePolicy(
        policy_id=f"usage:{provider_id}", license_label=license_label,
        commercial_use_status="provider-specific", redistribution_status="provider-specific",
        attribution_required=True, caching_status="provider-specific", quota_model="provider-specific",
        terms_reference=f"terms-reference:{provider_id}",
    )


def _provider(
    provider_id: str,
    display_name: str,
    kinds: list[ProviderKind],
    authority_class: str,
    authority_scope: str,
    operation: str,
    object_types: list[str],
    protocol: EndpointProtocol,
    auth: AuthenticationMode,
    *,
    historical: bool = False,
) -> ExternalProviderRecord:
    primary_kind = kinds[0]
    return ExternalProviderRecord(
        provider_id=provider_id,
        display_name=display_name,
        kinds=kinds,
        lifecycle_state=ProviderLifecycleState.reference_only,
        description="Reference registration used to validate the generic provider contract; adapter implementation and live connectivity are intentionally outside this registry record.",
        authority_scopes=[ProviderAuthorityScope(
            authority_id=f"authority:{provider_id}", scope=authority_scope, authority_class=authority_class,
        )],
        capabilities=[ProviderCapability(
            capability_id=f"capability:{provider_id}:{operation}", provider_kind=primary_kind,
            operation=operation, object_types=object_types, supports_historical_versions=historical,
        )],
        endpoints=[ProviderEndpoint(
            endpoint_id=f"endpoint:{provider_id}:reference", protocol=protocol,
            endpoint_label=f"Reference endpoint descriptor for {display_name}", authentication_mode=auth,
            credential_reference=None if auth == AuthenticationMode.none else f"credential-ref:{provider_id}",
        )],
        usage_policy=_usage(provider_id), provider_metadata_version="reference-v1",
    )


@lru_cache(maxsize=1)
def reference_external_provider_registry_bundle() -> ExternalProviderRegistryBundle:
    providers = [
        _provider("provider:pubmed", "PubMed / NCBI", [ProviderKind.knowledge], "domain-index", "Biomedical literature indexing and source metadata within provider-declared scope.", "literature-discovery", ["publication", "citation", "biomedical-metadata"], EndpointProtocol.rest, AuthenticationMode.none),
        _provider("provider:fred-alfred", "FRED / ALFRED", [ProviderKind.data], "official-statistics", "Economic time-series and historical-vintage observations within provider-declared scope.", "economic-time-series-retrieval", ["dataset", "observation", "vintage"], EndpointProtocol.rest, AuthenticationMode.api_key, historical=True),
        _provider("provider:wolfram", "Wolfram Computational Provider", [ProviderKind.computational], "computational-service", "External computational interpretation and result generation within declared engine capabilities.", "computational-evaluation", ["calculation-request", "calculation-result", "assumption-set"], EndpointProtocol.rest, AuthenticationMode.api_key),
        _provider("provider:nasa-earthdata", "NASA Earthdata", [ProviderKind.geospatial, ProviderKind.data], "official-geospatial", "Earth-observation discovery and geospatial asset metadata within provider-declared scope.", "geospatial-asset-discovery", ["catalog-item", "spatiotemporal-asset", "dataset"], EndpointProtocol.stac, AuthenticationMode.none),
        _provider("provider:gdelt", "GDELT", [ProviderKind.event, ProviderKind.data], "observational-signal", "Machine-readable event/media observations treated as signals rather than ground truth.", "event-signal-retrieval", ["event-signal", "media-observation", "location-reference"], EndpointProtocol.rest, AuthenticationMode.none, historical=True),
        _provider("provider:data-commons", "Data Commons", [ProviderKind.intelligence, ProviderKind.data], "cross-domain-normalization", "Cross-domain statistical entity/variable discovery and normalization within provider-declared scope.", "cross-domain-statistical-discovery", ["entity", "statistical-variable", "observation"], EndpointProtocol.rest, AuthenticationMode.api_key, historical=True),
    ]
    fps = {x.provider_id: x.fingerprint() for x in providers}
    deterministic = canonical_sha256({"contract": CONTRACT_VERSION, "providers": fps})
    return ExternalProviderRegistryBundle(
        policy=ExternalProviderRegistryPolicy(policy_id="external-provider-registry-policy:v1"),
        providers=providers,
        snapshots=[ProviderRegistrySnapshot(
            snapshot_id="provider-registry-snapshot:reference-v1",
            provider_fingerprints=fps,
            deterministic_registry_fingerprint_sha256=deterministic,
        )],
    )


def contract_document() -> dict:
    b = reference_external_provider_registry_bundle()
    kind_counts = {k.value: sum(k in p.kinds for p in b.providers) for k in ProviderKind}
    return {
        "ok": True,
        "release": CORE_RELEASE,
        "contract": CONTRACT_VERSION,
        "predecessor_contract": PREDECESSOR_CONTRACT,
        "identity": {
            "product": "Sustainable Catalyst Platform Core",
            "build": "External Provider Registry Contract",
            "major_api": "v4",
        },
        "principles": {
            "provider_identity_is_governed": True,
            "provider_classes_are_explicit": True,
            "capabilities_and_authority_scope_are_explicit": True,
            "usage_and_license_policy_are_preserved": True,
            "credentials_are_references_not_embedded_secrets": True,
            "retrieval_provenance_is_required": True,
            "adapter_implementation_is_separate_from_registration": True,
        },
        "boundaries": {
            "provider_registration_establishes_connectivity": False,
            "provider_authority_establishes_truth": False,
            "provider_output_auto_promotes_evidence": False,
            "computational_output_auto_promotes_evidence": False,
            "event_signal_establishes_ground_truth": False,
            "provider_agreement_establishes_truth": False,
            "registry_authorizes_automatic_graph_mutation": False,
        },
        "reference": {
            "providers": len(b.providers),
            "provider_kinds": len(ProviderKind),
            "kind_counts": kind_counts,
            "capabilities": sum(len(x.capabilities) for x in b.providers),
            "authority_scopes": sum(len(x.authority_scopes) for x in b.providers),
            "endpoints": sum(len(x.endpoints) for x in b.providers),
            "reference_only_providers": sum(x.lifecycle_state == ProviderLifecycleState.reference_only for x in b.providers),
            "bundle_fingerprint_sha256": b.fingerprint(),
            "registry_snapshot_fingerprint_sha256": b.snapshots[0].deterministic_registry_fingerprint_sha256,
        },
        "roadmap_integration": {
            "extends_v4200_without_reopening_reasoning_arc": True,
            "prepares_computational_provider_contract": True,
            "prepares_dataset_observation_vintage_contract": True,
            "prepares_external_retrieval_provenance_usage_policy": True,
            "prepares_library_provider_runtime": True,
            "prepares_workbench_wolfram_provider": True,
        },
        "database_migration": "none",
    }
