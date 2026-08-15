# Platform Core v2.11.0 — Install and Test

Use the release-bundle installer from `~/Downloads`. The installer verifies component SHA-256 hashes, the immutable repository manifest, syntax, deterministic tests, migration `0014`, humanitarian validation, facility validation, and streaming/reliability validation before promotion.

Production deployments may set `SC_CORE_HUMANITARIAN_FABRIC_ENABLED=true` and `SC_CORE_HUMANITARIAN_AUTO_MATERIALIZE=true`. External provider availability remains non-blocking for Core promotion.
