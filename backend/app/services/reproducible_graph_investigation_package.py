from __future__ import annotations

from enum import Enum
from typing import Any, Literal
from pydantic import BaseModel, Field, model_validator

from .computational_runtime_objects import canonical_sha256
from .entity_centric_timeline_event_association import (
    EntityCentricTimelineEventAssociationBundle,
    reference_entity_centric_timeline_event_association_bundle,
)

CORE_RELEASE = "3.88.0"
CONTRACT_VERSION = "sc.core.reproducible-graph-investigation-package.v1"


def _unique(values: list[str], label: str) -> None:
    if len(values) != len(set(values)):
        raise ValueError(f"{label} must be unique")


class EpistemicState(str, Enum):
    source_observed = "source-observed"
    candidate = "candidate"
    hypothesis = "hypothesis"
    qualified = "qualified"
    resolved_for_handoff = "resolved-for-handoff"
    partially_resolved = "partially-resolved"
    analytical = "analytical"
    documentary = "documentary"
    timeline_view = "timeline-view"
    reproducibility_metadata = "reproducibility-metadata"


class PackagingRole(str, Enum):
    primary = "primary"
    supporting = "supporting"
    contextual = "contextual"
    contradictory = "contradictory"
    provenance = "provenance"
    environment = "environment"
    reproducibility = "reproducibility"


class ReproductionOperation(str, Enum):
    load_snapshot = "load-snapshot"
    verify_fingerprint = "verify-fingerprint"
    reconstruct_view = "reconstruct-view"
    replay_query = "replay-query"
    validate_contract = "validate-contract"
    compare_output = "compare-output"
    export_package = "export-package"


class VerificationDisposition(str, Enum):
    verified = "verified"
    verified_with_qualifications = "verified-with-qualifications"
    mismatch = "mismatch"
    incomplete = "incomplete"
    not_run = "not-run"


class InvestigationPackagePolicy(BaseModel):
    package_policy_id: str = Field(min_length=2, max_length=500)
    require_content_fingerprints: Literal[True] = True
    require_upstream_contract_identity: Literal[True] = True
    require_epistemic_state_preservation: Literal[True] = True
    require_source_provenance_preservation: Literal[True] = True
    require_contradiction_preservation: Literal[True] = True
    require_environment_manifest: Literal[True] = True
    require_reproduction_plan: Literal[True] = True
    require_as_of_time: Literal[True] = True
    reproducibility_can_establish_truth: Literal[False] = False
    reproducibility_can_establish_authenticity: Literal[False] = False
    reproducibility_can_establish_admissibility: Literal[False] = False
    package_hash_can_establish_content_truth: Literal[False] = False
    replay_success_can_establish_correctness: Literal[False] = False
    automatic_graph_mutation_allowed: Literal[False] = False
    metadata: dict[str, Any] = Field(default_factory=dict)
    def fingerprint(self) -> str: return canonical_sha256(self)


class InvestigationQuestion(BaseModel):
    investigation_question_id: str = Field(min_length=2, max_length=500)
    question: str = Field(min_length=3, max_length=12000)
    scope_note: str = Field(min_length=3, max_length=12000)
    entity_refs: list[str] = Field(default_factory=list)
    temporal_scope: str | None = Field(default=None, max_length=2000)
    relationship_scope: str | None = Field(default=None, max_length=2000)
    question_is_not_claim: Literal[True] = True
    package_does_not_prejudge_answer: Literal[True] = True
    metadata: dict[str, Any] = Field(default_factory=dict)
    @model_validator(mode="after")
    def validate_question(self):
        _unique(self.entity_refs, "entity_refs"); return self
    def fingerprint(self) -> str: return canonical_sha256(self)


class InvestigationObjectBinding(BaseModel):
    object_binding_id: str = Field(min_length=2, max_length=500)
    upstream_contract: str = Field(min_length=3, max_length=500)
    object_type: str = Field(min_length=2, max_length=500)
    object_ref: str = Field(min_length=2, max_length=500)
    object_fingerprint_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    epistemic_state: EpistemicState
    packaging_role: PackagingRole
    provenance_refs: list[str] = Field(min_length=1)
    as_of: str = Field(min_length=10, max_length=80)
    source_state_preserved: Literal[True] = True
    packaging_does_not_promote_epistemic_state: Literal[True] = True
    current_state_not_guaranteed_after_as_of: Literal[True] = True
    metadata: dict[str, Any] = Field(default_factory=dict)
    @model_validator(mode="after")
    def validate_binding(self):
        _unique(self.provenance_refs, "provenance_refs"); return self
    def fingerprint(self) -> str: return canonical_sha256(self)


