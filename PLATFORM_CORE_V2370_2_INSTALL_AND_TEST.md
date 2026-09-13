# Platform Core v2.37.0.2 — Install and Test

1. Run bundle-only verification. This path must succeed without SQLAlchemy or any backend dependency installed in the system Python.
2. Run full validation. The Mac promoter creates `backend/.venv`, installs `backend/requirements.txt`, runs the release-critical suite, validates migration `0041`, and only then promotes GitHub.
3. Deploy the exact `v2.37.0.2` tag to Contabo using the dual Compose files.
4. Install the v2.37.0.2 WordPress plugin and verify the Causal Systems status shortcode.
