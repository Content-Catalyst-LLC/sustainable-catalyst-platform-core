# Platform Core v3.86.0 — Install and Test

Predecessor gate: v3.85.0 → v3.86.0.

Run the release bundle `APPLY_AND_PUSH_PLATFORM_CORE_V3860.sh` against the local Core repository. The script validates the v3.86 contract and targeted tests, confirms route mounting, commits/pushes/tags, and preserves the cleaned repository-root pattern.

Deploy to Contabo with `DEPLOY_PLATFORM_CORE_V3860_CONTABO.sh`; it requires production HEAD to be tagged `v3.86.0`, runs the validator and targeted tests inside Docker with `PYTHONPATH=/app`, recreates only the `core` service, and verifies local and public contract endpoints.
