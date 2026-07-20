# Sustainable Catalyst Public API JavaScript Client v2.8.0

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

## Live data gateway v2.7.0

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

## Scientific data v2.7.2

Use `scientific_records`, `scientific_record`, and `scientific_record_types` (camelCase in JavaScript) to discover normalized public scientific records through the scoped API.


## Economics and official statistics v2.7.3

```javascript
const records = await client.economicRecords({ indicator_code: "GDP", geography_code: "USA", limit: 25 });
const record = await client.economicRecord(records[0].id);
const types = await client.economicRecordTypes();
```


## Data fabric v2.8.0

```javascript
const capabilities = await client.fabricCapabilities();
const features = await client.geospatialFeatures({ bbox: "-88,41,-87,42" });
const series = await client.timeSeries({ metric: "temperature" });
const points = await client.timeSeriesPoints(series[0].id);
const assets = await client.scientificAssets({ format: "fits" });
const layers = await client.mapLayers({ layer_type: "cog" });
const stac = await client.stacSearch({ collections: "mast:JWST" });
```
