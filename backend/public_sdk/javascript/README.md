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
