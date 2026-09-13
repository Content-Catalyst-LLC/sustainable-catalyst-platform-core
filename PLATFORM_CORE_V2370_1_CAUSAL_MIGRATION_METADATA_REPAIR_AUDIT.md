# Platform Core v2.37.0.1 — Causal Migration Metadata Repair Audit

## Incident
The v2.37.0 production run created causal schema objects but failed while inserting migration `0041` into `schema_migrations` because the tag deployed from GitHub still contained an oversized migration description.

## Root cause
The prior promotion script reused an existing local `v2.37.0` tag instead of requiring a fresh tag on the rebuilt HEAD. The frozen archive and the deployed tag could therefore diverge.

## Repair
- Migration `0041` description length: 239 characters.
- Production storage contract: 300 characters.
- Added partial-0041 recovery test.
- Added tag-exists hard stop and tag-to-HEAD identity check.
- No new schema migration number; head remains `0041`.

## Validation
- 93/93 streamlined release-critical tests passed.
- True v2.36.1.2 -> v2.37.0.1 upgrade applied only `0041` and ended with `pending=[]`.
- Partial-0041 recovery test passed with all seven causal tables preserved and the short ledger row recorded.
- No causal semantics or execution boundaries were weakened by this repair.
