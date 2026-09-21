export class PublicApiError extends Error {}

export class PublicApiClient {
  constructor(baseUrl, apiKey) {
    this.baseUrl = baseUrl.replace(/\/$/, "");
    this.apiKey = apiKey;
  }

  async request(path, options = {}) {
    const response = await fetch(`${this.baseUrl}/api/v1${path}`, {
      ...options,
      headers: {
        Accept: "application/json",
        Authorization: `Bearer ${this.apiKey}`,
        ...(options.headers || {}),
      },
    });
    if (!response.ok) {
      throw new PublicApiError(`${response.status}: ${await response.text()}`);
    }
    const payload = await response.json();
    return payload.data;
  }

  async requestRaw(path, options = {}) {
    const response = await fetch(`${this.baseUrl}/api/v1${path}`, {
      ...options,
      headers: {
        Accept: "application/json",
        Authorization: `Bearer ${this.apiKey}`,
        ...(options.headers || {}),
      },
    });
    if (!response.ok) {
      throw new PublicApiError(`${response.status}: ${await response.text()}`);
    }
    return response.json();
  }

  status() {
    return this.request("/status");
  }

  entities(params = {}) {
    const query = new URLSearchParams(params);
    return this.request(`/entities?${query}`);
  }

  entity(entityId) {
    return this.request(`/entities/${encodeURIComponent(entityId)}`);
  }

  graph(entityId, params = {}) {
    const query = new URLSearchParams(params);
    return this.request(`/graph/${encodeURIComponent(entityId)}?${query}`);
  }

  claims(params = {}) {
    const query = new URLSearchParams(params);
    return this.request(`/claims?${query}`);
  }

  evidenceManifest(claimId) {
    return this.request(`/evidence/manifests/${encodeURIComponent(claimId)}`);
  }

  verifyLedger() {
    return this.request("/ledger/verify");
  }

  trustStatus() {
    return this.request("/trust/status");
  }

  trustEvaluations(params = {}) {
    const query = new URLSearchParams(params);
    return this.request(`/trust/evaluations?${query}`);
  }

  trustIncidents(includeResolved = false) {
    return this.request(`/trust/incidents?include_resolved=${includeResolved}`);
  }

  trustLimitations(includeRetired = false) {
    return this.request(`/trust/limitations?include_retired=${includeRetired}`);
  }

  trustAttestations() {
    return this.request("/trust/attestations");
  }

  workflowDefinitions() {
    return this.request("/workflow-definitions");
  }

  workflowRun(runId) {
    return this.request(`/workflow-runs/${encodeURIComponent(runId)}`);
  }

  dossiers(params = {}) {
    const query = new URLSearchParams(params);
    return this.request(`/dossiers?${query}`);
  }

  dossier(dossierId) {
    return this.request(`/dossiers/${encodeURIComponent(dossierId)}`);
  }

  verifyDossier(dossierId) {
    return this.request(`/dossiers/${encodeURIComponent(dossierId)}/verify`);
  }

  liveSources() {
    return this.request("/live/sources");
  }

  liveConnectors(params = {}) {
    const query = new URLSearchParams(params);
    return this.request(`/live/connectors?${query}`);
  }

  liveObservations(params = {}) {
    const query = new URLSearchParams(params);
    return this.request(`/live/observations/latest?${query}`);
  }

  liveTimeseries(metric, params = {}) {
    const query = new URLSearchParams({ metric, ...params });
    return this.request(`/live/timeseries?${query}`);
  }

  liveProvenance(observationId) {
    return this.request(`/live/provenance/${encodeURIComponent(observationId)}`);
  }

  internationalLawRecords(params = {}) {
    const query = new URLSearchParams(params);
    return this.request(`/international-law/records?${query}`);
  }

  internationalLawRecord(recordId) {
    return this.request(`/international-law/records/${encodeURIComponent(recordId)}`);
  }

  internationalLawAuthorityTaxonomy() {
    return this.request("/international-law/authority-taxonomy");
  }

  scientificRecords(params = {}) {
    const query = new URLSearchParams(params);
    return this.request(`/science/records?${query}`);
  }

  scientificRecord(recordId) {
    return this.request(`/science/records/${encodeURIComponent(recordId)}`);
  }

  scientificRecordTypes() {
    return this.request("/science/record-types");
  }

  identity() {
    return this.request("/developer/me");
  }

  usage(days = 30) {
    return this.request(`/developer/usage?days=${days}`);
  }
  economicRecords(params = {}) {
    const query = new URLSearchParams(params);
    return this.request(`/economics/records?${query}`);
  }

  economicRecord(recordId) {
    return this.request(`/economics/records/${encodeURIComponent(recordId)}`);
  }

  economicRecordTypes() {
    return this.request('/economics/record-types');
  }

  fabricCapabilities() {
    return this.request("/fabric/capabilities");
  }

  geospatialFeatures(params = {}) {
    const query = new URLSearchParams(params);
    return this.request(`/fabric/features?${query}`);
  }

  timeSeries(params = {}) {
    const query = new URLSearchParams(params);
    return this.request(`/fabric/timeseries?${query}`);
  }

