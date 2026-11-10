from types import SimpleNamespace
import pytest
from fastapi import FastAPI,Depends
from fastapi.testclient import TestClient
from app.dependencies import require_read

def test_private_reads_require_valid_configured_service_key():
 app=FastAPI();app.state.settings=SimpleNamespace(public_reads=False,write_api_key='synthetic-service-key')
 @app.get('/private',dependencies=[Depends(require_read)])
 def private():return {'ok':True}
 client=TestClient(app)
 assert client.get('/private').status_code==403
 assert client.get('/private',headers={'X-SC-API-Key':'wrong'}).status_code==403
 assert client.get('/private',headers={b'X-SC-API-Key':b'\xff'}).status_code==403
 assert client.get('/private',headers={'X-SC-API-Key':'synthetic-service-key'}).status_code==200
 app.state.settings.write_api_key=''
 assert client.get('/private',headers={'X-SC-API-Key':'synthetic-service-key'}).status_code==403
 app.state.settings.public_reads=True
 assert client.get('/private').status_code==200
