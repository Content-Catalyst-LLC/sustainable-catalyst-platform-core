from __future__ import annotations
from sqlalchemy import or_, select
from sqlalchemy.orm import Session
from ..models import PredicateDefinition, Relationship
from .entities import get_entity_or_404

SCHEMA_TYPE_MAP={"article":"schema:Article","publication":"schema:CreativeWork","dataset":"schema:Dataset","source":"schema:CreativeWork","tool":"schema:SoftwareApplication","product":"schema:SoftwareApplication","service":"schema:Service","organization":"schema:Organization","country":"schema:Country","city":"schema:City","place":"schema:Place","concept":"schema:DefinedTerm","indicator":"schema:PropertyValue","treaty":"schema:Legislation","claim":"schema:Claim"}

def entity_jsonld(db: Session, entity_id: str) -> dict:
    entity=get_entity_or_404(db,entity_id)
    predicates={p.id:p for p in db.scalars(select(PredicateDefinition)).all()}
    relationships=db.scalars(select(Relationship).where(or_(Relationship.subject_id==entity_id,Relationship.object_id==entity_id))).all()
    linked=[]
    for rel in relationships:
        outbound=rel.subject_id==entity_id
        target=rel.object_id if outbound else rel.subject_id
        predicate=predicates.get(rel.predicate)
        linked.append({"sc:direction":"outbound" if outbound else "inbound","sc:predicate":rel.predicate,"sc:predicateLabel":predicate.label if predicate else rel.predicate,"sc:target":{"@id":target},"sc:confidence":rel.confidence,"sc:reviewStatus":rel.status})
    same_as=[a.value for a in entity.aliases if a.value.startswith(("http://","https://"))]
    document={
        "@context":{"schema":"https://schema.org/","dcterms":"http://purl.org/dc/terms/","prov":"http://www.w3.org/ns/prov#","sc":"https://sustainablecatalyst.com/ns/","name":"schema:name","description":"schema:description","url":"schema:url","sameAs":"schema:sameAs"},
        "@id":entity.id,"@type":SCHEMA_TYPE_MAP.get(entity.entity_type,"schema:Thing"),
        "name":entity.name,"description":entity.description,"url":entity.canonical_url,
        "dcterms:identifier":entity.id,"sc:entityType":entity.entity_type,"sc:status":entity.status,
        "sc:visibility":entity.visibility,"sc:schemaVersion":entity.schema_version,
        "sc:metadata":entity.metadata_json,"sc:relationships":linked,
    }
    if same_as: document["sameAs"]=same_as
    return {k:v for k,v in document.items() if v is not None}
