#!/usr/bin/env python3
from sqlalchemy import inspect
from app.config import Settings
from app.database import Database
from app.models import (
    InvestigationWorkspace, InvestigationWorkspaceObject, InvestigationWorkspaceRelation,
    InvestigationWorkspaceView, InvestigationWorkspaceSnapshot, InvestigationWorkspaceHandoff,
)
EXPECTED={
    "investigation_workspaces","investigation_workspace_objects","investigation_workspace_relations",
    "investigation_workspace_views","investigation_workspace_snapshots","investigation_workspace_handoffs",
}
db=Database(Settings().database_url)
tables=[
    InvestigationWorkspace.__table__, InvestigationWorkspaceObject.__table__, InvestigationWorkspaceRelation.__table__,
    InvestigationWorkspaceView.__table__, InvestigationWorkspaceSnapshot.__table__, InvestigationWorkspaceHandoff.__table__,
]
# SQLAlchemy CREATE TABLE ... checkfirst is additive/idempotent and does not alter existing tables.
for table in tables:
    table.create(bind=db.engine, checkfirst=True)
found=set(inspect(db.engine).get_table_names())
missing=EXPECTED-found
assert not missing, f"schema repair failed; missing tables: {sorted(missing)}"
print("Platform Core v3.20.0.1 investigation schema repair: PASS")
