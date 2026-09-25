# Platform Core v3.39.0 Audit

PASS criteria:
- canonical runtime-neutral data types are explicit;
- schemas capture shape, field, null and endianness semantics;
- runtime-specific type mappings are explicit;
- runtime profiles declare actual readable/writable formats;
- Arrow/Parquet are contract-supported without false provider claims;
- format negotiation is candidate-discovery-only;
- Core never autonomously selects a format;
- conversion loss/null/category/timestamp policies are explicit;
- transfer completion requires verification;
- logical data identity is preserved across transfer;
- scientific-artifact projection validates against v3.38;
- source payloads remain owned by runtime/workflow systems;
- Core does not execute conversion;
- Core does not certify scientific validity;
- no database migration is introduced.
