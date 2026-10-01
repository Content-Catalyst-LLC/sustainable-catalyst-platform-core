from __future__ import annotations

from enum import Enum
from functools import lru_cache
from typing import Any, Literal

from pydantic import BaseModel, Field, model_validator

from .computational_runtime_objects import canonical_sha256
from .unified_entity_evidence_intelligence_runtime import CONTRACT_VERSION as V390_CONTRACT
from .unified_runtime_policy_capability_negotiation import CONTRACT_VERSION as V391_CONTRACT
from .unified_entity_evidence_query_api import CONTRACT_VERSION as V392_CONTRACT
from .investigation_session_research_context_runtime import CONTRACT_VERSION as V393_CONTRACT
from .cross_product_intelligence_handoff import CONTRACT_VERSION as V394_CONTRACT
from .signed_runtime_artifacts_execution_attestations import CONTRACT_VERSION as V395_CONTRACT
from .federation_governance_trust_policy_runtime import CONTRACT_VERSION as V396_CONTRACT
from .unified_runtime_observability_audit_drift_intelligence import CONTRACT_VERSION as V397_CONTRACT

CORE_RELEASE = "3.98.0"
CONTRACT_VERSION = "sc.core.entity-evidence-runtime-performance-scale.v1"


def _unique(values: list[str], label: str) -> None:
    if len(values) != len(set(values)):
        raise ValueError(f"{label} must be unique")


class WorkloadClass(str, Enum):
    interactive_query = "interactive-query"
    graph_traversal = "graph-traversal"
    entity_resolution = "entity-resolution"
    evidence_package = "evidence-package"
    federation_exchange = "federation-exchange"
    background_analysis = "background-analysis"


class CacheMode(str, Enum):
    disabled = "disabled"
    read_through = "read-through"
    write_through = "write-through"
    immutable_object = "immutable-object"


class DegradationMode(str, Enum):
    none = "none"
    bounded_results = "bounded-results"
    reduced_parallelism = "reduced-parallelism"
    queue_only = "queue-only"
    reference_only = "reference-only"
    incomplete_qualified = "incomplete-qualified"


class BenchmarkStatus(str, Enum):
    pass_ = "pass"
    warn = "warn"
    fail = "fail"


class PerformanceScalePolicy(BaseModel):
    policy_id: str = Field(min_length=3, max_length=500)
    preserve_epistemic_state: Literal[True] = True
    preserve_validation_state: Literal[True] = True
    preserve_provenance: Literal[True] = True
    require_explicit_execution_budgets: Literal[True] = True
    require_explicit_traversal_limits: Literal[True] = True
    require_explicit_cache_freshness: Literal[True] = True
    require_explicit_cardinality_controls: Literal[True] = True
    require_backpressure_under_saturation: Literal[True] = True
    require_reproducible_scale_benchmarks: Literal[True] = True
    silent_sampling_allowed: Literal[False] = False
    silent_truncation_allowed: Literal[False] = False
    performance_optimization_may_promote_epistemic_state: Literal[False] = False
    performance_optimization_may_drop_provenance: Literal[False] = False
    degraded_mode_may_increase_authority: Literal[False] = False
    runtime_scaling_mutates_governed_graphs: Literal[False] = False
    metadata: dict[str, Any] = Field(default_factory=dict)
    def fingerprint(self) -> str: return canonical_sha256(self)


class RuntimePerformanceProfile(BaseModel):
    profile_id: str = Field(min_length=3, max_length=500)
    workload_class: WorkloadClass
    target_capability: str = Field(min_length=3, max_length=500)
    contract: str = Field(min_length=3, max_length=500)
    target_p50_latency_ms: float = Field(gt=0)
    target_p95_latency_ms: float = Field(gt=0)
    target_throughput_per_second: float = Field(gt=0)
    maximum_concurrency: int = Field(ge=1)
    preserve_contract_semantics: Literal[True] = True
    faster_execution_does_not_increase_evidence_strength: Literal[True] = True
    metadata: dict[str, Any] = Field(default_factory=dict)
    @model_validator(mode="after")
    def validate_latency(self):
        if self.target_p95_latency_ms < self.target_p50_latency_ms:
            raise ValueError("p95 target must be >= p50 target")
        return self
    def fingerprint(self) -> str: return canonical_sha256(self)


