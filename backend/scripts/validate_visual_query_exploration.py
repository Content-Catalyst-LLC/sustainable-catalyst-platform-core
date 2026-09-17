#!/usr/bin/env python3
from app.config import Settings
from app.database import Database
from app.migrations import run_migrations,migration_status
from app.services.visual_query_exploration import boundaries
s=Settings();db=Database(s.database_url);run_migrations(db);m=migration_status(db);assert '0069' in m['applied'] and m['pending']==[],m
b=boundaries()
for k in ('visual_exploration_session_registry_by_core','visual_query_target_registry_by_core','visual_query_request_registry_by_core','visual_query_predicate_registry_by_core','visual_traversal_request_registry_by_core','visual_query_result_evidence_binding_by_core','saved_visual_exploration_state_by_core','immutable_visual_query_snapshots_by_core'):assert b[k] is True,k
for k in ('query_execution_by_core','graph_traversal_by_core','data_retrieval_by_core','data_filtering_by_core','aggregation_execution_by_core','result_ranking_by_core','result_recommendation_by_core','automatic_query_execution','visual_inference_by_core'):assert b[k] is False,k
print('PASS - Platform Core v2.65.0 Visual Query & Exploration Engine invariants')
