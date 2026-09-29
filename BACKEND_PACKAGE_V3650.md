# Platform Core v3.65.0 Backend Package

The v3.65.0 backend adds the `sc.core.multilingual-text-language-object.v1` contract and routes:

- `GET /public/v1/language-text/contract`
- `GET /api/v1/language-text/contract`
- `GET /api/v1/language-text/reference`
- validation endpoints for language, script, provenance, canonical source, text unit, language span and complete bundle objects.

No database migration is required. Platform Core defines and validates the objects; OCR/HTR, language detection, tokenization/parsing, translation and transliteration remain outside Core.
