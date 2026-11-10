# Isolated development activation

Base production Compose defaults remain unchanged. Use a distinct project name:

```sh
# Create .env.dev from .env.dev.example; generate new secrets locally.
# Never copy production credentials. Keep .env.dev private and excluded from Git.
docker compose --env-file .env.dev -p sc-dev-platform-core -f compose.yml -f compose.dev.yml config --quiet
docker compose --env-file .env.dev -p sc-dev-platform-core -f compose.yml -f compose.dev.yml up -d --build
```

Requires existing external development network `sc-internal`. Build one module at a time on ARM64. Existing Workbench, Workspace and WordPress containers must not be recreated. Published ports bind loopback only. Service tokens and signing secrets are development-specific; no production identity is accepted automatically.

Rollback: run the same Compose command with `stop` for this module only. Keep named volumes and `.env.dev` for recovery; never use `down -v`. Connector credentials and datasets are independent acceptance gates. A healthy API does not certify external providers or authenticated cross-product actions.

WordPress can reach the development API through the existing private network selected by `SC_DEV_WP_NETWORK`. Keep its external HTTP/mail guard; allow only the exact local service alias, HTTP scheme and API port. Back up plugin backend settings before installing development URLs and keys. Preserve WordPress login and application permission checks. Workspace authentication is not automatically shared with these services.

Memory limits are requested, but some Pi kernels lack memory cgroup support and discard them. Confirm kernel support; otherwise build sequentially and monitor available RAM. Cold-start migrations/imports can outlast the default health start period. Do not treat API liveness as provider, dataset, global-SSO or full cross-product acceptance.
