# Platform Core v2.41.0 Install and Test

1. Run bundle-only verification.
2. Run full Mac validation and GitHub promotion.
3. Confirm production is on v2.40.0 / migration 0044.
4. Deploy the Contabo backend with `DEPLOY_PLATFORM_CORE_V2410_CONTABO.sh`.
5. Verify public health and `/v1/reproducible-visual-knowledge/readiness`.
6. Install the v2.41.0 WordPress plugin and use `[sc_platform_core_reproducible_visual_knowledge_status]`.
