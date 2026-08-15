from __future__ import annotations
from pathlib import Path
import os, tempfile
from app.config import Settings
from app.database import Database
from app.migrations import migration_status, run_migrations
from app.services.cross_product_exchange import readiness

fd, path = tempfile.mkstemp(prefix='sc-core-v2140-', suffix='.db')
os.close(fd)
try:
    db=Database(f'sqlite:///{path}')
    run_migrations(db)
    status=migration_status(db)
    assert '0017' in status['applied'] and not status['pending'], status
    r=readiness()
    assert r['reference_first'] is True
    assert r['non_destructive'] is True
    assert r['automatic_truth_promotion'] is False
    assert r['automatic_cross_product_delivery'] is False
    assert {'site-intelligence','workspace','lab','knowledge-library','decision-studio'} <= set(r['products'])
    print('PASS - Core v2.14.0 cross-product evidence exchange validation')
finally:
    try: os.remove(path)
    except FileNotFoundError: pass