class InvestigationArtifactRecord(BaseModel):
    artifact_id: str = Field(min_length=2, max_length=500)
    logical_path: str = Field(min_length=1, max_length=2000)
    media_type: str = Field(min_length=3, max_length=300)
    content_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    byte_size: int = Field(ge=0)
    generated_from_refs: list[str] = Field(default_factory=list)
    provenance_refs: list[str] = Field(min_length=1)
    content_hash_verifies_bytes_not_truth: Literal[True] = True
    metadata: dict[str, Any] = Field(default_factory=dict)
    @model_validator(mode="after")
    def validate_artifact(self):
        _unique(self.generated_from_refs, "generated_from_refs"); _unique(self.provenance_refs, "provenance_refs"); return self
    def fingerprint(self) -> str: return canonical_sha256(self)


class ReproductionEnvironmentManifest(BaseModel):
    environment_manifest_id: str = Field(min_length=2, max_length=500)
    core_release: Literal["3.88.0"] = "3.88.0"
    contract_version: Literal["sc.core.reproducible-graph-investigation-package.v1"] = CONTRACT_VERSION
    upstream_release: Literal["3.87.0"] = "3.87.0"
    python_version: str = Field(min_length=3, max_length=100)
    dependency_lock_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    configuration_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    runtime_refs: list[str] = Field(default_factory=list)
    external_source_snapshot_refs: list[str] = Field(default_factory=list)
    environment_capture_is_not_execution_guarantee: Literal[True] = True
    replay_environment_is_not_truth_authority: Literal[True] = True
    metadata: dict[str, Any] = Field(default_factory=dict)
    @model_validator(mode="after")
    def validate_environment(self):
        _unique(self.runtime_refs,"runtime_refs"); _unique(self.external_source_snapshot_refs,"external_source_snapshot_refs"); return self
    def fingerprint(self) -> str: return canonical_sha256(self)


class ReproductionStep(BaseModel):
    reproduction_step_id: str = Field(min_length=2, max_length=500)
    sequence: int = Field(ge=1)
    operation: ReproductionOperation
    input_refs: list[str] = Field(min_length=1)
    expected_output_refs: list[str] = Field(default_factory=list)
    parameters: dict[str, Any] = Field(default_factory=dict)
    deterministic_expected: bool
    external_runtime_required: bool = False
    stopping_condition: str = Field(min_length=3, max_length=4000)
    replay_does_not_mutate_graph: Literal[True] = True
    successful_step_is_not_truth_validation: Literal[True] = True
    metadata: dict[str, Any] = Field(default_factory=dict)
    @model_validator(mode="after")
    def validate_step(self):
        _unique(self.input_refs,"input_refs"); _unique(self.expected_output_refs,"expected_output_refs"); return self
    def fingerprint(self) -> str: return canonical_sha256(self)


class GraphInvestigationManifest(BaseModel):
    investigation_manifest_id: str = Field(min_length=2, max_length=500)
    package_policy_ref: str = Field(min_length=2, max_length=500)
    question_refs: list[str] = Field(min_length=1)
    object_binding_refs: list[str] = Field(min_length=1)
    artifact_refs: list[str] = Field(min_length=1)
    environment_manifest_ref: str = Field(min_length=2, max_length=500)
    reproduction_step_refs: list[str] = Field(min_length=1)
    upstream_snapshot_refs: list[str] = Field(min_length=1)
    as_of: str = Field(min_length=10, max_length=80)
    title: str = Field(min_length=3, max_length=2000)
    purpose: str = Field(min_length=3, max_length=12000)
    limitations: list[str] = Field(min_length=1)
    portable: Literal[True] = True
    immutable_manifest: Literal[True] = True
    package_is_not_truth_verdict: Literal[True] = True
    package_is_not_completeness_guarantee: Literal[True] = True
    metadata: dict[str, Any] = Field(default_factory=dict)
    @model_validator(mode="after")
    def validate_manifest(self):
        for vals,label in ((self.question_refs,"question_refs"),(self.object_binding_refs,"object_binding_refs"),(self.artifact_refs,"artifact_refs"),(self.reproduction_step_refs,"reproduction_step_refs"),(self.upstream_snapshot_refs,"upstream_snapshot_refs"),(self.limitations,"limitations")):
            _unique(vals,label)
        return self
    def fingerprint(self) -> str: return canonical_sha256(self)


