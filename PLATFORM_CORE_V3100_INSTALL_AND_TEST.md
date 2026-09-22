# Platform Core v3.1.0 — Install and Test

1. Promote the repository release with `PUSH_PLATFORM_CORE_V3100_FINAL.sh`.
2. Deploy on Contabo with `DEPLOY_PLATFORM_CORE_V3100_CONTABO.sh`.
3. Verify `/health` returns `3.1.0`.
4. Verify `/v1/analytics/runtime-providers/readiness` reports migration 0103 and Catalyst Analytics R 2.0.1.
5. Verify provider bundle reports `runtime=r` and `execution_host=workspace`.
