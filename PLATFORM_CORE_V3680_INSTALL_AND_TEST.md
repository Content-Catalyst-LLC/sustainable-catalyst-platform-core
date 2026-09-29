# Platform Core v3.68.0 Install & Test

Apply with `APPLY_AND_PUSH_PLATFORM_CORE_V3680.sh`. The installer creates/reuses `backend/.venv`, installs backend requirements when needed, validates the historical-language contract, runs targeted tests, commits, pushes `main`, and tags `v3.68.0`.

Deploy with `DEPLOY_PLATFORM_CORE_V3680_CONTABO.sh`. Docker validation explicitly sets `PYTHONPATH=/app`.

No database migration is required.
