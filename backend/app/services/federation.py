from __future__ import annotations
import hashlib, hmac, json
from datetime import datetime, timezone
from sqlalchemy import select, func
from sqlalchemy.orm import Session
from ..models import FederationNodeRecord, FederationTrustRelationship, FederationExchangeManifest, FederationRemoteReference

SECRET_KEYS={"password","secret","token","authorization","api_key","apikey","credential","credentials","access_key","secret_key","shared_secret"}
TRUST_STATES={"pending","trusted","suspended","revoked"}
NODE_STATES={"active","disabled"}
VISIBILITY={"public","internal","private","restricted"}

def _now(): return datetime.now(timezone.utc)
def _scrub(value):
    if isinstance(value,dict): return {str(k):("[redacted]" if str(k).lower() in SECRET_KEYS else _scrub(v)) for k,v in value.items()}
    if isinstance(value,list): return [_scrub(v) for v in value]
    return value

def _canonical(value): return json.dumps(value,sort_keys=True,separators=(",",":"),ensure_ascii=False,default=str).encode()
def _sha(value): return hashlib.sha256(_canonical(value)).hexdigest()
def _secrets(settings):
    try:
        raw=json.loads(settings.federation_trust_secrets_json or "{}")
        return {str(k):str(v) for k,v in raw.items() if str(k).strip() and str(v)} if isinstance(raw,dict) else {}
    except Exception: return {}
def _sign(payload,secret): return hmac.new(secret.encode(),_canonical(payload),hashlib.sha256).hexdigest()

def register_node(db:Session,*,node_key:str,name:str,environment:str="production",base_url:str|None=None,trust_state:str="pending",signing_key_id:str|None=None,signing_key_fingerprint:str|None=None,capabilities:list|None=None,metadata:dict|None=None):
    node_key=node_key.strip(); name=name.strip()
    if not node_key or not name: raise ValueError("node_key and name are required.")
    if trust_state not in TRUST_STATES: raise ValueError("Unsupported trust_state.")
    existing=db.scalar(select(FederationNodeRecord).where(FederationNodeRecord.node_key==node_key))
    if existing: return existing
    row=FederationNodeRecord(node_key=node_key[:255],name=name[:300],environment=environment[:40],base_url=(base_url or None),trust_state=trust_state,signing_key_id=signing_key_id,signing_key_fingerprint=signing_key_fingerprint,capabilities_json=list(capabilities or []),metadata_json=_scrub(metadata or {}))
    db.add(row); db.commit(); db.refresh(row); return row

def list_nodes(db:Session): return db.scalars(select(FederationNodeRecord).order_by(FederationNodeRecord.node_key)).all()

def create_trust(db:Session,*,relationship_key:str,remote_node_key:str,allowed_subject_types:list|None=None,allow_snapshots:bool=False,allow_private_records:bool=False,signature_required:bool=True,metadata:dict|None=None):
    node=db.scalar(select(FederationNodeRecord).where(FederationNodeRecord.node_key==remote_node_key))
    if not node: raise ValueError("Remote node is not registered.")
    if node.trust_state in {"revoked","suspended"}: raise ValueError("Remote node cannot be trusted while suspended or revoked.")
    existing=db.scalar(select(FederationTrustRelationship).where(FederationTrustRelationship.remote_node_id==node.id))
    if existing: return existing
    node.trust_state="trusted"; db.add(node)
    row=FederationTrustRelationship(relationship_key=relationship_key[:255],remote_node_id=node.id,allowed_subject_types_json=list(allowed_subject_types or []),allow_snapshots=False,allow_private_records=bool(allow_private_records),signature_required=bool(signature_required),automatic_truth_promotion=False,automatic_ownership_transfer=False,metadata_json=_scrub(metadata or {}))
    db.add(row); db.commit(); db.refresh(row); return row

def list_trust(db:Session): return db.scalars(select(FederationTrustRelationship).order_by(FederationTrustRelationship.relationship_key)).all()

def _relationship(db:Session,node_key:str):
    node=db.scalar(select(FederationNodeRecord).where(FederationNodeRecord.node_key==node_key))
    if not node or node.state!="active" or node.trust_state!="trusted": raise ValueError("Remote node is not active and trusted.")
    rel=db.scalar(select(FederationTrustRelationship).where(FederationTrustRelationship.remote_node_id==node.id,FederationTrustRelationship.state=="active"))
    if not rel: raise ValueError("No active trust relationship exists for remote node.")
    return node,rel

