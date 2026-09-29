# Platform Core v3.66.0 — Install & Test

## Local validation

From the repository root, use the Core virtual environment:

```bash
python3 -m venv backend/.venv
backend/.venv/bin/python -m pip install -r backend/requirements.txt
cd backend
PYTHONPATH=. .venv/bin/python scripts/validate_linguistic_annotation_v3_66_0.py
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 PYTHONPATH=. .venv/bin/python -m pytest -q tests/test_linguistic_annotation_v3660.py
```

Expected targeted result: `28 passed`.

## Contract check

```bash
curl -fsS http://127.0.0.1:8090/public/v1/linguistic-annotations/contract | python3 -m json.tool
```

Expected release: `3.66.0`.
Expected contract: `sc.core.linguistic-annotation-provenance.v1`.

## Docker validation

Always supply `/app` on Python's import path for one-off Compose containers:

```bash
docker compose -f compose.yml run --rm --no-deps -e PYTHONPATH=/app core \
  python scripts/validate_linguistic_annotation_v3_66_0.py
```
