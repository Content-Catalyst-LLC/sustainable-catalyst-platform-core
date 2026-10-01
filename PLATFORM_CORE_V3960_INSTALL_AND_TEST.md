# Platform Core v3.96.0 Install & Test

Predecessor: v3.95.0.

Run the release bundle `APPLY_AND_PUSH_PLATFORM_CORE_V3960.sh`, then deploy with `DEPLOY_PLATFORM_CORE_V3960_CONTABO.sh`. The release uses backend/.venv, isolated pytest, Python-based version detection, Docker PYTHONPATH=/app, tag verification, and backup-before-promote.