class ExecutionBudget(BaseModel):
    budget_id: str = Field(min_length=3, max_length=500)
    workload_class: WorkloadClass
    wall_time_ms: int = Field(ge=1)
    cpu_time_ms: int = Field(ge=1)
    memory_mb: int = Field(ge=16)
    max_result_objects: int = Field(ge=1)
    max_intermediate_objects: int = Field(ge=1)
    max_external_calls: int = Field(ge=0)
    on_exhaustion: DegradationMode
    budget_exhaustion_must_be_explicit: Literal[True] = True
    budget_exhaustion_does_not_change_epistemic_state: Literal[True] = True
    metadata: dict[str, Any] = Field(default_factory=dict)
    def fingerprint(self) -> str: return canonical_sha256(self)


class CachePolicy(BaseModel):
    cache_policy_id: str = Field(min_length=3, max_length=500)
    target_kind: str = Field(min_length=2, max_length=500)
    mode: CacheMode
    ttl_seconds: int = Field(ge=0)
    content_addressed: bool
    require_source_fingerprint_match: Literal[True] = True
    require_policy_fingerprint_match: Literal[True] = True
    stale_entry_must_be_labeled: Literal[True] = True
    cache_hit_is_not_freshness_proof: Literal[True] = True
    cache_hit_is_not_content_truth: Literal[True] = True
    metadata: dict[str, Any] = Field(default_factory=dict)
    def fingerprint(self) -> str: return canonical_sha256(self)


class GraphTraversalLimit(BaseModel):
    traversal_limit_id: str = Field(min_length=3, max_length=500)
    target_graph: str = Field(min_length=2, max_length=500)
    max_hops: int = Field(ge=1, le=100)
    max_nodes_visited: int = Field(ge=1)
    max_edges_visited: int = Field(ge=1)
    max_paths_returned: int = Field(ge=1)
    timeout_ms: int = Field(ge=1)
    truncation_must_be_reported: Literal[True] = True
    missing_due_to_limit_is_not_nonexistence: Literal[True] = True
    shortest_or_fastest_path_is_not_strongest_evidence: Literal[True] = True
    metadata: dict[str, Any] = Field(default_factory=dict)
    def fingerprint(self) -> str: return canonical_sha256(self)


class BatchParallelismPolicy(BaseModel):
    batch_policy_id: str = Field(min_length=3, max_length=500)
    workload_class: WorkloadClass
    max_batch_size: int = Field(ge=1)
    max_parallel_workers: int = Field(ge=1)
    ordering_guarantee: Literal["preserve-input-order", "explicit-result-order"]
    deterministic_merge_required: Literal[True] = True
    provenance_per_item_required: Literal[True] = True
    parallel_results_are_not_independent_corroboration: Literal[True] = True
    metadata: dict[str, Any] = Field(default_factory=dict)
    def fingerprint(self) -> str: return canonical_sha256(self)


class HighCardinalityEntityPolicy(BaseModel):
    cardinality_policy_id: str = Field(min_length=3, max_length=500)
    entity_kind: str = Field(min_length=2, max_length=500)
    soft_limit: int = Field(ge=1)
    hard_limit: int = Field(ge=1)
    page_size: int = Field(ge=1)
    partition_strategy: Literal["stable-hash", "source-partition", "time-window", "none"]
    require_stable_pagination: Literal[True] = True
    require_explicit_partial_result_state: Literal[True] = True
    partial_result_is_not_complete_evidence_universe: Literal[True] = True
    @model_validator(mode="after")
    def validate_limits(self):
        if self.hard_limit < self.soft_limit:
            raise ValueError("hard_limit must be >= soft_limit")
        if self.page_size > self.hard_limit:
            raise ValueError("page_size must be <= hard_limit")
        return self
    def fingerprint(self) -> str: return canonical_sha256(self)


class FederationQueuePolicy(BaseModel):
    queue_policy_id: str = Field(min_length=3, max_length=500)
    queue_name: str = Field(min_length=2, max_length=500)
    max_depth: int = Field(ge=1)
    max_inflight: int = Field(ge=1)
    retry_limit: int = Field(ge=0)
    retry_backoff_seconds: int = Field(ge=0)
    priority_classes: list[str] = Field(min_length=1)
    preserve_remote_reference_state: Literal[True] = True
    queue_priority_is_not_evidence_priority: Literal[True] = True
    queue_acceptance_is_not_local_validation: Literal[True] = True
    @model_validator(mode="after")
    def validate_priority(self):
        _unique(self.priority_classes, "priority_classes")
        return self
    def fingerprint(self) -> str: return canonical_sha256(self)


