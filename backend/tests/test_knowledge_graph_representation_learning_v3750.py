import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.routers import knowledge_graph_representation_learning
from app.services.knowledge_graph_representation_learning import *


def ref(): return reference_knowledge_graph_representation_learning_bundle()

def test_release(): assert CORE_RELEASE == "3.75.0"
def test_contract(): assert CONTRACT_VERSION == "sc.core.knowledge-graph-representation-learning.v1"
def test_reference_validates(): KnowledgeGraphRepresentationLearningBundle.model_validate(ref().model_dump(mode="json"))
def test_fingerprint_deterministic(): assert ref().fingerprint() == ref().fingerprint()
def test_task_is_representation_learning(): assert ref().tasks[0].graph_ml_task_kind.value == "representation-learning"
def test_task_has_entities_and_relations(): assert len(ref().tasks[0].entity_refs)==3 and len(ref().tasks[0].relationship_types)==2
def test_task_model_resolves(): assert ref().tasks[0].model_ref == ref().graph_anomaly_detection_bundle.graph_link_prediction_bundle.graph_classification_bundle.graph_embedding_bundle.graph_ml_foundation_bundle.model_foundations[0].foundation_id
def test_runtime_core_does_not_execute(): assert ref().runtime_contracts[0].core_executes_kg_representation_learning is False
def test_runtime_cannot_mutate_graph(): assert ref().runtime_contracts[0].runtime_may_mutate_evidence_graph is False
def test_runtime_cannot_promote_score(): assert ref().runtime_contracts[0].runtime_may_promote_scored_triple is False
def test_negative_sample_not_false_fact(): assert ref().negative_sampling_policies[0].absent_edge_is_not_false_fact is True
def test_negative_sample_training_artifact(): assert ref().negative_sampling_policies[0].negative_samples_are_training_artifacts is True
def test_negative_samples_cannot_be_evidence(): assert ref().negative_sampling_policies[0].negative_samples_may_not_be_written_as_evidence is True
def test_filtered_negative_sampling_known_edges(): assert ref().negative_sampling_policies[0].filtered_against_known_evidence_edges is True
def test_space_snapshot_specific(): assert ref().representation_spaces[0].representation_space_is_model_and_snapshot_specific is True
def test_space_similarity_not_graph_fact(): assert ref().representation_spaces[0].representation_similarity_is_not_graph_fact is True
def test_vector_count(): assert len(ref().vectors)==5
def test_entity_vector_count(): assert len([v for v in ref().vectors if v.target_kind==KGRepresentationTargetKind.entity])==3
def test_relation_vector_count(): assert len([v for v in ref().vectors if v.target_kind==KGRepresentationTargetKind.relation])==2
def test_vector_is_not_fact_or_evidence():
    v=ref().vectors[0]; assert v.is_graph_fact is False and v.is_evidence is False and v.representation_does_not_establish_identity_or_relationship is True
def test_vector_dimension_mismatch_rejected():
    d=ref().vectors[0].model_dump(); d['dimensions']=5
    with pytest.raises(ValidationError): KGRepresentationVector.model_validate(d)
def test_vector_nonfinite_rejected():
    d=ref().vectors[0].model_dump(); d['vector'][0]=float('inf')
    with pytest.raises(ValidationError): KGRepresentationVector.model_validate(d)
def test_training_does_not_create_facts(): assert ref().training_provenance[0].training_does_not_create_graph_facts is True
def test_training_has_negative_sampling_lineage(): assert ref().training_provenance[0].negative_sampling_policy_ref == ref().negative_sampling_policies[0].negative_sampling_policy_id
def test_triple_score_count(): assert len(ref().triple_scores)==2
def test_known_edge_score_is_non_evidentiary():
    s=ref().triple_scores[0]; assert s.known_evidence_edge_ref and s.is_graph_fact is False and s.is_evidence is False
def test_candidate_score_is_non_evidentiary():
    s=ref().triple_scores[1]; assert s.candidate_relationship_ref and s.is_graph_fact is False and s.is_evidence is False
