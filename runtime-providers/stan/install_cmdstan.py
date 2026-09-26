#!/usr/bin/env python3
import os
from pathlib import Path

from cmdstanpy import install_cmdstan

version = os.environ.get("SC_STAN_CMDSTAN_VERSION", "2.36.0")
root = Path(os.environ.get("SC_STAN_CMDSTAN_ROOT", "/opt/sustainable-catalyst/stan-runtime/.cmdstan"))
target = root / f"cmdstan-{version}"

if (target / "bin" / "stanc").exists() and (target / "makefile").exists():
    print(f"CmdStan {version} already installed at {target}")
else:
    root.mkdir(parents=True, exist_ok=True)
    ok = install_cmdstan(
        dir=str(root),
        version=version,
        cores=int(os.environ.get("SC_STAN_INSTALL_CORES", "2")),
        overwrite=False,
        verbose=True,
    )
    if not ok:
        raise SystemExit(f"CmdStan {version} installation failed")

if not (target / "bin" / "stanc").exists():
    raise SystemExit(f"CmdStan stanc binary missing at {target / 'bin' / 'stanc'}")

print(f"PASS - CmdStan {version} installed at {target}")
