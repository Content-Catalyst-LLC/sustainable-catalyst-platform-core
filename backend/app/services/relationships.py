from __future__ import annotations
from collections import defaultdict, deque
from math import prod
from fastapi import HTTPException, status
from sqlalchemy import func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload
from ..models import Entity, PredicateDefinition, Relationship, RelationshipReview
from ..schemas import RelationshipCreate, RelationshipReviewCreate
from .entities import get_entity_or_404
from .predicates import validate_predicate_usage

RECOMMENDATION_WEIGHTS = {
    "routes_to":1.35,"uses":1.25,"implements":1.25,"about":1.20,"measured_by":1.20,
    "has_source":1.15,"supports":1.15,"applies_to":1.10,"part_of":1.05,"related_to":0.90,
}

def get_relationship_or_404(db: Session, relationship_id: str) -> Relationship:
    relationship = db.get(Relationship, relationship_id)
    if relationship is None:
        raise HTTPException(status_code=404, detail=f"Relationship not found: {relationship_id}")
    return relationship

def create_relationship(db: Session, payload: RelationshipCreate) -> Relationship:
    subject = get_entity_or_404(db, payload.subject_id)
    object_entity = get_entity_or_404(db, payload.object_id)
    validate_predicate_usage(db, predicate_id=payload.predicate, subject_type=subject.entity_type, object_type=object_entity.entity_type)
    relationship = Relationship(
        subject_id=payload.subject_id,predicate=payload.predicate,object_id=payload.object_id,
        confidence=payload.confidence,status=payload.status,provenance=payload.provenance,
    )
    db.add(relationship)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        existing = db.scalar(select(Relationship).where(
            Relationship.subject_id==payload.subject_id,
            Relationship.predicate==payload.predicate,
            Relationship.object_id==payload.object_id,
        ))
        if existing is not None:
            return existing
        raise HTTPException(status_code=409, detail="Relationship conflicts with an existing record.") from exc
    db.refresh(relationship)
    return relationship

def list_relationships(db: Session, *, subject_id, object_id, predicate, status_value, min_confidence, limit, offset):
    filters = []
    if subject_id: filters.append(Relationship.subject_id == subject_id)
    if object_id: filters.append(Relationship.object_id == object_id)
    if predicate: filters.append(Relationship.predicate == predicate)
    if status_value: filters.append(Relationship.status == status_value)
    if min_confidence is not None: filters.append(Relationship.confidence >= min_confidence)
    base = select(Relationship).where(*filters)
    total = int(db.scalar(select(func.count()).select_from(base.subquery())) or 0)
    items = db.scalars(base.order_by(Relationship.predicate, Relationship.created_at).limit(limit).offset(offset)).all()
    return list(items), total

def _filters(current_id, direction, predicates, statuses, min_confidence):
    filters = []
    if direction == "outbound":
        filters.append(Relationship.subject_id == current_id)
    elif direction == "inbound":
        filters.append(Relationship.object_id == current_id)
    else:
        filters.append(or_(Relationship.subject_id == current_id, Relationship.object_id == current_id))
    if predicates: filters.append(Relationship.predicate.in_(predicates))
    if statuses: filters.append(Relationship.status.in_(statuses))
    filters.append(Relationship.confidence >= min_confidence)
    return filters

def _neighbors(current_id, relationship, direction):
    found = []
    if direction in {"outbound","both"} and relationship.subject_id == current_id:
        found.append(relationship.object_id)
    if direction in {"inbound","both"} and relationship.object_id == current_id:
        found.append(relationship.subject_id)
    return found

def traverse_graph(db: Session, *, root_id, direction, max_depth, predicates, statuses=None, min_confidence=0.0):
    get_entity_or_404(db, root_id)
    visited={root_id}; queue=deque([(root_id,0)]); node_depths={root_id:0}; edge_depths={}
    while queue:
        current_id, current_depth = queue.popleft()
        if current_depth >= max_depth: continue
        rels = db.scalars(select(Relationship).where(*_filters(current_id,direction,predicates,statuses,min_confidence))).all()
        for rel in rels:
            next_depth=current_depth+1
            edge_depths.setdefault(rel.id,(rel,next_depth))
            for neighbor_id in _neighbors(current_id,rel,direction):
                if neighbor_id not in visited:
                    visited.add(neighbor_id); node_depths[neighbor_id]=next_depth; queue.append((neighbor_id,next_depth))
    entities = db.scalars(select(Entity).options(selectinload(Entity.aliases)).where(Entity.id.in_(visited))).all()
    nodes = sorted(((entity,node_depths[entity.id]) for entity in entities), key=lambda x:(x[1],x[0].entity_type,x[0].name))
    edges = sorted(edge_depths.values(), key=lambda x:(x[1],x[0].predicate,x[0].id))
    return nodes, edges

