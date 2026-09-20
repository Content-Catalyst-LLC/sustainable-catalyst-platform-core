#!/usr/bin/env python3
import os
from pathlib import Path

from sqlalchemy import inspect

from app.config import Settings
from app.main import create_app
from app.migrations import migration_status

path = Path(os.getenv("SC_CORE_V2780_VALIDATOR_DB", "/tmp/sc-core-v2780-validator.db"))
if path.exists():
    path.unlink()
app = create_app(Settings(database_url="sqlite:///" + str(path)))
db = app.state.database
expected = {
    "research_hypothesis_sets_v278",
    "research_hypotheses_v278",
    "research_hypothesis_revisions_v278",
    "research_hypothesis_evidence_assessments_v278",
    "research_hypothesis_predictions_v278",
    "research_hypothesis_assumptions_v278",
    "research_hypothesis_relations_v278",
    "research_hypothesis_discrimination_gaps_v278",
    "research_hypothesis_snapshots_v278",
}
assert expected.issubset(set(inspect(db.engine).get_table_names()))
status = migration_status(db)
assert "0082" in status["applied"] and status["pending"] == [], status
print("PASS - Platform Core v2.78.0 Hypothesis & Competing Explanation Engine invariants")
