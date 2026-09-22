# Platform Core v3.2.0 Analytical Result & Provenance Audit

- Core release: 3.2.0
- Migration: 0104
- Provider contract: `sc.core.analytical-runtime-provider.v1`
- Result/provenance contract: `sc.core.analytical-result-provenance.v1`
- Catalyst Analytics R provider: 2.1.0
- Workspace adapter baseline: 3.5.0
- Execution host: Workspace
- Core execution: prohibited
- Scientific-validity certification: prohibited
- Truth determination/ranking: prohibited
- Human review: required

The ingestion path is fingerprinted and idempotent. Result snapshots preserve immutable state hashes. Lineage is explicit rather than inferred.
