#!/usr/bin/env python3
from sqlalchemy import inspect
from app.config import Settings
from app.database import Database
from app.main import app
from app.routers.investigation_workspace import capabilities
EXPECTED={
    "investigation_workspaces","investigation_workspace_objects","investigation_workspace_relations",
    "investigation_workspace_views","investigation_workspace_snapshots","investigation_workspace_handoffs",
}
settings=Settings()
db=Database(settings.database_url)
found=set(inspect(db.engine).get_table_names())
missing=EXPECTED-found
assert not missing, f"missing tables: {sorted(missing)}"
routes={getattr(x,"path",None) for x in app.routes}
assert "/api/v1/investigation-workspace/capabilities" in routes, "investigation capabilities route not registered"
payload=capabilities()
assert payload.get("version")=="3.20.0", payload
assert payload.get("capability")=="Unified Investigation Workspace", payload
reported=getattr(settings,"version",getattr(settings,"app_version",None))
assert reported=="3.20.0.1", f"backend release identity is {reported!r}"
print("Platform Core v3.20.0.1 runtime validation: PASS")
