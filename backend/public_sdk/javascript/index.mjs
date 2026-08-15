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

}
