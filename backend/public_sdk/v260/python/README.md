# Sustainable Catalyst Gateway Python Client v2.6.0

```python
from sc_platform_core_gateway import GatewayClient

client = GatewayClient(
    base_url="https://api.sustainablecatalyst.com",
    public_api_key="scpk_...",
)

print(client.health())
print(client.read("site-intelligence", "health"))
```

The credential must include the `gateway:read` scope.
