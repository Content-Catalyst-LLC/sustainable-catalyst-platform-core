# Platform Core v2.24.0 — Install & Test

Use the v2.24.0 release bundle and macOS deployment script. The release gate verifies bundle checksums, clean extraction, the v2.24.0 contract, immutable source manifest, Python/PHP/JavaScript/shell syntax, the complete backend test suite, migration `0001–0027`, inherited operational validators, the new capacity validator, and connector-worker smoke execution before promotion.

Capacity governance remains advisory. Production certification does not require capacity readiness unless `SC_CORE_CERTIFICATION_REQUIRE_CAPACITY_READY=true` is set deliberately.
