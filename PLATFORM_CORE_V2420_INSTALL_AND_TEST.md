# Platform Core v2.42.0 Install and Test

1. Run bundle-only validation.
2. Run full Mac validation and GitHub promotion.
3. Confirm v2.41.0 / migration 0045 is live in production.
4. Copy and run `DEPLOY_PLATFORM_CORE_V2420_CONTABO.sh`.
5. Confirm `/health` reports `2.42.0` and `/v1/open-forensics/readiness` reports migration `0046`.
6. Install the v2.42.0 WordPress plugin and use `[sc_platform_core_open_forensics_status]`.
