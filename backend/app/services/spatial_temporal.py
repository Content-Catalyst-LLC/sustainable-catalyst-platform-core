from __future__ import annotations
from datetime import datetime, timezone
from typing import Any
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from ..models import (
    Entity, CausalGraphRecord, SpatialTemporalSceneRecord, SpatialFeatureRecord,
    TemporalEventRecord, TrajectoryRecord, TrajectoryPointRecord,
    SpatialTemporalChangeRecord, SpatialTemporalViewRecord,
)

GEOMETRY_TYPES={'Point','MultiPoint','LineString','MultiLineString','Polygon','MultiPolygon','GeometryCollection'}
VIEW_KINDS={'map','timeline','time-slider','linked-map-timeline','trajectory','change-detection','custom'}
TARGET_PRODUCTS={'site-intelligence','lab','workbench','external'}

def _dt(value: Any, *, required=False):
    if value in (None,''):
        if required: raise ValueError('A timestamp is required.')
        return None
    if isinstance(value, datetime): return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    text=str(value).strip().replace('Z','+00:00')
    try: out=datetime.fromisoformat(text)
    except ValueError as exc: raise ValueError(f'Invalid ISO-8601 timestamp: {value}') from exc
    return out if out.tzinfo else out.replace(tzinfo=timezone.utc)

def _ordered(start,end,label='temporal interval'):
    if start is not None and end is not None and start>end: raise ValueError(f'{label} start must be <= end.')

def _geometry(value:Any, *, point_only=False):
    if not isinstance(value,dict): raise ValueError('geometry must be a GeoJSON object.')
    typ=str(value.get('type') or '')
    if typ not in GEOMETRY_TYPES: raise ValueError('Unsupported GeoJSON geometry type.')
    if point_only and typ!='Point': raise ValueError('Trajectory points require GeoJSON Point geometry.')
    if typ=='GeometryCollection':
        if not isinstance(value.get('geometries'),list): raise ValueError('GeometryCollection requires geometries[].')
    elif 'coordinates' not in value: raise ValueError('GeoJSON geometry requires coordinates.')
    return typ,dict(value)

def _ser(row):
    out={}
    for c in row.__table__.columns:
        v=getattr(row,c.name)
        if isinstance(v,datetime): v=v.isoformat()
        out[c.name]=v
    return out

def _scene(db:Session,scene_id:str):
    row=db.get(SpatialTemporalSceneRecord,scene_id)
    if row is None: raise HTTPException(status_code=404,detail='Spatial-temporal scene not found.')
    return row

def _feature(db:Session,scene_id:str,feature_id:str):
    row=db.get(SpatialFeatureRecord,feature_id)
    if row is None or row.scene_id!=scene_id: raise ValueError('feature_id must belong to this scene.')
    return row

def readiness(db:Session):
    counts={
      'scenes':len(db.scalars(select(SpatialTemporalSceneRecord.id)).all()),
      'features':len(db.scalars(select(SpatialFeatureRecord.id)).all()),
      'events':len(db.scalars(select(TemporalEventRecord.id)).all()),
      'trajectories':len(db.scalars(select(TrajectoryRecord.id)).all()),
      'trajectory_points':len(db.scalars(select(TrajectoryPointRecord.id)).all()),
      'changes':len(db.scalars(select(SpatialTemporalChangeRecord.id)).all()),
      'views':len(db.scalars(select(SpatialTemporalViewRecord.id)).all()),
    }
    return {'migration_0042_applied':True,'spatial_temporal_scenes':True,'geojson_semantics':True,'temporal_interval_validation':True,'trajectory_reasoning':True,'change_observation_provenance':True,'map_timeline_specifications':True,'renderer_neutral':True,'crs_reprojection_by_core':False,'spatial_analysis_by_core':False,'raster_processing_by_core':False,'remote_sensing_by_core':False,'temporal_model_execution_by_core':False,'automatic_truth_promotion':False,'counts':counts}

