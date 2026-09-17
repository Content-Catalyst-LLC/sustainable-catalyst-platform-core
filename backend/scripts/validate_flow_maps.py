#!/usr/bin/env python3
from __future__ import annotations
import os,tempfile
from pathlib import Path
from app.config import Settings
from app.database import Database
from app.migrations import run_migrations,migration_status
from app.services import flow_maps,visual_reasoning,visualization_registry

fd,path=tempfile.mkstemp(prefix='sc-v232-',suffix='.db'); os.close(fd)
try:
    db=Database('sqlite:///'+path); run_migrations(db); status=migration_status(db)
    assert '0035' in status['applied'] and not status['pending'],status
    with db.session_factory() as session:
        ready=flow_maps.readiness(session)
        assert ready['flow_relations_reused'] is True
        assert ready['unit_conversion_by_core'] is False
        assert ready['simulation_by_core'] is False
        fm=flow_maps.create_map(session,{'name':'Validator flow map','slug':'validator-flow-map-v232','visibility':'public','quantity_mode':'quantitative','default_unit':'MWh'},release='2.34.0'); mid=fm['visual_entity_id']
        a=visual_reasoning.add_element(session,mid,{'element_key':'source','element_kind':'node','semantic_role':'input','label':'Source'})
        b=visual_reasoning.add_element(session,mid,{'element_key':'sink','element_kind':'node','semantic_role':'output','label':'Sink'})
        ch=flow_maps.add_channel(session,mid,{'channel_key':'energy','name':'Energy','flow_kind':'energy','unit':'MWh'})
        f=flow_maps.add_flow(session,mid,{'flow_key':'energy-flow','source_element_id':a['id'],'target_element_id':b['id'],'channel_id':ch['id'],'quantity_kind':'amount','quantity_value':5,'unit':'MWh'})
        assert f['source_element_id']==a['id']
        bal=flow_maps.balance_summary(session,mid); assert bal['flows_included']==1 and bal['unit_conversion_performed'] is False and bal['conservation_claim'] is False
        spec=flow_maps.compile_specification(session,mid,{'spec_key':'validator','spec_kind':'network','created_by':'validator'})
        resolution=visualization_registry.resolve_renderer(session,spec['id'],created_by='validator')
        assert resolution['resolved_renderer_key']=='contract.d3' and resolution['execution_performed'] is False
    print({'version':'2.34.0','migration_0035_applied':True,'flow_maps':True,'relation_bound_flows':True,'unit_conversion_by_core':False,'simulation_by_core':False})
    print('PASS - Core 2.34.0 Flow Maps validation')
finally:
    Path(path).unlink(missing_ok=True)
