# Platform Core v2.8.1 — Install and Test

## macOS release bundle

Place these in `~/Downloads`:

- `sustainable-catalyst-platform-core-v2.8.1-release-bundle.zip`
- `deploy_and_validate_platform_core_v2_8_1_macos.sh`

Then run:

```bash
cd ~/Downloads
chmod +x deploy_and_validate_platform_core_v2_8_1_macos.sh
./deploy_and_validate_platform_core_v2_8_1_macos.sh \
  sustainable-catalyst-platform-core-v2.8.1-release-bundle.zip
```

Use `SC_CORE_VALIDATE_ONLY=1` to validate without pushing. Use `SC_CORE_BUNDLE_ONLY=1` for checksum/manifest/static bundle verification only.

## Production configuration before live readiness can pass

Configure the deployed environment with the canonical Core URL and Site Intelligence backend URL. The Render blueprint intentionally leaves both deployment-supplied rather than hard-coding infrastructure addresses.

Verify after deployment:

```bash
curl "$SC_CORE_PUBLIC_BASE_URL/health"
curl "$SC_CORE_PUBLIC_BASE_URL/ready"
curl "$SC_CORE_PUBLIC_BASE_URL/integration/readiness"
```

A green `/health` with a blocked `/ready` is an intentional and truthful state when a required integration has not been configured or is unavailable.