def create_scene(db:Session,p:dict[str,Any]):
    project=str(p.get('project_entity_id') or '')
    if not project or db.get(Entity,project) is None: raise ValueError('project_entity_id must identify an existing entity.')
    causal=p.get('causal_graph_id')
    if causal and db.get(CausalGraphRecord,str(causal)) is None: raise ValueError('causal_graph_id does not exist.')
    start=_dt(p.get('temporal_start')); end=_dt(p.get('temporal_end')); _ordered(start,end,'scene')
    sr=dict(p.get('spatial_reference') or {'crs':'EPSG:4326','srid':4326})
    tr=dict(p.get('temporal_reference') or {'timezone':'UTC','calendar':'gregorian'})
    row=SpatialTemporalSceneRecord(scene_key=str(p.get('scene_key') or '').strip(),name=str(p.get('name') or '').strip(),description=p.get('description'),visibility=str(p.get('visibility') or 'private'),project_entity_id=project,model_entity_id=p.get('model_entity_id'),model_version_entity_id=p.get('model_version_entity_id'),causal_graph_id=causal,visual_entity_id=p.get('visual_entity_id'),scene_state=str(p.get('scene_state') or 'draft'),spatial_reference_json=sr,temporal_reference_json=tr,spatial_extent_json=dict(p.get('spatial_extent') or {}),temporal_start=start,temporal_end=end,provenance_json=dict(p.get('provenance') or {}),metadata_json=dict(p.get('metadata') or {}),created_by=str(p.get('created_by') or 'operator'))
    if not row.scene_key or not row.name: raise ValueError('scene_key and name are required.')
    db.add(row)
    try: db.commit(); db.refresh(row)
    except IntegrityError as exc: db.rollback(); raise HTTPException(status_code=409,detail='Scene key already exists in this project.') from exc
    return _ser(row)

def list_scenes(db:Session,*,project_entity_id=None,visibility=None,public_only=False):
    q=select(SpatialTemporalSceneRecord)
    if project_entity_id:q=q.where(SpatialTemporalSceneRecord.project_entity_id==project_entity_id)
    if public_only:q=q.where(SpatialTemporalSceneRecord.visibility=='public')
    elif visibility:q=q.where(SpatialTemporalSceneRecord.visibility==visibility)
    return [_ser(x) for x in db.scalars(q.order_by(SpatialTemporalSceneRecord.created_at.desc())).all()]

def read_scene(db:Session,scene_id:str,*,public_only=False):
    row=_scene(db,scene_id)
    if public_only and row.visibility!='public': raise HTTPException(status_code=404,detail='Spatial-temporal scene not found.')
    return _ser(row)

def add_feature(db:Session,scene_id:str,p:dict[str,Any]):
    _scene(db,scene_id); typ,geom=_geometry(p.get('geometry'))
    start=_dt(p.get('temporal_start')); end=_dt(p.get('temporal_end')); _ordered(start,end,'feature')
    row=SpatialFeatureRecord(scene_id=scene_id,feature_key=str(p.get('feature_key') or '').strip(),label=str(p.get('label') or '').strip(),feature_kind=str(p.get('feature_kind') or 'feature'),geometry_type=typ,geometry_json=geom,srid=int(p.get('srid') or 4326),crs=str(p.get('crs') or f"EPSG:{int(p.get('srid') or 4326)}"),spatial_role=str(p.get('spatial_role') or 'context'),bound_entity_id=p.get('bound_entity_id'),visual_element_id=p.get('visual_element_id'),temporal_start=start,temporal_end=end,properties_json=dict(p.get('properties') or {}),uncertainty_json=dict(p.get('uncertainty') or {}),provenance_json=dict(p.get('provenance') or {}),metadata_json=dict(p.get('metadata') or {}))
    if not row.feature_key or not row.label: raise ValueError('feature_key and label are required.')
    db.add(row)
    try: db.commit();db.refresh(row)
    except IntegrityError as exc: db.rollback(); raise HTTPException(status_code=409,detail='Feature key already exists in this scene.') from exc
    return _ser(row)

