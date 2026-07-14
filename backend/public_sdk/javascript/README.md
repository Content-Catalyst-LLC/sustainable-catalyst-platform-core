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

## Live data v2.7.0

```js
const sources = await client.liveSources();
const connectors = await client.liveConnectors({ domain: "hazards" });
const events = await client.liveObservations({ connector_id: "usgs.earthquakes" });
const series = await client.liveTimeseries("SP.POP.TOTL", { source_id: "world-bank" });
const lineage = await client.liveProvenance(events[0].id);
```

These methods require the `data:read` scope.