  timeSeriesPoints(seriesId, params = {}) {
    const query = new URLSearchParams(params);
    return this.request(`/fabric/timeseries/${encodeURIComponent(seriesId)}/points?${query}`);
  }

  scientificAssets(params = {}) {
    const query = new URLSearchParams(params);
    return this.request(`/fabric/assets?${query}`);
  }

  mapLayers(params = {}) {
    const query = new URLSearchParams(params);
    return this.request(`/fabric/map-layers?${query}`);
  }

  stacCatalog() {
    return this.requestRaw("/stac");
  }

  stacCollections(params = {}) {
    const query = new URLSearchParams(params);
    return this.requestRaw(`/stac/collections?${query}`);
  }

  stacSearch(params = {}) {
    const query = new URLSearchParams(params);
    return this.requestRaw(`/stac/search?${query}`);
  }

  reliabilityStreamUrl(params = {}) {
    const query = new URLSearchParams({ after_id: 0, once: false, ...params });
    return `${this.baseUrl}/api/v1/reliability/stream?${query}`;
  }

  facilities(params = {}) {
    const clean = Object.fromEntries(Object.entries(params).filter(([, value]) => value !== null && value !== undefined));
    const query = new URLSearchParams(clean);
    return this.request(`/facilities?${query}`);
  }

  facility(facilityId) {
    return this.request(`/facilities/${encodeURIComponent(facilityId)}`);
  }

  facilityObservations(facilityId, params = {}) {
    const clean = Object.fromEntries(Object.entries(params).filter(([, value]) => value !== null && value !== undefined));
    const query = new URLSearchParams(clean);
    return this.request(`/facilities/${encodeURIComponent(facilityId)}/observations?${query}`);
  }

  humanitarianConditions(params = {}) {
    const clean = Object.fromEntries(Object.entries(params).filter(([, value]) => value !== null && value !== undefined));
    const query = new URLSearchParams(clean);
    return this.request(`/humanitarian/conditions?${query}`);
  }

  humanitarianCountrySummary(countryCode) {
    return this.request(`/humanitarian/country/${encodeURIComponent(countryCode)}/summary`);
  }

  countryEvidenceFederation(countryCode) {
    return this.request(`/country-evidence/country/${encodeURIComponent(countryCode)}/federation`);
  }

  countryEvidenceReconcile(countryCode, concept) {
    const query = new URLSearchParams({ concept });
    return this.request(`/country-evidence/country/${encodeURIComponent(countryCode)}/reconcile?${query}`);
  }

  scientificDomains() {
    return this.request(`/scientific-fabric/domains`);
  }

  scientificDomain(domain) {
    return this.request(`/scientific-fabric/domains/${encodeURIComponent(domain)}`);
  }

  scientificDomainRecords(domain, params = {}) {
    const query = new URLSearchParams(params);
    return this.request(`/scientific-fabric/domains/${encodeURIComponent(domain)}/records?${query}`);
  }

  scientificDomainAssets(domain, params = {}) {
    const query = new URLSearchParams(params);
    return this.request(`/scientific-fabric/domains/${encodeURIComponent(domain)}/assets?${query}`);
  }

  scientificDomainTimeSeries(domain, params = {}) {
    const query = new URLSearchParams(params);
    return this.request(`/scientific-fabric/domains/${encodeURIComponent(domain)}/timeseries?${query}`);
  }

  scientificDomainMapLayers(domain, params = {}) {
    const query = new URLSearchParams(params);
    return this.request(`/scientific-fabric/domains/${encodeURIComponent(domain)}/map-layers?${query}`);
  }

  crossProductExchangeReadiness() {
    return this.request(`/exchange/readiness`);
  }

  scaleReadiness() {
    return this.request(`/scale/readiness`);
  }

  governanceReadiness() {
    return this.request(`/governance/readiness`);
  }

  certificationReadiness() {
    return this.request(`/certification/readiness`);
  }


  observabilityStatus() {
    return this.request(`/observability/status`);
  }


  operationsStatus() {
    return this.request(`/operations/status`);
  }

  continuityStatus() {
    return this.request(`/continuity/status`);
  }

  resilienceStatus() {
    return this.request(`/resilience/status`);
  }
  lifecycleStatus() {
    return this.request(`/lifecycle/status`);
  }

  federationStatus() {
    return this.request(`/federation/status`);
  }

  capacityStatus() {
    return this.request(`/capacity/status`);
  }

  credentialLifecycleStatus() {
    return this.request(`/credentials/status`);
  }


  workloadGovernanceStatus() {
    return this.request(`/workload-governance/status`);
  }

  scientificObjectStorageReadiness() {
    return this.request("/scientific-objects/readiness");
  }

  scientificStoredObjects(params = {}) {
    const clean = Object.fromEntries(Object.entries(params).filter(([, value]) => value !== null && value !== undefined));
    const query = new URLSearchParams(clean);
    return this.request(`/scientific-objects?${query}`);
  }

  scientificStoredObject(objectId) {
    return this.request(`/scientific-objects/${encodeURIComponent(objectId)}`);
  }

  scientificProcessingAdapters() {
    return this.request("/scientific-objects/adapters");
  }

  researchObjectReadiness() {
    return this.request("/research-objects/readiness");
  }

