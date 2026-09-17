from app.database import Database
from app.migrations import run_migrations,migration_status
from app.services.visual_decision_intelligence import CONTRACT,boundaries
import os
db=Database(os.environ["SC_CORE_DATABASE_URL"]);run_migrations(db);s=migration_status(db);b=boundaries();assert "0073" in s["applied"] and not s["pending"];assert CONTRACT=="sc.visual-runtime.decision-intelligence.v1";assert b["visual_decision_workspace_registry_by_core"] and b["option_ranking_by_core"] is False and b["decision_execution_by_core"] is False
print("PASS - Platform Core v2.69.0 Visual Decision Intelligence invariants")
