from __future__ import annotations
from datetime import datetime
import hashlib, json
from sqlalchemy import func, select
from sqlalchemy.inspection import inspect as sa_inspect
from ..models import (ScholarlyResearchPackageRecord,ScholarlyPackageMemberRecord,ScholarlyCitationRecord,ScholarlyPersistentIdentifierRecord,ScholarlyDatasetDescriptorRecord,ScholarlyNotebookDescriptorRecord,ScholarlyProvenanceManifestRecord,ScholarlyMetadataProfileRecord,ScholarlyExportProfileRecord,ScholarlyPublicationBindingRecord,ScholarlyInteroperabilityValidationRecord,ScholarlyInteroperabilityRevisionRecord,ScholarlyInteroperabilitySnapshotRecord)
CONTRACT="sc.research.scholarly-interoperability-packaging.v1"
PACKAGE_TYPES={"scholarly_publication","research_compendium","replication_package","data_package","notebook_package","investigation_package","mixed_research_package","other"}
PACKAGE_PROFILES={"research-compendium","ro-crate","replication-package","data-package","notebook-package","scholarly-publication","investigation-package","custom"}
CITATION_FORMATS={"csl-json","bibtex","ris","citation-json","plain-text"}
IDENTIFIER_SCHEMES={"doi","orcid","ror","ark","handle","isbn","issn","url","urn","accession","internal"}
METADATA_STANDARDS={"datacite","crossref","dublin-core","schema.org","codemeta","ro-crate","custom"}
EXPORT_FORMATS={"zip","json","jsonld","csv","bibtex","ris","csl-json","ro-crate","pdf","html","custom"}
VISIBILITIES={"private","internal","public"}
FORBIDDEN={"mint_identifier_by_core","register_doi_by_core","submit_publication_by_core","publish_package_by_core","resolve_citations_by_core","fetch_external_artifacts_by_core","transform_dataset_by_core","execute_notebook_by_core","certify_reproducibility_by_core","validate_scientific_content_by_core","infer_authorship_by_core","determine_truth_by_core"}
CLASSES=[ScholarlyResearchPackageRecord,ScholarlyPackageMemberRecord,ScholarlyCitationRecord,ScholarlyPersistentIdentifierRecord,ScholarlyDatasetDescriptorRecord,ScholarlyNotebookDescriptorRecord,ScholarlyProvenanceManifestRecord,ScholarlyMetadataProfileRecord,ScholarlyExportProfileRecord,ScholarlyPublicationBindingRecord,ScholarlyInteroperabilityValidationRecord,ScholarlyInteroperabilityRevisionRecord,ScholarlyInteroperabilitySnapshotRecord]
COUNT_NAMES=["packages","members","citations","identifiers","datasets","notebooks","provenance_manifests","metadata_profiles","export_profiles","publication_bindings","validations","revisions","snapshots"]
def _ser(r):
 o={}
 for a in sa_inspect(r).mapper.column_attrs:
  v=getattr(r,a.key); o[a.key]=v.isoformat() if isinstance(v,datetime) else v
 for k in list(o):
  if k.endswith("_json"): o[k[:-5]]=o.pop(k)
 return o
def _hash(v): return hashlib.sha256(json.dumps(v,sort_keys=True,separators=(",",":"),default=str).encode()).hexdigest()
def _reject(p):
 bad=sorted(k for k in FORBIDDEN if p.get(k) not in (None,False))
 if bad: raise ValueError("Core records interoperability/package metadata; it does not mint/register identifiers, publish/submit packages, resolve citations, fetch/transform artifacts, execute notebooks, certify reproducibility, validate scientific content, infer authorship, or determine truth: "+", ".join(bad))
def _vis(p):
 v=p.get("visibility","internal")
 if v not in VISIBILITIES: raise ValueError("unsupported visibility")
 return v
def _get(db,cls,i,label):
 r=db.get(cls,i)
 if not r: raise ValueError(label+" not found")
 return r
