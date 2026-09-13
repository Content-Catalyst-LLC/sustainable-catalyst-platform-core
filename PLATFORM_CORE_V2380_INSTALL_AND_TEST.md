# Platform Core v2.38.0 — Install and Test

1. Run bundle-only validation on macOS.
2. Run release-critical validation and promote the exact frozen repository to GitHub tag `v2.38.0`.
3. Copy `DEPLOY_PLATFORM_CORE_V2380_CONTABO.sh` to the VPS and execute it.
4. Install the WordPress plugin and verify `[sc_platform_core_spatial_temporal_status]`.

Migration `0042` is additive. Production must already have migration `0041` from v2.37.0.2.
