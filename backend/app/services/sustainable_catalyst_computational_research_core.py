from __future__ import annotations

from enum import Enum
from functools import lru_cache
from typing import Literal
from pydantic import BaseModel, Field, model_validator

from .computational_runtime_objects import canonical_sha256

CORE_RELEASE = "4.0.0"
CONTRACT_VERSION = "sc.core.sustainable-catalyst-computational-research-core.v1"


def _unique(values: list[str], label: str) -> None:
    if len(values) != len(set(values)):
        raise ValueError(f"{label} must be unique")


class MajorReleaseDisposition(str, Enum):
    approved_for_controlled_soak = "approved-for-controlled-soak"
    production_certified = "production-certified"
    blocked = "blocked"


class ComputationalResearchCorePolicy(BaseModel):
    policy_id: str = Field(min_length=3, max_length=500)
    stable_major_api: Literal[True] = True
    preserve_upstream_contract_identity: Literal[True] = True
    preserve_epistemic_state: Literal[True] = True
    preserve_provenance: Literal[True] = True
    preserve_validation_requirements: Literal[True] = True
    preserve_human_review_gates: Literal[True] = True
    preserve_remote_reference_boundary: Literal[True] = True
    original_language_is_primary_representation: Literal[True] = True
    translation_is_derived_representation: Literal[True] = True
    runtime_output_is_not_evidence_fact: Literal[True] = True
    performance_optimization_is_semantic_preserving: Literal[True] = True
    v399_soak_requirement_carried_forward: Literal[True] = True
    no_graph_mutation_authorized_by_major_release: Literal[True] = True
    def fingerprint(self) -> str: return canonical_sha256(self)


class UpstreamContractBinding(BaseModel):
    release: str = Field(pattern=r"^3\.(?:[5-9][0-9])\.0$")
    contract: str = Field(min_length=10, max_length=500)
    domain_id: str = Field(min_length=3, max_length=120)
    stable_in_v4: Literal[True] = True
    semantic_identity_preserved: Literal[True] = True
    provenance_boundary_preserved: Literal[True] = True
    compatibility_state: Literal["retained"] = "retained"
    def fingerprint(self) -> str: return canonical_sha256(self)


class CoreDomainProfile(BaseModel):
    domain_id: str = Field(min_length=3, max_length=120)
    title: str = Field(min_length=3, max_length=300)
    contract_refs: list[str] = Field(min_length=1)
    public_surface: str = Field(min_length=3, max_length=300)
    computational_authority: Literal["governed-contracts-and-orchestration"] = "governed-contracts-and-orchestration"
    domain_does_not_create_truth_authority: Literal[True] = True
    @model_validator(mode="after")
    def validate_refs(self): _unique(self.contract_refs, "contract_refs"); return self
    def fingerprint(self) -> str: return canonical_sha256(self)


class StableApiSurface(BaseModel):
    surface_id: str = Field(min_length=3, max_length=150)
    title: str = Field(min_length=3, max_length=300)
    route_prefix: str = Field(min_length=2, max_length=300)
    domain_refs: list[str] = Field(min_length=1)
    compatibility_policy: Literal["backward-compatible-within-v4"] = "backward-compatible-within-v4"
    explicit_versioned_contracts_required: Literal[True] = True
    def fingerprint(self) -> str: return canonical_sha256(self)


class ProductConsumerBinding(BaseModel):
    consumer_id: str = Field(min_length=3, max_length=120)
    display_name: str = Field(min_length=3, max_length=200)
    handoff_contract: Literal["sc.core.cross-product-intelligence-handoff.v1"] = "sc.core.cross-product-intelligence-handoff.v1"
    must_preserve_epistemic_state: Literal[True] = True
    must_preserve_provenance: Literal[True] = True
    returned_derived_output_requires_validation: Literal[True] = True
    def fingerprint(self) -> str: return canonical_sha256(self)


class MajorCompatibilityRule(BaseModel):
    rule_id: str = Field(min_length=3, max_length=150)
    subject: str = Field(min_length=3, max_length=500)
    requirement: str = Field(min_length=10, max_length=2000)
    authority_may_increase: Literal[False] = False
    semantics_may_silently_change: Literal[False] = False
    def fingerprint(self) -> str: return canonical_sha256(self)


