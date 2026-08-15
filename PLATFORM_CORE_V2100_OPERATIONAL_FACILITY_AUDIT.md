# v2.10.0 Operational Evidence & Facility Registry Audit

Release invariants:

1. Facility identity and status observations are separate records.
2. Observation history is append-oriented and date-aware.
3. Operational, damage, access and service status remain distinct dimensions.
4. Missing observations never imply normal operation.
5. Source identifiers deduplicate only on exact namespace/value identity.
6. Facility evidence preserves publisher and provenance.
7. Public APIs return only public facilities/observations and remain behind the public API authorization scope.
8. Creating a public facility observation emits a v2.9.0 stream event.
9. External provider health does not block Core promotion.
