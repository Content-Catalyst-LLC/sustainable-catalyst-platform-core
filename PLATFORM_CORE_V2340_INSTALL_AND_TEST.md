# Platform Core v2.34.0 Install & Test

## Local / macOS

Use `deploy_and_validate_platform_core_v2_34_0_macos.sh`. The default validation path is intentionally release-critical rather than a full historical recertification sweep.

Bundle-only:

```bash
SC_CORE_BUNDLE_ONLY=1 ./deploy_and_validate_platform_core_v2_34_0_macos.sh "$HOME/Downloads/sustainable-catalyst-platform-core-v2.34.0-release-bundle.zip"
```

Full release-critical validation and GitHub promotion:

```bash
./deploy_and_validate_platform_core_v2_34_0_macos.sh "$HOME/Downloads/sustainable-catalyst-platform-core-v2.34.0-release-bundle.zip"
```

Optional historical certification can be run separately with `SC_CORE_FULL_CERTIFICATION=1`.

## Contabo

After GitHub promotion, run `DEPLOY_PLATFORM_CORE_V2340_CONTABO.sh`. Production Compose must use both `compose.yml` and `compose.vps.yml` so the scientific-object persistent mount remains intact.

Expected live readiness route:

`/v1/model-canvases/readiness`

Expected migration head: `0037` with `pending: []`.
