# Release Checklist

- [ ] Run `pytest -q`
- [ ] Run migration on a clean SQLite database
- [ ] Seed the registry
- [ ] Confirm duplicate entity import is idempotent
- [ ] Confirm write routes reject an invalid API key
- [ ] Confirm `/health`, `/ready`, `/v1/meta`, and `/v1/stats`
- [ ] Confirm graph traversal depth limit
- [ ] Confirm no secrets in repository
- [ ] Confirm PostgreSQL URL is configured on Render
- [ ] Confirm CORS allows only Sustainable Catalyst origins
- [ ] Install WordPress plugin and configure backend URL
- [ ] Test status and entity shortcodes
- [ ] Add Platform Core service URL to product environments
