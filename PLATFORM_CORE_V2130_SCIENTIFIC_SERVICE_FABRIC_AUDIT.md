# Platform Core v2.13.0 Scientific Service Fabric Audit

## Required invariants

1. Domains are exactly `earth`, `ocean`, and `space` at the top service-routing layer.
2. Ocean-specific evidence is routed to Ocean as a first-class destination rather than silently collapsed into Earth.
3. Domain bindings are routing metadata only and carry `truth_precedence = none`.
4. Materialization is idempotent at `(subject_type, subject_id, domain)`.
5. A domain may contain zero routed records without implying absence of scientific evidence.
6. Existing scientific records, assets, time series, map layers, STAC records and provenance remain authoritative source objects.
7. External provider health does not independently block Core promotion.

## Release gate

- Migration `0016` applied with zero pending migrations.
- New v2.13.0 regression suite passes.
- Complete inherited Core suite passes.
- Python, PHP, JavaScript, Bash, JSON and release-manifest validation passes.
- Repository/plugin/bundle ZIP and SHA-256 verification passes.
