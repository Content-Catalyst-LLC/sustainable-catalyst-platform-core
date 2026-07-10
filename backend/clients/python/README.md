# Python Client

```python
from sc_platform_core import PlatformCoreClient

client = PlatformCoreClient(
    "https://your-platform-core.onrender.com",
    api_key="write-key-only-when-needed",
)

print(client.list_predicates())
print(client.get_entity_jsonld("sc:product:workbench"))
print(client.neighborhood("sc:product:research-librarian"))
print(client.path("sc:product:research-librarian", "sc:product:site-intelligence"))
print(client.recommendations("sc:product:research-librarian", target_type="product"))
```