def _rows(db,cls,project,public=False):
 q=select(cls).where(cls.project_ref==project)
 if public and hasattr(cls,"visibility"): q=q.where(cls.visibility=="public")
 return [_ser(x) for x in db.scalars(q.order_by(cls.created_at,cls.id)).all()]
def boundaries(): return {"scholarly_package_registry_by_core":True,"citation_metadata_registry_by_core":True,"persistent_identifier_registry_by_core":True,"dataset_notebook_descriptor_registry_by_core":True,"provenance_manifest_registry_by_core":True,"metadata_export_profile_registry_by_core":True,"publication_object_binding_registry_by_core":True,"external_validation_evidence_registry_by_core":True,"revision_history_by_core":True,"immutable_interoperability_snapshots_by_core":True,"interoperability_state_is_declared_not_certified":True,**{k:False for k in FORBIDDEN}}
def readiness(db):
 counts={n:db.scalar(select(func.count()).select_from(c)) or 0 for c,n in zip(CLASSES,COUNT_NAMES)}
 return {"release":"2.95.0","contract":CONTRACT,"package_types":sorted(PACKAGE_TYPES),"package_profiles":sorted(PACKAGE_PROFILES),"citation_formats":sorted(CITATION_FORMATS),"identifier_schemes":sorted(IDENTIFIER_SCHEMES),"metadata_standards":sorted(METADATA_STANDARDS),"export_formats":sorted(EXPORT_FORMATS),"counts":counts,"migration_0099_applied":True,**boundaries()}
def create_package(db,p):
 _reject(p); typ=p.get("package_type","research_compendium"); profile=p.get("package_profile","research-compendium")
 if typ not in PACKAGE_TYPES or profile not in PACKAGE_PROFILES: raise ValueError("unsupported package type/profile")
 r=ScholarlyResearchPackageRecord(package_key=p["package_key"],project_ref=p["project_ref"],package_type=typ,title=p["title"],description=p.get("description"),package_profile=profile,source_publication_ref=p.get("source_publication_ref"),source_reproducible_package_ref=p.get("source_reproducible_package_ref"),status=p.get("status","draft"),visibility=_vis(p),metadata_json=p.get("metadata",{}),provenance_json=p.get("provenance",{}),created_by=p.get("created_by","operator")); db.add(r); db.commit(); db.refresh(r); return _ser(r)
def add_member(db,p):
 _reject(p); _get(db,ScholarlyResearchPackageRecord,p["package_id"],"package"); r=ScholarlyPackageMemberRecord(member_key=p["member_key"],package_id=p["package_id"],project_ref=p["project_ref"],member_type=p["member_type"],object_ref=p["object_ref"],object_version_ref=p.get("object_version_ref"),content_hash=p.get("content_hash"),role=p.get("role","component"),required=bool(p.get("required",True)),visibility=_vis(p),metadata_json=p.get("metadata",{}),provenance_json=p.get("provenance",{})); db.add(r); db.commit(); db.refresh(r); return _ser(r)
def add_citation(db,p):
 _reject(p); _get(db,ScholarlyResearchPackageRecord,p["package_id"],"package"); fmt=p.get("citation_format","csl-json");
 if fmt not in CITATION_FORMATS: raise ValueError("unsupported citation format")
 r=ScholarlyCitationRecord(citation_key=p["citation_key"],package_id=p["package_id"],project_ref=p["project_ref"],cited_object_ref=p["cited_object_ref"],citation_format=fmt,locator=p.get("locator"),citation_text=p.get("citation_text"),citation_data_json=p.get("citation_data",{}),visibility=_vis(p),provenance_json=p.get("provenance",{})); db.add(r); db.commit(); db.refresh(r); return _ser(r)
