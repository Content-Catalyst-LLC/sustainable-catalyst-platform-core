# Platform Core v3.83.0 — Install and Test

Predecessor: v3.82.0.

```bash
./APPLY_AND_PUSH_PLATFORM_CORE_V3830.sh "$HOME/Downloads/sustainable-catalyst-platform-core"
```

Targeted backend validation:

```bash
cd backend
PYTHONPATH=. .venv/bin/python scripts/validate_network_structure_community_motif_v3_83_0.py
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 PYTHONPATH=. .venv/bin/python -m pytest --noconftest -q tests/test_network_structure_community_motif_v3830.py
```

Production deployment:

```bash
/tmp/DEPLOY_PLATFORM_CORE_V3830_CONTABO.sh
```