class PackageIntegrityRecord(BaseModel):
    package_integrity_record_id: str = Field(min_length=2, max_length=500)
    investigation_manifest_ref: str = Field(min_length=2, max_length=500)
    manifest_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    ordered_artifact_refs: list[str] = Field(min_length=1)
    ordered_artifact_sha256s: list[str] = Field(min_length=1)
    package_root_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    algorithm: Literal["sha256"] = "sha256"
    verified_at: str = Field(min_length=10, max_length=80)
    disposition: VerificationDisposition
    verification_note: str = Field(min_length=3, max_length=8000)
    integrity_verification_is_not_truth_verification: Literal[True] = True
    metadata: dict[str, Any] = Field(default_factory=dict)
    @model_validator(mode="after")
    def validate_integrity(self):
        _unique(self.ordered_artifact_refs,"ordered_artifact_refs")
        if len(self.ordered_artifact_refs) != len(self.ordered_artifact_sha256s):
            raise ValueError("artifact refs and sha256 lists must align")
        for x in self.ordered_artifact_sha256s:
            if len(x)!=64 or any(c not in '0123456789abcdef' for c in x): raise ValueError("invalid artifact sha256")
        return self
    def fingerprint(self) -> str: return canonical_sha256(self)


class PackageVerificationRecord(BaseModel):
    package_verification_record_id: str = Field(min_length=2, max_length=500)
    investigation_manifest_ref: str = Field(min_length=2, max_length=500)
    verifier_ref: str = Field(min_length=2, max_length=500)
    reproduced_step_refs: list[str] = Field(min_length=1)
    compared_object_binding_refs: list[str] = Field(default_factory=list)
    disposition: VerificationDisposition
    qualifications: list[str] = Field(default_factory=list)
    verified_at: str = Field(min_length=10, max_length=80)
    independent_verification_requires_independent_sources: Literal[True] = True
    byte_identical_replay_is_not_independent_corroboration: Literal[True] = True
    replay_success_is_not_correctness_proof: Literal[True] = True
    metadata: dict[str, Any] = Field(default_factory=dict)
    @model_validator(mode="after")
    def validate_verification(self):
        _unique(self.reproduced_step_refs,"reproduced_step_refs"); _unique(self.compared_object_binding_refs,"compared_object_binding_refs"); _unique(self.qualifications,"qualifications"); return self
    def fingerprint(self) -> str: return canonical_sha256(self)


class ReproducibleGraphInvestigationSnapshot(BaseModel):
    graph_investigation_snapshot_id: str = Field(min_length=2, max_length=500)
    event_timeline_snapshot_ref: str = Field(min_length=2, max_length=500)
    investigation_manifest_ref: str = Field(min_length=2, max_length=500)
    integrity_record_refs: list[str] = Field(min_length=1)
    verification_record_refs: list[str] = Field(min_length=1)
    created_at: str = Field(min_length=10, max_length=80)
    immutable: Literal[True] = True
    later_revisions_may_supersede_snapshot: Literal[True] = True
    snapshot_does_not_override_source_history: Literal[True] = True
    metadata: dict[str, Any] = Field(default_factory=dict)
    @model_validator(mode="after")
    def validate_snapshot(self):
        _unique(self.integrity_record_refs,"integrity_record_refs"); _unique(self.verification_record_refs,"verification_record_refs"); return self
    def fingerprint(self) -> str: return canonical_sha256(self)