class MajorReleaseReadiness(BaseModel):
    readiness_id: str = Field(min_length=3, max_length=150)
    disposition: MajorReleaseDisposition
    predecessor_release: Literal["3.99.0"] = "3.99.0"
    predecessor_certification_contract: Literal["sc.core.unified-core-production-certification-soak.v1"] = "sc.core.unified-core-production-certification-soak.v1"
    minimum_elapsed_soak_hours: Literal[24] = 24
    predecessor_elapsed_soak_required_for_production_certification: Literal[True] = True
    full_production_certification_claimed: Literal[False] = False
    major_version_transition_is_operational_not_epistemic: Literal[True] = True
    @model_validator(mode="after")
    def validate_disposition(self):
        if self.disposition == MajorReleaseDisposition.production_certified:
            raise ValueError("v4.0 reference package cannot fabricate elapsed v3.99 soak evidence")
        return self
    def fingerprint(self) -> str: return canonical_sha256(self)


class ComputationalResearchCoreSnapshot(BaseModel):
    snapshot_id: str = Field(min_length=3, max_length=150)
    policy_ref: str = Field(min_length=3, max_length=150)
    upstream_contract_refs: list[str] = Field(min_length=1)
    domain_refs: list[str] = Field(min_length=1)
    api_surface_refs: list[str] = Field(min_length=1)
    consumer_refs: list[str] = Field(min_length=1)
    compatibility_rule_refs: list[str] = Field(min_length=1)
    readiness_ref: str = Field(min_length=3, max_length=150)
    immutable: Literal[True] = True
    supersedable: Literal[True] = True
    snapshot_is_not_truth_certification: Literal[True] = True
    def fingerprint(self) -> str: return canonical_sha256(self)


class SustainableCatalystComputationalResearchCoreBundle(BaseModel):
    release: Literal["4.0.0"] = "4.0.0"
    contract: Literal[CONTRACT_VERSION] = CONTRACT_VERSION
    policy: ComputationalResearchCorePolicy
    upstream_contracts: list[UpstreamContractBinding] = Field(min_length=1)
    domains: list[CoreDomainProfile] = Field(min_length=1)
    api_surfaces: list[StableApiSurface] = Field(min_length=1)
    consumers: list[ProductConsumerBinding] = Field(min_length=1)
    compatibility_rules: list[MajorCompatibilityRule] = Field(min_length=1)
    readiness: MajorReleaseReadiness
    snapshots: list[ComputationalResearchCoreSnapshot] = Field(min_length=1)
    database_migration: Literal["none"] = "none"

    @model_validator(mode="after")
    def validate_bundle(self):
        _unique([x.contract for x in self.upstream_contracts], "upstream contracts")
        _unique([x.domain_id for x in self.domains], "domain ids")
        _unique([x.surface_id for x in self.api_surfaces], "surface ids")
        _unique([x.consumer_id for x in self.consumers], "consumer ids")
        _unique([x.rule_id for x in self.compatibility_rules], "rule ids")
        _unique([x.snapshot_id for x in self.snapshots], "snapshot ids")
        if len(self.upstream_contracts) != 43:
            raise ValueError("v4.0 requires all 43 governed upstream contracts from v3.57-v3.99")
        domain_ids = {x.domain_id for x in self.domains}
        if {x.domain_id for x in self.upstream_contracts} != domain_ids:
            raise ValueError("every upstream contract must map to exactly one declared domain")
        return self

    def fingerprint(self) -> str: return canonical_sha256(self)


