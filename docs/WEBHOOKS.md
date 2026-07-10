# Signed Webhooks

## Subscription patterns

A subscription can use:

```text
claim.created
claim.*
evidence.*
*
```

## Event body

```json
{
  "id": "sc:webhook-event:...",
  "type": "claim.created",
  "created_at": "2026-07-10T00:00:00Z",
  "resource": {
    "type": "claim",
    "id": "sc:claim:..."
  },
  "data": {}
}
```

## Signature verification

Headers:

```text
X-SC-Webhook-ID
X-SC-Webhook-Timestamp
X-SC-Webhook-Signature: v1=<hex digest>
```

Calculate HMAC-SHA256 with the subscription signing secret over:

```text
{timestamp}.{raw_request_body}
```

Compare signatures with a constant-time comparison and reject stale timestamps according to your own replay window.

## Delivery behavior

- Events are recorded transactionally in the database outbox.
- Successful HTTP `2xx` responses mark delivery complete.
- Non-`2xx` responses and connection failures mark the delivery failed.
- Failed events remain pending for another worker run.
- The delivery record preserves attempts, HTTP status, response excerpt, error, signature, and timestamps.

## Worker operation

```bash
python scripts/dispatch_webhooks.py --limit 100
```

or:

```text
POST /v1/developer/webhooks/dispatch
```

The HTTP route requires the internal write key.

## Security

Production subscriptions require HTTPS. Localhost, private-network, link-local, multicast, reserved, and unspecified addresses are rejected. URLs with embedded usernames or passwords are rejected.

The subscription secret is deterministically derived from the server master secret and subscription ID. Rotating the master secret rotates all effective subscription secrets, so subscribers must be updated after rotation.