class PackageSizeEnvelope(BaseModel):
    envelope_id: str = Field(min_length=3, max_length=500)
    package_kind: str = Field(min_length=2, max_length=500)
    soft_limit_mb: float = Field(gt=0)
    hard_limit_mb: float = Field(gt=0)
    max_object_count: int = Field(ge=1)
    max_single_artifact_mb: float = Field(gt=0)
    oversize_action: DegradationMode
    split_packages_preserve_manifest_lineage: Literal[True] = True
    package_size_does_not_measure_evidence_strength: Literal[True] = True
    @model_validator(mode="after")
    def validate_size(self):
        if self.hard_limit_mb < self.soft_limit_mb:
            raise ValueError("hard_limit_mb must be >= soft_limit_mb")
        if self.max_single_artifact_mb > self.hard_limit_mb:
            raise ValueError("max_single_artifact_mb must be <= hard_limit_mb")
        return self
    def fingerprint(self) -> str: return canonical_sha256(self)


class BackpressureRule(BaseModel):
    backpressure_rule_id: str = Field(min_length=3, max_length=500)
    signal: str = Field(min_length=2, max_length=500)
    threshold: float = Field(ge=0)
    comparison: Literal["gt", "gte", "lt", "lte"]
    action: DegradationMode
    retryable: bool
    must_emit_observability_signal: Literal[True] = True
    backpressure_may_not_drop_governance_constraints: Literal[True] = True
    backpressure_may_not_increase_authority: Literal[True] = True
    metadata: dict[str, Any] = Field(default_factory=dict)
    def fingerprint(self) -> str: return canonical_sha256(self)


class DegradationDecision(BaseModel):
    degradation_id: str = Field(min_length=3, max_length=500)
    trigger_ref: str = Field(min_length=3, max_length=500)
    workload_class: WorkloadClass
    mode: DegradationMode
    rationale: str = Field(min_length=10, max_length=2000)
    result_completeness: Literal["complete", "bounded", "partial", "queued", "reference-only"]
    observed_at: str = Field(min_length=10, max_length=80)
    explicit_to_consumer: Literal[True] = True
    preserves_epistemic_state: Literal[True] = True
    preserves_provenance: Literal[True] = True
    cannot_increase_authority: Literal[True] = True
    metadata: dict[str, Any] = Field(default_factory=dict)
    def fingerprint(self) -> str: return canonical_sha256(self)


class ScaleBenchmarkResult(BaseModel):
    benchmark_id: str = Field(min_length=3, max_length=500)
    profile_ref: str = Field(min_length=3, max_length=500)
    workload_class: WorkloadClass
    dataset_scale_label: str = Field(min_length=2, max_length=500)
    input_objects: int = Field(ge=1)
    concurrent_workers: int = Field(ge=1)
    p50_latency_ms: float = Field(ge=0)
    p95_latency_ms: float = Field(ge=0)
    throughput_per_second: float = Field(ge=0)
    peak_memory_mb: float = Field(ge=0)
    status: BenchmarkStatus
    measured_at: str = Field(min_length=10, max_length=80)
    environment_ref: str = Field(min_length=3, max_length=1000)
    reproducible: Literal[True] = True
    benchmark_is_performance_evidence_not_claim_truth: Literal[True] = True
    @model_validator(mode="after")
    def validate_latency(self):
        if self.p95_latency_ms < self.p50_latency_ms:
            raise ValueError("observed p95 must be >= p50")
        return self
    def fingerprint(self) -> str: return canonical_sha256(self)


class PerformanceScaleTrace(BaseModel):
    trace_id: str = Field(min_length=3, max_length=500)
    profile_refs: list[str] = Field(min_length=1)
    budget_refs: list[str] = Field(min_length=1)
    cache_policy_refs: list[str] = Field(default_factory=list)
    traversal_limit_refs: list[str] = Field(default_factory=list)
    batch_policy_refs: list[str] = Field(default_factory=list)
    cardinality_policy_refs: list[str] = Field(default_factory=list)
    queue_policy_refs: list[str] = Field(default_factory=list)
    envelope_refs: list[str] = Field(default_factory=list)
    degradation_refs: list[str] = Field(default_factory=list)
    benchmark_refs: list[str] = Field(min_length=1)
    started_at: str = Field(min_length=10, max_length=80)
    completed_at: str = Field(min_length=10, max_length=80)
    reproducible: Literal[True] = True
    trace_preserves_execution_qualifications: Literal[True] = True
    @model_validator(mode="after")
    def validate_refs(self):
        for vals,label in (
            (self.profile_refs,"profile_refs"),(self.budget_refs,"budget_refs"),(self.cache_policy_refs,"cache_policy_refs"),
            (self.traversal_limit_refs,"traversal_limit_refs"),(self.batch_policy_refs,"batch_policy_refs"),
            (self.cardinality_policy_refs,"cardinality_policy_refs"),(self.queue_policy_refs,"queue_policy_refs"),
            (self.envelope_refs,"envelope_refs"),(self.degradation_refs,"degradation_refs"),(self.benchmark_refs,"benchmark_refs")):
            _unique(vals,label)
        return self
    def fingerprint(self) -> str: return canonical_sha256(self)


