from sqlalchemy import inspect
from app.migrations import migration_status

def test_v2370_additive_schema_preserves_v236_contracts(client):
    insp=inspect(client.app.state.database.engine)
    tables=set(insp.get_table_names())
    assert {'sensitivity_studies','sensitivity_factors','sensitivity_measures','ensembles','uncertainty_compute_runs'} <= tables
    def cols(t): return {c['name'] for c in insp.get_columns(t)}
    assert {'id','study_key','project_entity_id'} <= cols('sensitivity_studies')
    assert 'visual_entity_id' not in cols('sensitivity_studies')
    assert {'id','study_id','parameter_entity_id'} <= cols('sensitivity_factors')
    assert {'id','study_id','factor_id'} <= cols('sensitivity_measures')
    assert {'id','ensemble_key'} <= cols('ensembles')
    assert {'id','sensitivity_study_id','ensemble_id'} <= cols('uncertainty_compute_runs')
    assert {'causal_graphs','causal_variables','causal_edges','causal_interventions','causal_identifications','causal_estimates','causal_diagnostics'} <= tables
    status=migration_status(client.app.state.database)
    assert status['pending']==[] and status['applied'][-1]=='0056'