def _normalize_items(items:list,rel:FederationTrustRelationship,settings):
    if not isinstance(items,list) or not items: raise ValueError("At least one manifest item is required.")
    if len(items)>settings.federation_max_manifest_items: raise ValueError("Manifest item limit exceeded.")
    allowed=set(rel.allowed_subject_types_json or [])
    out=[]
    for raw in items:
        if not isinstance(raw,dict): raise ValueError("Manifest items must be objects.")
        item=_scrub(raw)
        subject_type=str(item.get("subject_type","")).strip(); subject_id=str(item.get("subject_id","")).strip(); uri=str(item.get("canonical_uri","")).strip(); digest=str(item.get("content_sha256","")).strip().lower(); visibility=str(item.get("visibility","internal")).strip().lower()
        if not subject_type or not subject_id or not uri or len(digest)!=64 or any(c not in '0123456789abcdef' for c in digest): raise ValueError("Each manifest item requires subject_type, subject_id, canonical_uri, and a SHA-256 content hash.")
        if allowed and subject_type not in allowed: raise ValueError("Subject type is outside the trust relationship scope.")
        if visibility not in VISIBILITY: raise ValueError("Unsupported item visibility.")
        if visibility in {"private","restricted"} and not rel.allow_private_records: raise ValueError("Private/restricted federation is not allowed by this trust relationship.")
        if "snapshot" in item or "payload" in item: raise ValueError("Federation manifests are reference-first; embedded snapshots/payloads are disabled.")
        out.append({"subject_type":subject_type[:120],"subject_id":subject_id[:255],"canonical_uri":uri[:2000],"content_sha256":digest,"visibility":visibility,"provenance":_scrub(item.get("provenance") or {})})
    return out

def create_outbound_manifest(db:Session,settings,*,manifest_key:str,target_node_key:str,items:list,metadata:dict|None=None):
    if not settings.federation_trusted_node_exchange_enabled: raise ValueError("Federation is disabled.")
    node,rel=_relationship(db,target_node_key); clean_items=_normalize_items(items,rel,settings)
    existing=db.scalar(select(FederationExchangeManifest).where(FederationExchangeManifest.manifest_key==manifest_key))
    if existing: return existing
    core={"schema":"sc-core-federation-manifest-v1","origin_node":settings.federation_local_node_id,"target_node":target_node_key,"exchange_mode":"pull","reference_first":True,"automatic_truth_promotion":False,"automatic_ownership_transfer":False,"automatic_delivery":False,"items":clean_items}
    secrets=_secrets(settings); secret=secrets.get(target_node_key); signature_required=settings.federation_manifest_signature_required or rel.signature_required
    if signature_required and not secret: raise ValueError("No environment-provided trust secret is configured for the target node.")
    signature=_sign(core,secret) if secret else None
    row=FederationExchangeManifest(manifest_key=manifest_key[:255],direction="outbound",origin_node_key=settings.federation_local_node_id,target_node_key=target_node_key,state="created",item_count=len(clean_items),manifest_json=core,manifest_sha256=_sha(core),signature_algorithm="hmac-sha256",signature_key_id=node.signing_key_id,signature_value=signature,verification_state="self-authenticated" if signature else "unsigned",metadata_json=_scrub(metadata or {}))
    db.add(row); db.commit(); db.refresh(row); return row

def ingest_manifest(db:Session,settings,*,manifest_key:str,origin_node_key:str,manifest:dict,signature_value:str|None=None,signature_key_id:str|None=None,metadata:dict|None=None):
    if not settings.federation_trusted_node_exchange_enabled: raise ValueError("Federation is disabled.")
    node,rel=_relationship(db,origin_node_key)
    existing=db.scalar(select(FederationExchangeManifest).where(FederationExchangeManifest.manifest_key==manifest_key))
    if existing: return existing
    core=_scrub(manifest or {})
    if core.get("origin_node")!=origin_node_key: raise ValueError("Manifest origin does not match the trusted node.")
    if core.get("target_node")!=settings.federation_local_node_id: raise ValueError("Manifest target does not match this Core node.")
    if core.get("reference_first") is not True or core.get("automatic_truth_promotion") is not False or core.get("automatic_ownership_transfer") is not False: raise ValueError("Manifest violates federation authority boundaries.")
    clean_items=_normalize_items(core.get("items") or [],rel,settings); core={**core,"items":clean_items}
    secret=_secrets(settings).get(origin_node_key); required=settings.federation_manifest_signature_required or rel.signature_required
    valid=bool(secret and signature_value and hmac.compare_digest(_sign(core,secret),signature_value)) if required else (not signature_value or bool(secret and hmac.compare_digest(_sign(core,secret),signature_value)))
    state="verified" if valid else "rejected"; verification="verified" if valid else "signature-mismatch"
    row=FederationExchangeManifest(manifest_key=manifest_key[:255],direction="inbound",origin_node_key=origin_node_key,target_node_key=settings.federation_local_node_id,state=state,item_count=len(clean_items),manifest_json=core,manifest_sha256=_sha(core),signature_algorithm="hmac-sha256",signature_key_id=signature_key_id or node.signing_key_id,signature_value=signature_value,verification_state=verification,metadata_json=_scrub(metadata or {}),verified_at=_now() if valid else None)
    db.add(row); db.commit(); db.refresh(row); return row

