# Platform Core v2.58.0 — Install & Test

1. Run `deploy_and_validate_platform_core_v2_58_0_macos.sh` against the frozen release bundle.
2. The validator checks SHA-256, release contract, source manifest, secret safety, syntax, the full release regression list, migration `0062`, and causal-predictive invariants.
3. Promotion pushes `main` and creates immutable tag `v2.58.0` only after validation succeeds.
4. On Contabo, run `DEPLOY_PLATFORM_CORE_V2580_CONTABO.sh`. Production must already contain v2.57.0 migration `0061` and all eight v2.57 spatial-temporal tables.
5. The deployer backs up source and PostgreSQL, applies/repairs `0062`, rebuilds only Core, and verifies internal/public health and Predictive Intelligence readiness.
