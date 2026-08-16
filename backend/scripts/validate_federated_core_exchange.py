from app.config import Settings
from app.database import Database
from app.migrations import run_migrations,migration_status
from app.services import federation

def main():
    s=Settings.from_env(); d=Database(s.database_url); run_migrations(d); st=migration_status(d)
    with d.session_factory() as db: snap=federation.readiness(db,s)
    payload={'version':s.version,'migration_0026_applied':'0026' in st['applied'],'pending_migrations':st['pending'],'exchange_mode':snap['exchange_mode'],'reference_first':snap['reference_first'],'manifest_signature_algorithm':snap['manifest_signature_algorithm'],'trust_secrets_persisted':snap['trust_secrets_persisted'],'embedded_snapshots_enabled':snap['embedded_snapshots_enabled'],'automatic_truth_promotion':snap['automatic_truth_promotion'],'automatic_ownership_transfer':snap['automatic_ownership_transfer'],'automatic_cross_node_delivery':snap['automatic_cross_node_delivery'],'remote_governance_replication':snap['remote_governance_replication'],'local_subject_overwrite':snap['local_subject_overwrite']}
    print(payload)
    assert s.version=='2.25.0' and payload['migration_0026_applied'] and not st['pending']
    assert payload['exchange_mode']=='pull' and payload['reference_first'] and payload['manifest_signature_algorithm']=='hmac-sha256'
    assert payload['trust_secrets_persisted'] is False and payload['embedded_snapshots_enabled'] is False and payload['automatic_truth_promotion'] is False and payload['automatic_ownership_transfer'] is False and payload['automatic_cross_node_delivery'] is False and payload['remote_governance_replication'] is False and payload['local_subject_overwrite'] is False
    print('PASS - Core 2.25.0 federated trusted-node exchange validation')
if __name__=='__main__': main()
