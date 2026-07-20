from __future__ import annotations
from dataclasses import replace
import httpx
from app.connectors.adapters import ADAPTERS
from app.migrations import MIGRATIONS
from app.services.live_data import LiveDataRuntime


def _public_key(client,write_headers):
    app=client.post('/v1/developer/applications',headers=write_headers,json={'name':'Economics Test','owner_name':'Tester','owner_email':'economics@example.com','organization':'Test','website_url':'https://example.com','use_case':'Read official economic records.','status':'approved','plan_id':'free','metadata':{},'actor':'admin'})
    issued=client.post(f"/v1/developer/applications/{app.json()['id']}/credentials",headers=write_headers,json={'label':'Economics','scopes':['data:read'],'created_by':'admin'})
    return issued.json()['api_key']


def test_v273_catalog_migration_and_adapters(client):
    sources=client.get('/v1/live/sources').json(); connectors=client.get('/v1/live/connectors').json()
    assert len(sources)==40; assert len(connectors)==39
    assert {'imf','oecd','eurostat','ecb','bis','bea','bls','census','sec-edgar','eia','faostat','ilostat'} <= {x['id'] for x in sources}
    assert {'imf.sdmx','oecd.sdmx','eurostat.statistics','ecb.sdmx','bis.sdmx','bea.statistics','bls.timeseries','census.data','sec.companyfacts','eia.v2-data','faostat.data','ilostat.sdmx'} <= {x['id'] for x in connectors}
    assert {'sdmx_csv_observations_v1','eurostat_jsonstat_v1','bea_data_v1','bls_series_v2','census_data_v1','sec_companyfacts_v1','eia_v2_data_v1','faostat_data_v1'} <= set(ADAPTERS)
    assert any(v=='0010' for v,_ in MIGRATIONS)


def test_oecd_sdmx_ingestion_and_economic_provenance(client,write_headers):
    csv_data='REF_AREA,Reference area,FREQ,MEASURE,MEASURE_LABEL,UNIT_MEASURE,TIME_PERIOD,OBS_VALUE\nUSA,United States,A,GDP,Gross domestic product,USD,2025,29184.9\n'
    async def handler(request:httpx.Request):
        assert request.url.host=='sdmx.oecd.org'; assert 'OECD.SDD.NAD,DSD_TEST@DF_TEST' in str(request.url)
        return httpx.Response(200,text=csv_data,headers={'content-type':'text/csv'})
    client.app.state.live_data_runtime=LiveDataRuntime(client.app.state.settings,transport=httpx.MockTransport(handler))
    result=client.post('/v1/live/connectors/oecd.sdmx/ingest',headers=write_headers,json={'parameters':{'agency':'OECD.SDD.NAD','dataset':'DSD_TEST@DF_TEST','key':'USA.A.GDP','startPeriod':'2025'},'requested_by':'pytest'})
    assert result.status_code==200,result.text; assert result.json()['details']['economic_data_records_created']==1
    records=client.get('/v1/economics/records?indicator_code=GDP').json(); assert records['total']==1
    record=records['items'][0]; assert record['geography_code']=='USA'; assert record['value_number']==29184.9
    prov=client.get(f"/v1/economics/provenance/{record['id']}").json(); assert prov['source']['id']=='oecd'; assert prov['connector']['id']=='oecd.sdmx'


def test_bls_census_and_sec_adapters(client,write_headers):
    async def handler(request:httpx.Request):
        if request.url.host=='api.bls.gov':
            return httpx.Response(200,json={'status':'REQUEST_SUCCEEDED','Results':{'series':[{'seriesID':'CUUR0000SA0','catalog':{'series_title':'Consumer Price Index','area_name':'U.S. city average','measure_data_type':'Index'},'data':[{'year':'2026','period':'M06','periodName':'June','value':'321.5','footnotes':[]}]}]}})
        if request.url.host=='api.census.gov':
            return httpx.Response(200,json=[['NAME','B01003_001E','state'],['Illinois','12800000','17']])
        if request.url.host=='data.sec.gov':
            return httpx.Response(200,json={'cik':320193,'entityName':'Apple Inc.','facts':{'us-gaap':{'Assets':{'label':'Assets','description':'Total assets','units':{'USD':[{'val':365725000000,'fy':2025,'fp':'FY','form':'10-K','filed':'2025-10-31','end':'2025-09-27','accn':'0000320193-25-000079'}]}}}}})
        raise AssertionError(str(request.url))
    client.app.state.live_data_runtime=LiveDataRuntime(client.app.state.settings,transport=httpx.MockTransport(handler))
    bls=client.post('/v1/live/connectors/bls.timeseries/ingest',headers=write_headers,json={'parameters':{'series_ids':['CUUR0000SA0'],'startyear':'2026','endyear':'2026'},'requested_by':'pytest'}); assert bls.status_code==200,bls.text
    census=client.post('/v1/live/connectors/census.data/ingest',headers=write_headers,json={'parameters':{'year':'2024','dataset':'acs/acs5','get':'NAME,B01003_001E','for':'state:*'},'requested_by':'pytest'}); assert census.status_code==200,census.text
    sec=client.post('/v1/live/connectors/sec.companyfacts/ingest',headers=write_headers,json={'parameters':{'cik':'320193','tags':['Assets']},'requested_by':'pytest'}); assert sec.status_code==200,sec.text
    stats=client.get('/v1/economics/stats').json(); assert stats['by_record_type']['labour_statistic']==1; assert stats['by_record_type']['demographic_statistic']==1; assert stats['by_record_type']['company_filing_fact']==1


