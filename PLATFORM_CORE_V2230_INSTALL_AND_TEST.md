# Platform Core v2.23.0 — Install and Test

Run the release-bundle installer from macOS Terminal. The installer verifies component SHA-256 hashes, the release contract, the immutable source manifest, syntax, all backend test files one-by-one, migration `0001–0026`, every inherited operational validator, the new federation validator, and the connector worker before Git promotion.

`SC_CORE_BUNDLE_ONLY=1` performs artifact validation without installing Python dependencies or pushing.
`SC_CORE_VALIDATE_ONLY=1` performs the complete runtime validation but does not push.

Federation secrets must be configured only as runtime environment secrets. Do not place real trust secrets in source files or committed `.env` examples.