class ReproducibleGraphInvestigationPackageBundle(BaseModel):
    entity_centric_timeline_event_association_bundle: EntityCentricTimelineEventAssociationBundle
    policies: list[InvestigationPackagePolicy] = Field(min_length=1)
    questions: list[InvestigationQuestion] = Field(min_length=1)
    object_bindings: list[InvestigationObjectBinding] = Field(min_length=1)
    artifacts: list[InvestigationArtifactRecord] = Field(min_length=1)
    environments: list[ReproductionEnvironmentManifest] = Field(min_length=1)
    reproduction_steps: list[ReproductionStep] = Field(min_length=1)
    manifests: list[GraphInvestigationManifest] = Field(min_length=1)
    integrity_records: list[PackageIntegrityRecord] = Field(min_length=1)
    verification_records: list[PackageVerificationRecord] = Field(min_length=1)
    snapshots: list[ReproducibleGraphInvestigationSnapshot] = Field(min_length=1)
    identity_graph_mutation_performed: Literal[False] = False
    relationship_graph_mutation_performed: Literal[False] = False
    evidence_graph_mutation_performed: Literal[False] = False

    @model_validator(mode="after")
    def validate_bundle(self):
        def ids(items, attr, label):
            vals=[getattr(x,attr) for x in items]; _unique(vals,label); return set(vals)
        policy_ids=ids(self.policies,'package_policy_id','policy_ids')
        question_ids=ids(self.questions,'investigation_question_id','question_ids')
        binding_ids=ids(self.object_bindings,'object_binding_id','binding_ids')
        artifact_ids=ids(self.artifacts,'artifact_id','artifact_ids')
        env_ids=ids(self.environments,'environment_manifest_id','environment_ids')
        step_ids=ids(self.reproduction_steps,'reproduction_step_id','step_ids')
        manifest_ids=ids(self.manifests,'investigation_manifest_id','manifest_ids')
        integrity_ids=ids(self.integrity_records,'package_integrity_record_id','integrity_ids')
        verification_ids=ids(self.verification_records,'package_verification_record_id','verification_ids')
        snapshot_ids=ids(self.snapshots,'graph_investigation_snapshot_id','snapshot_ids')

        upstream=self.entity_centric_timeline_event_association_bundle
        contradiction=upstream.contradictory_identity_relationship_resolution_bundle
        reasoning=contradiction.multi_hop_research_investigation_graph_reasoning_bundle
        paths=reasoning.explainable_connection_paths_evidence_chains_bundle
        network=paths.network_structure_community_motif_bundle
        relationships=network.relationship_discovery_hypothesis_bundle
        documentary=relationships.public_record_documentary_source_bundle
        identity=documentary.cross_source_entity_reconciliation_bundle.probabilistic_record_linkage_bundle.temporal_identity_bundle.entity_resolution_identity_graph_bundle
        entity_ids={x.entity_id for x in identity.entities}
        allowed_refs=set()
        for seq, attr in [
            (upstream.snapshots,'event_timeline_snapshot_id'),(upstream.timelines,'entity_timeline_id'),(upstream.events,'event_id'),
            (contradiction.snapshots,'resolution_snapshot_id'),(contradiction.decisions,'resolution_decision_id'),(contradiction.contradiction_sets,'contradiction_set_id'),
            (reasoning.snapshots,'reasoning_snapshot_id'),(reasoning.traces,'reasoning_trace_id'),
            (paths.snapshots,'connection_path_evidence_snapshot_id'),(paths.connection_paths,'connection_path_id'),(paths.evidence_chains,'evidence_chain_id'),
            (network.structure_snapshots,'network_structure_snapshot_id'),
            (documentary.snapshots,'documentary_snapshot_id'),(documentary.segments,'document_segment_id'),
        ]:
            allowed_refs.update(getattr(x,attr) for x in seq)
        for q in self.questions:
            if not set(q.entity_refs).issubset(entity_ids): raise ValueError('question references unknown entity')
        for b in self.object_bindings:
            if b.object_ref not in allowed_refs: raise ValueError(f'object binding references unknown upstream object: {b.object_ref}')
        for m in self.manifests:
            if m.package_policy_ref not in policy_ids: raise ValueError('manifest references unknown policy')
            if not set(m.question_refs).issubset(question_ids): raise ValueError('manifest references unknown question')
            if not set(m.object_binding_refs).issubset(binding_ids): raise ValueError('manifest references unknown object binding')
            if not set(m.artifact_refs).issubset(artifact_ids): raise ValueError('manifest references unknown artifact')
            if m.environment_manifest_ref not in env_ids: raise ValueError('manifest references unknown environment')
            if not set(m.reproduction_step_refs).issubset(step_ids): raise ValueError('manifest references unknown reproduction step')
            if not set(m.upstream_snapshot_refs).issubset(allowed_refs): raise ValueError('manifest references unknown upstream snapshot')
        for i in self.integrity_records:
            if i.investigation_manifest_ref not in manifest_ids: raise ValueError('integrity record references unknown manifest')
            if not set(i.ordered_artifact_refs).issubset(artifact_ids): raise ValueError('integrity record references unknown artifact')
        for v in self.verification_records:
            if v.investigation_manifest_ref not in manifest_ids: raise ValueError('verification references unknown manifest')
            if not set(v.reproduced_step_refs).issubset(step_ids): raise ValueError('verification references unknown step')
            if not set(v.compared_object_binding_refs).issubset(binding_ids): raise ValueError('verification references unknown binding')
        upstream_snapshot_ids={x.event_timeline_snapshot_id for x in upstream.snapshots}
        for s in self.snapshots:
            if s.event_timeline_snapshot_ref not in upstream_snapshot_ids: raise ValueError('snapshot references unknown v3.87 timeline snapshot')
            if s.investigation_manifest_ref not in manifest_ids: raise ValueError('snapshot references unknown manifest')
            if not set(s.integrity_record_refs).issubset(integrity_ids): raise ValueError('snapshot references unknown integrity record')
            if not set(s.verification_record_refs).issubset(verification_ids): raise ValueError('snapshot references unknown verification record')
        return self

    def fingerprint(self) -> str: return canonical_sha256(self)


