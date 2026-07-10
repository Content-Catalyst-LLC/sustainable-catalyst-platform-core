# Sustainable Catalyst Public API Python Client

```python
from sc_platform_core_public import PublicApiClient

client = PublicApiClient(
    "https://YOUR-PLATFORM-CORE.onrender.com",
    "scpk_your_key",
)

print(client.status())
print(client.entities(entity_type="product"))
print(client.trust_status())
print(client.trust_evaluations(domain="ai-responsibility"))
```
