# Platform Core v3.95.0 — Signed Runtime Artifacts & Execution Attestations

Contract: `sc.core.signed-runtime-artifacts-execution-attestations.v1`

This release defines a provider-neutral signing and verification contract for content-addressed runtime artifacts and execution manifests. Core stores public signer/key references, artifact and manifest digests, detached attestation envelopes, explicit verification evidence, revocation/expiry status, and immutable attestation chains. Private-key operations remain outside Core behind a signing provider, HSM, KMS, or equivalent adapter.

## Governing boundaries
- A valid signature establishes integrity/signer association only; it does not establish content truth or scientific validity.
- Artifact hashes establish byte identity, not factual correctness.
- Attestation cannot promote epistemic state, bypass validation/review, or mutate governed graphs.
- Signed remote references remain remote and continue to require local validation.
- Revoked/expired keys cannot verify as current.
