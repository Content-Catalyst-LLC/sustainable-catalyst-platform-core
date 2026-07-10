# Sustainable Catalyst Public API Python Client v2.5.0

```python
from sc_platform_core_public import PublicApiClient

client = PublicApiClient(
    "https://YOUR-PLATFORM-CORE.onrender.com",
    "scpk_your_key",
)

print(client.status())
print(client.trust_status())
print(client.workflow_definitions())
print(client.dossiers())
print(client.verify_dossier("sc:dossier:..."))
```