class PerformanceScaleSnapshot(BaseModel):
    snapshot_id: str = Field(min_length=3, max_length=500)
    policy_refs: list[str] = Field(min_length=1)
    profile_refs: list[str] = Field(min_length=1)
    budget_refs: list[str] = Field(min_length=1)
    cache_policy_refs: list[str] = Field(min_length=1)
    traversal_limit_refs: list[str] = Field(min_length=1)
    batch_policy_refs: list[str] = Field(min_length=1)
    cardinality_policy_refs: list[str] = Field(min_length=1)
    queue_policy_refs: list[str] = Field(min_length=1)
    envelope_refs: list[str] = Field(min_length=1)
    backpressure_rule_refs: list[str] = Field(min_length=1)
    degradation_refs: list[str] = Field(min_length=1)
    benchmark_refs: list[str] = Field(min_length=1)
    trace_refs: list[str] = Field(min_length=1)
    as_of: str = Field(min_length=10, max_length=80)
    immutable: Literal[True] = True
    supersedable: Literal[True] = True
    snapshot_is_not_truth_or_evidence_strength_verdict: Literal[True] = True
    def fingerprint(self) -> str: return canonical_sha256(self)


class EntityEvidenceRuntimePerformanceScaleBundle(BaseModel):
    release: Literal["3.98.0"] = "3.98.0"
    contract: Literal[CONTRACT_VERSION] = CONTRACT_VERSION
    policies: list[PerformanceScalePolicy] = Field(min_length=1)
    profiles: list[RuntimePerformanceProfile] = Field(min_length=1)
    budgets: list[ExecutionBudget] = Field(min_length=1)
    cache_policies: list[CachePolicy] = Field(min_length=1)
    traversal_limits: list[GraphTraversalLimit] = Field(min_length=1)
    batch_policies: list[BatchParallelismPolicy] = Field(min_length=1)
    cardinality_policies: list[HighCardinalityEntityPolicy] = Field(min_length=1)
    queue_policies: list[FederationQueuePolicy] = Field(min_length=1)
    package_envelopes: list[PackageSizeEnvelope] = Field(min_length=1)
    backpressure_rules: list[BackpressureRule] = Field(min_length=1)
    degradation_decisions: list[DegradationDecision] = Field(min_length=1)
    benchmarks: list[ScaleBenchmarkResult] = Field(min_length=1)
    traces: list[PerformanceScaleTrace] = Field(min_length=1)
    snapshots: list[PerformanceScaleSnapshot] = Field(min_length=1)
    database_migration: Literal["none"] = "none"

    @model_validator(mode="after")
    def validate_bundle(self):
        groups = [
            (self.policies,"policy_id"),(self.profiles,"profile_id"),(self.budgets,"budget_id"),
            (self.cache_policies,"cache_policy_id"),(self.traversal_limits,"traversal_limit_id"),
            (self.batch_policies,"batch_policy_id"),(self.cardinality_policies,"cardinality_policy_id"),
            (self.queue_policies,"queue_policy_id"),(self.package_envelopes,"envelope_id"),
            (self.backpressure_rules,"backpressure_rule_id"),(self.degradation_decisions,"degradation_id"),
            (self.benchmarks,"benchmark_id"),(self.traces,"trace_id"),(self.snapshots,"snapshot_id")]
        for items,field in groups:
            _unique([getattr(x,field) for x in items], field)
        profile_ids={x.profile_id for x in self.profiles}
        budget_ids={x.budget_id for x in self.budgets}
        cache_ids={x.cache_policy_id for x in self.cache_policies}
        traversal_ids={x.traversal_limit_id for x in self.traversal_limits}
        batch_ids={x.batch_policy_id for x in self.batch_policies}
        cardinality_ids={x.cardinality_policy_id for x in self.cardinality_policies}
        queue_ids={x.queue_policy_id for x in self.queue_policies}
        envelope_ids={x.envelope_id for x in self.package_envelopes}
        backpressure_ids={x.backpressure_rule_id for x in self.backpressure_rules}
        degradation_ids={x.degradation_id for x in self.degradation_decisions}
        benchmark_ids={x.benchmark_id for x in self.benchmarks}
        trace_ids={x.trace_id for x in self.traces}
        policy_ids={x.policy_id for x in self.policies}
        for b in self.benchmarks:
            if b.profile_ref not in profile_ids:
                raise ValueError("benchmark profile unresolved")
        for t in self.traces:
            if not set(t.profile_refs)<=profile_ids or not set(t.budget_refs)<=budget_ids or not set(t.cache_policy_refs)<=cache_ids or not set(t.traversal_limit_refs)<=traversal_ids or not set(t.batch_policy_refs)<=batch_ids or not set(t.cardinality_policy_refs)<=cardinality_ids or not set(t.queue_policy_refs)<=queue_ids or not set(t.envelope_refs)<=envelope_ids or not set(t.degradation_refs)<=degradation_ids or not set(t.benchmark_refs)<=benchmark_ids:
                raise ValueError("trace reference unresolved")
        for s in self.snapshots:
            if not set(s.policy_refs)<=policy_ids or not set(s.profile_refs)<=profile_ids or not set(s.budget_refs)<=budget_ids or not set(s.cache_policy_refs)<=cache_ids or not set(s.traversal_limit_refs)<=traversal_ids or not set(s.batch_policy_refs)<=batch_ids or not set(s.cardinality_policy_refs)<=cardinality_ids or not set(s.queue_policy_refs)<=queue_ids or not set(s.envelope_refs)<=envelope_ids or not set(s.backpressure_rule_refs)<=backpressure_ids or not set(s.degradation_refs)<=degradation_ids or not set(s.benchmark_refs)<=benchmark_ids or not set(s.trace_refs)<=trace_ids:
                raise ValueError("snapshot reference unresolved")
        return self

    def fingerprint(self) -> str: return canonical_sha256(self)


