# Platform Core v2.78.0 Install and Test

1. Verify the release bundle checksums.
2. Run `deploy_and_validate_platform_core_v2_78_0_macos.sh` for clean-extraction and release-critical validation.
3. Promote the repository with `PUSH_PLATFORM_CORE_V2780_FINAL.sh`.
4. Deploy the tagged backend on Contabo with `DEPLOY_PLATFORM_CORE_V2780_CONTABO.sh`.
5. Confirm `/health` reports `2.78.0` and `/v1/research/hypotheses/readiness` reports migration `0082` applied.

See `PLATFORM_CORE_V2780_TERMINAL_COMMANDS.txt` for copy/paste terminal commands.
