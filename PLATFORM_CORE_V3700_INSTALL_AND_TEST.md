# Platform Core v3.70.0 Install and Test

Apply with `APPLY_AND_PUSH_PLATFORM_CORE_V3700.sh`. The installer creates/reuses `backend/.venv`, applies the v3.70 overlay to a v3.69/v3.70 repository, runs the validator and targeted tests, checks the full FastAPI route mount, pushes `main`, and tags `v3.70.0`.

Deploy production with `DEPLOY_PLATFORM_CORE_V3700_CONTABO.sh`. Docker validation explicitly sets `PYTHONPATH=/app`, verifies the tagged production commit, rebuilds/recreates the `core` service, then checks local and public health/contract endpoints.