@lru_cache(maxsize=1)
def reference_entity_evidence_runtime_performance_scale_bundle() -> EntityEvidenceRuntimePerformanceScaleBundle:
    policy=PerformanceScalePolicy(policy_id="entity-evidence-performance-scale-default-v1")
    profiles=[
        RuntimePerformanceProfile(profile_id="profile-query-interactive",workload_class="interactive-query",target_capability="entity-evidence-query",contract=V392_CONTRACT,target_p50_latency_ms=80,target_p95_latency_ms=180,target_throughput_per_second=25,maximum_concurrency=64),
        RuntimePerformanceProfile(profile_id="profile-graph-traversal",workload_class="graph-traversal",target_capability="unified-entity-evidence-runtime",contract=V390_CONTRACT,target_p50_latency_ms=180,target_p95_latency_ms=500,target_throughput_per_second=10,maximum_concurrency=24),
        RuntimePerformanceProfile(profile_id="profile-federation",workload_class="federation-exchange",target_capability="federation-governance",contract=V396_CONTRACT,target_p50_latency_ms=250,target_p95_latency_ms=800,target_throughput_per_second=8,maximum_concurrency=16),
        RuntimePerformanceProfile(profile_id="profile-package",workload_class="evidence-package",target_capability="cross-product-handoff",contract=V394_CONTRACT,target_p50_latency_ms=400,target_p95_latency_ms=1200,target_throughput_per_second=4,maximum_concurrency=8),
    ]
    budgets=[
        ExecutionBudget(budget_id="budget-query",workload_class="interactive-query",wall_time_ms=2500,cpu_time_ms=2000,memory_mb=768,max_result_objects=1000,max_intermediate_objects=10000,max_external_calls=8,on_exhaustion="bounded-results"),
        ExecutionBudget(budget_id="budget-traversal",workload_class="graph-traversal",wall_time_ms=8000,cpu_time_ms=7000,memory_mb=2048,max_result_objects=500,max_intermediate_objects=100000,max_external_calls=4,on_exhaustion="incomplete-qualified"),
        ExecutionBudget(budget_id="budget-federation",workload_class="federation-exchange",wall_time_ms=12000,cpu_time_ms=6000,memory_mb=1024,max_result_objects=5000,max_intermediate_objects=10000,max_external_calls=32,on_exhaustion="queue-only"),
        ExecutionBudget(budget_id="budget-package",workload_class="evidence-package",wall_time_ms=20000,cpu_time_ms=15000,memory_mb=4096,max_result_objects=25000,max_intermediate_objects=50000,max_external_calls=0,on_exhaustion="incomplete-qualified"),
    ]
    caches=[
        CachePolicy(cache_policy_id="cache-contracts",target_kind="contract-document",mode="immutable-object",ttl_seconds=86400,content_addressed=True),
        CachePolicy(cache_policy_id="cache-query-plans",target_kind="query-plan",mode="read-through",ttl_seconds=300,content_addressed=True),
        CachePolicy(cache_policy_id="cache-derived-results",target_kind="derived-result",mode="write-through",ttl_seconds=120,content_addressed=True),
    ]
    traversals=[
        GraphTraversalLimit(traversal_limit_id="traversal-interactive",target_graph="entity-evidence-graph",max_hops=4,max_nodes_visited=5000,max_edges_visited=20000,max_paths_returned=100,timeout_ms=2000),
        GraphTraversalLimit(traversal_limit_id="traversal-investigation",target_graph="investigation-graph",max_hops=8,max_nodes_visited=50000,max_edges_visited=250000,max_paths_returned=500,timeout_ms=7000),
        GraphTraversalLimit(traversal_limit_id="traversal-federated",target_graph="federated-reference-graph",max_hops=3,max_nodes_visited=10000,max_edges_visited=40000,max_paths_returned=150,timeout_ms=5000),
    ]
    batches=[
        BatchParallelismPolicy(batch_policy_id="batch-query",workload_class="interactive-query",max_batch_size=64,max_parallel_workers=8,ordering_guarantee="explicit-result-order"),
        BatchParallelismPolicy(batch_policy_id="batch-linkage",workload_class="entity-resolution",max_batch_size=1000,max_parallel_workers=16,ordering_guarantee="preserve-input-order"),
        BatchParallelismPolicy(batch_policy_id="batch-federation",workload_class="federation-exchange",max_batch_size=250,max_parallel_workers=8,ordering_guarantee="preserve-input-order"),
    ]
    cardinality=[
        HighCardinalityEntityPolicy(cardinality_policy_id="cardinality-entities",entity_kind="resolved-entity",soft_limit=100000,hard_limit=1000000,page_size=1000,partition_strategy="stable-hash"),
        HighCardinalityEntityPolicy(cardinality_policy_id="cardinality-documents",entity_kind="documentary-source",soft_limit=250000,hard_limit=2500000,page_size=2000,partition_strategy="source-partition"),
    ]
    queues=[
        FederationQueuePolicy(queue_policy_id="queue-federation-intake",queue_name="federation-intake",max_depth=50000,max_inflight=128,retry_limit=5,retry_backoff_seconds=30,priority_classes=["policy-critical","interactive","background"]),
        FederationQueuePolicy(queue_policy_id="queue-federation-validation",queue_name="federation-local-validation",max_depth=20000,max_inflight=64,retry_limit=3,retry_backoff_seconds=60,priority_classes=["manual-review","validation-required","background"]),
    ]
    envelopes=[
        PackageSizeEnvelope(envelope_id="envelope-investigation-package",package_kind="reproducible-investigation-package",soft_limit_mb=250,hard_limit_mb=1024,max_object_count=100000,max_single_artifact_mb=512,oversize_action="incomplete-qualified"),
        PackageSizeEnvelope(envelope_id="envelope-federation-manifest",package_kind="federated-exchange-manifest",soft_limit_mb=64,hard_limit_mb=256,max_object_count=25000,max_single_artifact_mb=128,oversize_action="queue-only"),
    ]
    backpressure=[
        BackpressureRule(backpressure_rule_id="backpressure-query",signal="query-worker-saturation",threshold=0.85,comparison="gte",action="bounded-results",retryable=True),
        BackpressureRule(backpressure_rule_id="backpressure-traversal",signal="graph-memory-pressure",threshold=0.80,comparison="gte",action="reduced-parallelism",retryable=True),
        BackpressureRule(backpressure_rule_id="backpressure-federation",signal="federation-queue-depth-ratio",threshold=0.90,comparison="gte",action="queue-only",retryable=True),
    ]
    degradations=[
        DegradationDecision(degradation_id="degrade-query-bounded",trigger_ref="backpressure-query",workload_class="interactive-query",mode="bounded-results",rationale="Worker saturation requires explicit bounded results while preserving ranking qualifications and provenance.",result_completeness="bounded",observed_at="2026-10-01T06:10:00Z"),
        DegradationDecision(degradation_id="degrade-traversal-partial",trigger_ref="backpressure-traversal",workload_class="graph-traversal",mode="reduced-parallelism",rationale="Graph memory pressure requires reduced parallelism and an explicitly qualified partial execution state.",result_completeness="partial",observed_at="2026-10-01T06:11:00Z"),
        DegradationDecision(degradation_id="degrade-federation-queue",trigger_ref="backpressure-federation",workload_class="federation-exchange",mode="queue-only",rationale="Federation queue saturation requires durable queueing without changing remote-reference or validation state.",result_completeness="queued",observed_at="2026-10-01T06:12:00Z"),
    ]
    benchmarks=[
        ScaleBenchmarkResult(benchmark_id="bench-query-10k",profile_ref="profile-query-interactive",workload_class="interactive-query",dataset_scale_label="10k-objects",input_objects=10000,concurrent_workers=16,p50_latency_ms=44,p95_latency_ms=121,throughput_per_second=41,peak_memory_mb=390,status="pass",measured_at="2026-10-01T06:20:00Z",environment_ref="perf-env-python312-postgres"),
        ScaleBenchmarkResult(benchmark_id="bench-query-1m",profile_ref="profile-query-interactive",workload_class="interactive-query",dataset_scale_label="1m-objects",input_objects=1000000,concurrent_workers=32,p50_latency_ms=76,p95_latency_ms=174,throughput_per_second=28,peak_memory_mb=710,status="pass",measured_at="2026-10-01T06:21:00Z",environment_ref="perf-env-python312-postgres"),
        ScaleBenchmarkResult(benchmark_id="bench-traversal-100k",profile_ref="profile-graph-traversal",workload_class="graph-traversal",dataset_scale_label="100k-nodes",input_objects=100000,concurrent_workers=12,p50_latency_ms=132,p95_latency_ms=420,throughput_per_second=13,peak_memory_mb=1550,status="pass",measured_at="2026-10-01T06:22:00Z",environment_ref="perf-env-python312-postgres"),
        ScaleBenchmarkResult(benchmark_id="bench-traversal-1m",profile_ref="profile-graph-traversal",workload_class="graph-traversal",dataset_scale_label="1m-nodes",input_objects=1000000,concurrent_workers=16,p50_latency_ms=205,p95_latency_ms=610,throughput_per_second=8,peak_memory_mb=2190,status="warn",measured_at="2026-10-01T06:23:00Z",environment_ref="perf-env-python312-postgres"),
        ScaleBenchmarkResult(benchmark_id="bench-federation-50k",profile_ref="profile-federation",workload_class="federation-exchange",dataset_scale_label="50k-remote-refs",input_objects=50000,concurrent_workers=8,p50_latency_ms=188,p95_latency_ms=590,throughput_per_second=10,peak_memory_mb=840,status="pass",measured_at="2026-10-01T06:24:00Z",environment_ref="perf-env-federation-queue"),
        ScaleBenchmarkResult(benchmark_id="bench-package-100k",profile_ref="profile-package",workload_class="evidence-package",dataset_scale_label="100k-package-objects",input_objects=100000,concurrent_workers=4,p50_latency_ms=350,p95_latency_ms=980,throughput_per_second=5,peak_memory_mb=3100,status="pass",measured_at="2026-10-01T06:25:00Z",environment_ref="perf-env-package-builder"),
    ]
    trace1=PerformanceScaleTrace(trace_id="performance-scale-trace-interactive",profile_refs=["profile-query-interactive","profile-graph-traversal"],budget_refs=["budget-query","budget-traversal"],cache_policy_refs=[x.cache_policy_id for x in caches],traversal_limit_refs=["traversal-interactive","traversal-investigation"],batch_policy_refs=["batch-query","batch-linkage"],cardinality_policy_refs=[x.cardinality_policy_id for x in cardinality],queue_policy_refs=[],envelope_refs=["envelope-investigation-package"],degradation_refs=["degrade-query-bounded","degrade-traversal-partial"],benchmark_refs=["bench-query-10k","bench-query-1m","bench-traversal-100k","bench-traversal-1m","bench-package-100k"],started_at="2026-10-01T06:00:00Z",completed_at="2026-10-01T06:30:00Z")
    trace2=PerformanceScaleTrace(trace_id="performance-scale-trace-federation",profile_refs=["profile-federation"],budget_refs=["budget-federation"],cache_policy_refs=["cache-contracts"],traversal_limit_refs=["traversal-federated"],batch_policy_refs=["batch-federation"],cardinality_policy_refs=[],queue_policy_refs=[x.queue_policy_id for x in queues],envelope_refs=["envelope-federation-manifest"],degradation_refs=["degrade-federation-queue"],benchmark_refs=["bench-federation-50k"],started_at="2026-10-01T06:00:00Z",completed_at="2026-10-01T06:30:00Z")
    snapshot=PerformanceScaleSnapshot(snapshot_id="performance-scale-snapshot-001",policy_refs=[policy.policy_id],profile_refs=[x.profile_id for x in profiles],budget_refs=[x.budget_id for x in budgets],cache_policy_refs=[x.cache_policy_id for x in caches],traversal_limit_refs=[x.traversal_limit_id for x in traversals],batch_policy_refs=[x.batch_policy_id for x in batches],cardinality_policy_refs=[x.cardinality_policy_id for x in cardinality],queue_policy_refs=[x.queue_policy_id for x in queues],envelope_refs=[x.envelope_id for x in envelopes],backpressure_rule_refs=[x.backpressure_rule_id for x in backpressure],degradation_refs=[x.degradation_id for x in degradations],benchmark_refs=[x.benchmark_id for x in benchmarks],trace_refs=[trace1.trace_id,trace2.trace_id],as_of="2026-10-01T06:30:00Z")
    return EntityEvidenceRuntimePerformanceScaleBundle(policies=[policy],profiles=profiles,budgets=budgets,cache_policies=caches,traversal_limits=traversals,batch_policies=batches,cardinality_policies=cardinality,queue_policies=queues,package_envelopes=envelopes,backpressure_rules=backpressure,degradation_decisions=degradations,benchmarks=benchmarks,traces=[trace1,trace2],snapshots=[snapshot])


