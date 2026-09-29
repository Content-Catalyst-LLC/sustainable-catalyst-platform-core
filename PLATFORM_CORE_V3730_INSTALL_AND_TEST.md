# Platform Core v3.73.0 Install & Test

Predecessor: v3.72.0.

The release apply script validates the predecessor, copies the payload, uses `backend/.venv`, runs the v3.73 validator and isolated pytest suite, verifies router mounts, commits, pushes main, and tags `v3.73.0`.

The Contabo deploy script fetches the tagged source, builds Core, executes validation with `PYTHONPATH=/app`, deploys the backend, and validates local/public health plus `/public/v1/link-prediction/contract`.

Database migration: none.
