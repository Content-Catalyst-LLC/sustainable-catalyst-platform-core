from __future__ import annotations

from collections import Counter
from typing import Any

from fastapi import HTTPException
from sqlalchemy import and_, delete, func, select
from sqlalchemy.orm import Session

from ..models import (
    MapLayer,
    ScientificDataAsset,
    ScientificDataRecord,
    ScientificDomainBinding,
    TimeSeriesDefinition,
)

DOMAINS: dict[str, dict[str, Any]] = {
    "earth": {
        "label": "Earth",
        "description": "Terrestrial, atmospheric, climate, hydrologic, cryosphere, ecosystem, hazard, and Earth-observation evidence.",
        "subdomains": ["earth-observation", "atmosphere", "climate", "hydrology", "cryosphere", "land", "hazards", "ecosystems", "geophysics", "other-earth"],
    },
    "ocean": {
        "label": "Ocean",
        "description": "Marine surface, water-column, seafloor, coastal, ecosystem, pollution, hazard, and oceanographic evidence.",
        "subdomains": ["surface", "water-column", "seafloor", "coastal", "marine-ecosystems", "marine-pollution", "marine-hazards", "oceanography", "other-ocean"],
    },
    "space": {
        "label": "Space",
        "description": "Earth-orbit, lunar, planetary, solar-system, astronomy, astrophysics, exoplanet, and technosignature evidence.",
        "subdomains": ["earth-orbit", "moon", "planetary", "solar-system", "astronomy", "astrophysics", "exoplanets", "technosignatures", "other-space"],
    },
}

SPACE_TOKENS = {
    "astronomy", "astrophysics", "telescope", "jwst", "hubble", "mast", "heasarc", "irsa", "eso",
    "exoplanet", "planetary", "solar system", "solar-system", "moon", "lunar", "mars", "venus", "jupiter",
    "saturn", "asteroid", "comet", "technosignature", "seti", "space science", "space_science",
}
OCEAN_TOKENS = {
    "ocean", "oceanographic", "marine", "sea surface", "sea-surface", "seawater", "salinity", "bathymetry",
    "seafloor", "water column", "water-column", "coastal", "coral", "plankton", "marine ecosystem",
}
EARTH_TOKENS = {
    "earth science", "earth_science", "earth observation", "earth_observation", "climate", "weather", "atmosphere",
    "hydrology", "river", "flood", "drought", "cryosphere", "glacier", "ice", "land surface", "vegetation",
    "wildfire", "earthquake", "volcano", "geophysical", "biodiversity", "ecosystem",
}


def _norm(value: Any) -> str:
    return str(value or "").strip().lower().replace("_", " ")


def _text(parts: list[Any]) -> str:
    flattened: list[str] = []
    for part in parts:
        if isinstance(part, dict):
            flattened.extend(f"{k} {v}" for k, v in part.items())
        elif isinstance(part, (list, tuple, set)):
            flattened.extend(str(x) for x in part)
        elif part is not None:
            flattened.append(str(part))
    return " ".join(flattened).lower()


def _contains(text: str, tokens: set[str]) -> list[str]:
    return sorted(token for token in tokens if token in text)