  researchObjects(params = {}) {
    const clean = Object.fromEntries(Object.entries(params).filter(([, value]) => value !== null && value !== undefined));
    const query = new URLSearchParams(clean);
    return this.request(`/research-objects?${query}`);
  }

  researchObject(entityId) {
    return this.request(`/research-objects/${encodeURIComponent(entityId)}`);
  }

  researchProjectBundle(projectEntityId) {
    return this.request(`/research-objects/projects/${encodeURIComponent(projectEntityId)}/bundle`);
  }

  visualReasoningReadiness() {
    return this.request("/visual-reasoning/readiness");
  }

  visualReasoningObjects(params = {}) {
    const clean = Object.fromEntries(Object.entries(params).filter(([, value]) => value !== null && value !== undefined));
    const query = new URLSearchParams(clean);
    return this.request(`/visual-reasoning/objects?${query}`);
  }

  visualReasoningObject(entityId) {
    return this.request(`/visual-reasoning/objects/${encodeURIComponent(entityId)}`);
  }

  visualReasoningBundle(entityId) {
    return this.request(`/visual-reasoning/objects/${encodeURIComponent(entityId)}/bundle`);
  }

  visualizationReadiness() {
    return this.request("/visualization/readiness");
  }

  visualizationRenderers() {
    return this.request("/visualization/renderers");
  }

  visualizationSpecifications(params = {}) {
    const clean = Object.fromEntries(Object.entries(params).filter(([, value]) => value !== null && value !== undefined));
    const query = new URLSearchParams(clean);
    return this.request(`/visualization/specifications?${query}`);
  }


  systemMapsReadiness() { return this.request("/system-maps/readiness"); }
  systemMaps(params = {}) { const clean = Object.fromEntries(Object.entries(params).filter(([, value]) => value !== null && value !== undefined)); const query = new URLSearchParams(clean); return this.request(`/system-maps?${query}`); }
  systemMap(entityId) { return this.request(`/system-maps/${encodeURIComponent(entityId)}`); }
  systemMapBundle(entityId) { return this.request(`/system-maps/${encodeURIComponent(entityId)}/bundle`); }


  flowMapsReadiness() { return this.request("/flow-maps/readiness"); }
  flowMaps(params = {}) { const clean = Object.fromEntries(Object.entries(params).filter(([, value]) => value !== null && value !== undefined)); const query = new URLSearchParams(clean); return this.request(`/flow-maps?${query}`); }
  flowMap(entityId) { return this.request(`/flow-maps/${encodeURIComponent(entityId)}`); }
  flowMapBundle(entityId) { return this.request(`/flow-maps/${encodeURIComponent(entityId)}/bundle`); }
  flowMapBalance(entityId) { return this.request(`/flow-maps/${encodeURIComponent(entityId)}/balance`); }

  scenarioLandscapesReadiness() { return this.request("/scenario-landscapes/readiness"); }
  scenarioLandscapes(params = {}) { const clean = Object.fromEntries(Object.entries(params).filter(([, value]) => value !== null && value !== undefined)); const query = new URLSearchParams(clean); return this.request(`/scenario-landscapes?${query}`); }
  scenarioLandscape(entityId) { return this.request(`/scenario-landscapes/${encodeURIComponent(entityId)}`); }
  scenarioLandscapeBundle(entityId) { return this.request(`/scenario-landscapes/${encodeURIComponent(entityId)}/bundle`); }
  scenarioLandscapeComparison(entityId) { return this.request(`/scenario-landscapes/${encodeURIComponent(entityId)}/comparison`); }

  modelCanvasesReadiness() { return this.request("/model-canvases/readiness"); }
  modelCanvases(params = {}) { const clean = Object.fromEntries(Object.entries(params).filter(([, value]) => value !== null && value !== undefined)); const query = new URLSearchParams(clean); return this.request(`/model-canvases?${query}`); }
  modelCanvas(entityId) { return this.request(`/model-canvases/${encodeURIComponent(entityId)}`); }
  modelCanvasBundle(entityId) { return this.request(`/model-canvases/${encodeURIComponent(entityId)}/bundle`); }

  scenarioComputeReadiness() { return this.request("/scenario-compute/readiness"); }
  scenarioComputePlans(params = {}) { const clean = Object.fromEntries(Object.entries(params).filter(([, value]) => value !== null && value !== undefined)); const query = new URLSearchParams(clean); return this.request(`/scenario-compute/plans?${query}`); }
  scenarioComputePlan(planId) { return this.request(`/scenario-compute/plans/${encodeURIComponent(planId)}`); }
  scenarioComputePlanBundle(planId) { return this.request(`/scenario-compute/plans/${encodeURIComponent(planId)}/bundle`); }

