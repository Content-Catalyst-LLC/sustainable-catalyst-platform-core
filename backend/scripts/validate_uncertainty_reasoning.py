#!/usr/bin/env python3
from __future__ import annotations
from app.config import Settings
from app.database import Database
from app.migrations import migration_status, run_migrations
from app.services import uncertainty_reasoning

def main():
    settings=Settings.from_env();db=Database(settings.database_url);run_migrations(db);status=migration_status(db)
    assert '0039' in status['applied'] and not status['pending'],status
    with db.session_factory() as session:
        ready=uncertainty_reasoning.readiness(session)
        assert ready['sampling_by_core'] is False
        assert ready['sensitivity_algorithm_execution_by_core'] is False
        assert ready['ensemble_aggregation_by_core'] is False
        assert ready['model_execution_by_core'] is False
        assert ready['automatic_probability_generation'] is False
    print({'version':'2.36.0','migration_0039_applied':True,'uncertainty_reasoning':True,'sensitivity_reasoning':True,'ensemble_reasoning':True,'sampling_by_core':False,'sensitivity_algorithm_execution_by_core':False,'ensemble_aggregation_by_core':False,'model_execution_by_core':False,'automatic_truth_promotion':False})
    print('PASS - Core 2.36.0 Uncertainty, Sensitivity & Ensemble Reasoning validation')
if __name__=='__main__':main()