def _subdomain(domain: str, text: str) -> str:
    if domain == "ocean":
        checks = [
            ("seafloor", {"bathymetry", "seafloor"}),
            ("water-column", {"water column", "water-column", "salinity"}),
            ("surface", {"sea surface", "sea-surface", "sst", "surface temperature"}),
            ("coastal", {"coastal", "shore", "coast"}),
            ("marine-ecosystems", {"coral", "plankton", "marine ecosystem", "biodiversity"}),
            ("marine-pollution", {"marine debris", "oil spill", "pollution"}),
            ("marine-hazards", {"tsunami", "storm surge", "harmful algal"}),
        ]
        fallback = "oceanography"
    elif domain == "space":
        checks = [
            ("technosignatures", {"technosignature", "seti"}),
            ("exoplanets", {"exoplanet"}),
            ("moon", {"moon", "lunar"}),
            ("planetary", {"planetary", "mars", "venus", "jupiter", "saturn", "asteroid", "comet"}),
            ("solar-system", {"solar system", "solar-system", "heliophysics"}),
            ("astrophysics", {"astrophysics", "high energy", "high-energy", "infrared astronomy"}),
            ("earth-orbit", {"earth orbit", "earth-orbit", "satellite"}),
        ]
        fallback = "astronomy"
    else:
        checks = [
            ("earth-observation", {"earth observation", "earth-observation", "remote sensing"}),
            ("atmosphere", {"atmosphere", "aerosol", "air quality", "weather"}),
            ("climate", {"climate", "temperature anomaly"}),
            ("hydrology", {"hydrology", "river", "flood", "drought"}),
            ("cryosphere", {"cryosphere", "glacier", "sea ice", "ice sheet"}),
            ("hazards", {"earthquake", "volcano", "wildfire"}),
            ("ecosystems", {"biodiversity", "ecosystem", "vegetation"}),
            ("geophysics", {"geophysical", "gravity", "geomagnetic"}),
            ("land", {"land surface", "soil", "land cover"}),
        ]
        fallback = "other-earth"
    for label, tokens in checks:
        if any(token in text for token in tokens):
            return label
    return fallback


def classify_record(record: ScientificDataRecord) -> list[dict[str, Any]]:
    text = _text([
        record.record_type, record.discipline, record.title, record.summary, record.collection, record.mission,
        record.instrument, record.target, record.keywords_json, record.variables_json, record.metadata_json,
    ])
    explicit = _norm(record.discipline)
    domains: list[tuple[str, str, list[str]]] = []
    space_hits = _contains(text, SPACE_TOKENS)
    ocean_hits = _contains(text, OCEAN_TOKENS)
    earth_hits = _contains(text, EARTH_TOKENS)
    if space_hits or explicit in {"astronomy", "astrophysics", "high energy astrophysics", "infrared astronomy", "space science"}:
        domains.append(("space", "explicit-discipline" if explicit in {"astronomy", "astrophysics", "high energy astrophysics", "infrared astronomy", "space science"} else "metadata-keyword", space_hits))
    if ocean_hits or explicit in {"oceanography", "marine science", "marine_science"}:
        domains.append(("ocean", "explicit-discipline" if explicit in {"oceanography", "marine science", "marine_science"} else "metadata-keyword", ocean_hits))
    if earth_hits or explicit in {"earth science", "earth_science", "climate", "hydrology", "geophysics", "environmental science"}:
        domains.append(("earth", "explicit-discipline" if explicit in {"earth science", "earth_science", "climate", "hydrology", "geophysics", "environmental science"} else "metadata-keyword", earth_hits))
    # Ocean is presented as its own front door even though it is part of the Earth system.
    if any(item[0] == "ocean" for item in domains):
        domains = [item for item in domains if item[0] != "earth"] + [item for item in domains if item[0] == "earth" and "earth observation" in item[2]]
    if not domains:
        return []
    result=[]
    for index,(domain,basis,hits) in enumerate(domains):
        result.append({
            "domain": domain,
            "subdomain": _subdomain(domain,text),
            "classification_basis": basis,
            "classification_evidence": hits[:12],
            "confidence": 1.0 if basis == "explicit-discipline" else 0.75,
            "is_primary": index == 0,
        })
    return result


def classify_series(series: TimeSeriesDefinition) -> list[dict[str, Any]]:
    text = _text([series.domain, series.metric, series.title, series.description, series.dataset_id, series.dimensions_json])
    raw_domain = _norm(series.domain)
    if any(token in text for token in OCEAN_TOKENS) or raw_domain in {"ocean", "oceanography", "marine"}:
        domain = "ocean"
    elif any(token in text for token in SPACE_TOKENS) or raw_domain in {"astronomy", "space science", "space_science"}:
        domain = "space"
    elif any(token in text for token in EARTH_TOKENS) or raw_domain in {"earth science", "earth_science", "climate", "hydrology", "earth observation", "earth_observation"}:
        domain = "earth"
    else:
        return []
    return [{
        "domain": domain, "subdomain": _subdomain(domain,text), "classification_basis": "series-domain",
        "classification_evidence": [series.domain], "confidence": 0.9, "is_primary": True,
    }]


