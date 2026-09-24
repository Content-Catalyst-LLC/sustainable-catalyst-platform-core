# Git push — Catalyst Julia Runtime v0.3.0

Use the release push script from macOS:

```bash
./PUSH_CATALYST_JULIA_V030.sh \
  "$HOME/Downloads/sustainable-catalyst-platform-core"
```

The script:
1. verifies Platform Core tag `v3.23.0`;
2. installs this provider at `runtime-providers/julia`;
3. runs static validation;
4. commits and pushes `main`;
5. creates immutable tag `catalyst-julia-v0.3.0`.

Expected commit message:

`Build Catalyst Julia Runtime v0.3.0 Core Runtime Contract Adapter`
