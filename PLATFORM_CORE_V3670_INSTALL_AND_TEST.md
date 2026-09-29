# Platform Core v3.67.0 — Install & Test

## Local validation

```bash
python3 -m venv backend/.venv
backend/.venv/bin/python -m pip install -r backend/requirements.txt
cd backend
PYTHONPATH=. .venv/bin/python scripts/validate_translation_alignment_v3_67_0.py
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 PYTHONPATH=. .venv/bin/python -m pytest -q tests/test_translation_alignment_v3670.py
```

## Contract check

```bash
curl -fsS http://127.0.0.1:8090/public/v1/translation-alignments/contract | python3 -m json.tool
```

Expected release: `3.67.0`.
Expected contract: `sc.core.translation-transliteration-alignment.v1`.

## Docker validation

```bash
docker compose -f compose.yml run --rm --no-deps -e PYTHONPATH=/app core \
  python scripts/validate_translation_alignment_v3_67_0.py

docker compose -f compose.yml run --rm --no-deps -e PYTHONPATH=/app \
  -e PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 core \
  python -m pytest -q tests/test_translation_alignment_v3670.py
```