  uncertaintyReasoningReadiness() { return this.request("/uncertainty-reasoning/readiness"); }
  uncertaintyDefinitions(params = {}) { const clean = Object.fromEntries(Object.entries(params).filter(([, value]) => value !== null && value !== undefined)); const query = new URLSearchParams(clean); return this.request(`/uncertainty-reasoning/uncertainties?${query}`); }
  sensitivityStudies(params = {}) { const clean = Object.fromEntries(Object.entries(params).filter(([, value]) => value !== null && value !== undefined)); const query = new URLSearchParams(clean); return this.request(`/uncertainty-reasoning/sensitivity-studies?${query}`); }
  sensitivityStudySummary(studyId) { return this.request(`/uncertainty-reasoning/sensitivity-studies/${encodeURIComponent(studyId)}/summary`); }
  ensembles(params = {}) { const clean = Object.fromEntries(Object.entries(params).filter(([, value]) => value !== null && value !== undefined)); const query = new URLSearchParams(clean); return this.request(`/uncertainty-reasoning/ensembles?${query}`); }
  ensembleSummary(ensembleId) { return this.request(`/uncertainty-reasoning/ensembles/${encodeURIComponent(ensembleId)}/summary`); }


  uncertaintyComputeReadiness() { return this.request("/uncertainty-compute/readiness"); }

  causalSystemsReadiness() { return this.request("/causal-systems/readiness"); }
  causalSystemsGraphs(params = {}) { const clean = Object.fromEntries(Object.entries(params).filter(([, value]) => value !== null && value !== undefined)); const query = new URLSearchParams(clean); return this.request(`/causal-systems/graphs?${query}`); }
  causalSystemsBundle(graphId) { return this.request(`/causal-systems/graphs/${encodeURIComponent(graphId)}/bundle`); }

  spatialTemporalReadiness() { return this.request("/spatial-temporal/readiness"); }
  spatialTemporalScenes(params = {}) { const clean = Object.fromEntries(Object.entries(params).filter(([, value]) => value !== null && value !== undefined)); const query = new URLSearchParams(clean); return this.request(`/spatial-temporal/scenes?${query}`); }
  spatialTemporalBundle(sceneId) { return this.request(`/spatial-temporal/scenes/${encodeURIComponent(sceneId)}/bundle`); }

  researchVisualExplanationsReadiness() { return this.request("/research-visual-explanations/readiness"); }
  researchVisualExplanations(params = {}) { const clean = Object.fromEntries(Object.entries(params).filter(([, value]) => value !== null && value !== undefined)); const query = new URLSearchParams(clean); return this.request(`/research-visual-explanations?${query}`); }
  researchVisualExplanationBundle(explanationId) { return this.request(`/research-visual-explanations/${encodeURIComponent(explanationId)}/bundle`); }

  crossProductVisualResearchReadiness() { return this.request("/cross-product-visual-research/readiness"); }
  crossProductVisualResearchObjects(params = {}) { const clean = Object.fromEntries(Object.entries(params).filter(([, value]) => value !== null && value !== undefined)); const query = new URLSearchParams(clean); return this.request(`/cross-product-visual-research?${query}`); }
  crossProductVisualResearchBundle(objectId) { return this.request(`/cross-product-visual-research/${encodeURIComponent(objectId)}/bundle`); }

}


PublicApiClient.prototype.reproducibleVisualKnowledgeReadiness = function () { return this.request("/reproducible-visual-knowledge/readiness"); };
PublicApiClient.prototype.reproducibleVisualKnowledgePackages = function (params = {}) { const query = new URLSearchParams(params); return this.request(`/reproducible-visual-knowledge?${query}`); };
PublicApiClient.prototype.reproducibleVisualKnowledgeBundle = function (packageId) { return this.request(`/reproducible-visual-knowledge/${encodeURIComponent(packageId)}/bundle`); };


// v2.43.0 Open Forensics — Evidence Integrity & Chain of Custody.
PublicApiClient.prototype.openForensicsReadiness = function () { return this.request("/open-forensics/readiness"); };
PublicApiClient.prototype.openForensicsInvestigations = function (params = {}) { const query = new URLSearchParams(params); return this.request(`/open-forensics/investigations?${query}`); };
PublicApiClient.prototype.openForensicsInvestigationBundle = function (investigationId) { return this.request(`/open-forensics/investigations/${encodeURIComponent(investigationId)}/bundle`); };

PublicApiClient.prototype.openForensicsCustodyChain = function (investigationId, evidenceId) { return this.request(`/open-forensics/investigations/${encodeURIComponent(investigationId)}/evidence/${encodeURIComponent(evidenceId)}/custody-chain`); };
PublicApiClient.prototype.openForensicsCustodyBundle = function (investigationId) { return this.request(`/open-forensics/investigations/${encodeURIComponent(investigationId)}/custody-bundle`); };


// v2.44.0 Open Forensics — Claims, Contradictions & Competing Hypotheses.
PublicApiClient.prototype.openForensicsClaimMap = function (investigationId) { return this.request(`/open-forensics/investigations/${encodeURIComponent(investigationId)}/claim-map`); };
PublicApiClient.prototype.openForensicsHypothesisMatrix = function (investigationId) { return this.request(`/open-forensics/investigations/${encodeURIComponent(investigationId)}/hypothesis-matrix`); };
PublicApiClient.prototype.openForensicsReasoningBundle = function (investigationId) { return this.request(`/open-forensics/investigations/${encodeURIComponent(investigationId)}/reasoning-bundle`); };


