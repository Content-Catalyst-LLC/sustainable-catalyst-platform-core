# Platform Core Backend v2.79.0

Backend package for **Research Argument & Evidentiary Synthesis Engine**.

Primary readiness endpoint:

`GET /v1/research/arguments/readiness`

Expected release: `2.79.0`  
Expected migration: `0083`

The deployment script enforces v2.78.0 / migration 0082 as the predecessor, accepts pristine or fully materialized partial-0083 states, performs a PostgreSQL backup, runs the migration, rebuilds Core, and validates local/public health.
