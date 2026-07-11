# Sustainable Catalyst Gateway JavaScript Client v2.6.0

```js
import { SustainableCatalystGatewayClient } from "./sc-platform-core-gateway.js";

const client = new SustainableCatalystGatewayClient({
  baseUrl: "https://api.sustainablecatalyst.com",
  publicApiKey: "scpk_...",
});

console.log(await client.health());
console.log(await client.read("workbench", "health"));
```

The credential must include the `gateway:read` scope.
