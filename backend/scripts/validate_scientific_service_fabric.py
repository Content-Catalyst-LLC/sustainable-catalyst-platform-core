from __future__ import annotations
import sys
from pathlib import Path
BACKEND=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(BACKEND))
from app.config import Settings
from app.database import Database
from app.migrations import migration_status, run_migrations
from app.models import ScientificDataRecord
from app.services.scientific_service_fabric import DOMAINS, classify_record

def sample(**overrides):
    values=dict(id='sample',connector_id='nasa.cmr-collections',source_id='nasa-earthdata',raw_record_id=None,source_record_id='sample',record_type='earth_science_dataset',discipline='earth_science',title='Earth observation',summary=None,dataset_id=None,collection=None,mission=None,instrument=None,target='Earth',doi=None,access_url=None,landing_page_url=None,geometry_json=None,observation_start=None,observation_end=None,published_at=None,identifiers_json={},keywords_json=[],variables_json=[],file_formats_json=[],quality_status='source_reported',license_name=None,attribution=None,content_hash='x'*64,metadata_json={},public=True)
    values.update(overrides); return ScientificDataRecord(**values)

def main():
    settings=Settings.from_env(); db=Database(settings.database_url); run_migrations(db); status=migration_status(db)
    assert settings.version=='2.13.0'; assert '0016' in status['applied']; assert not status['pending']
    assert list(DOMAINS)==['earth','ocean','space']
    earth=classify_record(sample())
    ocean=classify_record(sample(id='ocean',connector_id='noaa.ncei-data',source_id='noaa-ncei',discipline='oceanography',title='Sea surface temperature',keywords_json=['ocean']))
    space=classify_record(sample(id='space',connector_id='mast.observations',source_id='mast',discipline='astronomy',title='JWST exoplanet observation',mission='JWST',keywords_json=['exoplanet']))
    assert earth and earth[0]['domain']=='earth'
    assert ocean and ocean[0]['domain']=='ocean'
    assert space and space[0]['domain']=='space'
    print({'version':settings.version,'migration_0016_applied':True,'pending_migrations':status['pending'],'domains':list(DOMAINS),'routing_only':True,'truth_precedence':'none','external_provider_health_release_blocking':False})
    print('PASS - Core v2.13.0 Earth Ocean Space scientific service fabric validation')
if __name__=='__main__': main()
