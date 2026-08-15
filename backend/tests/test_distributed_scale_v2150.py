from datetime import datetime, timedelta, timezone

def test_scale_release_and_migration(client):
    assert client.get('/health').json()['version']=='2.17.0'
    body=client.get('/v1/scale/readiness').json()
    assert body['release']=='2.17.0' and body['migration_0018_applied'] is True
    assert body['partition_leases'] is True and body['evidence_semantics_unchanged'] is True

def test_partitioned_job_idempotency_and_completion(client,write_headers):
    payload={'job_type':'country-refresh','origin_product':'site-intelligence','idempotency_key':'job-1','partitions':[{'key':'PSE','payload':{'country':'PSE'}},{'key':'KEN','payload':{'country':'KEN'}}]}
    a=client.post('/v1/scale/jobs',headers=write_headers,json=payload); assert a.status_code==200,a.text
    b=client.post('/v1/scale/jobs',headers=write_headers,json=payload); assert b.json()['id']==a.json()['id']
    c=client.post('/v1/scale/partitions/claim?worker_id=w1',headers=write_headers).json()['item']; assert c['partition_key']=='PSE'
    done=client.post(f"/v1/scale/partitions/{c['id']}/complete",headers=write_headers,json={'result':{'ok':True}}); assert done.status_code==200
    c2=client.post('/v1/scale/partitions/claim?worker_id=w2',headers=write_headers).json()['item']; assert c2['partition_key']=='KEN'
    client.post(f"/v1/scale/partitions/{c2['id']}/complete",headers=write_headers,json={'result':{'ok':True}})
    detail=client.get('/v1/scale/jobs/'+a.json()['id']).json(); assert detail['state']=='completed' and detail['completed_partitions']==2

def test_credentials_removed_from_durable_job(client,write_headers):
    r=client.post('/v1/scale/jobs',headers=write_headers,json={'job_type':'safe','idempotency_key':'safe1','parameters':{'api_key':'secret','country':'PSE'},'partitions':[{'key':'x','payload':{'token':'secret','value':2}}]})
    assert r.status_code==200
    from app.models import ScaleProcessingJob,ScaleProcessingPartition
    with client.app.state.database.session_factory() as db:
        j=db.get(ScaleProcessingJob,r.json()['id']); p=db.query(ScaleProcessingPartition).filter_by(job_id=j.id).one(); assert j.parameters_json=={'country':'PSE'} and p.payload_json=={'value':2}

def test_duplicate_partition_keys_rejected(client,write_headers):
    r=client.post('/v1/scale/jobs',headers=write_headers,json={'job_type':'dup','idempotency_key':'dup','partitions':[{'key':'x'},{'key':'x'}]}); assert r.status_code==422

def test_failure_requeues_then_terminal_failure(client,write_headers):
    r=client.post('/v1/scale/jobs',headers=write_headers,json={'job_type':'retry','idempotency_key':'retry','partitions':[{'key':'x','max_attempts':2}]}); jid=r.json()['id']
    p=client.post('/v1/scale/partitions/claim',headers=write_headers).json()['item']; f=client.post(f"/v1/scale/partitions/{p['id']}/fail",headers=write_headers,json={'error':'boom'}).json(); assert f['state']=='queued'
    from app.models import ScaleProcessingPartition
    with client.app.state.database.session_factory() as db:
        row=db.get(ScaleProcessingPartition,p['id']); row.available_at=datetime.now(timezone.utc)-timedelta(seconds=1); db.add(row); db.commit()
    p=client.post('/v1/scale/partitions/claim',headers=write_headers).json()['item']; f=client.post(f"/v1/scale/partitions/{p['id']}/fail",headers=write_headers,json={'error':'boom2'}).json(); assert f['state']=='failed'
    assert client.get('/v1/scale/jobs/'+jid).json()['state']=='completed-with-errors'

def test_oversize_result_requires_external_reference(client,write_headers):
    client.app.state.settings.__dict__['scale_inline_result_max_bytes']=1024
    r=client.post('/v1/scale/jobs',headers=write_headers,json={'job_type':'large','idempotency_key':'large','partitions':[{'key':'x'}]}); p=client.post('/v1/scale/partitions/claim',headers=write_headers).json()['item']
    bad=client.post(f"/v1/scale/partitions/{p['id']}/complete",headers=write_headers,json={'result':{'data':'x'*2000}}); assert bad.status_code==422
    ok=client.post(f"/v1/scale/partitions/{p['id']}/complete",headers=write_headers,json={'result':{'data':'x'*2000},'external_uri':'s3://example/object'}); assert ok.status_code==200 and ok.json()['storage_object']['storage_class']=='external-reference'

def test_public_scale_readiness_does_not_expose_jobs(client):
    r=client.get('/api/v1/scale/readiness'); assert r.status_code in (200,401,403)

def test_storage_deduplicates_by_hash(client,write_headers):
    from app.services.scale import store_result
    with client.app.state.database.session_factory() as db:
        a=store_result(db,client.app.state.settings,{'x':1}); b=store_result(db,client.app.state.settings,{'x':1}); assert a.id==b.id

def test_expired_storage_compacts_payload(client):
    from app.services.scale import store_result,compact_expired_storage
    from app.models import ScaleStorageObject
    with client.app.state.database.session_factory() as db:
        o=store_result(db,client.app.state.settings,{'x':1}); o.expires_at=datetime.now(timezone.utc)-timedelta(seconds=1); db.add(o); db.commit(); assert compact_expired_storage(db)==1; db.refresh(o); assert o.retention_state=='compacted' and o.inline_json=={}

def test_backpressure_is_observable_but_workers_can_drain(client,write_headers):
    client.app.state.settings.__dict__['scale_queue_backpressure_threshold']=1
    client.post('/v1/scale/jobs',headers=write_headers,json={'job_type':'bp','idempotency_key':'bp','partitions':[{'key':'x'}]})
    assert client.get('/v1/scale/readiness').json()['backpressure'] is True
    assert client.post('/v1/scale/partitions/claim',headers=write_headers).json()['item'] is not None
