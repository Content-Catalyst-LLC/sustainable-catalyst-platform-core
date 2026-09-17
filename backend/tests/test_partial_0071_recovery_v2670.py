import sqlite3
from app.database import Database
from app.migrations import run_migrations,migration_status
from sqlalchemy import inspect
TABLES={'visual_predictive_workspaces','visual_forecast_overlays','visual_uncertainty_displays','visual_calibration_displays','visual_ensemble_comparison_overlays','visual_monitoring_overlays','visual_spatial_temporal_forecast_layers','visual_causal_predictive_overlays','visual_decision_prediction_bindings','visual_predictive_snapshots'}
def tables(db):return set(inspect(db.engine).get_table_names())
def test_pristine_0071(tmp_path):
 db=Database(f"sqlite:///{tmp_path/'p.db'}");assert '0071' in run_migrations(db);assert TABLES.issubset(tables(db));assert migration_status(db)['pending']==[]
def test_partial_0071(tmp_path):
 p=tmp_path/'q.db';db=Database(f'sqlite:///{p}');run_migrations(db);con=sqlite3.connect(p);con.execute("delete from schema_migrations where version='0071'");con.commit();con.close();assert run_migrations(db)==['0071'];assert migration_status(db)['pending']==[]
