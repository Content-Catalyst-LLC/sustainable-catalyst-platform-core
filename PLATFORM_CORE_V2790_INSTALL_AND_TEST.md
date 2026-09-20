# Platform Core v2.79.0 — Install and Test

## Release validation

```bash
python3 -S scripts/validate_v2790_release.py
python3 scripts/scan_push_safe_secrets.py .
python3 scripts/build_v2790_manifest.py
```

## Backend tests

```bash
export PYTHONPATH="backend:backend/public_sdk/python"
export PYTEST_DISABLE_PLUGIN_AUTOLOAD=1
python3 -m pytest -q \
  backend/tests/test_research_argument_evidentiary_synthesis_v2790.py \
  backend/tests/test_partial_0083_recovery_v2790.py \
  backend/tests/test_bundle_validator_v2790.py
```

## Backend invariant validator

```bash
PYTHONPATH=backend python3 backend/scripts/validate_research_arguments.py
```

## Readiness

```bash
curl -fsS http://127.0.0.1:8090/v1/research/arguments/readiness | python3 -m json.tool
```