// v2.45.0 Open Forensics — Forensic Timeline & Event Reconstruction.
PublicApiClient.prototype.openForensicsTimeline = function (investigationId) { return this.request(`/open-forensics/investigations/${encodeURIComponent(investigationId)}/timeline`); };
PublicApiClient.prototype.openForensicsTimelineSpecification = function (investigationId) { return this.request(`/open-forensics/investigations/${encodeURIComponent(investigationId)}/timeline-specification`); };


// v2.46.0 Open Forensics — Forensic Spatial/Temporal Evidence Integration.
PublicApiClient.prototype.openForensicsSpatialTemporalEvidence = function (investigationId) { return this.request(`/open-forensics/investigations/${encodeURIComponent(investigationId)}/spatial-temporal-evidence`); };
PublicApiClient.prototype.openForensicsForensicSceneSpecification = function (investigationId) { return this.request(`/open-forensics/investigations/${encodeURIComponent(investigationId)}/forensic-scene-specification`); };
PublicApiClient.prototype.openForensicsSiteIntelligenceHandoff = function (investigationId) { return this.request(`/open-forensics/investigations/${encodeURIComponent(investigationId)}/site-intelligence-handoff`); };

// v2.47.0 Open Forensics — Media Artifact & Derivative Provenance.
PublicApiClient.prototype.openForensicsMediaProvenance = function (investigationId) { return this.request(`/open-forensics/investigations/${encodeURIComponent(investigationId)}/media-provenance`); };
PublicApiClient.prototype.openForensicsMediaLineageGraph = function (investigationId) { return this.request(`/open-forensics/investigations/${encodeURIComponent(investigationId)}/media-lineage-graph`); };
PublicApiClient.prototype.openForensicsMediaComparisonBundle = function (investigationId) { return this.request(`/open-forensics/investigations/${encodeURIComponent(investigationId)}/media-comparison-bundle`); };


// v2.48.0 Open Forensics — Quantitative Reconstruction & Reproduction Handoffs.
PublicApiClient.prototype.openForensicsQuantitativeReconstructions = function (investigationId) { return this.request(`/open-forensics/investigations/${encodeURIComponent(investigationId)}/quantitative-reconstructions`); };


PublicApiClient.prototype.openForensicsDocumentaryEvidence = function (investigationId) {
  return this.get(`/api/v1/open-forensics/investigations/${encodeURIComponent(investigationId)}/documentary-evidence`);
};


// v2.50.0 Open Forensics — Forensic Research Graph.
PublicApiClient.prototype.openForensicsResearchGraph = function (investigationId, graphId) {
  return this.get(`/api/v1/open-forensics/investigations/${encodeURIComponent(investigationId)}/research-graphs/${encodeURIComponent(graphId)}`);
};
PublicApiClient.prototype.openForensicsResearchGraphVisualSpec = function (investigationId, graphId) {
  return this.get(`/api/v1/open-forensics/investigations/${encodeURIComponent(investigationId)}/research-graphs/${encodeURIComponent(graphId)}/visual-spec`);
};


PublicApiClient.prototype.openForensicsReproducibleInvestigationPackage = function (investigationId, packageId) {
  return this.get(`/api/v1/open-forensics/investigations/${encodeURIComponent(investigationId)}/reproducible-packages/${encodeURIComponent(packageId)}`);
};


// v2.53.0 Predictive Intelligence — Time-Series Forecasting & Backtesting.
PublicApiClient.prototype.predictiveIntelligenceReadiness=function(){return this.request("/predictive-intelligence/readiness");};
PublicApiClient.prototype.predictiveModels=function(params={}){const q=new URLSearchParams(params);return this.request(`/predictive-intelligence/models?${q}`);};
PublicApiClient.prototype.predictiveModelBundle=function(modelId){return this.request(`/predictive-intelligence/models/${encodeURIComponent(modelId)}/bundle`);};
PublicApiClient.prototype.predictiveBacktestBundle=function(modelId,planId){return this.request(`/predictive-intelligence/models/${encodeURIComponent(modelId)}/backtest-plans/${encodeURIComponent(planId)}/bundle`);};

// v2.54.0 Predictive Intelligence — Probabilistic Forecasting & Calibration.
PublicApiClient.prototype.predictiveCalibrationBundle=function(modelId,studyId){return this.request(`/predictive-intelligence/models/${encodeURIComponent(modelId)}/calibration-studies/${encodeURIComponent(studyId)}/bundle`);};

PublicApiClient.prototype.predictiveEnsembleBundle=function(ensembleId){return this.request(`/predictive-intelligence/ensembles/${encodeURIComponent(ensembleId)}/bundle`);};
PublicApiClient.prototype.predictiveComparisonBundle=function(studyId){return this.request(`/predictive-intelligence/comparison-studies/${encodeURIComponent(studyId)}/bundle`);};

// v2.56.0 Predictive Monitoring
PublicApiClient.prototype.predictiveMonitoringBundle=function(studyId){return this.request(`/predictive-intelligence/monitoring-studies/${encodeURIComponent(studyId)}/bundle`);};


// v2.57.0 Spatial-Temporal Predictive Intelligence
PublicApiClient.prototype.predictiveSpatialTemporalBundle=function(studyId){return this.request(`/predictive-intelligence/spatial-temporal-studies/${encodeURIComponent(studyId)}/bundle`);};