UPSTREAM = [('3.57.0', 'sc.core.machine-learning-neural-model-object.v1', 'neural-ml'), ('3.58.0', 'sc.core.training-run-checkpoint-experiment-lineage.v1', 'neural-ml'), ('3.59.0', 'sc.core.neural-dataset-feature-transformation-provenance.v1', 'neural-ml'), ('3.60.0', 'sc.core.neural-evaluation-calibration-uncertainty.v1', 'neural-ml'), ('3.61.0', 'sc.core.explainability-model-interpretation.v1', 'neural-ml'), ('3.62.0', 'sc.core.neural-embedding-representation-intelligence.v1', 'neural-ml'), ('3.63.0', 'sc.core.neural-inference-prediction-provenance.v1', 'neural-ml'), ('3.64.0', 'sc.core.neural-model-registry-reproducible-packages.v1', 'neural-ml'), ('3.65.0', 'sc.core.multilingual-text-language-object.v1', 'language-linguistics'), ('3.66.0', 'sc.core.linguistic-annotation-provenance.v1', 'language-linguistics'), ('3.67.0', 'sc.core.translation-transliteration-alignment.v1', 'language-linguistics'), ('3.68.0', 'sc.core.historical-language-script-orthography-variant.v1', 'language-linguistics'), ('3.69.0', 'sc.core.cross-lingual-semantic-linguistic-exchange.v1', 'language-linguistics'), ('3.70.0', 'sc.core.graph-machine-learning-foundation.v1', 'graph-ml'), ('3.71.0', 'sc.core.graph-embedding-runtime.v1', 'graph-ml'), ('3.72.0', 'sc.core.graph-node-edge-classification.v1', 'graph-ml'), ('3.73.0', 'sc.core.graph-link-prediction-candidate-relationship.v1', 'graph-ml'), ('3.74.0', 'sc.core.graph-anomaly-detection.v1', 'graph-ml'), ('3.75.0', 'sc.core.knowledge-graph-representation-learning.v1', 'graph-ml'), ('3.76.0', 'sc.core.evidence-graph-neural-analysis-validation.v1', 'graph-ml'), ('3.77.0', 'sc.core.entity-resolution-identity-graph-foundation.v1', 'entity-evidence'), ('3.78.0', 'sc.core.temporal-identity-alias-name-variant-intelligence.v1', 'entity-evidence'), ('3.79.0', 'sc.core.probabilistic-record-linkage-entity-matching.v1', 'entity-evidence'), ('3.80.0', 'sc.core.cross-source-entity-reconciliation-identity-provenance.v1', 'entity-evidence'), ('3.81.0', 'sc.core.public-record-documentary-source-object-model.v1', 'entity-evidence'), ('3.82.0', 'sc.core.relationship-discovery-connection-hypothesis.v1', 'entity-evidence'), ('3.83.0', 'sc.core.network-structure-community-motif-intelligence.v1', 'entity-evidence'), ('3.84.0', 'sc.core.explainable-connection-paths-evidence-chains.v1', 'entity-evidence'), ('3.85.0', 'sc.core.multi-hop-research-investigation-graph-reasoning.v1', 'entity-evidence'), ('3.86.0', 'sc.core.contradictory-identity-relationship-resolution.v1', 'entity-evidence'), ('3.87.0', 'sc.core.entity-centric-timeline-event-association.v1', 'entity-evidence'), ('3.88.0', 'sc.core.reproducible-graph-investigation-package.v1', 'entity-evidence'), ('3.89.0', 'sc.core.federated-evidence-graph-exchange.v1', 'entity-evidence'), ('3.90.0', 'sc.core.unified-entity-evidence-intelligence-runtime.v1', 'entity-evidence'), ('3.91.0', 'sc.core.unified-runtime-policy-capability-negotiation.v1', 'runtime-control'), ('3.92.0', 'sc.core.unified-entity-evidence-query-api.v1', 'runtime-control'), ('3.93.0', 'sc.core.investigation-session-research-context-runtime.v1', 'runtime-control'), ('3.94.0', 'sc.core.cross-product-intelligence-handoff.v1', 'runtime-control'), ('3.95.0', 'sc.core.signed-runtime-artifacts-execution-attestations.v1', 'integrity-federation'), ('3.96.0', 'sc.core.federation-governance-trust-policy-runtime.v1', 'integrity-federation'), ('3.97.0', 'sc.core.unified-runtime-observability-audit-drift-intelligence.v1', 'operations-scale-certification'), ('3.98.0', 'sc.core.entity-evidence-runtime-performance-scale.v1', 'operations-scale-certification'), ('3.99.0', 'sc.core.unified-core-production-certification-soak.v1', 'operations-scale-certification')]


