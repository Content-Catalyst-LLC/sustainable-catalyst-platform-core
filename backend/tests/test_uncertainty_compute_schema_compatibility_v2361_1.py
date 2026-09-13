from sqlalchemy import inspect
from app.models import (SensitivityStudyRecord,SensitivityFactorRecord,SensitivityMeasureRecord,EnsembleRecord,EnsembleMemberRecord,EnsembleStatisticRecord,UncertaintyComputeRunRecord)

def test_v2360_schema_contract_is_preserved():
    assert 'id' in SensitivityStudyRecord.__table__.c and 'visual_entity_id' not in SensitivityStudyRecord.__table__.c
    assert 'study_id' in SensitivityFactorRecord.__table__.c and 'visual_entity_id' not in SensitivityFactorRecord.__table__.c
    assert SensitivityMeasureRecord.__tablename__ == 'sensitivity_measures'
    assert 'id' in EnsembleRecord.__table__.c and 'visual_entity_id' not in EnsembleRecord.__table__.c
    assert 'ensemble_id' in EnsembleMemberRecord.__table__.c
    assert 'ensemble_id' in EnsembleStatisticRecord.__table__.c
    assert next(iter(UncertaintyComputeRunRecord.__table__.c.sensitivity_study_id.foreign_keys)).target_fullname == 'sensitivity_studies.id'
    assert next(iter(UncertaintyComputeRunRecord.__table__.c.ensemble_id.foreign_keys)).target_fullname == 'ensembles.id'

def test_upgrade_database_contains_additive_compute_table(client):
    # The client fixture runs migrations on a current database. This asserts the repair is additive.
    r=client.get('/v1/uncertainty-compute/readiness')
    assert r.status_code == 200, r.text
    assert r.json()['migration_0040_applied'] is True
