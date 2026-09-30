# Platform Core v3.80.0 Install and Test

Apply the release bundle to a v3.79.0 checkout using `APPLY_AND_PUSH_PLATFORM_CORE_V3800.sh`. The installer uses `backend/.venv`, validates the reference bundle, runs the targeted suite with `--noconftest`, commits, rebases onto newer `origin/main` when necessary, pushes `main`, and creates/pushes tag `v3.80.0`.

Deploy with `DEPLOY_PLATFORM_CORE_V3800_CONTABO.sh`. Docker validation explicitly sets `PYTHONPATH=/app`.
