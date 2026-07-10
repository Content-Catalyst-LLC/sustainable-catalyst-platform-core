# Sustainable Catalyst Public API JavaScript Client

```javascript
import { PublicApiClient } from "./index.mjs";

const client = new PublicApiClient(
  "https://YOUR-PLATFORM-CORE.onrender.com",
  "scpk_your_key"
);

console.log(await client.status());
console.log(await client.entities({ entity_type: "product" }));
```