def add_identifier(db,p):
 _reject(p); _get(db,ScholarlyResearchPackageRecord,p["package_id"],"package"); scheme=p["scheme"].lower();
 if scheme not in IDENTIFIER_SCHEMES: raise ValueError("unsupported identifier scheme")
 r=ScholarlyPersistentIdentifierRecord(identifier_key=p["identifier_key"],package_id=p["package_id"],project_ref=p["project_ref"],object_ref=p["object_ref"],scheme=scheme,identifier=p["identifier"],resolver_url=p.get("resolver_url"),status=p.get("status","declared"),visibility=_vis(p),provenance_json=p.get("provenance",{})); db.add(r); db.commit(); db.refresh(r); return _ser(r)
def add_dataset(db,p):
 _reject(p); _get(db,ScholarlyResearchPackageRecord,p["package_id"],"package"); r=ScholarlyDatasetDescriptorRecord(dataset_key=p["dataset_key"],package_id=p["package_id"],project_ref=p["project_ref"],dataset_ref=p["dataset_ref"],version_ref=p.get("version_ref"),content_hash=p.get("content_hash"),media_type=p.get("media_type"),schema_ref=p.get("schema_ref"),license_ref=p.get("license_ref"),metadata_json=p.get("metadata",{}),visibility=_vis(p)); db.add(r); db.commit(); db.refresh(r); return _ser(r)
def add_notebook(db,p):
 _reject(p); _get(db,ScholarlyResearchPackageRecord,p["package_id"],"package"); r=ScholarlyNotebookDescriptorRecord(notebook_key=p["notebook_key"],package_id=p["package_id"],project_ref=p["project_ref"],notebook_ref=p["notebook_ref"],notebook_format=p.get("notebook_format","ipynb"),version_ref=p.get("version_ref"),content_hash=p.get("content_hash"),environment_ref=p.get("environment_ref"),execution_ref=p.get("execution_ref"),metadata_json=p.get("metadata",{}),visibility=_vis(p)); db.add(r); db.commit(); db.refresh(r); return _ser(r)
def add_manifest(db,p):
 _reject(p); _get(db,ScholarlyResearchPackageRecord,p["package_id"],"package"); bindings=p.get("bindings",[]); r=ScholarlyProvenanceManifestRecord(manifest_key=p["manifest_key"],package_id=p["package_id"],project_ref=p["project_ref"],standard=p.get("standard","ro-crate"),standard_version=p.get("standard_version"),bindings_json=bindings,manifest_hash=_hash({"standard":p.get("standard","ro-crate"),"bindings":bindings}),visibility=_vis(p),provenance_json=p.get("provenance",{})); db.add(r); db.commit(); db.refresh(r); return _ser(r)
def add_metadata_profile(db,p):
 _reject(p); _get(db,ScholarlyResearchPackageRecord,p["package_id"],"package"); std=p["standard"]
 if std not in METADATA_STANDARDS: raise ValueError("unsupported metadata standard")
 r=ScholarlyMetadataProfileRecord(profile_key=p["profile_key"],package_id=p["package_id"],project_ref=p["project_ref"],standard=std,standard_version=p.get("standard_version"),metadata_json=p.get("metadata",{}),visibility=_vis(p)); db.add(r); db.commit(); db.refresh(r); return _ser(r)
def add_export_profile(db,p):
 _reject(p); _get(db,ScholarlyResearchPackageRecord,p["package_id"],"package"); fmt=p["export_format"]
 if fmt not in EXPORT_FORMATS: raise ValueError("unsupported export format")
 r=ScholarlyExportProfileRecord(export_key=p["export_key"],package_id=p["package_id"],project_ref=p["project_ref"],export_format=fmt,media_type=p.get("media_type"),profile=p.get("profile"),filename=p.get("filename"),spec_ref=p.get("spec_ref"),options_json=p.get("options",{}),visibility=_vis(p)); db.add(r); db.commit(); db.refresh(r); return _ser(r)
def bind_publication_object(db,p):
 _reject(p); _get(db,ScholarlyResearchPackageRecord,p["package_id"],"package"); r=ScholarlyPublicationBindingRecord(binding_key=p["binding_key"],package_id=p["package_id"],project_ref=p["project_ref"],publication_ref=p["publication_ref"],object_type=p["object_type"],object_ref=p["object_ref"],object_version_ref=p.get("object_version_ref"),role=p.get("role","supplement"),visibility=_vis(p),provenance_json=p.get("provenance",{})); db.add(r); db.commit(); db.refresh(r); return _ser(r)
