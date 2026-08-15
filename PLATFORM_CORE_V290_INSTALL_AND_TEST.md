# Platform Core v2.9.0 — Install and Test

## Local deterministic validation

```bash
cd backend
python scripts/migrate.py
pytest -q tests/test_streaming_alerts_reliability_v290.py
python scripts/run_connector_worker.py --once
cd ..
python scripts/validate_v290_release.py
```

## Production configuration

Start with `deployment/platform-core-v290.env.example`. Keep the existing v2.8.1 first-party readiness values and add the v2.9.0 streaming/worker/failover controls.

Provider failover is not globally inferred. Compatible connector groups must be declared explicitly in connector configuration.
