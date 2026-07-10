# Python Client

```python
from sc_platform_core import PlatformCoreClient

client = PlatformCoreClient(
    "https://your-platform-core.onrender.com",
    api_key="backend-write-key",
)

claim = client.create_claim({
    "actor": "decision-studio",
    "claim_text": "The proposed intervention reduces annual emissions.",
    "claim_type": "analytical",
    "status": "draft",
    "visibility": "public",
    "language": "en",
    "metadata": {},
})

snapshot = client.create_source_snapshot({
    "actor": "site-intelligence",
    "source_entity_id": "sc:source:example",
    "canonical_url": "https://example.org/report",
    "content": "Captured source text or canonical serialized data.",
    "media_type": "text/plain",
    "metadata": {},
})

evidence = client.create_evidence_record({
    "actor": "decision-studio",
    "evidence_type": "source-record",
    "stance": "supports",
    "claim_id": claim["id"],
    "source_snapshot_id": snapshot["id"],
    "statement": "The source reports the modeled reduction.",
    "confidence": 0.82,
    "provenance": {},
    "metadata": {},
})

print(client.evidence_manifest(claim["id"]))
print(client.verify_ledger())
```