def record_validation(db,p):
 _reject(p); _get(db,ScholarlyResearchPackageRecord,p["package_id"],"package"); r=ScholarlyInteroperabilityValidationRecord(validation_key=p["validation_key"],package_id=p["package_id"],project_ref=p["project_ref"],validator_ref=p["validator_ref"],validation_type=p["validation_type"],status=p.get("status","recorded"),evidence_json=p.get("evidence",[]),report_ref=p.get("report_ref"),visibility=_vis(p),provenance_json=p.get("provenance",{})); db.add(r); db.commit(); db.refresh(r); return _ser(r)
def revise(db,p):
 _reject(p); n=(db.scalar(select(func.max(ScholarlyInteroperabilityRevisionRecord.revision)).where(ScholarlyInteroperabilityRevisionRecord.project_ref==p["project_ref"])) or 0)+1; r=ScholarlyInteroperabilityRevisionRecord(project_ref=p["project_ref"],package_id=p.get("package_id"),revision=n,prior_state_json=p.get("prior_state",{}),revised_state_json=p.get("revised_state",{}),reason=p.get("reason"),created_by=p.get("created_by","operator")); db.add(r); db.commit(); db.refresh(r); return _ser(r)
def bundle(db,project,public=False):
 keys=["packages","members","citations","identifiers","datasets","notebooks","provenance_manifests","metadata_profiles","export_profiles","publication_bindings","validations"]
 data={k:_rows(db,c,project,public) for k,c in zip(keys,CLASSES[:11])}; data["revisions"]=[] if public else _rows(db,ScholarlyInteroperabilityRevisionRecord,project,False); data["snapshots"]=[] if public else _rows(db,ScholarlyInteroperabilitySnapshotRecord,project,False); data["contract"]=CONTRACT; data["release"]="2.95.0"; data["interoperability_state_is_declared_not_certified"]=True; return data
def snapshot(db,p):
 _reject(p); project=p["project_ref"]; state=bundle(db,project,False); state.pop("snapshots",None); rev=(db.scalar(select(func.max(ScholarlyInteroperabilitySnapshotRecord.revision)).where(ScholarlyInteroperabilitySnapshotRecord.project_ref==project)) or 0)+1; prev=db.scalar(select(ScholarlyInteroperabilitySnapshotRecord).where(ScholarlyInteroperabilitySnapshotRecord.project_ref==project).order_by(ScholarlyInteroperabilitySnapshotRecord.revision.desc()).limit(1)); h=_hash(state); r=ScholarlyInteroperabilitySnapshotRecord(project_ref=project,revision=rev,content_hash=h,previous_snapshot_hash=prev.content_hash if prev else None,state_json=state,provenance_json=p.get("provenance",{}),created_by=p.get("created_by","operator")); db.add(r); db.commit(); db.refresh(r); return _ser(r)
def summary(db,project,public=False):
 b=bundle(db,project,public); return {"release":"2.95.0","contract":CONTRACT,"project_ref":project,"counts":{k:len(v) for k,v in b.items() if isinstance(v,list)},"package_profiles":sorted({x["package_profile"] for x in b["packages"]}),"interoperability_state_is_declared_not_certified":True}
def lineage(db,project,public=False): return {"release":"2.95.0","contract":CONTRACT,"project_ref":project,"package_members":[{"package_id":x["package_id"],"object_ref":x["object_ref"],"version_ref":x.get("object_version_ref"),"content_hash":x.get("content_hash")} for x in bundle(db,project,public)["members"]],"provenance_manifests":bundle(db,project,public)["provenance_manifests"],"publication_bindings":bundle(db,project,public)["publication_bindings"],"lineage_is_declared_not_inferred":True}
