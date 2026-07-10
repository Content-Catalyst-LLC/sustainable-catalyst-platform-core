# SDK Guide

## Python

Download:

```text
/developers/sdk/python.zip
```

Example:

```python
from sc_platform_core_public import PublicApiClient

client = PublicApiClient(
    "https://YOUR-PLATFORM-CORE.onrender.com",
    "scpk_your_key",
)

print(client.status())
print(client.entities(entity_type="product"))
print(client.verify_ledger())
```

## JavaScript

Download:

```text
/developers/sdk/javascript.zip
```

Example:

```javascript
import { PublicApiClient } from "./index.mjs";

const client = new PublicApiClient(
  "https://YOUR-PLATFORM-CORE.onrender.com",
  "scpk_your_key"
);

console.log(await client.status());
console.log(await client.entities({ entity_type: "product" }));
```

## Direct HTTP

The SDKs intentionally remain thin. Any standards-compliant HTTP client can use the public API directly.