def test_score_requires_separate_validation(): assert all(x.separate_validation_required_for_candidate_or_evidence_use for x in ref().triple_scores)
def test_score_not_evidence_strength(): assert all(x.score_is_not_evidence_strength for x in ref().triple_scores)
def test_self_triple_rejected():
    d=ref().triple_scores[0].model_dump(); d['object_node_ref']=d['subject_node_ref']
    with pytest.raises(ValidationError): KGTripleScoreRecord.model_validate(d)
def test_missing_entity_vector_ref_rejected():
    b=ref().model_copy(deep=True); b.triple_scores[0].source_entity_vector_refs[0]='kg-vector:missing'
    with pytest.raises(ValidationError): KnowledgeGraphRepresentationLearningBundle.model_validate(b.model_dump(mode='json'))
def test_relation_vector_target_must_match():
    b=ref().model_copy(deep=True); b.triple_scores[0].relation_vector_ref=b.vectors[-1].kg_vector_id
    with pytest.raises(ValidationError): KnowledgeGraphRepresentationLearningBundle.model_validate(b.model_dump(mode='json'))
def test_task_entity_must_resolve():
    b=ref().model_copy(deep=True); b.tasks[0].entity_refs[0]='node:missing'
    with pytest.raises(ValidationError): KnowledgeGraphRepresentationLearningBundle.model_validate(b.model_dump(mode='json'))
def test_positive_edge_must_resolve():
    b=ref().model_copy(deep=True); b.negative_sampling_policies[0].positive_evidence_edge_refs=['edge:missing']
    with pytest.raises(ValidationError): KnowledgeGraphRepresentationLearningBundle.model_validate(b.model_dump(mode='json'))
def test_filtered_eval_requires_filter_ref():
    d=ref().evaluations[0].model_dump(); d['known_positive_filter_ref']=None
    with pytest.raises(ValidationError): KGRankingEvaluationRecord.model_validate(d)
def test_evaluation_is_descriptive():
    e=ref().evaluations[0]; assert e.evaluation_metrics_are_descriptive_not_evidence and e.ranking_performance_does_not_establish_graph_truth
def test_public_route():
    a=FastAPI(); a.include_router(knowledge_graph_representation_learning.public_router)
    with TestClient(a) as c: z=c.get('/public/v1/kg-representation/contract')
    assert z.status_code==200 and z.json()['release']=='3.75.0'
@pytest.mark.parametrize('key',["knowledge_graph_representation_is_derived_model_output","entity_embedding_is_not_entity_identity","relation_embedding_is_not_relationship_fact","triple_score_is_not_graph_fact","triple_score_is_not_evidence","triple_score_is_not_evidence_strength","high_triple_score_does_not_establish_relationship","negative_sample_is_not_false_fact","absent_edge_is_not_negative_evidence","ranking_metric_is_not_truth_measure","candidate_relationship_remains_non_evidentiary","gnn_prediction_is_not_graph_fact"])
def test_principles(key): assert contract_document()['principles'][key] is True
@pytest.mark.parametrize('key',["core_trains_kg_representation_model","core_executes_kg_triple_scoring","core_generates_negative_samples","core_mutates_evidence_graph_from_kg_score","core_promotes_scored_triple_to_evidence_edge","core_interprets_low_score_as_falsehood","runtime_may_mutate_evidence_graph","runtime_may_promote_scored_triple","v375_validates_candidate_relationship"])
def test_boundaries(key): assert contract_document()['boundaries'][key] is False
def test_extends_v374(): assert 'sc.core.graph-anomaly-detection.v1' in contract_document()['extends_contracts']
def test_prepares_v376(): assert contract_document()['roadmap_integration']['prepares_v3760_evidence_graph_neural_analysis_validation_workflow'] is True
def test_schema_generation_possible(): assert KnowledgeGraphRepresentationLearningBundle.model_json_schema()['title']=='KnowledgeGraphRepresentationLearningBundle'
