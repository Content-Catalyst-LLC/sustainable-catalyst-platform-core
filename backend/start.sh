#!/usr/bin/env bash
set -euo pipefail

python scripts/migrate.py
python scripts/seed_registry.py --skip-existing

exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8090}"