def add_event(db:Session,scene_id:str,p:dict[str,Any]):
    _scene(db,scene_id); start=_dt(p.get('starts_at'),required=True); end=_dt(p.get('ends_at')); _ordered(start,end,'event')
    fid=p.get('feature_id')
    if fid:_feature(db,scene_id,str(fid))
    row=TemporalEventRecord(scene_id=scene_id,event_key=str(p.get('event_key') or '').strip(),label=str(p.get('label') or '').strip(),event_kind=str(p.get('event_kind') or 'event'),starts_at=start,ends_at=end,temporal_precision=str(p.get('temporal_precision') or ('interval' if end else 'instant')),timezone_name=str(p.get('timezone') or 'UTC'),bound_entity_id=p.get('bound_entity_id'),feature_id=fid,uncertainty_json=dict(p.get('uncertainty') or {}),provenance_json=dict(p.get('provenance') or {}),metadata_json=dict(p.get('metadata') or {}))
    if not row.event_key or not row.label: raise ValueError('event_key and label are required.')
    db.add(row)
    try:db.commit();db.refresh(row)
    except IntegrityError as exc:db.rollback();raise HTTPException(status_code=409,detail='Event key already exists in this scene.') from exc
    return _ser(row)

def add_trajectory(db:Session,scene_id:str,p:dict[str,Any]):
    _scene(db,scene_id); fid=p.get('feature_id')
    if fid:_feature(db,scene_id,str(fid))
    row=TrajectoryRecord(scene_id=scene_id,trajectory_key=str(p.get('trajectory_key') or '').strip(),label=str(p.get('label') or '').strip(),subject_entity_id=p.get('subject_entity_id'),feature_id=fid,interpolation=str(p.get('interpolation') or 'linear'),unit=p.get('unit'),provenance_json=dict(p.get('provenance') or {}),metadata_json=dict(p.get('metadata') or {}))
    if not row.trajectory_key or not row.label:raise ValueError('trajectory_key and label are required.')
    db.add(row)
    try:db.commit();db.refresh(row)
    except IntegrityError as exc:db.rollback();raise HTTPException(status_code=409,detail='Trajectory key already exists in this scene.') from exc
    return _ser(row)

def add_trajectory_point(db:Session,trajectory_id:str,p:dict[str,Any]):
    traj=db.get(TrajectoryRecord,trajectory_id)
    if traj is None:raise HTTPException(status_code=404,detail='Trajectory not found.')
    _,geom=_geometry(p.get('geometry'),point_only=True)
    pos=int(p.get('sequence_position')); observed=_dt(p.get('observed_at'),required=True)
    row=TrajectoryPointRecord(trajectory_id=trajectory_id,sequence_position=pos,observed_at=observed,geometry_json=geom,srid=int(p.get('srid') or 4326),value_json=p.get('value'),uncertainty_json=dict(p.get('uncertainty') or {}),provenance_json=dict(p.get('provenance') or {}),metadata_json=dict(p.get('metadata') or {}))
    db.add(row)
    try:db.commit();db.refresh(row)
    except IntegrityError as exc:db.rollback();raise HTTPException(status_code=409,detail='Trajectory sequence_position already exists.') from exc
    return _ser(row)

def trajectory_summary(db:Session,trajectory_id:str):
    traj=db.get(TrajectoryRecord,trajectory_id)
    if traj is None:raise HTTPException(status_code=404,detail='Trajectory not found.')
    pts=db.scalars(select(TrajectoryPointRecord).where(TrajectoryPointRecord.trajectory_id==trajectory_id).order_by(TrajectoryPointRecord.sequence_position)).all()
    ordered_time=all(pts[i].observed_at<=pts[i+1].observed_at for i in range(len(pts)-1))
    return {'trajectory':_ser(traj),'points':[_ser(x) for x in pts],'point_count':len(pts),'time_ordered':ordered_time,'interpolation_is_declarative':True,'routing_or_motion_model_executed_by_core':False}

