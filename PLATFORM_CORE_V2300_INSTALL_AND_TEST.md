# Platform Core v2.30.0 — Install and Test

1. Run the bundle-only verifier on macOS.
2. Run the full macOS validation/promotion script to test and push/tag GitHub.
3. Deploy Git tag `v2.30.0` to Contabo using `compose.yml` plus the local `compose.vps.yml` override.
4. Apply migrations through `0033` before recreating `sc-core`.
5. Verify `/health`, `/v1/visualization/readiness`, migration state, container health, and the persistent scientific-object mount.
6. Install the v2.30.0 WordPress plugin and configure Backend URL as `https://core.sustainablecatalyst.com` if needed.
7. Verify `[sc_platform_core_visualization_registry_status]` before beginning v2.31.0.

Renderer contracts are metadata. No renderer runtime is installed or executed by this release.
