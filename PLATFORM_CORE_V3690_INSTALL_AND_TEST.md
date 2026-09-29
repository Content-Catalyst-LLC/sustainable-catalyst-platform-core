# Platform Core v3.69.0 Install and Test

Apply with `APPLY_AND_PUSH_PLATFORM_CORE_V3690.sh`. The installer uses `backend/.venv`, runs the v3.69 validator and targeted tests, pushes `main`, and tags `v3.69.0`. Deploy production with `DEPLOY_PLATFORM_CORE_V3690_CONTABO.sh`; Docker validation explicitly sets `PYTHONPATH=/app`.
