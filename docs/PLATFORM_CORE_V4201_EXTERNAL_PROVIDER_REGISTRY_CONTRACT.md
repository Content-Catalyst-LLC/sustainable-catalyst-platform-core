# Platform Core v4.20.1 — External Provider Registry Contract

This compatibility release extends the v4.20 consolidation milestone with a generic governed registry for external knowledge, data, computational, geospatial, event, and intelligence providers.

The registry defines provider identity, provider class, authority scope, capabilities, endpoints, authentication mode, licensing/usage constraints, quota/cache metadata, provenance requirements, lifecycle status, and deterministic registry snapshots.

It deliberately does **not** implement provider adapters, verify live connectivity, embed credentials, promote provider output into evidence, establish truth from source authority or source agreement, or authorize automatic graph mutation.

Reference provider records are contract examples only. They demonstrate how provider families can be registered without claiming that the corresponding adapter is implemented or live.

Database migration: none.
