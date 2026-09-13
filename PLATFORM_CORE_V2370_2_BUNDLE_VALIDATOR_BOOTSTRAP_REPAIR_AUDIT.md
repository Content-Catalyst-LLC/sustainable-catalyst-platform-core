# Platform Core v2.37.0.2 — Bundle Validator Bootstrap Repair Audit

## Defect
`SC_CORE_BUNDLE_ONLY=1` ran the v2.37.0.1 release validator before creating `backend/.venv`. That validator imported `app.migrations`, which imports SQLAlchemy, so a clean Mac failed with `ModuleNotFoundError: No module named 'sqlalchemy'`.

## Repair
- Release-contract validation is dependency-free and uses Python standard-library AST/regex inspection only.
- The bundle-only validator is invoked with `python -S`, explicitly disabling site-package loading.
- Bundle-only mode verifies checksums, release contract, secrets, frozen manifest, Python compilation, PHP syntax, JavaScript syntax, and shell syntax without installing backend dependencies.
- Full validation creates an isolated `backend/.venv` before runtime imports and pytest.
- New regression test executes `scripts/validate_v2370_2_release.py` under `python -S`.

## Preserved v2.37 safeguards
- Migration head remains `0041`; no schema migration is added.
- `0041` description remains 239 characters and fits `schema_migrations.description VARCHAR(300)`.
- Safe partial-`0041` recovery remains supported.
- Promotion refuses to reuse/move an existing release tag and verifies archive → committed HEAD → annotated tag identity for `migrations.py`.

## Validation
- 94/94 streamlined release-critical tests pass.
- Fresh database applies migration `0041` with `pending=[]`.
- Causal Systems validator reports Core `2.37.0.2` with DAG/path/adjustment reasoning enabled and automatic causal identification/effect estimation/truth promotion disabled.
