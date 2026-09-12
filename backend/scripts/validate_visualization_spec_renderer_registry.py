from __future__ import annotations

import tempfile
from pathlib import Path

from app.config import Settings
from app.database import Database
from app.migrations import migration_status, run_migrations
from app.services import visual_reasoning, visualization_registry

with tempfile.TemporaryDirectory() as td:
    db_path = Path(td) / 'core.db'
    settings = Settings(database_url=f'sqlite:///{db_path}', observability_request_metrics_enabled=False)
    database = Database(settings.database_url)
    run_migrations(database)
    status = migration_status(database)
    assert '0033' in status['applied'] and not status['pending']
    with database.session_factory() as db:
        ready = visualization_registry.readiness(db)
        assert ready['counts']['renderers'] == 4
        assert ready['renderer_registry'] is True
        assert ready['renderer_execution_by_core'] is False
        visual = visual_reasoning.create_object(
            db, name='v2.30 validation visual', slug='v230-validation-visual', description=None,
            entity_id=None, visibility='public', entity_status='active', visual_kind='system-map',
            reasoning_purpose='explain', semantic_state='draft', coordinate_space='abstract',
            project_entity_id=None, primary_subject_entity_id=None, lens={}, filters={}, assumptions=[],
            metadata={'validator':'v2.30.0'}, release='2.30.0',
        )
        spec = visualization_registry.create_specification(db, {
            'visual_entity_id': visual['id'], 'spec_key':'main', 'revision':1, 'spec_version':'1.0',
            'spec_kind':'diagram', 'title':'Validation specification', 'renderer_policy':'compatible',
            'encoding': {'nodes': {'label':'label'}}, 'interaction': {}, 'accessibility': {},
            'layout_constraints': {}, 'export': {}, 'metadata': {'validator':'v2.30.0'}, 'created_by':'validator',
        })
        assert len(spec['state_hash']) == 64
        resolved = visualization_registry.resolve_renderer(db, spec['id'], created_by='validator')
        assert resolved['resolved_renderer_key'] == 'contract.d3'
        assert resolved['execution_performed'] is False
        print({
            'version':'2.30.0', 'migration_0033_applied':True, 'renderer_registry':True,
            'renderer_contracts': ready['counts']['renderers'], 'resolved_renderer':resolved['resolved_renderer_key'],
            'renderer_execution_by_core':False, 'layout_execution_by_core':False,
        })
        print('PASS - Core 2.30.0 Visualization Specification & Renderer Registry validation')
