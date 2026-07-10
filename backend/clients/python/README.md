# Python Client

Copy `sc_platform_core` into a product backend or package it internally.

```python
from sc_platform_core import PlatformCoreClient

client = PlatformCoreClient(
    "https://your-platform-core.onrender.com",
    api_key="write-key-only-when-needed",
)

print(client.health())
print(client.get_entity("sc:product:workbench"))
print(client.graph("sc:product:research-librarian", depth=2))
```
