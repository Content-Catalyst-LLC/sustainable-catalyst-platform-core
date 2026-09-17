#!/usr/bin/env python3
from app.database import Database
from app.config import Settings
from app.migrations import run_migrations,migration_status
from app.services.visual_composition import boundaries
s=Settings(); db=Database(s.database_url); run_migrations(db); m=migration_status(db); assert '0066' in m['applied'] and m['pending']==[],m
b=boundaries(); assert b['view_composition_registry_by_core'] and b['renderer_capability_resolution_by_core']; assert not b['svg_canvas_webgl_drawing_by_core'] and not b['automatic_renderer_execution']
print('PASS - Platform Core v2.62.0 Interactive Renderer & View Composition invariants')
