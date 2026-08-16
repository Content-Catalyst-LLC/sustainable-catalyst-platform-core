import json, os, tempfile
from dataclasses import replace
from fastapi.testclient import TestClient
from app.config import Settings
from app.database import Database, Base
from app.main import create_app
from app.migrations import MIGRATIONS, run_migrations, migration_status
from app.models import SchemaMigration
from app.services import federation, certification

SECRET='shared-federation-secret-1234567890'
def settings_for(path,**kw): return Settings(database_url='sqlite:///'+path,observability_request_metrics_enabled=False,federation_local_node_id='node-a',federation_trust_secrets_json=json.dumps({'node-b':SECRET}),**kw)
def dbs(**kw):
    fd,p=tempfile.mkstemp(suffix='.db'); os.close(fd); d=Database('sqlite:///'+p); run_migrations(d); return d,p,settings_for(p,**kw)
def node_and_trust(db,private=False):
    federation.register_node(db,node_key='node-b',name='Remote B',trust_state='pending',metadata={'shared_secret':'must-not-persist'})
    return federation.create_trust(db,relationship_key='a-b',remote_node_key='node-b',allowed_subject_types=['evidence-record','claim'],allow_private_records=private)
def item(**kw):
    x={'subject_type':'evidence-record','subject_id':'e1','canonical_uri':'sc-core://evidence/e1','content_sha256':'a'*64,'visibility':'internal','provenance':{'source':'remote'}}; x.update(kw); return x

def test_readiness_and_migration_0026():
    fd,p=tempfile.mkstemp(suffix='.db'); os.close(fd)
    try:
        c=TestClient(create_app(settings_for(p))); b=c.get('/v1/federation/readiness').json(); assert b['release']=='2.23.1' and b['migration_0026_applied'] and b['reference_first'] and b['trust_secrets_persisted'] is False and b['automatic_truth_promotion'] is False
    finally: os.unlink(p)

def test_node_registration_scrubs_secret_like_metadata():
    d,p,s=dbs()
    try:
        with d.session_factory() as db:
            row=federation.register_node(db,node_key='node-b',name='Remote',metadata={'shared_secret':'nope','token':'nope','label':'ok'}); assert row.metadata_json['shared_secret']=='[redacted]' and row.metadata_json['token']=='[redacted]' and row.metadata_json['label']=='ok'
    finally: os.unlink(p)

def test_trust_relationship_disables_snapshots_and_authority_transfer():
    d,p,s=dbs()
    try:
        with d.session_factory() as db:
            rel=node_and_trust(db); assert rel.allow_snapshots is False and rel.automatic_truth_promotion is False and rel.automatic_ownership_transfer is False and rel.signature_required is True
    finally: os.unlink(p)

def test_outbound_manifest_is_authenticated_reference_first():
    d,p,s=dbs()
    try:
        with d.session_factory() as db:
            node_and_trust(db); row=federation.create_outbound_manifest(db,s,manifest_key='m1',target_node_key='node-b',items=[item()]); assert row.signature_value and len(row.signature_value)==64 and row.manifest_json['reference_first'] is True and row.manifest_json['automatic_truth_promotion'] is False and row.verification_state=='self-authenticated'
    finally: os.unlink(p)

def test_manifest_rejects_embedded_snapshot_payload():
    d,p,s=dbs()
    try:
        with d.session_factory() as db:
            node_and_trust(db)
            try: federation.create_outbound_manifest(db,s,manifest_key='m2',target_node_key='node-b',items=[item(snapshot={'x':1})])
            except ValueError: pass
            else: raise AssertionError('embedded snapshot accepted')
    finally: os.unlink(p)

