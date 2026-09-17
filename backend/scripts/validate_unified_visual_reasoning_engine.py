from app.database import Database
from app.migrations import run_migrations,migration_status
from app.services.unified_visual_reasoning import CONTRACT,boundaries
import os
db=Database(os.environ["SC_CORE_DATABASE_URL"]);run_migrations(db);s=migration_status(db);b=boundaries();assert "0074" in s["applied"] and not s["pending"];assert CONTRACT=="sc.visual-runtime.unified-reasoning.v1";assert b["unified_visual_reasoning_workspace_registry_by_core"] and b["render_by_core"] is False and b["decision_ranking_by_core"] is False
print("PASS - Platform Core v2.70.0 Unified Visual Reasoning Engine invariants")
