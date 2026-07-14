# Sustainable Catalyst Public API JavaScript Client v2.5.0

```javascript
import { PublicApiClient } from "./index.mjs";

const client = new PublicApiClient(
  "https://YOUR-PLATFORM-CORE.onrender.com",
  "scpk_your_key"
);

console.log(await client.status());
console.log(await client.trustStatus());
console.log(await client.workflowDefinitions());
console.log(await client.dossiers());
console.log(await client.verifyDossier("sc:dossier:..."));
```

## Live data and international law v2.7.1

```js
const sources = await client.liveSources();
const connectors = await client.liveConnectors({ domain: "hazards" });
const events = await client.liveObservations({ connector_id: "usgs.earthquakes" });
const series = await client.liveTimeseries("SP.POP.TOTL", { source_id: "world-bank" });
const lineage = await client.liveProvenance(events[0].id);
```

These methods require the `data:read` scope.


## International law and UN records v2.7.1

Use the international-law record, detail, and authority-taxonomy client methods to consume official-source records without exposing connector configuration or raw payloads.
