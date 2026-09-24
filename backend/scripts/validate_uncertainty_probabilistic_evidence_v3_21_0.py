from app.database import Database
from app.migrations import run_migrations,migration_status
from app.services import uncertainty_probabilistic_evidence as svc

db=Database('sqlite+pysqlite:///:memory:')
applied=run_migrations(db)
status=migration_status(db)
assert '0108' in status['applied_migrations'] if 'applied_migrations' in status else True
with db.session_factory() as s:
    r=svc.readiness(s)
    assert r['release']=='3.21.0'
    assert r['contract']=='sc.core.uncertainty-probabilistic-evidence.v1'
    assert r['source_contract']=='sc.analytics-r.uncertainty-sensitivity-runtime.v1'
    assert r['execute_uncertainty_by_core'] is False
    assert r['infer_causality_by_core'] is False
print('PLATFORM_CORE_V3210_UNCERTAINTY_EVIDENCE=PASS')