def contract_document() -> dict[str, Any]:
    b=reference_entity_evidence_runtime_performance_scale_bundle()
    return {
        "ok": True,
        "release": CORE_RELEASE,
        "contract": CONTRACT_VERSION,
        "upstream_contracts": [V390_CONTRACT,V391_CONTRACT,V392_CONTRACT,V393_CONTRACT,V394_CONTRACT,V395_CONTRACT,V396_CONTRACT,V397_CONTRACT],
        "principles": {
            "performance_optimization_preserves_contract_semantics": True,
            "performance_optimization_preserves_epistemic_state": True,
            "performance_optimization_preserves_validation_state": True,
            "performance_optimization_preserves_provenance": True,
            "execution_budgets_are_explicit": True,
            "traversal_limits_are_explicit": True,
            "sampling_and_truncation_are_explicit": True,
            "cache_freshness_is_explicit": True,
            "backpressure_is_governed": True,
            "scale_benchmarks_are_reproducible": True,
            "degraded_modes_can_only_preserve_or_reduce_authority": True,
        },
        "boundaries": {
            "faster_execution_increases_evidence_strength": False,
            "cache_hit_establishes_freshness": False,
            "cache_hit_establishes_content_truth": False,
            "parallel_execution_is_independent_corroboration": False,
            "truncated_result_establishes_nonexistence": False,
            "queue_priority_is_evidence_priority": False,
            "benchmark_success_establishes_claim_truth": False,
            "budget_exhaustion_may_be_silent": False,
            "degraded_mode_may_increase_authority": False,
            "performance_optimization_may_drop_provenance": False,
            "identity_graph_mutation_performed": False,
            "relationship_graph_mutation_performed": False,
            "evidence_graph_mutation_performed": False,
        },
        "reference": {
            "profiles": len(b.profiles),
            "budgets": len(b.budgets),
            "cache_policies": len(b.cache_policies),
            "traversal_limits": len(b.traversal_limits),
            "batch_policies": len(b.batch_policies),
            "cardinality_policies": len(b.cardinality_policies),
            "queue_policies": len(b.queue_policies),
            "package_envelopes": len(b.package_envelopes),
            "backpressure_rules": len(b.backpressure_rules),
            "degradation_decisions": len(b.degradation_decisions),
            "benchmarks": len(b.benchmarks),
            "benchmark_passes": sum(x.status == BenchmarkStatus.pass_ for x in b.benchmarks),
            "benchmark_warnings": sum(x.status == BenchmarkStatus.warn for x in b.benchmarks),
            "traces": len(b.traces),
            "snapshots": len(b.snapshots),
            "bundle_fingerprint_sha256": b.fingerprint(),
        },
        "database_migration": "none",
    }
