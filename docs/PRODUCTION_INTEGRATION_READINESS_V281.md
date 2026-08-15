# Production Integration & Readiness — v2.8.1

## Purpose

Core distinguishes process liveness from platform readiness. A healthy Core process must not imply that a required first-party product integration is configured or reachable.

## Readiness hierarchy

1. Core liveness — `/health`
2. Database and Core capability readiness — `/ready`
3. Required first-party product readiness — included in `/ready`
4. Public-safe integration state — `/integration/readiness`
5. Authenticated gateway diagnostics — `/v1/gateway/health`

## Required service rule

A service marked `SC_CORE_<SERVICE>_REQUIRED=true` blocks release readiness unless it is configured, enabled, operational, and compatible with any configured expected version prefix. If `TOKEN_REQUIRED=true`, an absent service token is a configuration error before a network call is made.

## Security boundary

Readiness payloads expose service identifiers, names, required/configured/enabled flags, status, readiness, and an upstream-reported version when available. They never expose the configured base URL or service token.

## Production Site Intelligence contract

The v2.8.1 Render blueprint requires a deployment-supplied Site Intelligence URL and checks the `4.` version family. This is a first-party integration contract; transient third-party data providers do not block Core promotion.