@lru_cache(maxsize=1)
def reference_sustainable_catalyst_computational_research_core_bundle() -> SustainableCatalystComputationalResearchCoreBundle:
    bindings=[UpstreamContractBinding(release=r, contract=c, domain_id=d) for r,c,d in UPSTREAM]
    by_domain={}
    for b in bindings: by_domain.setdefault(b.domain_id,[]).append(b.contract)
    titles={
        "neural-ml":"Neural & Machine Learning Research Objects",
        "language-linguistics":"Multilingual & Linguistic Intelligence",
        "graph-ml":"Graph Machine Learning & Neural Graph Reasoning",
        "entity-evidence":"Entity, Evidence & Investigation Intelligence",
        "runtime-control":"Unified Runtime Control, Query, Session & Handoff",
        "integrity-federation":"Signed Artifacts, Federation Governance & Trust",
        "operations-scale-certification":"Observability, Scale & Production Certification",
    }
    domains=[CoreDomainProfile(domain_id=k,title=titles[k],contract_refs=by_domain[k],public_surface=f"/public/v1/core/domains/{k}") for k in titles]
    surfaces=[
        StableApiSurface(surface_id="research-objects",title="Governed Research Objects",route_prefix="/v1/research",domain_refs=["neural-ml","language-linguistics"]),
        StableApiSurface(surface_id="graph-intelligence",title="Graph Intelligence",route_prefix="/v1/graph",domain_refs=["graph-ml"]),
        StableApiSurface(surface_id="entity-evidence",title="Entity & Evidence Intelligence",route_prefix="/v1/entity-evidence",domain_refs=["entity-evidence"]),
        StableApiSurface(surface_id="runtime-control",title="Runtime Control & Research Context",route_prefix="/v1/runtime",domain_refs=["runtime-control"]),
        StableApiSurface(surface_id="cross-product",title="Cross-Product Exchange",route_prefix="/v1/handoff",domain_refs=["runtime-control"]),
        StableApiSurface(surface_id="federation-integrity",title="Integrity & Federation",route_prefix="/v1/federation",domain_refs=["integrity-federation"]),
        StableApiSurface(surface_id="operations",title="Operations, Scale & Certification",route_prefix="/v1/operations",domain_refs=["operations-scale-certification"]),
    ]
    consumers=[ProductConsumerBinding(consumer_id=i,display_name=n) for i,n in [
        ("workspace","Workspace"),("knowledge-library","Knowledge Library"),("research-librarian","Research Librarian"),
        ("research-lab","Research Lab"),("workbench","Workbench"),("decision-studio","Decision Studio"),("site-intelligence","Site Intelligence")]]
    rules=[
        MajorCompatibilityRule(rule_id="contract-identity",subject="Existing governed contracts",requirement="Existing v3 governed contract identifiers remain addressable and retain their semantic identity in v4."),
        MajorCompatibilityRule(rule_id="epistemic-boundary",subject="Epistemic state",requirement="Candidates, hypotheses, remote references, analytical results, contradictions, and validated evidence remain distinct states."),
        MajorCompatibilityRule(rule_id="provenance",subject="Provenance",requirement="Cross-runtime execution, caching, handoffs, federation, and derived outputs must retain source and transformation provenance."),
        MajorCompatibilityRule(rule_id="language",subject="Original-language sources",requirement="Original language remains primary; translation and transliteration remain derived representations with lineage."),
        MajorCompatibilityRule(rule_id="performance",subject="Performance and scaling",requirement="Caching, batching, parallelism, truncation, queues, and degradation may alter execution strategy but not authority or meaning."),
        MajorCompatibilityRule(rule_id="wordpress",subject="WordPress connector",requirement="WordPress remains an integration client and must not become the authoritative computational or evidence runtime."),
    ]
    readiness=MajorReleaseReadiness(readiness_id="v4-major-release-readiness",disposition=MajorReleaseDisposition.approved_for_controlled_soak)
    snap=ComputationalResearchCoreSnapshot(
        snapshot_id="v4-computational-research-core-snapshot-1",policy_ref="v4-computational-research-core-policy",
        upstream_contract_refs=[x.contract for x in bindings],domain_refs=[x.domain_id for x in domains],
        api_surface_refs=[x.surface_id for x in surfaces],consumer_refs=[x.consumer_id for x in consumers],
        compatibility_rule_refs=[x.rule_id for x in rules],readiness_ref=readiness.readiness_id)
    return SustainableCatalystComputationalResearchCoreBundle(
        policy=ComputationalResearchCorePolicy(policy_id="v4-computational-research-core-policy"),upstream_contracts=bindings,
        domains=domains,api_surfaces=surfaces,consumers=consumers,compatibility_rules=rules,readiness=readiness,snapshots=[snap])


def contract_document() -> dict:
    b=reference_sustainable_catalyst_computational_research_core_bundle()
    return {
        "ok": True,"release": CORE_RELEASE,"contract": CONTRACT_VERSION,
        "identity":{"product":"Sustainable Catalyst Computational Research Core","major_api":"v4","stable_major_api":True},
        "principles":{
            "upstream_contract_identity_preserved":True,"epistemic_state_preserved":True,"provenance_preserved":True,
            "original_language_primary":True,"translation_is_derived":True,"runtime_output_is_not_evidence_fact":True,
            "performance_optimization_is_semantic_preserving":True,"cross_product_returns_require_validation":True,
            "v399_soak_requirement_carried_forward":True},
        "boundaries":{
            "major_version_transition_establishes_truth":False,"stable_api_label_establishes_evidence_validity":False,
            "runtime_output_auto_promotes_evidence":False,"compatibility_alias_changes_semantics":False,
            "wordpress_connector_is_runtime_authority":False,"production_certification_claimed_without_elapsed_soak":False,
            "identity_graph_mutation_performed":False,"relationship_graph_mutation_performed":False,"evidence_graph_mutation_performed":False},
        "reference":{"upstream_contracts":len(b.upstream_contracts),"domains":len(b.domains),"api_surfaces":len(b.api_surfaces),
            "consumers":len(b.consumers),"compatibility_rules":len(b.compatibility_rules),"readiness":b.readiness.disposition.value,
            "minimum_elapsed_soak_hours":b.readiness.minimum_elapsed_soak_hours,"snapshots":len(b.snapshots),
            "bundle_fingerprint_sha256":b.fingerprint()},
        "database_migration":"none"}