def add_change(db:Session,scene_id:str,p:dict[str,Any]):
    _scene(db,scene_id); fid=p.get('feature_id')
    if fid:_feature(db,scene_id,str(fid))
    before=_dt(p.get('before_at')); after=_dt(p.get('after_at')); _ordered(before,after,'change observation')
    source=dict(p.get('source_execution') or {}); prov=dict(p.get('provenance') or {})
    if not source and not prov:raise ValueError('Change observations require source_execution or provenance.')
    row=SpatialTemporalChangeRecord(scene_id=scene_id,change_key=str(p.get('change_key') or '').strip(),label=str(p.get('label') or '').strip(),change_kind=str(p.get('change_kind') or 'change'),feature_id=fid,before_at=before,after_at=after,before_json=p.get('before'),after_json=p.get('after'),delta_json=p.get('delta'),method=str(p.get('method') or 'reported'),source_execution_json=source,provenance_json=prov,metadata_json=dict(p.get('metadata') or {}))
    if not row.change_key or not row.label:raise ValueError('change_key and label are required.')
    db.add(row)
    try:db.commit();db.refresh(row)
    except IntegrityError as exc:db.rollback();raise HTTPException(status_code=409,detail='Change key already exists in this scene.') from exc
    return _ser(row)

def add_view(db:Session,scene_id:str,p:dict[str,Any]):
    _scene(db,scene_id); kind=str(p.get('view_kind') or 'linked-map-timeline')
    if kind not in VIEW_KINDS:raise ValueError('Unsupported view_kind.')
    start=_dt(p.get('temporal_start'));end=_dt(p.get('temporal_end'));_ordered(start,end,'view')
    row=SpatialTemporalViewRecord(scene_id=scene_id,view_key=str(p.get('view_key') or '').strip(),name=str(p.get('name') or '').strip(),view_kind=kind,spatial_window_json=dict(p.get('spatial_window') or {}),temporal_start=start,temporal_end=end,layer_config_json=list(p.get('layers') or []),renderer_contract=str(p.get('renderer_contract') or 'contract.d3'),metadata_json=dict(p.get('metadata') or {}))
    if not row.view_key or not row.name:raise ValueError('view_key and name are required.')
    db.add(row)
    try:db.commit();db.refresh(row)
    except IntegrityError as exc:db.rollback();raise HTTPException(status_code=409,detail='View key already exists in this scene.') from exc
    return _ser(row)

def timeline(db:Session,scene_id:str):
    _scene(db,scene_id); out=[]
    for e in db.scalars(select(TemporalEventRecord).where(TemporalEventRecord.scene_id==scene_id)).all(): out.append({'kind':'event','id':e.id,'label':e.label,'at':e.starts_at.isoformat(),'ends_at':e.ends_at.isoformat() if e.ends_at else None})
    trajs={x.id:x for x in db.scalars(select(TrajectoryRecord).where(TrajectoryRecord.scene_id==scene_id)).all()}
    if trajs:
        for p in db.scalars(select(TrajectoryPointRecord).where(TrajectoryPointRecord.trajectory_id.in_(list(trajs)))).all(): out.append({'kind':'trajectory-point','id':p.id,'trajectory_id':p.trajectory_id,'label':trajs[p.trajectory_id].label,'at':p.observed_at.isoformat(),'sequence_position':p.sequence_position})
    for c in db.scalars(select(SpatialTemporalChangeRecord).where(SpatialTemporalChangeRecord.scene_id==scene_id)).all():
        at=c.after_at or c.before_at
        if at:out.append({'kind':'change','id':c.id,'label':c.label,'at':at.isoformat(),'change_kind':c.change_kind})
    out.sort(key=lambda x:x['at'])
    return {'scene_id':scene_id,'items':out,'count':len(out),'sorted_by':'at','temporal_inference_by_core':False}

