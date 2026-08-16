# Platform Core v2.24.0 R1 — Secret-Scan Example Credential & Promotion Repair

R1 is a promotion-lineage repair for v2.24.0. It does **not** change the v2.24.0 runtime, capacity forecasting/resource governance behavior, database schema, migration head `0027`, public SDK version, WordPress plugin version, or federation semantics.

## Failure repaired

The original v2.24.0 promotion completed deterministic validation and manifest verification, then stopped before commit/push because the push-safe secret scan flagged the inherited documented placeholder:

`SC_CORE_FEDERATION_TRUST_SECRETS_JSON={"remote-node-id":"replace-with-long-random-secret"}`

The placeholder was documentation-only and not a live credential.

## R1 repair

- Replaces the brittle inline grep/allowlist pipeline with a deterministic repository secret scanner.
- Continues scanning `.env.example` files instead of broadly excluding them.
- Allows the exact documented federation placeholder values only after parsing the JSON assignment.
- Rejects real-looking federation trust values even when they appear in an `.env.example` or commented example line.
- Retains detection for OpenAI-style, Google API, GitHub, bearer, service-token, and federation trust-secret patterns.
- Adds regression tests for allowed placeholder, live-secret rejection, placeholder-prefix rejection, and repository-wide clean scan.
- Adds an R1 repair/resume wrapper that validates the repaired bundle before handing off to the canonical v2.24.0 deployment/promotion path.

Core remains version `2.24.0`; migration head remains `0027`.
