#!/usr/bin/env python3
from pathlib import Path
import ast
R=Path(__file__).resolve().parents[1]
cfg=(R/"backend/app/config.py").read_text(); assert 'version: str = "2.95.0"' in cfg; assert 'SustainableCatalystPlatformCore/2.95.0' in cfg; assert 'scholarly_interoperability_research_packaging_enabled: bool = True' in cfg; assert 'SC_CORE_SCHOLARLY_INTEROPERABILITY_RESEARCH_PACKAGING_ENABLED' in cfg
mtext=(R/"backend/app/migrations.py").read_text(); tree=ast.parse(mtext); migrations=None
for n in tree.body:
 if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='MIGRATIONS' for t in n.targets): migrations=ast.literal_eval(n.value); break
assert migrations and migrations[-1][0]=="0099"; assert len(migrations[-1][1])<=300
required=("backend/app/routers/scholarly_interoperability.py","backend/app/services/scholarly_interoperability.py","backend/tests/test_scholarly_interoperability_v2950.py","backend/tests/test_partial_0099_recovery_v2950.py","backend/scripts/validate_scholarly_interoperability.py","schemas/research-scholarly-interoperability-package-v1.schema.json","DEPLOY_PLATFORM_CORE_V2950_CONTABO.sh","PUSH_PLATFORM_CORE_V2950_FINAL.sh","PLATFORM_CORE_V2950_TERMINAL_COMMANDS.txt")
for f in required: assert (R/f).exists(),f
models=(R/"backend/app/models.py").read_text()
for table in ("scholarly_research_packages_v295","scholarly_package_members_v295","scholarly_citations_v295","scholarly_persistent_identifiers_v295","scholarly_dataset_descriptors_v295","scholarly_notebook_descriptors_v295","scholarly_provenance_manifests_v295","scholarly_metadata_profiles_v295","scholarly_export_profiles_v295","scholarly_publication_bindings_v295","scholarly_interoperability_validations_v295","scholarly_interoperability_revisions_v295","scholarly_interoperability_snapshots_v295"): assert table in models,table
svc=(R/"backend/app/services/scholarly_interoperability.py").read_text()
for invariant in ("mint_identifier_by_core","register_doi_by_core","submit_publication_by_core","publish_package_by_core","resolve_citations_by_core","execute_notebook_by_core","certify_reproducibility_by_core","validate_scientific_content_by_core","infer_authorship_by_core","determine_truth_by_core","interoperability_state_is_declared_not_certified"): assert invariant in svc,invariant
wp=(R/"wordpress-plugin/sustainable-catalyst-platform-core/sustainable-catalyst-platform-core.php").read_text(); assert "Version: 2.95.0" in wp; assert "SCPC_VERSION', '2.95.0'" in wp; assert "sc_platform_core_scholarly_interoperability_status" in wp
assert 'version = "2.95.0"' in (R/"backend/public_sdk/python/pyproject.toml").read_text(); assert '"version": "2.95.0"' in (R/"backend/public_sdk/javascript/package.json").read_text(); assert "scholarlyPackageBundle" in (R/"backend/public_sdk/javascript/index.mjs").read_text(); assert "scholarly_package_bundle" in (R/"backend/public_sdk/python/sc_platform_core_public/client.py").read_text()
print(f"PASS - dependency-free release contract; migration 0099 chars={len(migrations[-1][1])}")
print("PASS - v2.95.0 Scholarly Interoperability & Research Packaging release contract")