def _sha(text: str) -> str:
    import hashlib
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


def reference_reproducible_graph_investigation_package_bundle() -> ReproducibleGraphInvestigationPackageBundle:
    upstream=reference_entity_centric_timeline_event_association_bundle()
    contradiction=upstream.contradictory_identity_relationship_resolution_bundle
    reasoning=contradiction.multi_hop_research_investigation_graph_reasoning_bundle
    paths=reasoning.explainable_connection_paths_evidence_chains_bundle
    network=paths.network_structure_community_motif_bundle
    relationships=network.relationship_discovery_hypothesis_bundle
    documentary=relationships.public_record_documentary_source_bundle
    identity=documentary.cross_source_entity_reconciliation_bundle.probabilistic_record_linkage_bundle.temporal_identity_bundle.entity_resolution_identity_graph_bundle
    e1,e2=identity.entities[:2]
    policy=InvestigationPackagePolicy(package_policy_id='graph-investigation-package-policy:reference:v1',metadata={'synthetic_reference':True})
    questions=[InvestigationQuestion(
        investigation_question_id='investigation-question:synthetic:entity-a-b:v1',
        question='What documented, hypothesized, contradictory, temporal, and analytical connections exist between the two synthetic reference entities?',
        scope_note='Package the governed graph investigation state without promoting candidates, hypotheses, timeline associations, or analytical paths into graph facts.',
        entity_refs=[e1.entity_id,e2.entity_id],temporal_scope='2024 through package as-of time',relationship_scope='bounded source-observed relationship plus unresolved/qualified alternatives',metadata={'synthetic_reference':True})]

    chosen=[
        ('sc.core.network-structure-community-motif-intelligence.v1','NetworkStructureSnapshot',network.structure_snapshots[0],network.structure_snapshots[0].network_structure_snapshot_id,EpistemicState.analytical,PackagingRole.contextual),
        ('sc.core.explainable-connection-paths-evidence-chains.v1','ConnectionPath',paths.connection_paths[0],paths.connection_paths[0].connection_path_id,EpistemicState.source_observed,PackagingRole.primary),
        ('sc.core.explainable-connection-paths-evidence-chains.v1','ConnectionPath',paths.connection_paths[1],paths.connection_paths[1].connection_path_id,EpistemicState.hypothesis,PackagingRole.contradictory),
        ('sc.core.explainable-connection-paths-evidence-chains.v1','EvidenceChain',paths.evidence_chains[0],paths.evidence_chains[0].evidence_chain_id,EpistemicState.qualified,PackagingRole.supporting),
        ('sc.core.multi-hop-research-investigation-graph-reasoning.v1','MultiHopReasoningTrace',reasoning.traces[0],reasoning.traces[0].reasoning_trace_id,EpistemicState.analytical,PackagingRole.contextual),
        ('sc.core.contradictory-identity-relationship-resolution.v1','ResolutionDecision',contradiction.decisions[0],contradiction.decisions[0].resolution_decision_id,EpistemicState.partially_resolved,PackagingRole.contradictory),
        ('sc.core.contradictory-identity-relationship-resolution.v1','ResolutionDecision',contradiction.decisions[1],contradiction.decisions[1].resolution_decision_id,EpistemicState.resolved_for_handoff,PackagingRole.contextual),
        ('sc.core.entity-centric-timeline-event-association.v1','EntityTimeline',upstream.timelines[0],upstream.timelines[0].entity_timeline_id,EpistemicState.timeline_view,PackagingRole.primary),
        ('sc.core.entity-centric-timeline-event-association.v1','EntityTimeline',upstream.timelines[1],upstream.timelines[1].entity_timeline_id,EpistemicState.timeline_view,PackagingRole.primary),
        ('sc.core.public-record-documentary-source-object-model.v1','DocumentSegmentAnchor',documentary.segments[0],documentary.segments[0].document_segment_id,EpistemicState.documentary,PackagingRole.supporting),
        ('sc.core.public-record-documentary-source-object-model.v1','DocumentSegmentAnchor',documentary.segments[2],documentary.segments[2].document_segment_id,EpistemicState.documentary,PackagingRole.contextual),
        ('sc.core.entity-centric-timeline-event-association.v1','EventTimelineSnapshot',upstream.snapshots[0],upstream.snapshots[0].event_timeline_snapshot_id,EpistemicState.timeline_view,PackagingRole.reproducibility),
    ]
    bindings=[]
    for idx,(contract,otype,obj,oref,state,role) in enumerate(chosen,1):
        bindings.append(InvestigationObjectBinding(
            object_binding_id=f'graph-investigation-binding:synthetic:{idx:02d}:v1', upstream_contract=contract, object_type=otype, object_ref=oref,
            object_fingerprint_sha256=canonical_sha256(obj), epistemic_state=state, packaging_role=role,
            provenance_refs=[f'provenance:synthetic:package-binding:{idx:02d}:v1'], as_of='2026-09-30T22:30:00Z', metadata={'synthetic_reference':True}))

    artifacts=[
        InvestigationArtifactRecord(artifact_id='investigation-artifact:synthetic:manifest-json:v1',logical_path='manifest/investigation-manifest.json',media_type='application/json',content_sha256=_sha('synthetic-manifest-json-v1'),byte_size=8192,generated_from_refs=[x.object_binding_id for x in bindings],provenance_refs=['provenance:synthetic:package-export:v1']),
        InvestigationArtifactRecord(artifact_id='investigation-artifact:synthetic:graph-snapshot-json:v1',logical_path='graph/network-snapshot.json',media_type='application/json',content_sha256=_sha('synthetic-network-snapshot-v1'),byte_size=16384,generated_from_refs=[bindings[0].object_binding_id],provenance_refs=['provenance:synthetic:graph-export:v1']),
        InvestigationArtifactRecord(artifact_id='investigation-artifact:synthetic:evidence-index-json:v1',logical_path='evidence/evidence-index.json',media_type='application/json',content_sha256=_sha('synthetic-evidence-index-v1'),byte_size=12288,generated_from_refs=[bindings[3].object_binding_id,bindings[9].object_binding_id,bindings[10].object_binding_id],provenance_refs=['provenance:synthetic:evidence-export:v1']),
        InvestigationArtifactRecord(artifact_id='investigation-artifact:synthetic:readme:v1',logical_path='README.md',media_type='text/markdown',content_sha256=_sha('synthetic-investigation-readme-v1'),byte_size=4096,generated_from_refs=[],provenance_refs=['provenance:synthetic:package-documentation:v1']),
    ]
    env=ReproductionEnvironmentManifest(environment_manifest_id='reproduction-environment:synthetic:v3880:v1',python_version='3.14 reference environment',dependency_lock_sha256=_sha('synthetic-dependency-lock-v3880'),configuration_sha256=_sha('synthetic-config-v3880'),runtime_refs=['platform-core:3.88.0'],external_source_snapshot_refs=[documentary.snapshots[0].documentary_snapshot_id],metadata={'synthetic_reference':True})
    steps=[
        ReproductionStep(reproduction_step_id='reproduction-step:synthetic:01-load:v1',sequence=1,operation=ReproductionOperation.load_snapshot,input_refs=[upstream.snapshots[0].event_timeline_snapshot_id],expected_output_refs=[bindings[-1].object_binding_id],deterministic_expected=True,stopping_condition='Stop if the referenced v3.87 snapshot fingerprint is unavailable or mismatched.'),
        ReproductionStep(reproduction_step_id='reproduction-step:synthetic:02-verify:v1',sequence=2,operation=ReproductionOperation.verify_fingerprint,input_refs=[x.object_binding_id for x in bindings],expected_output_refs=[x.object_binding_id for x in bindings],deterministic_expected=True,stopping_condition='Stop on any object fingerprint mismatch; do not silently substitute current objects.'),
        ReproductionStep(reproduction_step_id='reproduction-step:synthetic:03-view:v1',sequence=3,operation=ReproductionOperation.reconstruct_view,input_refs=[bindings[7].object_binding_id,bindings[8].object_binding_id,bindings[0].object_binding_id],expected_output_refs=[artifacts[1].artifact_id],deterministic_expected=True,stopping_condition='Stop if required timeline or graph-snapshot bindings are absent.'),
        ReproductionStep(reproduction_step_id='reproduction-step:synthetic:04-reasoning:v1',sequence=4,operation=ReproductionOperation.replay_query,input_refs=[bindings[1].object_binding_id,bindings[2].object_binding_id,bindings[3].object_binding_id,bindings[4].object_binding_id],expected_output_refs=[bindings[4].object_binding_id],deterministic_expected=False,external_runtime_required=False,stopping_condition='Preserve the unvalidated-hypothesis stopping boundary and do not force endpoint truth.'),
        ReproductionStep(reproduction_step_id='reproduction-step:synthetic:05-compare:v1',sequence=5,operation=ReproductionOperation.compare_output,input_refs=[bindings[5].object_binding_id,bindings[6].object_binding_id],expected_output_refs=[artifacts[2].artifact_id],deterministic_expected=True,stopping_condition='Preserve both resolution states and all supersession/qualification lineage.'),
        ReproductionStep(reproduction_step_id='reproduction-step:synthetic:06-export:v1',sequence=6,operation=ReproductionOperation.export_package,input_refs=[x.artifact_id for x in artifacts],expected_output_refs=[artifacts[0].artifact_id],deterministic_expected=True,stopping_condition='Package only after all required artifact hashes have been recorded.'),
    ]
    manifest=GraphInvestigationManifest(
        investigation_manifest_id='graph-investigation-manifest:synthetic:v1',package_policy_ref=policy.package_policy_id,question_refs=[questions[0].investigation_question_id],object_binding_refs=[x.object_binding_id for x in bindings],artifact_refs=[x.artifact_id for x in artifacts],environment_manifest_ref=env.environment_manifest_id,reproduction_step_refs=[x.reproduction_step_id for x in steps],
        upstream_snapshot_refs=[network.structure_snapshots[0].network_structure_snapshot_id,paths.snapshots[0].connection_path_evidence_snapshot_id,reasoning.snapshots[0].reasoning_snapshot_id,contradiction.snapshots[0].resolution_snapshot_id,upstream.snapshots[0].event_timeline_snapshot_id,documentary.snapshots[0].documentary_snapshot_id],
        as_of='2026-09-30T22:30:00Z',title='Synthetic entity-to-entity graph investigation package',purpose='Reproduce the governed analytical state, evidence paths, contradiction state, and entity timelines used in the synthetic investigation without promoting analytical outputs to graph facts.',
        limitations=['Synthetic reference data only.','Package reproduces represented analytical state as of the manifest timestamp, not later revisions.','Reproducibility does not establish truth, authenticity, legal admissibility, completeness, causality, coordination, intent, or wrongdoing.'],metadata={'synthetic_reference':True})
    artifact_hashes=[x.content_sha256 for x in artifacts]
    root_sha=_sha(manifest.fingerprint()+''.join(artifact_hashes))
    integrity=PackageIntegrityRecord(package_integrity_record_id='package-integrity:synthetic:v1',investigation_manifest_ref=manifest.investigation_manifest_id,manifest_sha256=manifest.fingerprint(),ordered_artifact_refs=[x.artifact_id for x in artifacts],ordered_artifact_sha256s=artifact_hashes,package_root_sha256=root_sha,verified_at='2026-09-30T22:31:00Z',disposition=VerificationDisposition.verified,verification_note='All synthetic package manifest and artifact fingerprints match the recorded content-addressed references; this verifies integrity only, not truth.')
    verification=PackageVerificationRecord(package_verification_record_id='package-verification:synthetic:v1',investigation_manifest_ref=manifest.investigation_manifest_id,verifier_ref='reviewer:synthetic:reproducibility:v1',reproduced_step_refs=[x.reproduction_step_id for x in steps],compared_object_binding_refs=[x.object_binding_id for x in bindings],disposition=VerificationDisposition.verified_with_qualifications,qualifications=['The alternative connection path remains a hypothesis.','The identity contradiction remains partially resolved.','The bounded relationship resolution remains a handoff rather than a graph edge.'],verified_at='2026-09-30T22:32:00Z')
    snapshot=ReproducibleGraphInvestigationSnapshot(graph_investigation_snapshot_id='graph-investigation-snapshot:synthetic:2026-09-30:v1',event_timeline_snapshot_ref=upstream.snapshots[0].event_timeline_snapshot_id,investigation_manifest_ref=manifest.investigation_manifest_id,integrity_record_refs=[integrity.package_integrity_record_id],verification_record_refs=[verification.package_verification_record_id],created_at='2026-09-30T22:33:00Z',metadata={'synthetic_reference':True})
    return ReproducibleGraphInvestigationPackageBundle(entity_centric_timeline_event_association_bundle=upstream,policies=[policy],questions=questions,object_bindings=bindings,artifacts=artifacts,environments=[env],reproduction_steps=steps,manifests=[manifest],integrity_records=[integrity],verification_records=[verification],snapshots=[snapshot])


