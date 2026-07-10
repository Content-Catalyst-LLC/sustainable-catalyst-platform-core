# Developer Access and Credential Governance

## Application lifecycle

```text
pending → approved → suspended
pending → rejected
suspended → approved
```

Only approved applications can receive or use public API credentials.

## Credential lifecycle

```text
active → revoked
active → expired
```

Credentials inherit their allowed scope ceiling and quota plan from the developer application.

## Key storage

The issued key has the form:

```text
scpk_<public-prefix>_<secret>
```

Platform Core stores only the SHA-256 hash, prefix, last four characters, metadata, and lifecycle state. A lost plaintext key cannot be recovered; issue a replacement and revoke the old credential.

## Administrative responsibility

The internal write key can:

- Create and update developer applications
- Approve, suspend, or reject applications
- Issue and revoke public credentials
- Publish webhook events
- Dispatch webhook deliveries
- Read full developer usage and statistics

Public API credentials cannot perform those administrative operations.

## Recommended operational process

1. Review the stated use case.
2. Assign the lowest appropriate plan.
3. Issue only required scopes.
4. Store the plaintext key in a secret manager.
5. Review usage and errors.
6. Revoke unused or compromised credentials.
7. Issue a new key rather than attempting recovery.

## Privacy

Usage records store hashed network and user-agent identifiers. They are intended for rate limiting, abuse investigation, reliability analysis, and aggregate usage—not cross-site tracking.