def visualization_spec(db:Session,scene_id:str,view_id:str|None=None):
    scene=_scene(db,scene_id); view=None
    if view_id:
        view=db.get(SpatialTemporalViewRecord,view_id)
        if view is None or view.scene_id!=scene_id:raise ValueError('view_id must belong to this scene.')
    features=db.scalars(select(SpatialFeatureRecord).where(SpatialFeatureRecord.scene_id==scene_id)).all(); events=db.scalars(select(TemporalEventRecord).where(TemporalEventRecord.scene_id==scene_id)).all(); trajectories=db.scalars(select(TrajectoryRecord).where(TrajectoryRecord.scene_id==scene_id)).all()
    return {'contract':'sc.spatial-temporal-visualization.v1','scene_id':scene_id,'view_id':view_id,'visual_kind':view.view_kind if view else 'linked-map-timeline','spatial_reference':scene.spatial_reference_json,'temporal_reference':scene.temporal_reference_json,'spatial_extent':scene.spatial_extent_json,'temporal_window':{'start':scene.temporal_start.isoformat() if scene.temporal_start else None,'end':scene.temporal_end.isoformat() if scene.temporal_end else None},'layers':[{'kind':'features','count':len(features)},{'kind':'events','count':len(events)},{'kind':'trajectories','count':len(trajectories)}],'renderer_contract':view.renderer_contract if view else 'contract.d3','renderer_execution_by_core':False,'gis_layout_or_projection_by_core':False}

def runtime_handoff(db:Session,scene_id:str,p:dict[str,Any]):
    scene=_scene(db,scene_id); target=str(p.get('target_product') or 'site-intelligence')
    if target not in TARGET_PRODUCTS:raise ValueError('target_product must be site-intelligence, lab, workbench, or external.')
    if p.get('execute_by_core') is True:raise ValueError('Platform Core does not execute GIS, raster, remote-sensing, or arbitrary temporal models.')
    return {'contract':'sc.spatial-temporal-runtime-handoff.v1','scene_id':scene_id,'project_entity_id':scene.project_entity_id,'target_product':target,'operation':str(p.get('operation') or 'spatial-analysis'),'input_manifest':dict(p.get('input_manifest') or {}),'spatial_reference':scene.spatial_reference_json,'temporal_reference':scene.temporal_reference_json,'spatial_analysis_by_core':False,'raster_processing_by_core':False,'remote_sensing_by_core':False,'temporal_model_execution_by_core':False,'automatic_truth_promotion':False}

def bundle(db:Session,scene_id:str,*,public_only=False):
    scene=read_scene(db,scene_id,public_only=public_only)
    feats=db.scalars(select(SpatialFeatureRecord).where(SpatialFeatureRecord.scene_id==scene_id)).all(); evs=db.scalars(select(TemporalEventRecord).where(TemporalEventRecord.scene_id==scene_id)).all(); trajs=db.scalars(select(TrajectoryRecord).where(TrajectoryRecord.scene_id==scene_id)).all(); tids=[x.id for x in trajs]; pts=db.scalars(select(TrajectoryPointRecord).where(TrajectoryPointRecord.trajectory_id.in_(tids))).all() if tids else []; changes=db.scalars(select(SpatialTemporalChangeRecord).where(SpatialTemporalChangeRecord.scene_id==scene_id)).all(); views=db.scalars(select(SpatialTemporalViewRecord).where(SpatialTemporalViewRecord.scene_id==scene_id)).all()
    return {'scene':scene,'features':[_ser(x) for x in feats],'events':[_ser(x) for x in evs],'trajectories':[_ser(x) for x in trajs],'trajectory_points':[_ser(x) for x in pts],'changes':[_ser(x) for x in changes],'views':[_ser(x) for x in views],'timeline':timeline(db,scene_id),'visualization':visualization_spec(db,scene_id),'boundaries':{'renderer_neutral':True,'spatial_analysis_by_core':False,'raster_processing_by_core':False,'remote_sensing_by_core':False,'temporal_model_execution_by_core':False,'automatic_truth_promotion':False}}
