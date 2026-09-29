# Platform Core v3.65.0 — Install & Test

## Local validation

From the repository root:

```bash
cd backend
PYTHONPATH=. python3 scripts/validate_multilingual_text_language_v3_65_0.py
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 PYTHONPATH=. python3 -m pytest -q tests/test_multilingual_text_language_v3650.py
```

Expected targeted result: `17 passed`.

## Contract check

```bash
curl -fsS http://127.0.0.1:8090/public/v1/language-text/contract | python3 -m json.tool
```

Expected release: `3.65.0`.
Expected contract: `sc.core.multilingual-text-language-object.v1`.
