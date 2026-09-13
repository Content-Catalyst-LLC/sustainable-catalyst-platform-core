# Platform Core v2.36.0 Install & Test

1. Run the bundle-only Mac validator.
2. Run release-critical validation and GitHub promotion.
3. Upload and run `DEPLOY_PLATFORM_CORE_V2360_CONTABO.sh`.
4. Confirm migration `0039`, public health `2.36.0`, and `/v1/uncertainty-reasoning/readiness`.
5. Install the WordPress plugin and test `[sc_platform_core_uncertainty_reasoning_status]`.

The default validation path is the focused release-critical suite. Set `SC_CORE_FULL_CERTIFICATION=1` only when intentionally running the historical suite.
