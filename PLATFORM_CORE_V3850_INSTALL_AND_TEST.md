# Platform Core v3.85.0 Install and Test

Predecessor: v3.84.0. Run the release bundle `APPLY_AND_PUSH_PLATFORM_CORE_V3850.sh` against the Core repository, then deploy with `DEPLOY_PLATFORM_CORE_V3850_CONTABO.sh`.

The installer uses `backend/.venv`, isolated pytest (`--noconftest`), corrected indented `Settings.version` detection, Git rebase protection, and tag verification. The Contabo deployer tests inside Docker with `PYTHONPATH=/app`.

No database migration.