def classify_layer(layer: MapLayer) -> list[dict[str, Any]]:
    text = _text([layer.title, layer.description, layer.layer_type, layer.metadata_json])
    if any(token in text for token in OCEAN_TOKENS): domain="ocean"
    elif any(token in text for token in SPACE_TOKENS): domain="space"
    elif any(token in text for token in EARTH_TOKENS) or layer.source_id == "nasa-earthdata": domain="earth"
    else: return []
    return [{"domain":domain,"subdomain":_subdomain(domain,text),"classification_basis":"layer-metadata","classification_evidence":[],"confidence":0.75,"is_primary":True}]


def _upsert_bindings(db: Session, subject_type: str, subject_id: str, classifications: list[dict[str, Any]], public: bool) -> int:
    db.execute(delete(ScientificDomainBinding).where(and_(ScientificDomainBinding.subject_type==subject_type, ScientificDomainBinding.subject_id==subject_id)))
    created=0
    for item in classifications:
        db.add(ScientificDomainBinding(
            subject_type=subject_type, subject_id=subject_id, domain=item["domain"], subdomain=item["subdomain"],
            classification_basis=item["classification_basis"], classification_evidence_json=item["classification_evidence"],
            confidence=item["confidence"], is_primary=item["is_primary"], routing_only=True, truth_precedence="none", public=public,
        )); created += 1
    return created



def materialize_record_binding(db: Session, record: ScientificDataRecord) -> int:
    """Refresh deterministic domain routing for one scientific record.

    Routing bindings never change the underlying scientific record or its factual
    provenance and carry no Truth precedence.
    """
    created = _upsert_bindings(db, "scientific_record", record.id, classify_record(record), record.public)
    return created

def materialize(db: Session, *, public_only: bool = False) -> dict[str, int]:
    totals={"records":0,"series":0,"map_layers":0,"bindings":0}
    q=select(ScientificDataRecord)
    if public_only: q=q.where(ScientificDataRecord.public.is_(True))
    for row in db.scalars(q).all():
        classifications=classify_record(row); totals["bindings"] += materialize_record_binding(db,row); totals["records"] += int(bool(classifications))
    q=select(TimeSeriesDefinition)
    if public_only: q=q.where(TimeSeriesDefinition.public.is_(True))
    for row in db.scalars(q).all():
        classifications=classify_series(row); totals["bindings"] += _upsert_bindings(db,"time_series",row.id,classifications,row.public); totals["series"] += int(bool(classifications))
    q=select(MapLayer)
    if public_only: q=q.where(MapLayer.public.is_(True))
    for row in db.scalars(q).all():
        classifications=classify_layer(row); totals["bindings"] += _upsert_bindings(db,"map_layer",row.id,classifications,row.public); totals["map_layers"] += int(bool(classifications))
    db.commit(); return totals


def domain_or_404(domain: str) -> str:
    value=_norm(domain).replace(" ","-")
    if value not in DOMAINS: raise HTTPException(404,"Scientific domain not found.")
    return value


def domain_summary(db: Session, domain: str, *, public_only: bool = False) -> dict[str, Any]:
    domain=domain_or_404(domain)
    q=select(ScientificDomainBinding).where(ScientificDomainBinding.domain==domain)
    if public_only: q=q.where(ScientificDomainBinding.public.is_(True))
    bindings=list(db.scalars(q).all())
    counts=Counter(row.subject_type for row in bindings); subdomains=Counter(row.subdomain for row in bindings)
    record_ids=[row.subject_id for row in bindings if row.subject_type=="scientific_record"]
    missions: Counter[str]=Counter(); sources: Counter[str]=Counter()
    if record_ids:
        rq=select(ScientificDataRecord).where(ScientificDataRecord.id.in_(record_ids))
        if public_only: rq=rq.where(ScientificDataRecord.public.is_(True))
        for record in db.scalars(rq).all():
            if record.mission: missions[record.mission]+=1
            sources[record.source_id]+=1
    return {
        "domain": domain, **DOMAINS[domain], "bindings": len(bindings), "records": counts.get("scientific_record",0),
        "time_series": counts.get("time_series",0), "map_layers": counts.get("map_layer",0),
        "subdomains": dict(sorted(subdomains.items())), "missions": dict(missions.most_common()), "sources": dict(sources.most_common()),
        "routing_only": True, "truth_precedence": "none", "zero_records_implication": "no-routed-records-not-no-science",
    }