def accept_manifest(db:Session,row:FederationExchangeManifest,*,actor:str="operator"):
    if row.direction!="inbound" or row.verification_state!="verified": raise ValueError("Only verified inbound manifests can be accepted.")
    for item in row.manifest_json.get("items",[]):
        existing=db.scalar(select(FederationRemoteReference).where(FederationRemoteReference.origin_node_key==row.origin_node_key,FederationRemoteReference.subject_type==item["subject_type"],FederationRemoteReference.subject_id==item["subject_id"],FederationRemoteReference.content_sha256==item["content_sha256"]))
        if not existing:
            db.add(FederationRemoteReference(manifest_id=row.id,origin_node_key=row.origin_node_key,subject_type=item["subject_type"],subject_id=item["subject_id"],canonical_uri=item["canonical_uri"],content_sha256=item["content_sha256"],visibility=item["visibility"],state="reference-only",provenance_json={"remote_provenance":item.get("provenance") or {},"accepted_by":actor[:255],"truth_precedence":"none","ownership":"remote"},automatic_truth_promotion=False,automatic_ownership_transfer=False,local_subject_overwritten=False))
    row.state="accepted"; row.accepted_at=_now(); db.add(row); db.commit(); db.refresh(row); return row

def list_manifests(db:Session,limit:int=100): return db.scalars(select(FederationExchangeManifest).order_by(FederationExchangeManifest.created_at.desc()).limit(limit)).all()
def list_references(db:Session,limit:int=200): return db.scalars(select(FederationRemoteReference).order_by(FederationRemoteReference.created_at.desc()).limit(limit)).all()

def readiness(db:Session,settings):
    nodes=db.scalar(select(func.count()).select_from(FederationNodeRecord)) or 0; trusted=db.scalar(select(func.count()).select_from(FederationNodeRecord).where(FederationNodeRecord.trust_state=="trusted",FederationNodeRecord.state=="active")) or 0; rels=db.scalar(select(func.count()).select_from(FederationTrustRelationship).where(FederationTrustRelationship.state=="active")) or 0; refs=db.scalar(select(func.count()).select_from(FederationRemoteReference)) or 0; rejected=db.scalar(select(func.count()).select_from(FederationExchangeManifest).where(FederationExchangeManifest.verification_state=="signature-mismatch")) or 0
    secrets=_secrets(settings); missing=[]
    for node in db.scalars(select(FederationNodeRecord).where(FederationNodeRecord.trust_state=="trusted",FederationNodeRecord.state=="active")).all():
        if settings.federation_manifest_signature_required and node.node_key not in secrets: missing.append(node.node_key)
    state="disabled" if not settings.federation_trusted_node_exchange_enabled else ("attention" if missing or rejected else "ready")
    return {"enabled":settings.federation_trusted_node_exchange_enabled,"state":state,"local_node_id":settings.federation_local_node_id,"registered_nodes":nodes,"trusted_nodes":trusted,"active_trust_relationships":rels,"remote_references":refs,"signature_mismatches":rejected,"trusted_nodes_missing_runtime_secret":len(missing),"exchange_mode":"pull","reference_first":True,"manifest_signature_algorithm":"hmac-sha256","trust_secrets_persisted":False,"embedded_snapshots_enabled":False,"automatic_truth_promotion":False,"automatic_ownership_transfer":False,"automatic_cross_node_delivery":False,"remote_governance_replication":False,"local_subject_overwrite":False,"evidence_semantics_unchanged":True}

def public_status(db:Session,settings):
    s=readiness(db,settings); return {"state":s["state"],"registered_nodes":s["registered_nodes"],"trusted_nodes":s["trusted_nodes"],"active_trust_relationships":s["active_trust_relationships"],"remote_references":s["remote_references"],"signature_mismatches":s["signature_mismatches"],"exchange_mode":"pull","reference_first":True,"node_identities_publicly_exposed":False,"trust_relationship_details_publicly_exposed":False,"remote_reference_contents_publicly_exposed":False,"automatic_truth_promotion":False,"evidence_semantics_unchanged":True}

def certification_snapshot(db:Session,settings):
    s=readiness(db,settings); return {"state":s["state"],"federation_ready":s["state"]=="ready","signature_mismatches":s["signature_mismatches"],"missing_runtime_secrets":s["trusted_nodes_missing_runtime_secret"],"automatic_truth_promotion":False}
