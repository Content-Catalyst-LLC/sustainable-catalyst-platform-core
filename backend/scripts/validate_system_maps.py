#!/usr/bin/env python3
from __future__ import annotations
import os, tempfile
from pathlib import Path
from app.config import Settings
from app.database import Database
from app.migrations import run_migrations, migration_status
from app.services import system_maps

fd,path=tempfile.mkstemp(prefix="sc-v231-",suffix=".db"); os.close(fd)
try:
    db=Database("sqlite:///"+path); run_migrations(db); status=migration_status(db)
    assert "0034" in status["applied"] and not status["pending"], status
    with db.session_factory() as session:
        ready=system_maps.readiness(session)
        assert ready["renderer_neutral"] is True
        assert ready["layout_engine_in_core"] is False
        assert ready["causal_inference_by_core"] is False
    print({"version":"2.32.0","migration_0034_applied":True,"system_maps":True,"renderer_neutral":True,"layout_engine_in_core":False,"causal_inference_by_core":False})
    print("PASS - Core 2.32.0 System Maps validation")
finally:
    Path(path).unlink(missing_ok=True)
