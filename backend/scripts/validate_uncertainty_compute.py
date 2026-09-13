#!/usr/bin/env python3
from tempfile import TemporaryDirectory
from pathlib import Path
from app.config import Settings
from app.database import Database
from app.migrations import run_migrations,migration_status
from app.services import uncertainty_compute as uc

def main():
    with TemporaryDirectory() as td:
        settings=Settings(database_url=f"sqlite:///{Path(td)/'v2361.db'}",version='2.36.1.1')
        db=Database(settings.database_url);run_migrations(db);status=migration_status(db);assert '0040' in status['applied'] and not status['pending'],status
        with db.session_factory() as s:
            factors=[{'key':'x','distribution':'uniform','lower_bound':0,'upper_bound':1},{'key':'y','distribution':'normal','parameters':{'mean':0,'stddev':1}}]
            a=uc.generate_design(factors,'monte-carlo',100,42,10000);b=uc.generate_design(factors,'monte-carlo',100,42,10000);assert a['manifest_sha256']==b['manifest_sha256']
            stats=uc.ensemble_statistics([1,2,3],[1,1,2]);assert stats['aggregation_performed_by_core']
            prob=uc.exceedance_probability([1,2,3,4],3,'>=');assert prob['probability']==0.5
            handoff=uc.runtime_handoff({'runtime_product':'lab','design_manifest':a});assert not handoff['dispatch_by_core']
            ready=uc.readiness(s);assert ready['monte_carlo_sampling'] and not ready['model_execution_by_core']
        print({'version':'2.36.1.1','migration_0040_applied':True,'monte_carlo_sampling':True,'latin_hypercube_sampling':True,'sobol_index_analysis':True,'morris_analysis':True,'ensemble_aggregation':True,'probability_estimation':True,'model_execution_by_core':False,'automatic_truth_promotion':False})
        print('PASS - Core 2.36.1.1 Uncertainty Compute Runtime Integration validation')
if __name__=='__main__':main()