def test_verified_inbound_acceptance_creates_remote_reference_without_local_overwrite():
    d,p,s=dbs()
    try:
        with d.session_factory() as db:
            node_and_trust(db); core={'schema':'sc-core-federation-manifest-v1','origin_node':'node-b','target_node':'node-a','exchange_mode':'pull','reference_first':True,'automatic_truth_promotion':False,'automatic_ownership_transfer':False,'automatic_delivery':False,'items':[item()]}; sig=federation._sign(core,SECRET); row=federation.ingest_manifest(db,s,manifest_key='in1',origin_node_key='node-b',manifest=core,signature_value=sig); assert row.verification_state=='verified'; federation.accept_manifest(db,row,actor='ops'); refs=federation.list_references(db); assert len(refs)==1 and refs[0].state=='reference-only' and refs[0].local_subject_overwritten is False and refs[0].automatic_truth_promotion is False and refs[0].automatic_ownership_transfer is False
    finally: os.unlink(p)

def test_signature_mismatch_is_rejected_and_cannot_be_accepted():
    d,p,s=dbs()
    try:
        with d.session_factory() as db:
            node_and_trust(db); core={'origin_node':'node-b','target_node':'node-a','reference_first':True,'automatic_truth_promotion':False,'automatic_ownership_transfer':False,'items':[item()]}; row=federation.ingest_manifest(db,s,manifest_key='bad-sig',origin_node_key='node-b',manifest=core,signature_value='0'*64); assert row.verification_state=='signature-mismatch' and row.state=='rejected'
            try: federation.accept_manifest(db,row)
            except ValueError: pass
            else: raise AssertionError('rejected manifest accepted')
    finally: os.unlink(p)

def test_private_reference_requires_explicit_trust_scope():
    d,p,s=dbs()
    try:
        with d.session_factory() as db:
            node_and_trust(db,private=False)
            try: federation.create_outbound_manifest(db,s,manifest_key='private',target_node_key='node-b',items=[item(visibility='private')])
            except ValueError: pass
            else: raise AssertionError('private record escaped trust scope')
    finally: os.unlink(p)

def test_public_status_is_aggregate_only():
    d,p,s=dbs()
    try:
        with d.session_factory() as db:
            node_and_trust(db); b=federation.public_status(db,s); assert b['node_identities_publicly_exposed'] is False and b['trust_relationship_details_publicly_exposed'] is False and b['remote_reference_contents_publicly_exposed'] is False and 'nodes' not in b and 'items' not in b
    finally: os.unlink(p)

def test_certification_gate_is_opt_in_and_can_block_missing_runtime_secret():
    d,p,s=dbs()
    try:
        with d.session_factory() as db:
            node_and_trust(db); _,detail=certification.run_certification(db,d,s,{'release_ready':True,'required_blockers':[]}); assert 'federated_core_trusted_node_exchange' not in detail['blockers']
        with d.session_factory() as db:
            strict=replace(s,federation_trust_secrets_json='{}',certification_require_federation_ready=True); _,detail=certification.run_certification(db,d,strict,{'release_ready':True,'required_blockers':[]}); assert 'federated_core_trusted_node_exchange' in detail['blockers']
    finally: os.unlink(p)

def test_internal_api_round_trip():
    fd,p=tempfile.mkstemp(suffix='.db'); os.close(fd)
    try:
        c=TestClient(create_app(settings_for(p))); assert c.post('/v1/federation/nodes',json={'node_key':'node-b','name':'Remote B'}).status_code==200; assert c.post('/v1/federation/trust',json={'relationship_key':'a-b','remote_node_key':'node-b','allowed_subject_types':['evidence-record']}).status_code==200; r=c.post('/v1/federation/manifests/outbound',json={'manifest_key':'api-m','target_node_key':'node-b','items':[item()]}); assert r.status_code==200 and r.json()['signature_value']; pub=c.get('/api/v1/federation/status'); assert pub.status_code in (200,401,403)
    finally: os.unlink(p)

def test_migration_rehearsal_from_0025_applies_current_head():
    fd,p=tempfile.mkstemp(suffix='.db'); os.close(fd); d=Database('sqlite:///'+p)
    try:
        Base.metadata.create_all(d.engine)
        with d.session_factory() as db:
            for version,description in MIGRATIONS:
                if version<='0025': db.add(SchemaMigration(version=version,description=description))
            db.commit()
        expected=[version for version,_ in MIGRATIONS if version>'0025']; assert run_migrations(d)==expected and migration_status(d)['pending']==[]
    finally: os.unlink(p)
