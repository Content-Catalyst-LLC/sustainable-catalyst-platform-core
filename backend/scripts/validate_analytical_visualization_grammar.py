#!/usr/bin/env python3
from app.database import Database
from app.config import Settings
from app.migrations import run_migrations,migration_status
from app.services.visual_grammar import boundaries
s=Settings();db=Database(s.database_url);run_migrations(db);m=migration_status(db);assert '0067' in m['applied'] and m['pending']==[],m
b=boundaries();assert b['grammar_specification_registry_by_core'] and b['immutable_grammar_snapshots_by_core'];assert not b['transform_execution_by_core'] and not b['mark_drawing_by_core'] and not b['automatic_chart_generation_by_core']
print('PASS - Platform Core v2.63.0 Analytical Visualization Grammar invariants')