// v2.58.0 Causal-Predictive Integration
PublicApiClient.prototype.predictiveCausalBundle=function(studyId){return this.request(`/predictive-intelligence/causal-predictive-studies/${encodeURIComponent(studyId)}/bundle`);};

// v2.59.0 Predictive Decision Intelligence
PublicApiClient.prototype.predictiveDecisionBundle=function(studyId){return this.request(`/predictive-intelligence/decision-studies/${encodeURIComponent(studyId)}/bundle`);};

PublicApiClient.prototype.reproduciblePredictivePackageBundle=function(packageId){return this.request(`/predictive-intelligence/packages/${encodeURIComponent(packageId)}/bundle`);};


// v2.61.0 Visual Reasoning Runtime & Scene Graph
PublicApiClient.prototype.visualRuntimeSceneBundle=function(sceneId){return this.request(`/visual-runtime/scenes/${encodeURIComponent(sceneId)}/bundle`);};

export async function visualRuntimeCompositionBundle(client, compositionId) {
  return client.request(`/v1/visual-runtime/composition/compositions/${compositionId}/bundle`);
}


// v2.63.0 Analytical Visualization Grammar
PublicApiClient.prototype.visualRuntimeGrammarBundle=function(specificationId){return this.request(`/visual-runtime/grammar/specifications/${encodeURIComponent(specificationId)}/bundle`);};


// v2.64.0 Linked Views & Cross-Filtering
PublicApiClient.prototype.visualRuntimeLinkedViewsBundle=function(compositionId){return this.request(`/visual-runtime/linked-views/compositions/${encodeURIComponent(compositionId)}/bundle`);};


// v2.65.0 Visual Query & Exploration Engine
PublicApiClient.prototype.visualQueryExplorationBundle=function(sessionId){return this.request(`/visual-runtime/query/sessions/${encodeURIComponent(sessionId)}/bundle`);};


// v2.66.0 Visual Model Construction
PublicApiClient.prototype.visualModelConstructionBundle=function(constructionId){return this.request(`/visual-runtime/model-construction/constructions/${encodeURIComponent(constructionId)}/bundle`);};
PublicApiClient.prototype.visualPredictiveWorkspaceBundle=function(workspaceId){return this.request(`/visual-runtime/predictive/workspaces/${encodeURIComponent(workspaceId)}/bundle`);};

export async function visualForensicsWorkspaceBundle(client, workspaceId) { return client.get(`/api/v1/visual-runtime/forensics/workspaces/${workspaceId}/bundle`); }


export async function visualDecisionWorkspaceBundle(client, workspaceId) { return client.get(`/api/v1/visual-runtime/decision/workspaces/${workspaceId}/bundle`); }


// v2.70.0 Unified Visual Reasoning Engine
export async function unifiedVisualReasoningWorkspaceBundle(client, workspaceId) { return client.get(`/api/v1/visual-runtime/unified/workspaces/${workspaceId}/bundle`); }


// v2.71.0 Cross-Product Visual Runtime Integration
export async function crossProductVisualRuntimeWorkspaceBundle(client, workspaceId) { return client.get(`/api/v1/visual-runtime/integrations/workspaces/${workspaceId}/bundle`); }

// v2.72.0 Unified Research Project Object Model
export async function unifiedResearchProjectBundle(client, projectId) {
  return client.request("GET", `/research/projects/${projectId}/bundle`);
}


// v2.73.0 Research Lineage & Provenance Graph
PublicApiClient.prototype.researchLineageGraphBundle = function (graphId) { return this.request(`/research/lineage/graphs/${encodeURIComponent(graphId)}/bundle`); };

// v2.74.0 Methodology & Analysis Run Registry
export async function researchMethodologyReadiness(client) { return client.request("GET", "/v1/research/methodology/readiness"); }
export async function researchMethodologyBundle(client, projectId) { return client.request("GET", `/v1/research/methodology/projects/${projectId}/bundle`); }

export const reproducibleResearchPackage = (client, packageId) => client.get(`/api/v1/research/reproducibility/packages/${packageId}/bundle`);


// v2.76.0 Research Notebook & Analytical Narrative
export async function researchNotebookBundle(client, notebookId) { return client.request(`/research/notebooks/notebooks/${encodeURIComponent(notebookId)}/bundle`); }


// v2.77.0 Finding, Claim & Evidence Intelligence
export async function researchIntelligenceBundle(client, projectId) { return client.request(`/research/intelligence/projects/${encodeURIComponent(projectId)}/bundle`); }
export async function researchIntelligenceContradictionCandidates(client, projectId) { return client.request(`/research/intelligence/projects/${encodeURIComponent(projectId)}/contradiction-candidates`); }


// v2.78.0 Hypothesis & Competing Explanation Engine
export async function hypothesisIntelligenceBundle(client, setId) { return client.request(`/research/hypotheses/sets/${encodeURIComponent(setId)}/bundle`); }
export async function hypothesisIntelligenceComparison(client, setId) { return client.request(`/research/hypotheses/sets/${encodeURIComponent(setId)}/comparison`); }


