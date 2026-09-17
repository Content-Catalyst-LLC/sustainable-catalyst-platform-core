#!/usr/bin/env python3
from app.database import Database
from app.migrations import run_migrations,migration_status
from sqlalchemy import inspect
import tempfile, pathlib
TABLES={'visual_runtime_scenes','visual_runtime_layers','visual_runtime_nodes','visual_runtime_edges','visual_runtime_annotations','visual_runtime_views','visual_runtime_bindings','visual_runtime_snapshots'}
with tempfile.TemporaryDirectory() as td:
    db=Database(f"sqlite:///{pathlib.Path(td)/'validate.db'}")
    run_migrations(db)
    names=set(inspect(db.engine).get_table_names())
    assert TABLES.issubset(names)
    status=migration_status(db)
    assert status['pending']==[] and status['applied'][-1]=='0065'
print('PASS - Platform Core v2.61.0 visual reasoning runtime and scene graph invariants')
