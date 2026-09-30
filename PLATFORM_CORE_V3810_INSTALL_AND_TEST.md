# Install and Test — Platform Core v3.81.0

Apply the release bundle to a v3.80.0 checkout with `APPLY_AND_PUSH_PLATFORM_CORE_V3810.sh`.

The installer uses `backend/.venv`, runs the v3.81 validator and isolated targeted pytest suite, verifies route mounts, commits, rebases on newer `origin/main` when necessary, pushes `main`, and creates/pushes tag `v3.81.0`.

Production deployment uses `DEPLOY_PLATFORM_CORE_V3810_CONTABO.sh`, validates inside Docker with `PYTHONPATH=/app`, recreates Core, and verifies `/health` and `/public/v1/documentary-sources/contract`.

No database migration.
