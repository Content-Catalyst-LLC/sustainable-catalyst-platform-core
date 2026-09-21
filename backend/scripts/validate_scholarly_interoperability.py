#!/usr/bin/env python3
from app.database import Database
from app.migrations import run_migrations,migration_status
from app.services import scholarly_interoperability as svc
db=Database("sqlite:///:memory:"); run_migrations(db)
with db.session_factory() as s:
 r=svc.readiness(s); assert r["release"]=="2.95.0" and r["migration_0099_applied"] is True
 for k in ("scholarly_package_registry_by_core","citation_metadata_registry_by_core","persistent_identifier_registry_by_core","dataset_notebook_descriptor_registry_by_core","provenance_manifest_registry_by_core","metadata_export_profile_registry_by_core","publication_object_binding_registry_by_core","external_validation_evidence_registry_by_core","revision_history_by_core","immutable_interoperability_snapshots_by_core"): assert r[k] is True,k
 for k in ("mint_identifier_by_core","register_doi_by_core","submit_publication_by_core","publish_package_by_core","resolve_citations_by_core","fetch_external_artifacts_by_core","transform_dataset_by_core","execute_notebook_by_core","certify_reproducibility_by_core","validate_scientific_content_by_core","infer_authorship_by_core","determine_truth_by_core"): assert r[k] is False,k
assert migration_status(db)["pending"]==[]
print("PASS - v2.95.0 Scholarly Interoperability & Research Packaging invariants")
