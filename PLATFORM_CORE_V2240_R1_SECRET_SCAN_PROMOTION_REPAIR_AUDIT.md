# Platform Core v2.24.0 R1 — Secret-Scan Example Credential & Promotion Repair Audit

## Scope
Promotion tooling only. No runtime, API, model, migration, forecast, budget, governance-decision, federation, SDK-version, or WordPress-version change.

## Root cause
The v2.24.0 push-safe scan matched `SC_CORE_FEDERATION_TRUST_SECRETS_JSON` in `deployment/platform-core-v2231.env.example`. The line contained the approved documentation placeholder `replace-with-long-random-secret`, but the shell allowlist only understood narrower placeholder spellings such as `replace-me` and `change-me`.

## Repair controls
1. All text-like repository files remain in scan scope; example environment files are not globally exempted.
2. Federation JSON assignments are parsed before placeholder suppression.
3. Suppression requires every JSON value to exactly equal an approved placeholder literal.
4. A placeholder prefix with appended material is rejected.
5. Live-looking credential patterns remain release-blocking.
6. Promotion remains fail-closed: any hit exits non-zero before `git add`, commit, or push.
7. R1 validation asserts runtime `2.24.0`, migration `0027`, manifest release `2.24.0`, scanner wiring, and repair/resume wiring.

## Acceptance gates
- canonical v2.24.0 release contract passes;
- v2.24.0 R1 repair contract passes;
- repository-wide push-safe secret scan passes;
- R1 regression tests pass;
- full inherited backend regression remains green;
- migrations `0001`–`0027` apply with zero pending;
- operational validators remain green;
- clean-extraction manifest and bundle checksums verify;
- no commit/push is attempted until every gate above passes.
