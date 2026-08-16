# Platform Core v2.23.1 — Install and Test

Use `deploy_and_validate_platform_core_v2_23_1_macos.sh` with `sustainable-catalyst-platform-core-v2.23.1-release-bundle.zip`.

The installer verifies component checksums, clean extraction, the v2.23.1 release contract, immutable file manifest, syntax, capability metadata lineage, the full backend test suite, migrations through `0026`, operational validators, and the connector-worker smoke path before promotion.

## Bundle-only verification

```bash
SC_CORE_BUNDLE_ONLY=1 ./deploy_and_validate_platform_core_v2_23_1_macos.sh sustainable-catalyst-platform-core-v2.23.1-release-bundle.zip
```

## Full local validation without push

```bash
SC_CORE_VALIDATE_ONLY=1 ./deploy_and_validate_platform_core_v2_23_1_macos.sh sustainable-catalyst-platform-core-v2.23.1-release-bundle.zip
```

## Full validation and promotion

```bash
./deploy_and_validate_platform_core_v2_23_1_macos.sh sustainable-catalyst-platform-core-v2.23.1-release-bundle.zip
```

No migration beyond `0026` is expected in this release.
