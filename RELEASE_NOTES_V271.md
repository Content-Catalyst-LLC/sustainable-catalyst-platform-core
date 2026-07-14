# Sustainable Catalyst Platform Core v2.7.1

## International Law and United Nations Connector Pack

This release adds official UN document discovery, SDG methodology, humanitarian reporting and indicators, population, trade, displacement, and human-rights integration to the free live-data gateway.

### Included

- 16 governed free-source records in the combined registry
- 14 connector definitions in the combined registry
- Dedicated `international_law_records` storage
- Legal-authority taxonomy and public discovery APIs
- Raw-response provenance and stable content hashes
- Registration-aware configuration for ReliefWeb and OHCHR UHRI
- Metadata-only governance records for the UN Treaty Collection, ICJ, and ILC
- Migration `0008`

No paid API, credit-card-required provider, or unsupported automatic scraper is introduced.


### API surface

- Internal legal-record discovery, detail, provenance, authority taxonomy, and statistics routes
- Scoped public legal-record discovery, detail, and authority taxonomy routes
- Python internal-client methods
- Python and JavaScript public SDK methods
- WordPress `[sc_platform_core_international_law_status]` shortcode

### Legal safeguards

- Legal source types are not treated as equivalent.
- Security Council resolution symbols are classified as official records without automatically asserting binding effect.
- Human-rights recommendations and humanitarian reports are explicitly non-binding/informational authority classes.
- Treaty Collection, ICJ, and ILC sources remain governed metadata entries until approved public interfaces are available.


### Validation

- 75 backend tests passed
- Migrations `0001` through `0008` passed with no pending migrations
- 16 source records and 14 connector definitions seeded on a fresh database
- Python, PHP, JavaScript, Bash, JSON, secret-scan, and ZIP-integrity checks passed
