# Platform Core v2.27.0 — Install & Test

## Requirements

- macOS or Linux
- Python 3.10+; Python 3.12 is preferred and matches the repository `.python-version`
- PHP and Node for release lint checks

The supplied scripts refuse Python 3.9 or older rather than creating an incompatible environment.

## Local validation

```bash
cd sustainable-catalyst-platform-core-v2.27.0
python3.12 -m venv backend/.venv
backend/.venv/bin/python -m pip install -r backend/requirements.txt
export PYTHONPATH="backend:backend/public_sdk/python"
backend/.venv/bin/python backend/scripts/migrate.py
backend/.venv/bin/python backend/scripts/validate_scientific_object_storage.py
backend/.venv/bin/python -m pytest -q backend/tests/test_scientific_object_storage_processing_v2270.py
```

## Release validation

```bash
python3.12 scripts/validate_v2270_release.py
python3.12 scripts/scan_push_safe_secrets.py .
```

## Runtime configuration

The development default stores bytes under `./var/scientific-objects`. Production may point `SC_CORE_SCIENTIFIC_OBJECT_STORAGE_ROOT` at a durable mounted filesystem. v2.27.0 does not fetch external provider references and does not execute the external xarray/GDAL/Astropy contracts.
