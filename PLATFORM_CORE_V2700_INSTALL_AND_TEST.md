# Install and Test — Platform Core v2.70.0

Use `deploy_and_validate_platform_core_v2_70_0_macos.sh` for local release certification and immutable Git promotion. The validator verifies the release contract, push-safe secret policy, frozen repository manifest, syntax, complete historical regression list, migration `0074`, and Unified Visual Reasoning Engine invariants before promotion.

Production deployment uses `DEPLOY_PLATFORM_CORE_V2700_CONTABO.sh` only after v2.69.0/migration `0073` and all ten Visual Decision Intelligence tables are live.
