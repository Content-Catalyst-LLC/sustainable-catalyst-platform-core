#!/usr/bin/env python3
import tempfile
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from app.database import Database
from app.migrations import run_migrations,migration_status
from app.services import analytical_runtime_provider as svc
with tempfile.TemporaryDirectory() as d:
    db=Database("sqlite:///"+str(Path(d)/"validate.db")); run_migrations(db)
    with db.session_factory() as s:
        st=migration_status(db); r=svc.readiness(s); p=svc.provider_bundle(s,"catalystanalyticsr",True)
        assert "0103" in st["applied"] and st["pending"]==[],st
        assert r["release"]=="3.3.0" and r["catalyst_analytics_r_version"]=="2.2.0",r
        assert p["provider"]["runtime"]=="r" and p["execution_host"]=="workspace",p
        assert len(p["capabilities"])>=12,p
        req=svc.create_request(s,{"request_key":"validator","provider_ref":"catalystanalyticsr","analysis_type":"forecasting","input_refs":["dataset:test"]})
        assert req["runtime"]=="r" and req["execution_host"]=="workspace"
        assert r["execute_r_by_core"] is False and r["execute_analysis_by_core"] is False
print("PASS - Platform Core v3.1-compatible Analytical Runtime Provider Contract on Core v3.3.0")