def test_registration_gates_health_meta_and_public_api(client,write_headers):
    health=client.get('/v1/live/connectors/health').json(); statuses={x['id']:x['configuration_status'] for x in health['connectors']}
    assert statuses['imf.sdmx']=='endpoint_registration_required'; assert statuses['bea.statistics']=='credential_required'; assert statuses['eia.v2-data']=='credential_required'
    assert client.post('/v1/live/connectors/eia.v2-data/ingest',headers=write_headers,json={'parameters':{'route':'electricity/rto/region-data','data_fields':['value']},'requested_by':'pytest'}).status_code==503
    meta=client.get('/v1/meta').json(); assert 'economic_data_record_store' in meta['capabilities']; assert 'sdmx_statistics_gateway' in meta['capabilities']
    health_root=client.get('/health').json(); assert health_root['version']=='2.8.0'; assert health_root['economics_official_statistics_connector_pack'] is True
    stats=client.get('/v1/stats').json(); assert stats['live_data_sources']==40; assert stats['live_data_connectors']==39; assert stats['economic_data_records']==0
    key=_public_key(client,write_headers); public=client.get('/api/v1/economics/record-types',headers={'Authorization':f'Bearer {key}'}); assert public.status_code==200; assert 'macroeconomic_indicator' in public.json()['data']


def test_eia_and_bea_with_free_keys(client,write_headers):
    settings=replace(client.app.state.settings,eia_api_key='free-eia-key',bea_api_key='free-bea-key',census_api_key='free-census-key',bls_registration_key='free-bls-key')
    async def handler(request:httpx.Request):
        if request.url.host=='api.eia.gov': return httpx.Response(200,json={'response':{'data':[{'period':'2026-06','state':'IL','generation':1234.5,'generation-units':'megawatthours'}]}})
        if request.url.host=='apps.bea.gov': return httpx.Response(200,json={'BEAAPI':{'Results':{'Data':[{'TimePeriod':'2025','DataValue':'30507.2','LineDescription':'Gross domestic product','GeoFIPS':'00000','GeoName':'United States','UNIT_MULT':'Billions of dollars'}]}}})
        raise AssertionError(str(request.url))
    client.app.state.live_data_runtime=LiveDataRuntime(settings,transport=httpx.MockTransport(handler))
    eia=client.post('/v1/live/connectors/eia.v2-data/ingest',headers=write_headers,json={'parameters':{'route':'electricity/state-electricity-profiles/summary','data_fields':['generation']},'requested_by':'pytest'}); assert eia.status_code==200,eia.text
    bea=client.post('/v1/live/connectors/bea.statistics/ingest',headers=write_headers,json={'parameters':{'dataset_name':'NIPA','TableName':'T10101','Frequency':'A','Year':'2025'},'requested_by':'pytest'}); assert bea.status_code==200,bea.text
    energy = client.get('/v1/economics/records?record_type=energy_statistic').json()
    macro = client.get('/v1/economics/records?record_type=macroeconomic_indicator').json()
    assert energy['total']==1
    assert macro['total']==1
    assert 'free-eia-key' not in energy['items'][0]['source_url']
    assert 'free-bea-key' not in macro['items'][0]['source_url']


def test_public_sdk_economic_methods():
    from sc_platform_core_public.client import PublicApiClient
    assert callable(getattr(PublicApiClient,'economic_records')); assert callable(getattr(PublicApiClient,'economic_record')); assert callable(getattr(PublicApiClient,'economic_record_types'))


def test_public_python_sdk_uses_scoped_economics_paths(monkeypatch):
    from sc_platform_core_public.client import PublicApiClient
    calls = []

    class Response:
        is_error = False
        def json(self):
            return {"data": []}

    def fake_request(method, url, **kwargs):
        calls.append((method, url, kwargs))
        return Response()

    monkeypatch.setattr(httpx, "request", fake_request)
    sdk = PublicApiClient("https://core.example", "test-key")
    sdk.economic_records(indicator_code="GDP")
    sdk.economic_record("record-id")
    sdk.economic_record_types()
    assert calls[0][1] == "https://core.example/api/v1/economics/records"
    assert calls[0][2]["params"] == {"indicator_code": "GDP"}
    assert calls[1][1].endswith("/api/v1/economics/records/record-id")
    assert calls[2][1].endswith("/api/v1/economics/record-types")


def test_ingestion_parameters_are_redacted(client, write_headers):
    async def handler(request: httpx.Request):
        return httpx.Response(200, text='REF_AREA,FREQ,MEASURE,TIME_PERIOD,OBS_VALUE\nUSA,A,GDP,2025,1\n', headers={'content-type': 'text/csv'})
    client.app.state.live_data_runtime = LiveDataRuntime(client.app.state.settings, transport=httpx.MockTransport(handler))
    response = client.post('/v1/live/connectors/oecd.sdmx/ingest', headers=write_headers, json={
        'parameters': {'agency': 'OECD', 'dataset': 'TEST', 'key': 'USA.A.GDP', 'api_token': 'must-not-persist'},
        'requested_by': 'pytest',
    })
    assert response.status_code == 200
    run = response.json()
    assert run['parameters']['api_token'] == '[redacted]'
    assert run['parameters']['key'] == 'USA.A.GDP'