def contract_document() -> dict[str, Any]:
    b=reference_reproducible_graph_investigation_package_bundle()
    return {
        'ok':True,'release':CORE_RELEASE,'contract':CONTRACT_VERSION,
        'extends_contracts':['sc.core.entity-centric-timeline-event-association.v1','sc.core.contradictory-identity-relationship-resolution.v1','sc.core.multi-hop-research-investigation-graph-reasoning.v1','sc.core.explainable-connection-paths-evidence-chains.v1','sc.core.network-structure-community-motif-intelligence.v1','sc.core.public-record-documentary-source-object-model.v1'],
        'object_types':['InvestigationPackagePolicy','InvestigationQuestion','InvestigationObjectBinding','InvestigationArtifactRecord','ReproductionEnvironmentManifest','ReproductionStep','GraphInvestigationManifest','PackageIntegrityRecord','PackageVerificationRecord','ReproducibleGraphInvestigationSnapshot','ReproducibleGraphInvestigationPackageBundle'],
        'principles':{
            'reproducibility_preserves_epistemic_state':True,'package_is_content_addressed':True,'contradictions_are_preserved':True,'source_provenance_is_preserved':True,'reproduction_plan_is_explicit':True,'later_revisions_may_supersede_package_state':True,'integrity_verification_is_distinct_from_truth_verification':True,'replay_is_non_mutating':True,
        },
        'boundaries':{
            'reproducibility_establishes_truth':False,'reproducibility_establishes_authenticity':False,'reproducibility_establishes_admissibility':False,'package_hash_establishes_content_truth':False,'replay_success_establishes_correctness':False,'byte_identical_replay_is_independent_corroboration':False,'package_freezes_future_truth_state':False,'identity_graph_mutation_performed':False,'relationship_graph_mutation_performed':False,'evidence_graph_mutation_performed':False,
        },
        'reference':{
            'questions':len(b.questions),'object_bindings':len(b.object_bindings),'artifacts':len(b.artifacts),'reproduction_steps':len(b.reproduction_steps),'manifests':len(b.manifests),'integrity_records':len(b.integrity_records),'verification_records':len(b.verification_records),'snapshots':len(b.snapshots),'package_root_sha256':b.integrity_records[0].package_root_sha256,'bundle_fingerprint_sha256':b.fingerprint(),
        },
        'database_migration':'none',
    }
