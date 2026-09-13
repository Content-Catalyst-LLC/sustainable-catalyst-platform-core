# Platform Core v2.37.0.2 — Bundle Validator Bootstrap Repair

This patch fixes bundle-only verification on clean macOS Python installations. The v2.37.0.1 release validator imported `app.migrations` before the backend virtual environment existed, which transitively required SQLAlchemy and caused `ModuleNotFoundError` during `SC_CORE_BUNDLE_ONLY=1` validation.

v2.37.0.2 replaces that runtime import with dependency-free static AST inspection of `backend/app/migrations.py` plus a static verification of the `SchemaMigration.description` `String(300)` contract in `backend/app/models.py`.

No database schema changes are introduced. Migration head remains `0041`. All v2.37.0.1 causal migration metadata, partial-0041 recovery, and exact-tag identity safeguards are retained.
