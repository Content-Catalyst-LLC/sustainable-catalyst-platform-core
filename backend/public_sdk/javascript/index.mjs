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

  identity() {
    return this.request("/developer/me");
  }

  usage(days = 30) {
    return this.request(`/developer/usage?days=${days}`);
  }
}