// v2.79.0 Research Argument & Evidentiary Synthesis Engine
export async function researchArgumentBundle(client, argumentId) { return client.request(`/research/arguments/${encodeURIComponent(argumentId)}/bundle`); }
export async function researchArgumentMap(client, argumentId) { return client.request(`/research/arguments/${encodeURIComponent(argumentId)}/map`); }

// v2.80.0 Research Decision Trace & Conclusion Governance
export async function getResearchConclusionGovernance(client, conclusionId) {
  return client.request(`/research/conclusions/${encodeURIComponent(conclusionId)}/governance`);
}
export async function getResearchConclusionBundle(client, conclusionId) {
  return client.request(`/research/conclusions/${encodeURIComponent(conclusionId)}/bundle`);
}


// v2.81.0 Reproducible Research Publication & Scholarly Output Engine
export async function getResearchPublicationReadiness(client, publicationId) { return client.request(`/research/publications/${encodeURIComponent(publicationId)}/readiness`); }
export async function getResearchPublicationLineage(client, publicationId) { return client.request(`/research/publications/${encodeURIComponent(publicationId)}/lineage`); }
export async function getResearchPublicationBundle(client, publicationId) { return client.request(`/research/publications/${encodeURIComponent(publicationId)}/bundle`); }


// v2.82.0 Peer Review, Replication & Rebuttal Intelligence
PublicApiClient.prototype.peerReviewSummary=function(publicationId){return this.request(`/research/peer-review/publications/${encodeURIComponent(publicationId)}/summary`);};
PublicApiClient.prototype.peerReviewLineage=function(publicationId){return this.request(`/research/peer-review/publications/${encodeURIComponent(publicationId)}/lineage`);};
PublicApiClient.prototype.peerReviewBundle=function(publicationId){return this.request(`/research/peer-review/publications/${encodeURIComponent(publicationId)}/bundle`);};


// v2.83.0 Cross-Study Evidence Synthesis & Meta-Research
PublicApiClient.prototype.evidenceSynthesisSummary=function(synthesisId){return this.request(`/research/evidence-synthesis/syntheses/${encodeURIComponent(synthesisId)}/summary`);};
PublicApiClient.prototype.evidenceSynthesisLineage=function(synthesisId){return this.request(`/research/evidence-synthesis/syntheses/${encodeURIComponent(synthesisId)}/lineage`);};
PublicApiClient.prototype.evidenceSynthesisBundle=function(synthesisId){return this.request(`/research/evidence-synthesis/syntheses/${encodeURIComponent(synthesisId)}/bundle`);};


// v2.84.0 Research Program & Longitudinal Knowledge Graph
PublicApiClient.prototype.researchProgramSummary=function(programId){return this.request(`/research/programs/${encodeURIComponent(programId)}/summary`);};
PublicApiClient.prototype.researchProgramGraph=function(programId){return this.request(`/research/programs/${encodeURIComponent(programId)}/graph`);};
PublicApiClient.prototype.researchProgramTimeline=function(programId){return this.request(`/research/programs/${encodeURIComponent(programId)}/timeline`);};
PublicApiClient.prototype.researchProgramLineage=function(programId){return this.request(`/research/programs/${encodeURIComponent(programId)}/lineage`);};
PublicApiClient.prototype.researchProgramBundle=function(programId){return this.request(`/research/programs/${encodeURIComponent(programId)}/bundle`);};


// v2.85.0 Research Portfolio & Institutional Knowledge Governance
PublicApiClient.prototype.researchPortfolioSummary=function(portfolioId){return this.request(`/research/portfolios/${encodeURIComponent(portfolioId)}/summary`);};
PublicApiClient.prototype.researchPortfolioMap=function(portfolioId){return this.request(`/research/portfolios/${encodeURIComponent(portfolioId)}/map`);};
PublicApiClient.prototype.researchPortfolioLineage=function(portfolioId){return this.request(`/research/portfolios/${encodeURIComponent(portfolioId)}/lineage`);};
PublicApiClient.prototype.researchPortfolioBundle=function(portfolioId){return this.request(`/research/portfolios/${encodeURIComponent(portfolioId)}/bundle`);};

// v2.86.0 Scientific Study & Investigation Protocol Model
export async function researchProtocolSummary(client, protocolId) { return client.request("GET", `/research/protocols/${encodeURIComponent(protocolId)}/summary`); }
export async function researchProtocolLineage(client, protocolId) { return client.request("GET", `/research/protocols/${encodeURIComponent(protocolId)}/lineage`); }
export async function researchProtocolBundle(client, protocolId) { return client.request("GET", `/research/protocols/${encodeURIComponent(protocolId)}/bundle`); }

// v2.87.0 Computation, Analysis & Execution Lineage
export async function computationLineageSummary(client, executionId) { return client.request("GET", `/research/computation-lineage/executions/${encodeURIComponent(executionId)}/summary`); }
export async function computationLineage(client, executionId) { return client.request("GET", `/research/computation-lineage/executions/${encodeURIComponent(executionId)}/lineage`); }
export async function computationLineageBundle(client, executionId) { return client.request("GET", `/research/computation-lineage/executions/${encodeURIComponent(executionId)}/bundle`); }


