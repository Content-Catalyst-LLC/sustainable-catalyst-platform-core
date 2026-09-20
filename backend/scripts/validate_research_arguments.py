#!/usr/bin/env python3
import os
from pathlib import Path

from sqlalchemy import inspect

from app.config import Settings
from app.main import create_app
from app.migrations import migration_status

path = Path(os.getenv("SC_CORE_V2790_VALIDATOR_DB", "/tmp/sc-core-v2790-validator.db"))
if path.exists():
    path.unlink()
app = create_app(Settings(database_url="sqlite:///" + str(path)))
db = app.state.database
expected = {
    "research_arguments_v279",
    "research_argument_nodes_v279",
    "research_argument_edges_v279",
    "research_evidentiary_syntheses_v279",
    "research_synthesis_components_v279",
    "research_counterarguments_v279",
    "research_argument_tensions_v279",
    "research_argument_revisions_v279",
    "research_argument_snapshots_v279",
}
assert expected.issubset(set(inspect(db.engine).get_table_names()))
status = migration_status(db)
assert "0083" in status["applied"] and status["pending"] == [], status
print("PASS - Platform Core v2.79.0 Research Argument & Evidentiary Synthesis Engine invariants")
