# Platform Core v3.78.0 Install and Test

Required predecessor: v3.77.0 (repair is idempotent on v3.78.0).

Mac: unpack release bundle and run `./APPLY_AND_PUSH_PLATFORM_CORE_V3780.sh "$HOME/Downloads/sustainable-catalyst-platform-core"`.

Backend: copy `DEPLOY_PLATFORM_CORE_V3780_CONTABO.sh` to Contabo and run it as `catalystadmin`.

Public contract: `/public/v1/temporal-identity/contract`.

Database migration: none.