// v2.88.0 Unified Findings, Claims & Inference Engine
export async function inferenceSummary(client, inferenceId) { return client.request("GET", `/research/inferences/${encodeURIComponent(inferenceId)}/summary`); }
export async function inferenceLineage(client, inferenceId) { return client.request("GET", `/research/inferences/${encodeURIComponent(inferenceId)}/lineage`); }
export async function inferenceBundle(client, inferenceId) { return client.request("GET", `/research/inferences/${encodeURIComponent(inferenceId)}/bundle`); }

// v2.89.0 Research Quality, Bias & Methodological Audit Engine
export async function qualityAuditSummary(client, auditId) { return client.request("GET", `/research/quality-audits/${encodeURIComponent(auditId)}/summary`); }
export async function qualityAuditLineage(client, auditId) { return client.request("GET", `/research/quality-audits/${encodeURIComponent(auditId)}/lineage`); }
export async function qualityAuditBundle(client, auditId) { return client.request("GET", `/research/quality-audits/${encodeURIComponent(auditId)}/bundle`); }

// v2.90.0 Research Workflow & Orchestration Engine
export async function researchWorkflowSummary(client, workflowId) { return client.request("GET", `/research/workflows/${encodeURIComponent(workflowId)}/summary`); }
export async function researchWorkflowTimeline(client, workflowId) { return client.request("GET", `/research/workflows/${encodeURIComponent(workflowId)}/timeline`); }
export async function researchWorkflowLineage(client, workflowId) { return client.request("GET", `/research/workflows/${encodeURIComponent(workflowId)}/lineage`); }
export async function researchWorkflowBundle(client, workflowId) { return client.request("GET", `/research/workflows/${encodeURIComponent(workflowId)}/bundle`); }


// v2.91.0 Cross-Product Research Context & Handoff Protocol
export async function researchContextHandoffSummary(client, contextId) { return client.request("GET", `/research/context-handoffs/contexts/${encodeURIComponent(contextId)}/summary`); }
export async function researchContextHandoffLineage(client, contextId) { return client.request("GET", `/research/context-handoffs/contexts/${encodeURIComponent(contextId)}/lineage`); }
export async function researchContextHandoffBundle(client, contextId) { return client.request("GET", `/research/context-handoffs/contexts/${encodeURIComponent(contextId)}/bundle`); }

// v2.92.0 Research Project State, Versioning & Reproducibility
export async function researchProjectStateSummary(client, stateId) { return client.request("GET", `/research/project-state/states/${encodeURIComponent(stateId)}/summary`); }
export async function researchProjectStateLineage(client, stateId) { return client.request("GET", `/research/project-state/states/${encodeURIComponent(stateId)}/lineage`); }
export async function researchProjectStateBundle(client, stateId) { return client.request("GET", `/research/project-state/states/${encodeURIComponent(stateId)}/bundle`); }
export async function researchProjectStateManifest(client, stateId, version) { return client.request("GET", `/research/project-state/states/${encodeURIComponent(stateId)}/versions/${encodeURIComponent(version)}/manifest`); }

// v2.93.0 Research Roles, Agents & Contributor Provenance Framework
export async function researchContributorProvenanceSummary(client, projectRef) { return client.request("GET", `/research/contributors/projects/${encodeURIComponent(projectRef)}/summary`); }
export async function researchContributorProvenanceLineage(client, projectRef) { return client.request("GET", `/research/contributors/projects/${encodeURIComponent(projectRef)}/lineage`); }
export async function researchContributorProvenanceBundle(client, projectRef) { return client.request("GET", `/research/contributors/projects/${encodeURIComponent(projectRef)}/bundle`); }


// v2.94.0 Research Validation & Challenge Engine
export async function researchValidationChallengeSummary(client, projectRef) { return client.request("GET", `/research/validation-challenges/projects/${encodeURIComponent(projectRef)}/summary`); }
export async function researchValidationChallengeLineage(client, projectRef) { return client.request("GET", `/research/validation-challenges/projects/${encodeURIComponent(projectRef)}/lineage`); }
export async function researchValidationChallengeBundle(client, projectRef) { return client.request("GET", `/research/validation-challenges/projects/${encodeURIComponent(projectRef)}/bundle`); }


// v2.95.0 Scholarly Interoperability & Research Packaging
export async function scholarlyPackageSummary(client, projectRef) { return client.request("GET", `/research/scholarly-packages/projects/${encodeURIComponent(projectRef)}/summary`); }
export async function scholarlyPackageLineage(client, projectRef) { return client.request("GET", `/research/scholarly-packages/projects/${encodeURIComponent(projectRef)}/lineage`); }
export async function scholarlyPackageBundle(client, projectRef) { return client.request("GET", `/research/scholarly-packages/projects/${encodeURIComponent(projectRef)}/bundle`); }

// v2.96.0 Unified Research Runtime Contract
export async function researchRuntimeContractBundle(client, contractId) { return client.request("GET", `/research/runtime-contract/contracts/${encodeURIComponent(contractId)}/bundle`); }
export async function researchRuntimeProjectBundle(client, projectRef) { return client.request("GET", `/research/runtime-contract/projects/${encodeURIComponent(projectRef)}/bundle`); }