def list_domain_records(db: Session, domain: str, *, public_only: bool=False, mission: str|None=None, subdomain: str|None=None, limit:int=100, offset:int=0) -> tuple[list[ScientificDataRecord],int]:
    domain=domain_or_404(domain)
    bq=select(ScientificDomainBinding.subject_id).where(and_(ScientificDomainBinding.domain==domain,ScientificDomainBinding.subject_type=="scientific_record"))
    if subdomain: bq=bq.where(ScientificDomainBinding.subdomain==subdomain)
    if public_only: bq=bq.where(ScientificDomainBinding.public.is_(True))
    ids=list(db.scalars(bq).all())
    if not ids: return [],0
    q=select(ScientificDataRecord).where(ScientificDataRecord.id.in_(ids)); cq=select(func.count()).select_from(ScientificDataRecord).where(ScientificDataRecord.id.in_(ids))
    if mission: q=q.where(ScientificDataRecord.mission==mission); cq=cq.where(ScientificDataRecord.mission==mission)
    if public_only: q=q.where(ScientificDataRecord.public.is_(True)); cq=cq.where(ScientificDataRecord.public.is_(True))
    return list(db.scalars(q.order_by(ScientificDataRecord.title).limit(limit).offset(offset)).all()), int(db.scalar(cq) or 0)


def list_domain_series(db:Session,domain:str,*,public_only:bool=False,limit:int=100,offset:int=0):
    domain=domain_or_404(domain)
    bq=select(ScientificDomainBinding.subject_id).where(and_(ScientificDomainBinding.domain==domain,ScientificDomainBinding.subject_type=="time_series"))
    if public_only: bq=bq.where(ScientificDomainBinding.public.is_(True))
    ids=list(db.scalars(bq).all())
    if not ids:return [],0
    q=select(TimeSeriesDefinition).where(TimeSeriesDefinition.id.in_(ids)); cq=select(func.count()).select_from(TimeSeriesDefinition).where(TimeSeriesDefinition.id.in_(ids))
    if public_only:q=q.where(TimeSeriesDefinition.public.is_(True));cq=cq.where(TimeSeriesDefinition.public.is_(True))
    return list(db.scalars(q.order_by(TimeSeriesDefinition.title).limit(limit).offset(offset)).all()),int(db.scalar(cq) or 0)


def list_domain_layers(db:Session,domain:str,*,public_only:bool=False,limit:int=100,offset:int=0):
    domain=domain_or_404(domain)
    bq=select(ScientificDomainBinding.subject_id).where(and_(ScientificDomainBinding.domain==domain,ScientificDomainBinding.subject_type=="map_layer"))
    if public_only:bq=bq.where(ScientificDomainBinding.public.is_(True))
    ids=list(db.scalars(bq).all())
    if not ids:return [],0
    q=select(MapLayer).where(MapLayer.id.in_(ids));cq=select(func.count()).select_from(MapLayer).where(MapLayer.id.in_(ids))
    if public_only:q=q.where(MapLayer.public.is_(True));cq=cq.where(MapLayer.public.is_(True))
    return list(db.scalars(q.order_by(MapLayer.title).limit(limit).offset(offset)).all()),int(db.scalar(cq) or 0)


def list_domain_assets(db:Session,domain:str,*,public_only:bool=False,limit:int=100,offset:int=0):
    records,_=list_domain_records(db,domain,public_only=public_only,limit=100000,offset=0)
    ids=[r.id for r in records]
    if not ids:return [],0
    q=select(ScientificDataAsset).where(ScientificDataAsset.scientific_record_id.in_(ids));cq=select(func.count()).select_from(ScientificDataAsset).where(ScientificDataAsset.scientific_record_id.in_(ids))
    if public_only:q=q.where(ScientificDataAsset.public.is_(True));cq=cq.where(ScientificDataAsset.public.is_(True))
    return list(db.scalars(q.order_by(ScientificDataAsset.title).limit(limit).offset(offset)).all()),int(db.scalar(cq) or 0)
