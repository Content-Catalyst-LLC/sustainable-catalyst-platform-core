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

}
