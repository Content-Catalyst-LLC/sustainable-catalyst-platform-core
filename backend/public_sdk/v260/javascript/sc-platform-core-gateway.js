export class SustainableCatalystGatewayClient {
  constructor({ baseUrl, publicApiKey }) {
    if (!baseUrl || !/^https?:\/\//i.test(baseUrl)) {
      throw new TypeError("baseUrl must be an HTTP or HTTPS URL");
    }
    if (!publicApiKey) {
      throw new TypeError("publicApiKey is required");
    }
    this.baseUrl = baseUrl.replace(/\/$/, "");
    this.publicApiKey = publicApiKey;
  }

  async get(path, params = {}) {
    const url = new URL(`${this.baseUrl}${path}`);
    Object.entries(params).forEach(([key, value]) => {
      if (Array.isArray(value)) {
        value.forEach((item) => url.searchParams.append(key, String(item)));
      } else if (value !== undefined && value !== null) {
        url.searchParams.set(key, String(value));
      }
    });
    const response = await fetch(url, {
      method: "GET",
      headers: {
        Accept: "application/json",
        Authorization: `Bearer ${this.publicApiKey}`,
      },
      redirect: "manual",
    });
    const payload = await response.json().catch(() => null);
    if (!response.ok) {
      throw new Error(`Gateway request failed (${response.status}): ${JSON.stringify(payload)}`);
    }
    return payload;
  }

  services() {
    return this.get("/api/v1/gateway/services");
  }

  health() {
    return this.get("/api/v1/gateway/health");
  }

  read(service, path = "", params = {}) {
    const allowed = new Set([
      "site-intelligence",
      "workbench",
      "decision-studio",
      "research-librarian",
      "finance",
      "narrative-risk",
    ]);
    if (!allowed.has(service)) {
      throw new TypeError(`Unknown gateway service: ${service}`);
    }
    const cleanPath = String(path).replace(/^\/+/, "");
    return this.get(`/api/v1/${service}/${cleanPath}`, params);
  }
}
