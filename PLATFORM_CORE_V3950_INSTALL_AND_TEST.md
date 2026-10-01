# Platform Core v3.95.0 Install & Test

Predecessor: v3.94.0

1. Apply the release payload.
2. Run the v3.95 validator and isolated pytest suite.
3. Verify private/public route mounts.
4. Commit/push/tag v3.95.0.
5. Deploy the tagged backend to Contabo and verify `/health` plus `/public/v1/signed-runtime-attestations/contract`.
