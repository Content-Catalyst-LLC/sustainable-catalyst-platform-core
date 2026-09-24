#!/usr/bin/env bash
set -euo pipefail

SRC="${1:-}"
INSTALL_ROOT="${SC_JULIA_INSTALL_ROOT:-/opt/sustainable-catalyst/julia-runtime}"
SERVICE="catalyst-julia-runtime"
BASE="${SC_JULIA_URL:-http://127.0.0.1:18093}"
PRESERVED_MANIFEST=""

if [[ -z "$SRC" || ! -d "$SRC/runtime" ]]; then
  echo "Usage: $0 /path/to/catalyst-julia-runtime-v0.3.0-release"
  exit 2
fi

command -v julia >/dev/null || {
  echo "ERROR: Julia is not installed on this VPS."
  exit 3
}

JULIA_VERSION="$(julia --version)"
echo "Using: $JULIA_VERSION"
echo "$JULIA_VERSION" | grep -Eq 'julia version 1\.13\.' || {
  echo "ERROR: Catalyst Julia Runtime v0.3.0 is pinned to Julia 1.13.x."
  exit 4
}

if [[ -f "$INSTALL_ROOT/runtime/Manifest.toml" && ! -f "$SRC/runtime/Manifest.toml" ]]; then
  PRESERVED_MANIFEST="$(mktemp)"
  cp "$INSTALL_ROOT/runtime/Manifest.toml" "$PRESERVED_MANIFEST"
fi

sudo mkdir -p "$INSTALL_ROOT"
sudo rsync -a --delete "$SRC/" "$INSTALL_ROOT/"
sudo chown -R catalystadmin:catalystadmin "$INSTALL_ROOT"

if [[ -n "$PRESERVED_MANIFEST" && -f "$PRESERVED_MANIFEST" ]]; then
  cp "$PRESERVED_MANIFEST" "$INSTALL_ROOT/runtime/Manifest.toml"
  rm -f "$PRESERVED_MANIFEST"
fi

export JULIA_DEPOT_PATH="$INSTALL_ROOT/.julia-depot"
mkdir -p "$JULIA_DEPOT_PATH" "$INSTALL_ROOT/environment/snapshots"

cd "$INSTALL_ROOT/runtime"
julia --project=. -e 'using Pkg; Pkg.resolve(); Pkg.instantiate(); Pkg.precompile()'
julia --project=. test/runtests.jl

STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
julia --project=. bin/environment_snapshot.jl > "$INSTALL_ROOT/environment/snapshots/environment-${STAMP}.json"
cp Project.toml "$INSTALL_ROOT/environment/Project.toml"
cp Manifest.toml "$INSTALL_ROOT/environment/Manifest.toml"
sha256sum Project.toml Manifest.toml > "$INSTALL_ROOT/environment/LOCKFILE_SHA256SUMS.txt"
ln -sfn "snapshots/environment-${STAMP}.json" "$INSTALL_ROOT/environment/latest.json"

sudo cp "$INSTALL_ROOT/deploy/catalyst-julia-runtime.service" /etc/systemd/system/${SERVICE}.service
sudo systemctl daemon-reload
sudo systemctl enable "$SERVICE"
sudo systemctl restart "$SERVICE"

echo "Waiting for Catalyst Julia Runtime v0.3.0 readiness at $BASE ..."
READY=0
for attempt in $(seq 1 30); do
  if curl -fsS --max-time 2 "$BASE/health" >/tmp/catalyst-julia-health-v030.json 2>/dev/null; then
    if python3 - <<'PYREADY'
import json
from pathlib import Path
p = Path('/tmp/catalyst-julia-health-v030.json')
try:
    d = json.loads(p.read_text(encoding='utf-8'))
    ident = d.get('identity') or {}
    ok = (
        d.get('status') == 'ok'
        and ident.get('service') == 'catalyst-julia-runtime'
        and ident.get('service_version') == '0.3.0'
        and ident.get('environment_schema_version') == 'sc.environment.v1'
        and ident.get('core_adapter_contract_version') == 'sc.core.runtime-adapter.v1'
    )
except Exception:
    ok = False
raise SystemExit(0 if ok else 1)
PYREADY
    then
      READY=1
      break
    fi
  fi
  if ! sudo systemctl is-active --quiet "$SERVICE"; then
    echo "Service is not active while waiting for readiness."
    sudo systemctl status "$SERVICE" --no-pager -l || true
    sudo journalctl -u "$SERVICE" -n 100 --no-pager || true
    exit 5
  fi
  sleep 2
done

if [[ "$READY" -ne 1 ]]; then
  echo "ERROR: Julia runtime did not become ready within 60 seconds."
  sudo systemctl status "$SERVICE" --no-pager -l || true
  sudo journalctl -u "$SERVICE" -n 100 --no-pager || true
  exit 6
fi

"$INSTALL_ROOT/deploy/VERIFY_CATALYST_JULIA_V030.sh"

echo "PASS - CATALYST JULIA RUNTIME v0.3.0 BACKEND DEPLOYMENT COMPLETE"