def find_paths(db: Session, *, source_id, target_id, direction, max_depth, max_paths, predicates, statuses, min_confidence):
    get_entity_or_404(db, source_id); get_entity_or_404(db, target_id)
    if source_id == target_id: return [([source_id],[],1.0)]
    queue=deque([(source_id,[source_id],[])]); paths=[]; shortest=None
    while queue and len(paths)<max_paths:
        current_id,node_path,edge_path = queue.popleft()
        if shortest is not None and len(edge_path)>=shortest: continue
        if len(edge_path)>=max_depth: continue
        rels=db.scalars(select(Relationship).where(*_filters(current_id,direction,predicates,statuses,min_confidence))).all()
        for rel in rels:
            for neighbor in _neighbors(current_id,rel,direction):
                if neighbor in node_path: continue
                next_nodes=node_path+[neighbor]; next_edges=edge_path+[rel]
                if neighbor==target_id:
                    shortest=len(next_edges)
                    score=round(prod(max(edge.confidence,0.01) for edge in next_edges)/len(next_edges),6)
                    paths.append((next_nodes,next_edges,score))
                    if len(paths)>=max_paths: break
                elif shortest is None:
                    queue.append((neighbor,next_nodes,next_edges))
    return sorted(paths,key=lambda x:(-x[2],len(x[1])))

def neighborhood(db: Session, *, root_id, statuses, min_confidence):
    root=get_entity_or_404(db,root_id)
    predicates={p.id:p for p in db.scalars(select(PredicateDefinition)).all()}
    filters=[or_(Relationship.subject_id==root_id,Relationship.object_id==root_id),Relationship.confidence>=min_confidence]
    if statuses: filters.append(Relationship.status.in_(statuses))
    rels=db.scalars(select(Relationship).where(*filters)).all()
    raw=defaultdict(list); ids=set()
    for rel in rels:
        if rel.subject_id==root_id: direction="outbound"; neighbor=rel.object_id
        else: direction="inbound"; neighbor=rel.subject_id
        raw[(direction,rel.predicate)].append(neighbor); ids.add(neighbor)
    entities={e.id:e for e in db.scalars(select(Entity).options(selectinload(Entity.aliases)).where(Entity.id.in_(ids))).all()}
    groups=[]
    for (direction,predicate_id),entity_ids in sorted(raw.items()):
        predicate=predicates.get(predicate_id)
        groups.append({
            "direction":direction,"predicate":predicate_id,
            "predicate_label":predicate.label if predicate else predicate_id,
            "count":len(entity_ids),"entities":[entities[i] for i in entity_ids if i in entities],
        })
    return root,groups,len(rels)

def recommendations(db: Session, *, root_id, target_type, limit, statuses, min_confidence):
    get_entity_or_404(db,root_id)
    nodes,edges=traverse_graph(db,root_id=root_id,direction="both",max_depth=2,predicates=None,statuses=statuses,min_confidence=min_confidence)
    entity_by_id={e.id:e for e,_ in nodes}; depth_by_id={e.id:d for e,d in nodes}
    scores=defaultdict(float); counts=defaultdict(int); predicates=defaultdict(set); reasons=defaultdict(list)
    for rel,edge_depth in edges:
        candidate_ids={rel.subject_id,rel.object_id}-{root_id}
        weight=RECOMMENDATION_WEIGHTS.get(rel.predicate,1.0)
        status_weight=1.0 if rel.status in {"verified","approved"} else 0.65
        for candidate_id in candidate_ids:
            if candidate_id not in entity_by_id: continue
            candidate=entity_by_id[candidate_id]
            if target_type and candidate.entity_type!=target_type: continue
            depth=max(depth_by_id.get(candidate_id,edge_depth),1)
            scores[candidate_id]+=rel.confidence*weight*status_weight/depth
            counts[candidate_id]+=1; predicates[candidate_id].add(rel.predicate)
            reason=f"{rel.predicate.replace('_',' ')} at graph depth {depth}"
            if reason not in reasons[candidate_id]: reasons[candidate_id].append(reason)
    ranked=sorted(scores,key=lambda i:(-scores[i],entity_by_id[i].name))[:limit]
    return [{
        "entity":entity_by_id[i],"score":round(scores[i],6),"relationship_count":counts[i],
        "predicates":sorted(predicates[i]),"reasons":reasons[i][:5],
    } for i in ranked]

REVIEW_STATUS_MAP={"approve":"verified","reject":"rejected","needs_changes":"needs_changes","restore_proposed":"proposed"}

def review_relationship(db: Session, *, relationship_id, payload: RelationshipReviewCreate):
    relationship=get_relationship_or_404(db,relationship_id)
    resulting=REVIEW_STATUS_MAP[payload.decision]
    review=RelationshipReview(
        relationship_id=relationship_id,decision=payload.decision,reviewer=payload.reviewer,
        note=payload.note,previous_status=relationship.status,resulting_status=resulting,
        metadata_json=payload.metadata,
    )
    relationship.status=resulting
    db.add(review); db.add(relationship); db.commit(); db.refresh(review)
    return review

def list_reviews(db: Session, *, relationship_id, decision, limit):
    filters=[]
    if relationship_id: filters.append(RelationshipReview.relationship_id==relationship_id)
    if decision: filters.append(RelationshipReview.decision==decision)
    return list(db.scalars(select(RelationshipReview).where(*filters).order_by(RelationshipReview.created_at.desc()).limit(limit)).all())
