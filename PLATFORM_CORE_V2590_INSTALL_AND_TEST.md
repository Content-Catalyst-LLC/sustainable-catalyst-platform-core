# Platform Core v2.59.0 — Install & Test

1. Run `deploy_and_validate_platform_core_v2_59_0_macos.sh` against the frozen release bundle.
2. Validation checks SHA-256, release contract, source manifest, secret safety, syntax, regression tests, migration `0063`, and predictive-decision invariants.
3. Promotion pushes `main` and creates immutable tag `v2.59.0` only after validation succeeds.
4. Deploy on Contabo only after v2.58.0 / migration `0062` is live.
